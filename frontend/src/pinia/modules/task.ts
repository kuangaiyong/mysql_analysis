import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { taskApi, type CreateTaskRequest, type TaskEventItem, type TaskItem, type TaskListResponse } from '@/api/task'


export const useTaskStore = defineStore('task', () => {
  const tasks = ref<TaskItem[]>([])
  const total = ref(0)
  const loading = ref(false)
  const currentTask = ref<TaskItem | null>(null)
  const currentEvents = ref<TaskEventItem[]>([])
  const summary = ref<Record<string, number>>({})
  const activeStream = ref<AbortController | null>(null)

  const hasRunningTask = computed(() => tasks.value.some((task) => ['queued', 'running', 'pending', 'cancel_requested'].includes(task.status)))

  async function loadTasks(params?: {
    connection_id?: number
    task_type?: string
    status?: string
    limit?: number
    offset?: number
  }) {
    loading.value = true
    try {
      const res: TaskListResponse = await taskApi.list(params)
      tasks.value = res.data
      total.value = res.total
      summary.value = res.summary || res.stats || {}
    } finally {
      loading.value = false
    }
  }

  async function createTask(data: CreateTaskRequest): Promise<TaskItem | null> {
    try {
      const task = await taskApi.create(data)
      tasks.value = [task, ...tasks.value.filter((item) => item.id !== task.id)]
      total.value += 1
      return task
    } catch (error) {
      console.error('创建任务失败:', error)
      return null
    }
  }

  async function fetchTask(taskId: number): Promise<TaskItem | null> {
    try {
      currentTask.value = await taskApi.get(taskId)
      updateTaskInList(taskId, currentTask.value)
      return currentTask.value
    } catch (error) {
      console.error('获取任务详情失败:', error)
      return null
    }
  }

  async function fetchTaskEvents(taskId: number, afterSeq = 0): Promise<TaskEventItem[]> {
    const events = await taskApi.listEvents(taskId, { after_seq: afterSeq, limit: 200 })
    if (afterSeq === 0) {
      currentEvents.value = events
    } else if (events.length > 0) {
      currentEvents.value = [...currentEvents.value, ...events]
    }
    return events
  }

  function stopTaskStream() {
    activeStream.value?.abort()
    activeStream.value = null
  }

  async function startTaskStream(taskId: number) {
    stopTaskStream()
    const task = await fetchTask(taskId)
    await fetchTaskEvents(taskId)

    if (!task || ['success', 'failed', 'cancelled', 'timed_out'].includes(task.status)) {
      return
    }

    const lastSeq = currentEvents.value.at(-1)?.seq || 0
    let latestSeq = lastSeq
    activeStream.value = taskApi.subscribeEvents(taskId, {
      onEvent: async (event) => {
        if (event.seq <= latestSeq) return
        latestSeq = event.seq
        currentEvents.value = [...currentEvents.value, event]
        await fetchTask(taskId)
      },
      onComplete: async () => {
        await fetchTask(taskId)
        stopTaskStream()
      },
      onError: async () => {
        await fetchTask(taskId)
        stopTaskStream()
      },
    })
  }

  async function retryTask(taskId: number): Promise<TaskItem | null> {
    const task = await taskApi.retry(taskId)
    updateTaskInList(taskId, task)
    if (currentTask.value?.id === taskId) {
      currentTask.value = task
    }
    return task
  }

  async function cancelTask(taskId: number): Promise<TaskItem | null> {
    await taskApi.cancel(taskId)
    const task = await taskApi.get(taskId)
    updateTaskInList(taskId, task)
    if (currentTask.value?.id === taskId) {
      currentTask.value = task
    }
    return task
  }

  async function deleteTask(taskId: number) {
    await taskApi.remove(taskId)
    tasks.value = tasks.value.filter((item) => item.id !== taskId)
    total.value = Math.max(0, total.value - 1)
    if (currentTask.value?.id === taskId) {
      currentTask.value = null
      currentEvents.value = []
    }
  }

  function updateTaskInList(taskId: number, updates: Partial<TaskItem> | null) {
    if (!updates) return
    const index = tasks.value.findIndex((task) => task.id === taskId)
    if (index !== -1) {
      tasks.value[index] = { ...tasks.value[index], ...updates }
      return
    }
    if ('id' in updates && updates.id === taskId) {
      tasks.value.unshift(updates as TaskItem)
    }
  }

  return {
    tasks,
    total,
    loading,
    currentTask,
    currentEvents,
    summary,
    hasRunningTask,
    loadTasks,
    createTask,
    fetchTask,
    fetchTaskEvents,
    startTaskStream,
    stopTaskStream,
    retryTask,
    cancelTask,
    deleteTask,
    updateTaskInList,
  }
})
