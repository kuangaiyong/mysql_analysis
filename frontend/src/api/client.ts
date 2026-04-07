import axios, { AxiosInstance, AxiosRequestConfig, InternalAxiosRequestConfig } from 'axios'
import { ElMessage } from 'element-plus'
import { config } from '@/core/global'
import { getToken, getRefreshToken, setAccessToken, setRefreshToken, clearTokens } from '@/types/auth'
import { authApi } from '@/api/auth'

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

const service: AxiosInstance = axios.create({
  baseURL: config.baseApi,
  timeout: 30000
})

service.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = getToken()
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    // AI 接口需要更长超时（5分钟）
    if (config.url?.includes('/ai/')) {
      config.timeout = 300000
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

service.interceptors.response.use(
  (response) => {
    return response
  },
  async (error) => {
    const { config, response } = error

    if (!response) {
      ElMessage.error('网络错误')
      return Promise.reject(error)
    }

    const { status } = response
    const originalRequest = config as AxiosRequestConfig & { _retry?: boolean }

    // 401 错误且不是刷新接口，尝试刷新 Token
    if (status === 401 && !isRefreshRequest(originalRequest.url) && !originalRequest._retry) {
      if (isRefreshing) {
        // 如果正在刷新，加入队列等待
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        })
          .then((token) => {
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${token}`
            }
            return service(originalRequest)
          })
          .catch((err) => Promise.reject(err))
      }

      originalRequest._retry = true
      isRefreshing = true

      try {
        const refreshToken = getRefreshToken()
        if (refreshToken) {
          const { access_token, refresh_token: newRefreshToken } = await authApi.refresh(refreshToken)
          setAccessToken(access_token)
          if (newRefreshToken) {
            setRefreshToken(newRefreshToken)
          }
          processQueue(null, access_token)

          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${access_token}`
          }
          return service(originalRequest)
        } else {
          throw new Error('No refresh token')
        }
      } catch (refreshError) {
        processQueue(refreshError, null)
        clearTokens()
        window.location.href = '/#/login'
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }

    // 401 错误已处理，不显示错误消息
    if (status === 401) {
      return Promise.reject(error)
    }

    // 其他错误
    if (error.response?.data?.detail) {
      ElMessage.error(error.response.data.detail)
    } else {
      ElMessage.error('请求失败')
    }

    return Promise.reject(error)
  }
)

const isRefreshRequest = (url: string | undefined): boolean => {
  if (!url) return false
  try {
    const fullUrl = url.startsWith('http') ? url : new URL(url, config.baseApi).href
    const refreshUrl = new URL('/auth/refresh', config.baseApi).href
    return fullUrl === refreshUrl
  } catch {
    return false
  }
}

const request = <T = any>(
  url: string | AxiosRequestConfig,
  options: AxiosRequestConfig = {}
): Promise<T> => {
  const config: AxiosRequestConfig = typeof url === 'string'
    ? { url, ...options }
    : url
  return service.request(config)
}

export default service
export { request, isRefreshRequest }
