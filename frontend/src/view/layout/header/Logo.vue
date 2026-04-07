<template>
  <div class="logo flex items-center gap-3">
    <el-icon :size="32" color="#3b82f6">
      <DataAnalysis />
    </el-icon>
    <div class="logo-text">
      <h1 class="text-xl font-bold text-slate-800 dark:text-slate-200">MySQL诊断</h1>
      <p class="text-xs text-slate-500 dark:text-slate-400">性能监控与优化</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { DataAnalysis } from '@element-plus/icons-vue'

defineOptions({
  name: 'Logo'
})
</script>

<style scoped>
.logo {
  cursor: pointer;
}

.logo-text {
  display: flex;
  flex-direction: column;
}
</style>
