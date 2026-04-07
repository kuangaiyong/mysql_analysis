/**
 * 调优相关类型定义
 * 与后端 schemas/tuning.py 对应
 */

// SQL改写建议
export interface SQLRewriteSuggestion {
  type: string
  priority: string
  title: string
  description: string
  sql_before?: string
  sql_after?: string
  expected_improvement: string
}

export interface SQLRewriteResponse {
  sql: string
  suggestions: SQLRewriteSuggestion[]
  has_suggestions?: boolean
}

// InnoDB调优建议
export interface InnoDBTuningRecommendation {
  category: string
  param: string
  current_value: string
  recommended_value: string
  reason: string
  impact: string
  priority: string
  sql_statement: string
}

export interface InnoDBTuningResponse {
  connection_id: number
  recommendations: InnoDBTuningRecommendation[]
  buffer_pool_hit_rate?: number
}

// 索引建议
export interface IndexSuggestion {
  type: string
  table: string
  columns: string[]
  reason: string
  sql: string
  priority: string
  estimated_improvement: string
  rows_examined?: number
}

export interface IndexSuggestionResponse {
  connection_id: number
  sql: string
  database?: string
  recommendations: IndexSuggestion[]
  has_recommendations?: boolean
}

// 综合调优
export interface ComprehensiveTuningResponse {
  connection_id: number
  database_name?: string
  suggestions: Array<{
    category: string
    title: string
    items: Array<{
      param?: string
      current_value?: string
      recommended_value?: string
      reason: string
      priority: string
    }>
  }>
  summary: {
    total_categories: number
    high_priority_count: number
  }
}
