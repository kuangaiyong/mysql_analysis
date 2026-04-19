<template>
  <div class="analysis-result">
    <el-alert
      v-if="summaryText"
      :title="summaryText"
      type="info"
      show-icon
      :closable="false"
      class="summary-alert"
    />

    <div v-if="taskType === 'config_tuning' && riskModel" class="risk-overview">
      <h3 class="section-title">风险总览</h3>
      <div class="metric-grid">
        <div class="metric-card">
          <span class="metric-label">整体风险</span>
          <el-tag :type="riskTagType(riskModel.overall_risk)" size="large" effect="dark">
            {{ riskLabel(riskModel.overall_risk) }}
          </el-tag>
        </div>
        <div class="metric-card">
          <span class="metric-label">建议项</span>
          <span class="metric-value">{{ riskModel.issue_count || 0 }}</span>
        </div>
        <div class="metric-card">
          <span class="metric-label">高风险项</span>
          <span class="metric-value danger">{{ riskModel.high_risk_count || 0 }}</span>
        </div>
        <div class="metric-card">
          <span class="metric-label">需重启项</span>
          <span class="metric-value warning">{{ riskModel.restart_required_count || 0 }}</span>
        </div>
      </div>

      <el-table v-if="riskCategories.length > 0" :data="riskCategories" stripe border class="sub-table">
        <el-table-column label="分类" prop="category" min-width="140" />
        <el-table-column label="建议数" prop="count" width="100" align="center" />
        <el-table-column label="最高风险" width="120" align="center">
          <template #default="{ row }">
            <el-tag :type="riskTagType(row.highest_risk)" size="small">{{ riskLabel(row.highest_risk) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="需重启项" prop="restart_required_count" width="120" align="center" />
      </el-table>
    </div>

    <template v-if="issues.length > 0">
      <div v-if="taskType === 'index_advisor'" class="issues-section">
        <h3 class="section-title">
          <el-icon><WarningFilled /></el-icon>
          索引建议（共 {{ issues.length }} 项）
        </h3>
        <el-table :data="issues" stripe border>
          <el-table-column label="严重等级" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="severityType(row.severity)" size="small" effect="dark">{{ severityLabel(row.severity) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="表" min-width="140">
            <template #default="{ row }">{{ issueText(row, 'table') }}</template>
          </el-table-column>
          <el-table-column label="类型" width="120" align="center">
            <template #default="{ row }">
              <el-tag size="small">{{ issueText(row, 'type') }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="建议" min-width="260" show-overflow-tooltip>
            <template #default="{ row }">{{ issueText(row, 'suggestion', 'title', 'reason') }}</template>
          </el-table-column>
          <el-table-column label="提升预估" min-width="120" show-overflow-tooltip>
            <template #default="{ row }">{{ issueText(row, 'estimated_improvement') }}</template>
          </el-table-column>
          <el-table-column label="风险" width="110" align="center">
            <template #default="{ row }">
              <el-tag :type="riskTagType(row.risk)" size="small">{{ riskLabel(row.risk) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="SQL / 处置" min-width="320">
            <template #default="{ row }">
              <div class="code-stack">
                <pre v-if="issueText(row, 'create_statement')" class="sql-code">{{ issueText(row, 'create_statement') }}</pre>
                <pre v-if="issueText(row, 'drop_statement')" class="sql-code danger-code">{{ issueText(row, 'drop_statement') }}</pre>
                <span v-if="!issueText(row, 'create_statement') && !issueText(row, 'drop_statement')">-</span>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <div v-else-if="taskType === 'lock_analysis'" class="issues-section">
        <h3 class="section-title">
          <el-icon><WarningFilled /></el-icon>
          锁风险清单（共 {{ issues.length }} 项）
        </h3>
        <el-table :data="issues" stripe border>
          <el-table-column label="严重等级" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="severityType(row.severity)" size="small" effect="dark">{{ severityLabel(row.severity) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="类型" width="120" align="center">
            <template #default="{ row }">
              <el-tag size="small">{{ issueText(row, 'type') }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="阻塞会话" min-width="140" show-overflow-tooltip>
            <template #default="{ row }">{{ issueText(row, 'blocking_session') }}</template>
          </el-table-column>
          <el-table-column label="等待会话" min-width="140" show-overflow-tooltip>
            <template #default="{ row }">{{ issueText(row, 'waiting_session') }}</template>
          </el-table-column>
          <el-table-column label="对象" min-width="140" show-overflow-tooltip>
            <template #default="{ row }">{{ issueText(row, 'table', 'title') }}</template>
          </el-table-column>
          <el-table-column label="等待时长" min-width="110" align="center">
            <template #default="{ row }">{{ issueText(row, 'wait_time_seconds') }}</template>
          </el-table-column>
          <el-table-column label="处置命令" min-width="220">
            <template #default="{ row }">
              <pre v-if="issueText(row, 'fix_command')" class="sql-code">{{ issueText(row, 'fix_command') }}</pre>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column label="预防建议" min-width="220" show-overflow-tooltip>
            <template #default="{ row }">{{ issueText(row, 'prevention', 'reason') }}</template>
          </el-table-column>
        </el-table>
      </div>

      <div v-else-if="taskType === 'slow_query_patrol'" class="issues-section">
        <h3 class="section-title">
          <el-icon><WarningFilled /></el-icon>
          慢查询巡检（共 {{ issues.length }} 项）
        </h3>
        <el-table :data="issues" stripe border>
          <el-table-column label="严重等级" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="severityType(row.severity)" size="small" effect="dark">{{ severityLabel(row.severity) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="排序" width="80" align="center">
            <template #default="{ row }">{{ issueText(row, 'rank') }}</template>
          </el-table-column>
          <el-table-column label="类别" width="120" align="center">
            <template #default="{ row }">
              <el-tag size="small">{{ issueText(row, 'category') }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="执行画像" min-width="220">
            <template #default="{ row }">
              <div class="info-list compact">
                <span>次数：{{ issueText(row, 'execution_count') }}</span>
                <span>均耗时：{{ issueText(row, 'avg_time_ms') }}</span>
                <span>总耗时：{{ issueText(row, 'total_time_ms') }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="扫描 / 返回" min-width="180">
            <template #default="{ row }">
              <div class="info-list compact">
                <span>扫描：{{ issueText(row, 'rows_examined') }}</span>
                <span>返回：{{ issueText(row, 'rows_sent') }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="根因" min-width="220" show-overflow-tooltip>
            <template #default="{ row }">{{ issueText(row, 'root_cause', 'title') }}</template>
          </el-table-column>
          <el-table-column label="优化建议" min-width="240" show-overflow-tooltip>
            <template #default="{ row }">{{ issueText(row, 'fix_suggestion', 'index_suggestion') }}</template>
          </el-table-column>
          <el-table-column label="优化 SQL" min-width="240">
            <template #default="{ row }">
              <pre v-if="issueText(row, 'optimized_sql')" class="sql-code">{{ issueText(row, 'optimized_sql') }}</pre>
              <span v-else>-</span>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <div v-else-if="taskType === 'config_tuning'" class="issues-section">
        <h3 class="section-title">
          <el-icon><WarningFilled /></el-icon>
          配置调优建议（共 {{ issues.length }} 项）
        </h3>
        <el-table :data="issues" stripe border>
          <el-table-column label="严重等级" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="severityType(row.severity)" size="small" effect="dark">{{ severityLabel(row.severity) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="分类" width="120" align="center">
            <template #default="{ row }">
              <el-tag size="small">{{ issueText(row, 'category') }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="参数" min-width="160" show-overflow-tooltip>
            <template #default="{ row }">{{ issueText(row, 'parameter') }}</template>
          </el-table-column>
          <el-table-column label="当前值" min-width="120" show-overflow-tooltip>
            <template #default="{ row }">{{ issueText(row, 'current_value') }}</template>
          </el-table-column>
          <el-table-column label="建议值" min-width="140" show-overflow-tooltip>
            <template #default="{ row }">{{ issueText(row, 'recommended_value') }}</template>
          </el-table-column>
          <el-table-column label="风险" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="riskTagType(row.risk)" size="small">{{ riskLabel(row.risk) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="影响" min-width="220" show-overflow-tooltip>
            <template #default="{ row }">{{ issueText(row, 'impact', 'reason') }}</template>
          </el-table-column>
          <el-table-column label="需重启" width="90" align="center">
            <template #default="{ row }">
              <el-tag :type="row.requires_restart ? 'warning' : 'success'" size="small">{{ row.requires_restart ? '是' : '否' }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="建议命令" min-width="240">
            <template #default="{ row }">
              <pre v-if="issueText(row, 'command')" class="sql-code">{{ issueText(row, 'command') }}</pre>
              <span v-else>-</span>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <div v-else-if="taskType === 'capacity_prediction'" class="issues-section">
        <h3 class="section-title">
          <el-icon><WarningFilled /></el-icon>
          容量风险评估（共 {{ issues.length }} 项）
        </h3>
        <el-table :data="issues" stripe border>
          <el-table-column label="严重等级" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="severityType(row.severity)" size="small" effect="dark">{{ severityLabel(row.severity) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="维度" width="120" align="center">
            <template #default="{ row }">
              <el-tag size="small">{{ issueText(row, 'dimension') }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="当前状态" min-width="220">
            <template #default="{ row }">
              <div class="info-list compact">
                <span>用量：{{ issueText(row, 'current_usage') }}</span>
                <span>容量：{{ issueText(row, 'current_capacity') }}</span>
                <span>使用率：{{ issueText(row, 'usage_percentage') }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="增长趋势" min-width="120" show-overflow-tooltip>
            <template #default="{ row }">{{ issueText(row, 'growth_rate') }}</template>
          </el-table-column>
          <el-table-column label="风险时间点" min-width="160" show-overflow-tooltip>
            <template #default="{ row }">{{ issueText(row, 'estimated_exhaustion') }}</template>
          </el-table-column>
          <el-table-column label="优先级" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="priorityType(row.priority)" size="small">{{ priorityLabel(row.priority) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="建议动作" min-width="260" show-overflow-tooltip>
            <template #default="{ row }">{{ issueText(row, 'recommendation', 'title') }}</template>
          </el-table-column>
        </el-table>
      </div>

      <div v-else class="issues-section">
        <h3 class="section-title">
          <el-icon><WarningFilled /></el-icon>
          发现问题（共 {{ issues.length }} 项）
        </h3>
        <el-table :data="issues" stripe border>
          <el-table-column label="严重等级" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="severityType(row.severity)" size="small" effect="dark">{{ severityLabel(row.severity) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="类型" width="120" align="center">
            <template #default="{ row }">
              <el-tag size="small">{{ issueText(row, 'type', 'category') }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="问题描述" min-width="200" show-overflow-tooltip>
            <template #default="{ row }">{{ issueText(row, 'title', 'description') }}</template>
          </el-table-column>
          <el-table-column label="建议" min-width="260" show-overflow-tooltip>
            <template #default="{ row }">{{ issueText(row, 'suggestion', 'create_statement', 'reason') }}</template>
          </el-table-column>
        </el-table>
      </div>
    </template>

    <div v-if="detailText" class="detail-section">
      <h3 class="section-title">详细分析</h3>
      <div class="markdown-body" v-html="renderedDetail"></div>
    </div>

    <div v-else-if="answerText" class="detail-section">
      <h3 class="section-title">分析报告</h3>
      <div class="markdown-body" v-html="renderedAnswer"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { WarningFilled } from '@element-plus/icons-vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'

const props = defineProps<{
  data: any
  taskType: string
}>()

const structured = computed(() => props.data?.structured || {})
const issues = computed(() => Array.isArray(structured.value?.issues) ? structured.value.issues : [])
const summaryText = computed(() => textValue(structured.value?.summary))
const detailText = computed(() => textValue(structured.value?.detail))
const answerText = computed(() => textValue(props.data?.answer))
const riskModel = computed(() => structured.value?.risk_model || null)
const riskCategories = computed(() => Array.isArray(riskModel.value?.categories) ? riskModel.value.categories : [])

const renderedDetail = computed(() => DOMPurify.sanitize(marked.parse(detailText.value || '') as string))
const renderedAnswer = computed(() => DOMPurify.sanitize(marked.parse(answerText.value || '') as string))

function textValue(value: any, fallback = ''): string {
  if (value == null) return fallback
  if (typeof value === 'string') {
    const trimmed = value.trim()
    return trimmed || fallback
  }
  if (Array.isArray(value)) {
    return value.map((item) => textValue(item)).filter(Boolean).join('、') || fallback
  }
  if (typeof value === 'object') {
    try {
      return JSON.stringify(value)
    } catch {
      return fallback
    }
  }
  return String(value)
}

function issueText(issue: Record<string, any>, ...keys: string[]): string {
  for (const key of keys) {
    const value = textValue(issue?.[key])
    if (value) return value
  }
  return '-'
}

function severityLabel(s: string) {
  return { critical: '严重', warning: '警告', info: '建议' }[s] || s || '-'
}

function severityType(s: string): string {
  return ({ critical: 'danger', warning: 'warning', info: 'info' } as Record<string, string>)[s] || 'info'
}

function riskLabel(risk: string) {
  return { low: '低', medium: '中', high: '高' }[risk] || risk || '-'
}

function riskTagType(risk: string): string {
  return ({ low: 'success', medium: 'warning', high: 'danger' } as Record<string, string>)[risk] || 'info'
}

function priorityLabel(priority: string) {
  return { urgent: '紧急', planned: '规划', monitor: '观察' }[priority] || priority || '-'
}

function priorityType(priority: string): string {
  return ({ urgent: 'danger', planned: 'warning', monitor: 'info' } as Record<string, string>)[priority] || 'info'
}
</script>

<style scoped lang="scss">
@import '../../analysis-common.scss';

.analysis-result {
  .summary-alert {
    margin-bottom: 20px;
  }

  .section-title {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 16px;
    font-weight: 600;
    margin: 24px 0 12px;
  }

  .risk-overview,
  .issues-section {
    margin-bottom: 24px;
  }

  .metric-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 12px;
    margin-bottom: 16px;
  }

  .metric-card {
    display: flex;
    flex-direction: column;
    gap: 8px;
    padding: 16px;
    border: 1px solid var(--el-border-color-lighter);
    border-radius: 10px;
    background: var(--el-bg-color);
  }

  .metric-label {
    font-size: 13px;
    color: var(--el-text-color-secondary);
  }

  .metric-value {
    font-size: 28px;
    font-weight: 700;
    line-height: 1;

    &.danger {
      color: var(--el-color-danger);
    }

    &.warning {
      color: var(--el-color-warning);
    }
  }

  .sub-table {
    margin-top: 12px;
  }

  .detail-section {
    margin-top: 24px;

    .markdown-body {
      padding: 16px 20px;
      background: var(--el-bg-color-page);
      border: 1px solid var(--el-border-color-lighter);
      border-radius: 8px;
      line-height: 1.7;
      font-size: 14px;
    }
  }

  .info-list {
    display: flex;
    flex-direction: column;
    gap: 4px;

    &.compact {
      font-size: 12px;
      color: var(--el-text-color-secondary);
    }
  }

  .code-stack {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .sql-code {
    margin: 0;
    white-space: pre-wrap;
    font-family: 'Consolas', 'Monaco', monospace;
    font-size: 12px;
    background: var(--el-fill-color-light);
    padding: 8px 10px;
    border-radius: 6px;
    word-break: break-all;
    line-height: 1.5;
  }

  .danger-code {
    border-left: 3px solid var(--el-color-danger);
  }
}
</style>
