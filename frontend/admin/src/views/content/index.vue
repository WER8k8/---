<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">
          内容管理
        </h1>
        <p class="text-gray-500 mt-1">
          管理网站页面内容
        </p>
      </div>
      <router-link
        to="/content/edit/new"
        class="flex items-center px-4 py-2.5 bg-primary-500 text-white rounded-xl hover:bg-primary-600 text-sm font-medium transition-all shadow-lg shadow-primary-200"
      >
        <PlusOutlined class="w-4 h-4 mr-2" />
        添加内容
      </router-link>
    </div>

    <a-card
      :loading="loading"
      class="mb-6"
    >
      <div class="flex flex-wrap items-center gap-3">
        <a-input
          v-model="search"
          placeholder="搜索页面标题..."
          class="flex-1 min-w-[200px]"
          @keyup.enter="() => fetchContent()"
        >
          <template #prefix>
            <SearchOutlined />
          </template>
        </a-input>
        <a-select
          v-model="filterType"
          placeholder="全部类型"
          @change="() => fetchContent()"
        >
          <a-select-option value="">
            全部类型
          </a-select-option>
          <a-select-option value="about">
            关于我们
          </a-select-option>
          <a-select-option value="news">
            新闻资讯
          </a-select-option>
          <a-select-option value="contact">
            联系我们
          </a-select-option>
          <a-select-option value="custom">
            自定义页面
          </a-select-option>
        </a-select>
        <a-select
          v-model="filterStatus"
          placeholder="全部状态"
          @change="() => fetchContent()"
        >
          <a-select-option value="">
            全部状态
          </a-select-option>
          <a-select-option value="true">
            已发布
          </a-select-option>
          <a-select-option value="false">
            草稿
          </a-select-option>
        </a-select>
        <a-button
          type="primary"
          @click="() => fetchContent()"
        >
          搜索
        </a-button>
      </div>
    </a-card>

    <a-card>
      <a-table
        :columns="columns"
        :data-source="contentList"
        :pagination="pagination"
        :loading="loading"
        row-key="id"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'title'">
            <div class="font-medium text-gray-900">
              {{ record.title }}
            </div>
            <div class="text-sm text-gray-400">
              /{{ record.slug }}
            </div>
          </template>
          <template v-else-if="column.key === 'page_type'">
            <a-tag :color="getTypeColor(record.page_type)">
              {{ getTypeText(record.page_type) }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'is_published'">
            <a-tag :color="record.status === 'published' ? 'green' : 'default'">
              {{ record.status === 'published' ? '已发布' : '草稿' }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'updated_at'">
            {{ record.updated_at ? formatDate(record.updated_at) : '-' }}
          </template>
          <template v-else-if="column.key === 'actions'">
            <a-space>
              <router-link
                :to="`/content/edit/${record.id}`"
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
  PlusOutlined,
  SearchOutlined,
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
import { contentAPI } from '@/api'

const contentList = ref<any[]>([])
const loading = ref(false)
const search = ref('')
const filterType = ref('')
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
  { title: '页面标题', key: 'title', width: 250 },
  { title: '类型', key: 'page_type', width: 120 },
  { title: '状态', key: 'is_published', width: 100 },
  { title: '更新时间', key: 'updated_at', width: 150 },
  { title: '操作', key: 'actions', width: 100 },
]

function getTypeColor(type: string) {
  if (type === 'about') return 'blue'
  if (type === 'news') return 'purple'
  if (type === 'contact') return 'green'
  return 'default'
}

function getTypeText(type: string) {
  if (type === 'about') return '关于我们'
  if (type === 'news') return '新闻资讯'
  if (type === 'contact') return '联系我们'
  if (type === 'custom') return '自定义页面'
  return type
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleString('zh-CN')
}

async function fetchContent(page = 1) {
  loading.value = true
  pagination.value.current = page
  try {
    const params: Record<string, any> = {
      page,
      page_size: pagination.value.pageSize,
    }
    if (search.value) params.search = search.value
    if (filterType.value) params.page_type = filterType.value
    if (filterStatus.value) params.is_published = filterStatus.value

    const res = await contentAPI.list(params)
    contentList.value = res.data.items || []
    pagination.value.total = res.data.total || 0
  } catch (e) {
    console.error('Failed to fetch content:', e)
  } finally {
    loading.value = false
  }
}

function handleDelete(record: any) {
  Modal.confirm({
    title: '确认删除',
    content: `确定要删除页面 "${record.title}" 吗？此操作不可撤销。`,
    okType: 'danger',
    async onOk() {
      try {
        await contentAPI.delete(record.id)
        await fetchContent()
        Modal.success({ title: '删除成功' })
      } catch (e: any) {
        Modal.error({ title: '删除失败', content: e.message })
      }
    },
  })
}

onMounted(() => {
  fetchContent()
})
</script>
