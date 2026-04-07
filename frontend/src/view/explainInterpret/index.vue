<template>
  <div class="explain-interpret-container">
    <!-- 头部 -->
    <div class="header">
      <div class="title">
        <el-icon :size="24"><DocumentCopy /></el-icon>
        <h2>AI EXPLAIN 优化分析</h2>
      </div>
      <div class="actions">
        <el-select
          v-model="selectedConnectionId"
          placeholder="选择连接"
          style="width: 200px"
        >
          <el-option
            v-for="conn in connections"
            :key="conn.id"
            :label="conn.name"
            :value="conn.id"
          />
        </el-select>
      </div>
    </div>

    <div class="main-content">
      <!-- 输入区域 -->
      <div class="input-section">
        <h3>📝 输入 EXPLAIN SQL</h3>

        <div class="input-group">
          <label>EXPLAIN SQL 语句</label>
          <el-input
            v-model="sqlInput"
            type="textarea"
            :rows="14"
            placeholder="输入 EXPLAIN SQL 语句，例如：&#10;EXPLAIN SELECT * FROM users WHERE status = 'active'&#10;&#10;也可以直接输入 SELECT 语句，系统会自动添加 EXPLAIN"
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
          :loading="loading"
          :disabled="(!sqlInput || !selectedConnectionId) && !loading"
          class="analyze-btn"
        >
          🤖 AI 优化分析
        </el-button>
      </div>

      <!-- 结果区域 -->
      <div class="result-section">
        <h3>✨ 分析结果</h3>

        <div v-if="!result && !loading" class="empty-state">
          <el-icon :size="64" color="#909399"><DocumentCopy /></el-icon>
          <p>选择连接并输入 EXPLAIN SQL 后点击"AI 优化分析"</p>
        </div>

        <div v-if="loading" class="loading-state">
          <el-icon class="is-loading" :size="48"><Loading /></el-icon>
          <p>AI 正在分析执行计划...</p>
        </div>

        <div v-if="result && !loading" class="result-content">
          <div class="interpretation" v-html="renderMarkdown(result.interpretation || '')"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { DocumentCopy, Loading } from '@element-plus/icons-vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { connectionsApi } from '@/api/connection'
import { explainAnalyze } from '@/api/ai'
import type { ExplainResponse } from '@/api/ai'

// 状态
const sqlInput = ref('')
const loading = ref(false)
const result = ref<ExplainResponse | null>(null)
const selectedConnectionId = ref<number | null>(null)
const connections = ref<Array<{ id: number; name: string }>>([])

onMounted(async () => {
  try {
    const data = await connectionsApi.getAll()
    connections.value = data || []
    if (connections.value.length > 0) {
      selectedConnectionId.value = connections.value[0].id
    }
  } catch {
    ElMessage.error('获取连接列表失败')
  }
})

// 示例
function loadExample() {
  sqlInput.value = `EXPLAIN SELECT u.name, u.email, o.amount, o.status, oi.quantity, p.name AS product_name
FROM test_users u
JOIN test_orders o ON u.id = o.user_id
JOIN test_order_items oi ON o.id = oi.order_id
JOIN test_products p ON oi.product_id = p.id
WHERE u.status = 'active' AND o.created_at > '2025-01-01'
ORDER BY o.amount DESC
LIMIT 50`
}

// 执行 EXPLAIN 并 AI 分析
async function analyze() {
  if (!sqlInput.value.trim() || !selectedConnectionId.value) {
    return
  }

  try {
    loading.value = true
    result.value = null

    const response = await explainAnalyze({
      connection_id: selectedConnectionId.value,
      sql: sqlInput.value.trim()
    })

    if (response.success) {
      result.value = response
      ElMessage.success('分析完成')
    } else {
      ElMessage.error(response.error || '分析失败')
    }
  } catch (error: unknown) {
    const errorMessage = error instanceof Error ? error.message : '未知错误'
    ElMessage.error(`分析失败: ${errorMessage}`)
  } finally {
    loading.value = false
  }
}

// 渲染 Markdown
function renderMarkdown(content: string): string {
  try {
    return DOMPurify.sanitize(marked(content) as string)
  } catch {
    return content
  }
}
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
