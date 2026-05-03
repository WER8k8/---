import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'
import NProgress from 'nprogress'
import 'nprogress/nprogress.css'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/pages/Login.vue'),
    meta: { title: '登录', requiresAuth: false }
  },
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    redirect: '/dashboard',
    meta: { requiresAuth: true },
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/pages/Dashboard.vue'),
        meta: { title: '数据看板' }
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/pages/Settings.vue'),
        meta: { title: '系统全局设置' }
      },
      {
        path: 'regions',
        name: 'Regions',
        component: () => import('@/pages/Regions.vue'),
        meta: { title: '全国地域词库管理' }
      },
      {
        path: 'keywords',
        name: 'Keywords',
        component: () => import('@/pages/Keywords.vue'),
        meta: { title: '行业关键词库与AI组词' }
      },
      {
        path: 'templates',
        name: 'Templates',
        component: () => import('@/pages/Templates.vue'),
        meta: { title: 'AI文案模板与全自动生成' }
      },
      {
        path: 'articles',
        name: 'Articles',
        component: () => import('@/pages/Articles.vue'),
        meta: { title: '文章管理' }
      },
      {
        path: 'platforms',
        name: 'Platforms',
        component: () => import('@/pages/Platforms.vue'),
        meta: { title: '多平台账号管理与AI分发中心' }
      },
      {
        path: 'publish-tasks',
        name: 'PublishTasks',
        component: () => import('@/pages/PublishTasks.vue'),
        meta: { title: '发布任务管理' }
      },
      {
        path: 'monitoring',
        name: 'Monitoring',
        component: () => import('@/pages/Monitoring.vue'),
        meta: { title: '发布记录、数据看板与收录监控' }
      },
      {
        path: 'logs',
        name: 'Logs',
        component: () => import('@/pages/Logs.vue'),
        meta: { title: '系统日志' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

NProgress.configure({ showSpinner: false })

router.beforeEach(async (to, from, next) => {
  NProgress.start()
  document.title = to.meta.title ? `${to.meta.title} - SEO矩阵管理系统` : 'SEO矩阵管理系统'
  
  const userStore = useUserStore()
  
  if (to.meta.requiresAuth !== false && !userStore.token) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
  } else if (to.name === 'Login' && userStore.token) {
    next({ path: '/' })
  } else {
    next()
  }
})

router.afterEach(() => {
  NProgress.done()
})

export default router
