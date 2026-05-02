import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/login/Login.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/',
    name: 'Layout',
    component: () => import('@/layout/index.vue'),
    redirect: '/dashboard',
    meta: { requiresAuth: true },
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/index.vue'),
        meta: { title: '控制台', icon: 'DashboardOutlined' },
      },
      {
        path: 'products',
        name: 'Products',
        component: () => import('@/views/products/index.vue'),
        meta: { title: '产品管理', icon: 'PackageOutlined' },
      },
      {
        path: 'products/edit/:id',
        name: 'ProductEdit',
        component: () => import('@/views/products/edit.vue'),
        meta: { title: '编辑产品', hidden: true },
      },
      {
        path: 'products/categories',
        name: 'Categories',
        component: () => import('@/views/products/categories.vue'),
        meta: { title: '分类管理', icon: 'FolderOpenOutlined' },
      },
      {
        path: 'seo',
        name: 'SEO',
        component: () => import('@/views/seo/index.vue'),
        meta: { title: 'SEO概览', icon: 'SearchOutlined' },
      },
      {
        path: 'seo/llms-txt',
        name: 'LLMSTxt',
        component: () => import('@/views/seo/llms-txt.vue'),
        meta: { title: 'LLMs.txt生成', icon: 'FileTextOutlined' },
      },
      {
        path: 'seo/content-optimizer',
        name: 'ContentOptimizer',
        component: () => import('@/views/seo/content-optimizer.vue'),
        meta: { title: 'AI内容优化', icon: 'MagicOutlined' },
      },
      {
        path: 'seo/site-audit',
        name: 'SiteAudit',
        component: () => import('@/views/seo/site-audit.vue'),
        meta: { title: '站点审计', icon: 'AuditOutlined' },
      },
      {
        path: 'seo/batch-seo',
        name: 'BatchSEO',
        component: () => import('@/views/seo/batch-seo.vue'),
        meta: { title: '批量SEO管理', icon: 'CopyOutlined' },
      },
      {
        path: 'seo/schema-markup',
        name: 'SchemaMarkup',
        component: () => import('@/views/seo/schema-markup.vue'),
        meta: { title: 'Schema标记管理', icon: 'CodeOutlined' },
      },
      {
        path: 'seo/eeat',
        name: 'EEAT',
        component: () => import('@/views/seo/eeat.vue'),
        meta: { title: 'EEAT评分管理', icon: 'AwardOutlined' },
      },
      {
        path: 'seo/compliance',
        name: 'Compliance',
        component: () => import('@/views/seo/compliance.vue'),
        meta: { title: '广告法合规审查', icon: 'SafetyOutlined' },
      },
      {
        path: 'seo/keyword-ranking',
        name: 'KeywordRanking',
        component: () => import('@/views/seo/keyword-ranking.vue'),
        meta: { title: '关键词排名追踪', icon: 'RiseOutlined' },
      },
      {
        path: 'seo/performance',
        name: 'SEOPerformance',
        component: () => import('@/views/system/performance.vue'),
        meta: { title: '性能与安全监控', icon: 'DashboardOutlined' },
      },
      {
        path: 'content',
        name: 'Content',
        component: () => import('@/views/content/index.vue'),
        meta: { title: '内容管理', icon: 'FileOutlined' },
      },
      {
        path: 'content/edit/:id',
        name: 'ContentEdit',
        component: () => import('@/views/content/edit.vue'),
        meta: { title: '编辑内容', hidden: true },
      },
      {
        path: 'cases',
        name: 'Cases',
        component: () => import('@/views/cases/index.vue'),
        meta: { title: '案例管理', icon: 'PictureOutlined' },
      },
      {
        path: 'cases/edit/:id',
        name: 'CaseEdit',
        component: () => import('@/views/cases/edit.vue'),
        meta: { title: '编辑案例', hidden: true },
      },
      {
        path: 'inquiries',
        name: 'Inquiries',
        component: () => import('@/views/inquiries/index.vue'),
        meta: { title: '询盘管理', icon: 'MessageSquareOutlined' },
      },
      {
        path: 'users',
        name: 'Users',
        component: () => import('@/views/system/users.vue'),
        meta: { title: '用户管理', icon: 'UserOutlined' },
      },
      {
        path: 'analytics',
        name: 'Analytics',
        component: () => import('@/views/system/analytics.vue'),
        meta: { title: '数据分析', icon: 'BarChartOutlined' },
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/views/system/settings.vue'),
        meta: { title: '系统设置', icon: 'SettingOutlined' },
        children: [
          {
            path: '',
            name: 'SettingsMain',
            component: () => import('@/views/system/settings-main.vue'),
            meta: { title: '基本设置', icon: 'SettingOutlined' },
          },
          {
            path: 'drag-module',
            name: 'DragModule',
            component: () => import('@/views/system/drag-module.vue'),
            meta: { title: '自定义拖拽模块', icon: 'SettingOutlined' },
          },
          {
            path: 'effects',
            name: 'Effects',
            component: () => import('@/views/system/effects.vue'),
            meta: { title: '自定义特效组件', icon: 'PictureOutlined' },
          },
        ],
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, _from, next) => {
  const authStore = useAuthStore()
  const requiresAuth = to.meta.requiresAuth !== false
  
  if (requiresAuth && !authStore.isAuthenticated) {
    next('/login')
  } else if (!requiresAuth && authStore.isAuthenticated && to.path === '/login') {
    next('/dashboard')
  } else {
    next()
  }
})

export default router