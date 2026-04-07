<template>
  <el-dialog
    v-model="dialogVisible"
    title="测试连接"
    width="500px"
    :close-on-click-modal="false"
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-width="100px"
      label-position="right"
    >
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
    </el-form>

    <div v-if="testResult" class="test-result">
      <div v-if="testResult.status === 'success'" class="success">
        <el-icon class="success-icon"><CircleCheck /></el-icon>
        <span>连接成功</span>
        <span v-if="testResult.latency" class="latency">耗时: {{ testResult.latency }}ms</span>
      </div>
      <div v-else class="error">
        <el-icon class="error-icon"><CircleClose /></el-icon>
        <span>连接失败: {{ testResult.message }}</span>
      </div>
    </div>

    <template #footer>
      <el-button @click="handleCancel">取消</el-button>
      <el-button type="primary" :loading="testing" @click="handleTest">
        <el-icon class="mr-1"><ConnectionIcon /></el-icon>
        测试连接
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Connection as ConnectionIcon, CircleCheck, CircleClose } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import { connectionsApi } from '@/api/connection'
import type { ConnectionTest, ConnectionTestResult } from '@/types/connection'
import type { Connection as ConnectionType } from '@/types/connection'

const props = defineProps<{
  visible: boolean
  connection?: ConnectionType
}>()

const emit = defineEmits<{
  (e: 'update:visible', value: boolean): void
}>()

const formRef = ref<FormInstance>()
const testing = ref(false)
const testResult = ref<ConnectionTestResult | null>(null)

const dialogVisible = computed({
  get: () => props.visible,
  set: (val) => emit('update:visible', val)
})

const formData = ref<ConnectionTest>({
  host: '',
  port: 3306,
  username: '',
  password: '',
  database_name: ''
})

const rules: FormRules<ConnectionTest> = {
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

watch(() => props.visible, (val) => {
  if (val) {
    testResult.value = null
    if (props.connection) {
      formData.value = {
        host: props.connection.host,
        port: props.connection.port,
        username: props.connection.username,
        password: '',
        database_name: props.connection.database_name || ''
      }
    } else {
      resetForm()
    }
  }
})

const resetForm = () => {
  formData.value = {
    host: '',
    port: 3306,
    username: '',
    password: '',
    database_name: ''
  }
  formRef.value?.clearValidate()
}

const handleTest = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    testing.value = true
    testResult.value = null

    const startTime = Date.now()
    const result = await connectionsApi.test(formData.value)
    const latency = Date.now() - startTime

    testResult.value = {
      ...result,
      latency
    }
  } catch (error: any) {
    if (error.response?.status === 400) {
      testResult.value = {
        status: 'error',
        message: error.response.data.detail || '连接失败'
      }
    } else {
      ElMessage.error(error.response?.data?.detail || '测试失败')
    }
  } finally {
    testing.value = false
  }
}

const handleCancel = () => {
  dialogVisible.value = false
}
</script>

<style scoped lang="scss">
.test-result {
  padding: 12px;
  border-radius: 4px;
  margin-top: 16px;

  .success {
    display: flex;
    align-items: center;
    gap: 8px;
    color: #67c23a;
    background-color: #f0f9ff;
    padding: 12px;

    .success-icon {
      font-size: 20px;
    }

    .latency {
      margin-left: auto;
      font-size: 12px;
      color: #909399;
    }
  }

  .error {
    display: flex;
    align-items: center;
    gap: 8px;
    color: #f56c6c;
    background-color: #fef0f0;
    padding: 12px;

    .error-icon {
      font-size: 20px;
    }
  }
}

.mr-1 {
  margin-right: 4px;
}
</style>
