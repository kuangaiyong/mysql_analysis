import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { defineComponent } from 'vue'

const ResultTable = defineComponent({
  template: `
    <div class="result-table">
      <div class="table-header">
        <h3 class="table-title">{{ title }}</h3>
      </div>
      <table class="data-table">
        <thead>
          <tr>
            <th v-for="col in columns" :key="col" @click="$emit('sort', col)">{{ col }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in data" :key="row.id">
            <td v-for="col in columns" :key="col">{{ row[col] }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  `,
  props: {
    title: { type: String, default: 'EXPLAIN结果' },
    data: { type: Array, default: () => [] },
    columns: { type: Array, default: () => ['id', 'select_type', 'table', 'type'] }
  },
  emits: ['sort', 'filter']
})

describe('ResultTable', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('should render table with data', () => {
    const data = [
      { id: 1, select_type: 'SIMPLE', table: 'users', type: 'ALL' },
      { id: 2, select_type: 'range', table: 'orders', type: 'ref' }
    ]

    const wrapper = mount(ResultTable, {
      props: { data }
    })

    expect(wrapper.findAll('tbody tr').length).toBe(2)
    expect(wrapper.find('.table-title').text()).toBe('EXPLAIN结果')
  })

  it('should show empty state', () => {
    const wrapper = mount(ResultTable, {
      props: { data: [] }
    })

    expect(wrapper.findAll('tbody tr').length).toBe(0)
  })

  it('should emit sort event when header is clicked', () => {
    const wrapper = mount(ResultTable)

    const header = wrapper.find('th')
    header.trigger('click')

    expect(wrapper.emitted('sort')).toBeTruthy()
    expect(wrapper.emitted('sort')![0]).toEqual(['id'])
  })

  it('should render column headers', () => {
    const wrapper = mount(ResultTable)

    const headers = wrapper.findAll('th')
    expect(headers.length).toBe(4)
    expect(headers[0].text()).toBe('id')
    expect(headers[1].text()).toBe('select_type')
  })
})
