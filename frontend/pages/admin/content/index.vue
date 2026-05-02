<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-gray-900">
        内容列表
      </h1>
      <NuxtLink
        to="/admin/content/edit/new"
        class="px-4 py-2 bg-brand-blue text-white rounded-lg hover:bg-blue-800 text-sm transition-colors"
      >
        + 新建内容
      </NuxtLink>
    </div>
    <div
      v-if="loading"
      class="text-center py-12 text-gray-500"
    >
      加载中...
    </div>
    <div
      v-else-if="error"
      class="text-center py-12 text-red-500"
    >
      {{ error }}
    </div>
    <div
      v-else-if="pages && pages.length"
      class="bg-white rounded-xl shadow-sm overflow-hidden"
    >
      <table class="w-full">
        <thead>
          <tr class="bg-gray-50 border-b border-gray-200">
            <th class="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">
              标题
            </th>
            <th class="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">
              别名
            </th>
            <th class="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">
              状态
            </th>
            <th class="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">
              浏览
            </th>
            <th class="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">
              更新于
            </th>
            <th class="text-right px-6 py-3 text-xs font-semibold text-gray-500 uppercase">
              操作
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="page in pages"
            :key="page.id"
            class="border-b border-gray-100 hover:bg-gray-50"
          >
            <td class="px-6 py-4 text-sm font-medium text-gray-900">
              {{ page.title }}
            </td>
            <td class="px-6 py-4 text-sm text-gray-500">
              /{{ page.slug }}
            </td>
            <td class="px-6 py-4">
              <span
                :class="page.status === 'published' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'"
                class="inline-flex px-2 py-0.5 text-xs font-medium rounded-full"
              >
                {{ page.status === 'published' ? '已发布' : '草稿' }}
              </span>
            </td>
            <td class="px-6 py-4 text-sm text-gray-600">
              {{ page.view_count ?? 0 }}
            </td>
            <td class="px-6 py-4 text-sm text-gray-500">
              {{ page.updated_at ? new Date(page.updated_at).toLocaleDateString('zh-CN') : '-' }}
            </td>
            <td class="px-6 py-4 text-right">
              <NuxtLink
                :to="`/admin/content/edit/${page.id}`"
                class="text-brand-blue hover:text-blue-800 text-sm mr-3 transition-colors"
              >
                编辑
              </NuxtLink>
              <button
                class="text-red-500 hover:text-red-700 text-sm transition-colors"
                @click="handleDelete(page.id)"
              >
                删除
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div
      v-else
      class="bg-white rounded-xl shadow-sm p-6 text-center text-gray-400"
    >
      暂无内容数据
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

definePageMeta({ layout: 'admin' })

interface ContentPage {
  id: string
  title: string
  slug: string
  status: string
  view_count: number
  updated_at: string | null
}

const pages = ref<ContentPage[] | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)

async function fetchPages() {
  loading.value = true
  error.value = null
  try {
    const token = localStorage.getItem('admin_token')
    const res = await fetch('/api/v1/content/pages', {
      headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' }
    })
    if (!res.ok) throw new Error(`请求失败: ${res.status}`)
    pages.value = await res.json()
  } catch (e: any) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

async function handleDelete(pageId: string) {
  if (!confirm('确定删除此页面？此操作不可恢复。')) return
  try {
    const token = localStorage.getItem('admin_token')
    const res = await fetch(`/api/v1/content/pages/${pageId}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (!res.ok) throw new Error('删除失败')
    await fetchPages()
  } catch (e: any) {
    error.value = e.message
  }
}

onMounted(fetchPages)
</script>
