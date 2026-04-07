export interface PerformanceMetrics {
  connection_id: number
  qps: number
  tps: number
  read_qps?: number
  write_qps?: number
  connections: {
    current: number
    max: number
    active: number
  }
  buffer_pool_hit_rate: number
  queries: {
    select: number
    insert: number
    update: number
    delete: number
  }
  system: {
    uptime: number
    thread_count: number
  }
  timestamp: string
  innodb_locks?: InnoDBLockMetrics
  disk_io?: DiskIOMetrics
  memory_pressure?: MemoryPressureMetrics
  query_efficiency?: QueryEfficiencyMetrics
  connection_health?: ConnectionHealthMetrics
}

export interface InnoDBLockMetrics {
  row_lock_waits: number
  row_lock_time: number
  deadlocks: number
}

export interface DiskIOMetrics {
  data_reads: number
  data_writes: number
  log_fsyncs: number
}

export interface MemoryPressureMetrics {
  tmp_disk_tables: number
  tmp_tables: number
  sort_merge_passes: number
}

export interface QueryEfficiencyMetrics {
  handler_read_rnd_next: number
}

export interface ConnectionHealthMetrics {
  aborted_connects: number
  aborted_clients: number
}

export interface MetricsHistory {
  connection_id: number
  start_time: string
  end_time: string
  interval: number
  data: PerformanceMetrics[]
}

export interface AutoCollectionConfig {
  interval: number
  duration?: number
}

export interface AutoCollection {
  id: number
  connection_id: number
  status: 'running' | 'stopped' | 'error'
  started_at: string
  stopped_at?: string
  config: AutoCollectionConfig
}
