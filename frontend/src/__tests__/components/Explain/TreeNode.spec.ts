import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { defineComponent, ref } from 'vue'

const TreeNode = defineComponent({
  template: `
    <div class="tree-node">
      <div class="node-content" @click="handleToggle">
        <span class="node-icon">{{ isExpanded ? '-' : '+' }}</span>
        <span class="node-label">{{ label }}</span>
      </div>
      <div v-if="isExpanded" class="node-children">
        <div v-for="child in children" :key="child.id" class="child-node">
          {{ child.label }}
        </div>
      </div>
    </div>
  `,
  props: {
    label: { type: String, default: 'Node' },
    children: { type: Array, default: () => [] },
    isExpanded: { type: Boolean, default: false }
  },
  emits: ['toggle'],
  setup(props, { emit }) {
    const isExpanded = ref(props.isExpanded)
    const handleToggle = () => {
      isExpanded.value = !isExpanded.value
      emit('toggle', isExpanded.value)
    }
    return { isExpanded, handleToggle }
  }
})

describe('TreeNode', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('should render node with label', () => {
    const wrapper = mount(TreeNode, {
      props: { label: 'Table: users' }
    })

    expect(wrapper.find('.node-label').text()).toBe('Table: users')
    expect(wrapper.find('.node-icon').text()).toBe('+')
  })

  it('should render children when expanded', () => {
    const children = [
      { id: 1, label: 'Column: id' },
      { id: 2, label: 'Column: name' }
    ]

    const wrapper = mount(TreeNode, {
      props: { children, isExpanded: true }
    })

    expect(wrapper.findAll('.child-node').length).toBe(2)
  })

  it('should hide children when collapsed', () => {
    const children = [
      { id: 1, label: 'Column: id' },
      { id: 2, label: 'Column: name' }
    ]

    const wrapper = mount(TreeNode, {
      props: { children, isExpanded: false }
    })

    expect(wrapper.findAll('.child-node').length).toBe(0)
  })

  it('should emit toggle event', () => {
    const wrapper = mount(TreeNode)

    const nodeContent = wrapper.find('.node-content')
    nodeContent.trigger('click')

    expect(wrapper.emitted('toggle')).toBeTruthy()
  })
})
