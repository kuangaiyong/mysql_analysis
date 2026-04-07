<template>
  <div class="tools flex items-center gap-3">
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
import { computed } from 'vue'
import { FullScreen, Sunny, Moon } from '@element-plus/icons-vue'
import { useAppStore } from '@/pinia/modules/app'

defineOptions({
  name: 'Tools'
})

const appStore = useAppStore()
const isDark = computed(() => appStore.darkMode === 'dark')

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
