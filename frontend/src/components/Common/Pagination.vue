<template>
  <el-pagination
    v-model:current-page="pagination.page"
    v-model:page-size="pagination.pageSize"
    :total="pagination.total"
    :page-sizes="pageSizes"
    :layout="layout"
    :style="{ marginTop: marginTop, justifyContent: justifyContent }"
    @size-change="handleSizeChange"
    @current-change="handlePageChange"
  />
</template>

<script setup lang="ts">
interface Pagination {
  page: number
  pageSize: number
  total: number
}

interface Props {
  pagination: Pagination
  pageSizes?: number[]
  layout?: string
  marginTop?: string
  justifyContent?: string
}

const props = withDefaults(defineProps<Props>(), {
  pageSizes: () => [10, 20, 50, 100],
  layout: 'total, sizes, prev, pager, next, jumper',
  marginTop: '20px',
  justifyContent: 'flex-end'
})

const emit = defineEmits<{
  sizeChange: [size: number]
  pageChange: [page: number]
}>()

const handleSizeChange = (size: number) => {
  props.pagination.pageSize = size
  props.pagination.page = 1
  emit('sizeChange', size)
}

const handlePageChange = (page: number) => {
  props.pagination.page = page
  emit('pageChange', page)
}
</script>
