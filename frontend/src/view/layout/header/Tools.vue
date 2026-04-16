<template>
  <div class="tools flex items-center gap-3">
    <!-- 全局数据库连接选择器 -->
    <div class="connection-selector flex items-center gap-2">
      <el-icon color="#409eff"><Connection /></el-icon>
      <el-select
        v-model="connectionStore.selectedConnectionId"
        placeholder="选择数据库连接"
        style="width: 220px"
        :loading="connectionStore.loading"
        @change="handleConnectionChange"
      >
        <el-option
          v-for="conn in connectionStore.connectionList"
          :key="conn.id"
          :label="`${conn.name} (${conn.host}:${conn.port})`"
          :value="conn.id"
        />
      </el-select>
    </div>

    <el-divider direction="vertical" />

    <el-tooltip content="全屏" placement="bottom">
      <el-button circle @click="toggleFullScreen">
        <el-icon>
          <FullScreen />
        </el-icon>
      </el-button>
    </el-tooltip>

    <el-tooltip content="切换主题" placement="bottom">
      <el-button circle @click="toggleTheme">
        <el-icon>
          <Sunny v-if="isDark" />
          <Moon v-else />
        </el-icon>
      </el-button>
    </el-tooltip>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { FullScreen, Sunny, Moon, Connection } from '@element-plus/icons-vue'
import { useAppStore } from '@/pinia/modules/app'
import { useConnectionStore } from '@/pinia/modules/connection'

defineOptions({
  name: 'Tools'
})

const appStore = useAppStore()
const connectionStore = useConnectionStore()
const isDark = computed(() => appStore.darkMode === 'dark')

onMounted(() => {
  connectionStore.loadConnections()
})

function handleConnectionChange(id: number) {
  connectionStore.selectConnection(id)
}

const toggleFullScreen = () => {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen()
  } else {
    document.exitFullscreen()
  }
}

const toggleTheme = () => {
  appStore.toggleDarkMode()
}
</script>

<style scoped>
.connection-selector {
  padding: 0 4px;
}
</style>
