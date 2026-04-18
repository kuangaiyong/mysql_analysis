import { defineStore } from 'pinia'
import { ref } from 'vue'
import { taskApi, type TaskItem, type CreateTaskRequest } from '@/api/task'

export const useTaskStore = defineStore('task', () => {
  const tasks = ref<TaskItem[]>([])
  const total = ref(0)
  const loading = ref(false)
  const currentTask = ref<TaskItem | null>(null)

  /** 加载任务列表 */
  async function loadTasks(params?: {
    connection_id?: number
    task_type?: string
    status?: string
    limit?: number
    offset?: number
  }) {
    loading.value = true
    try {
      const res = await taskApi.list(params)
      tasks.value = res.data
      total.value = res.total
    } catch (e) {
      console.error('加载任务列表失败:', e)
    } finally {
      loading.value = false
    }
  }

  /** 创建任务 */
  async function createTask(data: CreateTaskRequest): Promise<TaskItem | null> {
    try {
      const task = await taskApi.create(data)
      // 刷新列表
      await loadTasks({ connection_id: data.connection_id })
      return task
    } catch (e) {
      console.error('创建任务失败:', e)
      return null
    }
  }

  /** 获取任务详情 */
  async function fetchTask(taskId: number) {
    try {
      currentTask.value = await taskApi.get(taskId)
    } catch (e) {
      console.error('获取任务详情失败:', e)
    }
  }

  /** 重试任务 */
  async function retryTask(taskId: number) {
    try {
      await taskApi.retry(taskId)
      // 更新列表中的状态
      const idx = tasks.value.findIndex((t) => t.id === taskId)
      if (idx !== -1) {
        tasks.value[idx].status = 'pending'
        tasks.value[idx].progress = 0
      }
    } catch (e) {
      console.error('重试任务失败:', e)
      throw e
    }
  }

  /** 取消任务 */
  async function cancelTask(taskId: number) {
    try {
      await taskApi.cancel(taskId)
      const idx = tasks.value.findIndex((t) => t.id === taskId)
      if (idx !== -1) {
        tasks.value[idx].status = 'cancelled'
      }
    } catch (e) {
      console.error('取消任务失败:', e)
      throw e
    }
  }

  /** 删除任务 */
  async function deleteTask(taskId: number) {
    try {
      await taskApi.remove(taskId)
      tasks.value = tasks.value.filter((t) => t.id !== taskId)
      total.value = Math.max(0, total.value - 1)
    } catch (e) {
      console.error('删除任务失败:', e)
      throw e
    }
  }

  /** 更新列表中某个任务的状态（用于 SSE 回调） */
  function updateTaskInList(taskId: number, updates: Partial<TaskItem>) {
    const idx = tasks.value.findIndex((t) => t.id === taskId)
    if (idx !== -1) {
      tasks.value[idx] = { ...tasks.value[idx], ...updates }
    }
  }

  return {
    tasks,
    total,
    loading,
    currentTask,
    loadTasks,
    createTask,
    fetchTask,
    retryTask,
    cancelTask,
    deleteTask,
    updateTaskInList,
  }
})
