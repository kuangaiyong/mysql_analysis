<template>
  <el-dialog
    v-model="dialogVisible"
    :title="isEdit ? '编辑连接' : '新增连接'"
    width="600px"
    :close-on-click-modal="false"
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-width="100px"
      label-position="right"
    >
      <el-form-item label="连接名称" prop="name">
        <el-input v-model="formData.name" placeholder="请输入连接名称" clearable />
      </el-form-item>

      <el-form-item label="主机地址" prop="host">
        <el-input v-model="formData.host" placeholder="请输入主机地址" clearable />
      </el-form-item>

      <el-form-item label="端口" prop="port">
        <el-input-number v-model="formData.port" :min="1" :max="65535" controls-position="right" style="width: 100%" />
      </el-form-item>

      <el-form-item label="用户名" prop="username">
        <el-input v-model="formData.username" placeholder="请输入用户名" clearable />
      </el-form-item>

      <el-form-item label="密码" prop="password">
        <el-input v-model="formData.password" type="password" placeholder="请输入密码" clearable show-password />
      </el-form-item>

      <el-form-item label="数据库名" prop="database_name">
        <el-input v-model="formData.database_name" placeholder="请输入数据库名（可选）" clearable />
      </el-form-item>

      <el-form-item label="连接池大小" prop="connection_pool_size">
        <el-input-number v-model="formData.connection_pool_size" :min="1" :max="100" controls-position="right" style="width: 100%" />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="handleCancel">取消</el-button>
      <el-button type="primary" :loading="submitting" @click="handleSubmit">确定</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { connectionsApi } from '@/api/connection'
import type { Connection, ConnectionCreate, ConnectionUpdate } from '@/types/connection'

const props = defineProps<{
  visible: boolean
  connection: Connection | null
}>()

const emit = defineEmits<{
  (e: 'update:visible', value: boolean): void
  (e: 'success'): void
}>()

const formRef = ref<FormInstance>()
const submitting = ref(false)

const dialogVisible = computed({
  get: () => props.visible,
  set: (val) => emit('update:visible', val)
})

const isEdit = computed(() => !!props.connection)

const formData = ref<ConnectionCreate>({
  name: '',
  host: '',
  port: 3306,
  username: '',
  password: '',
  database_name: '',
  connection_pool_size: 10
})

const rules: FormRules<ConnectionCreate> = {
  name: [
    { required: true, message: '请输入连接名称', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  host: [
    { required: true, message: '请输入主机地址', trigger: 'blur' }
  ],
  port: [
    { required: true, message: '请输入端口号', trigger: 'blur' },
    { type: 'number', min: 1, max: 65535, message: '端口号范围为 1-65535', trigger: 'blur' }
  ],
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' }
  ]
}

const resetForm = () => {
  formData.value = {
    name: '',
    host: '',
    port: 3306,
    username: '',
    password: '',
    database_name: '',
    connection_pool_size: 10
  }
  formRef.value?.clearValidate()
}

watch(() => props.visible, (val) => {
  if (val) {
    if (props.connection) {
      formData.value = {
        name: props.connection.name,
        host: props.connection.host,
        port: props.connection.port,
        username: props.connection.username,
        password: '',
        database_name: props.connection.database_name || '',
        connection_pool_size: 10
      }
    } else {
      resetForm()
    }
  }
})

const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    submitting.value = true

    if (isEdit.value && props.connection) {
      const updateData: ConnectionUpdate = {
        name: formData.value.name,
        host: formData.value.host,
        port: formData.value.port,
        username: formData.value.username,
        database_name: formData.value.database_name || undefined,
        connection_pool_size: formData.value.connection_pool_size
      }
      if (formData.value.password) {
        updateData.password = formData.value.password
      }
      await connectionsApi.update(props.connection.id, updateData)
      ElMessage.success('更新成功')
    } else {
      await connectionsApi.create(formData.value)
      ElMessage.success('创建成功')
    }

    emit('success')
    dialogVisible.value = false
  } catch (error: any) {
    if (error !== false) {
      ElMessage.error(error.response?.data?.detail || '操作失败')
    }
  } finally {
    submitting.value = false
  }
}

const handleCancel = () => {
  dialogVisible.value = false
}
</script>
