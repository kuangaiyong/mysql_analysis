export interface Table {
  table_name: string
  table_type: 'BASE TABLE' | 'VIEW' | 'SYSTEM VIEW'
  engine: string
  row_format: string
  table_rows: number
  data_length: number
  index_length: number
  data_free: number
  auto_increment: number | null
  create_time: string
  update_time: string
  comment: string
}

export interface Column {
  column_name: string
  ordinal_position: number
  column_default: string | null
  is_nullable: boolean
  data_type: string
  character_maximum_length: number | null
  numeric_precision: number | null
  numeric_scale: number | null
  character_set_name: string | null
  collation_name: string | null
  column_type: string
  column_key: 'PRI' | 'UNI' | 'MUL' | ''
  extra: string
  comment: string
}

export interface TableStructure {
  table_name: string
  columns: Column[]
  indexes: IndexInfo[]
  foreign_keys: ForeignKey[]
  engine: string
  charset: string
  collation: string
  comment: string
}

export interface IndexInfo {
  index_name: string
  column_name: string
  index_type: string
  unique: boolean
  primary: boolean
}

export interface ForeignKey {
  constraint_name: string
  column_name: string
  referenced_table_name: string
  referenced_column_name: string
  on_update: string
  on_delete: string
}

export interface TableSize {
  table_name: string
  data_size: number
  index_size: number
  total_size: number
  data_size_mb: number
  index_size_mb: number
  total_size_mb: number
}

export interface TableStats {
  table_name: string
  row_count: number
  avg_row_length: number
  data_length: number
  index_length: number
  max_data_length: number
  max_index_length: number
  data_free: number
  auto_increment: number
  create_time: string
  update_time: string
  last_analyze_time: string
}

export interface HealthScoreDimension {
  name: string
  score: number
  weight: number
  max_score: number
  details?: string
}

export interface TableHealthScore {
  table_name: string
  total_score: number
  grade: string
  dimensions: HealthScoreDimension[]
  calculated_at: string
}

export interface PerformanceIssue {
  issue_type: string
  severity: 'critical' | 'warning' | 'info'
  description: string
  impact: string
  metric_value?: number
  threshold?: number
}

export interface TableDiagnosis {
  table_name: string
  issues: PerformanceIssue[]
  issue_count: number
  critical_count: number
  warning_count: number
  analyzed_at: string
}

export interface OptimizationRecommendation {
  title: string
  description: string
  priority: 'high' | 'medium' | 'low'
  sql_statement?: string
  estimated_impact: string
}

export interface TableRecommendations {
  table_name: string
  recommendations: OptimizationRecommendation[]
  generated_at: string
}

export interface SpaceOverview {
  table_count: number
  total_data_bytes: number
  total_index_bytes: number
  total_bytes: number
  total_data_free_bytes: number
  total_rows: number
  total_data_mb: number
  total_index_mb: number
  total_mb: number
  total_data_free_mb: number
}

export interface SpaceByTableItem {
  table_name: string
  data_mb: number
  index_mb: number
  total_mb: number
  data_bytes?: number
  index_bytes?: number
  total_bytes?: number
  table_rows?: number
  data_free_bytes?: number
  data_free_mb?: number
}

export interface SpaceByIndexItem {
  table_name: string
  index_name: string
  index_type: string
  non_unique: number
  index_size_mb: number
  index_size_bytes?: number
  columns?: string
}

export interface FragmentationItem {
  table_name: string
  free_mb: number
  free_bytes?: number
  total_mb: number
  total_bytes?: number
  fragmentation_pct: number
  table_rows?: number
}

export interface SpaceAnomalyThreshold {
  large_table_threshold_mb: number
  empty_table_rows: number
  high_fragmentation_pct: number
}

export interface SpaceAnomalyTable {
  table_name: string
  data_mb?: number
  index_mb?: number
  total_mb?: number
  table_rows?: number
  free_mb?: number
  fragmentation_pct?: number
}

export interface SpaceAnomaly {
  large_tables: SpaceAnomalyTable[]
  large_tables_count: number
  empty_tables: SpaceAnomalyTable[]
  empty_tables_count: number
  high_fragmentation_tables: SpaceAnomalyTable[]
  high_fragmentation_count: number
  thresholds: SpaceAnomalyThreshold
}
