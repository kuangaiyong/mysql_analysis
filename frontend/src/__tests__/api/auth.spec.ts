import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

vi.mock('@/api/client', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn()
  }
}))

import { authApi } from '@/api/auth'
import service from '@/api/client'
import type { LoginRequest, RefreshTokenResponse, RegisterRequest, RegisterResponse, User } from '@/types/auth'

describe('authApi', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('login', () => {
    it('should send login request with remember_me', async () => {
      const mockData: LoginRequest = {
        username: 'testuser',
        password: 'password123',
        rememberMe: true
      }

      ;(service.post as any).mockResolvedValue({
        data: {
          access_token: 'access_token',
          refresh_token: 'refresh_token',
          token_type: 'bearer'
        }
      })

      await authApi.login(mockData)

      expect(service.post).toHaveBeenCalledWith(
        '/auth/login',
        expect.any(FormData),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Content-Type': 'application/x-www-form-urlencoded'
          })
        })
      )
    })

    it('should return access_token and refresh_token', async () => {
      const mockResponse = {
        access_token: 'access_token_123',
        refresh_token: 'refresh_token_456',
        token_type: 'bearer'
      }

      ;(service.post as any).mockResolvedValue({
        data: mockResponse
      })

      const result = await authApi.login({ username: 'test', password: 'test' })

      expect(result).toEqual(mockResponse)
    })

    // 测试 rememberMe 为 undefined 时使用默认值 false
    it('should use false as default when rememberMe is undefined', async () => {
      const mockData: LoginRequest = {
        username: 'testuser',
        password: 'password123'
        // rememberMe 未定义
      }

      ;(service.post as any).mockResolvedValue({
        data: {
          access_token: 'access_token',
          refresh_token: 'refresh_token',
          token_type: 'bearer'
        }
      })

      await authApi.login(mockData)

      // 验证 FormData 中 remember_me 为 'false'
      const callArgs = (service.post as any).mock.calls[0]
      const formData = callArgs[1] as FormData
      expect(formData.get('remember_me')).toBe('false')
    })
    })
  })

  describe('refresh', () => {
    it('should send refresh token request', async () => {
      const mockToken = 'refresh_token_123'
      const mockResponse: RefreshTokenResponse = {
        access_token: 'new_access_token',
        refresh_token: 'new_refresh_token',
        token_type: 'bearer'
      }

      ;(service.post as any).mockResolvedValue({
        data: mockResponse
      })

      const result = await authApi.refresh(mockToken)

      expect(service.post).toHaveBeenCalledWith('/auth/refresh', {
        refresh_token: mockToken
      })
      expect(result).toEqual(mockResponse)
    })
  })

  describe('logout', () => {
    it('should send logout request', async () => {
      const mockToken = 'refresh_token_123'

      ;(service.post as any).mockResolvedValue({
        data: { message: '登出成功' }
      })

      await authApi.logout(mockToken)

      expect(service.post).toHaveBeenCalledWith('/auth/logout', {
        refresh_token: mockToken
      })
      expect(service.post).toHaveBeenCalledWith('/auth/logout', {
        refresh_token: mockToken
      })
    })
  })

  // 注册功能测试
  describe('register', () => {
    it('should send register request with user data', async () => {
      const mockData: RegisterRequest = {
        username: 'newuser',
        password: 'newpassword123'
      }

      const mockResponse: RegisterResponse = {
        id: 1,
        username: 'newuser',
        is_active: true,
        created_at: '2026-03-01T00:00:00Z'
      }

      ;(service.post as any).mockResolvedValue({
        data: mockResponse
      })

      const result = await authApi.register(mockData)

      expect(service.post).toHaveBeenCalledWith('/auth/register', mockData)
      expect(result).toEqual(mockResponse)
    })

    it('should return registered user info', async () => {
      const mockResponse: RegisterResponse = {
        id: 42,
        username: 'testuser',
        is_active: true,
        created_at: '2026-03-01T12:00:00Z'
      }

      ;(service.post as any).mockResolvedValue({
        data: mockResponse
      })

      const result = await authApi.register({
        username: 'testuser',
        password: 'password123'
      })

      expect(result.id).toBe(42)
      expect(result.username).toBe('testuser')
      expect(result.is_active).toBe(true)
    })
  })

  // 获取当前用户信息测试
  describe('getCurrentUser', () => {
    it('should fetch current user info', async () => {
      const mockUser: User = {
        id: 1,
        username: 'testuser',
        email: 'test@example.com',
        is_active: true
      }

      ;(service.get as any).mockResolvedValue({
        data: mockUser
      })

      const result = await authApi.getCurrentUser()

      expect(service.get).toHaveBeenCalledWith('/auth/me')
      expect(result).toEqual(mockUser)
    })

    it('should return user without email (email is optional)', async () => {
      const mockUser: User = {
        id: 2,
        username: 'simpleuser',
        is_active: true
      }

      ;(service.get as any).mockResolvedValue({
        data: mockUser
      })

      const result = await authApi.getCurrentUser()

      expect(result.id).toBe(2)
      expect(result.username).toBe('simpleuser')
      expect(result.email).toBeUndefined()
    })

    it('should return inactive user', async () => {
      const mockUser: User = {
        id: 3,
        username: 'inactiveuser',
        is_active: false
      }

      ;(service.get as any).mockResolvedValue({
        data: mockUser
      })

      const result = await authApi.getCurrentUser()

      expect(result.is_active).toBe(false)
    })
  })

