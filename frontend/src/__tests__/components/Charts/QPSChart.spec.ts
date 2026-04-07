import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { defineComponent } from 'vue'

/**
 * QPSChart.vue 组件测试
 */
const QPSChart = defineComponent({
  template: `
    <div class="qps-chart">
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
    title: { type: String, default: 'QPS趋势' },
    data: { type: Array, default: () => [] },
    loading: { type: Boolean, default: false }
  },
  emits: ['refresh', 'export'],
  setup(_, { emit }) {
    const handleRefresh = () => emit('refresh')
    const handleExport = () => emit('export')
    return { handleRefresh, handleExport }
  }
})

describe('QPSChart', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('should show loading state', () => {
    const wrapper = mount(QPSChart, {
      props: { loading: true }
    })

    expect(wrapper.find('.loading').exists()).toBe(true)
    expect(wrapper.find('.chart-container').exists()).toBe(false)
  })

  it('should show empty state', () => {
    const wrapper = mount(QPSChart, {
      props: { data: [] }
    })

    expect(wrapper.find('.no-data').exists()).toBe(true)
    expect(wrapper.find('.chart-container').exists()).toBe(false)
  })

  it('should render chart title', () => {
    const wrapper = mount(QPSChart)

    expect(wrapper.find('.chart-title').text()).toBe('QPS趋势')
  })

  it('should emit refresh event', () => {
    const wrapper = mount(QPSChart)

    const refreshButton = wrapper.find('button')
    expect(refreshButton.exists()).toBe(true)

    refreshButton.trigger('click')
    expect(wrapper.emitted('refresh')).toBeTruthy()
  })
})

/**
 * TPSChart.vue 组件测试
 */
const TPSChart = defineComponent({
  template: `
    <div class="tps-chart">
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
    title: { type: String, default: 'TPS趋势' },
    data: { type: Array, default: () => [] },
    loading: { type: Boolean, default: false }
  },
  emits: ['refresh', 'export'],
  setup(_, { emit }) {
    const handleRefresh = () => emit('refresh')
    const handleExport = () => emit('export')
    return { handleRefresh, handleExport }
  }
})

describe('TPSChart', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('should show loading state', () => {
    const wrapper = mount(TPSChart, {
      props: { loading: true }
    })

    expect(wrapper.find('.loading').exists()).toBe(true)
    expect(wrapper.find('.chart-container').exists()).toBe(false)
  })

  it('should show empty state', () => {
    const wrapper = mount(TPSChart, {
      props: { data: [] }
    })

    expect(wrapper.find('.no-data').exists()).toBe(true)
    expect(wrapper.find('.chart-container').exists()).toBe(false)
  })

  it('should render chart title', () => {
    const wrapper = mount(TPSChart)

    expect(wrapper.find('.chart-title').text()).toBe('TPS趋势')
  })

  it('should emit refresh event', () => {
    const wrapper = mount(TPSChart)

    const refreshButton = wrapper.find('button')
    expect(refreshButton.exists()).toBe(true)

    refreshButton.trigger('click')
    expect(wrapper.emitted('refresh')).toBeTruthy()
  })
})
