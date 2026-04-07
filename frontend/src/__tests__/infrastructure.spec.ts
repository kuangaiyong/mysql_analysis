import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { defineComponent } from 'vue'

const TestComponent = defineComponent({
  template: '<div class="test">Hello Vitest</div>'
})

describe('Vitest Infrastructure', () => {
  it('should run basic test', () => {
    expect(1 + 1).toBe(2)
  })

  it('should mount Vue component', () => {
    const wrapper = mount(TestComponent)
    expect(wrapper.find('.test').exists()).toBe(true)
    expect(wrapper.text()).toBe('Hello Vitest')
  })
})
