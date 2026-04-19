import { ElMessage } from 'element-plus'
import type { Router } from 'vue-router'

import { TASK_TYPE_MAP, type CreateTaskRequest } from '@/api/task'
import type { useTaskStore } from '@/pinia/modules/task'


type TaskStore = ReturnType<typeof useTaskStore>


export async function createAnalysisTaskAndOpen(
  taskStore: TaskStore,
  router: Router,
  request: CreateTaskRequest,
) {
  const task = await taskStore.createTask(request)
  if (!task) {
    ElMessage.error('创建任务失败')
    return null
  }

  const label = TASK_TYPE_MAP[task.task_type]?.label || task.title
  ElMessage.success(`${label}任务已创建`)
  await router.push(`/task-detail/${task.id}`)
  return task
}
