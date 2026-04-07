export interface ExplainRequest {
  sql: string
  analyze_type?: 'traditional' | 'json' | 'tree' | 'flowchart'
  database_name?: string
}

export interface ExplainResult {
  id: number
  select_type: string
  table: string
  partitions: string | null
  type: string
  possible_keys: string[]
  key: string | null
  key_len: number | null
  ref: string | null
  rows: number
  filtered: number | null
  Extra: string | null
  children?: ExplainResult[]
}

export interface ExplainAnalyzeResult extends ExplainResult {
  execution_time?: number
  query_cost?: number
  table_rows?: number
}

export interface IndexSuggestion {
  type: 'add' | 'remove' | 'modify'
  index_name: string
  table_name: string
  columns: string[]
  reason: string
  estimated_improvement?: string
}

export interface ExplainAnalysis {
  execution_time?: number
  query_cost?: number
  total_rows?: number
  efficiency_score: 'A' | 'B' | 'C' | 'D' | 'E'
  suggestions: IndexSuggestion[]
}
