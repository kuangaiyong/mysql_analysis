<template>
  <div class="page-container task-center-page">
    <div class="header">
      <div class="title-wrap">
        <div class="title">
          <el-icon :size="24"><List /></el-icon>
          <h2>任务中心</h2>
        </div>
        <div class="sub-title">统一承载健康巡检、索引顾问、锁分析、慢查询巡检、配置调优与容量风险评估</div>
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

    <div class="stats-grid">
      <el-card v-for="card in statCards" :key="card.key" shadow="hover" class="stat-card">
        <div class="stat-label">{{ card.label }}</div>
        <div class="stat-value">{{ card.value }}</div>
      </el-card>
    </div>

    <el-card shadow="never" class="filter-panel">
      <div class="filter-bar">
        <div class="filter-item current-connection">
          <span class="label">当前连接</span>
          <span class="value">{{ connectionLabel }}</span>
        </div>
        <el-select v-model="filterType" placeholder="任务类型" clearable class="filter-select" @change="handleFilterChange">
          <el-option v-for="(info, type) in TASK_TYPE_MAP" :key="type" :label="info.label" :value="type" />
        </el-select>
        <el-select v-model="filterStatus" placeholder="状态" clearable class="filter-select" @change="handleFilterChange">
          <el-option v-for="(info, key) in TASK_STATUS_MAP" :key="key" :label="info.label" :value="key" />
        </el-select>
      </div>
    </el-card>

    <el-card shadow="never" class="table-panel">
      <el-table :data="taskStore.tasks" v-loading="taskStore.loading" stripe>
        <el-table-column label="ID" prop="id" width="70" align="center" />
        <el-table-column label="任务类型" width="180">
          <template #default="{ row }">
            {{ TASK_TYPE_MAP[row.task_type]?.label || row.task_type }}
          </template>
        </el-table-column>
        <el-table-column label="标题" prop="title" min-width="220" show-overflow-tooltip />
        <el-table-column label="状态" width="110" align="center">
          <template #default="{ row }">
            <el-tag :type="TASK_STATUS_MAP[row.status]?.type || 'info'" size="small" effect="dark">
              {{ TASK_STATUS_MAP[row.status]?.label || row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="阶段" min-width="180" show-overflow-tooltip>
          <template #default="{ row }">
            {{ row.stage_message || row.progress_message || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="进度" width="180">
          <template #default="{ row }">
            <el-progress :percentage="row.live_progress ?? row.progress ?? 0" :stroke-width="12" :text-inside="true" />
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="170">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="viewDetail(row)">查看详情</el-button>
            <el-button v-if="row.status === 'failed' && row.retry_count < row.max_retries" type="warning" link size="small" @click="handleRetry(row)">重试</el-button>
            <el-button v-if="['running', 'queued', 'pending', 'cancel_requested'].includes(row.status)" type="warning" link size="small" @click="handleCancel(row)">取消</el-button>
            <el-popconfirm title="确定删除该任务？" @confirm="handleDelete(row)">
              <template #reference>
                <el-button v-if="!['running', 'queued', 'pending', 'cancel_requested'].includes(row.status)" type="danger" link size="small">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-bar" v-if="taskStore.total > pageSize">
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="pageSize"
          :total="taskStore.total"
          layout="total, prev, pager, next"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowDown, List, Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

import { TASK_STATUS_MAP, TASK_TYPE_MAP, type TaskItem } from '@/api/task'
import { useConnectionStore } from '@/pinia/modules/connection'
import { useTaskStore } from '@/pinia/modules/task'

const router = useRouter()
const connectionStore = useConnectionStore()
const taskStore = useTaskStore()

const selectedConnectionId = computed(() => connectionStore.selectedConnectionId)
const selectedConnection = computed(() => connectionStore.selectedConnection)

const filterType = ref('')
const filterStatus = ref('')
const currentPage = ref(1)
const pageSize = 20
let refreshTimer: ReturnType<typeof setInterval> | null = null

const connectionLabel = computed(() => {
  if (!selectedConnection.value) return '未选择连接'
  return `${selectedConnection.value.name} (${selectedConnection.value.host}:${selectedConnection.value.port})`
})

const statCards = computed(() => [
  { key: 'total', label: '总任务数', value: taskStore.summary.total || taskStore.total },
  { key: 'running', label: '运行中', value: (taskStore.summary.running || 0) + (taskStore.summary.queued || 0) },
  { key: 'completed', label: '已完成', value: taskStore.summary.completed || 0 },
  { key: 'failed', label: '失败/取消', value: (taskStore.summary.failed || 0) + (taskStore.summary.cancelled || 0) },
])

onMounted(() => {
  refreshList()
  refreshTimer = setInterval(() => {
    if (taskStore.hasRunningTask) {
      refreshList()
    }
  }, 5000)
})

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer)
})

watch(selectedConnectionId, () => {
  currentPage.value = 1
  refreshList()
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

function handleFilterChange() {
  currentPage.value = 1
  refreshList()
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
    payload: { connection_id: selectedConnectionId.value },
    source_page: 'task-center',
  })
  if (!task) {
    ElMessage.error('创建任务失败')
    return
  }
  ElMessage.success(`任务“${task.title}”已创建`)
  viewDetail(task)
}

async function handleRetry(row: TaskItem) {
  try {
    const task = await taskStore.retryTask(row.id)
    if (task) {
      ElMessage.success('已重新提交任务')
      viewDetail(task)
    }
  } catch {
    ElMessage.error('重试失败')
  }
}

async function handleCancel(row: TaskItem) {
  try {
    await taskStore.cancelTask(row.id)
    ElMessage.success('已提交取消请求')
    refreshList()
  } catch {
    ElMessage.error('取消失败')
  }
}

async function handleDelete(row: TaskItem) {
  try {
    await taskStore.deleteTask(row.id)
    ElMessage.success('任务已删除')
  } catch {
    ElMessage.error('删除失败')
  }
}

function viewDetail(row: TaskItem) {
  router.push(`/task-detail/${row.id}`)
}

function formatTime(iso: string | null | undefined) {
  if (!iso) return '-'
  return new Date(iso).toLocaleString('zh-CN', { hour12: false })
}
</script>

<style scoped lang="scss">
.task-center-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
}

.title-wrap {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.title {
  display: flex;
  align-items: center;
  gap: 8px;

  h2 {
    margin: 0;
    font-size: 22px;
  }
}

.sub-title {
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

.actions {
  display: flex;
  gap: 8px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.stat-card {
  .stat-label {
    color: var(--el-text-color-secondary);
    font-size: 13px;
  }

  .stat-value {
    margin-top: 8px;
    font-size: 28px;
    font-weight: 700;
  }
}

.filter-panel,
.table-panel {
  border-radius: 12px;
}

.filter-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.filter-item {
  display: flex;
  flex-direction: column;
  gap: 4px;

  .label {
    color: var(--el-text-color-secondary);
    font-size: 12px;
  }

  .value {
    font-size: 13px;
    font-weight: 600;
  }
}

.current-connection {
  min-width: 260px;
}

.filter-select {
  width: 180px;
}

.pagination-bar {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

@media (max-width: 1100px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .header {
    flex-direction: column;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .actions {
    width: 100%;
  }
}
</style>
