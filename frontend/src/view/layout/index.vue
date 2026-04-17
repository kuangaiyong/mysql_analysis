<template>
  <div class="gva-layout h-screen flex flex-col">
    <div class="gva-header h-16">
      <Header />
    </div>
    <div class="gva-container flex-1 flex overflow-hidden">
      <aside class="gva-aside">
        <Aside />
      </aside>
      <main class="gva-main flex-1 flex flex-col overflow-hidden">
        <div class="gva-tabs">
          <Tabs />
        </div>
        <div class="gva-content flex-1 overflow-auto p-4">
          <router-view v-slot="{ Component, route }">
            <component :is="Component" :key="route.path" />
          </router-view>
        </div>
        <div class="gva-footer h-8 flex items-center justify-center text-sm text-slate-500">
          <Footer />
        </div>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import Header from './header/index.vue'
import Aside from './aside/index.vue'
import Tabs from './tabs/index.vue'
import Footer from './bottom/index.vue'

defineOptions({
  name: 'Layout'
})
</script>

<style scoped>
.gva-layout {
  width: 100%;
  height: 100%;
}

.gva-header {
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
  z-index: 10;
}

.gva-aside {
  width: 220px;
  background-color: var(--el-menu-bg-color, var(--el-bg-color));
  box-shadow: 1px 0 4px rgba(0, 0, 0, 0.08);
  z-index: 9;
}

.gva-main {
  background-color: var(--el-bg-color-page);
}

.gva-content {
  background-color: transparent;
}

.gva-tabs {
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}
</style>
