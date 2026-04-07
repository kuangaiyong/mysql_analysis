/**
 * Query Trends Type Definitions
 */

/**
 * Query fingerprint trend data
 */
export interface QueryTrend {
  fingerprint_hash: string
  normalized_sql: string
  execution_count: number
  avg_query_time: number
  min_query_time: number
  max_query_time: number
  first_seen: string
  last_seen: string
  table_name: string
  database_name: string
}

/**
 * Query fingerprint historical data
 */
export interface QueryTrendHistory {
  fingerprint_hash: string
  history: {
    timestamp: string
    query_time: number
    execution_count: number
  }[]
}

/**
 * Request to generate query fingerprints
 */
export interface GenerateFingerprintsRequest {
  connection_id: number
  days?: number
}

/**
 * Search parameters for query trends
 */
export interface TrendSearchParams {
  connection_id: number
  skip?: number
  limit?: number
  table_name?: string
  database?: string
  start_time?: string
  end_time?: string
}
