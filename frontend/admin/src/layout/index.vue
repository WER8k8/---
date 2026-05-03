<template>
  <div class="flex h-screen bg-gray-50">
    <aside
      class="bg-white border-r border-gray-200 flex flex-col fixed left-0 top-0 h-full z-10 transition-all duration-300 ease-in-out"
      :class="collapsed ? 'w-16' : 'w-64'"
    >
      <div class="p-4 border-b border-gray-100 flex items-center justify-between">
        <div
          v-if="!collapsed"
          class="flex items-center"
        >
          <div class="w-10 h-10 bg-gradient-to-br from-primary-500 to-primary-600 rounded-xl flex items-center justify-center mr-3">
            <svg
              class="w-5 h-5 text-white"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M13 10V3L4 14h7v7l9-11h-7z"
              />
            </svg>
          </div>
          <h1 class="text-lg font-bold text-primary-600">
            优丁管理后台
          </h1>
        </div>
        <div
          v-else
          class="w-full flex justify-center"
        >
          <div class="w-10 h-10 bg-gradient-to-br from-primary-500 to-primary-600 rounded-xl flex items-center justify-center">
            <svg
              class="w-5 h-5 text-white"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M13 10V3L4 14h7v7l9-11h-7z"
              />
            </svg>
          </div>
        </div>
        <button
          v-if="!collapsed"
          class="p-2 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
          @click="collapsed = true"
        >
          <svg
            class="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M15 19l-7-7 7-7"
            />
          </svg>
        </button>
      </div>
      
      <button
        v-if="collapsed"
        class="absolute right-0 top-4 transform translate-x-1/2 p-1 bg-white border border-gray-200 rounded-full shadow-md hover:bg-gray-50 transition-all hover:scale-110"
        @click="collapsed = false"
      >
        <svg
          class="w-4 h-4 text-gray-600"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M9 5l7 7-7 7"
          />
        </svg>
      </button>

      <nav class="flex-1 p-3 overflow-y-auto">
        <div
          v-for="(item, index) in menuItems"
          :key="index"
          class="mb-3"
        >
          <div
            v-if="item.title && !collapsed"
            class="text-xs font-semibold text-gray-400 uppercase tracking-wider px-3 py-2 mt-2"
          >
            {{ item.title }}
          </div>
          <div class="space-y-1">
            <div
              v-for="child in item.children"
              :key="child.name"
              class="relative"
            >
              <template v-if="child.children && child.children.length > 0">
                <button
                  class="w-full flex items-center px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 mb-1 group"
                  :class="currentPath.startsWith(child.path)
                    ? 'bg-primary-500 text-white shadow-lg shadow-primary-500/30' 
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'"
                  @click="handleNavClick(child.path); toggleSubMenu(child.name)"
                >
                  <component
                    :is="getIcon(child.icon)"
                    class="w-5 h-5 flex-shrink-0 transition-transform duration-200"
                    :class="currentPath.startsWith(child.path) ? 'scale-110' : 'group-hover:scale-105'"
                  />
                  <span
                    v-if="!collapsed"
                    class="ml-3 overflow-hidden transition-all duration-200"
                  >
                    {{ child.title }}
                  </span>
                  <svg
                    v-if="!collapsed"
                    class="ml-auto w-4 h-4 text-gray-400 transition-transform duration-200"
                    :class="{ 'rotate-90': expandedSubMenus.includes(child.name) }"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M9 5l7 7-7 7"
                    />
                  </svg>
                </button>
                <transition name="collapse">
                  <div
                    v-if="expandedSubMenus.includes(child.name)"
                    class="ml-4 space-y-1 pl-2 border-l border-gray-100"
                  >
                    <button
                      v-for="subChild in child.children"
                      :key="subChild.name"
                      class="w-full flex items-center px-3 py-2 rounded-lg text-sm transition-all duration-200"
                      :class="currentPath === subChild.path
                        ? 'bg-primary-50 text-primary-600 font-medium'
                        : 'text-gray-500 hover:bg-gray-50 hover:text-gray-700'"
                      @click="handleNavClick(subChild.path)"
                    >
                      <component
                        :is="getIcon(subChild.icon)"
                        class="w-4 h-4 flex-shrink-0"
                      />
                      <span class="ml-2">{{ subChild.title }}</span>
                    </button>
                  </div>
                </transition>
              </template>
              <template v-else>
                <button
                  class="w-full flex items-center px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 mb-1 group"
                  :class="currentPath === child.path
                    ? 'bg-primary-500 text-white shadow-lg shadow-primary-500/30' 
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'"
                  @click="handleNavClick(child.path)"
                >
                  <component
                    :is="getIcon(child.icon)"
                    class="w-5 h-5 flex-shrink-0 transition-transform duration-200"
                    :class="currentPath === child.path ? 'scale-110' : 'group-hover:scale-105'"
                  />
                  <span
                    v-if="!collapsed"
                    class="ml-3 overflow-hidden transition-all duration-200"
                  >
                    {{ child.title }}
                  </span>
                  <span
                    v-if="currentPath === child.path && !collapsed"
                    class="ml-auto w-1.5 h-1.5 rounded-full bg-white/80"
                  />
                </button>
                <div
                  v-if="collapsed"
                  class="absolute left-full ml-2 px-3 py-2 bg-gray-900 text-white text-sm rounded-lg shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 whitespace-nowrap z-50"
                >
                  {{ child.title }}
                </div>
              </template>
            </div>
          </div>
        </div>
      </nav>

      <div class="p-3 border-t border-gray-100">
        <button
          class="w-full flex items-center px-3 py-2.5 rounded-lg text-sm font-medium text-gray-600 hover:bg-red-50 hover:text-red-600 transition-all duration-200"
          @click="handleLogout"
        >
          <LogoutOutlined class="w-5 h-5 flex-shrink-0" />
          <span
            v-if="!collapsed"
            class="ml-3"
          >退出登录</span>
        </button>
      </div>
    </aside>

    <main
      class="flex-1 transition-all duration-300"
      :class="collapsed ? 'ml-16' : 'ml-64'"
    >
      <header class="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between sticky top-0 z-10">
        <h2 class="text-xl font-semibold text-gray-800">
          {{ currentPageTitle }}
        </h2>
        <div class="flex items-center space-x-4">
          <span class="text-sm text-gray-500">{{ auth.username }}</span>
        </div>
      </header>
      <div class="p-6">
        <router-view />
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  DashboardOutlined,
  PauseOutlined,
  FolderOpenOutlined,
  SearchOutlined,
  FileTextOutlined,
  MailOutlined,
  AuditOutlined,
  CopyOutlined,
  FileOutlined,
  PictureOutlined,
  MessageOutlined,
  UserOutlined,
  BarChartOutlined,
  SettingOutlined,
  LogoutOutlined,
} from '@ant-design/icons-vue'
import { useAuthStore } from '@/stores/auth'

const collapsed = ref(false)

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const currentPath = computed(() => route.path)

const expandedSubMenus = ref<string[]>([])

function toggleSubMenu(name: string) {
  const index = expandedSubMenus.value.indexOf(name)
  if (index > -1) {
    expandedSubMenus.value.splice(index, 1)
  } else {
    expandedSubMenus.value.push(name)
  }
}

const iconMap: Record<string, any> = {
  DashboardOutlined,
  PauseOutlined,
  FolderOpenOutlined,
  SearchOutlined,
  FileTextOutlined,
  MailOutlined,
  AuditOutlined,
  CopyOutlined,
  FileOutlined,
  PictureOutlined,
  MessageOutlined,
  UserOutlined,
  BarChartOutlined,
  SettingOutlined,
}

function getIcon(iconName: string) {
  return iconMap[iconName] || DashboardOutlined
}

const menuItems = [
  {
    title: '控制台',
    children: [
      { name: 'Dashboard', path: '/dashboard', title: '数据概览', icon: 'DashboardOutlined' },
    ],
  },
  {
    title: '产品管理',
    children: [
      { name: 'Products', path: '/products', title: '产品列表', icon: 'PauseOutlined' },
      { name: 'Categories', path: '/products/categories', title: '分类管理', icon: 'FolderOpenOutlined' },
    ],
  },
  {
    title: 'SEO优化',
    children: [
      { name: 'SEO', path: '/seo', title: 'SEO概览', icon: 'SearchOutlined' },
      { name: 'BatchSEO', path: '/seo/batch-seo', title: '批量SEO管理', icon: 'CopyOutlined' },
      { name: 'ContentOptimizer', path: '/seo/content-optimizer', title: 'AI内容优化', icon: 'MailOutlined' },
      { name: 'LLMSTxt', path: '/seo/llms-txt', title: 'LLMs.txt生成', icon: 'FileTextOutlined' },
      { name: 'SiteAudit', path: '/seo/site-audit', title: '站点审计', icon: 'AuditOutlined' },
    ],
  },
  {
    title: '内容管理',
    children: [
      { name: 'Content', path: '/content', title: '内容列表', icon: 'FileOutlined' },
      { name: 'Cases', path: '/cases', title: '案例管理', icon: 'PictureOutlined' },
    ],
  },
  {
    title: '营销获客',
    children: [
      { name: 'Inquiries', path: '/inquiries', title: '询盘管理', icon: 'MessageOutlined' },
    ],
  },
  {
    title: '系统管理',
    children: [
      { name: 'Users', path: '/users', title: '用户管理', icon: 'UserOutlined' },
      { name: 'Analytics', path: '/analytics', title: '数据分析', icon: 'BarChartOutlined' },
      { 
        name: 'Settings', 
        path: '/settings', 
        title: '系统设置', 
        icon: 'SettingOutlined',
        children: [
          { name: 'SettingsMain', path: '/settings', title: '基本设置', icon: 'SettingOutlined' },
          { name: 'DragModule', path: '/settings/drag-module', title: '自定义拖拽模块', icon: 'SettingOutlined' },
          { name: 'Effects', path: '/settings/effects', title: '自定义特效组件', icon: 'PictureOutlined' },
        ]
      },
    ],
  },
]

const currentPageTitle = computed(() => {
  for (const item of menuItems) {
    for (const child of item.children) {
      if (child.children) {
        for (const subChild of child.children) {
          if (currentPath.value === subChild.path) {
            return subChild.title
          }
        }
      }
      if (currentPath.value === child.path || currentPath.value.startsWith(child.path)) {
        return child.title
      }
    }
  }
  return '控制台'
})

function handleNavClick(path: string) {
  router.push(path)
}

function handleLogout() {
  auth.logout()
  router.push('/login')
}
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.fade-enter-from {
  opacity: 0;
  transform: translateX(20px);
}

.fade-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}

.collapse-enter-active,
.collapse-leave-active {
  transition: all 0.2s ease-out;
  overflow: hidden;
}

.collapse-enter-from,
.collapse-leave-to {
  opacity: 0;
  max-height: 0;
}

.collapse-enter-to,
.collapse-leave-from {
  max-height: 200px;
}

::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: #a1a1a1;
}
</style>
