<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { DataAnalysis } from '@element-plus/icons-vue'
import { authApi } from '@/api/auth'
import { setAccessToken, setRefreshToken } from '@/types/auth'

const router = useRouter()
const loading = ref(false)
const isRegisterMode = ref(false)

const form = reactive({
  username: '',
  password: '',
  confirmPassword: '',
  rememberMe: false
})

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度在 3 到 50 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 100, message: '密码长度在 6 到 100 个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { 
      validator: (_rule: any, value: string, callback: any) => {
        if (value !== form.password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

const formRef = ref()
const buttonText = computed(() => {
  if (loading.value) return isRegisterMode.value ? '注册中...' : '登录中...'
  return isRegisterMode.value ? '注 册' : '登 录'
})

const passwordStrength = computed(() => {
  const password = form.password
  if (!password) return { level: 0, text: '', color: '' }

  let level = 0
  if (password.length >= 6) level++
  if (password.length >= 10) level++
  if (/[a-z]/.test(password) && /[A-Z]/.test(password)) level++
  if (/[0-9]/.test(password)) level++
  if (/[^a-zA-Z0-9]/.test(password)) level++

  if (level <= 2) return { level, text: '弱', color: '#f56c6c' }
  if (level <= 4) return { level, text: '中', color: '#e6a23c' }
  return { level, text: '强', color: '#67c23a' }
})

const handleLogin = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
  } catch {
    return
  }

  loading.value = true
  try {
    const response = await authApi.login({
      username: form.username,
      password: form.password,
      rememberMe: form.rememberMe
    })
    setAccessToken(response.access_token)
    if (response.refresh_token) {
      setRefreshToken(response.refresh_token)
    }
    ElMessage.success('登录成功')
    router.push('/ai-diagnostic')
  } catch (error: any) {
    if (error.response?.status === 401) {
      ElMessage.error('用户名或密码错误')
    } else {
      ElMessage.error(error.response?.data?.detail || '登录失败')
    }
  } finally {
    loading.value = false
  }
}

const handleRegister = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
  } catch {
    return
  }

  loading.value = true
  try {
    await authApi.register({
      username: form.username,
      password: form.password
    })
    ElMessage.success('注册成功，请登录')
    isRegisterMode.value = false
    form.password = ''
    form.confirmPassword = ''
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '注册失败')
  } finally {
    loading.value = false
  }
}

const handleSubmit = () => {
  if (isRegisterMode.value) {
    handleRegister()
  } else {
    handleLogin()
  }
}

const switchMode = () => {
  isRegisterMode.value = !isRegisterMode.value
  form.password = ''
  form.confirmPassword = ''
  formRef.value?.clearValidate()
}
</script>

<template>
  <div class="login-container">
    <div class="login-bg">
      <div class="bg-gradient"></div>
      <div class="bg-mesh"></div>
    </div>
    
    <div class="login-card">
      <div class="login-header">
        <div class="logo-icon">
          <el-icon :size="40"><DataAnalysis /></el-icon>
        </div>
        <h1 class="login-title">MySQL 性能诊断系统</h1>
        <p class="login-subtitle">Performance Analysis & Optimization</p>
      </div>
      
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        class="login-form"
        @submit.prevent="handleSubmit"
      >
        <el-form-item prop="username">
          <el-input
            v-model="form.username"
            placeholder="用户名"
            :prefix-icon="User"
            size="large"
          />
        </el-form-item>
        
        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="密码"
            :prefix-icon="Lock"
            size="large"
            show-password
            @keyup.enter="handleSubmit"
          />
          <div v-if="isRegisterMode && form.password" class="password-strength">
            <div class="strength-bar">
              <div
                class="strength-fill"
                :style="{ width: passwordStrength.level * 20 + '%', backgroundColor: passwordStrength.color }"
              ></div>
            </div>
            <span class="strength-text" :style="{ color: passwordStrength.color }">
              {{ passwordStrength.text }}
            </span>
          </div>
        </el-form-item>
        
        <el-form-item v-if="isRegisterMode" prop="confirmPassword">
          <el-input
            v-model="form.confirmPassword"
            type="password"
            placeholder="确认密码"
            :prefix-icon="Lock"
            size="large"
            show-password
            @keyup.enter="handleSubmit"
          />
        </el-form-item>

        <el-form-item v-if="!isRegisterMode">
          <el-checkbox v-model="form.rememberMe">记住我（7天）</el-checkbox>
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            size="large"
            class="login-btn"
            :loading="loading"
            @click="handleSubmit"
          >
            {{ buttonText }}
          </el-button>
        </el-form-item>
      </el-form>
      
      <div class="switch-mode">
        <span v-if="!isRegisterMode">
          没有账号？
          <el-link type="primary" @click="switchMode">立即注册</el-link>
        </span>
        <span v-else>
          已有账号？
          <el-link type="primary" @click="switchMode">立即登录</el-link>
        </span>
      </div>
      
      <div class="login-footer">
        <span>MySQL Performance Analysis System</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
}

.login-bg {
  position: absolute;
  inset: 0;
  z-index: 0;
}

.bg-gradient {
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
}

.bg-mesh {
  position: absolute;
  inset: 0;
  background-image: 
    radial-gradient(at 20% 30%, rgba(59, 130, 246, 0.15) 0px, transparent 50%),
    radial-gradient(at 80% 70%, rgba(16, 185, 129, 0.1) 0px, transparent 50%),
    radial-gradient(at 50% 50%, rgba(99, 102, 241, 0.08) 0px, transparent 50%);
}

.login-card {
  position: relative;
  z-index: 1;
  width: 420px;
  padding: 48px 40px;
  background: rgba(30, 41, 59, 0.85);
  backdrop-filter: blur(20px);
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 
    0 25px 50px -12px rgba(0, 0, 0, 0.5),
    0 0 0 1px rgba(255, 255, 255, 0.05) inset;
}

.login-header {
  text-align: center;
  margin-bottom: 36px;
}

.logo-icon {
  width: 72px;
  height: 72px;
  margin: 0 auto 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #3b82f6 0%, #10b981 100%);
  border-radius: 16px;
  color: #fff;
  box-shadow: 0 8px 24px rgba(59, 130, 246, 0.3);
}

.login-title {
  font-size: 24px;
  font-weight: 600;
  color: #f1f5f9;
  margin: 0 0 8px;
  letter-spacing: 0.5px;
}

.login-subtitle {
  font-size: 13px;
  color: #64748b;
  margin: 0;
  text-transform: uppercase;
  letter-spacing: 2px;
}

.login-form {
  margin-top: 0;
}

.login-form :deep(.el-input__wrapper) {
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: none;
  transition: all 0.3s ease;
}

.login-form :deep(.el-input__wrapper:hover) {
  border-color: rgba(59, 130, 246, 0.5);
}

.login-form :deep(.el-input__wrapper.is-focus) {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
}

.login-form :deep(.el-input__inner) {
  color: #f1f5f9;
}

.login-form :deep(.el-input__inner::placeholder) {
  color: #64748b;
}

.login-form :deep(.el-input__prefix) {
  color: #64748b;
}

.login-form :deep(.el-form-item) {
  margin-bottom: 24px;
}

.login-form :deep(.el-form-item__error) {
  padding-top: 4px;
}

.login-btn {
  width: 100%;
  height: 48px;
  font-size: 16px;
  font-weight: 500;
  border: none;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  box-shadow: 0 4px 14px rgba(59, 130, 246, 0.4);
  transition: all 0.3s ease;
}

.login-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(59, 130, 246, 0.5);
}

.login-btn:active {
  transform: translateY(0);
}

.switch-mode {
  text-align: center;
  font-size: 14px;
  color: #94a3b8;
}

.switch-mode .el-link {
  font-size: 14px;
  font-weight: 500;
}

.login-footer {
  text-align: center;
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.login-footer span {
  font-size: 12px;
  color: #475569;
  letter-spacing: 0.5px;
}

@media (max-width: 480px) {
  .login-card {
    width: calc(100% - 32px);
    padding: 32px 24px;
  }
  
  .login-title {
    font-size: 20px;
  }
  
  .logo-icon {
    width: 60px;
    height: 60px;
  }
}

.password-strength {
  margin-top: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.strength-bar {
  flex: 1;
  height: 4px;
  background: #e5e7eb;
  border-radius: 2px;
  overflow: hidden;
}

.strength-fill {
  height: 100%;
  transition: all 0.3s ease;
}

.strength-text {
  font-size: 12px;
  font-weight: 500;
  min-width: 20px;
}
</style>
