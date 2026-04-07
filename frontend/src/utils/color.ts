/**
 * 颜色工具函数
 * 统一管理项目中所有颜色判断逻辑，替换硬编码颜色值
 */

/**
 * 获取健康评分颜色
 * @param score 分数值 (0-100)
 * @returns CSS颜色变量
 */
export const getHealthColor = (score: number): string => {
  if (score >= 80) return 'var(--health-good)'
  if (score >= 60) return 'var(--health-warning)'
  return 'var(--health-critical)'
}

/**
 * 获取健康评分十六进制颜色值
 * 用于需要直接颜色值的场景（如ECharts）
 * @param score 分数值 (0-100)
 * @returns 十六进制颜色值
 */
export const getHealthColorHex = (score: number): string => {
  if (score >= 80) return '#67c23a'
  if (score >= 60) return '#e6a23c'
  return '#f56c6c'
}

/**
 * 获取扫描效率颜色
 * @param efficiency 效率值 (0.0-1.0)
 * @returns CSS类名
 */
export const getScanEfficiencyClass = (efficiency: number): string => {
  if (efficiency >= 0.8) return 'efficiency-good'
  if (efficiency >= 0.5) return 'efficiency-warning'
  return 'efficiency-critical'
}

/**
 * 获取扫描效率颜色值
 * @param efficiency 效率值 (0.0-1.0)
 * @returns CSS颜色变量
 */
export const getScanEfficiencyColor = (efficiency: number): string => {
  if (efficiency >= 0.8) return 'var(--efficiency-good)'
  if (efficiency >= 0.5) return 'var(--efficiency-warning)'
  return 'var(--efficiency-critical)'
}

/**
 * 获取执行时间样式类
 * @param time 执行时间（秒）
 * @returns CSS类名
 */
export const getQueryTimeClass = (time: number): string => {
  if (time > 5) return 'query-time-critical'
  if (time > 1) return 'query-time-warning'
  return ''
}

/**
 * 获取执行时间颜色值
 * @param time 执行时间（秒）
 * @returns CSS颜色变量
 */
export const getQueryTimeColor = (time: number): string => {
  if (time > 5) return 'var(--time-critical)'
  if (time > 1) return 'var(--time-warning)'
  return 'var(--time-normal)'
}

/**
 * 获取优先级标签类型（Element Plus）
 * @param priority 优先级 ('high' | 'medium' | 'low')
 * @returns Element Plus Tag类型
 */
export const getPriorityType = (priority: string): 'danger' | 'warning' | 'info' => {
  switch (priority) {
    case 'high':
      return 'danger'
    case 'medium':
      return 'warning'
    case 'low':
    default:
      return 'info'
  }
}

/**
 * 获取优先级标签文本
 * @param priority 优先级 ('high' | 'medium' | 'low')
 * @returns 中文标签
 */
export const getPriorityLabel = (priority: string): string => {
  switch (priority) {
    case 'high':
      return '高优先级'
    case 'medium':
      return '中优先级'
    case 'low':
      return '低优先级'
    default:
      return priority
  }
}

/**
 * 获取严重程度标签类型（Element Plus）
 * @param severity 严重程度 ('CRIT' | 'WARN' | 'INFO')
 * @returns Element Plus Tag类型
 */
export const getSeverityType = (severity: string): 'danger' | 'warning' | 'info' => {
  switch (severity) {
    case 'CRIT':
      return 'danger'
    case 'WARN':
      return 'warning'
    case 'INFO':
    default:
      return 'info'
  }
}

/**
 * 获取建议类型标签类型（Element Plus）
 * @param type 建议类型 ('index' | 'query_rewrite' | 'schema' | 'config')
 * @returns Element Plus Tag类型
 */
export const getSuggestionTypeTag = (type: string): 'success' | 'primary' | 'warning' | 'info' => {
  switch (type) {
    case 'index':
      return 'success'
    case 'query_rewrite':
      return 'primary'
    case 'schema':
      return 'warning'
    case 'config':
    default:
      return 'info'
  }
}

/**
 * 获取建议类型标签文本
 * @param type 建议类型
 * @returns 中文标签
 */
export const getSuggestionTypeLabel = (type: string): string => {
  switch (type) {
    case 'index':
      return '索引优化'
    case 'query_rewrite':
      return '查询重写'
    case 'schema':
      return '表结构优化'
    case 'config':
      return '配置优化'
    default:
      return type
  }
}

/**
 * 获取瓶颈类型标签类型
 * @param type 瓶颈类型
 * @returns Element Plus Tag类型
 */
export const getBottleneckTypeTag = (type?: string): 'danger' | 'warning' | 'info' => {
  const typeMap: Record<string, 'danger' | 'warning' | 'info'> = {
    'cpu-bound': 'danger',
    'io-bound': 'warning',
    'lock-wait': 'warning',
    'none': 'info'
  }
  return typeMap[type || 'none'] || 'info'
}

/**
 * 获取瓶颈类型标签文本
 * @param type 瓶颈类型
 * @returns 中文标签
 */
export const getBottleneckTypeLabel = (type?: string): string => {
  const labelMap: Record<string, string> = {
    'cpu-bound': 'CPU密集',
    'io-bound': 'I/O密集',
    'lock-wait': '锁等待',
    'none': '无明显瓶颈'
  }
  return labelMap[type || 'none'] || '未知'
}

/**
 * 获取性能评分描述
 * @param score 评分 ('A' | 'B' | 'C' | 'D' | 'E')
 * @returns 描述文本
 */
export const getScoreDesc = (score?: string): string => {
  switch (score) {
    case 'A':
      return '性能优秀'
    case 'B':
      return '性能良好'
    case 'C':
      return '性能一般'
    case 'D':
      return '性能较差'
    case 'E':
      return '性能极差'
    default:
      return '未知'
  }
}

/**
 * 获取性能评分颜色类名
 * @param score 评分
 * @returns CSS类名
 */
export const getScoreClass = (score?: string): string => {
  switch (score) {
    case 'A':
      return 'score-a'
    case 'B':
      return 'score-b'
    case 'C':
      return 'score-c'
    case 'D':
      return 'score-d'
    case 'E':
      return 'score-e'
    default:
      return 'score-c'
  }
}


/**
 * 获取风险等级标签
 * 根据执行时间和扫描效率综合评估风险等级
 * @param queryTime 执行时间（秒）
 * @param scanEfficiency 扫描效率 (0.0-1.0)
 * @returns 风险等级标签
 */
export const getRiskLevelLabel = (queryTime: number, scanEfficiency?: number): string => {
  // 高风险：执行时间 > 5s 或扫描效率 < 0.3
  if (queryTime > 5 || (scanEfficiency !== undefined && scanEfficiency < 0.3)) {
    return '高风险'
  }
  // 中风险：执行时间 > 1s 或扫描效率 < 0.5
  if (queryTime > 1 || (scanEfficiency !== undefined && scanEfficiency < 0.5)) {
    return '中风险'
  }
  return '低风险'
}

/**
 * 获取风险等级标签类型（Element Plus）
 * @param queryTime 执行时间（秒）
 * @param scanEfficiency 扫描效率 (0.0-1.0)
 * @returns Element Plus Tag类型
 */
export const getRiskLevelTagType = (queryTime: number, scanEfficiency?: number): 'danger' | 'warning' | 'success' => {
  // 高风险
  if (queryTime > 5 || (scanEfficiency !== undefined && scanEfficiency < 0.3)) {
    return 'danger'
  }
  // 中风险
  if (queryTime > 1 || (scanEfficiency !== undefined && scanEfficiency < 0.5)) {
    return 'warning'
  }
  return 'success'
}