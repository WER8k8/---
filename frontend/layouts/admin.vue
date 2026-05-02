<template>
  <div class="min-h-screen bg-gray-100 flex">
    <aside class="w-64 bg-white shadow-sm border-r border-gray-200 flex flex-col">
      <div class="p-6 border-b border-gray-100">
        <NuxtLink
          to="/admin"
          class="text-lg font-bold text-brand-blue"
        >
          优丁管理后台
        </NuxtLink>
      </div>
      <nav class="flex-1 p-4 space-y-1 overflow-y-auto">
        <div class="text-xs font-semibold text-gray-400 uppercase tracking-wider px-4 pt-2 pb-1">
          SEO 优化
        </div>
        <NuxtLink
          to="/admin/seo"
          class="block px-4 py-2.5 rounded-lg text-sm font-medium transition-colors"
          :class="route.path === '/admin/seo' ? 'bg-brand-blue text-white' : 'text-gray-600 hover:bg-gray-50'"
        >
          SEO 概览
        </NuxtLink>
        <NuxtLink
          to="/admin/seo/batch-seo"
          class="block px-4 py-2.5 rounded-lg text-sm font-medium transition-colors"
          :class="route.path.startsWith('/admin/seo/batch-seo') ? 'bg-brand-blue text-white' : 'text-gray-600 hover:bg-gray-50'"
        >
          SEO 批量管理
        </NuxtLink>
        <NuxtLink
          to="/admin/seo/ai-optimize"
          class="block px-4 py-2.5 rounded-lg text-sm font-medium transition-colors"
          :class="route.path.startsWith('/admin/seo/ai-optimize') ? 'bg-brand-blue text-white' : 'text-gray-600 hover:bg-gray-50'"
        >
          AI 内容优化
        </NuxtLink>
        <NuxtLink
          to="/admin/seo/llms-txt"
          class="block px-4 py-2.5 rounded-lg text-sm font-medium transition-colors"
          :class="route.path.startsWith('/admin/seo/llms-txt') ? 'bg-brand-blue text-white' : 'text-gray-600 hover:bg-gray-50'"
        >
          LLMs.txt 生成
        </NuxtLink>
        <NuxtLink
          to="/admin/seo/site-audit"
          class="block px-4 py-2.5 rounded-lg text-sm font-medium transition-colors"
          :class="route.path.startsWith('/admin/seo/site-audit') ? 'bg-brand-blue text-white' : 'text-gray-600 hover:bg-gray-50'"
        >
          站点审计
        </NuxtLink>
        <NuxtLink
          to="/admin/ranking"
          class="block px-4 py-2.5 rounded-lg text-sm font-medium transition-colors"
          :class="route.path.startsWith('/admin/ranking') ? 'bg-brand-blue text-white' : 'text-gray-600 hover:bg-gray-50'"
        >
          关键词排名
        </NuxtLink>

        <div class="text-xs font-semibold text-gray-400 uppercase tracking-wider px-4 pt-4 pb-1">
          内容管理
        </div>
        <NuxtLink
          to="/admin/content"
          class="block px-4 py-2.5 rounded-lg text-sm font-medium transition-colors"
          :class="route.path === '/admin/content' ? 'bg-brand-blue text-white' : 'text-gray-600 hover:bg-gray-50'"
        >
          内容列表
        </NuxtLink>
        <NuxtLink
          to="/admin/cases"
          class="block px-4 py-2.5 rounded-lg text-sm font-medium transition-colors"
          :class="route.path.startsWith('/admin/cases') ? 'bg-brand-blue text-white' : 'text-gray-600 hover:bg-gray-50'"
        >
          案例中心
        </NuxtLink>

        <div class="text-xs font-semibold text-gray-400 uppercase tracking-wider px-4 pt-4 pb-1">
          营销获客
        </div>
        <NuxtLink
          to="/admin/inquiries"
          class="block px-4 py-2.5 rounded-lg text-sm font-medium transition-colors"
          :class="route.path.startsWith('/admin/inquiries') ? 'bg-brand-blue text-white' : 'text-gray-600 hover:bg-gray-50'"
        >
          询盘管理
        </NuxtLink>

        <div class="text-xs font-semibold text-gray-400 uppercase tracking-wider px-4 pt-4 pb-1">
          产品管理
        </div>
        <NuxtLink
          to="/admin/products"
          class="block px-4 py-2.5 rounded-lg text-sm font-medium transition-colors"
          :class="route.path.startsWith('/admin/products') && !route.path.includes('/categories') ? 'bg-brand-blue text-white' : 'text-gray-600 hover:bg-gray-50'"
        >
          产品列表
        </NuxtLink>
        <NuxtLink
          to="/admin/products/categories"
          class="block px-4 py-2.5 rounded-lg text-sm font-medium transition-colors"
          :class="route.path.includes('/categories') ? 'bg-brand-blue text-white' : 'text-gray-600 hover:bg-gray-50'"
        >
          分类管理
        </NuxtLink>

        <div class="text-xs font-semibold text-gray-400 uppercase tracking-wider px-4 pt-4 pb-1">
          系统管理
        </div>
        <NuxtLink
          to="/admin/users"
          class="block px-4 py-2.5 rounded-lg text-sm font-medium transition-colors"
          :class="route.path.startsWith('/admin/users') ? 'bg-brand-blue text-white' : 'text-gray-600 hover:bg-gray-50'"
        >
          用户管理
        </NuxtLink>
        <NuxtLink
          to="/admin/analytics"
          class="block px-4 py-2.5 rounded-lg text-sm font-medium transition-colors"
          :class="route.path.startsWith('/admin/analytics') ? 'bg-brand-blue text-white' : 'text-gray-600 hover:bg-gray-50'"
        >
          数据分析
        </NuxtLink>
        <NuxtLink
          to="/admin/settings"
          class="block px-4 py-2.5 rounded-lg text-sm font-medium transition-colors"
          :class="route.path.startsWith('/admin/settings') ? 'bg-brand-blue text-white' : 'text-gray-600 hover:bg-gray-50'"
        >
          系统设置
        </NuxtLink>
      </nav>
      <div class="p-4 border-t border-gray-100 space-y-2">
        <ClientOnly>
          <div
            v-if="currentUser"
            class="px-4 py-2 text-sm text-gray-500"
          >
            {{ currentUser }}
          </div>
        </ClientOnly>
        <button
          class="w-full text-left px-4 py-2.5 rounded-lg text-sm text-gray-500 hover:bg-gray-50 transition-colors"
          @click="handleLogout"
        >
          退出登录 →
        </button>
        <NuxtLink
          to="/"
          class="block px-4 py-2.5 rounded-lg text-sm text-gray-500 hover:bg-gray-50 transition-colors"
        >
          ← 返回网站
        </NuxtLink>
      </div>
    </aside>
    <main class="flex-1 p-8">
      <slot />
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { navigateTo } from '#app'
import { useAuthStore } from '~/stores/auth'

const route = useRoute()
const auth = useAuthStore()
const currentUser = ref<string | null>(null)
const isChecking = ref(true)

const skipAuthPaths = ['/admin/login']

async function checkAuth() {
  isChecking.value = true
  await new Promise(resolve => setTimeout(resolve, 100))
  
  if (skipAuthPaths.includes(route.path)) {
    isChecking.value = false
    return
  }
  
  if (!auth.isAuthenticated) {
    navigateTo('/admin/login')
    return
  }
  
  currentUser.value = auth.username || '管理员'
  isChecking.value = false
}

onMounted(() => {
  checkAuth()
})

watch(() => route.path, () => {
  checkAuth()
})

function handleLogout() {
  auth.logout()
  navigateTo('/admin/login')
}
</script>
