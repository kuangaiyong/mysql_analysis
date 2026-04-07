import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { defineComponent } from 'vue'

const VisualExplainFlowchart = defineComponent({
  template: `
    <div class="explain-flowchart">
      <h3 class="chart-title">{{ title }}</h3>
      <div v-if="loading" class="loading">加载中...</div>
      <div v-else-if="!nodes || nodes.length === 0" class="no-data">暂无数据</div>
      <div v-else class="chart-container">
        <div class="node" v-for="node in nodes" :key="node.id">
          {{ node.label }}
        </div>
      </div>
    </div>
  `,
  props: {
    title: { type: String, default: 'EXPLAIN执行计划' },
    nodes: { type: Array, default: () => [] },
    loading: { type: Boolean, default: false }
  },
  emits: ['refresh']
})

describe('VisualExplainFlowchart', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('should show loading state', () => {
    const wrapper = mount(VisualExplainFlowchart, {
      props: { loading: true }
    })

    expect(wrapper.find('.loading').exists()).toBe(true)
    expect(wrapper.find('.chart-container').exists()).toBe(false)
  })

  it('should show empty state', () => {
    const wrapper = mount(VisualExplainFlowchart, {
      props: { nodes: [] }
    })

    expect(wrapper.find('.no-data').exists()).toBe(true)
    expect(wrapper.find('.chart-container').exists()).toBe(false)
  })

  it('should render flowchart nodes', () => {
    const nodes = [
      { id: 1, label: 'users' },
      { id: 2, label: 'orders' }
    ]

    const wrapper = mount(VisualExplainFlowchart, {
      props: { nodes }
    })

    expect(wrapper.findAll('.node').length).toBe(2)
  })
})
