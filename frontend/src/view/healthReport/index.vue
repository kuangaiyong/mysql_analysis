<template>
  <div class="page-container health-report-page">
    <!-- 头部 -->
    <div class="header">
      <div class="title">
        <el-icon :size="24"><Document /></el-icon>
        <h2>健康巡检报告</h2>
      </div>
      <div class="actions">
        <el-button
          type="primary"
          :loading="generating"
          :disabled="!selectedConnectionId"
          @click="startGenerate"
        >
          生成新报告
        </el-button>
        <el-button v-if="generating" type="danger" plain @click="cancelGenerate">取消</el-button>
      </div>
    </div>

    <div class="main-content">
      <!-- 左侧：报告历史 -->
      <div class="sidebar">
        <div class="sidebar-header"><h3>历史报告</h3></div>
        <div class="report-list">
          <div v-if="reports.length === 0 && !generating" class="empty-list">
            <el-icon :size="32" color="#c0c4cc"><Document /></el-icon>
            <p>暂无历史报告</p>
          </div>
          <div
            v-for="r in reports"
            :key="r.id"
            :class="['report-item', { active: activeReportId === r.id }]"
            @click="loadReport(r.id)"
          >
            <el-progress
              type="circle"
              :percentage="r.health_score"
              :width="36"
              :stroke-width="4"
              :color="scoreColor(r.health_score)"
            />
            <div class="report-info">
              <span class="report-score">{{ r.health_score }} 分</span>
              <span class="report-date">{{ formatDate(r.created_at) }}</span>
            </div>
            <el-icon class="delete-btn" @click.stop="removeReport(r.id)"><Delete /></el-icon>
          </div>
        </div>
      </div>

      <!-- 右侧 -->
      <div class="detail-panel">
        <!-- 生成中 -->
        <div v-if="generating" class="generating-state">
          <h3>正在生成健康巡检报告...</h3>
          <div class="progress-steps">
            <div
              v-for="(step, idx) in progressSteps"
              :key="idx"
              :class="['step', step.status]"
            >
              <div class="step-indicator">
                <el-icon v-if="step.status === 'done'" color="#67C23A"><Check /></el-icon>
                <el-icon v-else-if="step.status === 'running'" class="is-loading"><Loading /></el-icon>
                <span v-else class="step-number">{{ idx + 1 }}</span>
              </div>
              <div class="step-info">
                <span class="step-name">{{ step.name }}</span>
                <span v-if="step.score !== undefined" class="step-score">{{ step.score }} 分</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 报告详情 -->
        <div v-else-if="currentReport" class="report-detail">
          <div class="score-dashboard">
            <el-progress
              type="dashboard"
              :percentage="currentReport.health_score"
              :color="scoreColor(currentReport.health_score)"
              :width="180"
              :stroke-width="12"
            >
              <template #default>
                <div class="score-inner">
                  <span class="score-number">{{ currentReport.health_score }}</span>
                  <span class="score-label">综合评分</span>
                </div>
              </template>
            </el-progress>

            <!-- 雷达图 -->
            <div v-if="currentReport.dimensions?.length" class="radar-chart-wrapper">
              <v-chart :option="radarOption" autoresize style="width: 320px; height: 260px" />
            </div>

            <div class="score-summary">
              <p class="score-level" :style="{ color: scoreColor(currentReport.health_score) }">
                {{ scoreLevelText(currentReport.health_score) }}
              </p>
              <el-button type="primary" plain @click="exportMarkdown">
                <el-icon><Download /></el-icon>
                导出 Markdown
              </el-button>
            </div>
          </div>

          <!-- 问题汇总列表 -->
          <div v-if="reportIssues.length > 0" class="issues-section">
            <h3 class="section-title">
              <el-icon><WarningFilled /></el-icon>
              问题汇总（共 {{ reportIssues.length }} 项）
            </h3>
            <el-table :data="reportIssues" stripe border style="width: 100%" class="issues-table">
              <el-table-column label="序号" type="index" width="60" align="center" />
              <el-table-column label="严重等级" width="100" align="center">
                <template #default="{ row }">
                  <el-tag :type="severityTagType(row.severity)" size="small" effect="dark">
                    {{ severityLabel(row.severity) }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="问题类型" prop="category" width="100" />
              <el-table-column label="问题描述" prop="description" min-width="200" show-overflow-tooltip />
              <el-table-column label="问题详情" min-width="240">
                <template #default="{ row }">
                  <el-popover placement="top-start" :width="400" trigger="hover" :content="row.detail">
                    <template #reference>
                      <span class="detail-text">{{ row.detail }}</span>
                    </template>
                  </el-popover>
                </template>
              </el-table-column>
              <el-table-column label="优化建议" min-width="240">
                <template #default="{ row }">
                  <el-popover placement="top-start" :width="400" trigger="hover" :content="row.suggestion">
                    <template #reference>
                      <span class="suggestion-text">{{ row.suggestion }}</span>
                    </template>
                  </el-popover>
                </template>
              </el-table-column>
            </el-table>
          </div>

          <!-- 各维度详情 -->
          <h3 v-if="currentReport.dimensions?.length" class="section-title" style="margin-top: 24px">
            各维度评估详情
          </h3>
          <div class="dimension-cards">
            <el-card v-for="dim in sortedDimensions" :key="dim.name" shadow="hover" class="dimension-card"
              :class="{ 'dimension-worst': isWorstDimension(dim.name) }"
            >
              <template #header>
                <div class="dimension-header">
                  <span class="dimension-name">{{ dim.name }}</span>
                  <el-tag v-if="isWorstDimension(dim.name)" type="danger" size="small" effect="plain">需关注</el-tag>
                  <span class="dimension-weight">权重 {{ (dim.weight * 100).toFixed(0) }}%</span>
                  <span class="dimension-score" :style="{ color: scoreColor(dim.score) }">{{ dim.score }} 分</span>
                </div>
              </template>
              <el-progress
                :percentage="dim.score"
                :color="scoreColor(dim.score)"
                :stroke-width="10"
                :show-text="false"
                style="margin-bottom: 12px"
              />
              <el-collapse :model-value="isWorstDimension(dim.name) ? ['detail'] : []">
                <el-collapse-item title="查看详细分析" name="detail">
                  <div class="dimension-detail" v-html="renderMarkdown(dim.analysis)"></div>
                </el-collapse-item>
              </el-collapse>
            </el-card>
          </div>
        </div>

        <!-- 空状态 -->
        <div v-else class="empty-state">
          <el-icon :size="64" color="#909399"><Document /></el-icon>
          <p>选择历史报告查看，或点击"生成新报告"开始巡检</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { Document, Delete, Check, Loading, Download, WarningFilled } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { useConnectionStore } from '@/pinia/modules/connection'
import {
  generateHealthReportStream,
  getReports,
  getReportDetail,
  deleteReport,
  exportReportMarkdown,
  type DimensionScore,
  type ReportSSEListeners,
} from '@/api/ai'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { RadarChart } from 'echarts/charts'
import { TitleComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

use([RadarChart, TitleComponent, TooltipComponent, LegendComponent, CanvasRenderer])

interface ProgressStep {
  name: string
  score?: number
  status: 'pending' | 'running' | 'done'
}

interface ReportListItem {
  id: number
  health_score: number
  created_at: string
}

interface ReportDetail {
  id: number
  health_score: number
  dimensions: DimensionScore[]
  content: Record<string, any>
  created_at: string
}

const connectionStore = useConnectionStore()
const selectedConnectionId = computed(() => connectionStore.selectedConnectionId)
const reports = ref<ReportListItem[]>([])
const activeReportId = ref<number | null>(null)
const currentReport = ref<ReportDetail | null>(null)
const generating = ref(false)
const progressSteps = ref<ProgressStep[]>([])
const abortController = ref<AbortController | null>(null)

// 维度名称（与后端 DIMENSIONS 对应）
const DIM_NAMES = ['整体性能', '配置', '慢查询', '索引', 'BufferPool', '锁', '连接', 'I/O']

// 从当前报告中提取问题列表
const reportIssues = computed(() => {
  if (!currentReport.value?.content?.issues) return []
  return currentReport.value.content.issues
})

// 严重等级标签
function severityLabel(severity: string): string {
  const map: Record<string, string> = { critical: '严重', warning: '警告', info: '建议' }
  return map[severity] || severity
}

// 严重等级标签颜色
function severityTagType(severity: string): string {
  const map: Record<string, string> = { critical: 'danger', warning: 'warning', info: 'info' }
  return map[severity] || 'info'
}

onMounted(async () => {
  if (selectedConnectionId.value) await loadReports()
})

watch(selectedConnectionId, async (newId) => {
  if (newId) {
    await loadReports()
  } else {
    activeReportId.value = null
    currentReport.value = null
    reports.value = []
  }
})

async function loadReports() {
  if (!selectedConnectionId.value) return
  try {
    const res = await getReports(selectedConnectionId.value)
    reports.value = res.data || []
  } catch (error) {
    console.error('加载报告列表失败:', error)
  }
}

async function loadReport(reportId: number) {
  try {
    activeReportId.value = reportId
    const res = await getReportDetail(reportId)
    currentReport.value = res.data
  } catch (error) {
    ElMessage.error('加载报告失败')
  }
}

function startGenerate() {
  if (!selectedConnectionId.value || generating.value) return

  generating.value = true
  currentReport.value = null
  activeReportId.value = null
  progressSteps.value = DIM_NAMES.map((name) => ({ name, status: 'pending' }))

  const listeners: ReportSSEListeners = {
    onProgress: (data) => {
      const idx = data.current - 1
      if (idx >= 0 && idx < progressSteps.value.length) {
        for (let i = 0; i < idx; i++) {
          if (progressSteps.value[i].status !== 'done') {
            progressSteps.value[i].status = 'done'
          }
        }
        progressSteps.value[idx].status = 'running'
        progressSteps.value[idx].name = data.dimension || progressSteps.value[idx].name
      }
    },
    onDimension: (data) => {
      const idx = progressSteps.value.findIndex((s) => s.name === data.name)
      if (idx >= 0) {
        progressSteps.value[idx].status = 'done'
        progressSteps.value[idx].score = data.score
      }
    },
    onResult: (data) => {
      generating.value = false
      abortController.value = null
      progressSteps.value.forEach((s) => (s.status = 'done'))

      currentReport.value = {
        id: data.report_id,
        health_score: data.health_score,
        dimensions: data.dimensions,
        content: data.content,
        created_at: new Date().toISOString(),
      }
      activeReportId.value = data.report_id
      loadReports()
      ElMessage.success(`报告生成完成，综合评分: ${data.health_score} 分`)
    },
    onError: (data) => {
      generating.value = false
      abortController.value = null
      ElMessage.error(`报告生成失败: ${data.message}`)
    },
  }

  abortController.value = generateHealthReportStream(selectedConnectionId.value, listeners)
}

function cancelGenerate() {
  if (abortController.value) {
    abortController.value.abort()
    abortController.value = null
  }
  generating.value = false
  ElMessage.info('已取消生成')
}

async function removeReport(reportId: number) {
  try {
    await ElMessageBox.confirm('确定删除此报告？', '确认删除', { type: 'warning' })
    await deleteReport(reportId)
    reports.value = reports.value.filter((r) => r.id !== reportId)
    if (activeReportId.value === reportId) {
      activeReportId.value = null
      currentReport.value = null
    }
    ElMessage.success('已删除')
  } catch { /* 用户取消 */ }
}

async function exportMarkdown() {
  if (!activeReportId.value) return
  try {
    const res = await exportReportMarkdown(activeReportId.value)
    const blob = new Blob([res.data], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `health-report-${activeReportId.value}.md`
    a.click()
    URL.revokeObjectURL(url)
  } catch {
    ElMessage.error('导出失败')
  }
}

function scoreColor(score: number): string {
  if (score >= 70) return '#67C23A'
  if (score >= 40) return '#E6A23C'
  return '#F56C6C'
}

function scoreLevelText(score: number): string {
  if (score >= 90) return '健康状态：优秀'
  if (score >= 70) return '健康状态：良好'
  if (score >= 40) return '健康状态：需关注'
  return '健康状态：亟需优化'
}

// 最差的 3 个维度名称
const worstDimensionNames = computed<Set<string>>(() => {
  const dims = currentReport.value?.dimensions
  if (!dims || dims.length === 0) return new Set()
  const sorted = [...dims].sort((a, b) => a.score - b.score)
  const worst3 = sorted.slice(0, 3).map((d) => d.name)
  return new Set(worst3)
})

function isWorstDimension(name: string): boolean {
  return worstDimensionNames.value.has(name)
}

// 按分数升序排列（最差的在前）
const sortedDimensions = computed(() => {
  const dims = currentReport.value?.dimensions
  if (!dims) return []
  return [...dims].sort((a, b) => a.score - b.score)
})

// 雷达图配置
const radarOption = computed(() => {
  const dims = currentReport.value?.dimensions
  if (!dims || dims.length === 0) return {}

  const indicator = dims.map((d) => ({
    name: d.name,
    max: 100,
  }))
  const values = dims.map((d) => d.score)

  return {
    tooltip: {},
    radar: {
      indicator,
      shape: 'polygon',
      radius: '70%',
      axisName: {
        color: '#606266',
        fontSize: 12,
      },
      splitArea: {
        areaStyle: { color: ['#fff', '#f5f7fa'] },
      },
    },
    series: [
      {
        type: 'radar',
        data: [
          {
            value: values,
            name: '健康评分',
            areaStyle: { color: 'rgba(64, 158, 255, 0.15)' },
            lineStyle: { color: '#409eff', width: 2 },
            itemStyle: { color: '#409eff' },
          },
        ],
      },
    ],
  }
})

function renderMarkdown(content: string): string {
  if (!content) return ''
  try {
    return DOMPurify.sanitize(marked(content) as string)
  } catch {
    return content
  }
}

function formatDate(dateStr: string): string {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}
</script>

<style scoped>
.health-report-page {
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

.sidebar {
  width: 240px;
  background: white;
  border-right: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: 16px;
  border-bottom: 1px solid #e4e7ed;
}

.sidebar-header h3 {
  margin: 0;
  font-size: 14px;
  color: #606266;
}

.report-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.empty-list {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px 16px;
  color: #c0c4cc;
}

.empty-list p {
  margin: 8px 0 0 0;
  font-size: 13px;
}

.report-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px;
  border-radius: 6px;
  cursor: pointer;
  margin-bottom: 4px;
  transition: background 0.2s;
}

.report-item:hover {
  background: #f5f7fa;
}

.report-item.active {
  background: #ecf5ff;
}

.report-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.report-score {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.report-date {
  font-size: 11px;
  color: #909399;
  margin-top: 2px;
}

.delete-btn {
  cursor: pointer;
  color: #909399;
  opacity: 0;
  transition: opacity 0.2s;
}

.report-item:hover .delete-btn {
  opacity: 1;
}

.delete-btn:hover {
  color: #F56C6C;
}

.detail-panel {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  background: white;
}

/* 生成中 */
.generating-state {
  max-width: 500px;
  margin: 40px auto;
  text-align: center;
}

.generating-state h3 {
  margin-bottom: 32px;
  color: #303133;
}

.progress-steps {
  display: flex;
  flex-direction: column;
  gap: 16px;
  text-align: left;
}

.step {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  border-radius: 6px;
  transition: background 0.3s;
}

.step.running {
  background: #ecf5ff;
}

.step.done {
  background: #f0f9eb;
}

.step-indicator {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f0f2f5;
  flex-shrink: 0;
}

.step.running .step-indicator {
  background: #409eff;
  color: white;
}

.step.done .step-indicator {
  background: #67c23a;
  color: white;
}

.step-number {
  font-size: 12px;
  color: #909399;
}

.step-info {
  flex: 1;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.step-name {
  font-size: 14px;
  color: #606266;
}

.step-score {
  font-size: 14px;
  font-weight: 600;
  color: #67c23a;
}

/* 报告详情 */
.report-detail {
  max-width: 900px;
  margin: 0 auto;
}

.score-dashboard {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 40px;
  padding: 32px;
  margin-bottom: 24px;
}

.score-inner {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.score-number {
  font-size: 40px;
  font-weight: 700;
  line-height: 1;
}

.score-label {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}

.score-summary {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.score-level {
  font-size: 20px;
  font-weight: 600;
  margin: 0;
}

/* 问题汇总 */
.issues-section {
  margin-bottom: 24px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  color: #303133;
  margin: 0 0 16px 0;
}

.issues-table {
  border-radius: 8px;
  overflow: hidden;
}

.detail-text,
.suggestion-text {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
  font-size: 13px;
  line-height: 1.5;
  cursor: pointer;
  color: #606266;
}

.suggestion-text {
  color: #409eff;
}

.dimension-cards {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.dimension-card {
  border-radius: 8px;
}

.dimension-card.dimension-worst {
  border: 1px solid #f89898;
  box-shadow: 0 0 8px rgba(245, 108, 108, 0.15);
}

.radar-chart-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
}

.dimension-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.dimension-name {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  flex: 1;
}

.dimension-weight {
  font-size: 12px;
  color: #909399;
}

.dimension-score {
  font-size: 18px;
  font-weight: 700;
}

.dimension-detail {
  line-height: 1.7;
  color: #606266;
  font-size: 13px;
}

.dimension-detail :deep(code) {
  background: #f0f2f5;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 12px;
}

.dimension-detail :deep(pre) {
  background: #282c34;
  color: #abb2bf;
  padding: 12px;
  border-radius: 6px;
  overflow-x: auto;
}

.dimension-detail :deep(pre code) {
  background: transparent;
  color: inherit;
}

.dimension-detail :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 8px 0;
}

.dimension-detail :deep(th),
.dimension-detail :deep(td) {
  border: 1px solid #e4e7ed;
  padding: 6px 10px;
  text-align: left;
}

.dimension-detail :deep(th) {
  background: #f5f7fa;
  font-weight: 600;
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

@media (max-width: 1200px) {
  .dimension-cards {
    grid-template-columns: 1fr;
  }
}
</style>
