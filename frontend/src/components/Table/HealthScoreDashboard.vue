<template>
  <div class="health-score-dashboard">
    <el-row :gutter="20">
      <el-col :span="8">
        <el-card class="score-card">
          <div class="score-ring">
            <el-progress
              type="dashboard"
              :percentage="healthScore.total_score"
              :color="getScoreColor(healthScore.total_score)"
              :width="150"
            >
              <template #default>
                <span class="score-value">{{ healthScore.total_score }}</span>
                <span class="score-grade">等级: {{ healthScore.grade }}</span>
              </template>
            </el-progress>
          </div>
          <div class="score-label">健康评分</div>
        </el-card>
      </el-col>

      <el-col :span="16">
        <el-card>
          <template #header>各维度评分</template>
          <div class="dimension-list">
            <div
              v-for="dim in healthScore.dimensions"
              :key="dim.name"
              class="dimension-item"
            >
              <div class="dimension-header">
                <span class="dimension-name">{{ dim.name }}</span>
                <span class="dimension-weight">权重: {{ (dim.weight * 100).toFixed(0) }}%</span>
              </div>
              <el-progress
                :percentage="dim.score"
                :color="getScoreColor(dim.score)"
              />
              <div v-if="dim.details" class="dimension-details">{{ dim.details }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import type { TableHealthScore } from '@/types/table'

defineProps<{
  healthScore: TableHealthScore
}>()

const getScoreColor = (score: number): string => {
  if (score >= 90) return '#67C23A'
  if (score >= 70) return '#E6A23C'
  return '#F56C6C'
}
</script>

<style scoped>
.health-score-dashboard {
  padding: 10px 0;
}

.score-card {
  text-align: center;
}

.score-ring {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-bottom: 16px;
}

.score-value {
  display: block;
  font-size: 32px;
  font-weight: bold;
  line-height: 1;
}

.score-grade {
  display: block;
  font-size: 14px;
  color: #909399;
  margin-top: 8px;
}

.score-label {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.dimension-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.dimension-item {
  padding: 12px;
  background: #f5f7fa;
  border-radius: 4px;
}

.dimension-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.dimension-name {
  font-weight: 600;
  color: #303133;
}

.dimension-weight {
  font-size: 12px;
  color: #909399;
}

.dimension-details {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
</style>
