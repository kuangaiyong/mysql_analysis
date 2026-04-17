<template>
  <div class="sql-optimizer-container">
    <!-- 头部 -->
    <div class="header">
      <div class="title">
        <el-icon :size="24"><Edit /></el-icon>
        <h2>AI SQL 优化</h2>
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
            <div class="history-sql">{{ truncateSQL(record.original_sql) }}</div>
            <div class="history-meta">
              <span>{{ formatTime(record.created_at) }}</span>
              <el-button size="small" text type="danger" @click.stop="deleteRecord(record.id)">
                删除
              </el-button>
            </div>
          </div>
        </div>
      </div>
      <!-- 左侧：SQL 输入 -->
      <div class="sql-input-panel">
        <div class="panel-header">
          <h3>📝 输入 SQL</h3>
          <div class="actions">
            <el-button size="small" @click="formatSQL" :disabled="!sqlInput">
              格式化
            </el-button>
            <el-button size="small" @click="clearAll" :disabled="!sqlInput && !optimizationResult">
              清空
            </el-button>
          </div>
        </div>
        
        <el-input
          v-model="sqlInput"
          type="textarea"
          :rows="15"
          placeholder="请输入需要优化的 SQL 语句..."
          class="sql-textarea"
        />
        
        <div class="examples">
          <span class="label">示例：</span>
          <el-tag
            v-for="(example, index) in examples"
            :key="index"
            @click="loadExample(example)"
            class="example-tag"
          >
            {{ example.name }}
          </el-tag>
        </div>
        
        <el-button
          type="primary"
          size="large"
          @click="handleOptimizeSQL"
          :loading="loading && !canCancel"
          :disabled="(!sqlInput || !selectedConnectionId) && !loading"
          class="optimize-btn"
        >
          <span v-if="loading">{{ progressMessage || '分析中...' }}</span>
          <span v-else>🤖 AI 优化分析</span>
        </el-button>
        
        <el-button
          v-if="loading"
          type="danger"
          size="large"
          @click="cancelOptimization"
          class="cancel-btn"
        >
          取消分析
        </el-button>
      </div>

      <!-- 右侧：优化结果 -->
      <div class="result-panel">
        <div class="panel-header">
          <h3>✨ 优化结果</h3>
          <div class="actions" v-if="optimizationResult">
            <el-button size="small" @click="copyOptimizedSQL" v-if="optimizationResult.optimization?.optimized_sql">
              复制优化后 SQL
            </el-button>
          </div>
        </div>

        <div v-if="!optimizationResult && !loading" class="empty-state">
          <el-icon :size="64" color="#909399"><Document /></el-icon>
          <p>输入 SQL 并点击"AI 优化分析"查看结果</p>
        </div>

        <div v-if="loading" class="loading-state">
          <div class="loading-animation">
            <el-icon class="is-loading" :size="48"><Loading /></el-icon>
          </div>
          <p class="loading-title">AI 正在分析 SQL...</p>
          <div class="progress-steps">
            <div 
              v-for="(step, index) in progressSteps" 
              :key="index"
              class="progress-step"
              :class="{ active: currentStep === index + 1, completed: currentStep > index + 1 }"
            >
              <div class="step-icon">
                <el-icon v-if="currentStep > index + 1"><CircleCheck /></el-icon>
                <el-icon v-else-if="currentStep === index + 1" class="is-loading"><Loading /></el-icon>
                <span v-else>{{ index + 1 }}</span>
              </div>
              <span class="step-label">{{ step }}</span>
            </div>
          </div>
          <p class="progress-message" v-if="progressMessage">{{ progressMessage }}</p>
          <p class="progress-tip">💡 分析可能需要 10-30 秒，请耐心等待</p>
        </div>

        <div v-if="optimizationResult && !loading" class="result-content">
          <!-- 问题分析 -->
          <el-card class="result-card" v-if="optimizationResult.optimization?.problem_analysis">
            <template #header>
              <div class="card-header">
                <el-icon><WarningFilled /></el-icon>
                <span>🔍 问题分析</span>
              </div>
            </template>
            <div class="card-content" v-html="renderMarkdown(optimizationResult.optimization.problem_analysis)"></div>
          </el-card>

           <!-- 优化后 SQL（与原始对比） -->
          <el-card class="result-card" v-if="optimizationResult.optimization?.optimized_sql">
            <template #header>
              <div class="card-header">
                <el-icon><CircleCheck /></el-icon>
                <span>优化后 SQL</span>
              </div>
            </template>
            <div class="sql-compare">
              <div class="sql-compare-side">
                <div class="sql-compare-label">原始 SQL</div>
                <pre class="sql-code sql-before"><code>{{ sqlInput }}</code></pre>
              </div>
              <div class="sql-compare-side">
                <div class="sql-compare-label">优化后 SQL</div>
                <pre class="sql-code sql-after"><code>{{ optimizationResult.optimization.optimized_sql }}</code></pre>
              </div>
            </div>
          </el-card>

          <!-- 索引建议 -->
          <el-card class="result-card" v-if="optimizationResult.optimization?.index_suggestions?.length">
            <template #header>
              <div class="card-header">
                <el-icon><Collection /></el-icon>
                <span>📇 索引建议</span>
                <el-button size="small" style="margin-left: auto" @click="copyAllDDL">
                  复制全部 DDL
                </el-button>
              </div>
            </template>
            <div class="index-suggestions">
              <div
                v-for="(suggestion, index) in optimizationResult.optimization.index_suggestions"
                :key="index"
                class="suggestion-item"
              >
                <div class="suggestion-header">
                  <el-tag type="primary">{{ suggestion.table }}</el-tag>
                  <el-tag v-if="suggestion.impact" :type="impactTagType(suggestion.impact)" size="small">
                    {{ suggestion.impact === 'high' ? '高影响' : suggestion.impact === 'medium' ? '中影响' : '低影响' }}
                  </el-tag>
                  <span class="columns">列: {{ suggestion.columns?.join(', ') }}</span>
                </div>
                <div class="ddl-block">
                  <pre class="index-sql"><code>{{ suggestion.create_statement }}</code></pre>
                  <div class="ddl-actions">
                    <el-button size="small" @click="copyText(suggestion.create_statement)">
                      复制
                    </el-button>
                    <el-button size="small" type="primary" plain @click="executeIndexDDL(suggestion)">
                      一键执行
                    </el-button>
                  </div>
                </div>
                <p class="reason">{{ suggestion.reason }}</p>
                <p class="improvement" v-if="suggestion.estimated_improvement">
                  预期提升: {{ suggestion.estimated_improvement }}
                </p>
              </div>
            </div>
          </el-card>

          <!-- 预期效果 -->
          <el-card class="result-card" v-if="optimizationResult.optimization?.expected_improvement">
            <template #header>
              <div class="card-header">
                <el-icon><TrendCharts /></el-icon>
                <span>📈 预期效果</span>
              </div>
            </template>
            <div class="card-content" v-html="renderMarkdown(optimizationResult.optimization.expected_improvement)"></div>
          </el-card>

          <!-- EXPLAIN 对比 -->
          <el-card class="result-card" v-if="optimizationResult.explain_before">
            <template #header>
              <div class="card-header">
                <el-icon><DataAnalysis /></el-icon>
                <span>📊 EXPLAIN {{ optimizationResult.explain_after ? '对比' : '分析' }}</span>
              </div>
            </template>

            <!-- 有优化后 EXPLAIN 时显示对比 -->
            <div v-if="optimizationResult.explain_after" class="explain-comparison">
              <!-- 差异摘要 -->
              <div v-if="explainDiffSummary" class="explain-diff-summary">
                <el-tag v-for="(item, i) in explainDiffSummary" :key="i" :type="item.type" size="small" class="diff-tag">
                  {{ item.text }}
                </el-tag>
              </div>
              <div class="explain-sides">
                <div class="explain-side">
                  <h4>优化前</h4>
                  <el-table :data="formatExplainData(optimizationResult.explain_before)" border size="small" :row-class-name="explainBeforeRowClass">
                    <el-table-column prop="table" label="表" width="100" />
                    <el-table-column prop="type" label="类型" width="80">
                      <template #default="{ row }">
                        <el-tag :type="getAccessTypeTag(row.type)" size="small">{{ row.type }}</el-tag>
                      </template>
                    </el-table-column>
                    <el-table-column prop="key" label="索引" width="120" />
                    <el-table-column prop="rows" label="行数" width="80" />
                    <el-table-column prop="Extra" label="Extra" show-overflow-tooltip />
                  </el-table>
                </div>
                <div class="explain-side">
                  <h4>优化后</h4>
                  <el-table :data="formatExplainData(optimizationResult.explain_after)" border size="small" :row-class-name="explainAfterRowClass">
                    <el-table-column prop="table" label="表" width="100" />
                    <el-table-column prop="type" label="类型" width="80">
                      <template #default="{ row }">
                        <el-tag :type="getAccessTypeTag(row.type)" size="small">{{ row.type }}</el-tag>
                      </template>
                    </el-table-column>
                    <el-table-column prop="key" label="索引" width="120" />
                    <el-table-column prop="rows" label="行数" width="80" />
                    <el-table-column prop="Extra" label="Extra" show-overflow-tooltip />
                  </el-table>
                </div>
              </div>
            </div>

            <!-- 无优化后 EXPLAIN 时只显示原始 -->
            <el-table v-else :data="formatExplainData(optimizationResult.explain_before)" border size="small">
              <el-table-column prop="table" label="表" width="120" />
              <el-table-column prop="type" label="访问类型" width="100">
                <template #default="{ row }">
                  <el-tag :type="getAccessTypeTag(row.type)">{{ row.type }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="key" label="使用索引" width="150" />
              <el-table-column prop="rows" label="扫描行数" width="100" />
              <el-table-column prop="Extra" label="额外信息" show-overflow-tooltip />
            </el-table>
          </el-card>
        </div>
      </div>
    </div>
  </div>

  <!-- 一键执行对话框 -->
  <ExecuteSQLDialog
    v-model="showExecuteDialog"
    :sql="pendingExecuteSQL"
    :connection-id="selectedConnectionId || 0"
    @executed="onSQLExecuted"
  />
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  Edit, 
  Document, 
  Loading, 
  WarningFilled, 
  CircleCheck, 
  Collection, 
  TrendCharts,
  DataAnalysis
} from '@element-plus/icons-vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { format as sqlFormat } from 'sql-formatter'
import { useConnectionStore } from '@/pinia/modules/connection'
import { optimizeSQLStream, getSqlOptRecords, getSqlOptRecordDetail, deleteSqlOptRecord, saveSqlOptRecord } from '@/api/ai'
import type { OptimizeSQLResponse, ExecuteSQLResponse, SqlOptRecord } from '@/api/ai'
import ExecuteSQLDialog from '@/components/Common/ExecuteSQLDialog.vue'

// 全局连接
const connectionStore = useConnectionStore()
const selectedConnectionId = computed(() => connectionStore.selectedConnectionId)

// 状态
const sqlInput = ref('')
const loading = ref(false)
const canCancel = ref(false)
const cancelFn = ref<(() => void) | null>(null)
const progressMessage = ref<string>('')
const currentStep = ref(0)
const progressSteps = ['连接数据库', '执行 EXPLAIN', 'AI 分析', '对比验证', '生成建议']
const optimizationResult = ref<OptimizeSQLResponse | null>(null)

// 历史记录
const showHistory = ref(false)
const historyLoading = ref(false)
const historyRecords = ref<SqlOptRecord[]>([])
const activeRecordId = ref<number | null>(null)

// 一键执行对话框
const showExecuteDialog = ref(false)
const pendingExecuteSQL = ref('')

// 示例 SQL
const examples = [
  {
    name: '全表扫描（无索引）',
    sql: `SELECT * FROM test_no_index_table WHERE category = 'electronics' AND value > 500 ORDER BY created_at DESC LIMIT 100;`
  },
  {
    name: '多表 JOIN',
    sql: `SELECT u.name, u.email, o.amount, o.status, oi.quantity, p.name AS product_name
FROM test_users u
JOIN test_orders o ON u.id = o.user_id
JOIN test_order_items oi ON o.id = oi.order_id
JOIN test_products p ON oi.product_id = p.id
WHERE u.status = 'active' AND o.created_at > '2025-01-01'
ORDER BY o.amount DESC
LIMIT 50;`
  },
  {
    name: '子查询 + 模糊匹配',
    sql: `SELECT * FROM test_users
WHERE id IN (
  SELECT user_id FROM test_orders WHERE amount > (
    SELECT AVG(amount) FROM test_orders
  )
)
AND email LIKE '%@gmail.com'
ORDER BY score DESC;`
  }
]

// 格式化 SQL
function formatSQL() {
  if (!sqlInput.value) return
  
  try {
    sqlInput.value = sqlFormat(sqlInput.value, {
      language: 'mysql',
      tabWidth: 2,
      keywordCase: 'upper'
    })
  } catch {
    ElMessage.warning('SQL 格式化失败，请检查语法')
  }
}

// 清空
function clearAll() {
  sqlInput.value = ''
  optimizationResult.value = null
}

// 加载示例
function loadExample(example: { name: string; sql: string }) {
  sqlInput.value = example.sql
  optimizationResult.value = null
}

// 优化 SQL
function handleOptimizeSQL() {
  if (!sqlInput.value.trim() || !selectedConnectionId.value) {
    return
  }

  loading.value = true
  canCancel.value = true
  optimizationResult.value = null
  progressMessage.value = '开始分析...'
  currentStep.value = 0

  cancelFn.value = optimizeSQLStream(
    {
      connection_id: selectedConnectionId.value,
      sql: sqlInput.value.trim()
    },
    {
      onStatus: (data) => {
        progressMessage.value = data.message || '初始化...'
        currentStep.value = 1
      },
      onContext: (data) => {
        progressMessage.value = data.message || 'EXPLAIN 完成'
        currentStep.value = 2
      },
      onAnalysis: (data) => {
        progressMessage.value = data.message || '正在分析...'
        currentStep.value = 3
      },
      onChunk: () => {
        // SQL 优化返回 JSON，chunk 不直接显示，仅更新进度
        if (currentStep.value < 4) {
          progressMessage.value = 'AI 正在生成优化建议...'
          currentStep.value = 4
        }
      },
      onResult: (data) => {
        progressMessage.value = ''
        currentStep.value = 5
        const result = data as unknown as OptimizeSQLResponse
        if (result.success) {
          optimizationResult.value = result
          autoSaveResult(sqlInput.value.trim(), result)
          ElMessage.success('SQL 优化分析完成')
        } else {
          ElMessage.error(result.error || '优化分析失败')
        }
        loading.value = false
        canCancel.value = false
        cancelFn.value = null
      },
      onError: (data) => {
        progressMessage.value = ''
        ElMessage.error(`优化分析失败: ${data.message}`)
        loading.value = false
        canCancel.value = false
        cancelFn.value = null
      }
    }
  )
}

// 取消优化
function cancelOptimization() {
  if (cancelFn.value) {
    cancelFn.value()
    cancelFn.value = null
  }
  loading.value = false
  canCancel.value = false
  progressMessage.value = ''
  currentStep.value = 0
  ElMessage.info('已取消分析')
}

// 复制文本到剪贴板
async function copyText(text: string) {
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success('已复制到剪贴板')
  } catch {
    ElMessage.error('复制失败')
  }
}

// 复制优化后 SQL
async function copyOptimizedSQL() {
  if (!optimizationResult.value?.optimization?.optimized_sql) return
  await copyText(optimizationResult.value.optimization.optimized_sql)
}

// 复制全部 DDL
async function copyAllDDL() {
  const suggestions = optimizationResult.value?.optimization?.index_suggestions
  if (!suggestions?.length) return
  const ddl = suggestions.map(s => s.create_statement).join('\n\n')
  await copyText(ddl)
}

// 影响级别标签类型
function impactTagType(impact: string): string {
  const map: Record<string, string> = { high: 'danger', medium: 'warning', low: 'info' }
  return map[impact] || 'info'
}

// 渲染 Markdown
function renderMarkdown(content: string): string {
  try {
    return DOMPurify.sanitize(marked(content) as string)
  } catch {
    return content
  }
}

// 格式化 EXPLAIN 数据
function formatExplainData(explainData: unknown): Array<Record<string, unknown>> {
  if (!explainData) return []
  
  if (Array.isArray(explainData)) {
    return explainData
  }
  
  if (typeof explainData === 'object' && explainData !== null) {
    const data = explainData as Record<string, unknown>
    if (data.rows && Array.isArray(data.rows)) {
      return data.rows
    }
  }
  
  return []
}

// 访问类型标签
function getAccessTypeTag(type: string): string {
  const typeMap: Record<string, string> = {
    system: 'success',
    const: 'success',
    eq_ref: 'success',
    ref: 'primary',
    range: 'warning',
    index: 'warning',
    ALL: 'danger'
  }
  return typeMap[type] || 'info'
}

// 访问类型优先级（越小越好）
const ACCESS_TYPE_RANK: Record<string, number> = {
  system: 0, const: 1, eq_ref: 2, ref: 3, fulltext: 4,
  ref_or_null: 5, index_merge: 6, unique_subquery: 7,
  index_subquery: 8, range: 9, index: 10, ALL: 11
}

// EXPLAIN 差异摘要
const explainDiffSummary = computed(() => {
  if (!optimizationResult.value?.explain_before || !optimizationResult.value?.explain_after) return null
  const before = formatExplainData(optimizationResult.value.explain_before)
  const after = formatExplainData(optimizationResult.value.explain_after)
  const diffs: Array<{ text: string; type: string }> = []

  // 行数变化
  const rowsBefore = before.reduce((sum, r) => sum + (Number(r.rows) || 0), 0)
  const rowsAfter = after.reduce((sum, r) => sum + (Number(r.rows) || 0), 0)
  if (rowsBefore > 0 && rowsAfter < rowsBefore) {
    const pct = Math.round((1 - rowsAfter / rowsBefore) * 100)
    diffs.push({ text: `扫描行数减少 ${pct}%`, type: 'success' })
  }

  // 访问类型改善
  for (let i = 0; i < Math.min(before.length, after.length); i++) {
    const bType = String(before[i].type || '')
    const aType = String(after[i].type || '')
    if (bType !== aType) {
      const bRank = ACCESS_TYPE_RANK[bType] ?? 99
      const aRank = ACCESS_TYPE_RANK[aType] ?? 99
      if (aRank < bRank) {
        diffs.push({ text: `${before[i].table}: ${bType} → ${aType}`, type: 'success' })
      }
    }
  }

  // 新增索引使用
  for (let i = 0; i < Math.min(before.length, after.length); i++) {
    if (!before[i].key && after[i].key) {
      diffs.push({ text: `${after[i].table}: 新使用索引 ${after[i].key}`, type: 'primary' })
    }
  }

  return diffs.length > 0 ? diffs : null
})

// 行高亮：对比前后差异的行
function explainBeforeRowClass({ row, rowIndex }: { row: Record<string, unknown>; rowIndex: number }): string {
  if (!optimizationResult.value?.explain_after) return ''
  const after = formatExplainData(optimizationResult.value.explain_after)
  if (rowIndex >= after.length) return ''
  const afterRow = after[rowIndex]
  if (row.type !== afterRow.type || row.key !== afterRow.key || row.rows !== afterRow.rows) {
    return 'explain-row-changed'
  }
  return ''
}

function explainAfterRowClass({ row, rowIndex }: { row: Record<string, unknown>; rowIndex: number }): string {
  if (!optimizationResult.value?.explain_before) return ''
  const before = formatExplainData(optimizationResult.value.explain_before)
  if (rowIndex >= before.length) return 'explain-row-improved'
  const beforeRow = before[rowIndex]
  if (row.type !== beforeRow.type || row.key !== beforeRow.key || row.rows !== beforeRow.rows) {
    return 'explain-row-improved'
  }
  return ''
}

// 一键执行索引 DDL
async function executeIndexDDL(suggestion: { create_statement: string; table: string }) {
  if (!selectedConnectionId.value) {
    ElMessage.warning('请先选择数据库连接')
    return
  }
  pendingExecuteSQL.value = suggestion.create_statement
  showExecuteDialog.value = true
}

function onSQLExecuted(result: ExecuteSQLResponse) {
  if (result.success) {
    ElMessage.success('索引创建成功')
  }
}

// ==================== 历史记录 ====================

async function loadHistory() {
  if (!selectedConnectionId.value) return
  historyLoading.value = true
  try {
    historyRecords.value = await getSqlOptRecords(selectedConnectionId.value)
  } catch {
    ElMessage.error('加载历史记录失败')
  } finally {
    historyLoading.value = false
  }
}

async function loadRecord(recordId: number) {
  try {
    const detail = await getSqlOptRecordDetail(recordId)
    activeRecordId.value = recordId
    sqlInput.value = detail.original_sql
    optimizationResult.value = detail.result as unknown as OptimizeSQLResponse
  } catch {
    ElMessage.error('加载记录详情失败')
  }
}

async function deleteRecord(recordId: number) {
  try {
    await deleteSqlOptRecord(recordId)
    historyRecords.value = historyRecords.value.filter(r => r.id !== recordId)
    if (activeRecordId.value === recordId) {
      activeRecordId.value = null
    }
    ElMessage.success('已删除')
  } catch {
    ElMessage.error('删除失败')
  }
}

async function autoSaveResult(sql: string, result: OptimizeSQLResponse) {
  if (!selectedConnectionId.value) return
  try {
    await saveSqlOptRecord(selectedConnectionId.value, sql, result as unknown as Record<string, any>)
    if (showHistory.value) loadHistory()
  } catch {
    // 保存失败不影响用户体验
  }
}

function truncateSQL(sql: string): string {
  const oneLine = sql.replace(/\s+/g, ' ').trim()
  return oneLine.length > 60 ? oneLine.slice(0, 60) + '...' : oneLine
}

function formatTime(dateStr: string): string {
  const d = new Date(dateStr)
  return `${d.getMonth() + 1}/${d.getDate()} ${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`
}

// 连接变化时自动加载历史
watch(selectedConnectionId, () => {
  if (showHistory.value) loadHistory()
})

watch(showHistory, (val) => {
  if (val) loadHistory()
})
</script>

<style scoped>
.sql-optimizer-container {
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

.sql-input-panel,
.result-panel {
  flex: 1;
  background: white;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #e4e7ed;
}

.panel-header h3 {
  margin: 0;
  font-size: 16px;
  color: #303133;
}

.sql-textarea {
  flex: 1;
}

.sql-textarea :deep(textarea) {
  font-family: 'Fira Code', 'Monaco', monospace;
  font-size: 13px;
  line-height: 1.5;
}

.examples {
  padding: 12px 16px;
  border-top: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  gap: 8px;
}

.examples .label {
  font-size: 13px;
  color: #909399;
}

.example-tag {
  cursor: pointer;
}

.example-tag:hover {
  opacity: 0.8;
}

.optimize-btn {
  margin: 16px;
  width: calc(100% - 32px);
}

.cancel-btn {
  margin: 0 16px 16px 16px;
  width: calc(100% - 32px);
}

.empty-state,
.loading-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #909399;
}

.loading-animation {
  margin-bottom: 20px;
}

.loading-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 30px;
}

.progress-steps {
  display: flex;
  gap: 24px;
  margin-bottom: 24px;
}

.progress-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.step-icon {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f0f2f5;
  color: #909399;
  font-size: 14px;
  transition: all 0.3s ease;
}

.progress-step.active .step-icon {
  background: #409eff;
  color: white;
}

.progress-step.completed .step-icon {
  background: #67c23a;
  color: white;
}

.step-label {
  font-size: 12px;
  color: #909399;
  transition: color 0.3s ease;
}

.progress-step.active .step-label,
.progress-step.completed .step-label {
  color: #303133;
}

.progress-message {
  font-size: 14px;
  color: #606266;
  margin-bottom: 16px;
}

.progress-tip {
  font-size: 13px;
  color: #909399;
}
.result-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.result-card {
  margin-bottom: 16px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}

.card-content {
  line-height: 1.6;
  color: #606266;
}

.sql-code,
.index-sql {
  background: #282c34;
  color: #abb2bf;
  padding: 12px;
  border-radius: 6px;
  overflow-x: auto;
  font-family: 'Fira Code', 'Monaco', monospace;
  font-size: 13px;
  margin: 0;
}

.index-suggestions {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.suggestion-item {
  padding: 12px;
  background: #f5f7fa;
  border-radius: 6px;
}

.suggestion-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.suggestion-header .columns {
  font-size: 13px;
  color: #606266;
}

.index-sql {
  margin: 8px 0;
  padding: 8px;
}

.reason {
  margin: 8px 0 0 0;
  font-size: 13px;
  color: #909399;
}

.improvement {
  margin: 4px 0 0 0;
  font-size: 13px;
  color: #67c23a;
  font-weight: 500;
}

.ddl-block {
  position: relative;
}

.copy-ddl-btn {
  position: absolute;
  top: 8px;
  right: 8px;
}

.ddl-actions {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}

/* SQL 对比视图 */
.sql-compare {
  display: flex;
  gap: 16px;
}

.sql-compare-side {
  flex: 1;
  min-width: 0;
}

.sql-compare-label {
  font-size: 13px;
  font-weight: 600;
  color: #606266;
  margin-bottom: 6px;
}

.sql-before {
  border-left: 3px solid #F56C6C;
}

.sql-after {
  border-left: 3px solid #67C23A;
}

/* EXPLAIN 行高亮 */
:deep(.explain-row-changed) {
  background-color: #fef0f0 !important;
}

:deep(.explain-row-improved) {
  background-color: #f0f9eb !important;
}

.explain-comparison {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.explain-diff-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 8px 0;
}

.diff-tag {
  font-size: 13px;
}

.explain-sides {
  display: flex;
  gap: 16px;
}

.explain-side {
  flex: 1;
  min-width: 0;
}

.explain-side h4 {
  margin: 0 0 8px 0;
  font-size: 13px;
  color: #606266;
}

/* Markdown 样式 */
.card-content :deep(code) {
  background: #f0f2f5;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Fira Code', monospace;
  font-size: 13px;
}

.card-content :deep(ul),
.card-content :deep(ol) {
  padding-left: 20px;
  margin: 8px 0;
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
</style>
