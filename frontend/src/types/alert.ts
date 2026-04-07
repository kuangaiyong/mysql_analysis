export interface AlertRule {
  id: number
  connection_id: number
  name: string
  rule_type: 'cpu_usage' | 'memory_usage' | 'connection_count' | 'slow_query' | 'disk_usage' | 'replication_lag'
  condition: string
  threshold: number
  comparison: 'greater' | 'less' | 'equal'
  severity: 'info' | 'warning' | 'critical'
  enabled: boolean
  notification_channels: string[]
  created_at: string
  updated_at: string
}

export interface AlertRuleCreate {
  connection_id: number
  name: string
  rule_type: string
  condition: string
  threshold: number
  comparison: string
  severity: string
  notification_channels: string[]
}

export interface AlertRuleUpdate {
  name?: string
  condition?: string
  threshold?: number
  comparison?: string
  severity?: string
  notification_channels?: string[]
  enabled?: boolean
}

export interface AlertHistory {
  id: number
  connection_id: number
  rule_id: number
  rule_name: string
  severity: 'info' | 'warning' | 'critical'
  message: string
  triggered_at: string
  resolved: boolean
  resolved_at?: string
  resolved_note?: string
}

export interface AlertStatistics {
  connection_id: number
  total_alerts: number
  critical_alerts: number
  warning_alerts: number
  info_alerts: number
  resolved_alerts: number
  unresolved_alerts: number
  most_frequent_rules: MostFrequentRule[]
  time_range: string
}

export interface MostFrequentRule {
  rule_id: number
  rule_name: string
  trigger_count: number
}
