<template>
  <el-dropdown @command="handleCommand">
    <div class="user-dropdown flex items-center gap-3 cursor-pointer">
      <el-avatar :size="32">
        <el-icon :size="20">
          <User />
        </el-icon>
      </el-avatar>
      <span class="text-slate-700 dark:text-slate-200">{{ username }}</span>
    </div>
    <template #dropdown>
      <el-dropdown-menu>
        <el-dropdown-item command="settings">
          <el-icon><Setting /></el-icon>
          <span>个人设置</span>
        </el-dropdown-item>
        <el-dropdown-item divided command="logout">
          <el-icon><SwitchButton /></el-icon>
          <span>退出登录</span>
        </el-dropdown-item>
      </el-dropdown-menu>
    </template>
  </el-dropdown>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { User, Setting, SwitchButton } from '@element-plus/icons-vue'
import { clearTokens, getToken, getRefreshToken } from '@/types/auth'
import { authApi } from '@/api/auth'

defineOptions({
  name: 'UserDropdown'
})

const router = useRouter()

const username = computed(() => {
  const token = getToken()
  if (token) {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]))
      return payload.sub || '用户'
    } catch {
      return '用户'
    }
  }
  return '用户'
})

const handleCommand = async (command: string) => {
  if (command === 'logout') {
    try {
      await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      })
      const refreshToken = getRefreshToken()
      if (refreshToken) {
        try {
          await authApi.logout(refreshToken)
        } catch (error) {
          console.error('撤销 Refresh Token 失败:', error)
        }
      }
      clearTokens()
      ElMessage.success('已退出登录')
      router.push('/login')
    } catch {
      // 用户取消
    }
  } else if (command === 'settings') {
    ElMessage.info('个人设置功能开发中，敬请期待')
  }
}
</script>

<style scoped>
.user-dropdown {
  padding: 8px 12px;
  border-radius: 6px;
  transition: background-color 0.3s;
}

.user-dropdown:hover {
  background-color: var(--el-bg-color-page);
}
</style>
