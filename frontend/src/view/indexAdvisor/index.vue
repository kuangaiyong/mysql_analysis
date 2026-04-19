<template>
  <div class="page-container analysis-page">
    <div class="header">
      <div class="title">
        <el-icon :size="24"><Grid /></el-icon>
        <h2>AI 索引顾问</h2>
      </div>
      <div class="actions">
        <el-button type="primary" :disabled="!selectedConnectionId || creating" @click="startAnalysis">
          {{ creating ? '创建中...' : '创建分析任务' }}
        </el-button>
      </div>
    </div>

    <div class="main-content">
      <div class="empty-state">
        <el-icon :size="64" color="#909399"><Grid /></el-icon>
        <p>填写连接后点击“创建分析任务”，系统会在任务中心后台执行索引顾问分析。</p>
        <p class="sub-text">包括：冗余索引、缺失索引、未使用索引、合并建议等</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Grid } from '@element-plus/icons-vue'
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
      task_type: 'index_advisor',
      payload: { connection_id: selectedConnectionId.value },
      source_page: 'index-advisor',
    })
  } finally {
    creating.value = false
  }
}
</script>

<style scoped lang="scss">
@import '../analysis-common.scss';
</style>
