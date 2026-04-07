import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { ref } from 'vue'
import PageHeader from '@/components/Common/PageHeader.vue'

// Mock vue-router
const mockPush = vi.fn()
const mockBack = vi.fn()
vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: mockPush,
    back: mockBack
  })
}))

describe('PageHeader', () => {
  beforeEach(() => {
    // 每个测试前重置 mock
    mockPush.mockClear()
    mockBack.mockClear()
  })

  describe('基础渲染', () => {
    it('应该正确渲染页面标题', () => {
      const wrapper = mount(PageHeader, {
        props: { title: '测试页面' }
      })

      expect(wrapper.find('.page-title').text()).toBe('测试页面')
    })

    it('应该包含 page-header 根元素', () => {
      const wrapper = mount(PageHeader, {
        props: { title: '测试' }
      })

      expect(wrapper.find('.page-header').exists()).toBe(true)
      expect(wrapper.find('.header-left').exists()).toBe(true)
      expect(wrapper.find('.header-actions').exists()).toBe(true)
    })
  })

  describe('Props 测试', () => {
    it('默认不显示返回按钮', () => {
      const wrapper = mount(PageHeader, {
        props: { title: '测试' }
      })

      expect(wrapper.find('.header-left .el-button').exists()).toBe(false)
    })

    it('showBack 为 true 时显示返回按钮', () => {
      const wrapper = mount(PageHeader, {
        props: { title: '测试', showBack: true }
      })

      const backButton = wrapper.find('.header-left .el-button')
      expect(backButton.exists()).toBe(true)
      expect(backButton.text()).toContain('返回')
    })

    it('默认不显示刷新按钮', () => {
      const wrapper = mount(PageHeader, {
        props: { title: '测试' }
      })

      // actions 插槽区域不应该有按钮（使用默认插槽时）
      const buttons = wrapper.findAll('.header-actions .el-button')
      expect(buttons.length).toBe(0)
    })

    it('showRefresh 为 true 时显示刷新按钮', () => {
      const wrapper = mount(PageHeader, {
        props: { title: '测试', showRefresh: true }
      })

      const refreshButton = wrapper.findAll('.header-actions .el-button')[0]
      expect(refreshButton.exists()).toBe(true)
      expect(refreshButton.text()).toContain('刷新')
    })

    it('refreshLoading 控制刷新按钮加载状态', () => {
      const wrapper = mount(PageHeader, {
        props: { title: '测试', showRefresh: true, refreshLoading: true }
      })

      const refreshButton = wrapper.find('.header-actions .el-button')
      expect(refreshButton.classes()).toContain('is-loading')
    })

    it('showAdd 为 true 时显示新增按钮', () => {
      const wrapper = mount(PageHeader, {
        props: { title: '测试', showAdd: true }
      })

      const addButton = wrapper.find('.header-actions .el-button--primary')
      expect(addButton.exists()).toBe(true)
      expect(addButton.text()).toContain('新增')
    })

    it('addText 自定义新增按钮文字', () => {
      const wrapper = mount(PageHeader, {
        props: { title: '测试', showAdd: true, addText: '创建连接' }
      })

      const addButton = wrapper.find('.header-actions .el-button--primary')
      expect(addButton.text()).toContain('创建连接')
    })

    it('同时显示刷新和新增按钮', () => {
      const wrapper = mount(PageHeader, {
        props: { title: '测试', showRefresh: true, showAdd: true }
      })

      const buttons = wrapper.findAll('.header-actions .el-button')
      expect(buttons.length).toBe(2)
    })
  })

  describe('插槽测试', () => {
    it('extra 插槽在标题旁渲染内容', () => {
      const wrapper = mount(PageHeader, {
        props: { title: '测试' },
        slots: {
          extra: '<span class="extra-content">额外信息</span>'
        }
      })

      expect(wrapper.find('.extra-content').exists()).toBe(true)
      expect(wrapper.find('.extra-content').text()).toBe('额外信息')
    })

    it('actions 插槽替换默认操作按钮', () => {
      const wrapper = mount(PageHeader, {
        props: { title: '测试' },
        slots: {
          actions: '<button class="custom-action">自定义操作</button>'
        }
      })

      expect(wrapper.find('.custom-action').exists()).toBe(true)
      expect(wrapper.find('.custom-action').text()).toBe('自定义操作')
      // 默认按钮不应该存在
      expect(wrapper.find('.el-button--primary').exists()).toBe(false)
    })
  })

  describe('事件测试', () => {
    it('点击刷新按钮触发 refresh 事件', async () => {
      const wrapper = mount(PageHeader, {
        props: { title: '测试', showRefresh: true }
      })

      const refreshButton = wrapper.findAll('.header-actions .el-button')[0]
      await refreshButton.trigger('click')

      expect(wrapper.emitted('refresh')).toBeTruthy()
      expect(wrapper.emitted('refresh')?.length).toBe(1)
    })

    it('点击新增按钮触发 add 事件', async () => {
      const wrapper = mount(PageHeader, {
        props: { title: '测试', showAdd: true }
      })

      const addButton = wrapper.find('.header-actions .el-button--primary')
      await addButton.trigger('click')

      expect(wrapper.emitted('add')).toBeTruthy()
      expect(wrapper.emitted('add')?.length).toBe(1)
    })

    it('点击返回按钮触发 back 事件并调用 router.back()', async () => {
      const wrapper = mount(PageHeader, {
        props: { title: '测试', showBack: true }
      })

      const backButton = wrapper.find('.header-left .el-button')
      await backButton.trigger('click')

      expect(wrapper.emitted('back')).toBeTruthy()
      expect(mockBack).toHaveBeenCalled()
      expect(mockPush).not.toHaveBeenCalled()
    })

    it('设置 backTo 时点击返回按钮跳转到指定路由', async () => {
      const wrapper = mount(PageHeader, {
        props: { title: '测试', showBack: true, backTo: '/dashboard' }
      })

      const backButton = wrapper.find('.header-left .el-button')
      await backButton.trigger('click')

      expect(wrapper.emitted('back')).toBeTruthy()
      expect(mockPush).toHaveBeenCalledWith('/dashboard')
      expect(mockBack).not.toHaveBeenCalled()
    })
  })

  describe('快照测试', () => {
    it('匹配基础快照', () => {
      const wrapper = mount(PageHeader, {
        props: { title: '页面标题' }
      })

      expect(wrapper.html()).toMatchSnapshot()
    })

    it('匹配完整功能快照', () => {
      const wrapper = mount(PageHeader, {
        props: {
          title: '连接管理',
          showBack: true,
          showRefresh: true,
          showAdd: true,
          addText: '新建连接',
          refreshLoading: false
        }
      })

      expect(wrapper.html()).toMatchSnapshot()
    })
  })
})
