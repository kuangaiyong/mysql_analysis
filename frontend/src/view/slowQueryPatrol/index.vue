<template>
  <div class="page-container analysis-page">
    <div class="header">
      <div class="title">
        <el-icon :size="24"><Timer /></el-icon>
        <h2>AI 慢查询巡检</h2>
      </div>
      <div class="actions">
        <el-button type="primary" :disabled="!selectedConnectionId || creating" @click="startAnalysis">
          {{ creating ? '创建中...' : '创建巡检任务' }}
        </el-button>
      </div>
    </div>

    <div class="main-content">
      <div class="empty-state">
        <el-icon :size="64" color="#909399"><Timer /></el-icon>
        <p>点击“创建巡检任务”，系统会在后台完成慢查询巡检并持续记录时间线。</p>
        <p class="sub-text">包括：Top-N 排名、分类聚合、根因分析、优化建议</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Timer } from '@element-plus/icons-vue'
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
      task_type: 'slow_query_patrol',
      payload: { connection_id: selectedConnectionId.value },
      source_page: 'slow-query-patrol',
    })
  } finally {
    creating.value = false
  }
}
</script>

<style scoped lang="scss">
@import '../analysis-common.scss';
</style>
