<template>
  <div class="tabs-container h-full flex items-center px-4">
    <el-scrollbar class="flex-1">
      <div class="flex gap-2">
        <el-tag
          v-for="tag in visitedViews"
          :key="tag.path"
          :closable="!tag.meta?.affix"
          :type="isActive(tag) ? 'primary' : 'info'"
          :effect="isActive(tag) ? 'dark' : 'plain'"
          @click="handleClick(tag)"
          @close="handleClose(tag)"
          class="cursor-pointer"
        >
          {{ tag.meta?.title }}
        </el-tag>
      </div>
    </el-scrollbar>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAppStore } from '@/pinia/modules/app'

defineOptions({
  name: 'Tabs'
})

const router = useRouter()
const route = useRoute()
const appStore = useAppStore()

const visitedViews = computed(() => appStore.visitedViews)

const isActive = (tag: any) => {
  return tag.path === route.path
}

const handleClick = (tag: any) => {
  router.push(tag.path)
}

const handleClose = (tag: any) => {
  appStore.delView(tag)
}
</script>

<style scoped>
.tabs-container {
  background-color: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color);
}
</style>
