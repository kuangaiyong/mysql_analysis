/**
 * AI 诊断 API
 */

import client from './client'
import { config } from '@/core/config'
import { getToken } from '@/types/auth'

export interface ChatRequest {
  connection_id: number
  question: string
  history?: Array<{ role: string; content: string }>
}

export interface ChatResponse {
  success: boolean
  answer: string
  context_summary?: {
    connection_id: number
    database: string
    metrics_available: boolean
    config_issues_count: number
    slow_queries_count: number
    bottleneck_type: string
  }
  error?: string
  provider?: string
  cached?: boolean
}

export interface OptimizeSQLRequest {
  connection_id: number
  sql: string
}

export interface IndexSuggestion {
  table: string
  index_name?: string
  columns: string[]
  type?: string
  create_statement: string
  drop_statement?: string
  reason: string
  impact?: 'high' | 'medium' | 'low'
  estimated_improvement?: string
}

export interface OptimizationPoint {
  type: 'rewrite' | 'index' | 'config'
  description: string
  impact: 'high' | 'medium' | 'low'
}

export interface OptimizeSQLResponse {
  success: boolean
  original_sql: string
  optimization?: {
    problem_analysis: string
    optimized_sql: string
    optimization_points?: OptimizationPoint[]
    index_suggestions: IndexSuggestion[]
    expected_improvement: string
  }
  explain_before?: Record<string, unknown>
  explain_after?: Record<string, unknown>
  error?: string
  provider?: string
}

export interface ExplainRequest {
  sql: string
  explain_result: Record<string, unknown>
}

export interface ExplainAnalyzeRequest {
  connection_id: number
  sql: string
}

export interface ExplainResponse {
  success: boolean
  sql: string
  interpretation?: string
  original_explain?: Record<string, unknown>
  error?: string
  provider?: string
}

export type QuestionType = 'slow_database' | 'config_issues' | 'slow_queries' | 'index_suggestions' | 'buffer_pool' | 'lock_analysis' | 'connection_health' | 'io_bottleneck'

export interface QuickDiagnosisRequest {
  connection_id: number
  question_type: QuestionType
}

export interface AIStatusResponse {
  enabled: boolean
  provider: string
  model: string
  cache_enabled: boolean
  rate_limit: number
}

/**
 * AI 诊断对话
 */
export async function aiChat(request: ChatRequest): Promise<ChatResponse> {
  const response = await client.post('/ai/chat', request)
  return response.data
}

/**
 * SQL 优化建议
 */
export async function optimizeSQL(request: OptimizeSQLRequest): Promise<OptimizeSQLResponse> {
  const response = await client.post('/ai/optimize-sql', request)
  return response.data
}

/**
 * EXPLAIN 结果解读
 */
export async function explainInterpret(request: ExplainRequest): Promise<ExplainResponse> {
  const response = await client.post('/ai/explain-interpret', request)
  return response.data
}

/**
 * 执行 EXPLAIN 并由 AI 进行优化分析
 */
export async function explainAnalyze(request: ExplainAnalyzeRequest): Promise<ExplainResponse> {
  const response = await client.post('/ai/explain-analyze', request)
  return response.data
}

/**
 * 快速诊断
 */
export async function quickDiagnosis(request: QuickDiagnosisRequest): Promise<ChatResponse> {
  const response = await client.post('/ai/quick-diagnosis', request)
  return response.data
}

/**
 * 获取 AI 服务状态
 */
export async function getAIStatus(): Promise<AIStatusResponse> {
  const response = await client.get('/ai/status')
  return response.data
}

export default {
  aiChat,
  optimizeSQL,
  explainInterpret,
  quickDiagnosis,
  getAIStatus,
  // SSE 流式 API
  aiChatStream,
  quickDiagnosisStream,
  optimizeSQLStream,
}

/**
 * SSE 流式响应事件类型
 */
export interface SSEEvent {
  type: 'status' | 'context' | 'analysis' | 'comparison' | 'chunk' | 'result' | 'error'
  message: string
  success?: boolean
  answer?: string
  error?: string
  session_id?: number
  text?: string
  data?: Record<string, unknown>
}

/**
 * SSE 事件监听器
 */
export interface SSEListeners {
  onStatus?: (data: SSEEvent) => void
  onContext?: (data: SSEEvent) => void
  onAnalysis?: (data: SSEEvent) => void
  onComparison?: (data: SSEEvent) => void
  onChunk?: (data: SSEEvent) => void
  onResult?: (data: SSEEvent) => void
  onError?: (data: SSEEvent) => void
}

/**
 * 创建 SSE 连接（GET 请求）
 * 注意: 标准 EventSource 不支持自定义 headers
 * 如需认证，建议使用 createFetchSSEConnection 或将 token 作为 URL 参数传递
 */
export function createSSEConnection(
  url: string,
  _token: string,
  listeners: SSEListeners
): () => void {
  // 注意: 标准 EventSource 不支持自定义 headers
  // 如果需要 Authorization，建议将 token 作为 URL 参数传递或使用 fetch + ReadableStream
  const eventSource = new EventSource(url)

  eventSource.addEventListener('status', (event: MessageEvent) => {
    listeners.onStatus?.(JSON.parse(event.data))
  })

  eventSource.addEventListener('context', (event: MessageEvent) => {
    listeners.onContext?.(JSON.parse(event.data))
  })

  eventSource.addEventListener('analysis', (event: MessageEvent) => {
    listeners.onAnalysis?.(JSON.parse(event.data))
  })

  eventSource.addEventListener('result', (event: MessageEvent) => {
    listeners.onResult?.(JSON.parse(event.data))
    eventSource.close()
  })

  eventSource.addEventListener('error', (event: MessageEvent) => {
    if (event.data) {
      listeners.onError?.(JSON.parse(event.data))
    }
    eventSource.close()
  })

  eventSource.onerror = () => {
    listeners.onError?.({ type: 'error', message: '连接失败' })
    eventSource.close()
  }

  return () => {
    eventSource.close()
  }
}

/**
 * AI 诊断 SSE 流式对话
 */
export function aiChatStream(
  request: ChatRequest,
  listeners: SSEListeners
): () => void {
  const url = `${config.baseApi}/ai/chat/stream`
  const token = getToken()
  // 注意: EventSource 不支持 POST 请求，需要使用 fetch + ReadableStream
  // 这里提供一个基于 fetch 的实现
  return createFetchSSEConnection(url, token || '', request, listeners)
}

/**
 * 快速诊断 SSE 流式
 */
export function quickDiagnosisStream(
  request: QuickDiagnosisRequest,
  listeners: SSEListeners
): () => void {
  const url = `${config.baseApi}/ai/quick-diagnosis/stream`
  const token = getToken()
  return createFetchSSEConnection(url, token || '', request, listeners)
}

/**
 * SQL 优化 SSE 流式
 */
export function optimizeSQLStream(
  request: OptimizeSQLRequest,
  listeners: SSEListeners
): () => void {
  const url = `${config.baseApi}/ai/optimize-sql/stream`
  const token = getToken()
  return createFetchSSEConnection(url, token || '', request, listeners)
}

/**
 * 通用 SSE POST 请求（支持自定义事件类型）
 * 用于带会话持久化的对话等新端点
 */
export function ssePost(
  path: string,
  body: unknown,
  listeners: Record<string, (data: any) => void>
): () => void {
  const url = `${config.baseApi}${path.replace(/^\/api\/v1/, '')}`
  const token = getToken()
  const extendedListeners: SSEListeners & Record<string, any> = {}

  // 映射标准事件
  if (listeners.onStatus) extendedListeners.onStatus = listeners.onStatus
  if (listeners.onContext) extendedListeners.onContext = listeners.onContext
  if (listeners.onAnalysis) extendedListeners.onAnalysis = listeners.onAnalysis
  if (listeners.onComparison) extendedListeners.onComparison = listeners.onComparison
  if (listeners.onChunk) extendedListeners.onChunk = listeners.onChunk
  if (listeners.onResult) extendedListeners.onResult = listeners.onResult
  if (listeners.onError) extendedListeners.onError = listeners.onError

  // 存储额外的自定义事件监听器
  const customListeners = { ...listeners }

  return createFetchSSEConnectionEx(url, token || '', body, extendedListeners, customListeners)
}

/**
 * 扩展 SSE 连接（支持自定义事件）
 */
function createFetchSSEConnectionEx(
  url: string,
  token: string,
  body: unknown,
  listeners: SSEListeners,
  customListeners: Record<string, (data: any) => void>
): () => void {
  let abortController = new AbortController()

  fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      'Accept': 'text/event-stream',
    },
    body: JSON.stringify(body),
    signal: abortController.signal
  })
    .then(async response => {
      if (!response.ok) {
        listeners.onError?.({ type: 'error', message: `请求失败: ${response.status}` })
        return
      }

      const reader = response.body?.getReader()
      if (!reader) {
        listeners.onError?.({ type: 'error', message: '无法获取响应流' })
        return
      }

      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        let currentEvent = ''
        let dataLines: string[] = []

        for (const line of lines) {
          if (line.startsWith('event:')) {
            currentEvent = line.substring(6).trim()
          } else if (line.startsWith('data:')) {
            dataLines.push(line.substring(5).trim())
          } else if (line === '' && currentEvent && dataLines.length > 0) {
            const currentData = dataLines.join('\n')
            dataLines = []
            try {
              const eventData = JSON.parse(currentData)
              // 标准事件
              switch (currentEvent) {
                case 'status': listeners.onStatus?.(eventData); break
                case 'context': listeners.onContext?.(eventData); break
                case 'analysis': listeners.onAnalysis?.(eventData); break
                case 'comparison': listeners.onComparison?.(eventData); break
                case 'chunk': listeners.onChunk?.(eventData); break
                case 'result': listeners.onResult?.(eventData); break
                case 'error': listeners.onError?.(eventData); break
                default: {
                  // 自定义事件（如 session）
                  const handlerName = `on${currentEvent.charAt(0).toUpperCase()}${currentEvent.slice(1)}`
                  customListeners[handlerName]?.(eventData)
                }
              }
            } catch (parseError) {
              console.error('SSE JSON 解析失败:', parseError)
            }
            currentEvent = ''
          }
        }
      }
    })
    .catch(error => {
      if (error.name !== 'AbortError') {
        listeners.onError?.({ type: 'error', message: error.message || '连接失败' })
      }
    })

  return () => {
    abortController.abort()
  }
}

/**
 * 使用 fetch + ReadableStream 实现 SSE（因为 EventSource 不支持 POST）
 */
function createFetchSSEConnection(
  url: string,
  token: string,
  body: unknown,
  listeners: SSEListeners
): () => void {
  let abortController = new AbortController()

  fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      'Accept': 'text/event-stream',
    },
    body: JSON.stringify(body),
    signal: abortController.signal
  })
    .then(async response => {
      if (!response.ok) {
        listeners.onError?.({ type: 'error', message: `请求失败: ${response.status}` })
        return
      }

      const reader = response.body?.getReader()
      if (!reader) {
        listeners.onError?.({ type: 'error', message: '无法获取响应流' })
        return
      }

      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })

        // 解析 SSE 事件
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        let currentEvent = ''
        let dataLines: string[] = []

        for (const line of lines) {
          if (line.startsWith('event:')) {
            currentEvent = line.substring(6).trim()
          } else if (line.startsWith('data:')) {
            // 支持多行 data 字段（SSE 规范）
            dataLines.push(line.substring(5).trim())
          } else if (line === '' && currentEvent && dataLines.length > 0) {
            // 空行表示事件结束
            const currentData = dataLines.join('\n')
            dataLines = []
            try {
              const eventData = JSON.parse(currentData)
              switch (currentEvent) {
                case 'status':
                  listeners.onStatus?.(eventData)
                  break
                case 'context':
                  listeners.onContext?.(eventData)
                  break
                case 'analysis':
                  listeners.onAnalysis?.(eventData)
                  break
                case 'comparison':
                  listeners.onComparison?.(eventData)
                  break
                case 'chunk':
                  listeners.onChunk?.(eventData)
                  break
                case 'result':
                  listeners.onResult?.(eventData)
                  break
                case 'error':
                  listeners.onError?.(eventData)
                  break
              }
            } catch (parseError) {
              console.error('SSE JSON 解析失败:', parseError, 'data:', currentData)
              listeners.onError?.({ type: 'error', message: '响应数据解析失败' })
            }
            currentEvent = ''
          }
        }
      }
    })
    .catch(error => {
      if (error.name !== 'AbortError') {
        listeners.onError?.({ type: 'error', message: error.message || '连接失败' })
      }
    })

  return () => {
    abortController.abort()
  }
}

// ==================== 会话管理 ====================

/** 诊断会话 */
export interface DiagnosisSession {
  id: number
  connection_id: number
  session_type: string
  title: string
  created_at: string
  updated_at: string
  message_count: number
}

/** 会话消息 */
export interface SessionMessage {
  id: number
  session_id: number
  role: 'user' | 'assistant'
  content: string
  context_snapshot?: string
  created_at: string
}

/** 会话详情（含消息列表） */
export interface SessionDetail {
  session: DiagnosisSession
  messages: SessionMessage[]
}

/**
 * 创建诊断会话
 */
export function createSession(connectionId: number, title?: string) {
  return client.post<DiagnosisSession>('/ai/sessions', {
    connection_id: connectionId,
    session_type: 'chat',
    title: title || '新对话',
  })
}

/**
 * 获取会话列表
 */
export function getSessions(connectionId: number, limit = 50, offset = 0) {
  return client.get<DiagnosisSession[]>('/ai/sessions', {
    params: { connection_id: connectionId, limit, offset },
  })
}

/**
 * 获取会话详情（含消息）
 */
export function getSessionDetail(sessionId: number) {
  return client.get<SessionDetail>(`/ai/sessions/${sessionId}`)
}

/**
 * 更新会话标题
 */
export function updateSessionTitle(sessionId: number, title: string) {
  return client.put<DiagnosisSession>(`/ai/sessions/${sessionId}`, { title })
}

/**
 * 删除会话
 */
export function deleteSession(sessionId: number) {
  return client.delete(`/ai/sessions/${sessionId}`)
}

// ==================== 健康报告 ====================

/** 维度评分 */
export interface DimensionScore {
  name: string
  score: number
  weight: number
  analysis: string
}

/** 健康报告 */
export interface HealthReport {
  id: number
  connection_id: number
  report_type: string
  health_score: number
  content: Record<string, any>
  dimensions: DimensionScore[]
  created_at: string
}

/**
 * 获取报告列表
 */
export function getReports(connectionId: number, limit = 20) {
  return client.get<HealthReport[]>('/ai/reports', {
    params: { connection_id: connectionId, limit },
  })
}

/**
 * 获取报告详情
 */
export function getReportDetail(reportId: number) {
  return client.get<HealthReport>(`/ai/reports/${reportId}`)
}

/**
 * 删除报告
 */
export function deleteReport(reportId: number) {
  return client.delete(`/ai/reports/${reportId}`)
}

/**
 * 导出报告为 Markdown
 */
export function exportReportMarkdown(reportId: number) {
  return client.get(`/ai/reports/${reportId}/export`, {
    responseType: 'blob',
  })
}

// ==================== 健康报告 SSE 流式生成 ====================

/** 报告 SSE 事件监听器 */
export interface ReportSSEListeners {
  onProgress?: (data: { current: number; total: number; dimension: string; status: string }) => void
  onDimension?: (data: { name: string; score: number; analysis: string }) => void
  onResult?: (data: { report_id: number; health_score: number; dimensions: DimensionScore[]; content: Record<string, any> }) => void
  onError?: (data: { message: string }) => void
}

/**
 * 流式生成健康报告（SSE）
 * 返回 AbortController，调用 abort() 可取消生成
 */
export function generateHealthReportStream(
  connectionId: number,
  listeners: ReportSSEListeners
): AbortController {
  const controller = new AbortController()
  const body = JSON.stringify({ connection_id: connectionId })

  const url = `${config.baseApi}/ai/reports/generate/stream`
  const token = getToken()

  fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token || ''}`,
    },
    body,
    signal: controller.signal,
  })
    .then(async (response) => {
      if (!response.ok) throw new Error(`HTTP ${response.status}`)
      const reader = response.body!.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        let currentEvent = ''
        for (const line of lines) {
          if (line.startsWith('event: ')) {
            currentEvent = line.slice(7).trim()
          } else if (line.startsWith('data: ') && currentEvent) {
            try {
              const data = JSON.parse(line.slice(6))
              switch (currentEvent) {
                case 'progress': listeners.onProgress?.(data); break
                case 'dimension': listeners.onDimension?.(data); break
                case 'result': listeners.onResult?.(data); break
                case 'error': listeners.onError?.(data); break
              }
            } catch { /* 忽略解析错误 */ }
            currentEvent = ''
          }
        }
      }
    })
    .catch((err) => {
      if (err.name !== 'AbortError') {
        listeners.onError?.({ message: err.message })
      }
    })

  return controller
}


// ==================== SQL 执行 API ====================

export interface SQLClassification {
  risk_level: 'low' | 'medium' | 'high' | 'forbidden'
  risk_label: string
  risk_color: string
  description: string
  rollback_sql?: string
  impact?: string
  requires_confirmation: boolean
}

export interface ExecuteSQLRequest {
  connection_id: number
  sql: string
}

export interface ExecuteSQLResponse {
  success: boolean
  rows_affected?: number
  data?: Record<string, unknown>[]
  message?: string
  error?: string
  risk_level?: string
  risk_label?: string
  rollback_sql?: string
}

/**
 * SQL 安全分类
 */
export async function classifySQL(sql: string): Promise<SQLClassification> {
  const response = await client.post('/ai/classify-sql', { sql })
  return response.data
}

/**
 * 执行 SQL（带安全校验）
 */
export async function executeSQL(request: ExecuteSQLRequest): Promise<ExecuteSQLResponse> {
  const response = await client.post('/ai/execute-sql', request)
  return response.data
}


// ==================== SQL 优化历史记录 ====================

export interface SqlOptRecord {
  id: number
  connection_id: number
  original_sql: string
  created_at: string
}

export interface SqlOptRecordDetail extends SqlOptRecord {
  result: Record<string, any>
}

export async function getSqlOptRecords(connectionId: number, limit = 50): Promise<SqlOptRecord[]> {
  const response = await client.get('/ai/sql-optimization-records', {
    params: { connection_id: connectionId, limit }
  })
  return response.data
}

export async function getSqlOptRecordDetail(recordId: number): Promise<SqlOptRecordDetail> {
  const response = await client.get(`/ai/sql-optimization-records/${recordId}`)
  return response.data
}

export async function deleteSqlOptRecord(recordId: number): Promise<void> {
  await client.delete(`/ai/sql-optimization-records/${recordId}`)
}

export async function saveSqlOptRecord(connectionId: number, originalSql: string, result: Record<string, any>): Promise<{ success: boolean; id: number }> {
  const response = await client.post('/ai/sql-optimization-records/save', {
    connection_id: connectionId,
    original_sql: originalSql,
    result,
  })
  return response.data
}


// ==================== EXPLAIN 分析历史记录 ====================

export interface ExplainRecord {
  id: number
  connection_id: number
  sql: string
  created_at: string
}

export interface ExplainRecordDetail extends ExplainRecord {
  result: Record<string, any>
}

export async function getExplainRecords(connectionId: number, limit = 50): Promise<ExplainRecord[]> {
  const response = await client.get('/ai/explain-analysis-records', {
    params: { connection_id: connectionId, limit }
  })
  return response.data
}

export async function getExplainRecordDetail(recordId: number): Promise<ExplainRecordDetail> {
  const response = await client.get(`/ai/explain-analysis-records/${recordId}`)
  return response.data
}

export async function deleteExplainRecord(recordId: number): Promise<void> {
  await client.delete(`/ai/explain-analysis-records/${recordId}`)
}

export async function saveExplainRecord(connectionId: number, sql: string, result: Record<string, any>): Promise<{ success: boolean; id: number }> {
  const response = await client.post('/ai/explain-analysis-records/save', {
    connection_id: connectionId,
    sql,
    result,
  })
  return response.data
}


// ==================== 5 个新 AI 模块 SSE 流式 ====================

/** 通用分析模块 SSE 流式请求 */
function createAnalysisStream(
  path: string,
  connectionId: number,
  callbacks: {
    onStatus?: (data: any) => void
    onContext?: (data: any) => void
    onAnalysis?: (data: any) => void
    onChunk?: (text: string) => void
    onResult?: (data: any) => void
    onError?: (error: string) => void
  }
): AbortController {
  const controller = new AbortController()
  const baseURL = client.defaults.baseURL || ''
  const url = `${baseURL}${path}`

  fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${getToken() || ''}`,
    },
    body: JSON.stringify({ connection_id: connectionId }),
    signal: controller.signal,
  })
    .then(async (response) => {
      if (!response.ok) {
        callbacks.onError?.(`HTTP ${response.status}`)
        return
      }
      const reader = response.body?.getReader()
      if (!reader) return
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        let currentEvent = ''
        for (const line of lines) {
          if (line.startsWith('event:')) {
            currentEvent = line.substring(6).trim()
          } else if (line.startsWith('data:') && currentEvent) {
            try {
              const data = JSON.parse(line.substring(5).trim())
              switch (currentEvent) {
                case 'status': callbacks.onStatus?.(data); break
                case 'context': callbacks.onContext?.(data); break
                case 'analysis': callbacks.onAnalysis?.(data); break
                case 'chunk': callbacks.onChunk?.(data.text || ''); break
                case 'result': callbacks.onResult?.(data); break
                case 'error': callbacks.onError?.(data.message || '未知错误'); break
              }
            } catch { /* ignore */ }
            currentEvent = ''
          }
        }
      }
    })
    .catch((err) => {
      if (err.name !== 'AbortError') {
        callbacks.onError?.(err.message || '网络错误')
      }
    })

  return controller
}

export type AnalysisCallbacks = {
  onStatus?: (data: any) => void
  onContext?: (data: any) => void
  onAnalysis?: (data: any) => void
  onChunk?: (text: string) => void
  onResult?: (data: any) => void
  onError?: (error: string) => void
}

/** AI 索引顾问 */
export function indexAdvisorStream(connectionId: number, callbacks: AnalysisCallbacks): AbortController {
  return createAnalysisStream('/ai/index-advisor/stream', connectionId, callbacks)
}

/** AI 锁分析 */
export function lockAnalysisStream(connectionId: number, callbacks: AnalysisCallbacks): AbortController {
  return createAnalysisStream('/ai/lock-analysis/stream', connectionId, callbacks)
}

/** AI 慢查询巡检 */
export function slowQueryPatrolStream(connectionId: number, callbacks: AnalysisCallbacks): AbortController {
  return createAnalysisStream('/ai/slow-query-patrol/stream', connectionId, callbacks)
}

/** AI 配置调优 */
export function configTuningStream(connectionId: number, callbacks: AnalysisCallbacks): AbortController {
  return createAnalysisStream('/ai/config-tuning/stream', connectionId, callbacks)
}

/** AI 容量预测 */
export function capacityPredictionStream(connectionId: number, callbacks: AnalysisCallbacks): AbortController {
  return createAnalysisStream('/ai/capacity-prediction/stream', connectionId, callbacks)
}


// ==================== EXPLAIN 分析 SSE 流式 ====================

export function explainAnalyzeStream(
  connectionId: number,
  sql: string,
  callbacks: {
    onStatus?: (data: any) => void
    onContext?: (data: any) => void
    onAnalysis?: (data: any) => void
    onChunk?: (text: string) => void
    onResult?: (data: any) => void
    onError?: (error: string) => void
  }
): AbortController {
  const controller = new AbortController()

  const eventHandlers: Record<string, (data: any) => void> = {
    status: (data) => callbacks.onStatus?.(data),
    context: (data) => callbacks.onContext?.(data),
    analysis: (data) => callbacks.onAnalysis?.(data),
    chunk: (data) => callbacks.onChunk?.(data.text || ''),
    result: (data) => callbacks.onResult?.(data),
    error: (data) => callbacks.onError?.(data.message || '未知错误'),
  }

  const baseURL = client.defaults.baseURL || ''
  const url = `${baseURL}/ai/explain-analyze/stream`

  fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ connection_id: connectionId, sql }),
    signal: controller.signal,
  })
    .then(async (response) => {
      if (!response.ok) {
        callbacks.onError?.(`HTTP ${response.status}`)
        return
      }
      const reader = response.body?.getReader()
      if (!reader) return
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        let currentEvent = ''
        for (const line of lines) {
          if (line.startsWith('event: ')) {
            currentEvent = line.slice(7).trim()
          } else if (line.startsWith('data: ') && currentEvent) {
            try {
              const data = JSON.parse(line.slice(6))
              eventHandlers[currentEvent]?.(data)
            } catch { /* ignore parse errors */ }
            currentEvent = ''
          }
        }
      }
    })
    .catch((err) => {
      if (err.name !== 'AbortError') {
        callbacks.onError?.(err.message || '网络错误')
      }
    })

  return controller
}
