<template>
  <el-config-provider :locale="zhCn">
    <router-view />
  </el-config-provider>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import zhCn from 'element-plus/dist/locale/zh-cn.js'
import { useAppStore } from '@/pinia/modules/app'

defineOptions({
  name: 'App'
})

onMounted(() => {
  const appStore = useAppStore()
  if (appStore.darkMode === 'dark') {
    document.documentElement.classList.add('dark')
  }
})
</script>

<style>
#app {
  width: 100%;
  height: 100%;
}
</style>
