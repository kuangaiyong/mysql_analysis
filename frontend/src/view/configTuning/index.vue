<template>
  <div class="page-container analysis-page">
    <div class="header">
      <div class="title">
        <el-icon :size="24"><SetUp /></el-icon>
        <h2>AI 配置调优</h2>
      </div>
      <div class="actions">
        <el-button type="primary" :disabled="!selectedConnectionId || creating" @click="startAnalysis">
          {{ creating ? '创建中...' : '创建调优任务' }}
        </el-button>
      </div>
    </div>

    <div class="main-content">
      <div class="empty-state">
        <el-icon :size="64" color="#909399"><SetUp /></el-icon>
        <p>点击“创建调优任务”，系统将在后台评估当前配置并给出风险化建议。</p>
        <p class="sub-text">包括：InnoDB 引擎、连接线程、日志、查询缓存、复制、安全配置</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { SetUp } from '@element-plus/icons-vue'
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
      task_type: 'config_tuning',
      payload: { connection_id: selectedConnectionId.value },
      source_page: 'config-tuning',
    })
  } finally {
    creating.value = false
  }
}
</script>

<style scoped lang="scss">
@import '../analysis-common.scss';
</style>
