export interface WaitEvent {
  event_name: string
  event_class: string
  wait_time: number
  timestamp: string
}

export interface WaitEventSummary {
  event_name: string
  total_wait_time: number
  wait_count: number
  avg_wait_time: number
}
