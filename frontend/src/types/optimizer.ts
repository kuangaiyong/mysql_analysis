/**
 * 优化器追踪分析类型定义
 */

export interface IndexSelection {
  chosen_index: string | null
  considered_indexes: string[]
  choice_reason: string
  rows_examined: number
}

export interface JoinOrderItem {
  table: string
  access_type: string
  key: string | null
  rows: number | null
  cost: number | null
}

export interface CostEstimation {
  estimated_rows: number
  estimated_cost: number
  read_cost: number | null
  eval_cost: number | null
}

export interface OptimizerRecommendation {
  type: string
  description: string
  sql: string | null
  priority: 'high' | 'medium' | 'low'
}

export interface OptimizerTraceResponse {
  index_selection: IndexSelection
  join_order: JoinOrderItem[]
  cost_estimation: CostEstimation
  recommendations: OptimizerRecommendation[]
}

export interface OptimizerTraceRequest {
  sql: string
  database_name?: string
}
