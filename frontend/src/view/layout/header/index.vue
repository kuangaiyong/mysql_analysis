<template>
  <div class="gva-header-content flex items-center justify-between px-6 h-full">
    <div class="flex items-center gap-6">
      <Logo />
      <div class="header-left-border ml-6">
        <el-breadcrumb separator="/">
          <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
          <el-breadcrumb-item>{{ currentRouteTitle }}</el-breadcrumb-item>
        </el-breadcrumb>
      </div>
    </div>
    <div class="flex items-center gap-4">
      <Tools />
      <UserDropdown />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import Logo from './Logo.vue'
import Tools from './Tools.vue'
import UserDropdown from './UserDropdown.vue'

defineOptions({
  name: 'Header'
})

const route = useRoute()
const currentRouteTitle = computed(() => (route.meta.title as string) || '')
</script>

<style scoped>
.gva-header-content {
  background-color: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color);
}

.header-left-border {
  border-left: 1px solid var(--el-border-color);
  padding-left: 24px;
}
</style>
