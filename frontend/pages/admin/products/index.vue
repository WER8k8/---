<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-primary-900">
        产品管理
      </h1>
      <div class="flex items-center space-x-3">
        <NuxtLink
          to="/admin/products/categories"
          class="px-4 py-2.5 border border-border text-text-secondary rounded-xl hover:bg-surface-hover text-sm font-medium transition-colors"
        >
          分类管理
        </NuxtLink>
        <NuxtLink
          to="/admin/products/edit/new"
          class="px-4 py-2.5 bg-gradient-to-r from-secondary-500 to-secondary-600 text-white rounded-xl hover:from-secondary-600 hover:to-secondary-700 text-sm font-medium transition-all shadow-lg shadow-secondary-200"
        >
          + 添加产品
        </NuxtLink>
      </div>
    </div>

    <div class="bg-surface rounded-xl border border-border p-4 mb-6">
      <div class="flex flex-wrap items-center gap-3">
        <input
          v-model="search"
          placeholder="搜索产品名称..."
          class="flex-1 min-w-[200px] bg-surface-elevated border border-border rounded-xl px-4 py-2.5 text-sm text-primary-900 placeholder:text-text-muted focus:outline-none focus:border-secondary-500 focus:ring-2 focus:ring-secondary-500/20 transition-all"
          @input="debounceSearch"
        >
        <select
          v-model="filterCategory"
          class="bg-surface-elevated border border-border rounded-xl px-4 py-2.5 text-sm text-primary-900 focus:outline-none focus:border-secondary-500 focus:ring-2 focus:ring-secondary-500/20 transition-all"
          @change="fetchProducts"
        >
          <option value="">
            全部分类
          </option>
          <option
            v-for="cat in categories"
            :key="cat.id"
            :value="cat.id"
          >
            {{ cat.name }}
          </option>
        </select>
        <select
          v-model="filterStatus"
          class="bg-surface-elevated border border-border rounded-xl px-4 py-2.5 text-sm text-primary-900 focus:outline-none focus:border-secondary-500 focus:ring-2 focus:ring-secondary-500/20 transition-all"
          @change="fetchProducts"
        >
          <option value="">
            全部状态
          </option>
          <option value="true">
            上架
          </option>
          <option value="false">
            下架
          </option>
        </select>
      </div>
    </div>

    <div
      v-if="loading"
      class="text-center py-12 text-text-muted"
    >
      加载中...
    </div>
    <div
      v-else-if="error"
      class="text-center py-12 text-danger"
    >
      {{ error }}
    </div>
    <div
      v-else-if="products && products.length"
      class="bg-surface rounded-xl border border-border overflow-hidden"
    >
      <table class="w-full">
        <thead>
          <tr class="bg-surface-elevated border-b border-border">
            <th class="text-left px-6 py-4 text-xs font-semibold text-text-secondary uppercase">
              产品名称
            </th>
            <th class="text-left px-6 py-4 text-xs font-semibold text-text-secondary uppercase">
              分类
            </th>
            <th class="text-left px-6 py-4 text-xs font-semibold text-text-secondary uppercase">
              防火等级
            </th>
            <th class="text-left px-6 py-4 text-xs font-semibold text-text-secondary uppercase">
              状态
            </th>
            <th class="text-left px-6 py-4 text-xs font-semibold text-text-secondary uppercase">
              浏览
            </th>
            <th class="text-left px-6 py-4 text-xs font-semibold text-text-secondary uppercase">
              更新于
            </th>
            <th class="text-right px-6 py-4 text-xs font-semibold text-text-secondary uppercase">
              操作
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="p in products"
            :key="p.id"
            class="border-b border-border-light hover:bg-surface-hover/50 transition-colors"
          >
            <td class="px-6 py-4">
              <div class="text-sm font-medium text-primary-900">
                {{ p.name }}
              </div>
              <div class="text-xs text-text-muted">
                /{{ p.slug }}
              </div>
            </td>
            <td class="px-6 py-4 text-sm text-text-secondary">
              {{ p.category_name || '-' }}
            </td>
            <td class="px-6 py-4">
              <span
                v-if="p.fire_rating"
                class="inline-flex px-3 py-1 text-xs font-medium rounded-full"
                :class="fireRatingClass(p.fire_rating)"
              >
                {{ p.fire_rating }}
              </span>
              <span
                v-else
                class="text-text-muted text-sm"
              >-</span>
            </td>
            <td class="px-6 py-4">
              <span
                :class="p.is_active ? 'bg-accent/10 text-accent' : 'bg-surface-hover text-text-muted'"
                class="inline-flex px-3 py-1 text-xs font-medium rounded-full"
              >
                {{ p.is_active ? '上架' : '下架' }}
              </span>
            </td>
            <td class="px-6 py-4 text-sm text-text-secondary">
              {{ p.view_count ?? 0 }}
            </td>
            <td class="px-6 py-4 text-sm text-text-muted">
              {{ p.updated_at ? new Date(p.updated_at).toLocaleDateString('zh-CN') : '-' }}
            </td>
            <td class="px-6 py-4 text-right">
              <NuxtLink
                :to="`/admin/products/edit/${p.id}`"
                class="text-secondary hover:text-secondary/80 text-sm font-medium mr-3 transition-colors"
              >
                编辑
              </NuxtLink>
              <button
                class="text-danger hover:text-danger/80 text-sm font-medium transition-colors"
                @click="handleDelete(p.id, p.name)"
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
      class="bg-surface rounded-xl border border-border p-12 text-center"
    >
      <p class="text-text-muted mb-4">
        暂无产品数据
      </p>
      <NuxtLink
        to="/admin/products/edit/new"
        class="text-secondary hover:text-secondary/80 text-sm font-medium"
      >
        添加第一个产品 →
      </NuxtLink>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

definePageMeta({ layout: 'admin' })

interface Product {
  id: string
  name: string
  slug: string
  category_id: string
  category_name?: string
  fire_rating: string | null
  is_active: boolean
  view_count: number
  updated_at: string | null
}

interface Category {
  id: string
  name: string
}

const products = ref<Product[] | null>(null)
const categories = ref<Category[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const search = ref('')
const filterCategory = ref('')
const filterStatus = ref('')

let searchTimer: ReturnType<typeof setTimeout> | null = null

function debounceSearch() {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(fetchProducts, 300)
}

function fireRatingClass(rating: string) {
  if (rating === 'A级') return 'bg-accent/10 text-accent'
  if (rating === 'B1级') return 'bg-warning/10 text-warning'
  if (rating === 'B2级') return 'bg-warm/10 text-warm'
  return 'bg-surface-hover text-text-muted'
}

async function fetchCategories() {
  try {
    const token = localStorage.getItem('admin_token')
    const res = await fetch('/api/v1/products/categories', {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (res.ok) {
      categories.value = await res.json()
    }
  } catch {}
}

async function fetchProducts() {
  loading.value = true
  error.value = null
  try {
    const token = localStorage.getItem('admin_token')
    const params = new URLSearchParams()
    if (filterCategory.value) params.set('category_id', filterCategory.value)
    if (search.value) params.set('search', search.value)
    if (filterStatus.value) params.set('is_active', filterStatus.value)

    const qs = params.toString()
    const res = await fetch(`/api/v1/products${qs ? '?' + qs : ''}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (!res.ok) throw new Error('获取产品列表失败')
    const data = await res.json()
    const catMap = new Map(categories.value.map(c => [c.id, c.name]))
    products.value = data.map((p: any) => ({
      ...p,
      category_name: catMap.get(p.category_id) || '-',
    }))
  } catch (e: any) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

async function handleDelete(id: string, name: string) {
  if (!confirm(`确定要删除产品 "${name}" 吗？此操作不可撤销。`)) return
  try {
    const token = localStorage.getItem('admin_token')
    const res = await fetch(`/api/v1/products/${id}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (!res.ok) {
      const err = await res.json()
      throw new Error(err.detail || '删除失败')
    }
    await fetchProducts()
  } catch (e: any) {
    alert('删除失败: ' + e.message)
  }
}

onMounted(() => {
  fetchCategories()
  fetchProducts()
})
</script>
