/**
 * 测试数据生成器
 * 
 * 提供可复用的测试数据，遵循现有E2E测试数据模式
 */

// ============================================================================
// 连接测试数据
// ============================================================================

export const testConnections = [
  {
    id: 1,
    name: 'Test Connection 1',
    host: 'localhost',
    port: 3306,
    username: 'root',
    password_encrypted: 'encrypted_password',
    database_name: 'test_db',
    connection_pool_size: 10,
    is_active: true,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 2,
    name: 'Test Connection 2',
    host: 'localhost',
    port: 3306,
    username: 'root',
    password_encrypted: 'encrypted_password',
    database_name: 'test_db',
    connection_pool_size: 20,
    is_active: true,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 3,
    name: 'Inactive Connection',
    host: 'offline.example.com',
    port: 3306,
    username: 'app_user',
    password_encrypted: 'encrypted_password',
    database_name: 'offline_db',
    connection_pool_size: 15,
    is_active: false,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
]

export const mockConnection = testConnections[0]
export const mockConnectionList = (count = 3) => testConnections.slice(0, count)

// ============================================================================
// 慢查询测试数据
// ============================================================================

export const testSlowQueries = [
  {
    id: 1,
    connection_id: 1,
    query_hash: 'abc123',
    sql_digest: 'SELECT * FROM users WHERE id = ?',
    full_sql: 'SELECT * FROM users WHERE id = 1',
    query_time: 5.2,
    lock_time: 0.1,
    rows_examined: 10000,
    rows_sent: 500,
    database_name: 'test_db',
    timestamp: '2024-01-01T10:00:00Z',
    execution_count: 10,
    fingerprint_id: 1,
  },
  {
    id: 2,
    connection_id: 1,
    query_hash: 'def456',
    sql_digest: 'SELECT * FROM orders WHERE status = ?',
    full_sql: 'SELECT * FROM orders WHERE status = 1',
    query_time: 8.5,
    lock_time: 0.2,
    rows_examined: 50000,
    rows_sent: 1000,
    database_name: 'test_db',
    timestamp: '2024-01-01T11:00:00Z',
    execution_count: 5,
    fingerprint_id: 2,
  },
  {
    id: 3,
    connection_id: 2,
    query_hash: 'ghi789',
    sql_digest: 'SELECT * FROM products LIMIT 100',
    full_sql: 'SELECT * FROM products LIMIT 100',
    query_time: 12.3,
    lock_time: 0.5,
    rows_examined: 100000,
    rows_sent: 5000,
    database_name: 'test_db',
    timestamp: '2024-01-01T12:00:00Z',
    execution_count: 3,
    fingerprint_id: 3,
  },
]

export const mockSlowQuery = testSlowQueries[0]
export const mockSlowQueryList = (count = 2) => testSlowQueries.slice(0, count)

// ============================================================================
// 告警规则测试数据
// ============================================================================

export const testAlertRules = [
  {
    id: 1,
    connection_id: 1,
    rule_name: 'High CPU Usage',
    metric_name: 'cpu_usage',
    condition_operator: '>',
    threshold_value: 80,
    time_window: 300,
    severity: 'high',
    is_enabled: true,
    notification_channels: ['email'],
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 2,
    connection_id: 1,
    rule_name: 'High Memory Usage',
    metric_name: 'memory_usage',
    condition_operator: '>',
    threshold_value: 85,
    time_window: 300,
    severity: 'medium',
    is_enabled: true,
    notification_channels: ['email', 'webhook'],
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 3,
    connection_id: 2,
    rule_name: 'Slow Query Threshold',
    metric_name: 'slow_query_time',
    condition_operator: '>',
    threshold_value: 5.0,
    time_window: 600,
    severity: 'high',
    is_enabled: false,
    notification_channels: ['email'],
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
]

export const mockAlertRule = testAlertRules[0]
export const mockAlertRuleList = (count = 2) => testAlertRules.slice(0, count)

// ============================================================================
// 告警历史测试数据
// ============================================================================

export const testAlertHistory = [
  {
    id: 1,
    alert_rule_id: 1,
    connection_id: 1,
    alert_time: '2024-01-01T10:00:00Z',
    metric_value: 85.5,
    message: 'CPU usage exceeded threshold',
    status: 'active',
    resolved_at: null,
  },
  {
    id: 2,
    alert_rule_id: 1,
    connection_id: 1,
    alert_time: '2024-01-01T11:00:00Z',
    metric_value: 88.0,
    message: 'Memory usage exceeded threshold',
    status: 'resolved',
    resolved_at: '2024-01-01T12:00:00Z',
  },
  {
    id: 3,
    alert_rule_id: 2,
    connection_id: 2,
    alert_time: '2024-01-01T12:30:00Z',
    metric_value: 6.5,
    message: 'Slow query threshold exceeded',
    status: 'active',
    resolved_at: null,
  },
]

export const mockAlertHistory = testAlertHistory[0]
export const mockAlertHistoryList = (count = 2) => testAlertHistory.slice(0, count)

// ============================================================================
// 性能指标测试数据
// ============================================================================

export const testMetrics = {
  qps_read: 150,
  qps_write: 80,
  tps_read: 50,
  tps_write: 30,
  connections: 10,
  buffer_pool_hit_rate: 95.5,
  buffer_pool_size: 128,
  timestamp: '2024-01-01T10:00:00Z',
}

export const mockMetricsList = [
  testMetrics,
  {
    ...testMetrics,
    timestamp: '2024-01-01T10:05:00Z',
    qps_read: 145,
    qps_write: 75,
  },
  {
    ...testMetrics,
    timestamp: '2024-01-01T10:10:00Z',
    qps_read: 140,
    qps_write: 70,
  },
]

export const mockMetrics = testMetrics
export const mockMetricsHistory = (count = 3) => mockMetricsList.slice(0, count)

// ============================================================================
// EXPLAIN结果测试数据
// ============================================================================

export const testExplainResult = {
  id: '1',
  select_type: 'SIMPLE',
  table: 'users',
  type: 'ALL',
  possible_keys: null,
  key: 'PRIMARY',
  key_len: 4,
  ref: null,
  rows: 1,
  filtered_rows: 1,
  Extra: null,
}

export const testExplainResults = [testExplainResult]

// ============================================================================
// 索引建议测试数据
// ============================================================================

export const testIndexSuggestion = {
  id: 1,
  connection_id: 1,
  table_name: 'users',
  column_names: ['id', 'name', 'email'],
  index_type: 'BTREE',
  suggestion_type: 'create',
  estimated_rows_reduction: 50,
  estimated_time_improvement: 30,
  confidence_level: 'high',
  status: 'pending',
  reason: '为提升查询性能，建议添加复合索引',
  sql_statement: 'CREATE INDEX idx_user_name_email ON users(name, email)',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
}

export const testIndexSuggestions = [testIndexSuggestion]
export const mockIndexSuggestionList = (count = 1) => testIndexSuggestions.slice(0, count)

// ============================================================================
// 便捷函数
// ============================================================================

/**
 * 随机生成测试数据
 */
export const generateTestData = {
  connection: () => ({
    id: Math.floor(Math.random() * 10000),
    name: `Test Connection ${Math.floor(Math.random() * 100)}`,
    host: 'test.example.com',
    port: 3306,
    username: 'test_user',
    password_encrypted: 'encrypted_password',
    database_name: 'test_db',
    connection_pool_size: 10,
    is_active: true,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  }),

  slowQuery: () => ({
    id: Math.floor(Math.random() * 10000),
    connection_id: 1,
    query_hash: Math.random().toString(36).substring(0, 8),
    sql_digest: 'SELECT * FROM test_table WHERE id = ?',
    full_sql: 'SELECT * FROM test_table WHERE id = 1',
    query_time: Math.random() * 10,
    lock_time: Math.random() * 1,
    rows_examined: Math.floor(Math.random() * 10000),
    rows_sent: Math.floor(Math.random() * 1000),
    database_name: 'test_db',
    timestamp: new Date().toISOString(),
    execution_count: Math.floor(Math.random() * 10) + 1,
    fingerprint_id: 1,
  }),

  alertRule: () => ({
    id: Math.floor(Math.random() * 10000),
    connection_id: 1,
    rule_name: `Test Rule ${Math.floor(Math.random() * 100)}`,
    metric_name: ['cpu_usage', 'memory_usage', 'slow_query_time'][Math.floor(Math.random() * 3)],
    condition_operator: ['>', '>=', '<', '!='][Math.floor(Math.random() * 4)],
    threshold_value: Math.floor(Math.random() * 100),
    time_window: [300, 600, 900][Math.floor(Math.random() * 3)],
    severity: ['low', 'medium', 'high'][Math.floor(Math.random() * 3)],
    is_enabled: Math.random() > 0.5,
    notification_channels: ['email', 'webhook'].slice(0, Math.floor(Math.random() * 2) + 1),
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  }),
}

/**
 * 创建测试数据生成器
 */
export const testDataGenerator = {
  createConnection: (data?: Partial<typeof testConnections[0]>) => ({
    ...testConnections[0],
    ...data,
    id: Math.floor(Math.random() * 10000),
  }),

  createSlowQuery: (data?: Partial<typeof testSlowQueries[0]>) => ({
    ...testSlowQueries[0],
    ...data,
    id: Math.floor(Math.random() * 10000),
  }),

  createAlertRule: (data?: Partial<typeof testAlertRules[0]>) => ({
    ...testAlertRules[0],
    ...data,
    id: Math.floor(Math.random() * 10000),
  }),
}
