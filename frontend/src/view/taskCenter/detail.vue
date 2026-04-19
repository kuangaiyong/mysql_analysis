<template>
  <div class="page-container task-detail-page">
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
        <el-button v-if="task && ['queued', 'pending', 'running', 'cancel_requested'].includes(task.status)" type="warning" @click="handleCancel">取消</el-button>
      </div>
    </div>

    <div v-if="task" class="overview-grid">
      <el-card shadow="never" class="overview-card">
        <template #header>任务概览</template>
        <div class="meta-row">
          <span>类型：{{ TASK_TYPE_MAP[task.task_type]?.label || task.task_type }}</span>
          <span>连接：{{ task.connection_id }}</span>
          <span>创建：{{ formatTime(task.created_at) }}</span>
          <span>更新：{{ formatTime(task.updated_at) }}</span>
        </div>
        <div class="meta-row">
          <span>阶段：{{ task.stage_message || task.progress_message || '-' }}</span>
          <span>重试：{{ task.retry_count }}/{{ task.max_retries }}</span>
          <span>来源：{{ task.source_page || '-' }}</span>
        </div>
        <el-progress :percentage="progressValue" :stroke-width="16" :text-inside="true" />
      </el-card>

      <el-card shadow="never" class="timeline-card">
        <template #header>执行时间线</template>
        <el-timeline>
          <el-timeline-item
            v-for="event in currentEvents"
            :key="event.seq"
            :timestamp="formatTime(event.created_at)"
            :type="timelineType(event.event_type)"
            placement="top"
          >
            <div class="event-item">
              <div class="event-title">{{ eventTitle(event) }}</div>
              <div v-if="eventMessage(event)" class="event-message">{{ eventMessage(event) }}</div>
            </div>
          </el-timeline-item>
        </el-timeline>
      </el-card>
    </div>

    <div v-if="task && ['running', 'queued', 'pending', 'cancel_requested'].includes(task.status)" class="running-state">
      <el-icon class="is-loading" :size="32" color="#409EFF"><Loading /></el-icon>
      <p>{{ task.stage_message || task.progress_message || '任务执行中...' }}</p>
    </div>

    <div v-else-if="task?.status === 'failed'" class="error-state">
      <el-alert type="error" :title="task.error_message || '任务执行失败'" show-icon :closable="false" />
    </div>

    <div v-else-if="task?.status === 'cancelled'" class="cancelled-state">
      <el-alert type="warning" title="任务已取消" show-icon :closable="false" />
    </div>

    <div v-else-if="task?.status === 'success' && parsedResult" class="result-container">
      <template v-if="task.task_type === 'health_report'">
        <HealthReportResult :data="parsedResult.structured || parsedResult" />
      </template>
      <template v-else>
        <AnalysisResult :data="parsedResult.structured ? parsedResult : { structured: parsedResult.structured || {}, answer: parsedResult.raw?.answer || parsedResult.answer || '', meta: parsedResult.meta }" :task-type="task.task_type" />
      </template>
    </div>

    <div v-else-if="loading" class="loading-state">
      <el-skeleton :rows="8" animated />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, Loading } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

import { TASK_STATUS_MAP, TASK_TYPE_MAP, type TaskEventItem } from '@/api/task'
import { useTaskStore } from '@/pinia/modules/task'
import HealthReportResult from './components/HealthReportResult.vue'
import AnalysisResult from './components/AnalysisResult.vue'

const route = useRoute()
const router = useRouter()
const taskStore = useTaskStore()

const loading = ref(true)

const task = computed(() => taskStore.currentTask)
const progressValue = computed(() => task.value?.live_progress ?? task.value?.progress ?? 0)
const currentEvents = computed(() => taskStore.currentEvents)

const parsedResult = computed(() => {
  if (!task.value?.result_json) return null
  try {
    return JSON.parse(task.value.result_json)
  } catch {
    return null
  }
})

onMounted(async () => {
  await loadTask()
})

watch(() => route.params.id, async (id, oldId) => {
  if (id !== oldId) {
    await loadTask()
  }
})

onUnmounted(() => {
  taskStore.stopTaskStream()
})

async function loadTask() {
  const id = Number(route.params.id)
  if (!id) return
  loading.value = true
  try {
    const loadedTask = await taskStore.fetchTask(id)
    if (!loadedTask) throw new Error('任务不存在')
    await taskStore.startTaskStream(id)
  } catch {
    ElMessage.error('加载任务失败')
  } finally {
    loading.value = false
  }
}

async function handleRetry() {
  if (!task.value) return
  try {
    await taskStore.retryTask(task.value.id)
    await loadTask()
    ElMessage.success('已重新提交')
  } catch {
    ElMessage.error('重试失败')
  }
}

async function handleCancel() {
  if (!task.value) return
  try {
    await taskStore.cancelTask(task.value.id)
    ElMessage.success('已提交取消请求')
  } catch {
    ElMessage.error('取消失败')
  }
}

function goBack() {
  if (window.history.length > 1) {
    router.back()
    return
  }
  router.push('/task-center')
}

function formatTime(iso: string | null | undefined): string {
  if (!iso) return '-'
  return new Date(iso).toLocaleString('zh-CN', { hour12: false })
}

function timelineType(eventType: string) {
  if (eventType === 'error') return 'danger'
  if (eventType === 'result_ready') return 'success'
  if (eventType === 'status_changed') return 'primary'
  return 'info'
}

function eventTitle(event: TaskEventItem) {
  const mapping: Record<string, string> = {
    task_created: '任务已创建',
    status_changed: '状态变更',
    status: '任务状态',
    context: '上下文采集',
    analysis: 'AI 分析',
    progress: '执行进度',
    result_ready: '结果已生成',
    retry_requested: '重新提交',
    error: '执行失败',
    chunk: '流式输出',
  }
  return mapping[event.event_type] || event.event_type
}

function eventMessage(event: TaskEventItem) {
  if (!event.event) return ''
  if (typeof event.event === 'string') return event.event
  return event.event.message || event.event.status || ''
}
</script>

<style scoped lang="scss">
.task-detail-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;

  .title {
    display: flex;
    align-items: center;
    gap: 8px;

    h2 {
      margin: 0;
      font-size: 20px;
      font-weight: 600;
    }
  }
}

.overview-grid {
  display: grid;
  grid-template-columns: 1.1fr 1fr;
  gap: 16px;
}

.overview-card,
.timeline-card {
  border-radius: 12px;
}

.meta-row {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 12px;
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

.event-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.event-title {
  font-weight: 600;
}

.event-message {
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

.running-state,
.loading-state {
  text-align: center;
  padding: 40px 20px;
}

.error-state,
.cancelled-state {
  margin-top: 8px;
}

.result-container {
  display: flex;
  flex-direction: column;
}

@media (max-width: 1100px) {
  .overview-grid {
    grid-template-columns: 1fr;
  }
}
</style>
