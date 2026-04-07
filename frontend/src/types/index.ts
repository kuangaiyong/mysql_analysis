export interface Index {
  name: string
  table_name: string
  column_name: string | null
  index_type: 'BTREE' | 'HASH' | 'FULLTEXT' | 'RTREE'
  unique: boolean
  primary: boolean
  cardinality: number
  size_bytes: number
  created_at: string
  usage_count?: number
  last_used?: string | number | null
}

export interface IndexCreate {
  table_name: string
  index_name: string
  columns: string[]
  unique?: boolean
  index_type?: string
}

export interface IndexUsage {
  index_name: string
  table_name: string
  usage_count: number
  last_used: string | number | null
  efficiency: 'high' | 'medium' | 'low' | 'unused'
}

export interface IndexUsageReport {
  connection_id: number
  total_indexes: number
  unused_indexes: number
  unused_indexes_detail?: IndexUsage[]
  low_usage_indexes: IndexUsage[]
  high_usage_indexes: IndexUsage[]
  analyzed_at: string
}

export interface RedundantIndex {
  index_name_1: string
  index_name_2: string
  table_name: string
  redundancy_type: 'duplicate' | 'subset'
  recommendation: string
}

export interface TableColumn {
  column_name: string
  data_type: string
  nullable: boolean
  key?: string
  default?: string | null
  extra?: string
}

export interface FragmentationResult {
  table_name: string
  engine: string
  table_rows: number
  data_length: number
  index_length: number
  data_free: number
  fragmentation_pct: number
  severity: 'ok' | 'warning' | 'critical'
  recommendation: string
}
