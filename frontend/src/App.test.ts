import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import App from '@/App.vue'

vi.mock('vue-router', () => ({
  RouterView: { name: 'RouterView', template: '<div><slot /></div>' },
  useRoute: vi.fn(),
  useRouter: vi.fn(() => ({ push: vi.fn(), replace: vi.fn() })),
}))

vi.mock('element-plus', () => ({
  ElConfigProvider: { name: 'ElConfigProvider', template: '<div><slot /></div>' },
}))

describe('App.vue', () => {
  it('renders properly with router-view', () => {
    const wrapper = mount(App, {
      global: {
        stubs: {
          'router-view': true,
          'el-config-provider': true,
        },
      },
    })
    expect(wrapper.exists()).toBe(true)
    expect(wrapper.findComponent({ name: 'App' }).exists()).toBe(true)
  })
})
