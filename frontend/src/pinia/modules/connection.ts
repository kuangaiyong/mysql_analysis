import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { connectionsApi } from '@/api/connection'

export interface ConnectionItem {
  id?: number
  name: string
  host: string
  port: number
  username: string
  database_name?: string
}

export const useConnectionStore = defineStore('connection', () => {
  const currentConnection = ref<ConnectionItem | null>(null)
  const connectionList = ref<ConnectionItem[]>([])
  const selectedConnectionId = ref<number | null>(null)
  const loading = ref(false)

  /** 当前选中的连接对象 */
  const selectedConnection = computed(() => {
    if (!selectedConnectionId.value) return null
    return connectionList.value.find((c) => c.id === selectedConnectionId.value) || null
  })

  /** 从后端加载连接列表，自动选中第一个（若尚未选中） */
  async function loadConnections() {
    if (loading.value) return
    loading.value = true
    try {
      const data = await connectionsApi.getAll()
      connectionList.value = data || []
      // 如果之前选中的连接不在列表中，重置
      if (selectedConnectionId.value) {
        const exists = connectionList.value.some((c) => c.id === selectedConnectionId.value)
        if (!exists) selectedConnectionId.value = null
      }
      // 自动选中第一个
      if (!selectedConnectionId.value && connectionList.value.length > 0) {
        selectedConnectionId.value = connectionList.value[0].id ?? null
      }
    } catch (error) {
      console.error('加载连接列表失败:', error)
    } finally {
      loading.value = false
    }
  }

  /** 切换选中连接 */
  function selectConnection(id: number | null) {
    selectedConnectionId.value = id
    if (id) {
      const conn = connectionList.value.find((c) => c.id === id)
      currentConnection.value = conn || null
    } else {
      currentConnection.value = null
    }
  }

  const setCurrentConnection = (connection: ConnectionItem) => {
    currentConnection.value = connection
  }

  const setConnectionList = (list: ConnectionItem[]) => {
    connectionList.value = list
  }

  const addConnection = (connection: ConnectionItem) => {
    connectionList.value.push(connection)
  }

  const updateConnection = (id: number, connection: Partial<ConnectionItem>) => {
    const index = connectionList.value.findIndex((c) => c.id === id)
    if (index !== -1) {
      const existing = connectionList.value[index]
      connectionList.value[index] = { ...existing, ...connection }
    }
  }

  const deleteConnection = (id: number) => {
    connectionList.value = connectionList.value.filter((c) => c.id !== id)
    if (currentConnection.value?.id === id) {
      currentConnection.value = null
    }
    if (selectedConnectionId.value === id) {
      selectedConnectionId.value = connectionList.value.length > 0
        ? (connectionList.value[0].id ?? null)
        : null
    }
  }

  const clearCurrentConnection = () => {
    currentConnection.value = null
  }

  return {
    currentConnection,
    connectionList,
    selectedConnectionId,
    selectedConnection,
    loading,
    loadConnections,
    selectConnection,
    setCurrentConnection,
    setConnectionList,
    addConnection,
    updateConnection,
    deleteConnection,
    clearCurrentConnection
  }
})
