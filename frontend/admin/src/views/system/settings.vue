<template>
  <YdPage title="系统设置" subtitle="基本设置、拖拽模块与特效组件" surface="elevated">
    <div class="flex gap-6">
    <!-- 侧边导航 -->
    <div class="w-56 flex-shrink-0">
      <div class="bg-white rounded-xl border border-gray-100 p-2">
        <div class="text-xs font-medium text-gray-400 px-3 py-2">
          系统设置
        </div>
        <a-menu
          mode="inline"
          :selected-keys="[currentSubMenu]"
          class="border-none"
        >
          <a-menu-item
            key="main"
            @click="navigateTo('')"
          >
            <template #icon>
              <SettingOutlined class="w-4 h-4" />
            </template>
            基本设置
          </a-menu-item>
          <a-menu-item
            key="drag-module"
            @click="navigateTo('drag-module')"
          >
            <template #icon>
              <SettingOutlined class="w-4 h-4" />
            </template>
            自定义拖拽模块
          </a-menu-item>
          <a-menu-item
            key="effects"
            @click="navigateTo('effects')"
          >
            <template #icon>
              <PictureOutlined class="w-4 h-4" />
            </template>
            自定义特效组件
          </a-menu-item>
        </a-menu>
      </div>
    </div>

    <!-- 主内容区域 -->
    <div class="flex-1">
      <router-view v-slot="{ Component }">
        <transition
          name="fade"
          mode="out-in"
        >
          <component :is="Component" />
        </transition>
      </router-view>
    </div>
    </div>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { YdPage } from '@/components/youding';
import { useRouter, useRoute } from 'vue-router'
import { SettingOutlined, PictureOutlined } from '@ant-design/icons-vue'
import { apiGet } from '@/utils/api'

const router = useRouter()
const route = useRoute()
const currentSubMenu = ref('main')

function settingsSubKey(path: string): string {
  const p = path.replace(/\/$/, '')
  if (p === '/settings') return 'main'
  const rest = p.startsWith('/settings/') ? p.slice('/settings/'.length) : ''
  return rest.split('/')[0] || 'main'
}

const navigateTo = (path: string) => {
  currentSubMenu.value = path || 'main'
  router.push(`/settings${path ? '/' + path : ''}`)
}

onMounted(async () => {
  currentSubMenu.value = settingsSubKey(route.path)
  try { await apiGet('/settings') } catch { /* 空状态 */ }
})

watch(
  () => route.path,
  (newPath) => {
    currentSubMenu.value = settingsSubKey(newPath)
  },
)
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition:
    opacity 0.2s ease,
    transform 0.2s ease;
}
.fade-enter-from {
  opacity: 0;
  transform: translateX(10px);
}
.fade-leave-to {
  opacity: 0;
  transform: translateX(-10px);
}
</style>
