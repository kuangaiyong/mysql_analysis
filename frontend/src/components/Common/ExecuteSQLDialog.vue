<template>
  <el-dialog
    v-model="visible"
    title="确认执行 SQL"
    width="600px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <!-- 风险等级标识 -->
    <div class="risk-banner" :style="{ background: classification?.risk_color || '#409EFF' }">
      <el-icon :size="20"><WarningFilled /></el-icon>
      <span>{{ classification?.risk_label || '未知' }} — {{ classification?.description || '' }}</span>
    </div>

    <!-- SQL 预览 -->
    <div class="sql-section">
      <h4>待执行 SQL</h4>
      <pre class="sql-code">{{ sql }}</pre>
    </div>

    <!-- 影响说明 -->
    <div v-if="classification?.impact" class="impact-section">
      <h4>影响说明</h4>
      <p>{{ classification.impact }}</p>
    </div>

    <!-- 回滚命令 -->
    <div v-if="classification?.rollback_sql" class="rollback-section">
      <h4>回滚命令</h4>
      <pre class="sql-code rollback">{{ classification.rollback_sql }}</pre>
    </div>

    <!-- 执行结果 -->
    <div v-if="executeResult" class="result-section">
      <el-result
        :icon="executeResult.success ? 'success' : 'error'"
        :title="executeResult.success ? '执行成功' : '执行失败'"
        :sub-title="executeResult.message || executeResult.error || ''"
      >
        <template v-if="executeResult.success" #extra>
          <p class="result-info">影响行数: {{ executeResult.rows_affected ?? 0 }}</p>
        </template>
      </el-result>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">{{ executeResult ? '关闭' : '取消' }}</el-button>
        <el-button
          v-if="!executeResult"
          type="primary"
          :loading="executing"
          @click="handleExecute"
        >
          确认执行
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { WarningFilled } from '@element-plus/icons-vue'
import { classifySQL, executeSQL, type SQLClassification, type ExecuteSQLResponse } from '@/api/ai'

const props = defineProps<{
  modelValue: boolean
  sql: string
  connectionId: number
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', val: boolean): void
  (e: 'executed', result: ExecuteSQLResponse): void
}>()

const visible = ref(false)
const classification = ref<SQLClassification | null>(null)
const executing = ref(false)
const executeResult = ref<ExecuteSQLResponse | null>(null)

watch(() => props.modelValue, async (val) => {
  visible.value = val
  if (val && props.sql) {
    executeResult.value = null
    executing.value = false
    try {
      classification.value = await classifySQL(props.sql)
    } catch {
      classification.value = null
    }
  }
})

watch(visible, (val) => {
  if (!val) emit('update:modelValue', false)
})

function handleClose() {
  visible.value = false
}

async function handleExecute() {
  if (!props.connectionId || !props.sql) return
  executing.value = true
  try {
    const result = await executeSQL({
      connection_id: props.connectionId,
      sql: props.sql,
    })
    executeResult.value = result
    emit('executed', result)
  } catch (err: any) {
    executeResult.value = {
      success: false,
      error: err?.response?.data?.error || err?.message || '执行失败',
    }
  } finally {
    executing.value = false
  }
}
</script>

<style scoped>
.risk-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  border-radius: 6px;
  color: white;
  font-weight: 600;
  font-size: 14px;
  margin-bottom: 16px;
}

.sql-section,
.impact-section,
.rollback-section,
.result-section {
  margin-bottom: 16px;
}

.sql-section h4,
.impact-section h4,
.rollback-section h4 {
  font-size: 13px;
  color: #606266;
  margin: 0 0 8px 0;
}

.impact-section p {
  font-size: 13px;
  color: #909399;
  margin: 0;
  line-height: 1.6;
}

.sql-code {
  background: #282c34;
  color: #abb2bf;
  padding: 12px 16px;
  border-radius: 6px;
  font-family: 'Fira Code', 'Consolas', monospace;
  font-size: 13px;
  line-height: 1.5;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-all;
  margin: 0;
}

.sql-code.rollback {
  background: #fdf6ec;
  color: #e6a23c;
  border: 1px solid #faecd8;
}

.result-info {
  font-size: 14px;
  color: #606266;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>
