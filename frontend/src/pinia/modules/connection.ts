import { defineStore } from 'pinia'
import { ref } from 'vue'

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
  }

  const clearCurrentConnection = () => {
    currentConnection.value = null
  }

  return {
    currentConnection,
    connectionList,
    setCurrentConnection,
    setConnectionList,
    addConnection,
    updateConnection,
    deleteConnection,
    clearCurrentConnection
  }
})
