<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">
          产品管理
        </h1>
        <p class="text-gray-500 mt-1">
          管理产品信息和分类
        </p>
      </div>
      <div class="flex items-center space-x-3">
        <router-link
          to="/products/categories"
          class="flex items-center px-4 py-2.5 border border-gray-200 text-gray-600 rounded-xl hover:bg-gray-50 text-sm font-medium transition-colors"
        >
          <FolderOpenOutlined class="w-4 h-4 mr-2" />
          分类管理
        </router-link>
        <router-link
          to="/products/edit/new"
          class="flex items-center px-4 py-2.5 bg-primary-500 text-white rounded-xl hover:bg-primary-600 text-sm font-medium transition-all shadow-lg shadow-primary-200"
        >
          <PlusOutlined class="w-4 h-4 mr-2" />
          添加产品
        </router-link>
      </div>
    </div>

    <a-card
      :loading="loading"
      class="mb-6"
    >
      <div class="flex flex-wrap items-center gap-3">
        <a-input
          v-model="search"
          placeholder="搜索产品名称..."
          class="flex-1 min-w-[200px]"
          @keyup.enter="() => fetchProducts()"
        >
          <template #prefix>
            <SearchOutlined />
          </template>
        </a-input>
        <a-select
          v-model="filterCategory"
          placeholder="全部分类"
          @change="() => fetchProducts()"
        >
          <a-select-option value="">
            全部分类
          </a-select-option>
          <a-select-option
            v-for="cat in categories"
            :key="cat.id"
            :value="cat.id"
          >
            {{ cat.name }}
          </a-select-option>
        </a-select>
        <a-select
          v-model="filterStatus"
          placeholder="全部状态"
          @change="() => fetchProducts()"
        >
          <a-select-option value="">
            全部状态
          </a-select-option>
          <a-select-option value="true">
            上架
          </a-select-option>
          <a-select-option value="false">
            下架
          </a-select-option>
        </a-select>
        <a-button
          type="primary"
          @click="() => fetchProducts()"
        >
          搜索
        </a-button>
      </div>
    </a-card>

    <a-card>
      <a-table
        :columns="columns"
        :data-source="products"
        :pagination="pagination"
        :loading="loading"
        row-key="id"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'name'">
            <div class="font-medium text-gray-900">
              {{ record.name }}
            </div>
            <div class="text-sm text-gray-400">
              /{{ record.slug }}
            </div>
          </template>
          <template v-else-if="column.key === 'category'">
            {{ record.category_name || '-' }}
          </template>
          <template v-else-if="column.key === 'fire_rating'">
            <a-tag :color="getFireRatingColor(record.fire_rating)">
              {{ record.fire_rating || '-' }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'is_active'">
            <a-tag :color="record.is_active ? 'green' : 'default'">
              {{ record.is_active ? '上架' : '下架' }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'updated_at'">
            {{ record.updated_at ? formatDate(record.updated_at) : '-' }}
          </template>
          <template v-else-if="column.key === 'actions'">
            <a-space>
              <router-link
                :to="`/products/edit/${record.id}`"
                class="text-primary hover:text-primary/80"
              >
                <EditOutlined />
              </router-link>
              <a-button
                type="text"
                danger
                @click="handleDelete(record)"
              >
                <DeleteOutlined />
              </a-button>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import {
  SearchOutlined,
  FolderOpenOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
} from '@ant-design/icons-vue'
import {
  Card as ACard,
  Input as AInput,
  Select as ASelect,
  SelectOption as ASelectOption,
  Button as AButton,
  Table as ATable,
  Tag as ATag,
  Space as ASpace,
  Modal,
} from 'ant-design-vue'
import { productsAPI } from '@/api'

const products = ref<any[]>([])
const categories = ref<any[]>([])
const loading = ref(false)
const search = ref('')
const filterCategory = ref('')
const filterStatus = ref('')

const pagination = ref({
  current: 1,
  pageSize: 20,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total: number) => `共 ${total} 条记录`,
  total: 0,
})

const columns = [
  { title: '产品名称', key: 'name', width: 200 },
  { title: '分类', key: 'category', width: 120 },
  { title: '防火等级', key: 'fire_rating', width: 100 },
  { title: '状态', key: 'is_active', width: 80 },
  { title: '浏览量', key: 'view_count', width: 80 },
  { title: '更新时间', key: 'updated_at', width: 120 },
  { title: '操作', key: 'actions', width: 100 },
]

function getFireRatingColor(rating: string) {
  if (rating === 'A级') return 'green'
  if (rating === 'B1级') return 'gold'
  if (rating === 'B2级') return 'orange'
  return 'default'
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

async function fetchCategories() {
  try {
    const res = await productsAPI.categories()
    categories.value = res.data.categories || []
  } catch (e) {
    console.error('Failed to fetch categories:', e)
  }
}

async function fetchProducts(page = 1) {
  loading.value = true
  pagination.value.current = page
  try {
    const params: Record<string, any> = {
      page,
      page_size: pagination.value.pageSize,
    }
    if (search.value) params.search = search.value
    if (filterCategory.value) params.category_id = filterCategory.value
    if (filterStatus.value) params.is_active = filterStatus.value

    const res = await productsAPI.list(params)
    const catMap = new Map(categories.value.map((c: any) => [c.id, c.name]))
    const items = res.data.items || []
    products.value = items.map((p: any) => ({
      ...p,
      category_name: catMap.get(p.category_id) || '-',
    }))
    pagination.value.total = res.data.total || 0
  } catch (e) {
    console.error('Failed to fetch products:', e)
  } finally {
    loading.value = false
  }
}

function handleDelete(record: any) {
  Modal.confirm({
    title: '确认删除',
    content: `确定要删除产品 "${record.name}" 吗？此操作不可撤销。`,
    okType: 'danger',
    async onOk() {
      try {
        await productsAPI.delete(record.id)
        await fetchProducts()
        Modal.success({ title: '删除成功' })
      } catch (e: any) {
        Modal.error({ title: '删除失败', content: e.message })
      }
    },
  })
}

onMounted(() => {
  fetchCategories()
  fetchProducts()
})
</script>