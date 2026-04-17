<template>
  <div class="page-container analysis-page">
    <div class="header">
      <div class="title">
        <el-icon :size="24"><SetUp /></el-icon>
        <h2>AI 配置调优</h2>
      </div>
      <div class="actions">
        <el-button type="primary" :loading="analyzing" :disabled="!selectedConnectionId" @click="startAnalysis">
          开始分析
        </el-button>
        <el-button v-if="analyzing" type="danger" plain @click="cancelAnalysis">取消</el-button>
      </div>
    </div>

    <div class="main-content">
      <div v-if="analyzing" class="analyzing-state">
        <el-icon class="is-loading" :size="32" color="#409EFF"><Loading /></el-icon>
        <p class="status-text">{{ statusMessage }}</p>
        <div v-if="streamingText" class="streaming-output" v-html="renderedStreaming"></div>
      </div>

      <div v-else-if="result" class="result-section">
        <el-alert v-if="result.structured?.summary" :title="result.structured.summary" type="info" show-icon :closable="false" class="summary-alert" />

        <div v-if="issues.length > 0" class="issues-section">
          <h3 class="section-title">
            <el-icon><WarningFilled /></el-icon>
            配置建议（共 {{ issues.length }} 项）
          </h3>
          <el-table :data="issues" stripe border style="width: 100%">
            <el-table-column label="严重等级" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="severityType(row.severity)" size="small" effect="dark">{{ severityLabel(row.severity) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="分类" width="110" align="center">
              <template #default="{ row }">
                <el-tag size="small">{{ row.category || '-' }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="参数" prop="parameter" width="220" show-overflow-tooltip />
            <el-table-column label="当前值" prop="current_value" width="150" align="center" />
            <el-table-column label="建议值" width="150" align="center">
              <template #default="{ row }">
                <span class="recommended-value">{{ row.recommended_value }}</span>
              </template>
            </el-table-column>
            <el-table-column label="风险" width="80" align="center">
              <template #default="{ row }">
                <el-tag :type="row.risk === 'high' ? 'danger' : row.risk === 'medium' ? 'warning' : 'success'" size="small">{{ row.risk || 'low' }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="需重启" width="80" align="center">
              <template #default="{ row }">
                <el-tag v-if="row.requires_restart" type="danger" size="small">是</el-tag>
                <el-tag v-else type="success" size="small">否</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="修改原因" prop="reason" min-width="200" show-overflow-tooltip />
            <el-table-column label="修改命令" prop="command" min-width="250" show-overflow-tooltip />
          </el-table>
        </div>

        <div v-if="result.structured?.detail" class="detail-section">
          <h3 class="section-title">详细分析</h3>
          <div class="markdown-body" v-html="renderedDetail"></div>
        </div>
      </div>

      <div v-else class="empty-state">
        <el-icon :size="64" color="#909399"><SetUp /></el-icon>
        <p>点击"开始分析"，AI 将全面分析 MySQL 配置参数</p>
        <p class="sub-text">包括：InnoDB 引擎、连接线程、日志、查询缓存、复制、安全配置</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { SetUp, Loading, WarningFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { useConnectionStore } from '@/pinia/modules/connection'
import { configTuningStream } from '@/api/ai'

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

  abortController.value = configTuningStream(selectedConnectionId.value, {
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
}
</script>

<style scoped lang="scss">
@import '../analysis-common.scss';
</style>
