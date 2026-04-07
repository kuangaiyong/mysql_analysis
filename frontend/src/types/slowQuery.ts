export interface SlowQuery {
  id: number
  query_hash: string
  sql_digest: string
  full_sql?: string
  database_name: string
  table_name?: string
  query_time: number
  lock_time: number
  rows_sent: number
  rows_examined: number
  rows_affected?: number
  execution_count: number
  last_seen?: string
  timestamp?: string
  resolved?: number
  resolved_at?: string
  resolved_note?: string
  scan_efficiency?: number
  anomaly?: AnomalyInfo
}

export interface AnomalyInfo {
  is_anomaly: boolean
  deviation?: number
  baseline_mean?: number
  baseline_std?: number
  status: 'active' | 'insufficient_data'
}

export interface Baseline {
  status: 'active' | 'insufficient_data'
  mean?: number
  std?: number
  threshold?: number
  sample_count: number
  message?: string
}

export interface SlowQueryDetail extends SlowQuery {
  connection_id: number
  execution_plan?: ExplainResult
  optimization_suggestions?: OptimizationSuggestion[]
  performance_score: 'A' | 'B' | 'C' | 'D' | 'E'
  performance_bottlenecks: string[]
  anomaly?: AnomalyInfo
}

export interface ExplainResult {
  id: number
  select_type: string
  table: string
  partitions: string
  type: string
  possible_keys: string[]
  key: string
  key_len: number
  ref: string
  rows: number
  filtered: number
  Extra: string
  children?: ExplainResult[]
}

export interface OptimizationSuggestion {
  type: string
  priority: 'high' | 'medium' | 'low'
  title: string
  description: string
  example_before?: string
  example_after?: string
  sql_after?: string
  estimated_improvement?: string
  expected_improvement?: string
  actionable?: ActionableInfo
}

export interface ActionableInfo {
  sql: string
  estimated_size?: string
  risk?: string
}

export interface SlowQueryHistory {
  query_hash: string
  executions: {
    timestamp: string
    query_time: number
    rows_examined: number
  }[]
}

export interface SlowQueryStats {
  total_count: number
  avg_query_time: number
  max_query_time: number
  total_rows_examined: number
  total_rows_sent: number
  percentiles?: {
    p50: number
    p90: number
    p99: number
  }
}

export interface TimeDistributionItem {
  time: string
  count: number
}

export interface TimeDistribution {
  granularity: 'hour' | 'day'
  distribution: TimeDistributionItem[]
}
