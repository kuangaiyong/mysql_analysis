/**
 * MySQL配置分析相关类型
 */

export interface ConfigViolation {
  severity: 'CRIT' | 'WARN' | 'INFO'
  param: string
  current_value: string
  recommended_value: string
  impact: string
  description?: string
  fix_sql?: string
  fix_config?: string
  source?: 'file' | 'runtime' | 'both'
}

export interface ConfigSummary {
  config_source: string
  total_params: number
  file_params: number
  runtime_params: number
  mysql_version: string
}

export interface ConfigAnalysis {
  id: number
  connection_id: number
  analysis_timestamp: string
  health_score: number
  critical_count: number
  warning_count: number
  info_count: number
  violations: ConfigViolation[]
  config_summary: ConfigSummary
  mysql_version: string
}

export interface ConfigHistoryItem {
  id: number
  analysis_timestamp: string
  health_score: number
  critical_count: number
  warning_count: number
  info_count: number
}

export interface ConfigHistory {
  total: number
  analyses: ConfigHistoryItem[]
}

export interface ConfigDiffItem {
  param: string
  value_1: string | null
  value_2: string | null
  is_different: boolean
  source_1: string | null
  source_2: string | null
}

export interface ConfigComparison {
  comparison_type: 'time' | 'instance'
  timestamp_1: string | null
  timestamp_2: string | null
  connection_id_1: number | null
  connection_id_2: number | null
  total_params: number
  different_params: number
  same_params: number
  diffs: ConfigDiffItem[]
}

export interface AnalysisProgress {
  analysis_id: number
  status: 'started' | 'in_progress' | 'completed'
  progress: number
  message: string
}

export interface ConfigAlertMessage {
  type: 'config_alert' | 'config_completion'
  connection_id: number
  analysis_id: number
  severity: 'CRIT' | 'INFO'
  health_score: number
  message: string
  top_issue: string | null
  timestamp: string
}
