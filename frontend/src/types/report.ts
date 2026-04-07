export interface Report {
  id: number
  connection_id: number
  connection_name: string
  report_type: 'daily' | 'weekly' | 'monthly' | 'custom'
  start_time: string
  end_time: string
  status: 'generating' | 'completed' | 'failed'
  generated_at: string
  file_size: number
  include_metrics: boolean
  include_slow_queries: boolean
  include_index_usage: boolean
  include_alerts: boolean
  note?: string
}

export interface ReportGenerate {
  connection_id: number
  report_type: 'daily' | 'weekly' | 'monthly' | 'custom'
  start_time: string
  end_time: string
  include_metrics: boolean
  include_slow_queries: boolean
  include_index_usage: boolean
  include_alerts: boolean
  note?: string
}

export interface ReportDetail extends Report {
  metrics_summary: MetricsSummary
  slow_queries: SlowQuerySummary[]
  index_usage: IndexUsageSummary
  alert_summary: AlertSummary
  optimization_suggestions: OptimizationSuggestion[]
}

export interface MetricsSummary {
  avg_qps: number
  max_qps: number
  avg_tps: number
  max_tps: number
  avg_connections: number
  max_connections: number
  avg_buffer_pool_hit_rate: number
  total_slow_queries: number
}

export interface SlowQuerySummary {
  query_hash: string
  sql_digest: string
  execution_count: number
  avg_query_time: number
  max_query_time: number
  total_rows_examined: number
  optimization_potential: string
}

export interface IndexUsageSummary {
  total_indexes: number
  unused_indexes: number
  low_usage_indexes: number
  high_usage_indexes: number
  recommendations: string[]
}

export interface AlertSummary {
  total_alerts: number
  critical_alerts: number
  warning_alerts: number
  info_alerts: number
  resolved_alerts: number
  top_alert_rules: TopAlertRule[]
}

export interface TopAlertRule {
  rule_id: number
  rule_name: string
  trigger_count: number
}

export interface OptimizationSuggestion {
  category: 'index' | 'query' | 'schema' | 'config'
  priority: 'high' | 'medium' | 'low'
  title: string
  description: string
  impact: string
  estimated_improvement: string
}
