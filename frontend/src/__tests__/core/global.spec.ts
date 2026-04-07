import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

/**
 * global.ts 测试文件
 * 测试全局配置导出功能
 */

describe('core/global', () => {
  describe('config 导出', () => {
    it('应该正确导出 config 对象', async () => {
      // 动态导入以获取最新状态
      const { config } = await import('@/core/global')

      expect(config).toBeDefined()
      expect(typeof config).toBe('object')
    })

    it('config 应该包含 baseApi 属性', async () => {
      const { config } = await import('@/core/global')

      expect(config).toHaveProperty('baseApi')
      expect(typeof config.baseApi).toBe('string')
      expect(config.baseApi.length).toBeGreaterThan(0)
    })

    it('config 应该包含 wsUrl 属性', async () => {
      const { config } = await import('@/core/global')

      expect(config).toHaveProperty('wsUrl')
      expect(typeof config.wsUrl).toBe('string')
      expect(config.wsUrl.length).toBeGreaterThan(0)
    })

    it('config 应该包含 title 属性', async () => {
      const { config } = await import('@/core/global')

      expect(config).toHaveProperty('title')
      expect(typeof config.title).toBe('string')
      expect(config.title).toBe('MySQL性能诊断与优化系统')
    })

    it('config 应该只包含预期的属性', async () => {
      const { config } = await import('@/core/global')

      const keys = Object.keys(config)
      expect(keys).toHaveLength(3)
      expect(keys).toContain('baseApi')
      expect(keys).toContain('wsUrl')
      expect(keys).toContain('title')
    })
  })

  describe('默认值', () => {
    it('baseApi 应该有有效的默认值', async () => {
      const { config } = await import('@/core/global')

      // 验证 baseApi 是有效的 URL 格式
      expect(config.baseApi).toMatch(/^https?:\/\/.+|^\/api/)
    })

    it('wsUrl 应该有有效的默认值', async () => {
      const { config } = await import('@/core/global')

      // 验证 wsUrl 是有效的 WebSocket URL 格式
      expect(config.wsUrl).toMatch(/^wss?:\/\/.+/)
    })
  })

  describe('模块重导出', () => {
    it('global.ts 应该与 config.ts 导出相同的 config 对象', async () => {
      const { config: globalConfig } = await import('@/core/global')
      const { config: originalConfig } = await import('@/core/config')

      // 验证两个导入的 config 对象属性值相同
      expect(globalConfig.baseApi).toBe(originalConfig.baseApi)
      expect(globalConfig.wsUrl).toBe(originalConfig.wsUrl)
      expect(globalConfig.title).toBe(originalConfig.title)
    })
  })
})
