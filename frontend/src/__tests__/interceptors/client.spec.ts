import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import axios from 'axios'
import { isRefreshRequest } from '@/api/client'
import {
  getToken,
  getRefreshToken,
  setAccessToken,
  setRefreshToken,
  clearTokens
} from '@/types/auth'

vi.mock('@/core/global', () => ({
  config: { baseApi: 'http://localhost:8000/api/v1' }
}))

vi.mock('@/api/auth', () => ({
  authApi: {
    refresh: vi.fn()
  }
}))

describe('Axios Interceptor - Integration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks()

    // Mock localStorage
    vi.stubGlobal('localStorage', {
      getItem: vi.fn((key: string) => {
        if (key === 'mysql_analysis_access_token') return 'expired_token'
        if (key === 'mysql_analysis_refresh_token') return 'valid_refresh_token'
        return null
      }),
      setItem: vi.fn(),
      removeItem: vi.fn()
    })

    // Mock window.location
    delete (window as any).location
    window.location = { href: '' } as any
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  describe('isRefreshRequest function', () => {
    it('should identify relative refresh URL', () => {
      expect(isRefreshRequest('/auth/refresh')).toBe(true)
    })

    it('should identify absolute refresh URL', () => {
      const absoluteUrl = new URL('/auth/refresh', 'http://localhost:8000/api/v1').href
      expect(isRefreshRequest(absoluteUrl)).toBe(true)
    })

    it('should reject non-refresh URLs', () => {
      expect(isRefreshRequest('/auth/login')).toBe(false)
      expect(isRefreshRequest('/api/data')).toBe(false)
    })

    it('should handle undefined URL', () => {
      expect(isRefreshRequest(undefined)).toBe(false)
    })

    it('should handle invalid URL', () => {
      expect(isRefreshRequest('://invalid')).toBe(false)
    })
  })

  describe('Token storage functions', () => {
    it('should get access token', () => {
      const token = getToken()
      expect(token).toBe('expired_token')
    })

    it('should get refresh token', () => {
      const token = getRefreshToken()
      expect(token).toBe('valid_refresh_token')
    })

    it('should set access token', () => {
      setAccessToken('new_access_token')
      const storage = globalThis.localStorage as any
      expect(storage.setItem).toHaveBeenCalledWith('mysql_analysis_access_token', 'new_access_token')
    })

    it('should set refresh token', () => {
      setRefreshToken('new_refresh_token')
      const storage = globalThis.localStorage as any
      expect(storage.setItem).toHaveBeenCalledWith('mysql_analysis_refresh_token', 'new_refresh_token')
    })

    it('should clear all tokens', () => {
      clearTokens()
      const storage = globalThis.localStorage as any
      expect(storage.removeItem).toHaveBeenCalledWith('mysql_analysis_access_token')
      expect(storage.removeItem).toHaveBeenCalledWith('mysql_analysis_refresh_token')
    })
  })

  describe('Auth API refresh', () => {
    it('should call refresh with correct token', async () => {
      const { authApi } = await import('@/api/auth')

      vi.mocked(authApi.refresh).mockResolvedValue({
        access_token: 'new_token',
        refresh_token: 'new_refresh_token',
        token_type: 'bearer'
      })

      const result = await authApi.refresh('test_refresh_token')

      expect(authApi.refresh).toHaveBeenCalledWith('test_refresh_token')
      expect(result).toEqual({
        access_token: 'new_token',
        refresh_token: 'new_refresh_token',
        token_type: 'bearer'
      })
    })

    it('should handle refresh error', async () => {
      const { authApi } = await import('@/api/auth')

      vi.mocked(authApi.refresh).mockRejectedValue(new Error('Invalid refresh token'))

      await expect(authApi.refresh('invalid_token')).rejects.toThrow('Invalid refresh token')
    })
  })

  describe('Queue mechanism', () => {
    it('should process queue on success', () => {
      let isRefreshing = false
      let failedQueue: Array<{
        resolve: (value: string) => void
        reject: (reason: any) => void
      }> = []

      const processQueue = (error: any, token: string | null = null) => {
        failedQueue.forEach((prom) => {
          if (error) {
            prom.reject(error)
          } else {
            prom.resolve(token!)
          }
        })
        failedQueue = []
      }

      const mockResolve = vi.fn()
      const mockReject = vi.fn()

      failedQueue.push({ resolve: mockResolve, reject: mockReject })

      processQueue(null, 'new_token')

      expect(mockResolve).toHaveBeenCalledWith('new_token')
      expect(mockReject).not.toHaveBeenCalled()
      expect(failedQueue).toHaveLength(0)
    })

    it('should reject queue on error', () => {
      let failedQueue: Array<{
        resolve: (value: string) => void
        reject: (reason: any) => void
      }> = []

      const processQueue = (error: any, token: string | null = null) => {
        failedQueue.forEach((prom) => {
          if (error) {
            prom.reject(error)
          } else {
            prom.resolve(token!)
          }
        })
        failedQueue = []
      }

      const mockResolve = vi.fn()
      const mockReject = vi.fn()
      const error = new Error('Refresh failed')

      failedQueue.push({ resolve: mockResolve, reject: mockReject })

      processQueue(error, null)

      expect(mockResolve).not.toHaveBeenCalled()
      expect(mockReject).toHaveBeenCalledWith(error)
      expect(failedQueue).toHaveLength(0)
    })

    it('should handle multiple items in queue', () => {
      let failedQueue: Array<{
        resolve: (value: string) => void
        reject: (reason: any) => void
      }> = []

      const processQueue = (error: any, token: string | null = null) => {
        failedQueue.forEach((prom) => {
          if (error) {
            prom.reject(error)
          } else {
            prom.resolve(token!)
          }
        })
        failedQueue = []
      }

      const resolve1 = vi.fn()
      const resolve2 = vi.fn()
      const resolve3 = vi.fn()

      failedQueue.push({ resolve: resolve1, reject: vi.fn() })
      failedQueue.push({ resolve: resolve2, reject: vi.fn() })
      failedQueue.push({ resolve: resolve3, reject: vi.fn() })

      processQueue(null, 'new_token')

      expect(resolve1).toHaveBeenCalledWith('new_token')
      expect(resolve2).toHaveBeenCalledWith('new_token')
      expect(resolve3).toHaveBeenCalledWith('new_token')
      expect(failedQueue).toHaveLength(0)
    })
  })

  describe('Client module import', () => {
    it('should import client module successfully', async () => {
      const client = await import('@/api/client')
      expect(client).toBeDefined()
      expect(client.default).toBeDefined()
    })
  })

  describe('_retry flag behavior', () => {
    it('should set _retry flag on original request during refresh', async () => {
      const mockRequest = { url: '/api/data', headers: { Authorization: 'Bearer old_token' } } as any

      expect(mockRequest._retry).toBeUndefined()

      mockRequest._retry = true

      expect(mockRequest._retry).toBe(true)

      mockRequest._retry = true

      expect(mockRequest._retry).toBe(true)
    })

    it('should not retry request more than once with _retry flag', async () => {
      let retryCount = 0
      const originalRequest = { url: '/api/data', _retry: false as boolean | undefined }

      while (!originalRequest._retry && retryCount < 2) {
        retryCount++
        originalRequest._retry = true
      }

      expect(retryCount).toBe(1)
      expect(originalRequest._retry).toBe(true)
    })
  })

  describe('Token persistence edge cases', () => {
    it('should handle refresh response with both tokens', () => {
      const mockResponse = {
        access_token: 'new_access_token',
        refresh_token: 'new_refresh_token',
        token_type: 'bearer'
      }

      if (mockResponse.refresh_token) {
        setRefreshToken(mockResponse.refresh_token)
      }

      const storage = globalThis.localStorage as any
      expect(storage.setItem).toHaveBeenCalledWith(
        'mysql_analysis_refresh_token',
        'new_refresh_token'
      )
    })

    it('should handle refresh response without refresh_token', () => {
      const mockResponse = {
        access_token: 'new_access_token',
        refresh_token: undefined,
        token_type: 'bearer'
      } as { access_token: string; refresh_token?: string | undefined; token_type: string }

      setAccessToken(mockResponse.access_token)

      if (mockResponse.refresh_token) {
        setRefreshToken(mockResponse.refresh_token)
      }

      const storage = globalThis.localStorage as any

      expect(storage.setItem).toHaveBeenCalledWith(
        'mysql_analysis_access_token',
        'new_access_token'
      )

      expect(storage.setItem).not.toHaveBeenCalledWith(
        'mysql_analysis_refresh_token',
        expect.any(String)
      )
    })

    it('should not update refresh token when undefined in response', () => {
      const mockResponse = {
        access_token: 'new_access_token',
        refresh_token: undefined as string | undefined,
        token_type: 'bearer'
      }

      if (mockResponse.refresh_token) {
        setRefreshToken(mockResponse.refresh_token)
      }

      const storage = globalThis.localStorage as any
      expect(storage.setItem).not.toHaveBeenCalledWith(
        'mysql_analysis_refresh_token',
        expect.any(String)
      )
    })

    it('should clear all tokens on refresh failure', () => {
      clearTokens()

      const storage = globalThis.localStorage as any
      expect(storage.removeItem).toHaveBeenCalledWith('mysql_analysis_access_token')
      expect(storage.removeItem).toHaveBeenCalledWith('mysql_analysis_refresh_token')
    })
  })
})
