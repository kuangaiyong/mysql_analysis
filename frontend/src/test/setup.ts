import '@testing-library/vue'
import { config } from '@vue/test-utils'
import { vi } from 'vitest'

// 全局测试配置
config.global.mocks = {
  $router: {
    push: vi.fn(),
    replace: vi.fn(),
  },
}

// Element Plus全局mock
vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn(),
    info: vi.fn(),
  },
  ElNotification: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn(),
    info: vi.fn(),
  },
}))
