<template>
  <div class="page-container task-detail-page">
    <!-- 头部 -->
    <div class="header">
      <div class="title">
        <el-button text @click="goBack"><el-icon><ArrowLeft /></el-icon></el-button>
        <h2>{{ task?.title || '任务详情' }}</h2>
        <el-tag v-if="task" :type="TASK_STATUS_MAP[task.status]?.type || 'info'" size="small" effect="dark">
          {{ TASK_STATUS_MAP[task.status]?.label || task.status }}
        </el-tag>
      </div>
      <div class="actions">
        <el-button v-if="task?.status === 'failed' && task.retry_count < task.max_retries" type="warning" @click="handleRetry">重试</el-button>
        <el-button v-if="task?.status === 'running'" type="warning" @click="handleCancel">取消</el-button>
      </div>
    </div>

    <!-- 任务元信息 -->
    <div v-if="task" class="meta-bar">
      <span>类型：{{ TASK_TYPE_MAP[task.task_type]?.label || task.task_type }}</span>
      <el-divider direction="vertical" />
      <span>创建：{{ formatTime(task.created_at) }}</span>
      <template v-if="task.completed_at">
        <el-divider direction="vertical" />
        <span>完成：{{ formatTime(task.completed_at) }}</span>
      </template>
      <template v-if="task.retry_count > 0">
        <el-divider direction="vertical" />
        <span>重试次数：{{ task.retry_count }}/{{ task.max_retries }}</span>
      </template>
    </div>

    <!-- 运行中/等待中 -->
    <div v-if="task && (task.status === 'running' || task.status === 'pending')" class="running-state">
      <el-icon class="is-loading" :size="32" color="#409EFF"><Loading /></el-icon>
      <p>{{ liveMessage || '任务执行中...' }}</p>
      <el-progress :percentage="liveProgress" :stroke-width="16" :text-inside="true" style="max-width: 500px; margin: 16px auto" />
    </div>

    <!-- 失败 -->
    <div v-else-if="task?.status === 'failed'" class="error-state">
      <el-alert type="error" :title="task.error_message || '任务执行失败'" show-icon :closable="false" />
    </div>

    <!-- 已取消 -->
    <div v-else-if="task?.status === 'cancelled'" class="cancelled-state">
      <el-alert type="warning" title="任务已取消" show-icon :closable="false" />
    </div>

    <!-- 结果渲染 -->
    <div v-else-if="task?.status === 'success' && parsedResult" class="result-container">
      <!-- 健康报告 -->
      <template v-if="task.task_type === 'health_report'">
        <HealthReportResult :data="parsedResult" />
      </template>
      <!-- 5 种分析结果共用同一组件 -->
      <template v-else>
        <AnalysisResult :data="parsedResult" :task-type="task.task_type" />
      </template>
    </div>

    <!-- 加载中 -->
    <div v-else-if="loading" class="loading-state">
      <el-skeleton :rows="8" animated />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, Loading } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { taskApi, TASK_TYPE_MAP, TASK_STATUS_MAP, type TaskItem } from '@/api/task'
import HealthReportResult from './components/HealthReportResult.vue'
import AnalysisResult from './components/AnalysisResult.vue'

const route = useRoute()
const router = useRouter()

const task = ref<TaskItem | null>(null)
const loading = ref(true)
const liveProgress = ref(0)
const liveMessage = ref('')

let eventSource: EventSource | null = null
let pollTimer: ReturnType<typeof setInterval> | null = null

const parsedResult = computed(() => {
  if (!task.value?.result_json) return null
  try {
    return JSON.parse(task.value.result_json)
  } catch {
    return null
  }
})

onMounted(() => {
  loadTask()
})

onUnmounted(() => {
  eventSource?.close()
  if (pollTimer) clearInterval(pollTimer)
})

async function loadTask() {
  const id = Number(route.params.id)
  if (!id) return
  loading.value = true
  try {
    task.value = await taskApi.get(id)
    if (task.value.live_progress) liveProgress.value = task.value.live_progress
    if (task.value.live_message) liveMessage.value = task.value.live_message
    // 如果任务正在运行，订阅 SSE 进度
    if (task.value.status === 'running' || task.value.status === 'pending') {
      subscribeProgress(id)
    }
  } catch {
    ElMessage.error('加载任务失败')
  } finally {
    loading.value = false
  }
}

function subscribeProgress(taskId: number) {
  // 使用轮询替代 SSE（SSE 需要认证 header，EventSource 不支持）
  pollTimer = setInterval(async () => {
    try {
      const t = await taskApi.get(taskId)
      task.value = t
      liveProgress.value = t.live_progress ?? t.progress
      liveMessage.value = t.live_message ?? t.progress_message
      if (t.status === 'success' || t.status === 'failed' || t.status === 'cancelled') {
        if (pollTimer) clearInterval(pollTimer)
      }
    } catch { /* ignore */ }
  }, 2000)
}

async function handleRetry() {
  if (!task.value) return
  try {
    await taskApi.retry(task.value.id)
    ElMessage.success('已重新提交')
    loadTask()
  } catch {
    ElMessage.error('重试失败')
  }
}

async function handleCancel() {
  if (!task.value) return
  try {
    await taskApi.cancel(task.value.id)
    ElMessage.success('任务已取消')
    task.value.status = 'cancelled'
    if (pollTimer) clearInterval(pollTimer)
  } catch {
    ElMessage.error('取消失败')
  }
}

function goBack() {
  router.push('/task-center')
}

function formatTime(iso: string | null): string {
  if (!iso) return '-'
  return new Date(iso).toLocaleString('zh-CN', { hour12: false })
}
</script>

<style scoped lang="scss">
.task-detail-page {
  padding: 20px;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow-y: auto;

  .header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;

    .title {
      display: flex;
      align-items: center;
      gap: 8px;
      h2 { margin: 0; font-size: 20px; font-weight: 600; }
    }
  }

  .meta-bar {
    font-size: 13px;
    color: var(--el-text-color-secondary);
    margin-bottom: 20px;
  }

  .running-state, .loading-state {
    text-align: center;
    padding: 60px 20px;
    p { color: var(--el-text-color-secondary); margin: 16px 0; }
  }

  .error-state, .cancelled-state {
    margin: 20px 0;
  }

  .result-container {
    flex: 1;
  }
}
</style>
