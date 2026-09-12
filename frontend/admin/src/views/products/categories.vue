<template>
  <YdPage title="分类管理" subtitle="产品分类树 · 来自 /products/categories/tree" surface="elevated">
    <template #actions>
      <router-link
        :to="`${productBase}/products`"
        class="px-4 py-2 border border-gray-200 text-gray-700 rounded-xl text-sm font-medium hover:bg-gray-50"
      >
        返回产品列表
      </router-link>
      <a-button type="default" :loading="loading" @click="fetchTree">刷新</a-button>
      <a-button type="primary" @click="openCreate">
        <PlusOutlined class="w-4 h-4 mr-2" />
        添加分类
      </a-button>
    </template>
  <div class="space-y-6 animate-fade-in">
    <a-alert
      v-if="loadError"
      type="warning"
      show-icon
      :message="loadError"
      class="rounded-xl"
    />

    <a-card>
      <SkeletonCard v-if="loading" variant="card" />
      <template v-else>
        <a-empty
          v-if="!treeRows.length"
          description="暂无分类数据"
        />
        <a-tree
          v-else
          v-model:expanded-keys="expandedKeys"
          :tree-data="treeRows"
          :field-names="fieldNames"
        >
          <template #title="{ title, data }">
            <span class="flex items-center justify-between gap-3 w-full min-w-0">
              <span class="truncate">{{ title }}</span>
              <span class="flex shrink-0 items-center space-x-1">
                <a-button
                  type="text"
                  size="small"
                  @click.stop="handleEdit(data.id)"
                >
                  <EditOutlined />
                </a-button>
                <a-button
                  type="text"
                  size="small"
                  danger
                  @click.stop="handleDelete(data.id)"
                >
                  <DeleteOutlined />
                </a-button>
              </span>
            </span>
          </template>
        </a-tree>
      </template>
    </a-card>

    <a-modal
      v-model:open="showAddModal"
      :title="editingCategory ? '编辑分类' : '添加分类'"
      :confirm-loading="saveLoading"
      ok-text="保存"
      cancel-text="取消"
      @ok="handleSaveCategory"
      @cancel="closeModal"
      :width="500"
    >
      <a-form
        :model="categoryForm"
        layout="vertical"
        class="space-y-4"
      >
        <a-form-item
          label="分类名称"
          :required="true"
          validate-trigger="change"
        >
          <a-input
            v-model:value="categoryForm.name"
            placeholder="请输入分类名称"
            class="w-full"
          />
        </a-form-item>
        <a-form-item label="上级分类">
          <a-select
            v-model:value="categoryForm.parent_id"
            allow-clear
            placeholder="无（顶级分类）"
            class="w-full"
          >
            <a-select-option
              v-for="cat in parentOptions"
              :key="cat.id"
              :value="cat.id"
            >
              {{ cat.name }}
            </a-select-option>
          </a-select>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
  </YdPage>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRoute } from 'vue-router';
const route = useRoute();
const productBase = computed(() => (route.path.startsWith('/client') ? '/client' : ''));
import { ref, watch, onMounted } from 'vue'
import { YdPage } from '@/components/youding'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
} from '@ant-design/icons-vue'
import {
  Card as ACard,
  Tree as ATree,
  Button as AButton,
  Modal as AModal,
  Form as AForm,
  FormItem as AFormItem,
  Input as AInput,
  Select as ASelect,
  SelectOption as ASelectOption,
  Empty as AEmpty,
  message,
} from 'ant-design-vue'
import { ydConfirm } from '@/utils/ydModal'
import { productsAPI, unwrapApiData } from '@/api'
import SkeletonCard from '@/components/common/SkeletonCard.vue'

const treeRows = ref<any[]>([])
const loading = ref(false)
const saveLoading = ref(false)
const loadError = ref('')
const expandedKeys = ref<string[]>([])
const showAddModal = ref(false)
const editingCategory = ref<any | null>(null)

const categoryForm = ref({
  name: '',
  parent_id: undefined as string | undefined,
})

const fieldNames = {
  title: 'name',
  key: 'id',
  children: 'children',
}

function makeCategorySlug(name: string, fallback?: string) {
  let s = name
    .trim()
    .toLowerCase()
    .replace(/\s+/g, '-')
    .replace(/[^a-z0-9-]/g, '')
  if (!s && fallback && /^[a-z0-9-]+$/.test(fallback))
    s = fallback
  if (!s)
    s = `cat-${Date.now().toString(36)}`
  return s.slice(0, 95)
}

function buildTreeFromFlat(list: any[]) {
  const map = new Map<string, any>()
  const roots: any[] = []
  if (!Array.isArray(list)) return roots
  list.forEach((cat) => {
    map.set(cat.id, { ...cat, children: [] })
  })
  map.forEach((cat) => {
    if (cat.parent_id && map.has(cat.parent_id))
      map.get(cat.parent_id).children.push(cat)
    else
      roots.push(cat)
  })
  return roots
}

function collectIds(nodes: any[]): string[] {
  const ids: string[] = []
  const walk = (arr: any[]) => {
    for (const n of arr || []) {
      ids.push(n.id)
      if (n.children?.length) walk(n.children)
    }
  }
  walk(nodes || [])
  return ids
}

function findCategoryById(id: string): any | null {
  const walk = (nodes: any[]): any | null => {
    for (const n of nodes || []) {
      if (n.id === id) return n
      if (n.children?.length) {
        const f = walk(n.children)
        if (f) return f
      }
    }
    return null
  }
  return walk(treeRows.value)
}

const parentOptions = computed(() => {
  const out: { id: string; name: string }[] = []
  const walk = (items: any[], prefix = '') => {
    for (const item of items || []) {
      if (!editingCategory.value || item.id !== editingCategory.value.id) {
        out.push({ id: item.id, name: prefix + item.name })
        if (item.children?.length)
          walk(item.children, `${prefix}└ `)
      }
    }
  }
  walk(treeRows.value)
  return out
})

async function fetchFlatCategories() {
  const res = await productsAPI.categories()
  const raw = unwrapApiData<unknown>(res)
  const flat = Array.isArray(raw)
    ? raw
    : (raw && typeof raw === 'object' && Array.isArray((raw as { categories?: unknown }).categories)
        ? (raw as { categories: any[] }).categories
        : [])
  return flat
}

async function fetchTree() {
  loading.value = true
  loadError.value = ''
  try {
    const res = await productsAPI.categoriesTree()
    const raw = unwrapApiData<unknown>(res)
    if (Array.isArray(raw) && raw.length) {
      treeRows.value = raw as any[]
      expandedKeys.value = collectIds(treeRows.value).slice(0, 80)
      loading.value = false
      return
    }
  }
  catch {
    /* 回退扁平 */
  }
  try {
    const flat = await fetchFlatCategories()
    treeRows.value = buildTreeFromFlat(flat)
    expandedKeys.value = collectIds(treeRows.value).slice(0, 80)
    if (!treeRows.value.length)
      loadError.value = '分类树为空；可在后端写入分类或使用「添加分类」。'
  }
  catch (e) {
    treeRows.value = []
    loadError.value = '分类数据加载失败（请检查 /api/v1/products/categories 与 tree 接口）。'
    message.error(loadError.value)
    if (import.meta.env.DEV) console.error(e)
  }
  loading.value = false
}

function openCreate() {
  editingCategory.value = null
  categoryForm.value = { name: '', parent_id: undefined }
  showAddModal.value = true
}

function closeModal() {
  showAddModal.value = false
  editingCategory.value = null
  categoryForm.value = { name: '', parent_id: undefined }
}

watch(showAddModal, (open) => {
  if (open && !editingCategory.value)
    categoryForm.value = { name: '', parent_id: undefined }
})

function handleEdit(id: string) {
  const cat = findCategoryById(id)
  if (cat) {
    editingCategory.value = cat
    categoryForm.value = {
      name: cat.name,
      parent_id: cat.parent_id || undefined,
    }
    showAddModal.value = true
  }
}

function handleDelete(id: string) {
  ydConfirm({
    title: '确认删除',
    content: '确定要删除该分类吗？可能影响关联产品。',
    okType: 'danger',
    onOk() {
      return (async () => {
        try {
          await productsAPI.deleteCategory(id)
          message.success('已删除')
          await fetchTree()
        }
        catch (e: unknown) {
          message.error(e instanceof Error ? e.message : '删除失败')
        }
      })();
    },
  })
}

async function handleSaveCategory() {
  if (!categoryForm.value.name?.trim()) {
    message.warning('请输入分类名称')
    return Promise.reject()
  }

  saveLoading.value = true
  try {
    const name = categoryForm.value.name.trim()
    const parentId = categoryForm.value.parent_id

    if (editingCategory.value) {
      const slug = makeCategorySlug(name, editingCategory.value.slug)
      const updateRes = await productsAPI.updateCategory(editingCategory.value.id, {
        name,
        slug,
        parent_id: parentId ?? null,
      })
      const updatedData = unwrapApiData<any>(updateRes)
      if (updatedData && updatedData.id) {
        const idx = treeRows.value.findIndex((t: any) => t.id === updatedData.id)
        if (idx !== -1) {
          treeRows.value[idx] = { ...treeRows.value[idx], ...updatedData }
        }
      }
      message.success('已更新分类')
    }
    else {
      const createRes = await productsAPI.createCategory({
        name,
        slug: makeCategorySlug(name),
        parent_id: parentId ?? null,
      })
      const newCategory = unwrapApiData<any>(createRes)
      if (newCategory && newCategory.id) {
        if (parentId) {
          const addToParent = (nodes: any[]): boolean => {
            for (const node of nodes) {
              if (node.id === parentId) {
                node.children = node.children || []
                node.children.push({ ...newCategory, children: [] })
                return true
              }
              if (node.children && node.children.length && addToParent(node.children)) {
                return true
              }
            }
            return false
          }
          addToParent(treeRows.value)
        } else {
          treeRows.value.push({ ...newCategory, children: [] })
        }
        expandedKeys.value = [...expandedKeys.value, newCategory.id]
      }
      message.success('已创建分类')
    }

    closeModal()
  }
  catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '保存失败')
    if (import.meta.env.DEV) console.error('Save category error:', e)
    return Promise.reject(e)
  }
  finally {
    saveLoading.value = false
  }
}

onMounted(() => {
  fetchTree()
})
</script>
