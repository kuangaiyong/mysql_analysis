import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface RealtimeMetrics {
  connection_id: number
  qps: number
  tps: number
  connections: {
    current: number
    max: number
    active: number
  }
  buffer_pool_hit_rate: number
}

export interface SlowQueryAlert {
  query_hash: string
  sql_digest: string
  query_time: number
  database_name?: string
}

export interface AlertData {
  id: number
  alert_rule_id: number
  connection_id: number
  alert_time: string
  metric_value?: number
  message?: string
  severity: string
  status: string
}

export const useRealtimeStore = defineStore('realtime', () => {
  const wsConnected = ref(false)
  const wsReconnectAttempts = ref(0)
  const metrics = ref<RealtimeMetrics | null>(null)
  const recentSlowQueries = ref<SlowQueryAlert[]>([])
  const activeAlerts = ref<AlertData[]>([])

  const setWsConnected = (status: boolean) => {
    wsConnected.value = status
  }

  const setWsReconnectAttempts = (attempts: number) => {
    wsReconnectAttempts.value = attempts
  }

  const updateMetrics = (data: RealtimeMetrics) => {
    metrics.value = data
  }

  const addSlowQuery = (query: SlowQueryAlert) => {
    recentSlowQueries.value.unshift(query)
    if (recentSlowQueries.value.length > 50) {
      recentSlowQueries.value = recentSlowQueries.value.slice(0, 50)
    }
  }

  const addAlert = (alert: AlertData) => {
    activeAlerts.value.unshift(alert)
    if (activeAlerts.value.length > 100) {
      activeAlerts.value = activeAlerts.value.slice(0, 100)
    }
  }

  const resolveAlert = (alertId: number) => {
    const index = activeAlerts.value.findIndex((a) => a.id === alertId)
    if (index !== -1 && activeAlerts.value[index]) {
      activeAlerts.value[index].status = 'resolved'
    }
  }

  const clearMetrics = () => {
    metrics.value = null
  }

  const clearSlowQueries = () => {
    recentSlowQueries.value = []
  }

  const clearAlerts = () => {
    activeAlerts.value = []
  }

  return {
    wsConnected,
    wsReconnectAttempts,
    metrics,
    recentSlowQueries,
    activeAlerts,
    setWsConnected,
    setWsReconnectAttempts,
    updateMetrics,
    addSlowQuery,
    addAlert,
    resolveAlert,
    clearMetrics,
    clearSlowQueries,
    clearAlerts
  }
})
