<template>
  <div class="ai-diagnostic-container">
    <!-- 头部 -->
    <div class="header">
      <div class="title">
        <el-icon :size="24"><Cpu /></el-icon>
        <h2>AI 诊断助手</h2>
      </div>
      <div class="actions">
        <el-tag v-if="aiStatus.enabled" type="success">
          {{ aiStatus.provider }} - {{ aiStatus.model }}
        </el-tag>
        <el-tag v-else type="danger">AI 服务未启用</el-tag>
      </div>
    </div>

    <div class="main-content">
      <!-- 左侧：会话历史 + 快捷问题 -->
      <div class="sidebar">
        <!-- 会话历史 -->
        <div class="session-section">
          <div class="section-header">
            <h3>对话历史</h3>
            <el-button size="small" type="primary" @click="startNewSession" :disabled="!selectedConnectionId">
              新建对话
            </el-button>
          </div>
          <div class="session-list">
            <div
              v-for="session in sessions"
              :key="session.id"
              :class="['session-item', { active: activeSessionId === session.id }]"
              @click="loadSession(session.id)"
            >
              <div class="session-info">
                <span class="session-title">{{ session.title }}</span>
                <span class="session-meta">{{ formatTime(session.updated_at) }} · {{ session.message_count }} 条</span>
              </div>
              <div class="session-actions" @click.stop>
                <el-dropdown trigger="click" size="small">
                  <el-icon class="more-btn"><MoreFilled /></el-icon>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item @click="renameSession(session)">重命名</el-dropdown-item>
                      <el-dropdown-item @click="removeSession(session.id)" divided>删除</el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
            </div>
            <div v-if="sessions.length === 0" class="no-sessions">
              暂无对话历史
            </div>
          </div>
        </div>

        <!-- 快捷问题（可折叠） -->
        <el-collapse class="quick-collapse">
          <el-collapse-item title="快捷诊断" name="quick">
            <div class="question-list">
              <el-button
                v-for="(config, key) in quickQuestions"
                :key="key"
                :type="activeQuestion === key ? 'primary' : 'default'"
                @click="askQuickQuestion(key as QuestionType)"
                :loading="loading && activeQuestion === key"
                class="question-btn"
                size="small"
              >
                {{ config.label }}
              </el-button>
            </div>
          </el-collapse-item>
        </el-collapse>
      </div>

      <!-- 右侧：对话区域 -->
      <div class="chat-area">
        <!-- 消息列表 -->
        <div class="messages" ref="messagesContainer">
          <div v-if="messages.length === 0" class="empty-state">
            <el-icon :size="64" color="#909399"><ChatDotRound /></el-icon>
            <p>选择一个快捷问题或输入您的问题开始诊断</p>
          </div>

          <div
            v-for="(msg, index) in messages"
            :key="index"
            :class="['message', msg.role]"
          >
            <div class="message-header">
              <el-avatar :size="32" :class="msg.role === 'user' ? 'user-avatar' : 'ai-avatar'">
                {{ msg.role === 'user' ? 'U' : 'AI' }}
              </el-avatar>
              <span class="role-name">{{ msg.role === 'user' ? '您' : 'AI 助手' }}</span>
            </div>
            <!-- 结构化 AI 响应 -->
            <template v-if="msg.role === 'assistant' && hasStructuredContent(msg.content)">
              <div class="structured-response">
                <!-- 摘要卡片 -->
                <div v-if="parseStructuredContent(msg.content).summary" class="summary-card">
                  <div class="summary-header">
                    <el-icon color="#409eff"><InfoFilled /></el-icon>
                    <span>诊断摘要</span>
                  </div>
                  <div class="summary-body" v-html="renderMarkdown(parseStructuredContent(msg.content).summary)"></div>
                </div>

                <!-- 问题卡片列表 -->
                <div v-if="parseStructuredContent(msg.content).issues.length > 0" class="issues-cards">
                  <div class="issues-header">
                    <el-icon color="#E6A23C"><WarningFilled /></el-icon>
                    <span>发现 {{ parseStructuredContent(msg.content).issues.length }} 个问题</span>
                  </div>
                  <div
                    v-for="(issue, i) in parseStructuredContent(msg.content).issues"
                    :key="i"
                    class="issue-card"
                  >
                    <div class="issue-card-header">
                      <el-tag
                        :type="issue.severity === 'critical' ? 'danger' : issue.severity === 'warning' ? 'warning' : 'info'"
                        size="small"
                        effect="dark"
                      >
                        {{ issue.severity === 'critical' ? '严重' : issue.severity === 'warning' ? '警告' : '建议' }}
                      </el-tag>
                      <span class="issue-title">{{ issue.title || issue.description }}</span>
                      <el-tag v-if="issue.category" size="small" type="primary" plain>{{ issue.category }}</el-tag>
                    </div>
                    <p v-if="issue.detail" class="issue-detail">{{ issue.detail }}</p>
                    <p v-if="issue.suggestion" class="issue-suggestion">
                      <el-icon color="#67c23a"><CircleCheck /></el-icon>
                      {{ issue.suggestion }}
                    </p>
                    <div v-if="issue.fix_command" class="issue-fix">
                      <pre class="fix-sql"><code>{{ issue.fix_command }}</code></pre>
                      <div class="fix-actions">
                        <el-tag v-if="issue.fix_risk" :type="issue.fix_risk === 'low' ? 'success' : issue.fix_risk === 'medium' ? 'warning' : 'danger'" size="small">
                          风险: {{ issue.fix_risk === 'low' ? '低' : issue.fix_risk === 'medium' ? '中' : '高' }}
                        </el-tag>
                        <el-button size="small" @click="copyText(issue.fix_command)">复制</el-button>
                        <el-button size="small" type="primary" plain @click="openExecuteDialog(issue.fix_command)">一键执行</el-button>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- 详细分析 (可折叠) -->
                <div v-if="parseStructuredContent(msg.content).detail" class="detail-section">
                  <el-collapse>
                    <el-collapse-item title="查看详细分析">
                      <div class="message-content" v-html="renderMarkdown(parseStructuredContent(msg.content).detail)"></div>
                    </el-collapse-item>
                  </el-collapse>
                </div>
              </div>
            </template>
            <!-- 普通消息 -->
            <div v-else class="message-content" v-html="renderMarkdown(msg.content)"></div>
          </div>

          <div v-if="loading" class="message assistant loading">
            <div class="message-header">
              <el-avatar :size="32" class="ai-avatar">AI</el-avatar>
              <span class="role-name">AI 助手</span>
            </div>
            <div v-if="streamingContent" class="message-content" v-html="renderMarkdown(streamingContent)"></div>
            <div class="message-content" v-else>
              <el-icon class="is-loading"><Loading /></el-icon>
              <span>{{ progressMessage || '正在分析中...' }}</span>
              <el-button size="small" type="danger" plain @click="cancelRequest" style="margin-left: 12px">
                取消
              </el-button>
            </div>
          </div>
        </div>

        <!-- 输入区域 -->
        <div class="input-area">
          <el-input
            v-model="userInput"
            type="textarea"
            :rows="3"
            placeholder="输入问题，如：为什么数据库最近变慢了？"
            :disabled="loading || !selectedConnectionId"
            @keyup.ctrl.enter="sendMessage"
          />
          <div class="input-actions">
            <span class="hint">Ctrl + Enter 发送</span>
            <el-button
              type="primary"
              @click="sendMessage"
              :loading="loading"
              :disabled="!userInput.trim() || !selectedConnectionId"
            >
              发送
            </el-button>
          </div>
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
import { ref, onMounted, nextTick, watch, computed } from 'vue'
import { Cpu, ChatDotRound, Loading, MoreFilled, WarningFilled, InfoFilled, CircleCheck } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { useConnectionStore } from '@/pinia/modules/connection'
import {
  getAIStatus,
  getSessions,
  getSessionDetail,
  updateSessionTitle,
  deleteSession as deleteSessionApi,
  ssePost,
  type AIStatusResponse,
  type DiagnosisSession,
} from '@/api/ai'
import type { ExecuteSQLResponse } from '@/api/ai'
import ExecuteSQLDialog from '@/components/Common/ExecuteSQLDialog.vue'

// 类型定义
type QuestionType = 'slow_database' | 'config_issues' | 'slow_queries' | 'index_suggestions' | 'buffer_pool' | 'lock_analysis' | 'connection_health' | 'io_bottleneck'

// 全局连接
const connectionStore = useConnectionStore()
const selectedConnectionId = computed(() => connectionStore.selectedConnectionId)
const aiStatus = ref<AIStatusResponse>({ enabled: false, provider: '', model: '', cache_enabled: false, rate_limit: 100 })
const messages = ref<Array<{ role: string; content: string }>>([])
const userInput = ref('')

// 一键执行对话框
const showExecuteDialog = ref(false)
const pendingExecuteSQL = ref('')

function openExecuteDialog(sql: string) {
  if (!selectedConnectionId.value) {
    ElMessage.warning('请先选择数据库连接')
    return
  }
  pendingExecuteSQL.value = sql
  showExecuteDialog.value = true
}

function onSQLExecuted(result: ExecuteSQLResponse) {
  if (result.success) {
    ElMessage.success('执行成功')
  }
}
const loading = ref(false)
const activeQuestion = ref<string | null>(null)
const progressStep = ref<string>('')
const progressMessage = ref<string>('')
const streamingContent = ref<string>('')
const messagesContainer = ref<HTMLElement | null>(null)
const cancelFn = ref<(() => void) | null>(null)

// 会话管理状态
const sessions = ref<DiagnosisSession[]>([])
const activeSessionId = ref<number | null>(null)

// 快捷问题
const quickQuestions: Record<string, { label: string }> = {
  slow_database: { label: '🔍 为什么数据库变慢？' },
  config_issues: { label: '⚙️ 分析配置问题' },
  slow_queries: { label: '🐌 Top 5 慢查询' },
  index_suggestions: { label: '📇 索引建议' },
  buffer_pool: { label: '💾 Buffer Pool 分析' },
  lock_analysis: { label: '🔒 锁等待分析' },
  connection_health: { label: '🔌 连接健康检查' },
  io_bottleneck: { label: '💿 I/O 瓶颈分析' },
}

// 初始化
onMounted(async () => {
  await loadAIStatus()
})

// 连接变更时清空状态并加载会话列表
watch(selectedConnectionId, async (newId, oldId) => {
  if (newId !== oldId) {
    // 切换连接时清空当前会话状态
    cancelRequest()
    activeSessionId.value = null
    messages.value = []
    sessions.value = []
  }
  if (newId) {
    await loadSessions()
  }
})

// 加载 AI 状态
async function loadAIStatus() {
  try {
    aiStatus.value = await getAIStatus()
  } catch (error) {
    console.error('加载 AI 状态失败:', error)
  }
}

// 加载会话列表
async function loadSessions() {
  if (!selectedConnectionId.value) return
  try {
    const res = await getSessions(selectedConnectionId.value)
    sessions.value = res.data || []
  } catch (error) {
    console.error('加载会话列表失败:', error)
  }
}

// 加载指定会话
async function loadSession(sessionId: number) {
  try {
    const res = await getSessionDetail(sessionId)
    const detail = res.data
    activeSessionId.value = sessionId
    messages.value = detail.messages.map((m: any) => ({
      role: m.role,
      content: m.content,
    }))
    scrollToBottom()
  } catch (error) {
    console.error('加载会话详情失败:', error)
    ElMessage.error('加载会话失败')
  }
}

// 新建对话
function startNewSession() {
  activeSessionId.value = null
  messages.value = []
  cancelRequest()
}

// 重命名会话
async function renameSession(session: DiagnosisSession) {
  try {
    const { value } = await ElMessageBox.prompt('请输入新标题', '重命名对话', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputValue: session.title,
      inputPattern: /\S+/,
      inputErrorMessage: '标题不能为空',
    })
    await updateSessionTitle(session.id, value)
    session.title = value
    ElMessage.success('已重命名')
  } catch {
    // 用户取消
  }
}

// 删除会话
async function removeSession(sessionId: number) {
  try {
    await ElMessageBox.confirm('确定删除此对话？删除后无法恢复。', '确认删除', {
      type: 'warning',
    })
    await deleteSessionApi(sessionId)
    sessions.value = sessions.value.filter((s) => s.id !== sessionId)
    if (activeSessionId.value === sessionId) {
      activeSessionId.value = null
      messages.value = []
    }
    ElMessage.success('已删除')
  } catch {
    // 用户取消
  }
}

// 发送消息（使用会话持久化端点）
async function sendMessage() {
  if (!userInput.value.trim() || !selectedConnectionId.value || loading.value) {
    return
  }

  const question = userInput.value.trim()
  userInput.value = ''

  // 添加用户消息到本地
  messages.value.push({ role: 'user', content: question })
  scrollToBottom()

  await callAIWithSession(question)
}

// 快捷问题（通过会话持久化端点发送，这样也能保存到历史记录）
async function askQuickQuestion(key: QuestionType) {
  if (!selectedConnectionId.value || loading.value) {
    return
  }

  activeQuestion.value = key
  const questionConfig = quickQuestions[key]
  const question = questionConfig.label

  // 添加用户消息
  messages.value.push({ role: 'user', content: question })
  scrollToBottom()

  loading.value = true
  progressStep.value = 'init'
  progressMessage.value = '开始诊断...'
  streamingContent.value = ''

  const body = {
    connection_id: selectedConnectionId.value,
    question,
    session_id: activeSessionId.value || undefined,
    depth: 'standard',
  }

  cancelFn.value = ssePost('/api/v1/ai/chat-with-session/stream', body, {
    onStatus: (data: any) => {
      progressStep.value = 'status'
      progressMessage.value = data.message || '初始化...'
    },
    onContext: (data: any) => {
      progressStep.value = 'context'
      progressMessage.value = data.message || '数据收集完成'
    },
    onAnalysis: (data: any) => {
      progressStep.value = 'analysis'
      progressMessage.value = data.message || '正在分析...'
    },
    onChunk: (data: any) => {
      streamingContent.value += data.text || ''
      scrollToBottom()
    },
    onSession: (data: any) => {
      if (data.session_id) {
        activeSessionId.value = data.session_id
      }
    },
    onResult: (data: any) => {
      progressStep.value = ''
      progressMessage.value = ''
      streamingContent.value = ''
      loading.value = false
      activeQuestion.value = null
      cancelFn.value = null
      if (data.session_id) {
        activeSessionId.value = data.session_id
      }
      if (data.success) {
        messages.value.push({ role: 'assistant', content: data.answer || '' })
      } else {
        messages.value.push({ role: 'assistant', content: `诊断失败: ${data.error || '未知错误'}` })
      }
      scrollToBottom()
      loadSessions()
    },
    onError: (data: any) => {
      progressStep.value = ''
      progressMessage.value = ''
      loading.value = false
      activeQuestion.value = null
      cancelFn.value = null
      messages.value.push({ role: 'assistant', content: `请求失败: ${data.message}` })
      scrollToBottom()
    },
  })
}

// 调用 AI（带会话持久化）
async function callAIWithSession(question: string) {
  if (!selectedConnectionId.value) return

  loading.value = true
  progressStep.value = 'init'
  progressMessage.value = '开始诊断...'
  streamingContent.value = ''

  const body = {
    connection_id: selectedConnectionId.value,
    question,
    session_id: activeSessionId.value || undefined,
    depth: 'standard',
  }

  cancelFn.value = ssePost('/api/v1/ai/chat-with-session/stream', body, {
    onStatus: (data: any) => {
      progressStep.value = 'status'
      progressMessage.value = data.message || '初始化...'
    },
    onContext: (data: any) => {
      progressStep.value = 'context'
      progressMessage.value = data.message || '数据收集完成'
    },
    onAnalysis: (data: any) => {
      progressStep.value = 'analysis'
      progressMessage.value = data.message || '正在分析...'
    },
    onChunk: (data: any) => {
      streamingContent.value += data.text || ''
      scrollToBottom()
    },
    onSession: (data: any) => {
      // 新创建的会话
      if (data.session_id) {
        activeSessionId.value = data.session_id
      }
    },
    onResult: (data: any) => {
      progressStep.value = ''
      progressMessage.value = ''
      streamingContent.value = ''
      loading.value = false
      cancelFn.value = null
      if (data.session_id) {
        activeSessionId.value = data.session_id
      }
      if (data.success) {
        messages.value.push({ role: 'assistant', content: data.answer || '' })
      } else {
        messages.value.push({ role: 'assistant', content: `诊断失败: ${data.error || '未知错误'}` })
      }
      scrollToBottom()
      // 刷新会话列表
      loadSessions()
    },
    onError: (data: any) => {
      progressStep.value = ''
      progressMessage.value = ''
      loading.value = false
      cancelFn.value = null
      messages.value.push({ role: 'assistant', content: `请求失败: ${data.message}` })
      scrollToBottom()
    },
  })
}

// 取消请求
function cancelRequest() {
  if (cancelFn.value) {
    cancelFn.value()
    cancelFn.value = null
  }
  loading.value = false
  activeQuestion.value = null
  progressStep.value = ''
  progressMessage.value = ''
  streamingContent.value = ''
}

// 结构化内容解析
interface StructuredIssue {
  severity?: string
  title?: string
  description?: string
  category?: string
  detail?: string
  suggestion?: string
  fix_command?: string
  fix_risk?: string
}

interface StructuredContent {
  summary: string
  issues: StructuredIssue[]
  detail: string
}

const structuredCache = new Map<string, StructuredContent>()

function hasStructuredContent(content: string): boolean {
  return content.includes('<!-- SUMMARY_START -->') || content.includes('<!-- ISSUES_JSON_START -->')
}

function parseStructuredContent(content: string): StructuredContent {
  const cached = structuredCache.get(content)
  if (cached) return cached

  let summary = ''
  let issues: StructuredIssue[] = []
  let detail = ''

  // 提取摘要
  const summaryMatch = content.match(/<!-- SUMMARY_START -->([\s\S]*?)<!-- SUMMARY_END -->/)
  if (summaryMatch) summary = summaryMatch[1].trim()

  // 提取问题 JSON
  const issuesMatch = content.match(/<!-- ISSUES_JSON_START -->([\s\S]*?)<!-- ISSUES_JSON_END -->/)
  if (issuesMatch) {
    try {
      const parsed = JSON.parse(issuesMatch[1].trim())
      issues = Array.isArray(parsed) ? parsed : (parsed.issues || [])
    } catch {
      // JSON 解析失败，忽略
    }
  }

  // 提取详细分析
  const detailMatch = content.match(/<!-- DETAIL_START -->([\s\S]*?)<!-- DETAIL_END -->/)
  if (detailMatch) detail = detailMatch[1].trim()

  // 如果没有结构化标记但有内容，回退到全文作为 detail
  if (!summary && !issues.length && !detail) {
    detail = content
  }

  const result = { summary, issues, detail }
  structuredCache.set(content, result)
  return result
}

// 复制文本
async function copyText(text: string) {
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success('已复制到剪贴板')
  } catch {
    ElMessage.error('复制失败')
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

// 格式化时间
function formatTime(dateStr: string): string {
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / 60000)
  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes} 分钟前`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours} 小时前`
  const days = Math.floor(hours / 24)
  if (days < 7) return `${days} 天前`
  return `${date.getMonth() + 1}/${date.getDate()}`
}

// 滚动到底部
function scrollToBottom() {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}
</script>

<style scoped>
.ai-diagnostic-container {
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

.actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.main-content {
  flex: 1;
  display: flex;
  overflow: hidden;
}

/* 侧边栏 */
.sidebar {
  width: 260px;
  background: white;
  border-right: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.session-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #f0f2f5;
}

.section-header h3 {
  margin: 0;
  font-size: 14px;
  color: #606266;
}

.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.session-item {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s;
  margin-bottom: 4px;
}

.session-item:hover {
  background: #f5f7fa;
}

.session-item.active {
  background: #ecf5ff;
}

.session-info {
  flex: 1;
  min-width: 0;
}

.session-title {
  display: block;
  font-size: 13px;
  color: #303133;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.session-meta {
  display: block;
  font-size: 11px;
  color: #909399;
  margin-top: 2px;
}

.session-actions {
  flex-shrink: 0;
  opacity: 0;
  transition: opacity 0.2s;
}

.session-item:hover .session-actions {
  opacity: 1;
}

.more-btn {
  cursor: pointer;
  color: #909399;
  padding: 4px;
}

.more-btn:hover {
  color: #409eff;
}

.no-sessions {
  padding: 24px;
  text-align: center;
  color: #c0c4cc;
  font-size: 13px;
}

/* 快捷问题折叠 */
.quick-collapse {
  border-top: 1px solid #e4e7ed;
  flex-shrink: 0;
}

.quick-collapse :deep(.el-collapse-item__header) {
  padding: 0 16px;
  font-size: 14px;
  color: #606266;
}

.quick-collapse :deep(.el-collapse-item__wrap) {
  max-height: 300px;
  overflow-y: auto;
}

.question-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 0 8px 8px;
}

.question-btn {
  justify-content: flex-start;
  text-align: left;
  white-space: normal;
  height: auto;
  padding: 8px 10px;
  line-height: 1.4;
}

.chat-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: white;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #909399;
}

.empty-state p {
  margin-top: 16px;
  font-size: 14px;
}

.message {
  margin-bottom: 24px;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.message-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.user-avatar {
  background: #409eff;
}

.ai-avatar {
  background: #67c23a;
}

.role-name {
  font-size: 14px;
  font-weight: 500;
  color: #606266;
}

.message-content {
  padding: 12px 16px;
  border-radius: 8px;
  line-height: 1.6;
  font-size: 14px;
}

.message.user .message-content {
  background: #ecf5ff;
  color: #409eff;
}

.message.assistant .message-content {
  background: #f4f4f5;
  color: #303133;
}

.message.loading .message-content {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #909399;
}

.input-area {
  padding: 16px 24px;
  border-top: 1px solid #e4e7ed;
  background: #fafafa;
}

.input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
}

.hint {
  font-size: 12px;
  color: #909399;
}

/* 结构化响应样式 */
.structured-response {
  padding: 12px 16px;
}

.summary-card {
  background: #ecf5ff;
  border: 1px solid #d9ecff;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
}

.summary-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 15px;
  color: #303133;
  margin-bottom: 8px;
}

.summary-body {
  color: #606266;
  line-height: 1.6;
  font-size: 14px;
}

.issues-cards {
  margin-bottom: 16px;
}

.issues-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 15px;
  color: #303133;
  margin-bottom: 12px;
}

.issue-card {
  background: #fafafa;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 14px 16px;
  margin-bottom: 10px;
  transition: box-shadow 0.2s;
}

.issue-card:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.issue-card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.issue-title {
  font-weight: 600;
  font-size: 14px;
  color: #303133;
  flex: 1;
}

.issue-detail {
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
  margin: 4px 0 8px 0;
}

.issue-suggestion {
  font-size: 13px;
  color: #67c23a;
  display: flex;
  align-items: flex-start;
  gap: 6px;
  margin: 4px 0 8px 0;
  line-height: 1.5;
}

.issue-fix {
  margin-top: 8px;
}

.fix-sql {
  background: #282c34;
  color: #abb2bf;
  padding: 10px 12px;
  border-radius: 6px;
  font-family: 'Fira Code', monospace;
  font-size: 12px;
  margin: 0 0 8px 0;
  overflow-x: auto;
}

.fix-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.detail-section {
  margin-top: 8px;
}

.detail-section :deep(.el-collapse-item__header) {
  font-size: 14px;
  color: #606266;
}

/* Markdown 样式 */
.message-content :deep(h1),
.message-content :deep(h2),
.message-content :deep(h3) {
  margin: 16px 0 8px 0;
}

.message-content :deep(h1) { font-size: 18px; }
.message-content :deep(h2) { font-size: 16px; }
.message-content :deep(h3) { font-size: 14px; }

.message-content :deep(ul),
.message-content :deep(ol) {
  padding-left: 20px;
  margin: 8px 0;
}

.message-content :deep(code) {
  background: #f0f2f5;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Fira Code', monospace;
  font-size: 13px;
}

.message-content :deep(pre) {
  background: #282c34;
  color: #abb2bf;
  padding: 12px;
  border-radius: 6px;
  overflow-x: auto;
  margin: 12px 0;
}

.message-content :deep(pre code) {
  background: transparent;
  padding: 0;
  color: inherit;
}

.message-content :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 12px 0;
}

.message-content :deep(th),
.message-content :deep(td) {
  border: 1px solid #e4e7ed;
  padding: 8px 12px;
  text-align: left;
}

.message-content :deep(th) {
  background: #f5f7fa;
  font-weight: 600;
}
</style>
