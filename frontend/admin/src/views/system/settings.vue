<template>
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
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { SettingOutlined, PictureOutlined } from '@ant-design/icons-vue'

const router = useRouter()
const route = useRoute()

const currentSubMenu = ref('')

const navigateTo = (path: string) => {
  currentSubMenu.value = path || 'main'
  router.push(`/admin/settings${path ? '/' + path : ''}`)
}

onMounted(() => {
  const subPath = route.path.split('/').pop() || ''
  currentSubMenu.value = subPath || 'main'
})

watch(() => route.path, (newPath) => {
  const subPath = newPath.split('/').pop() || ''
  currentSubMenu.value = subPath || 'main'
})
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
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
