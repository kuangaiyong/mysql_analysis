import { beforeEach, describe, expect, it, vi } from 'vitest'

import { createPinia, setActivePinia } from 'pinia'

import { taskApi } from '@/api/task'
import { useTaskStore } from '@/pinia/modules/task'


vi.mock('@/api/task', async () => {
  const actual = await vi.importActual<typeof import('@/api/task')>('@/api/task')
  return {
    ...actual,
    taskApi: {
      list: vi.fn(),
      create: vi.fn(),
      get: vi.fn(),
      retry: vi.fn(),
      cancel: vi.fn(),
      remove: vi.fn(),
      listEvents: vi.fn(),
      subscribeEvents: vi.fn(() => ({ abort: vi.fn() })),
    },
  }
})


describe('task store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('loads task list and summary', async () => {
    vi.mocked(taskApi.list).mockResolvedValue({
      success: true,
      data: [{
        id: 1,
        connection_id: 1,
        task_type: 'index_advisor',
        status: 'queued',
        title: 'AI 索引顾问',
        progress: 0,
        progress_message: '等待调度',
        result_json: null,
        error_message: null,
        retry_count: 0,
        max_retries: 2,
        started_at: null,
        completed_at: null,
        created_at: null,
        updated_at: null,
      }],
      total: 1,
      summary: { total: 1, queued: 1 },
    } as any)

    const store = useTaskStore()
    await store.loadTasks({ connection_id: 1 })

    expect(store.tasks).toHaveLength(1)
    expect(store.summary.queued).toBe(1)
  })

  it('updates current task events when fetching', async () => {
    vi.mocked(taskApi.get).mockResolvedValue({
      id: 1,
      connection_id: 1,
      task_type: 'health_report',
      status: 'running',
      title: '健康巡检报告',
      progress: 10,
      progress_message: '采集中',
      result_json: null,
      error_message: null,
      retry_count: 0,
      max_retries: 2,
      started_at: null,
      completed_at: null,
      created_at: null,
      updated_at: null,
    } as any)
    vi.mocked(taskApi.listEvents).mockResolvedValue([
      { id: 1, task_id: 1, seq: 1, event_type: 'status', progress: 10, stage_code: 'context', event: { message: '采集中' }, created_at: null },
    ] as any)

    const store = useTaskStore()
    await store.fetchTask(1)
    await store.fetchTaskEvents(1)

    expect(store.currentTask?.status).toBe('running')
    expect(store.currentEvents).toHaveLength(1)
  })
})
