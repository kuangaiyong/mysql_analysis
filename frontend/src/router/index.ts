import { createRouter, createWebHashHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import Layout from '@/view/layout/index.vue'
import { isAuthenticated } from '@/types/auth'
import { useAppStore } from '@/pinia/modules/app'

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
      },
      {
        path: '/index-advisor',
        name: 'IndexAdvisor',
        component: () => import('@/view/indexAdvisor/index.vue'),
        meta: { title: 'AI 索引顾问', icon: 'Grid' }
      },
      {
        path: '/lock-analysis',
        name: 'LockAnalysis',
        component: () => import('@/view/lockAnalysis/index.vue'),
        meta: { title: 'AI 锁分析', icon: 'Lock' }
      },
      {
        path: '/slow-query-patrol',
        name: 'SlowQueryPatrol',
        component: () => import('@/view/slowQueryPatrol/index.vue'),
        meta: { title: 'AI 慢查询巡检', icon: 'Timer' }
      },
      {
        path: '/config-tuning',
        name: 'ConfigTuning',
        component: () => import('@/view/configTuning/index.vue'),
        meta: { title: 'AI 配置调优', icon: 'SetUp' }
      },
      {
        path: '/capacity-prediction',
        name: 'CapacityPrediction',
        component: () => import('@/view/capacityPrediction/index.vue'),
        meta: { title: 'AI 容量预测', icon: 'TrendCharts' }
      },
      {
        path: '/task-center',
        name: 'TaskCenter',
        component: () => import('@/view/taskCenter/index.vue'),
        meta: { title: '任务中心', icon: 'List' }
      },
      {
        path: '/task-detail/:id',
        name: 'TaskDetail',
        component: () => import('@/view/taskCenter/detail.vue'),
        meta: { title: '任务详情', icon: 'Document' }
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

router.afterEach((to) => {
  if (to.path !== '/login' && to.meta.title) {
    const appStore = useAppStore()
    appStore.addView({
      path: to.path,
      meta: { title: to.meta.title as string, icon: to.meta.icon as string }
    })
  }
})

export default router
