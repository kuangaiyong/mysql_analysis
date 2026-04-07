import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { defineComponent, ref } from 'vue'

// 模拟连接对话框组件
const ConnectionDialog = defineComponent({
  template: `
    <div class="connection-dialog">
      <input v-model="form.name" class="name-input" />
      <input v-model="form.host" class="host-input" />
      <input v-model="form.port" class="port-input" type="number" />
      <input v-model="form.username" class="username-input" />
      <input v-model="form.password" class="password-input" type="password" />
      <button @click="handleSubmit" class="submit-btn">保存</button>
      <button @click="handleTest" class="test-btn">测试连接</button>
    </div>
  `,
  setup() {
    const form = ref({
      name: '',
      host: '',
      port: 3306,
      username: '',
      password: ''
    })
    
    const handleSubmit = () => {
      console.log('Submit:', form.value)
    }
    
    const handleTest = () => {
      console.log('Test connection')
    }
    
    return { form, handleSubmit, handleTest }
  }
})

describe('ConnectionDialog', () => {
  it('should render form inputs', () => {
    const wrapper = mount(ConnectionDialog)
    
    expect(wrapper.find('.name-input').exists()).toBe(true)
    expect(wrapper.find('.host-input').exists()).toBe(true)
    expect(wrapper.find('.port-input').exists()).toBe(true)
    expect(wrapper.find('.username-input').exists()).toBe(true)
    expect(wrapper.find('.password-input').exists()).toBe(true)
  })

  it('should have default port value', () => {
    const wrapper = mount(ConnectionDialog)
    const portInput = wrapper.find('.port-input')
    
    expect(portInput.element.value).toBe('3306')
  })

  it('should render action buttons', () => {
    const wrapper = mount(ConnectionDialog)
    
    expect(wrapper.find('.submit-btn').exists()).toBe(true)
    expect(wrapper.find('.test-btn').exists()).toBe(true)
    expect(wrapper.find('.submit-btn').text()).toBe('保存')
    expect(wrapper.find('.test-btn').text()).toBe('测试连接')
  })

  it('should update form data on input', async () => {
    const wrapper = mount(ConnectionDialog)
    
    await wrapper.find('.name-input').setValue('Test Connection')
    await wrapper.find('.host-input').setValue('localhost')
    
    expect(wrapper.vm.form.name).toBe('Test Connection')
    expect(wrapper.vm.form.host).toBe('localhost')
  })
})
