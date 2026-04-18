<template>
  <div class="analysis-result">
    <!-- 摘要 -->
    <el-alert v-if="data?.structured?.summary" :title="data.structured.summary" type="info" show-icon :closable="false" class="summary-alert" />

    <!-- 问题列表 -->
    <div v-if="issues.length > 0" class="issues-section">
      <h3 class="section-title">
        <el-icon><WarningFilled /></el-icon>
        发现问题（共 {{ issues.length }} 项）
      </h3>
      <el-table :data="issues" stripe border style="width: 100%">
        <el-table-column label="严重等级" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="severityType(row.severity)" size="small" effect="dark">{{ severityLabel(row.severity) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="类型" width="120" align="center">
          <template #default="{ row }">
            <el-tag size="small">{{ row.type || row.category || '-' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="问题描述" prop="title" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            {{ row.title || row.description || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="建议" min-width="260" show-overflow-tooltip>
          <template #default="{ row }">
            <span v-if="row.suggestion">{{ row.suggestion }}</span>
            <code v-else-if="row.create_statement" class="sql-code">{{ row.create_statement }}</code>
            <span v-else>-</span>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 详细分析 Markdown -->
    <div v-if="data?.structured?.detail" class="detail-section">
      <h3 class="section-title">详细分析</h3>
      <div class="markdown-body" v-html="renderedDetail"></div>
    </div>

    <!-- 原始回答（如果没有结构化输出） -->
    <div v-else-if="data?.answer" class="detail-section">
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

const issues = computed(() => props.data?.structured?.issues || [])
const renderedDetail = computed(() => DOMPurify.sanitize(marked.parse(props.data?.structured?.detail || '') as string))
const renderedAnswer = computed(() => DOMPurify.sanitize(marked.parse(props.data?.answer || '') as string))

function severityLabel(s: string) { return { critical: '严重', warning: '警告', info: '建议' }[s] || s }
function severityType(s: string): string { return ({ critical: 'danger', warning: 'warning', info: 'info' } as Record<string, string>)[s] || 'info' }
</script>

<style scoped lang="scss">
@import '../../analysis-common.scss';

.analysis-result {
  .summary-alert { margin-bottom: 20px; }
  .section-title {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 16px;
    font-weight: 600;
    margin: 24px 0 12px;
  }
  .issues-section { margin-bottom: 24px; }
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
  .sql-code {
    display: block;
    font-family: 'Consolas', 'Monaco', monospace;
    font-size: 12px;
    background: var(--el-fill-color-light);
    padding: 4px 8px;
    border-radius: 4px;
    word-break: break-all;
  }
}
</style>
