<template>
  <div class="health-report-result">
    <!-- 综合评分 -->
    <div class="score-section">
      <div class="score-circle" :class="scoreClass">
        <span class="score-value">{{ data?.health_score ?? '-' }}</span>
        <span class="score-label">综合评分</span>
      </div>
    </div>

    <!-- 维度评分 -->
    <div v-if="dimensions.length > 0" class="dimensions-section">
      <h3 class="section-title">维度评分</h3>
      <div class="dimension-grid">
        <div v-for="dim in dimensions" :key="dim.name" class="dimension-card">
          <div class="dim-header">
            <span class="dim-name">{{ dim.name }}</span>
            <el-tag :type="dimScoreType(dim.score)" size="small" effect="dark">{{ dim.score }}分</el-tag>
          </div>
          <el-progress :percentage="dim.score" :stroke-width="8" :color="dimColor(dim.score)" :show-text="false" />
          <div v-if="dim.analysis" class="dim-summary">{{ truncate(dim.analysis, 120) }}</div>
        </div>
      </div>
    </div>

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
        <el-table-column label="类别" width="100" align="center" prop="category" />
        <el-table-column label="描述" prop="description" min-width="200" show-overflow-tooltip />
        <el-table-column label="建议" prop="suggestion" min-width="260" show-overflow-tooltip />
        <el-table-column label="修复命令" min-width="200">
          <template #default="{ row }">
            <code v-if="row.fix_command" class="sql-code">{{ row.fix_command }}</code>
            <span v-else>-</span>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { WarningFilled } from '@element-plus/icons-vue'

const props = defineProps<{ data: any }>()

const dimensions = computed(() => {
  if (!props.data?.dimensions) return []
  if (Array.isArray(props.data.dimensions)) {
    return props.data.dimensions.map((item: any) => ({
      name: item.name,
      score: item.score ?? 0,
      analysis: item.analysis ?? '',
    }))
  }
  return Object.entries(props.data.dimensions).map(([name, val]: [string, any]) => ({
    name,
    score: val.score ?? 0,
    analysis: val.analysis ?? '',
  }))
})

const issues = computed(() => props.data?.issues || props.data?.content?.issues || [])

const scoreClass = computed(() => {
  const s = props.data?.health_score ?? 0
  if (s >= 80) return 'good'
  if (s >= 60) return 'warning'
  return 'danger'
})

function dimScoreType(score: number): string {
  if (score >= 80) return 'success'
  if (score >= 60) return 'warning'
  return 'danger'
}

function dimColor(score: number): string {
  if (score >= 80) return '#67c23a'
  if (score >= 60) return '#e6a23c'
  return '#f56c6c'
}

function severityLabel(s: string) { return { critical: '严重', warning: '警告', info: '建议' }[s] || s }
function severityType(s: string): string { return ({ critical: 'danger', warning: 'warning', info: 'info' } as Record<string, string>)[s] || 'info' }
function truncate(s: string, len: number) { return s.length > len ? s.slice(0, len) + '...' : s }
</script>

<style scoped lang="scss">
.health-report-result {
  .score-section {
    display: flex;
    justify-content: center;
    margin-bottom: 24px;

    .score-circle {
      width: 120px;
      height: 120px;
      border-radius: 50%;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      border: 4px solid;

      &.good { border-color: #67c23a; background: #f0f9eb; }
      &.warning { border-color: #e6a23c; background: #fdf6ec; }
      &.danger { border-color: #f56c6c; background: #fef0f0; }

      .score-value { font-size: 36px; font-weight: 700; line-height: 1; }
      .score-label { font-size: 12px; color: var(--el-text-color-secondary); margin-top: 4px; }
    }
  }

  .section-title {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 16px;
    font-weight: 600;
    margin: 24px 0 12px;
  }

  .dimensions-section {
    margin-bottom: 24px;

    .dimension-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
      gap: 12px;
    }

    .dimension-card {
      padding: 14px 16px;
      border: 1px solid var(--el-border-color-lighter);
      border-radius: 8px;
      background: var(--el-bg-color);

      .dim-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
        .dim-name { font-weight: 600; font-size: 14px; }
      }

      .dim-summary {
        margin-top: 8px;
        font-size: 12px;
        color: var(--el-text-color-secondary);
        line-height: 1.5;
      }
    }
  }

  .issues-section { margin-bottom: 24px; }

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
