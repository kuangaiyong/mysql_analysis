<template>
  <div class="table-structure-view">
    <el-card class="mb-4">
      <template #header>
        <div class="card-header">
          <span>基本信息</span>
        </div>
      </template>
      <el-descriptions :column="4" border>
        <el-descriptions-item label="表名">{{ structure.table_name }}</el-descriptions-item>
        <el-descriptions-item label="引擎">{{ structure.engine }}</el-descriptions-item>
        <el-descriptions-item label="字符集">{{ structure.charset }}</el-descriptions-item>
        <el-descriptions-item label="排序规则">{{ structure.collation }}</el-descriptions-item>
        <el-descriptions-item label="注释" :span="4">{{ structure.comment || '-' }}</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-card class="mb-4">
      <template #header>
        <div class="card-header">
          <span>列信息</span>
        </div>
      </template>
      <el-table :data="structure.columns" stripe border>
        <el-table-column prop="ordinal_position" label="序号" width="80" />
        <el-table-column prop="column_name" label="字段名称" min-width="150" />
        <el-table-column prop="column_type" label="类型" min-width="120" />
        <el-table-column label="允许NULL" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_nullable === 'YES' ? 'danger' : 'success'">
              {{ row.is_nullable === 'YES' ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="键" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.column_key === 'PRI'" type="warning">PRI</el-tag>
            <el-tag v-else-if="row.column_key === 'UNI'" type="success">UNI</el-tag>
            <el-tag v-else-if="row.column_key === 'MUL'" type="info">MUL</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="column_default" label="默认值" width="120">
          <template #default="{ row }">
            {{ row.column_default || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="extra" label="额外信息" width="120">
          <template #default="{ row }">
            {{ row.extra || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="comment" label="注释" min-width="150" />
      </el-table>
    </el-card>

    <el-card v-if="structure.indexes?.length" class="mb-4">
      <template #header>
        <div class="card-header">
          <span>索引信息</span>
        </div>
      </template>
      <el-table :data="structure.indexes" stripe border>
        <el-table-column prop="index_name" label="索引名称" min-width="150" />
        <el-table-column prop="column_name" label="列名" min-width="150" />
        <el-table-column prop="index_type" label="类型" width="120" />
        <el-table-column label="主键" width="100">
          <template #default="{ row }">
            <el-tag :type="row.primary ? 'warning' : 'info'">
              {{ row.primary ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="唯一" width="100">
          <template #default="{ row }">
            <el-tag :type="row.unique ? 'success' : 'info'">
              {{ row.unique ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card v-if="structure.foreign_keys?.length">
      <template #header>
        <div class="card-header">
          <span>外键关系</span>
        </div>
      </template>
      <el-table :data="structure.foreign_keys" stripe border>
        <el-table-column prop="constraint_name" label="约束名称" min-width="180" />
        <el-table-column prop="column_name" label="列名" min-width="150" />
        <el-table-column prop="referenced_table_name" label="引用表" min-width="150" />
        <el-table-column prop="referenced_column_name" label="引用列" min-width="150" />
        <el-table-column prop="on_update" label="ON UPDATE" width="120" />
        <el-table-column prop="on_delete" label="ON DELETE" width="120" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import type { TableStructure } from '@/types/table'

defineProps<{
  structure: TableStructure
}>()
</script>

<style scoped>
.card-header {
  font-weight: 600;
}
</style>
