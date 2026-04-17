<template>
  <div class="page-container analysis-page">
    <div class="header">
      <div class="title">
        <el-icon :size="24"><Grid /></el-icon>
        <h2>AI 索引顾问</h2>
      </div>
      <div class="actions">
        <el-button type="primary" :loading="analyzing" :disabled="!selectedConnectionId" @click="startAnalysis">
          开始分析
        </el-button>
        <el-button v-if="analyzing" type="danger" plain @click="cancelAnalysis">取消</el-button>
      </div>
    </div>

    <div class="main-content">
      <!-- 分析中 -->
      <div v-if="analyzing" class="analyzing-state">
        <el-icon class="is-loading" :size="32" color="#409EFF"><Loading /></el-icon>
        <p class="status-text">{{ statusMessage }}</p>
        <div v-if="streamingText" class="streaming-output" v-html="renderedStreaming"></div>
      </div>

      <!-- 结果 -->
      <div v-else-if="result" class="result-section">
        <!-- 摘要 -->
        <el-alert v-if="result.structured?.summary" :title="result.structured.summary" type="info" show-icon :closable="false" class="summary-alert" />

        <!-- 问题列表 -->
        <div v-if="issues.length > 0" class="issues-section">
          <h3 class="section-title">
            <el-icon><WarningFilled /></el-icon>
            索引问题（共 {{ issues.length }} 项）
          </h3>
          <el-table :data="issues" stripe border style="width: 100%">
            <el-table-column label="严重等级" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="severityType(row.severity)" size="small" effect="dark">{{ severityLabel(row.severity) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="类型" width="100" align="center">
              <template #default="{ row }">
                <el-tag size="small">{{ row.type || '-' }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="表" prop="table" width="150" show-overflow-tooltip />
            <el-table-column label="问题描述" prop="title" min-width="200" show-overflow-tooltip />
            <el-table-column label="原因" prop="reason" min-width="200" show-overflow-tooltip />
            <el-table-column label="建议 SQL" min-width="260">
              <template #default="{ row }">
                <code v-if="row.create_statement" class="sql-code">{{ row.create_statement }}</code>
                <code v-else-if="row.drop_statement" class="sql-code danger">{{ row.drop_statement }}</code>
                <span v-else>-</span>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <!-- 详细分析 -->
        <div v-if="result.structured?.detail" class="detail-section">
          <h3 class="section-title">详细分析</h3>
          <div class="markdown-body" v-html="renderedDetail"></div>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-else class="empty-state">
        <el-icon :size="64" color="#909399"><Grid /></el-icon>
        <p>点击"开始分析"，AI 将全面分析索引使用情况</p>
        <p class="sub-text">包括：冗余索引、缺失索引、未使用索引、合并建议等</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { Grid, Loading, WarningFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { useConnectionStore } from '@/pinia/modules/connection'
import { indexAdvisorStream } from '@/api/ai'

const connectionStore = useConnectionStore()
const selectedConnectionId = computed(() => connectionStore.selectedConnectionId)

const analyzing = ref(false)
const statusMessage = ref('')
const streamingText = ref('')
const result = ref<any>(null)
const abortController = ref<AbortController | null>(null)

const issues = computed(() => result.value?.structured?.issues || [])
const renderedStreaming = computed(() => DOMPurify.sanitize(marked.parse(streamingText.value) as string))
const renderedDetail = computed(() => DOMPurify.sanitize(marked.parse(result.value?.structured?.detail || '') as string))

function severityLabel(s: string) { return { critical: '严重', warning: '警告', info: '建议' }[s] || s }
function severityType(s: string) { return { critical: 'danger', warning: 'warning', info: 'info' }[s] || 'info' }

function startAnalysis() {
  if (!selectedConnectionId.value) return
  analyzing.value = true
  statusMessage.value = '正在初始化...'
  streamingText.value = ''
  result.value = null

  abortController.value = indexAdvisorStream(selectedConnectionId.value, {
    onStatus: (data) => { statusMessage.value = data.message || '处理中...' },
    onContext: (data) => { statusMessage.value = data.message || '上下文已收集' },
    onAnalysis: (data) => { statusMessage.value = data.message || '正在分析...' },
    onChunk: (text) => { streamingText.value += text },
    onResult: (data) => { result.value = data; analyzing.value = false },
    onError: (err) => { ElMessage.error(err); analyzing.value = false },
  })
}

function cancelAnalysis() {
  abortController.value?.abort()
  analyzing.value = false
  statusMessage.value = ''
}
</script>

<style scoped lang="scss">
@import '../analysis-common.scss';
</style>
