<template>
  <el-card>
    <template #header>
      <div class="card-header">
        <span>性能问题 ({{ diagnosis.issue_count }})</span>
        <div class="issue-stats">
          <el-tag v-if="diagnosis.critical_count > 0" type="danger" size="small">
            严重: {{ diagnosis.critical_count }}
          </el-tag>
          <el-tag v-if="diagnosis.warning_count > 0" type="warning" size="small">
            警告: {{ diagnosis.warning_count }}
          </el-tag>
        </div>
      </div>
    </template>

    <el-table v-if="diagnosis.issues.length > 0" :data="diagnosis.issues" stripe border>
      <el-table-column prop="issue_type" label="问题类型" width="120" />
      <el-table-column label="严重程度" width="100">
        <template #default="{ row }">
          <el-tag :type="getSeverityType(row.severity)">
            {{ getSeverityText(row.severity) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="description" label="问题描述" min-width="200" />
      <el-table-column prop="impact" label="影响" min-width="200" />
      <el-table-column label="指标值" width="100">
        <template #default="{ row }">
          <span v-if="row.metric_value !== undefined && row.metric_value !== null">
            {{ row.metric_value.toFixed ? row.metric_value.toFixed(1) : row.metric_value }}
            <span v-if="row.threshold">%</span>
          </span>
          <span v-else>-</span>
        </template>
      </el-table-column>
    </el-table>

    <el-empty v-else description="未发现性能问题" />
  </el-card>
</template>

<script setup lang="ts">
import type { TableDiagnosis } from '@/types/table'

defineProps<{
  diagnosis: TableDiagnosis
}>()

const getSeverityType = (severity: string): 'danger' | 'warning' | 'info' | 'success' => {
  switch (severity) {
    case 'critical':
      return 'danger'
    case 'warning':
      return 'warning'
    case 'info':
      return 'info'
    default:
      return 'success'
  }
}

const getSeverityText = (severity: string): string => {
  switch (severity) {
    case 'critical':
      return '严重'
    case 'warning':
      return '警告'
    case 'info':
      return '提示'
    default:
      return '未知'
  }
}
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.issue-stats {
  display: flex;
  gap: 8px;
}
</style>
