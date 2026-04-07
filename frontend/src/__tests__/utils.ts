import { mount, shallowMount } from '@vue/test-utils'
import type { Component } from 'vue'

/**
 * 挂载组件的封装函数
 * @param component 要测试的 Vue 组件
 * @param options 额外的挂载选项
 * @returns 挂载的组件包装器
 */
export function mountComponent(component: Component, options = {}) {
  return mount(component, {
    ...options
  })
}

/**
 * 浅挂载组件（不渲染子组件）
 * @param component 要测试的 Vue 组件
 * @param options 额外的挂载选项
 * @returns 挂载的组件包装器
 */
export function shallowMountComponent(component: Component, options = {}) {
  return shallowMount(component, {
    ...options
  })
}

/**
 * 模拟 API 响应
 * @param data 响应数据
 * @param delay 延迟时间（毫秒）
 * @returns Promise
 */
export function mockApiResponse<T>(data: T, delay = 0): Promise<T> {
  return new Promise((resolve) => {
    setTimeout(() => resolve(data), delay)
  })
}

/**
 * 模拟 API 错误
 * @param message 错误消息
 * @param status HTTP 状态码
 * @returns Promise<never>
 */
export function mockApiError(message: string, status = 500): Promise<never> {
  return Promise.reject({
    response: {
      data: { detail: message },
      status
    },
    message
  })
}

/**
 * 等待指定时间
 * @param ms 毫秒数
 * @returns Promise
 */
export function wait(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms))
}

/**
 * 等待下一个 tick
 * @returns Promise
 */
export function nextTick(): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, 0))
}
