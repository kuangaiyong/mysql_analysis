<template>
  <div class="page-container task-center-page">
    <div class="header">
      <div class="title">
        <el-icon :size="24"><List /></el-icon>
        <h2>任务中心</h2>
      </div>
      <div class="actions">
        <el-dropdown @command="handleCreateTask" :disabled="!selectedConnectionId">
          <el-button type="primary">
            新建分析任务 <el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item v-for="(info, type) in TASK_TYPE_MAP" :key="type" :command="type">
                {{ info.label }}
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <el-button @click="refreshList" :loading="taskStore.loading">
          <el-icon><Refresh /></el-icon>
        </el-button>
      </div>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <el-select v-model="filterType" placeholder="任务类型" clearable style="width: 160px" @change="refreshList">
        <el-option v-for="(info, type) in TASK_TYPE_MAP" :key="type" :label="info.label" :value="type" />
      </el-select>
      <el-select v-model="filterStatus" placeholder="状态" clearable style="width: 120px" @change="refreshList">
        <el-option v-for="(info, key) in TASK_STATUS_MAP" :key="key" :label="info.label" :value="key" />
      </el-select>
    </div>

    <!-- 任务列表 -->
    <el-table :data="taskStore.tasks" v-loading="taskStore.loading" stripe border style="width: 100%">
      <el-table-column label="ID" prop="id" width="60" align="center" />
      <el-table-column label="任务类型" width="160">
        <template #default="{ row }">
          {{ TASK_TYPE_MAP[row.task_type]?.label || row.task_type }}
        </template>
      </el-table-column>
      <el-table-column label="标题" prop="title" min-width="180" show-overflow-tooltip />
      <el-table-column label="状态" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="TASK_STATUS_MAP[row.status]?.type || 'info'" size="small" effect="dark">
            {{ TASK_STATUS_MAP[row.status]?.label || row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="进度" width="180">
        <template #default="{ row }">
          <el-progress
            v-if="row.status === 'running'"
            :percentage="row.live_progress ?? row.progress"
            :stroke-width="14"
            :text-inside="true"
          />
          <el-progress
            v-else-if="row.status === 'success'"
            :percentage="100"
            :stroke-width="14"
            :text-inside="true"
            status="success"
          />
          <span v-else-if="row.status === 'failed'" class="text-danger">{{ row.error_message || '失败' }}</span>
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column label="重试" width="70" align="center">
        <template #default="{ row }">
          {{ row.retry_count }}/{{ row.max_retries }}
        </template>
      </el-table-column>
      <el-table-column label="创建时间" width="170">
        <template #default="{ row }">
          {{ formatTime(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" align="center" fixed="right">
        <template #default="{ row }">
          <el-button v-if="row.status === 'success'" type="primary" link size="small" @click="viewDetail(row)">查看结果</el-button>
          <el-button v-if="row.status === 'failed' && row.retry_count < row.max_retries" type="warning" link size="small" @click="handleRetry(row)">重试</el-button>
          <el-button v-if="row.status === 'running' || row.status === 'pending'" type="warning" link size="small" @click="handleCancel(row)">取消</el-button>
          <el-popconfirm title="确定删除该任务？" @confirm="handleDelete(row)">
            <template #reference>
              <el-button type="danger" link size="small">删除</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <div class="pagination-bar" v-if="taskStore.total > pageSize">
      <el-pagination
        v-model:current-page="currentPage"
        :page-size="pageSize"
        :total="taskStore.total"
        layout="total, prev, pager, next"
        @current-change="handlePageChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { List, ArrowDown, Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useConnectionStore } from '@/pinia/modules/connection'
import { useTaskStore } from '@/pinia/modules/task'
import { taskApi, TASK_TYPE_MAP, TASK_STATUS_MAP } from '@/api/task'

const router = useRouter()
const connectionStore = useConnectionStore()
const taskStore = useTaskStore()
const selectedConnectionId = computed(() => connectionStore.selectedConnectionId)

const filterType = ref('')
const filterStatus = ref('')
const currentPage = ref(1)
const pageSize = 20

// 自动刷新定时器
let refreshTimer: ReturnType<typeof setInterval> | null = null

onMounted(() => {
  refreshList()
  // 每 5 秒自动刷新（有运行中任务时）
  refreshTimer = setInterval(() => {
    const hasRunning = taskStore.tasks.some((t) => t.status === 'running' || t.status === 'pending')
    if (hasRunning) refreshList()
  }, 5000)
})

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer)
})

function refreshList() {
  taskStore.loadTasks({
    connection_id: selectedConnectionId.value ?? undefined,
    task_type: filterType.value || undefined,
    status: filterStatus.value || undefined,
    limit: pageSize,
    offset: (currentPage.value - 1) * pageSize,
  })
}

function handlePageChange(page: number) {
  currentPage.value = page
  refreshList()
}

async function handleCreateTask(taskType: string) {
  if (!selectedConnectionId.value) {
    ElMessage.warning('请先选择数据库连接')
    return
  }
  const task = await taskStore.createTask({
    connection_id: selectedConnectionId.value,
    task_type: taskType,
  })
  if (task) {
    ElMessage.success(`任务"${task.title}"已创建`)
  }
}

async function handleRetry(row: any) {
  try {
    await taskStore.retryTask(row.id)
    ElMessage.success('已重新提交任务')
    refreshList()
  } catch {
    ElMessage.error('重试失败')
  }
}

async function handleCancel(row: any) {
  try {
    await taskStore.cancelTask(row.id)
    ElMessage.success('任务已取消')
  } catch {
    ElMessage.error('取消失败')
  }
}

async function handleDelete(row: any) {
  try {
    await taskStore.deleteTask(row.id)
    ElMessage.success('任务已删除')
  } catch {
    ElMessage.error('删除失败')
  }
}

function viewDetail(row: any) {
  router.push(`/task-detail/${row.id}`)
}

function formatTime(iso: string | null): string {
  if (!iso) return '-'
  const d = new Date(iso)
  return d.toLocaleString('zh-CN', { hour12: false })
}
</script>

<style scoped lang="scss">
.task-center-page {
  padding: 20px;
  height: 100%;
  display: flex;
  flex-direction: column;

  .header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;

    .title {
      display: flex;
      align-items: center;
      gap: 8px;

      h2 { margin: 0; font-size: 20px; font-weight: 600; }
    }

    .actions {
      display: flex;
      gap: 8px;
    }
  }

  .filter-bar {
    display: flex;
    gap: 12px;
    margin-bottom: 16px;
  }

  .pagination-bar {
    display: flex;
    justify-content: flex-end;
    margin-top: 16px;
  }

  .text-danger {
    color: var(--el-color-danger);
    font-size: 12px;
  }
}
</style>
