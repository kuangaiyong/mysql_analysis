/**
 * Index Suggestions Type Definitions
 */

/**
 * Index suggestion for query optimization
 */
export interface IndexSuggestion {
  id: number
  connection_id: number
  table_name: string
  column_names: string[]
  index_type: string
  confidence: 'high' | 'medium' | 'low'
  current_rows_examined: number
  estimated_rows_after: number
  rows_reduction_percent: number
  time_improvement_percent: number
  create_statement: string
  status: 'pending' | 'accepted' | 'rejected'
  created_at: string
  updated_at: string
  rejected_reason?: string
}

/**
 * Request to analyze queries and generate index suggestions
 */
export interface IndexAnalysisRequest {
  connection_id: number
  query_ids?: number[]
  table_name?: string
}

/**
 * Response from index analysis
 */
export interface IndexAnalysisResponse {
  suggestions: IndexSuggestion[]
  analysis_summary: {
    total_queries_analyzed: number
    total_suggestions: number
    high_confidence_count: number
  }
}

/**
 * Request to create an index based on suggestion
 */
export interface CreateIndexRequest {
  suggestion_id: number
  execute_immediately?: boolean
}

/**
 * Request to reject an index suggestion
 */
export interface RejectSuggestionRequest {
  reason: string
}
