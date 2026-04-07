<template>
  <div class="aside-container h-full py-4">
    <el-menu
      :default-active="activeMenu"
      :collapse="isCollapse"
      :unique-opened="true"
      router
      @select="handleSelect"
      class="aside-menu"
    >
      <!-- 系统配置 -->
      <el-sub-menu index="system-group">
        <template #title>
          <el-icon><Setting /></el-icon>
          <span>系统配置</span>
        </template>
        <el-menu-item v-for="menu in systemMenus" :key="menu.path" :index="menu.path">
          <el-icon><component :is="menu.icon" /></el-icon>
          <template #title>{{ menu.title }}</template>
        </el-menu-item>
      </el-sub-menu>

      <!-- AI 智能 -->
      <el-sub-menu index="ai-group">
        <template #title>
          <el-icon><Cpu /></el-icon>
          <span>AI 智能</span>
        </template>
        <el-menu-item v-for="menu in aiMenus" :key="menu.path" :index="menu.path">
          <el-icon><component :is="menu.icon" /></el-icon>
          <template #title>{{ menu.title }}</template>
        </el-menu-item>
      </el-sub-menu>
    </el-menu>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAppStore } from '@/pinia/modules/app'
import { Cpu, Setting } from '@element-plus/icons-vue'

defineOptions({
  name: 'Aside'
})

const route = useRoute()
const router = useRouter()
const appStore = useAppStore()

const activeMenu = computed(() => route.path)
const isCollapse = computed(() => appStore.layoutSideCollapsed)

const handleSelect = (index: string) => {
  router.push(index)
}

// 系统配置分组
const systemMenus = [
  { path: '/connections', title: '连接管理', icon: 'Connection' }
]


// AI 智能分组
const aiMenus = [
  { path: '/ai-diagnostic', title: 'AI 诊断', icon: 'ChatDotRound' },
  { path: '/sql-optimizer', title: 'AI SQL 优化', icon: 'Edit' },
  { path: '/explain-interpret', title: 'AI EXPLAIN 解读', icon: 'DocumentCopy' },
  { path: '/health-report', title: '健康巡检报告', icon: 'Document' }
]
</script>

<style scoped>
.aside-container {
  overflow-y: auto;
}

.aside-menu {
  border-right: none;
}

.aside-menu:not(.el-menu--collapse) {
  width: 220px;
}
</style>
