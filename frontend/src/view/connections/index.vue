<template>
  <div class="page-container">
    <PageHeader title="连接管理" show-add add-text="添加连接" @add="handleAdd" />

    <el-card>
      <el-form :model="searchForm" inline class="search-form">
        <el-form-item label="名称">
          <el-input v-model="searchForm.name" placeholder="请输入连接名称" clearable class="input-lg" />
        </el-form-item>
        <el-form-item label="主机">
          <el-input v-model="searchForm.host" placeholder="请输入主机地址" clearable class="input-lg" />
        </el-form-item>
        <el-form-item label="数据库">
          <el-input v-model="searchForm.database" placeholder="请输入数据库名" clearable class="input-lg" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="handleSearch">查询</el-button>
          <el-button :icon="Refresh" @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table
        v-loading="loading"
        :data="tableData"
        stripe
        border
        class="w-full"
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="连接名称" min-width="150" />
        <el-table-column prop="host" label="主机地址" min-width="150" />
        <el-table-column prop="port" label="端口" width="100" />
        <el-table-column prop="username" label="用户名" width="120" />
        <el-table-column prop="database_name" label="数据库" min-width="120" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <div class="status-indicator">
              <span :class="['status-dot', row.is_active ? 'online' : 'offline']"></span>
              <span>{{ row.is_active ? '在线' : '离线' }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link :icon="Edit" @click="handleEdit(row)">编辑</el-button>
            <el-button type="warning" link :icon="ConnectionIcon" @click="handleTest(row)">测试</el-button>
            <el-button type="danger" link :icon="Delete" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <Pagination
        :pagination="pagination"
        @size-change="handleSizeChange"
        @page-change="handlePageChange"
      />
    </el-card>

    <ConnectionDialog
      v-model:visible="dialogVisible"
      :connection="currentConnection"
      @success="handleDialogSuccess"
    />

    <ConnectionTest
      v-model:visible="testDialogVisible"
      :connection="currentConnection || undefined"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, Edit, Delete, Connection as ConnectionIcon } from '@element-plus/icons-vue'
import { connectionsApi } from '@/api/connection'
import type { Connection } from '@/types/connection'
import ConnectionDialog from './components/ConnectionDialog.vue'
import ConnectionTest from './components/ConnectionTest.vue'
import Pagination from '@/components/Common/Pagination.vue'
import PageHeader from '@/components/Common/PageHeader.vue'

defineOptions({
  name: 'Connections'
})

const loading = ref(false)
const tableData = ref<Connection[]>([])
const dialogVisible = ref(false)
const testDialogVisible = ref(false)
const currentConnection = ref<Connection | null>(null)

const searchForm = reactive({
  name: '',
  host: '',
  database: ''
})

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

const fetchData = async () => {
  loading.value = true
  tableData.value = []  // 清空现有数据，避免显示旧数据
  try {
    const skip = (pagination.page - 1) * pagination.pageSize
    const params: any = { skip, limit: pagination.pageSize }
    
    // 添加搜索参数
    if (searchForm.name) params.name = searchForm.name
    if (searchForm.host) params.host = searchForm.host
    if (searchForm.database) params.database_name = searchForm.database
    
    const data = await connectionsApi.getAll(params)
    tableData.value = Array.isArray(data) ? data : []
    
    // 修复分页总数计算：应该根据返回数据判断是否有更多数据
    if (data && data.length > 0) {
      if (data.length >= pagination.pageSize) {
        // 返回数据等于pageSize，说明可能还有更多数据
        // 使用估算值：当前页起始位置 + 返回数量 + 1
        pagination.total = skip + data.length + 1
      } else {
        // 返回数据少于pageSize，说明这是最后一页
        pagination.total = skip + data.length
      }
    } else {
      pagination.total = 0
    }
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '获取数据失败')
    pagination.total = 0
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  fetchData()
}

const handleReset = () => {
  searchForm.name = ''
  searchForm.host = ''
  searchForm.database = ''
  pagination.page = 1
  fetchData()
}

const handleAdd = () => {
  currentConnection.value = null
  dialogVisible.value = true
}

const handleEdit = (row: Connection) => {
  currentConnection.value = { ...row }
  dialogVisible.value = true
}

const handleTest = (row: Connection) => {
  currentConnection.value = { ...row }
  testDialogVisible.value = true
}

const handleDelete = async (row: Connection) => {
  try {
    await ElMessageBox.confirm('确定要删除该连接吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    await connectionsApi.delete(row.id)
    ElMessage.success('删除成功')
    fetchData()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}

const handleDialogSuccess = () => {
  fetchData()
}

const handleSizeChange = (size: number) => {
  pagination.pageSize = size
  pagination.page = 1
  fetchData()
}

const handlePageChange = (page: number) => {
  pagination.page = page
  fetchData()
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped lang="scss">
/* 页面容器使用 .page-container 工具类 */
/* 搜索表单使用 .search-form 工具类 */
/* 状态指示器使用 .status-indicator 工具类 */
</style>
