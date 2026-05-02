<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-gray-900">
        {{ isNew ? '新建内容' : '编辑内容' }}
      </h1>
      <NuxtLink
        to="/admin/content"
        class="text-sm text-gray-500 hover:text-gray-700 transition-colors"
      >
        ← 返回列表
      </NuxtLink>
    </div>
    <div class="bg-white rounded-xl shadow-sm p-6 space-y-6">
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">页面标题</label>
          <input
            v-model="form.title"
            class="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:ring-2 focus:ring-brand-blue focus:border-transparent"
            placeholder="输入页面标题"
          >
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">URL别名 (slug)</label>
          <div class="flex items-center space-x-2">
            <span class="text-sm text-gray-400">/</span>
            <input
              v-model="form.slug"
              class="flex-1 border border-gray-300 rounded-lg px-4 py-2.5 focus:ring-2 focus:ring-brand-blue focus:border-transparent"
              placeholder="page-url-alias"
            >
          </div>
        </div>
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">摘要</label>
        <input
          v-model="form.summary"
          class="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:ring-2 focus:ring-brand-blue focus:border-transparent"
          placeholder="页面摘要，用于列表展示"
        >
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">页面类型</label>
        <select
          v-model="form.page_type"
          class="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:ring-2 focus:ring-brand-blue focus:border-transparent"
        >
          <option value="page">
            普通页面
          </option>
          <option value="news">
            新闻文章
          </option>
          <option value="product">
            产品页面
          </option>
        </select>
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">正文内容（支持富文本）</label>
        <RichTextEditor
          v-model="form.content"
          placeholder="在此编写页面内容..."
        />
      </div>
      <div class="border-t border-gray-100 pt-6">
        <h3 class="text-lg font-semibold text-gray-900 mb-4">
          SEO 设置
        </h3>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">SEO 标题 (meta title)</label>
            <input
              v-model="seo.meta_title"
              maxlength="70"
              class="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:ring-2 focus:ring-brand-blue focus:border-transparent"
              placeholder="显示在浏览器标题栏和搜索结果中"
            >
            <p class="text-xs text-gray-400 mt-1">
              {{ seo.meta_title?.length || 0 }}/70
            </p>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">SEO 描述 (meta description)</label>
            <textarea
              v-model="seo.meta_description"
              maxlength="160"
              rows="2"
              class="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:ring-2 focus:ring-brand-blue focus:border-transparent"
              placeholder="显示在搜索结果摘要中"
            />
            <p class="text-xs text-gray-400 mt-1">
              {{ seo.meta_description?.length || 0 }}/160
            </p>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">关键词 (meta keywords)</label>
            <input
              v-model="seo.meta_keywords"
              class="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:ring-2 focus:ring-brand-blue focus:border-transparent"
              placeholder="轻集料混凝土,陶粒混凝土"
            >
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">H1 标签</label>
            <input
              v-model="seo.h1_tag"
              class="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:ring-2 focus:ring-brand-blue focus:border-transparent"
              placeholder="页面主标题 (H1)"
            >
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Open Graph 图片</label>
            <input
              v-model="seo.og_image"
              class="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:ring-2 focus:ring-brand-blue focus:border-transparent"
              placeholder="https://example.com/image.jpg"
            >
          </div>
          <div class="flex items-center">
            <label class="flex items-center space-x-2 cursor-pointer">
              <input
                v-model="seo.noindex"
                type="checkbox"
                class="rounded border-gray-300 text-brand-blue focus:ring-brand-blue"
              >
              <span class="text-sm text-gray-700">禁止搜索引擎索引 (noindex)</span>
            </label>
          </div>
        </div>
      </div>
      <div
        v-if="saveError"
        class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm"
      >
        {{ saveError }}
      </div>
      <div class="flex items-center space-x-4 pt-4 border-t border-gray-100">
        <button
          :disabled="saving"
          class="px-6 py-2.5 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 disabled:opacity-50 transition-colors"
          @click="handleSave(false)"
        >
          {{ saving ? '保存中...' : '保存草稿' }}
        </button>
        <button
          :disabled="saving"
          class="px-6 py-2.5 bg-brand-blue text-white rounded-lg hover:bg-blue-800 disabled:opacity-50 transition-colors"
          @click="handleSave(true)"
        >
          {{ saving ? '发布中...' : '发布' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, navigateTo } from '#app'
import RichTextEditor from '~/components/admin/RichTextEditor.vue'

definePageMeta({ layout: 'admin' })

const route = useRoute()
const isNew = ref(true)
const saving = ref(false)
const saveError = ref<string | null>(null)

const form = ref({
  title: '',
  slug: '',
  summary: '',
  content: '',
  page_type: 'page',
})

const seo = ref({
  meta_title: '',
  meta_description: '',
  meta_keywords: '',
  h1_tag: '',
  og_image: '',
  noindex: false,
})

onMounted(async () => {
  const id = route.params.id
  if (id && id !== 'new') {
    isNew.value = false
    try {
      const token = localStorage.getItem('admin_token')
      const res = await fetch(`/api/v1/content/pages/${id}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (res.ok) {
        const data = await res.json()
        form.value = {
          title: data.title,
          slug: data.slug,
          summary: data.summary || '',
          content: data.content || '',
          page_type: data.page_type || 'page',
        }
        try {
          const seoRes = await fetch(`/api/v1/content/seo/page/${id}`, {
            headers: { 'Authorization': `Bearer ${token}` }
          })
          if (seoRes.ok) {
            const seoData = await seoRes.json()
            seo.value = {
              meta_title: seoData.meta_title || '',
              meta_description: seoData.meta_description || '',
              meta_keywords: seoData.meta_keywords || '',
              h1_tag: seoData.h1_tag || '',
              og_image: seoData.og_image || '',
              noindex: seoData.noindex || false,
            }
          }
        } catch (_e) {}
      }
    } catch (e: any) {
      saveError.value = '加载页面失败: ' + e.message
    }
  } else {
    form.value.slug = generateSlug()
  }
})

function generateSlug() {
  return 'page-' + Date.now().toString(36)
}

async function handleSave(publish: boolean) {
  saving.value = true
  saveError.value = null
  try {
    const token = localStorage.getItem('admin_token')
    const id = route.params.id

    if (isNew.value || id === 'new') {
      const res = await fetch('/api/v1/content/pages', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...form.value,
          status: publish ? 'published' : 'draft',
        }),
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || '保存失败')
      }
      const page = await res.json()
      await saveSeo(token, page.id)
      await navigateTo('/admin/content')
    } else {
      const res = await fetch(`/api/v1/content/pages/${id}`, {
        method: 'PUT',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...form.value,
          status: publish ? 'published' : undefined,
        }),
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || '保存失败')
      }
      await saveSeo(token, id as string)
      await navigateTo('/admin/content')
    }
  } catch (e: any) {
    saveError.value = e.message
  } finally {
    saving.value = false
  }
}

async function saveSeo(token: string, pageId: string) {
  const hasSeoFields = seo.value.meta_title || seo.value.meta_description || seo.value.meta_keywords
  if (!hasSeoFields) return

  try {
    const existingRes = await fetch(`/api/v1/content/seo/page/${pageId}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (existingRes.ok) {
      await fetch(`/api/v1/content/seo/page/${pageId}`, {
        method: 'PUT',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(seo.value),
      })
    } else {
      await fetch('/api/v1/content/seo', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          resource_type: 'page',
          resource_id: pageId,
          ...seo.value,
        }),
      })
    }
  } catch (_e) {}
}
</script>
