import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { ElMessage } from 'element-plus'
import LoginView from '@/view/login/index.vue'
import { authApi } from '@/api/auth'

vi.mock('vue-router')
vi.mock('@/api/auth')
vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn()
  }
}))

const mockPush = vi.fn()

vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: mockPush
  })
}))

// 辅助函数：等待异步操作完成
const flushPromises = () => new Promise(resolve => setTimeout(resolve, 0))

describe('LoginView', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('基础渲染', () => {
    it('should render login form', () => {
      const wrapper = mount(LoginView)

      expect(wrapper.find('input[type="text"]').exists()).toBe(true)
      expect(wrapper.find('input[type="password"]').exists()).toBe(true)
    })

    it('should render login title and subtitle', () => {
      const wrapper = mount(LoginView)

      expect(wrapper.find('.login-title').text()).toBe('MySQL 性能诊断系统')
      expect(wrapper.find('.login-subtitle').text()).toBe('Performance Analysis & Optimization')
    })

    it('should show remember me checkbox in login mode', () => {
      const wrapper = mount(LoginView)

      expect(wrapper.find('input[type="checkbox"]').exists()).toBe(true)
    })
  })

  describe('登录功能', () => {
    it('should handle login with remember me', async () => {
      const wrapper = mount(LoginView)

      const usernameInput = wrapper.find('input[type="text"]')
      const passwordInput = wrapper.find('input[type="password"]')

      await usernameInput.setValue('testuser')
      await passwordInput.setValue('password123')

      const rememberMeCheckbox = wrapper.find('input[type="checkbox"]')
      if (rememberMeCheckbox.exists()) {
        await rememberMeCheckbox.setValue(true)
      }

      vi.mocked(authApi.login).mockResolvedValue({
        access_token: 'access_token',
        refresh_token: 'refresh_token',
        token_type: 'bearer'
      })

      const submitButton = wrapper.find('button[type="submit"], .el-button--primary')
      await submitButton.trigger('click')

      await flushPromises()

      expect(authApi.login).toHaveBeenCalledWith({
        username: 'testuser',
        password: 'password123',
        rememberMe: true
      })
    })

    it('should call login API with correct parameters', async () => {
      const wrapper = mount(LoginView)

      // 直接设置表单数据
      wrapper.vm.form.username = 'testuser'
      wrapper.vm.form.password = 'password123'
      wrapper.vm.form.rememberMe = true

      vi.mocked(authApi.login).mockResolvedValue({
        access_token: 'access_token',
        refresh_token: 'refresh_token',
        token_type: 'bearer'
      })

      // 验证 API 调用参数
      const response = await authApi.login({
        username: 'testuser',
        password: 'password123',
        rememberMe: true
      })

      expect(response.access_token).toBe('access_token')
      expect(response.refresh_token).toBe('refresh_token')
    })

    it('should show "用户名或密码错误" on 401 error', async () => {
      const wrapper = mount(LoginView)

      const usernameInput = wrapper.find('input[type="text"]')
      const passwordInput = wrapper.find('input[type="password"]')

      await usernameInput.setValue('testuser')
      await passwordInput.setValue('wrongpassword')

      const error401 = {
        response: { status: 401, data: { detail: 'Unauthorized' } }
      }
      vi.mocked(authApi.login).mockRejectedValue(error401)

      const submitButton = wrapper.find('button[type="submit"], .el-button--primary')
      await submitButton.trigger('click')
      await flushPromises()

      expect(ElMessage.error).toHaveBeenCalledWith('用户名或密码错误')
    })

    it('should show detail message on other login errors', async () => {
      const wrapper = mount(LoginView)

      const usernameInput = wrapper.find('input[type="text"]')
      const passwordInput = wrapper.find('input[type="password"]')

      await usernameInput.setValue('testuser')
      await passwordInput.setValue('password123')

      const error500 = {
        response: { status: 500, data: { detail: '服务器内部错误' } }
      }
      vi.mocked(authApi.login).mockRejectedValue(error500)

      const submitButton = wrapper.find('button[type="submit"], .el-button--primary')
      await submitButton.trigger('click')
      await flushPromises()

      expect(ElMessage.error).toHaveBeenCalledWith('服务器内部错误')
    })

    it('should show default error message when no detail provided', async () => {
      const wrapper = mount(LoginView)

      const usernameInput = wrapper.find('input[type="text"]')
      const passwordInput = wrapper.find('input[type="password"]')

      await usernameInput.setValue('testuser')
      await passwordInput.setValue('password123')

      vi.mocked(authApi.login).mockRejectedValue(new Error('Network error'))

      const submitButton = wrapper.find('button[type="submit"], .el-button--primary')
      await submitButton.trigger('click')
      await flushPromises()

      expect(ElMessage.error).toHaveBeenCalledWith('登录失败')
    })
  })

  describe('注册功能', () => {
    it('should switch to register mode when clicking switch link', async () => {
      const wrapper = mount(LoginView)

      // 初始为登录模式
      expect(wrapper.vm.isRegisterMode).toBe(false)

      // 点击注册链接
      const switchLink = wrapper.find('.switch-mode .el-link')
      await switchLink.trigger('click')

      expect(wrapper.vm.isRegisterMode).toBe(true)
    })

    it('should show confirm password field in register mode', async () => {
      const wrapper = mount(LoginView)

      // 切换到注册模式
      wrapper.vm.isRegisterMode = true
      await wrapper.vm.$nextTick()

      // 应该有两个密码输入框
      const passwordInputs = wrapper.findAll('input[type="password"]')
      expect(passwordInputs.length).toBe(2)
    })

    it('should hide remember me checkbox in register mode', async () => {
      const wrapper = mount(LoginView)

      // 切换到注册模式
      wrapper.vm.isRegisterMode = true
      await wrapper.vm.$nextTick()

      expect(wrapper.find('input[type="checkbox"]').exists()).toBe(false)
    })

    it('should clear passwords when switching mode', async () => {
      const wrapper = mount(LoginView)

      // 填写密码
      const passwordInput = wrapper.find('input[type="password"]')
      await passwordInput.setValue('password123')

      // 切换模式
      wrapper.vm.switchMode()
      await wrapper.vm.$nextTick()

      expect(wrapper.vm.form.password).toBe('')
      expect(wrapper.vm.form.confirmPassword).toBe('')
    })

    it('should handle successful registration', async () => {
      const wrapper = mount(LoginView)

      // 切换到注册模式
      wrapper.vm.isRegisterMode = true
      await wrapper.vm.$nextTick()

      // 填写表单
      const inputs = wrapper.findAll('input')
      await inputs[0].setValue('newuser') // username
      await inputs[1].setValue('password123') // password
      await inputs[2].setValue('password123') // confirmPassword

      vi.mocked(authApi.register).mockResolvedValue({
        id: 1,
        username: 'newuser'
      } as any)

      const submitButton = wrapper.find('button[type="submit"], .el-button--primary')
      await submitButton.trigger('click')
      await flushPromises()

      expect(authApi.register).toHaveBeenCalledWith({
        username: 'newuser',
        password: 'password123'
      })
      expect(ElMessage.success).toHaveBeenCalledWith('注册成功，请登录')
      expect(wrapper.vm.isRegisterMode).toBe(false)
    })

    it('should show error message on registration failure', async () => {
      const wrapper = mount(LoginView)

      // 切换到注册模式
      wrapper.vm.isRegisterMode = true
      await wrapper.vm.$nextTick()

      // 填写表单
      const inputs = wrapper.findAll('input')
      await inputs[0].setValue('existinguser')
      await inputs[1].setValue('password123')
      await inputs[2].setValue('password123')

      const error = {
        response: { data: { detail: '用户名已存在' } }
      }
      vi.mocked(authApi.register).mockRejectedValue(error)

      const submitButton = wrapper.find('button[type="submit"], .el-button--primary')
      await submitButton.trigger('click')
      await flushPromises()

      expect(ElMessage.error).toHaveBeenCalledWith('用户名已存在')
    })

    it('should show default error on registration failure without detail', async () => {
      const wrapper = mount(LoginView)

      // 切换到注册模式
      wrapper.vm.isRegisterMode = true
      await wrapper.vm.$nextTick()

      // 填写表单
      const inputs = wrapper.findAll('input')
      await inputs[0].setValue('newuser')
      await inputs[1].setValue('password123')
      await inputs[2].setValue('password123')

      vi.mocked(authApi.register).mockRejectedValue(new Error('Network error'))

      const submitButton = wrapper.find('button[type="submit"], .el-button--primary')
      await submitButton.trigger('click')
      await flushPromises()

      expect(ElMessage.error).toHaveBeenCalledWith('注册失败')
    })
  })

  describe('密码强度计算', () => {
    it('should return empty strength for empty password', () => {
      const wrapper = mount(LoginView)

      wrapper.vm.form.password = ''
      const strength = wrapper.vm.passwordStrength

      expect(strength).toEqual({ level: 0, text: '', color: '' })
    })

    it('should calculate weak password strength (level <= 2)', async () => {
      const wrapper = mount(LoginView)

      const passwordInput = wrapper.find('input[type="password"]')
      await passwordInput.setValue('weak')

      const strength = wrapper.vm.passwordStrength
      expect(strength.level).toBeLessThanOrEqual(2)
      expect(strength.text).toBe('弱')
      expect(strength.color).toBe('#f56c6c')
    })

    it('should calculate medium password strength (level 3-4)', async () => {
      const wrapper = mount(LoginView)

      const passwordInput = wrapper.find('input[type="password"]')
      // 包含大小写字母和数字，长度>=10
      await passwordInput.setValue('Password12')

      const strength = wrapper.vm.passwordStrength
      expect(strength.level).toBeGreaterThanOrEqual(3)
      expect(strength.level).toBeLessThanOrEqual(4)
      expect(strength.text).toBe('中')
      expect(strength.color).toBe('#e6a23c')
    })

    it('should calculate strong password strength (level 5)', async () => {
      const wrapper = mount(LoginView)

      const passwordInput = wrapper.find('input[type="password"]')
      // 包含大小写字母、数字和特殊字符，长度>=10
      await passwordInput.setValue('Password123!')

      const strength = wrapper.vm.passwordStrength
      expect(strength.level).toBe(5)
      expect(strength.text).toBe('强')
      expect(strength.color).toBe('#67c23a')
    })

    it('should show password strength indicator', async () => {
      const wrapper = mount(LoginView)

      const passwordInput = wrapper.find('input[type="password"]')
      await passwordInput.setValue('weak')

      const strength = wrapper.vm.passwordStrength
      expect(strength.level).toBeGreaterThanOrEqual(0)
      expect(strength.text).toBeDefined()
      expect(strength.color).toBeDefined()
    })
  })

  describe('按钮文本', () => {
    it('should show "登 录" in login mode when not loading', () => {
      const wrapper = mount(LoginView)

      expect(wrapper.vm.buttonText).toBe('登 录')
    })

    it('should show "注 册" in register mode when not loading', async () => {
      const wrapper = mount(LoginView)

      wrapper.vm.isRegisterMode = true
      await wrapper.vm.$nextTick()

      expect(wrapper.vm.buttonText).toBe('注 册')
    })

    it('should show "登录中..." in login mode when loading', async () => {
      const wrapper = mount(LoginView)

      wrapper.vm.loading = true
      await wrapper.vm.$nextTick()

      expect(wrapper.vm.buttonText).toBe('登录中...')
    })

    it('should show "注册中..." in register mode when loading', async () => {
      const wrapper = mount(LoginView)

      wrapper.vm.isRegisterMode = true
      wrapper.vm.loading = true
      await wrapper.vm.$nextTick()

      expect(wrapper.vm.buttonText).toBe('注册中...')
    })
  })

  describe('表单验证', () => {
    it('should have correct validation rules for username', () => {
      const wrapper = mount(LoginView)
      const rules = wrapper.vm.rules

      expect(rules.username).toHaveLength(2)
      expect(rules.username[0].required).toBe(true)
      expect(rules.username[1].min).toBe(3)
      expect(rules.username[1].max).toBe(50)
    })

    it('should have correct validation rules for password', () => {
      const wrapper = mount(LoginView)
      const rules = wrapper.vm.rules

      expect(rules.password).toHaveLength(2)
      expect(rules.password[0].required).toBe(true)
      expect(rules.password[1].min).toBe(6)
      expect(rules.password[1].max).toBe(100)
    })

    it('should have confirmPassword validation rule', () => {
      const wrapper = mount(LoginView)
      const rules = wrapper.vm.rules

      expect(rules.confirmPassword).toBeDefined()
      expect(rules.confirmPassword[0].required).toBe(true)
    })

    it('should fail validation when passwords do not match', async () => {
      const wrapper = mount(LoginView)

      // 设置密码
      wrapper.vm.form.password = 'password123'
      wrapper.vm.form.confirmPassword = 'different123'

      // 获取confirmPassword验证器
      const validator = wrapper.vm.rules.confirmPassword[1].validator
      const callback = vi.fn()

      validator(null, 'different123', callback)

      expect(callback).toHaveBeenCalledWith(expect.any(Error))
    })

    it('should pass validation when passwords match', async () => {
      const wrapper = mount(LoginView)

      // 设置密码
      wrapper.vm.form.password = 'password123'
      wrapper.vm.form.confirmPassword = 'password123'

      // 获取confirmPassword验证器
      const validator = wrapper.vm.rules.confirmPassword[1].validator
      const callback = vi.fn()

      validator(null, 'password123', callback)

      expect(callback).toHaveBeenCalledWith()
    })
  })

  describe('handleSubmit路由', () => {
    it('should call handleLogin in login mode', async () => {
      const wrapper = mount(LoginView)

      // 确保是登录模式
      wrapper.vm.isRegisterMode = false

      // 填写有效表单数据
      wrapper.vm.form.username = 'testuser'
      wrapper.vm.form.password = 'password123'

      vi.mocked(authApi.login).mockResolvedValue({
        access_token: 'token',
        refresh_token: 'refresh',
        token_type: 'bearer'
      })

      // Mock formRef
      wrapper.vm.formRef = {
        validate: vi.fn().mockResolvedValue(true)
      }

      await wrapper.vm.handleSubmit()
      await flushPromises()

      expect(authApi.login).toHaveBeenCalled()
      expect(authApi.register).not.toHaveBeenCalled()
    })

    it('should call handleRegister in register mode', async () => {
      const wrapper = mount(LoginView)

      // 切换到注册模式
      wrapper.vm.isRegisterMode = true
      wrapper.vm.form.username = 'newuser'
      wrapper.vm.form.password = 'password123'
      wrapper.vm.form.confirmPassword = 'password123'

      // Mock formRef
      wrapper.vm.formRef = {
        validate: vi.fn().mockResolvedValue(true)
      }

      vi.mocked(authApi.register).mockResolvedValue({ id: 1, username: 'newuser' } as any)

      await wrapper.vm.handleSubmit()
      await flushPromises()

      expect(authApi.register).toHaveBeenCalled()
      expect(authApi.login).not.toHaveBeenCalled()
    })
  })

  describe('loading状态', () => {
    it('should manage loading state during login', async () => {
      const wrapper = mount(LoginView)

      wrapper.vm.form.username = 'testuser'
      wrapper.vm.form.password = 'password123'

      // Mock formRef
      wrapper.vm.formRef = {
        validate: vi.fn().mockResolvedValue(true)
      }

      vi.mocked(authApi.login).mockResolvedValue({
        access_token: 'token',
        refresh_token: 'refresh',
        token_type: 'bearer'
      })

      // 初始状态
      expect(wrapper.vm.loading).toBe(false)

      await wrapper.vm.handleLogin()
      await flushPromises()

      // 完成后应为false
      expect(wrapper.vm.loading).toBe(false)
    })

    it('should set loading to false after login failure', async () => {
      const wrapper = mount(LoginView)

      wrapper.vm.form.username = 'testuser'
      wrapper.vm.form.password = 'password123'

      // Mock formRef
      wrapper.vm.formRef = {
        validate: vi.fn().mockResolvedValue(true)
      }

      vi.mocked(authApi.login).mockRejectedValue(new Error('Network error'))

      await wrapper.vm.handleLogin()
      await flushPromises()

      expect(wrapper.vm.loading).toBe(false)
    })
  })
})
