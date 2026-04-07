/**
 * 共享性能指标类型定义
 * 用于 Dashboard 和 Monitoring 页面的指标数据
 */

import type { PerformanceMetrics } from '@/types/monitoring'

/** 指标卡片数据类型 */
export interface MetricCardData {
  title: string
  value: string | number
  unit?: string
  icon?: string
  color?: string
  key?: string
}

/** 关键指标数据类型 */
export interface CriticalMetricData {
  title: string
  value: string | number
  icon?: string
  color?: string
  key?: string
}

/** 指标更新函数类型 */
export type MetricUpdater = (metrics: PerformanceMetrics) => void

/** 主要指标配置 */
export const PRIMARY_METRICS_CONFIG = [
  { title: '活跃连接', key: 'connections.active', unit: '', icon: 'Connection', color: 'var(--warning-color)' },
  { title: '最大连接', key: 'connections.max', unit: '', icon: 'UserFilled', color: 'var(--primary-color)' },
  { title: '缓冲池命中率', key: 'buffer_pool_hit_rate', unit: '%', icon: 'DataLine', color: 'var(--danger-color)' },
  { title: '查询缓存命中率', key: 'query_cache_hit_rate', unit: '%', icon: 'Cpu', color: 'var(--success-color)' }
] as const

/** 关键指标配置 */
export const CRITICAL_METRICS_CONFIG = [
  { title: '行锁等待', key: 'innodb_locks.row_lock_waits', unit: '次', icon: 'Lock', color: '#8b5cf6' },
  { title: '死锁次数', key: 'innodb_locks.deadlocks', unit: '次', icon: 'Warning', color: '#ec4899' },
  { title: '磁盘临时表', key: 'memory_pressure.tmp_disk_tables', unit: '表', icon: 'Files', color: '#06b6d4' },
  { title: '全表扫描', key: 'query_efficiency.handler_read_rnd_next', unit: '次', icon: 'Search', color: 'var(--warning-color)' }
] as const

/**
 * 从 PerformanceMetrics 提取指标值
 */
export function extractMetricValue(metrics: PerformanceMetrics, key: string): string | number {
  const keys = key.split('.')
  let value: any = metrics
  
  for (const k of keys) {
    if (value && typeof value === 'object' && k in value) {
      value = value[k]
    } else {
      return 0
    }
  }
  
  if (typeof value === 'number') {
    return key.includes('rate') || key === 'buffer_pool_hit_rate' 
      ? value.toFixed(2) 
      : value
  }
  
  return value ?? 0
}

/**
 * 从 PerformanceMetrics 构建指标卡片数据
 */
export function buildPrimaryMetrics(metrics: PerformanceMetrics): MetricCardData[] {
  return PRIMARY_METRICS_CONFIG.map(config => ({
    title: config.title,
    value: extractMetricValue(metrics, config.key),
    unit: config.unit,
    icon: config.icon,
    color: config.color,
    key: config.key
  }))
}

export function buildCriticalMetrics(metrics: PerformanceMetrics): CriticalMetricData[] {
  return CRITICAL_METRICS_CONFIG.map(config => ({
    title: config.title,
    value: extractMetricValue(metrics, config.key),
    unit: config.unit,
    icon: config.icon,
    color: config.color,
    key: config.key
  }))
}
