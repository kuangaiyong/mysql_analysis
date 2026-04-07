/**
 * 颜色工具函数测试
 */
import { describe, it, expect } from 'vitest'
import {
  getHealthColor,
  getHealthColorHex,
  getScanEfficiencyClass,
  getScanEfficiencyColor,
  getQueryTimeClass,
  getQueryTimeColor,
  getPriorityType,
  getPriorityLabel,
  getSeverityType,
  getSuggestionTypeTag,
  getSuggestionTypeLabel,
  getBottleneckTypeTag,
  getBottleneckTypeLabel,
  getScoreDesc,
  getScoreClass
} from '@/utils/color'

describe('颜色工具函数', () => {
  describe('getHealthColor', () => {
    it('评分 >= 80 返回健康状态颜色', () => {
      expect(getHealthColor(80)).toBe('var(--health-good)')
      expect(getHealthColor(100)).toBe('var(--health-good)')
    })
    it('评分 >= 60 且 < 80 返回警告状态颜色', () => {
      expect(getHealthColor(60)).toBe('var(--health-warning)')
      expect(getHealthColor(79)).toBe('var(--health-warning)')
    })
    it('评分 < 60 返回严重状态颜色', () => {
      expect(getHealthColor(0)).toBe('var(--health-critical)')
      expect(getHealthColor(59)).toBe('var(--health-critical)')
    })
  })

  describe('getHealthColorHex', () => {
    it('返回正确的十六进制颜色值', () => {
      expect(getHealthColorHex(80)).toBe('#67c23a')
      expect(getHealthColorHex(60)).toBe('#e6a23c')
      expect(getHealthColorHex(50)).toBe('#f56c6c')
    })
  })

  describe('getScanEfficiencyClass', () => {
    it('返回正确的效率类名', () => {
      expect(getScanEfficiencyClass(0.8)).toBe('efficiency-good')
      expect(getScanEfficiencyClass(0.5)).toBe('efficiency-warning')
      expect(getScanEfficiencyClass(0.4)).toBe('efficiency-critical')
    })
  })

  describe('getScanEfficiencyColor', () => {
    it('返回正确的效率颜色', () => {
      expect(getScanEfficiencyColor(0.8)).toBe('var(--efficiency-good)')
      expect(getScanEfficiencyColor(0.5)).toBe('var(--efficiency-warning)')
      expect(getScanEfficiencyColor(0.3)).toBe('var(--efficiency-critical)')
    })
  })

  describe('getQueryTimeClass', () => {
    it('返回正确的查询时间类名', () => {
      expect(getQueryTimeClass(6)).toBe('query-time-critical')
      expect(getQueryTimeClass(2)).toBe('query-time-warning')
      expect(getQueryTimeClass(0.5)).toBe('')
    })
  })

  describe('getQueryTimeColor', () => {
    it('返回正确的查询时间颜色', () => {
      expect(getQueryTimeColor(6)).toBe('var(--time-critical)')
      expect(getQueryTimeColor(2)).toBe('var(--time-warning)')
      expect(getQueryTimeColor(0.5)).toBe('var(--time-normal)')
    })
  })

  describe('getPriorityType', () => {
    it('返回正确的优先级类型', () => {
      expect(getPriorityType('high')).toBe('danger')
      expect(getPriorityType('medium')).toBe('warning')
      expect(getPriorityType('low')).toBe('info')
      expect(getPriorityType('unknown')).toBe('info')
    })
  })

  describe('getPriorityLabel', () => {
    it('返回正确的优先级标签', () => {
      expect(getPriorityLabel('high')).toBe('高优先级')
      expect(getPriorityLabel('medium')).toBe('中优先级')
      expect(getPriorityLabel('low')).toBe('低优先级')
    })
  })

  describe('getSeverityType', () => {
    it('返回正确的严重程度类型', () => {
      expect(getSeverityType('CRIT')).toBe('danger')
      expect(getSeverityType('WARN')).toBe('warning')
      expect(getSeverityType('INFO')).toBe('info')
      expect(getSeverityType('unknown')).toBe('info')
    })
  })

  describe('getSuggestionTypeTag', () => {
    it('返回正确的建议类型标签', () => {
      expect(getSuggestionTypeTag('index')).toBe('success')
      expect(getSuggestionTypeTag('query_rewrite')).toBe('primary')
      expect(getSuggestionTypeTag('schema')).toBe('warning')
      expect(getSuggestionTypeTag('config')).toBe('info')
      expect(getSuggestionTypeTag('unknown')).toBe('info')
    })
  })

  describe('getSuggestionTypeLabel', () => {
    it('返回正确的建议类型文本', () => {
      expect(getSuggestionTypeLabel('index')).toBe('索引优化')
      expect(getSuggestionTypeLabel('query_rewrite')).toBe('查询重写')
      expect(getSuggestionTypeLabel('schema')).toBe('表结构优化')
      expect(getSuggestionTypeLabel('config')).toBe('配置优化')
      expect(getSuggestionTypeLabel('unknown')).toBe('unknown')
    })
  })

  describe('getBottleneckTypeTag', () => {
    it('返回正确的瓶颈类型标签', () => {
      expect(getBottleneckTypeTag('cpu-bound')).toBe('danger')
      expect(getBottleneckTypeTag('io-bound')).toBe('warning')
      expect(getBottleneckTypeTag('lock-wait')).toBe('warning')
      expect(getBottleneckTypeTag('none')).toBe('info')
      expect(getBottleneckTypeTag(undefined)).toBe('info')
    })
  })

  describe('getBottleneckTypeLabel', () => {
    it('返回正确的瓶颈类型文本', () => {
      expect(getBottleneckTypeLabel('cpu-bound')).toBe('CPU密集')
      expect(getBottleneckTypeLabel('io-bound')).toBe('I/O密集')
      expect(getBottleneckTypeLabel('lock-wait')).toBe('锁等待')
      expect(getBottleneckTypeLabel('none')).toBe('无明显瓶颈')
      expect(getBottleneckTypeLabel(undefined)).toBe('无明显瓶颈')
    })
  })

  describe('getScoreDesc', () => {
    it('返回正确的评分描述', () => {
      expect(getScoreDesc('A')).toBe('性能优秀')
      expect(getScoreDesc('B')).toBe('性能良好')
      expect(getScoreDesc('C')).toBe('性能一般')
      expect(getScoreDesc('D')).toBe('性能较差')
      expect(getScoreDesc('E')).toBe('性能极差')
      expect(getScoreDesc(undefined)).toBe('未知')
    })
  })

  describe('getScoreClass', () => {
    it('返回正确的评分类名', () => {
      expect(getScoreClass('A')).toBe('score-a')
      expect(getScoreClass('B')).toBe('score-b')
      expect(getScoreClass('C')).toBe('score-c')
      expect(getScoreClass('D')).toBe('score-d')
      expect(getScoreClass('E')).toBe('score-e')
      expect(getScoreClass(undefined)).toBe('score-c')
    })
  })
})
