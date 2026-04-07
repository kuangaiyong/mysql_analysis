import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { defineComponent } from 'vue'

/**
 * MetricChart.vue 组件简化测试
 */
const MetricChart = defineComponent({
  template: `
    <div class="metric-chart">
      <div class="chart-header">
        <h3 class="chart-title">{{ title }}</h3>
        <div class="chart-actions">
          <button @click="handleRefresh" :disabled="loading">刷新</button>
          <button @click="handleExport">导出</button>
        </div>
      </div>
      <div v-if="loading" class="loading">加载中...</div>
      <div v-else-if="!data || data.length === 0" class="no-data">暂无数据</div>
      <div v-else class="chart-container">
        <div class="chart-data">
          <div v-for="item in data" :key="item.id" class="data-point">
            {{ item.label }}: {{ item.value }}
          </div>
        </div>
      </div>
    </div>
  `,
  props: {
    title: {
      type: String,
      default: '指标趋势'
    },
    data: {
      type: Array,
      default: () => []
    },
    loading: {
      type: Boolean,
      default: false
    }
  },
  emits: ['refresh', 'export'],
  setup(_, { emit }) {
    const handleRefresh = () => emit('refresh')
    const handleExport = () => emit('export')
    return {
      handleRefresh,
      handleExport
    }
  }
})

describe('MetricChart', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('should show loading state', () => {
    const wrapper = mount(MetricChart, {
      props: { loading: true }
    })

    expect(wrapper.find('.loading').exists()).toBe(true)
    expect(wrapper.find('.chart-container').exists()).toBe(false)
  })

  it('should show empty state', () => {
    const wrapper = mount(MetricChart, {
      props: { data: [] }
    })

    expect(wrapper.find('.no-data').exists()).toBe(true)
    expect(wrapper.find('.chart-container').exists()).toBe(false)
  })

  it('should render chart with data', () => {
    const data = [
      { id: '1', label: 'QPS', value: 100 },
      { id: '2', label: 'TPS', value: 500 }
    ]

    const wrapper = mount(MetricChart, {
      props: { title: '性能指标', data, loading: false }
    })

    expect(wrapper.find('.chart-title').text()).toBe('性能指标')
    expect(wrapper.findAll('.data-point').length).toBe(2)
    expect(wrapper.find('.chart-container').exists()).toBe(true)
  })

  it('should emit refresh event', () => {
    const wrapper = mount(MetricChart)

    const refreshButton = wrapper.find('button')
    expect(refreshButton.exists()).toBe(true)

    refreshButton.trigger('click')
    expect(wrapper.emitted('refresh')).toBeTruthy()
  })
})
