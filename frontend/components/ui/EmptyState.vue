<template>
  <div class="flex flex-col items-center justify-center py-12 px-6 text-center">
    <div class="text-5xl mb-4 opacity-50">{{ icon }}</div>
    <p class="text-lg font-semibold text-gray-900 mb-2">{{ title }}</p>
    <p v-if="description" class="text-sm text-gray-400 leading-relaxed max-w-[280px]">{{ description }}</p>
    <slot />
  </div>
</template>

<script setup lang="ts">
withDefaults(defineProps<{
  icon?: string
  title?: string
  description?: string
}>(), {
  icon: '📋',
  title: '暂无数据',
  description: ''
})
</script>
