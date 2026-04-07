/**
 * API Mock Factory Functions
 * 
 * Provides mock implementations for all API modules with success and failure scenarios
 * Used for unit and integration testing
 */

import type {
  Connection,
  ConnectionCreate,
  ConnectionUpdate,
  ConnectionTest,
  ConnectionTestResult,
} from '@/types/connection'
import type {
  SlowQuery,
  SlowQueryDetail,
  ExplainResult,
  OptimizationSuggestion,
  SlowQueryHistory,
} from '@/types/slowQuery'
import type { ExplainRequest, ExplainResult, ExplainAnalyzeResult, IndexSuggestion, ExplainAnalysis } from '@/types/explain'
import type {
  AlertRule,
  AlertRuleCreate,
  AlertRuleUpdate,
  AlertHistory,
  AlertStatistics,
} from '@/types/alert'
import type {
  PerformanceMetrics,
  MetricsHistory,
  AutoCollectionConfig,
} from '@/types/monitoring'

// ============================================================================
// Mock Client Factory
// ============================================================================

export function mockApiClient() {
  return {
    get: vi.fn().mockImplementation(() => ({ data: {} })),
    post: vi.fn().mockImplementation(() => ({ data: {} })),
    put: vi.fn().mockImplementation(() => ({ data: {} })),
    delete: vi.fn().mockImplementation(() => undefined),
  }
}

// ============================================================================
// Connection API Mocks
// ============================================================================

/**
 * Mock for connectionsApi.getAll()
 * @param success - whether to return success or error
 * @param data - optional mock data to return on success
 */
export function mockConnectionApi(success: boolean = true, data?: Connection[]) {
  const connectionsApi = {
    getAll: vi.fn().mockImplementation(async () => {
      if (success) {
        return data || mockConnectionList(3)
      }
      throw new Error('Failed to fetch connections')
    }),

    getById: vi.fn().mockImplementation(async (id: number) => {
      if (success) {
        return mockConnection({ id })
      }
      throw new Error('Failed to fetch connection ' + id)
    }),

    create: vi.fn().mockImplementation(async (data: ConnectionCreate) => {
      if (success) {
        return mockConnection({ ...data, id: 1 })
      }
      throw new Error('Failed to create connection')
    }),

    update: vi.fn().mockImplementation(async (id: number, data: ConnectionUpdate) => {
      if (success) {
        return mockConnection({ id, ...data })
      }
      throw new Error('Failed to update connection ' + id)
    }),

    delete: vi.fn().mockImplementation(async (id: number) => {
      if (success) {
        return undefined
      }
      throw new Error('Failed to delete connection ' + id)
    }),

    test: vi.fn().mockImplementation(async (data: ConnectionTest) => {
      if (success) {
        return mockConnectionTestResult()
      }
      throw new Error('Connection test failed')
    }),
  }

  return connectionsApi
}

/**
 * Mock for 404 error scenarios
 */
export function mockConnectionApi404() {
  const error = new Error('Not Found')
  ;(error as any).response = { status: 404, data: { detail: 'Connection not found' } }
  throw error
}

/**
 * Mock for 500 error scenarios
 */
export function mockConnectionApi500() {
  const error = new Error('Internal Server Error')
  ;(error as any).response = { status: 500, data: { detail: 'Server error' } }
  throw error
}

/**
 * Mock for network error scenarios
 */
export function mockConnectionApiNetworkError() {
  throw new Error('Network Error')
}

// ============================================================================
// Slow Query API Mocks
// ============================================================================

/**
 * Mock for slowQueryApi
 * @param success - whether to return success or error
 * @param data - optional mock data to return on success
 */
export function mockSlowQueryApi(success: boolean = true, data?: SlowQuery[]) {
  const slowQueryApi = {
    getList: vi.fn().mockImplementation(async (connectionId: number, params?: any) => {
      if (success) {
        const totalCount = data?.length || 3
        return {
          total: totalCount,
          items: data || mockSlowQueryList(totalCount)
        }
      }
      throw new Error('Failed to fetch slow queries')
    }),

    getDetail: vi.fn().mockImplementation(async (queryId: number) => {
      if (success) {
        return mockSlowQueryDetail({ id: queryId })
      }
      throw new Error('Failed to fetch slow query ' + queryId)
    }),

    analyze: vi.fn().mockImplementation(async (sql: string, connectionId: number) => {
      if (success) {
        return {
          execution_plan: mockExplainResultList(2),
          suggestions: mockOptimizationSuggestions(3)
        }
      }
      throw new Error('Failed to analyze query')
    }),

    getOptimizationSuggestions: vi.fn().mockImplementation(async (queryId: number) => {
      if (success) {
        return mockOptimizationSuggestions(3)
      }
      throw new Error('Failed to fetch suggestions for query ' + queryId)
    }),

    getHistory: vi.fn().mockImplementation(async (queryHash: string, params?: any) => {
      if (success) {
        return {
          query_hash: queryHash,
          executions: mockSlowQueryHistory(5)
        }
      }
      throw new Error('Failed to fetch slow query history')
    }),

    markResolved: vi.fn().mockImplementation(async (queryId: number, note?: string) => {
      if (success) {
        return undefined
      }
      throw new Error('Failed to mark query ' + queryId + ' as resolved')
    }),

    delete: vi.fn().mockImplementation(async (queryId: number) => {
      if (success) {
        return undefined
      }
      throw new Error('Failed to delete query ' + queryId)
    }),

    batchDelete: vi.fn().mockImplementation(async (queryIds: number[]) => {
      if (success) {
        return undefined
      }
      throw new Error('Failed to batch delete queries')
    }),

    batchResolve: vi.fn().mockImplementation(async (queryIds: number[], note?: string) => {
      if (success) {
        return undefined
      }
      throw new Error('Failed to batch resolve queries')
    }),
  }

// ============================================================================
// EXPLAIN API Mocks
// ============================================================================

/**
 * Mock for explainApi
 * @param success - whether to return success or error
 * @param data - optional mock data to return on success
 */
export function mockExplainApi(success: boolean = true, data?: ExplainResult[]) {
  const explainApi = {
    explain: vi.fn().mockImplementation(async (connectionId: number, data: ExplainRequest) => {
      if (success) {
        return data || mockExplainResultList(2)
      }
      throw new Error('Failed to analyze query')
    }),

    analyzeExecution: vi.fn().mockImplementation(async (connectionId: number, sql: string, databaseName?: string) => {
      if (success) {
        return mockExplainAnalyzeResultList(2)
      }
      throw new Error('Failed to execute EXPLAIN ANALYZE')
    }),

    getIndexSuggestions: vi.fn().mockImplementation(async (connectionId: number, sql: string, tableName?: string) => {
      if (success) {
        return {
          suggestions: mockIndexSuggestions(3)
        }
      throw new Error('Failed to fetch index suggestions')
    }),
  }

// ============================================================================
// Alert API Mocks
// ============================================================================

/**
 * Mock for alertApi
 * @param success - whether to return success or error
 * @param data - optional mock data to return on success
 */
export function mockAlertApi(success: boolean = true, data?: AlertRule[]) {
  const alertApi = {
    getRules: vi.fn().mockImplementation(async (params?: any) => {
      if (success) {
        return data || mockAlertRuleList(3)
      }
      throw new Error('Failed to fetch alert rules')
    }),

    getRuleById: vi.fn().mockImplementation(async (ruleId: number) => {
      if (success) {
        return mockAlertRule({ id: ruleId })
      }
      throw new Error('Failed to fetch alert rule ' + ruleId)
    }),

    createRule: vi.fn().mockImplementation(async (data: AlertRuleCreate) => {
      if (success) {
        return mockAlertRule({ ...data, id: 1 })
      }
      throw new Error('Failed to create alert rule')
    }),

    updateRule: vi.fn().mockImplementation(async (ruleId: number, data: AlertRuleUpdate) => {
      if (success) {
        return mockAlertRule({ id: ruleId, ...data })
      }
      throw new Error('Failed to update alert rule ' + ruleId)
    }),

    deleteRule: vi.fn().mockImplementation(async (ruleId: number) => {
      if (success) {
        return undefined
      }
      throw new Error('Failed to delete alert rule ' + ruleId)
    }),

    toggleRule: vi.fn().mockImplementation(async (ruleId: number, enabled: boolean) => {
      if (success) {
        return undefined
      }
      throw new Error('Failed to toggle alert rule ' + ruleId)
    }),

    getHistory: vi.fn().mockImplementation(async (params?: any) => {
      if (success) {
        return mockAlertHistoryList(3)
      }
      throw new Error('Failed to fetch alert history')
    }),

    getStatistics: vi.fn().mockImplementation(async (connectionId: number) => {
      if (success) {
        return mockAlertStatistics(connectionId)
      }
      throw new Error('Failed to fetch alert statistics for connection ' + connectionId)
    }),

    resolveAlert: vi.fn().mockImplementation(async (alertId: number, note?: string) => {
      if (success) {
        return undefined
      }
      throw new Error('Failed to resolve alert ' + alertId)
    }),

    batchResolve: vi.fn().mockImplementation(async (alertIds: number[], note?: string) => {
      if (success) {
        return undefined
      }
      throw new Error('Failed to batch resolve alerts')
    }),

    batchDelete: vi.fn().mockImplementation(async (alertIds: number[]) => {
      if (success) {
        return undefined
      }
      throw new Error('Failed to batch delete alerts')
    }),
  }

// ============================================================================
// Monitoring API Mocks
// ============================================================================

/**
 * Mock for monitoringApi
 * @param success - whether to return success or error
 * @param data - optional mock data to return on success
 */
export function mockMonitoringApi(success: boolean = true, data?: PerformanceMetrics) {
  const monitoringApi = {
    getMetrics: vi.fn().mockImplementation(async (connectionId: number, params?: any) => {
      if (success) {
        return data || mockPerformanceMetrics()
      }
      throw new Error('Failed to fetch metrics')
    }),

    startAutoCollection: vi.fn().mockImplementation(async (connectionId: number, config?: AutoCollectionConfig) => {
      if (success) {
        return undefined
      }
      throw new Error('Failed to start auto collection')
    }),

    stopAutoCollection: vi.fn().mockImplementation(async (collectionId: number) => {
      if (success) {
        return undefined
      }
      throw new Error('Failed to stop auto collection')
    }),

    getRealtimeMetrics: vi.fn().mockImplementation(async (connectionId: number) => {
      if (success) {
        return data || mockPerformanceMetrics()
      }
      throw new Error('Failed to fetch realtime metrics')
    }),

    getMetricsHistory: vi.fn().mockImplementation(async (connectionId: number, params: any) => {
      if (success) {
        return {
          connection_id: connectionId,
          start_time: '2024-01-01T00:00:00Z',
          end_time: '2024-01-02T00:00:00:00Z',
          interval: 3600,
          data: [mockPerformanceMetrics(), mockPerformanceMetrics()]
        }
      }
      throw new Error('Failed to fetch metrics history')
    }),
  }

// ============================================================================
// Mock Data Generators
// ============================================================================

function mockConnectionList(count: number): Connection[] {
  const connections: Connection[] = []
  for (let i = 1; i <= count; i++) {
    connections.push({
      id: i,
      name: 'Test Connection ' + i,
      host: 'localhost',
      port: 3306,
      username: 'root',
      password_encrypted: 'encrypted_password',
      database_name: 'test_db_' + i,
      is_active: true,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    })
  }
  return connections
}

function mockConnection(overrides: Partial<Connection> = {}): Connection {
  return {
    id: 1,
    name: 'Test Connection',
    host: 'localhost',
    port: 3306,
    username: 'root',
    password_encrypted: 'encrypted_password',
    database_name: 'test_db',
    is_active: true,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00Z',
    ...overrides,
  }
}

function mockConnectionTestResult(): ConnectionTestResult {
  return {
    status: 'success',
    message: 'Connection successful',
    latency: 10.5,
  }
}

function mockSlowQueryList(count: number): SlowQuery[] {
  const queries: SlowQuery[] = []
  for (let i = 1; i <= count; i++) {
    queries.push({
      id: i,
      query_hash: 'hash_' + i,
      sql_digest: 'SELECT * FROM users WHERE id = ?',
      full_sql: 'SELECT * FROM users WHERE id = 1',
      database_name: 'test_db',
      table_name: 'users',
      query_time: 1.5 + i * 0.1,
      lock_time: 0.01,
      rows_sent: 10,
      rows_examined: 100,
      execution_count: 5,
      timestamp: '2024-01-01T00:00:00Z',
    })
  }
  return queries
}

function mockSlowQueryDetail(overrides: Partial<SlowQueryDetail> = {}): SlowQueryDetail {
  return {
    id: 1,
    query_hash: 'hash_1',
    sql_digest: 'SELECT * FROM users WHERE id = ?',
    database_name: 'test_db',
    table_name: 'users',
    query_time: 1.5,
    lock_time: 0.01,
    rows_sent: 10,
    rows_examined: 100,
    execution_count: 5,
    timestamp: '2024-01-01T00:00:00Z',
    ...overrides,
  }
}

function mockSlowQueryHistory(count: number): SlowQueryHistory {
  return {
    query_hash: 'hash_1',
    executions: Array.from({ length: count }, (_, i) => ({
      timestamp: '2024-01-01T' + i.toString().padStart(2, '0') + ':00:00:00Z',
      query_time: 1.5 + i * 0.1,
      rows_examined: 100 + i * 10,
    })
  }
}

function mockExplainResultList(count: number): ExplainResult[] {
  const results: ExplainResult[] = []
  for (let i = 1; i <= count; i++) {
    results.push({
      id: i,
      select_type: i === 1 ? 'eq_ref' : 'range',
      table: 'users',
      partitions: 'p1,p2',
      type: 'ref',
      possible_keys: ['PRIMARY', 'idx_username'],
      key: 'PRIMARY',
      key_len: 4,
      ref: 'const',
      rows: 100 - i * 10,
      filtered: 100,
      Extra: 'Using where condition',
    })
  }
  return results
}

function mockExplainAnalyzeResultList(count: number): ExplainAnalyzeResult[] {
  const results: ExplainAnalyzeResult[] = []
  for (let i = 1; i <= count; i++) {
    results.push({
      id: i,
      select_type: i === 1 ? 'eq_ref' : 'range',
      table: 'users',
      partitions: 'p1,p2',
      type: 'ref',
      possible_keys: ['PRIMARY', 'idx_username'],
      key: 'PRIMARY',
      key_len: 4,
      ref: 'const',
      rows: 100 - i * 10,
      filtered: 100,
      Extra: 'Using where condition',
      execution_time: 0.5 + i * 0.1,
      query_cost: 150 + i * 10,
      table_rows: 1000,
    })
  }
  return results
}

function mockOptimizationSuggestions(count: number): OptimizationSuggestion[] {
  const suggestions: OptimizationSuggestion[] = []
  const types = ['index', 'query_rewrite', 'schema', 'config'] as const
  for (let i = 1; i <= count; i++) {
    suggestions.push({
      type: types[i % 4],
      priority: i % 2 === 0 ? 'high' : 'medium',
      title: 'Optimization ' + i,
      description: 'Optimize query ' + i,
      example_before: 'SELECT * FROM users',
      example_after: 'SELECT id, name FROM users',
      estimated_improvement: '${10 * i} + '%',
    })
  }
  return suggestions
}

function mockIndexSuggestions(count: number): IndexSuggestion[] {
  const suggestions: IndexSuggestion[] = []
  for (let i = 1; i <= count; i++) {
    suggestions.push({
      type: i % 2 === 0 ? 'add' : 'remove',
      index_name: 'idx_' + i,
      table_name: 'users',
      columns: ['id', 'name'],
      reason: 'Reason for suggestion ' + i,
      estimated_improvement: '${10 * i} + '%',
    })
  }
  return suggestions
}

function mockAlertRuleList(count: number): AlertRule[] {
  const rules: AlertRule[] = []
  for (let i =   for (let i = 1; i <= count; i++) {
    rules.push({
      id: i,
      connection_id: 1,
      name: 'Alert Rule ' + i,
      rule_type: 'cpu_usage',
      condition: 'greater',
      threshold: 90 + i * 5,
      comparison: 'greater',
      severity: i % 3 === 0 ? 'critical' : i % 3 === 1 ? 'warning' : 'info',
      enabled: true,
      notification_channels: ['email'],
      created_at: '2024-01-01T00:00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    })
  }
  return rules
}

function mockAlertRule(overrides: Partial<AlertRule> = {}): AlertRule {
  return {
    id: 1,
    connection_id: 1,
    name: 'Alert Rule 1',
    rule_type: 'cpu_usage',
    condition: 'greater',
    threshold: 90,
    comparison: 'greater',
    severity: 'warning',
    enabled: true,
    notification_channels: ['email'],
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    ...overrides,
  }
}

function mockAlertHistoryList(count: number): AlertHistory[] {
  const history: AlertHistory[] = []
  for (let i = 1; i <= count; i++) {
    history.push({
      id: i,
      connection_id: 1,
      rule_id: i,
      rule_name: 'Alert Rule ' + i,
      severity: i % 3 === 0 ? 'critical' : i % 3 === 1 ? 'warning' : 'info',
      message: 'Alert message ' + i,
      triggered_at: '2024-01-01T00:00:00Z',
      resolved: i % 2 === 0,
      resolved_at: i % 2 === 0 ? '2024-01-01T00:00:00:00Z' : undefined,
      resolved_note: i % 2 === 0 ? 'Note' : undefined,
    })
  }
  return history
}

function mockAlertStatistics(connectionId: number): AlertStatistics {
  return {
    connection_id: connectionId,
    total_alerts: 15,
    critical_alerts: 3,
    warning_alerts: 8,
    info_alerts: 4,
    resolved_alerts: 10,
    unresolved_alerts: 5,
    most_frequent_rules: [
      {
        rule_id: 1,
        rule_name: 'CPU Usage Alert',
        trigger_count: 8,
      },
      {
        rule_id: 2,
        rule_name: 'Memory Usage Alert',
        trigger_count: 7,
      },
    ],
    time_range: 'Last 7 days',
  }
}

function mockPerformanceMetrics(): PerformanceMetrics {
  return {
    connection_id: 1,
    qps: 150,
    tps: 80,
    read_qps: 100,
    write_qps: 50,
    connections: {
      current: 10,
      max: 100,
      active: 8,
    },
    buffer_pool_hit_rate: 95.5,
    queries: {
      select: 100,
      insert: 40,
      update: 30,
      delete: 10,
    },
    system: {
      uptime: 3600,
      thread_count: 4,
    },
    timestamp: '2024-01-01T00:00:00:00Z',
  }
}
EOF