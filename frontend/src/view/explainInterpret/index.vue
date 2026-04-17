<template>
  <div class="explain-interpret-container">
    <!-- 头部 -->
    <div class="header">
      <div class="title">
        <el-icon :size="24"><DocumentCopy /></el-icon>
        <h2>AI EXPLAIN 优化分析</h2>
      </div>
      <div class="actions">
        <el-button size="small" @click="showHistory = !showHistory">
          {{ showHistory ? '隐藏历史' : '📜 历史记录' }}
        </el-button>
      </div>
    </div>

    <div class="main-content">
      <!-- 历史侧边栏 -->
      <div v-if="showHistory" class="history-sidebar">
        <div class="sidebar-header">
          <h3>历史记录</h3>
          <el-button size="small" text @click="loadHistory" :loading="historyLoading">
            刷新
          </el-button>
        </div>
        <div v-if="historyRecords.length === 0" class="sidebar-empty">
          暂无历史记录
        </div>
        <div v-else class="history-list">
          <div
            v-for="record in historyRecords"
            :key="record.id"
            class="history-item"
            :class="{ active: activeRecordId === record.id }"
            @click="loadRecord(record.id)"
          >
            <div class="history-sql">{{ truncateSQL(record.sql) }}</div>
            <div class="history-meta">
              <span>{{ formatTime(record.created_at) }}</span>
              <el-button size="small" text type="danger" @click.stop="deleteRecord(record.id)">
                删除
              </el-button>
            </div>
          </div>
        </div>
      </div>

      <!-- 输入区域 -->
      <div class="input-section">
        <h3>输入 SQL</h3>

        <div class="input-group">
          <label>SQL 语句（可带或不带 EXPLAIN 前缀）</label>
          <el-input
            v-model="sqlInput"
            type="textarea"
            :rows="14"
            placeholder="输入 SQL 语句，例如：&#10;SELECT * FROM users WHERE status = 'active'&#10;&#10;系统会自动执行 EXPLAIN 并由 AI 分析"
          />
        </div>

        <div class="examples">
          <span class="label">快速填充示例：</span>
          <el-button size="small" @click="loadExample">加载示例</el-button>
        </div>

        <el-button
          type="primary"
          size="large"
          @click="analyze"
          :loading="loading && !canCancel"
          :disabled="(!sqlInput || !selectedConnectionId) && !loading"
          class="analyze-btn"
        >
          <span v-if="loading">{{ progressMessage || '分析中...' }}</span>
          <span v-else>🤖 AI 优化分析</span>
        </el-button>

        <el-button
          v-if="loading"
          type="danger"
          size="large"
          @click="cancelAnalysis"
          class="cancel-btn"
        >
          取消分析
        </el-button>
      </div>

      <!-- 结果区域 -->
      <div class="result-section">
        <h3>分析结果</h3>

        <div v-if="!result && !loading && !streamingText" class="empty-state">
          <el-icon :size="64" color="#909399"><DocumentCopy /></el-icon>
          <p>选择连接并输入 SQL 后点击"AI 优化分析"</p>
        </div>

        <div v-if="loading && !streamingText" class="loading-state">
          <el-icon class="is-loading" :size="48"><Loading /></el-icon>
          <p>{{ progressMessage || 'AI 正在分析执行计划...' }}</p>
        </div>

        <div v-if="(result || streamingText) && !(loading && !streamingText)" class="result-content">
          <!-- EXPLAIN 结果表格 -->
          <div v-if="explainRows.length > 0" class="explain-table-section">
            <h4>执行计划</h4>

            <!-- 关键指标仪表盘 -->
            <div class="metrics-dashboard">
              <div class="metric-item">
                <span class="metric-value">{{ totalRows }}</span>
                <span class="metric-label">总扫描行数</span>
              </div>
              <div class="metric-item">
                <span class="metric-value" :style="{ color: worstAccessColor }">{{ worstAccessType }}</span>
                <span class="metric-label">最差访问类型</span>
              </div>
              <div class="metric-item">
                <span class="metric-value">{{ explainRows.length }}</span>
                <span class="metric-label">涉及表数</span>
              </div>
              <div v-if="hasFullScan" class="metric-item metric-danger">
                <span class="metric-value">全表扫描</span>
                <span class="metric-label">需优化</span>
              </div>
            </div>

            <el-table :data="explainRows" border size="small" style="width: 100%">
              <el-table-column type="index" label="#" width="50" />
              <el-table-column prop="id" label="id" width="50" />
              <el-table-column prop="select_type" label="select_type" width="120" />
              <el-table-column prop="table" label="table" width="120" />
              <el-table-column label="type" width="100">
                <template #default="{ row }">
                  <el-tag :type="getAccessTypeTag(row.type)" size="small" effect="dark">{{ row.type }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="possible_keys" label="possible_keys" width="160" show-overflow-tooltip />
              <el-table-column prop="key" label="key" width="120">
                <template #default="{ row }">
                  <span :class="{ 'no-key': !row.key }">{{ row.key || 'NULL' }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="key_len" label="key_len" width="80" />
              <el-table-column prop="rows" label="rows" width="90">
                <template #default="{ row }">
                  <span :class="{ 'high-rows': Number(row.rows) > 10000 }">{{ row.rows }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="filtered" label="filtered" width="80">
                <template #default="{ row }">
                  {{ row.filtered }}%
                </template>
              </el-table-column>
              <el-table-column prop="Extra" label="Extra" min-width="180" show-overflow-tooltip />
            </el-table>
          </div>

          <!-- AI 分析（流式或完成后） -->
          <div class="interpretation" v-html="renderMarkdown(streamingText || result?.interpretation || '')"></div>
          <div v-if="loading && streamingText" class="streaming-indicator">
            <el-icon class="is-loading"><Loading /></el-icon>
            <span>AI 正在生成分析...</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { DocumentCopy, Loading } from '@element-plus/icons-vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { useConnectionStore } from '@/pinia/modules/connection'
import {
  explainAnalyzeStream,
  getExplainRecords,
  getExplainRecordDetail,
  deleteExplainRecord,
  saveExplainRecord,
} from '@/api/ai'
import type { ExplainResponse, ExplainRecord } from '@/api/ai'

// 全局连接
const connectionStore = useConnectionStore()
const selectedConnectionId = computed(() => connectionStore.selectedConnectionId)

// 状态
const sqlInput = ref('')
const loading = ref(false)
const canCancel = ref(false)
const abortController = ref<AbortController | null>(null)
const progressMessage = ref('')
const streamingText = ref('')
const result = ref<ExplainResponse | null>(null)

// 历史记录
const showHistory = ref(false)
const historyLoading = ref(false)
const historyRecords = ref<ExplainRecord[]>([])
const activeRecordId = ref<number | null>(null)

// EXPLAIN 行数据
const explainRows = computed(() => {
  if (!result.value?.original_explain) return []
  const data = result.value.original_explain
  if (Array.isArray(data)) return data
  if (data && typeof data === 'object') {
    const d = data as Record<string, unknown>
    if (Array.isArray(d.rows)) return d.rows as Record<string, unknown>[]
  }
  return []
})

// 关键指标
const totalRows = computed(() => {
  return explainRows.value.reduce((sum, r) => sum + (Number(r.rows) || 0), 0).toLocaleString()
})

const ACCESS_TYPE_RANK: Record<string, number> = {
  system: 0, const: 1, eq_ref: 2, ref: 3, fulltext: 4,
  ref_or_null: 5, index_merge: 6, unique_subquery: 7,
  index_subquery: 8, range: 9, index: 10, ALL: 11
}

const worstAccessType = computed(() => {
  let worst = ''
  let worstRank = -1
  for (const row of explainRows.value) {
    const t = String(row.type || '')
    const rank = ACCESS_TYPE_RANK[t] ?? 99
    if (rank > worstRank) {
      worstRank = rank
      worst = t
    }
  }
  return worst || '-'
})

const worstAccessColor = computed(() => {
  const rank = ACCESS_TYPE_RANK[worstAccessType.value] ?? 99
  if (rank <= 3) return '#67C23A'
  if (rank <= 9) return '#E6A23C'
  return '#F56C6C'
})

const hasFullScan = computed(() => {
  return explainRows.value.some((r) => r.type === 'ALL')
})

function getAccessTypeTag(type: string): string {
  const map: Record<string, string> = {
    system: 'success', const: 'success', eq_ref: 'success',
    ref: 'primary', range: 'warning', index: 'warning', ALL: 'danger'
  }
  return map[type] || 'info'
}

// 示例
function loadExample() {
  sqlInput.value = `SELECT u.name, u.email, o.amount, o.status, oi.quantity, p.name AS product_name
FROM test_users u
JOIN test_orders o ON u.id = o.user_id
JOIN test_order_items oi ON o.id = oi.order_id
JOIN test_products p ON oi.product_id = p.id
WHERE u.status = 'active' AND o.created_at > '2025-01-01'
ORDER BY o.amount DESC
LIMIT 50`
}

// 执行 EXPLAIN 并 AI 分析（SSE 流式）
function analyze() {
  if (!sqlInput.value.trim() || !selectedConnectionId.value) return

  loading.value = true
  canCancel.value = true
  result.value = null
  streamingText.value = ''
  progressMessage.value = '开始分析...'

  abortController.value = explainAnalyzeStream(
    selectedConnectionId.value,
    sqlInput.value.trim(),
    {
      onStatus: (data) => {
        progressMessage.value = data.message || '初始化...'
      },
      onContext: (data) => {
        progressMessage.value = 'EXPLAIN 执行完成'
        // 提取 EXPLAIN 结果用于显示表格
        if (data.explain_result) {
          result.value = {
            success: true,
            sql: sqlInput.value.trim(),
            interpretation: '',
            original_explain: data.explain_result,
          } as ExplainResponse
        }
      },
      onAnalysis: (data) => {
        progressMessage.value = data.message || '正在分析...'
      },
      onChunk: (text) => {
        streamingText.value += text
      },
      onResult: (data) => {
        progressMessage.value = ''
        streamingText.value = ''
        if (data.success) {
          result.value = data as ExplainResponse
          autoSaveResult(sqlInput.value.trim(), data as ExplainResponse)
          ElMessage.success('分析完成')
        } else {
          ElMessage.error(data.error || '分析失败')
        }
        loading.value = false
        canCancel.value = false
        abortController.value = null
      },
      onError: (msg) => {
        progressMessage.value = ''
        streamingText.value = ''
        ElMessage.error(`分析失败: ${msg}`)
        loading.value = false
        canCancel.value = false
        abortController.value = null
      },
    }
  )
}

function cancelAnalysis() {
  abortController.value?.abort()
  abortController.value = null
  loading.value = false
  canCancel.value = false
  progressMessage.value = ''
  streamingText.value = ''
  ElMessage.info('已取消分析')
}

// 渲染 Markdown
function renderMarkdown(content: string): string {
  try {
    return DOMPurify.sanitize(marked(content) as string)
  } catch {
    return content
  }
}

// ==================== 历史记录 ====================

async function loadHistory() {
  if (!selectedConnectionId.value) return
  historyLoading.value = true
  try {
    historyRecords.value = await getExplainRecords(selectedConnectionId.value)
  } catch {
    ElMessage.error('加载历史记录失败')
  } finally {
    historyLoading.value = false
  }
}

async function loadRecord(recordId: number) {
  try {
    const detail = await getExplainRecordDetail(recordId)
    activeRecordId.value = recordId
    sqlInput.value = detail.sql
    result.value = detail.result as unknown as ExplainResponse
    streamingText.value = ''
  } catch {
    ElMessage.error('加载记录详情失败')
  }
}

async function deleteRecord(recordId: number) {
  try {
    await deleteExplainRecord(recordId)
    historyRecords.value = historyRecords.value.filter(r => r.id !== recordId)
    if (activeRecordId.value === recordId) activeRecordId.value = null
    ElMessage.success('已删除')
  } catch {
    ElMessage.error('删除失败')
  }
}

async function autoSaveResult(sql: string, resultData: ExplainResponse) {
  if (!selectedConnectionId.value) return
  try {
    await saveExplainRecord(selectedConnectionId.value, sql, resultData as unknown as Record<string, any>)
    if (showHistory.value) loadHistory()
  } catch { /* ignore */ }
}

function truncateSQL(sql: string): string {
  const oneLine = sql.replace(/\s+/g, ' ').trim()
  return oneLine.length > 60 ? oneLine.slice(0, 60) + '...' : oneLine
}

function formatTime(dateStr: string): string {
  const d = new Date(dateStr)
  return `${d.getMonth() + 1}/${d.getDate()} ${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`
}

watch(selectedConnectionId, () => {
  if (showHistory.value) loadHistory()
})

watch(showHistory, (val) => {
  if (val) loadHistory()
})
</script>

<style scoped>
.explain-interpret-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: white;
  border-bottom: 1px solid #e4e7ed;
}

.title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.title h2 {
  margin: 0;
  font-size: 20px;
  color: #303133;
}

.main-content {
  flex: 1;
  display: flex;
  gap: 16px;
  padding: 16px;
  overflow: hidden;
}

.input-section,
.result-section {
  flex: 1;
  background: white;
  border-radius: 8px;
  padding: 16px;
  overflow-y: auto;
}

.input-section h3,
.result-section h3 {
  margin: 0 0 16px 0;
  font-size: 16px;
  color: #303133;
}

.input-group {
  margin-bottom: 16px;
}

.input-group label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  color: #606266;
  font-weight: 500;
}

.input-group :deep(textarea) {
  font-family: 'Fira Code', 'Monaco', monospace;
  font-size: 13px;
}

.examples {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}

.examples .label {
  font-size: 13px;
  color: #909399;
}

.analyze-btn {
  width: 100%;
}

.cancel-btn {
  width: 100%;
  margin-top: 8px;
}

.streaming-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 0;
  color: #409eff;
  font-size: 13px;
}

/* 历史侧边栏 */
.history-sidebar {
  width: 260px;
  min-width: 260px;
  background: white;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #e4e7ed;
}

.sidebar-header h3 {
  margin: 0;
  font-size: 14px;
  color: #303133;
}

.sidebar-empty {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #909399;
  font-size: 13px;
}

.history-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.history-item {
  padding: 10px 12px;
  border-radius: 6px;
  cursor: pointer;
  margin-bottom: 4px;
  transition: background 0.2s;
}

.history-item:hover {
  background: #f5f7fa;
}

.history-item.active {
  background: #ecf5ff;
  border: 1px solid #b3d8ff;
}

.history-sql {
  font-size: 12px;
  color: #303133;
  font-family: 'Fira Code', monospace;
  line-height: 1.4;
  word-break: break-all;
}

.history-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 6px;
  font-size: 11px;
  color: #909399;
}

.empty-state,
.loading-state {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  color: #909399;
}

.empty-state p,
.loading-state p {
  margin: 0;
  font-size: 14px;
}

.result-content {
  padding: 8px 0;
}

/* EXPLAIN 表格区域 */
.explain-table-section {
  margin-bottom: 24px;
}

.explain-table-section h4 {
  margin: 0 0 12px 0;
  font-size: 15px;
  color: #303133;
}

/* 关键指标仪表盘 */
.metrics-dashboard {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
}

.metric-item {
  flex: 1;
  background: #f5f7fa;
  border-radius: 8px;
  padding: 16px;
  text-align: center;
  border: 1px solid #ebeef5;
}

.metric-item.metric-danger {
  background: #fef0f0;
  border-color: #fbc4c4;
}

.metric-value {
  display: block;
  font-size: 22px;
  font-weight: 700;
  color: #303133;
  line-height: 1.2;
}

.metric-danger .metric-value {
  color: #F56C6C;
}

.metric-label {
  display: block;
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.no-key {
  color: #F56C6C;
  font-weight: 600;
}

.high-rows {
  color: #E6A23C;
  font-weight: 600;
}

/* AI 解读 */
.interpretation :deep(h1),
.interpretation :deep(h2),
.interpretation :deep(h3) {
  color: #303133;
  margin: 16px 0 8px;
}

.interpretation :deep(p) {
  color: #606266;
  line-height: 1.6;
  margin: 8px 0;
}

.interpretation :deep(ul),
.interpretation :deep(ol) {
  padding-left: 20px;
  color: #606266;
}

.interpretation :deep(li) {
  margin: 4px 0;
  line-height: 1.6;
}

.interpretation :deep(code) {
  background: #f5f7fa;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Fira Code', 'Monaco', monospace;
  font-size: 13px;
  color: #e6a23c;
}

.interpretation :deep(pre) {
  background: #1e1e1e;
  padding: 16px;
  border-radius: 8px;
  overflow-x: auto;
}

.interpretation :deep(pre code) {
  background: none;
  color: #d4d4d4;
  padding: 0;
}

.interpretation :deep(blockquote) {
  border-left: 4px solid #409eff;
  margin: 8px 0;
  padding: 8px 16px;
  background: #ecf5ff;
  color: #606266;
}

.interpretation :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 8px 0;
}

.interpretation :deep(th),
.interpretation :deep(td) {
  border: 1px solid #e4e7ed;
  padding: 8px 12px;
  text-align: left;
}

.interpretation :deep(th) {
  background: #f5f7fa;
  font-weight: 600;
}
</style>
