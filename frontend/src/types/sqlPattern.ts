export interface PatternResult {
  type: string
  priority: 'critical' | 'high' | 'medium' | 'low'
  title: string
  description: string
  sql_before: string
  sql_after: string | null
  expected_improvement: string
}

export interface PatternSummary {
  total_patterns: number
  critical_count: number
  high_count: number
  medium_count: number
  low_count: number
}

export interface PatternDetectResponse {
  patterns: PatternResult[]
  summary: PatternSummary
}

export interface PatternInfo {
  type: string
  priority: string
  title: string
  description: string
}
