export interface LoginRequest {
  username: string
  password: string
  rememberMe?: boolean
}

export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface RefreshTokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface LogoutRequest {
  refresh_token: string
}

export interface User {
  id: number
  username: string
  email?: string
  is_active: boolean
}

export const ACCESS_TOKEN_KEY = 'mysql_analysis_access_token'
export const REFRESH_TOKEN_KEY = 'mysql_analysis_refresh_token'

export const getToken = (): string | null => {
  return localStorage.getItem(ACCESS_TOKEN_KEY)
}

export const setAccessToken = (token: string): void => {
  localStorage.setItem(ACCESS_TOKEN_KEY, token)
}

export const setRefreshToken = (token: string): void => {
  localStorage.setItem(REFRESH_TOKEN_KEY, token)
}

export const getRefreshToken = (): string | null => {
  return localStorage.getItem(REFRESH_TOKEN_KEY)
}

export const removeToken = (): void => {
  clearTokens()
}

export const clearTokens = (): void => {
  localStorage.removeItem(ACCESS_TOKEN_KEY)
  localStorage.removeItem(REFRESH_TOKEN_KEY)
}

export const isAuthenticated = (): boolean => {
  return !!getToken()
}

export interface RegisterRequest {
  username: string
  password: string
}

export interface RegisterResponse {
  id: number
  username: string
  is_active: boolean
  created_at: string
}
