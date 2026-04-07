import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { ElMessage, ElMessageBox } from 'element-plus'
import ConnectionsView from '@/view/connections/index.vue'
import { connectionsApi } from '@/api/connection'
import type { Connection } from '@/types/connection'

// Mock vue-router
const mockPush = vi.fn()
vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: mockPush
  })
}))

// Mock API
vi.mock('@/api/connection')

// Mock element-plus
vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn()
  },
  ElMessageBox: {
    confirm: vi.fn()
  }
}))

// Mock 子组件
vi.mock('@/view/connections/components/ConnectionDialog.vue', () => ({
  default: {
    name: 'ConnectionDialog',
    template: '<div class="mock-connection-dialog"></div>',
    props: ['visible', 'connection']
  }
}))

vi.mock('@/view/connections/components/ConnectionTest.vue', () => ({
  default: {
    name: 'ConnectionTest',
    template: '<div class="mock-connection-test"></div>',
    props: ['visible', 'connection']
  }
}))

vi.mock('@/components/Common/Pagination.vue', () => ({
  default: {
    name: 'Pagination',
    template: '<div class="mock-pagination"></div>',
    props: ['pagination'],
    emits: ['size-change', 'page-change']
  }
}))

vi.mock('@/components/Common/PageHeader.vue', () => ({
  default: {
    name: 'PageHeader',
    template: `
      <div class="mock-page-header">
        <h1>{{ title }}</h1>
        <button v-if="showAdd" class="add-btn" @click="$emit('add')">{{ addText }}</button>
      </div>
    `,
    props: {
      title: { type: String, default: '' },
      showAdd: { type: Boolean, default: false },
      addText: { type: String, default: '' }
    },
    emits: ['add']
  }
}))

// 测试数据
const mockConnections: Connection[] = [
  {
    id: 1,
    name: '测试连接1',
    host: 'localhost',
    port: 3306,
    username: 'root',
    password_encrypted: 'encrypted_password',
    database_name: 'test_db',
    is_active: true,
    created_at: '2024-01-01 10:00:00',
    updated_at: '2024-01-01 10:00:00'
  },
  {
    id: 2,
    name: '测试连接2',
    host: '192.168.1.100',
    port: 3306,
    username: 'admin',
    password_encrypted: 'encrypted_password',
    database_name: 'production_db',
    is_active: false,
    created_at: '2024-01-02 10:00:00',
    updated_at: '2024-01-02 10:00:00'
  }
]

describe('ConnectionsView', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    // 默认 mock getAll 返回空数组
    vi.mocked(connectionsApi.getAll).mockResolvedValue([])
  })

  describe('页面渲染', () => {
    it('应该渲染页面标题和添加按钮', async () => {
      const wrapper = mount(ConnectionsView)
      await wrapper.vm.$nextTick()

      // 检查 PageHeader 组件存在
      const pageHeader = wrapper.findComponent({ name: 'PageHeader' })
      expect(pageHeader.exists()).toBe(true)
      expect(pageHeader.props('title')).toBe('连接管理')
      expect(pageHeader.props('showAdd')).toBe(true)
      expect(pageHeader.props('addText')).toBe('添加连接')
    })

    it('应该渲染搜索表单', () => {
      const wrapper = mount(ConnectionsView)

      // 检查搜索表单存在
      const form = wrapper.find('.search-form')
      expect(form.exists()).toBe(true)

      // 检查搜索输入框
      const inputs = wrapper.findAll('input')
      // 至少有3个搜索输入框（名称、主机、数据库）
      expect(inputs.length).toBeGreaterThanOrEqual(3)
    })

    it('应该渲染连接列表表格', () => {
      const wrapper = mount(ConnectionsView)

      // 检查表格存在
      const table = wrapper.find('.el-table')
      expect(table.exists()).toBe(true)
    })

    it('应该渲染分页组件', () => {
      const wrapper = mount(ConnectionsView)

      // 检查分页组件
      const pagination = wrapper.find('.mock-pagination')
      expect(pagination.exists()).toBe(true)
    })
  })

  describe('连接列表加载', () => {
    it('组件挂载时应该调用 fetchData 加载数据', async () => {
      vi.mocked(connectionsApi.getAll).mockResolvedValue(mockConnections)

      mount(ConnectionsView)

      // 等待异步操作完成
      await new Promise(resolve => setTimeout(resolve, 0))

      expect(connectionsApi.getAll).toHaveBeenCalledWith({
        skip: 0,
        limit: 10
      })
    })

    it('应该正确显示连接列表数据', async () => {
      vi.mocked(connectionsApi.getAll).mockResolvedValue(mockConnections)

      const wrapper = mount(ConnectionsView)

      // 等待数据加载
      await new Promise(resolve => setTimeout(resolve, 0))
      await wrapper.vm.$nextTick()

      // 检查表格数据
      expect(wrapper.vm.tableData).toEqual(mockConnections)
    })

    it('加载数据时应该显示 loading 状态', async () => {
      // 创建一个延迟的 Promise
      let resolvePromise: (value: Connection[]) => void
      const pendingPromise = new Promise<Connection[]>(resolve => {
        resolvePromise = resolve
      })
      vi.mocked(connectionsApi.getAll).mockReturnValue(pendingPromise as any)

      const wrapper = mount(ConnectionsView)

      // 此时应该处于加载状态
      expect(wrapper.vm.loading).toBe(true)

      // 完成 Promise
      resolvePromise!([])
      await new Promise(resolve => setTimeout(resolve, 0))

      // 加载完成
      expect(wrapper.vm.loading).toBe(false)
    })

    it('加载数据失败时应该显示错误消息', async () => {
      const error = {
        response: {
          data: {
            detail: '网络错误'
          }
        }
      }
      vi.mocked(connectionsApi.getAll).mockRejectedValue(error)

      mount(ConnectionsView)

      await new Promise(resolve => setTimeout(resolve, 0))

      expect(ElMessage.error).toHaveBeenCalledWith('网络错误')
    })

    it('加载数据失败但没有 detail 时应该显示默认错误消息', async () => {
      vi.mocked(connectionsApi.getAll).mockRejectedValue(new Error('Unknown error'))

      mount(ConnectionsView)

      await new Promise(resolve => setTimeout(resolve, 0))

      expect(ElMessage.error).toHaveBeenCalledWith('获取数据失败')
    })
  })

  describe('搜索功能', () => {
    it('点击查询按钮应该触发搜索', async () => {
      vi.mocked(connectionsApi.getAll).mockResolvedValue(mockConnections)

      const wrapper = mount(ConnectionsView)

      // 等待初始加载完成
      await new Promise(resolve => setTimeout(resolve, 0))
      vi.clearAllMocks()

      // 设置搜索条件
      await wrapper.find('input').setValue('测试')
      wrapper.vm.searchForm.host = 'localhost'
      wrapper.vm.searchForm.database = 'test_db'

      // 触发搜索
      wrapper.vm.handleSearch()

      await new Promise(resolve => setTimeout(resolve, 0))

      expect(connectionsApi.getAll).toHaveBeenCalledWith({
        skip: 0,
        limit: 10,
        name: '测试',
        host: 'localhost',
        database_name: 'test_db'
      })
    })

    it('搜索时应该重置到第一页', async () => {
      const wrapper = mount(ConnectionsView)
      wrapper.vm.pagination.page = 5

      wrapper.vm.handleSearch()

      expect(wrapper.vm.pagination.page).toBe(1)
    })

    it('点击重置按钮应该清空搜索条件并重新加载', async () => {
      vi.mocked(connectionsApi.getAll).mockResolvedValue(mockConnections)

      const wrapper = mount(ConnectionsView)

      // 等待初始加载
      await new Promise(resolve => setTimeout(resolve, 0))
      vi.clearAllMocks()

      // 设置搜索条件
      wrapper.vm.searchForm.name = '测试'
      wrapper.vm.searchForm.host = 'localhost'
      wrapper.vm.searchForm.database = 'test_db'
      wrapper.vm.pagination.page = 5

      // 触发重置
      wrapper.vm.handleReset()

      // 检查搜索条件已清空
      expect(wrapper.vm.searchForm.name).toBe('')
      expect(wrapper.vm.searchForm.host).toBe('')
      expect(wrapper.vm.searchForm.database).toBe('')
      expect(wrapper.vm.pagination.page).toBe(1)

      // 检查重新加载数据
      await new Promise(resolve => setTimeout(resolve, 0))
      expect(connectionsApi.getAll).toHaveBeenCalled()
    })
  })

  describe('创建连接', () => {
    it('点击添加按钮应该打开对话框', async () => {
      const wrapper = mount(ConnectionsView)
      await wrapper.vm.$nextTick()

      // 通过组件触发 add 事件
      const pageHeader = wrapper.findComponent({ name: 'PageHeader' })
      await pageHeader.vm.$emit('add')
      await wrapper.vm.$nextTick()

      // 检查对话框状态
      expect(wrapper.vm.dialogVisible).toBe(true)
      expect(wrapper.vm.currentConnection).toBeNull()
    })
  })

  describe('编辑连接', () => {
    it('点击编辑按钮应该打开对话框并设置当前连接', async () => {
      const wrapper = mount(ConnectionsView)

      // 调用编辑方法
      wrapper.vm.handleEdit(mockConnections[0])

      // 检查对话框状态
      expect(wrapper.vm.dialogVisible).toBe(true)
      expect(wrapper.vm.currentConnection).toEqual(mockConnections[0])
    })
  })

  describe('删除连接', () => {
    it('确认删除时应该调用 API 并刷新列表', async () => {
      vi.mocked(ElMessageBox.confirm).mockResolvedValue('confirm' as any)
      vi.mocked(connectionsApi.delete).mockResolvedValue(undefined)
      vi.mocked(connectionsApi.getAll).mockResolvedValue([])

      const wrapper = mount(ConnectionsView)

      // 等待初始加载
      await new Promise(resolve => setTimeout(resolve, 0))
      vi.clearAllMocks()

      // 触发删除
      await wrapper.vm.handleDelete(mockConnections[0])

      // 检查确认对话框被调用
      expect(ElMessageBox.confirm).toHaveBeenCalledWith(
        '确定要删除该连接吗？',
        '提示',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }
      )

      // 检查删除 API 被调用
      expect(connectionsApi.delete).toHaveBeenCalledWith(1)

      // 检查成功消息
      expect(ElMessage.success).toHaveBeenCalledWith('删除成功')

      // 检查刷新列表
      expect(connectionsApi.getAll).toHaveBeenCalled()
    })

    it('取消删除时不应该调用 API', async () => {
      vi.mocked(ElMessageBox.confirm).mockRejectedValue('cancel')

      const wrapper = mount(ConnectionsView)

      // 触发删除
      await wrapper.vm.handleDelete(mockConnections[0])

      // 检查删除 API 未被调用
      expect(connectionsApi.delete).not.toHaveBeenCalled()

      // 检查没有错误消息
      expect(ElMessage.error).not.toHaveBeenCalled()
    })

    it('删除失败时应该显示错误消息', async () => {
      vi.mocked(ElMessageBox.confirm).mockResolvedValue('confirm' as any)
      const error = {
        response: {
          data: {
            detail: '删除失败：连接正在使用中'
          }
        }
      }
      vi.mocked(connectionsApi.delete).mockRejectedValue(error)

      const wrapper = mount(ConnectionsView)

      await wrapper.vm.handleDelete(mockConnections[0])

      expect(ElMessage.error).toHaveBeenCalledWith('删除失败：连接正在使用中')
    })
  })

  describe('测试连接', () => {
    it('点击测试按钮应该打开测试对话框', async () => {
      const wrapper = mount(ConnectionsView)

      // 调用测试方法
      wrapper.vm.handleTest(mockConnections[0])

      // 检查对话框状态
      expect(wrapper.vm.testDialogVisible).toBe(true)
      expect(wrapper.vm.currentConnection).toEqual(mockConnections[0])
    })
  })

  describe('分页功能', () => {
    it('改变每页数量应该重新加载数据', async () => {
      vi.mocked(connectionsApi.getAll).mockResolvedValue(mockConnections)

      const wrapper = mount(ConnectionsView)

      // 等待初始加载
      await new Promise(resolve => setTimeout(resolve, 0))
      vi.clearAllMocks()

      // 改变每页数量
      wrapper.vm.handleSizeChange(20)

      expect(wrapper.vm.pagination.pageSize).toBe(20)
      expect(wrapper.vm.pagination.page).toBe(1)

      await new Promise(resolve => setTimeout(resolve, 0))
      expect(connectionsApi.getAll).toHaveBeenCalledWith({
        skip: 0,
        limit: 20
      })
    })

    it('改变页码应该重新加载数据', async () => {
      vi.mocked(connectionsApi.getAll).mockResolvedValue(mockConnections)

      const wrapper = mount(ConnectionsView)

      // 等待初始加载
      await new Promise(resolve => setTimeout(resolve, 0))
      vi.clearAllMocks()

      // 改变页码
      wrapper.vm.handlePageChange(2)

      expect(wrapper.vm.pagination.page).toBe(2)

      await new Promise(resolve => setTimeout(resolve, 0))
      expect(connectionsApi.getAll).toHaveBeenCalledWith({
        skip: 10,
        limit: 10
      })
    })
  })

  describe('对话框成功回调', () => {
    it('对话框成功后应该刷新列表', async () => {
      vi.mocked(connectionsApi.getAll).mockResolvedValue(mockConnections)

      const wrapper = mount(ConnectionsView)

      // 等待初始加载
      await new Promise(resolve => setTimeout(resolve, 0))
      vi.clearAllMocks()

      // 触发成功回调
      wrapper.vm.handleDialogSuccess()

      await new Promise(resolve => setTimeout(resolve, 0))
      expect(connectionsApi.getAll).toHaveBeenCalled()
    })
  })

  describe('分页总数计算', () => {
    it('返回数据等于 pageSize 时应该估算还有更多数据', async () => {
      // 创建 10 条数据（等于 pageSize）
      const tenConnections: Connection[] = Array.from({ length: 10 }, (_, i) => ({
        id: i + 1,
        name: `测试连接${i + 1}`,
        host: 'localhost',
        port: 3306,
        username: 'root',
        password_encrypted: 'encrypted_password',
        database_name: 'test_db',
        is_active: true,
        created_at: '2024-01-01 10:00:00',
        updated_at: '2024-01-01 10:00:00'
      }))
      vi.mocked(connectionsApi.getAll).mockResolvedValue(tenConnections)

      const wrapper = mount(ConnectionsView)

      await new Promise(resolve => setTimeout(resolve, 0))

      // total = 0 + 10 + 1 = 11
      expect(wrapper.vm.pagination.total).toBe(11)
    })

    it('返回数据少于 pageSize 时应该计算准确总数', async () => {
      // 返回少于 pageSize 的数据
      vi.mocked(connectionsApi.getAll).mockResolvedValue([mockConnections[0]])

      const wrapper = mount(ConnectionsView)

      await new Promise(resolve => setTimeout(resolve, 0))

      // total = 0 + 1 = 1
      expect(wrapper.vm.pagination.total).toBe(1)
    })

    it('返回空数据时 total 应该为 0', async () => {
      vi.mocked(connectionsApi.getAll).mockResolvedValue([])

      const wrapper = mount(ConnectionsView)

      await new Promise(resolve => setTimeout(resolve, 0))

      expect(wrapper.vm.pagination.total).toBe(0)
    })
  })
})
