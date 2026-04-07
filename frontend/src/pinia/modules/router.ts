import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useRouterStore = defineStore('router', () => {
  const cachedViews = ref<string[]>([])
  const loading = ref(false)

  const addCachedView = (view: string) => {
    if (cachedViews.value.includes(view)) {
      return
    }
    cachedViews.value.push(view)
  }

  const delCachedView = (view: string) => {
    cachedViews.value = cachedViews.value.filter((v) => v !== view)
  }

  const setLoading = (status: boolean) => {
    loading.value = status
  }

  return {
    cachedViews,
    loading,
    addCachedView,
    delCachedView,
    setLoading
  }
})
