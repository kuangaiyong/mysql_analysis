<template>
  <div class="application-wrapper">
    <el-overlay v-if="loading" :show="loading" :z-index="9999" class="loading-overlay">
      <div class="loading-content">
        <el-icon class="is-loading" :size="48"><Loading /></el-icon>
        <p class="loading-text">{{ loadingText || '加载中...' }}</p>
      </div>
    </el-overlay>

    <div class="status-bar" :class="{ 'status-offline': !isOnline }">
      <div class="status-item">
        <el-icon :size="16" :color="isOnline ? '#67C23A' : '#F56C6C'">
          <component :is="isOnline ? 'Connection' : 'CircleClose'" />
        </el-icon>
        <span>{{ isOnline ? '在线' : '离线' }}</span>
      </div>

      <div class="status-item" v-if="wsStatus">
        <el-icon :size="16" :color="wsStatusColor">
          <component :is="wsStatusIcon" />
        </el-icon>
        <span>WebSocket: {{ wsStatusText }}</span>
      </div>

      <div class="status-item" v-if="lastUpdateTime">
        <el-icon :size="16"><Clock /></el-icon>
        <span>更新: {{ formatTime(lastUpdateTime) }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElNotification } from 'element-plus'
import {
  Loading,
  CircleClose,
  Clock,
  WarnTriangleFilled,
  SuccessFilled
} from '@element-plus/icons-vue'

interface Props {
  loading?: boolean
  loadingText?: string
  wsStatus?: 'connected' | 'disconnected' | 'connecting' | 'error'
  lastUpdateTime?: number
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  loadingText: '加载中...',
  wsStatus: undefined,
  lastUpdateTime: undefined
})

const isOnline = ref(true)

const wsStatusColor = computed(() => {
  const colors = {
    connected: '#67C23A',
    disconnected: '#909399',
    connecting: '#E6A23C',
    error: '#F56C6C'
  }
  return colors[props.wsStatus!] || '#909399'
})

const wsStatusIcon = computed(() => {
  const icons = {
    connected: SuccessFilled,
    disconnected: CircleClose,
    connecting: Loading,
    error: WarnTriangleFilled
  }
  return icons[props.wsStatus!] || CircleClose
})

const wsStatusText = computed(() => {
  const texts = {
    connected: '已连接',
    disconnected: '未连接',
    connecting: '连接中',
    error: '错误'
  }
  return texts[props.wsStatus!] || ''
})

const formatTime = (timestamp: number) => {
  const date = new Date(timestamp)
  const hours = date.getHours().toString().padStart(2, '0')
  const minutes = date.getMinutes().toString().padStart(2, '0')
  const seconds = date.getSeconds().toString().padStart(2, '0')
  return `${hours}:${minutes}:${seconds}`
}

const handleOnline = () => {
  isOnline.value = true
}

const handleOffline = () => {
  isOnline.value = false
}

const handleError = (error: Error) => {
  console.error('Application error:', error)
  ElNotification({
    title: '发生错误',
    message: error.message || '未知错误',
    type: 'error',
    duration: 5000,
    position: 'top-right'
  })
}

const handleWarning = (message: string) => {
  ElNotification({
    title: '警告',
    message,
    type: 'warning',
    duration: 3000,
    position: 'top-right'
  })
}

const handleSuccess = (message: string) => {
  ElNotification({
    title: '成功',
    message,
    type: 'success',
    duration: 2000,
    position: 'top-right'
  })
}

const handleInfo = (message: string) => {
  ElNotification({
    title: '提示',
    message,
    type: 'info',
    duration: 3000,
    position: 'top-right'
  })
}

const showNotification = (options: {
  title: string
  message: string
  type?: 'success' | 'warning' | 'error' | 'info'
  duration?: number
}) => {
  ElNotification({
    title: options.title,
    message: options.message,
    type: options.type || 'info',
    duration: options.duration || 3000,
    position: 'top-right'
  })
}

window.addEventListener('online', handleOnline)
window.addEventListener('offline', handleOffline)
window.onerror = (event: Event | string) => {
  const message = typeof event === 'string' ? event : (event as ErrorEvent).message || '未知错误'
  handleError(new Error(message))
}

onMounted(() => {
  isOnline.value = navigator.onLine
})

onUnmounted(() => {
  window.removeEventListener('online', handleOnline)
  window.removeEventListener('offline', handleOffline)
})

defineExpose({
  handleError,
  handleWarning,
  handleSuccess,
  handleInfo,
  showNotification
})
</script>

<style scoped>
.application-wrapper {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 9999;
}

.loading-overlay {
  pointer-events: auto;
}

.loading-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.loading-text {
  margin-top: 16px;
  font-size: 16px;
}

.status-bar {
  position: fixed;
  top: 0;
  right: 0;
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 8px 16px;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(4px);
  color: #fff;
  font-size: 12px;
  border-bottom-left-radius: 8px;
  z-index: 9998;
  transition: background-color 0.3s;
}

.status-offline {
  background: rgba(245, 108, 108, 0.9);
}

.status-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

@media (max-width: 768px) {
  .status-bar {
    font-size: 10px;
    padding: 6px 12px;
    gap: 12px;
  }
}
</style>
