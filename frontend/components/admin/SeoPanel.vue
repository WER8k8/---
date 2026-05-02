<template>
  <div class="border-t border-gray-100 pt-6">
    <h3 class="text-lg font-semibold text-gray-900 mb-4">
      SEO 设置
    </h3>
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">SEO 标题 (meta title)</label>
        <input
          v-model="local.meta_title"
          maxlength="70"
          class="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:ring-2 focus:ring-brand-blue focus:border-transparent"
          placeholder="显示在浏览器标题栏和搜索结果中"
        >
        <p class="text-xs text-gray-400 mt-1">
          {{ local.meta_title?.length || 0 }}/70
        </p>
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">SEO 描述 (meta description)</label>
        <textarea
          v-model="local.meta_description"
          maxlength="160"
          rows="2"
          class="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:ring-2 focus:ring-brand-blue focus:border-transparent"
          placeholder="显示在搜索结果摘要中"
        />
        <p class="text-xs text-gray-400 mt-1">
          {{ local.meta_description?.length || 0 }}/160
        </p>
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">关键词 (meta keywords)</label>
        <input
          v-model="local.meta_keywords"
          class="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:ring-2 focus:ring-brand-blue focus:border-transparent"
          placeholder="岩棉板,保温材料,厂家直供"
        >
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">H1 标签</label>
        <input
          v-model="local.h1_tag"
          class="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:ring-2 focus:ring-brand-blue focus:border-transparent"
          placeholder="页面主标题 (H1)"
        >
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Open Graph 标题</label>
        <input
          v-model="local.og_title"
          class="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:ring-2 focus:ring-brand-blue focus:border-transparent"
          placeholder="分享到社交网络时显示的标题"
        >
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Open Graph 描述</label>
        <textarea
          v-model="local.og_description"
          rows="2"
          class="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:ring-2 focus:ring-brand-blue focus:border-transparent"
          placeholder="分享到社交网络时显示的描述"
        />
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Open Graph 图片</label>
        <input
          v-model="local.og_image"
          class="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:ring-2 focus:ring-brand-blue focus:border-transparent"
          placeholder="https://example.com/image.jpg"
        >
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Canonical URL</label>
        <input
          v-model="local.canonical_url"
          class="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:ring-2 focus:ring-brand-blue focus:border-transparent"
          placeholder="规范URL，防止重复内容"
        >
      </div>
      <div class="flex items-center space-x-6">
        <label class="flex items-center space-x-2 cursor-pointer">
          <input
            v-model="local.noindex"
            type="checkbox"
            class="rounded border-gray-300 text-brand-blue focus:ring-brand-blue"
          >
          <span class="text-sm text-gray-700">禁止索引 (noindex)</span>
        </label>
        <div class="text-xs text-gray-400">
          <span
            v-if="!local.noindex"
            class="text-green-600"
          >✓ 允许搜索引擎索引</span>
          <span
            v-else
            class="text-red-500"
          >✗ 将禁止搜索引擎收录此页面</span>
        </div>
      </div>
    </div>
    <div
      v-if="local.meta_title || local.meta_description"
      class="mt-4 p-4 bg-gray-50 rounded-lg border border-gray-200"
    >
      <p class="text-xs font-medium text-gray-500 mb-2">
        搜索结果预览
      </p>
      <p class="text-sm text-blue-700 font-medium truncate">
        {{ local.meta_title || '页面标题' }}
      </p>
      <p class="text-xs text-gray-600 mt-1 line-clamp-2">
        {{ local.meta_description || '页面描述将显示在这里，建议包含关键词和吸引点击的内容。' }}
      </p>
      <p class="text-xs text-green-700 mt-0.5">
        {{ previewUrl }}
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, computed, watch } from 'vue'

export interface SeoData {
  meta_title: string
  meta_description: string
  meta_keywords: string
  canonical_url: string
  og_title: string
  og_description: string
  og_image: string
  h1_tag: string
  noindex: boolean
}

const props = defineProps<{
  modelValue: SeoData
  slug?: string
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: SeoData): void
}>()

const local = reactive({
  meta_title: props.modelValue.meta_title || '',
  meta_description: props.modelValue.meta_description || '',
  meta_keywords: props.modelValue.meta_keywords || '',
  canonical_url: props.modelValue.canonical_url || '',
  og_title: props.modelValue.og_title || '',
  og_description: props.modelValue.og_description || '',
  og_image: props.modelValue.og_image || '',
  h1_tag: props.modelValue.h1_tag || '',
  noindex: props.modelValue.noindex || false,
})

const previewUrl = computed(() => {
  if (props.slug) {
    return `https://youding.com/${props.slug}`
  }
  return 'https://youding.com/page-url'
})

watch(local, () => {
  emit('update:modelValue', { ...local })
}, { deep: true })
</script>
