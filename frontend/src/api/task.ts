/**
 * 任务管理 API
 */

import client from './client'
import { config } from '@/core/config'
import { getToken } from '@/types/auth'

export interface TaskItem {
  id: number
  connection_id: number
  task_type: string
  status: 'pending' | 'queued' | 'running' | 'retry_waiting' | 'success' | 'failed' | 'cancelled' | 'timed_out' | 'cancel_requested'
  title: string
  progress: number
  stage_code?: string | null
  stage_message?: string
  progress_message: string
  result_json: string | null
  result_schema_version?: number
  error_code?: string | null
  error_message: string | null
  retry_count: number
  max_retries: number
  source_page?: string | null
  payload_summary?: Record<string, any> | null
  worker_id?: string | null
  heartbeat_at?: string | null
  cancel_requested_at?: string | null
  started_at: string | null
  completed_at: string | null
  created_at: string | null
  updated_at: string | null
  live_progress?: number
  live_message?: string
}

export interface CreateTaskRequest {
  connection_id: number
  task_type: string
  title?: string
  payload?: Record<string, any>
  source_page?: string
}

export interface TaskListResponse {
  success: boolean
  data: TaskItem[]
  total: number
  stats?: Record<string, number>
  summary?: Record<string, number>
}

export interface TaskEventItem {
  id: number
  task_id: number
  seq: number
  event_type: string
  progress: number | null
  stage_code: string | null
  event: Record<string, any> | string | null
  created_at: string | null
}

export const taskApi = {
  /** 创建并启动任务 */
  async create(data: CreateTaskRequest): Promise<TaskItem> {
    const res = await client.post('/tasks', data)
    return res.data.data
  },

  /** 获取任务列表 */
  async list(params?: {
    connection_id?: number
    task_type?: string
    status?: string
    limit?: number
    offset?: number
  }): Promise<TaskListResponse> {
    const res = await client.get('/tasks', { params })
    return res.data
  },

  /** 获取任务详情 */
  async get(taskId: number): Promise<TaskItem> {
    const res = await client.get(`/tasks/${taskId}`)
    return res.data.data
  },

  /** 重试失败的任务 */
  async retry(taskId: number): Promise<TaskItem> {
    const res = await client.post(`/tasks/${taskId}/retry`)
    return res.data.data
  },

  /** 取消任务 */
  async cancel(taskId: number): Promise<void> {
    await client.post(`/tasks/${taskId}/cancel`)
  },

  /** 删除任务 */
  async remove(taskId: number): Promise<void> {
    await client.delete(`/tasks/${taskId}`)
  },

  async listEvents(taskId: number, params?: { after_seq?: number; limit?: number }): Promise<TaskEventItem[]> {
    const res = await client.get(`/tasks/${taskId}/events`, { params })
    return res.data.data || []
  },

  /** 订阅任务事件流 */
  subscribeEvents(
    taskId: number,
    callbacks: {
      onEvent?: (data: TaskEventItem) => void
      onComplete?: (data: { task_id: number; status: string; progress: number; message: string }) => void
      onError?: (err: string) => void
    }
  ): AbortController {
    const controller = new AbortController()
    const url = `${config.baseApi}/tasks/${taskId}/events/stream`

    fetch(url, {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${getToken() || ''}`,
        Accept: 'text/event-stream',
      },
      signal: controller.signal,
    })
      .then(async (response) => {
        if (!response.ok) {
          callbacks.onError?.(`HTTP ${response.status}`)
          return
        }
        const reader = response.body?.getReader()
        if (!reader) {
          callbacks.onError?.('无法建立事件流')
          return
        }

        const decoder = new TextDecoder()
        let buffer = ''
        let currentEvent = ''
        let dataLines: string[] = []

        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split('\n')
          buffer = lines.pop() || ''

          for (const line of lines) {
            if (line.startsWith('event:')) {
              currentEvent = line.substring(6).trim()
            } else if (line.startsWith('data:')) {
              dataLines.push(line.substring(5).trim())
            } else if (line === '' && currentEvent) {
              const payload = dataLines.join('\n')
              dataLines = []
              try {
                const data = JSON.parse(payload)
                if (currentEvent === 'event') {
                  callbacks.onEvent?.(data)
                } else if (currentEvent === 'complete') {
                  callbacks.onComplete?.(data)
                  controller.abort()
                  return
                } else if (currentEvent === 'error') {
                  callbacks.onError?.(data.message || '事件流异常')
                  controller.abort()
                  return
                }
              } catch {
                callbacks.onError?.('任务事件解析失败')
                controller.abort()
                return
              }
              currentEvent = ''
            }
          }
        }
      })
      .catch((err) => {
        if (err.name !== 'AbortError') {
          callbacks.onError?.(err.message || '连接中断')
        }
      })

    return controller
  },
}

/** 任务类型映射 */
export const TASK_TYPE_MAP: Record<string, { label: string; icon: string }> = {
  health_report: { label: '健康巡检报告', icon: 'Document' },
  index_advisor: { label: 'AI 索引顾问', icon: 'Grid' },
  lock_analysis: { label: 'AI 锁分析', icon: 'Lock' },
  slow_query_patrol: { label: 'AI 慢查询巡检', icon: 'Timer' },
  config_tuning: { label: 'AI 配置调优', icon: 'SetUp' },
  capacity_prediction: { label: '容量风险评估', icon: 'TrendCharts' },
}

/** 状态映射 */
export const TASK_STATUS_MAP: Record<string, { label: string; type: string }> = {
  pending: { label: '等待中', type: 'info' },
  queued: { label: '已入队', type: 'info' },
  running: { label: '运行中', type: '' },
  retry_waiting: { label: '等待重试', type: 'warning' },
  success: { label: '已完成', type: 'success' },
  failed: { label: '失败', type: 'danger' },
  cancelled: { label: '已取消', type: 'warning' },
  cancel_requested: { label: '取消中', type: 'warning' },
  timed_out: { label: '超时', type: 'danger' },
}
