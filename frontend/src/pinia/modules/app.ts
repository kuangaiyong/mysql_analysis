import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface AppConfig {
  side_mode: 'normal' | 'head' | 'combination' | 'sidebar'
  showTabs: boolean
  showWatermark: boolean
  primaryColor: string
  darkMode: 'auto' | 'dark' | 'light'
  transitionType: string
  layoutSideWidth: number
  layoutSideCollapsedWidth: number
}

export interface VisitedView {
  path: string
  meta?: {
    title?: string
    icon?: string
    hidden?: boolean
    affix?: boolean
  }
}

export const useAppStore = defineStore(
  'app',
  () => {
    const sideMode = ref<AppConfig['side_mode']>('normal')
    const showTabs = ref(true)
    const showWatermark = ref(false)
    const primaryColor = ref('#3b82f6')
    const darkMode = ref<AppConfig['darkMode']>('light')
    const transitionType = ref('fade-transform')
    const layoutSideWidth = ref(220)
    const layoutSideCollapsedWidth = ref(64)
    const layoutSideCollapsed = ref(false)
    const visitedViews = ref<VisitedView[]>([
      { path: '/dashboard', meta: { title: '仪表盘', affix: true } }
    ])

    const toggleDarkMode = () => {
      if (darkMode.value === 'light') {
        darkMode.value = 'dark'
        document.documentElement.classList.add('dark')
      } else {
        darkMode.value = 'light'
        document.documentElement.classList.remove('dark')
      }
    }

    const toggleSideMode = (mode: AppConfig['side_mode']) => {
      sideMode.value = mode
    }

    const toggleSideCollapsed = () => {
      layoutSideCollapsed.value = !layoutSideCollapsed.value
    }

    const addView = (view: VisitedView) => {
      const exist = visitedViews.value.some((v) => v.path === view.path)
      if (!exist) {
        visitedViews.value.push(view)
      }
    }

    const delView = (view: VisitedView) => {
      visitedViews.value = visitedViews.value.filter((v) => v.path !== view.path)
    }

    const delOthersViews = (view: VisitedView) => {
      visitedViews.value = visitedViews.value.filter(
        (v) => v.path === view.path || v.meta?.affix
      )
    }

    const delAllViews = () => {
      visitedViews.value = visitedViews.value.filter((v) => v.meta?.affix)
    }

    const setSideMode = (mode: AppConfig['side_mode']) => {
      sideMode.value = mode
    }

    const setPrimaryColor = (color: string) => {
      primaryColor.value = color
    }

    return {
      sideMode,
      showTabs,
      showWatermark,
      primaryColor,
      darkMode,
      transitionType,
      layoutSideWidth,
      layoutSideCollapsedWidth,
      layoutSideCollapsed,
      visitedViews,
      toggleDarkMode,
      toggleSideMode,
      toggleSideCollapsed,
      addView,
      delView,
      delOthersViews,
      delAllViews,
      setSideMode,
      setPrimaryColor
    }
  },
  {
    persist: {
      key: 'app-store',
      pick: ['darkMode', 'sideMode', 'primaryColor', 'showTabs']
    }
  }
)
