import { config } from '@vue/test-utils'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

// 全局配置 Vue Test Utils
config.global.plugins = [createPinia(), ElementPlus]

// 注册所有 Element Plus 图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  config.global.components[key] = component
}

// 全局 mock 配置
config.global.mocks = {
  $t: (msg: string) => msg,
  $route: {
    params: {},
    query: {}
  },
  $router: {
    push: () => Promise.resolve(),
    replace: () => Promise.resolve()
  }
}

// 全局 stubs
config.global.stubs = {
  'router-link': true,
  'router-view': true
}
