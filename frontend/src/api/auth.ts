import service from './client'
import type { LoginRequest, LoginResponse, User, RegisterRequest, RegisterResponse, RefreshTokenResponse } from '@/types/auth'

export const authApi = {
  login: async (data: LoginRequest): Promise<LoginResponse> => {
    const formData = new FormData()
    formData.append('username', data.username)
    formData.append('password', data.password)
    formData.append('remember_me', String(data.rememberMe || false))
    const response = await service.post<LoginResponse>('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    })
    return response.data
  },

  refresh: async (refreshToken: string): Promise<RefreshTokenResponse> => {
    const response = await service.post<RefreshTokenResponse>('/auth/refresh', {
      refresh_token: refreshToken
    })
    return response.data
  },

  logout: async (refreshToken: string): Promise<void> => {
    await service.post('/auth/logout', {
      refresh_token: refreshToken
    })
  },

  register: async (data: RegisterRequest): Promise<RegisterResponse> => {
    const response = await service.post<RegisterResponse>('/auth/register', data)
    return response.data
  },

  getCurrentUser: async (): Promise<User> => {
    const response = await service.get<User>('/auth/me')
    return response.data
  }
}
