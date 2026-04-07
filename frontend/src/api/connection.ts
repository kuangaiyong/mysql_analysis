import service from './client'
import type { Connection, ConnectionCreate, ConnectionUpdate, ConnectionTest, ConnectionTestResult } from '@/types/connection'

export const connectionsApi = {
  getAll: async (params?: { skip?: number; limit?: number }) => {
    const response = await service.get<Connection[]>('/connections/', { params })
    return response.data
  },

  getById: async (id: number) => {
    const response = await service.get<Connection>(`/connections/${id}`)
    return response.data
  },

  create: async (data: ConnectionCreate) => {
    const response = await service.post<Connection>('/connections/', data)
    return response.data
  },

  update: async (id: number, data: ConnectionUpdate) => {
    const response = await service.put<Connection>(`/connections/${id}`, data)
    return response.data
  },

  delete: async (id: number) => {
    await service.delete(`/connections/${id}`)
  },

  test: async (data: ConnectionTest) => {
    const response = await service.post<ConnectionTestResult>('/connections/test', data)
    return response.data
  }
}
