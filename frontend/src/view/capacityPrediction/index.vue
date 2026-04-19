<template>
  <div class="page-container analysis-page">
    <div class="header">
      <div class="title">
        <el-icon :size="24"><TrendCharts /></el-icon>
        <h2>容量风险评估</h2>
      </div>
      <div class="actions">
        <el-button type="primary" :disabled="!selectedConnectionId || creating" @click="startAnalysis">
          {{ creating ? '创建中...' : '创建评估任务' }}
        </el-button>
      </div>
    </div>

    <div class="main-content">
      <div class="empty-state">
        <el-icon :size="64" color="#909399"><TrendCharts /></el-icon>
        <p>点击“创建评估任务”，系统会基于当前证据生成容量风险评估结果。</p>
        <p class="sub-text">包括：磁盘容量、内存使用、连接数、热点风险、建议动作与证据边界</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { TrendCharts } from '@element-plus/icons-vue'
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
      task_type: 'capacity_prediction',
      payload: { connection_id: selectedConnectionId.value },
      source_page: 'capacity-prediction',
    })
  } finally {
    creating.value = false
  }
}
</script>

<style scoped lang="scss">
@import '../analysis-common.scss';
</style>
