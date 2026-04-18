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
  status: 'pending' | 'running' | 'success' | 'failed' | 'cancelled'
  title: string
  progress: number
  progress_message: string
  result_json: string | null
  error_message: string | null
  retry_count: number
  max_retries: number
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
}

export interface TaskListResponse {
  success: boolean
  data: TaskItem[]
  total: number
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

  /** 订阅任务进度 SSE */
  subscribeProgress(
    taskId: number,
    callbacks: {
      onProgress?: (data: { task_id: number; status: string; progress: number; message: string }) => void
      onComplete?: (data: { task_id: number; status: string; progress: number; message: string }) => void
      onError?: (err: string) => void
    },
  ): EventSource {
    const url = `${config.baseApi}/tasks/${taskId}/progress`
    const es = new EventSource(url)

    es.addEventListener('progress', (e) => {
      try {
        callbacks.onProgress?.(JSON.parse(e.data))
      } catch { /* ignore */ }
    })

    es.addEventListener('complete', (e) => {
      try {
        callbacks.onComplete?.(JSON.parse(e.data))
      } catch { /* ignore */ }
      es.close()
    })

    es.addEventListener('error', () => {
      callbacks.onError?.('连接中断')
      es.close()
    })

    return es
  },
}

/** 任务类型映射 */
export const TASK_TYPE_MAP: Record<string, { label: string; icon: string }> = {
  health_report: { label: '健康巡检报告', icon: 'Document' },
  index_advisor: { label: 'AI 索引顾问', icon: 'Grid' },
  lock_analysis: { label: 'AI 锁分析', icon: 'Lock' },
  slow_query_patrol: { label: 'AI 慢查询巡检', icon: 'Timer' },
  config_tuning: { label: 'AI 配置调优', icon: 'SetUp' },
  capacity_prediction: { label: 'AI 容量预测', icon: 'TrendCharts' },
}

/** 状态映射 */
export const TASK_STATUS_MAP: Record<string, { label: string; type: string }> = {
  pending: { label: '等待中', type: 'info' },
  running: { label: '运行中', type: '' },
  success: { label: '已完成', type: 'success' },
  failed: { label: '失败', type: 'danger' },
  cancelled: { label: '已取消', type: 'warning' },
}
