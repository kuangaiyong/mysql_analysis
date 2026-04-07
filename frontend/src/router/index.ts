import { createRouter, createWebHashHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import Layout from '@/view/layout/index.vue'
import { isAuthenticated } from '@/types/auth'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/view/login/index.vue'),
    meta: { title: '登录', requiresAuth: false }
  },
  {
    path: '/',
    component: Layout,
    redirect: '/ai-diagnostic',
    children: [
      {
        path: '/connections',
        name: 'Connections',
        component: () => import('@/view/connections/index.vue'),
        meta: { title: '连接管理', icon: 'Connection' }
      },
      {
        path: '/ai-diagnostic',
        name: 'AIDiagnostic',
        component: () => import('@/view/aiDiagnostic/index.vue'),
        meta: { title: 'AI 诊断', icon: 'ChatDotRound' }
      },
      {
        path: '/sql-optimizer',
        name: 'SQLOptimizer',
        component: () => import('@/view/sqlOptimizer/index.vue'),
        meta: { title: 'AI SQL 优化', icon: 'Edit' }
      },
      {
        path: '/explain-interpret',
        name: 'ExplainInterpret',
        component: () => import('@/view/explainInterpret/index.vue'),
        meta: { title: 'AI EXPLAIN 解读', icon: 'DocumentCopy' }
      },
      {
        path: '/health-report',
        name: 'HealthReport',
        component: () => import('@/view/healthReport/index.vue'),
        meta: { title: '健康巡检报告', icon: 'Document' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

router.beforeEach((to, _from, next) => {
  const requiresAuth = to.meta.requiresAuth !== false
  
  if (requiresAuth && !isAuthenticated()) {
    next('/login')
  } else if (to.path === '/login' && isAuthenticated()) {
    next('/ai-diagnostic')
  } else {
    next()
  }
})

export default router
