<template>
  <div class="page-container analysis-page">
    <div class="header">
      <div class="title">
        <el-icon :size="24"><Lock /></el-icon>
        <h2>AI 锁分析</h2>
      </div>
      <div class="actions">
        <el-button type="primary" :disabled="!selectedConnectionId || creating" @click="startAnalysis">
          {{ creating ? '创建中...' : '创建分析任务' }}
        </el-button>
      </div>
    </div>

    <div class="main-content">
      <div class="empty-state">
        <el-icon :size="64" color="#909399"><Lock /></el-icon>
        <p>点击“创建分析任务”，系统将后台执行锁分析并持续记录进度。</p>
        <p class="sub-text">包括：阻塞链分析、死锁检测、热点表检测、锁竞争优化建议</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Lock } from '@element-plus/icons-vue'
import { useConnectionStore } from '@/pinia/modules/connection'
import { useTaskStore } from '@/pinia/modules/task'
import { createAnalysisTaskAndOpen } from '@/view/components/analysisTaskStarter'

const router = useRouter()
const connectionStore = useConnectionStore()
const taskStore = useTaskStore()
const selectedConnectionId = computed(() => connectionStore.selectedConnectionId)
const creating = ref(false)

async function startAnalysis() {
  if (!selectedConnectionId.value || creating.value) return
  creating.value = true
  try {
    await createAnalysisTaskAndOpen(taskStore, router, {
      connection_id: selectedConnectionId.value,
      task_type: 'lock_analysis',
      payload: { connection_id: selectedConnectionId.value },
      source_page: 'lock-analysis',
    })
  } finally {
    creating.value = false
  }
}
</script>

<style scoped lang="scss">
@import '../analysis-common.scss';
</style>
