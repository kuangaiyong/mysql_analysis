<template>
  <el-card>
    <template #header>
      <span>优化建议 ({{ recommendations.recommendations.length }})</span>
    </template>

    <div v-if="recommendations.recommendations.length > 0" class="recommendation-list">
      <el-card
        v-for="(rec, index) in recommendations.recommendations"
        :key="index"
        class="recommendation-card"
        shadow="hover"
      >
        <div class="recommendation-header">
          <span class="recommendation-title">{{ rec.title }}</span>
          <el-tag :type="getPriorityType(rec.priority)" size="small">
            {{ getPriorityText(rec.priority) }}
          </el-tag>
        </div>

        <div class="recommendation-content">
          <p class="recommendation-description">{{ rec.description }}</p>
          <p class="recommendation-impact">
            <strong>预期影响：</strong>{{ rec.estimated_impact }}
          </p>

          <div v-if="rec.sql_statement" class="sql-section">
            <div class="sql-header">
              <span>操作语句</span>
              <el-button
                type="primary"
                link
                size="small"
                @click="copySQL(rec.sql_statement || '')"
              >
                复制
              </el-button>
            </div>
            <el-input
              :model-value="rec.sql_statement"
              type="textarea"
              :rows="3"
              readonly
            />
          </div>
        </div>
      </el-card>
    </div>

    <el-empty v-else description="暂无优化建议" />
  </el-card>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus'
import type { TableRecommendations } from '@/types/table'

defineProps<{
  recommendations: TableRecommendations
}>()

const getPriorityType = (priority: string): 'danger' | 'warning' | 'info' => {
  switch (priority) {
    case 'high':
      return 'danger'
    case 'medium':
      return 'warning'
    case 'low':
      return 'info'
    default:
      return 'info'
  }
}

const getPriorityText = (priority: string): string => {
  switch (priority) {
    case 'high':
      return '高优先级'
    case 'medium':
      return '中优先级'
    case 'low':
      return '低优先级'
    default:
      return '未知'
  }
}

const copySQL = async (sql: string) => {
  try {
    await navigator.clipboard.writeText(sql)
    ElMessage.success('复制成功')
  } catch {
    ElMessage.error('复制失败')
  }
}
</script>

<style scoped>
.recommendation-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.recommendation-card {
  margin-bottom: 0;
}

.recommendation-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.recommendation-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.recommendation-content {
  font-size: 14px;
  color: #606266;
}

.recommendation-description {
  margin: 0 0 8px 0;
}

.recommendation-impact {
  margin: 0 0 12px 0;
  color: #909399;
}

.sql-section {
  margin-top: 12px;
}

.sql-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-weight: 600;
  color: #303133;
}
</style>
