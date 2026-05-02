<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-primary-900">
        分类管理
      </h1>
      <div class="flex items-center space-x-3">
        <NuxtLink
          to="/admin/products"
          class="px-4 py-2.5 border border-border text-text-secondary rounded-xl hover:bg-surface-hover text-sm font-medium transition-colors"
        >
          产品列表
        </NuxtLink>
        <button
          class="px-4 py-2.5 bg-gradient-to-r from-secondary-500 to-secondary-600 text-white rounded-xl hover:from-secondary-600 hover:to-secondary-700 text-sm font-medium transition-all shadow-lg shadow-secondary-200"
          @click="showAddDialog(null)"
        >
          + 添加分类
        </button>
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
      v-else-if="!categories.length"
      class="bg-surface rounded-xl border border-border p-12 text-center"
    >
      <p class="text-text-muted mb-4">
        暂无分类，请添加第一个分类
      </p>
    </div>
    <div
      v-else
      class="bg-surface rounded-xl border border-border overflow-hidden"
    >
      <table class="w-full">
        <thead>
          <tr class="bg-surface-elevated border-b border-border">
            <th class="text-left px-6 py-4 text-xs font-semibold text-text-secondary uppercase">
              分类名称
            </th>
            <th class="text-left px-6 py-4 text-xs font-semibold text-text-secondary uppercase">
              别名 (slug)
            </th>
            <th class="text-left px-6 py-4 text-xs font-semibold text-text-secondary uppercase">
              父级分类
            </th>
            <th class="text-left px-6 py-4 text-xs font-semibold text-text-secondary uppercase">
              排序
            </th>
            <th class="text-left px-6 py-4 text-xs font-semibold text-text-secondary uppercase">
              状态
            </th>
            <th class="text-right px-6 py-4 text-xs font-semibold text-text-secondary uppercase">
              操作
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="cat in categories"
            :key="cat.id"
            class="border-b border-border-light hover:bg-surface-hover/50 transition-colors"
          >
            <td class="px-6 py-4">
              <div class="text-sm font-medium text-primary-900">
                {{ cat.name }}
              </div>
              <div
                v-if="cat.description"
                class="text-xs text-text-muted"
              >
                {{ cat.description }}
              </div>
            </td>
            <td class="px-6 py-4 text-sm text-text-secondary">
              {{ cat.slug }}
            </td>
            <td class="px-6 py-4 text-sm text-text-secondary">
              {{ parentName(cat.parent_id) }}
            </td>
            <td class="px-6 py-4 text-sm text-text-secondary">
              {{ cat.sort_order }}
            </td>
            <td class="px-6 py-4">
              <span
                :class="cat.is_active ? 'bg-accent/10 text-accent' : 'bg-surface-hover text-text-muted'"
                class="inline-flex px-3 py-1 text-xs font-medium rounded-full"
              >
                {{ cat.is_active ? '启用' : '停用' }}
              </span>
            </td>
            <td class="px-6 py-4 text-right">
              <button
                class="text-text-secondary hover:text-primary-900 text-sm font-medium mr-3 transition-colors"
                @click="showAddDialog(cat)"
              >
                添加子级
              </button>
              <button
                class="text-secondary hover:text-secondary/80 text-sm font-medium mr-3 transition-colors"
                @click="showEditDialog(cat)"
              >
                编辑
              </button>
              <button
                class="text-danger hover:text-danger/80 text-sm font-medium transition-colors"
                @click="handleDelete(cat)"
              >
                删除
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div
      v-if="showDialog"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
      @click.self="showDialog = false"
    >
      <div class="bg-surface rounded-2xl shadow-elevated border border-border p-6 w-full max-w-md">
        <h3 class="text-lg font-semibold text-primary-900 mb-4">
          {{ editingCategory ? '编辑分类' : '添加分类' }}
        </h3>
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-semibold text-primary-900 mb-2">分类名称</label>
            <input
              v-model="dialogForm.name"
              class="w-full bg-surface-elevated border border-border rounded-xl px-4 py-2.5 text-primary-900 placeholder:text-text-muted focus:outline-none focus:border-secondary-500 focus:ring-2 focus:ring-secondary-500/20 transition-all"
              placeholder="如: 岩棉制品"
              @input="dialogAutoSlug"
            >
          </div>
          <div>
            <label class="block text-sm font-semibold text-primary-900 mb-2">别名 (slug)</label>
            <input
              v-model="dialogForm.slug"
              class="w-full bg-surface-elevated border border-border rounded-xl px-4 py-2.5 text-primary-900 placeholder:text-text-muted focus:outline-none focus:border-secondary-500 focus:ring-2 focus:ring-secondary-500/20 transition-all"
              placeholder="rock-wool"
            >
          </div>
          <div>
            <label class="block text-sm font-semibold text-primary-900 mb-2">父级分类</label>
            <select
              v-model="dialogForm.parent_id"
              class="w-full bg-surface-elevated border border-border rounded-xl px-4 py-2.5 text-primary-900 focus:outline-none focus:border-secondary-500 focus:ring-2 focus:ring-secondary-500/20 transition-all"
            >
              <option value="">
                无（顶级分类）
              </option>
              <option
                v-for="cat in categories"
                :key="cat.id"
                :value="cat.id"
                :disabled="cat.id === editingCategory?.id"
              >
                {{ cat.name }}
              </option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-semibold text-primary-900 mb-2">描述</label>
            <textarea
              v-model="dialogForm.description"
              rows="2"
              class="w-full bg-surface-elevated border border-border rounded-xl px-4 py-2.5 text-primary-900 placeholder:text-text-muted focus:outline-none focus:border-secondary-500 focus:ring-2 focus:ring-secondary-500/20 transition-all"
              placeholder="简短描述此分类"
            />
          </div>
          <div>
            <label class="block text-sm font-semibold text-primary-900 mb-2">排序</label>
            <input
              v-model.number="dialogForm.sort_order"
              type="number"
              class="w-full bg-surface-elevated border border-border rounded-xl px-4 py-2.5 text-primary-900 focus:outline-none focus:border-secondary-500 focus:ring-2 focus:ring-secondary-500/20 transition-all"
            >
          </div>
        </div>
        <div
          v-if="dialogError"
          class="mt-3 text-sm text-danger"
        >
          {{ dialogError }}
        </div>
        <div class="flex justify-end space-x-3 mt-6">
          <button
            class="px-4 py-2.5 text-text-secondary border border-border rounded-xl hover:bg-surface-hover text-sm font-medium transition-colors"
            @click="showDialog = false"
          >
            取消
          </button>
          <button
            :disabled="dialogSaving"
            class="px-4 py-2.5 bg-gradient-to-r from-secondary-500 to-secondary-600 text-white rounded-xl hover:from-secondary-600 hover:to-secondary-700 disabled:opacity-50 text-sm font-medium transition-all shadow-lg shadow-secondary-200"
            @click="handleSaveCategory"
          >
            {{ dialogSaving ? '保存中...' : '保存' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'

definePageMeta({ layout: 'admin' })

interface Category {
  id: string
  name: string
  slug: string
  parent_id: string | null
  description: string
  sort_order: number
  is_active: boolean
}

const categories = ref<Category[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

const showDialog = ref(false)
const editingCategory = ref<Category | null>(null)
const dialogSaving = ref(false)
const dialogError = ref<string | null>(null)

const dialogForm = reactive({
  name: '',
  slug: '',
  parent_id: '',
  description: '',
  sort_order: 0,
})

function dialogAutoSlug() {
  if (dialogForm.slug || !dialogForm.name) return
  dialogForm.slug = dialogForm.name
    .replace(/[^\w\u4e00-\u9fff]/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '')
    .toLowerCase()
}

function parentName(parentId: string | null) {
  if (!parentId) return '-'
  const parent = categories.value.find(c => c.id === parentId)
  return parent ? parent.name : '-'
}

function showAddDialog(parent: Category | null) {
  editingCategory.value = null
  dialogForm.name = ''
  dialogForm.slug = ''
  dialogForm.parent_id = parent ? parent.id : ''
  dialogForm.description = ''
  dialogForm.sort_order = 0
  dialogError.value = null
  showDialog.value = true
}

function showEditDialog(cat: Category) {
  editingCategory.value = cat
  dialogForm.name = cat.name
  dialogForm.slug = cat.slug
  dialogForm.parent_id = cat.parent_id || ''
  dialogForm.description = cat.description || ''
  dialogForm.sort_order = cat.sort_order || 0
  dialogError.value = null
  showDialog.value = true
}

async function fetchCategories() {
  loading.value = true
  error.value = null
  try {
    const token = localStorage.getItem('admin_token')
    const res = await fetch('/api/v1/products/categories', {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (!res.ok) throw new Error('获取分类失败')
    categories.value = await res.json()
  } catch (e: any) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

async function handleSaveCategory() {
  if (!dialogForm.name.trim()) {
    dialogError.value = '请输入分类名称'
    return
  }
  if (!dialogForm.slug.trim()) {
    dialogError.value = '请输入别名 (slug)'
    return
  }
  dialogSaving.value = true
  dialogError.value = null
  try {
    const token = localStorage.getItem('admin_token')
    const payload = {
      name: dialogForm.name.trim(),
      slug: dialogForm.slug.trim(),
      parent_id: dialogForm.parent_id || null,
      description: dialogForm.description.trim(),
      sort_order: dialogForm.sort_order || 0,
    }

    if (editingCategory.value) {
      const res = await fetch(`/api/v1/products/categories/${editingCategory.value.id}`, {
        method: 'PUT',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || '保存失败')
      }
    } else {
      const res = await fetch('/api/v1/products/categories', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || '保存失败')
      }
    }
    showDialog.value = false
    await fetchCategories()
  } catch (e: any) {
    dialogError.value = e.message
  } finally {
    dialogSaving.value = false
  }
}

async function handleDelete(cat: Category) {
  if (!confirm(`确定要删除分类 "${cat.name}" 吗？`)) return
  try {
    const token = localStorage.getItem('admin_token')
    const res = await fetch(`/api/v1/products/categories/${cat.id}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (!res.ok) {
      const err = await res.json()
      throw new Error(err.detail || '删除失败')
    }
    await fetchCategories()
  } catch (e: any) {
    alert('删除失败: ' + e.message)
  }
}

onMounted(fetchCategories)
</script>
