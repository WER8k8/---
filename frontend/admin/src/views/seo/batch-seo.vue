<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">
          批量SEO管理
        </h1>
        <p class="text-gray-500 mt-1">
          批量管理页面SEO信息
        </p>
      </div>
      <div class="flex items-center space-x-3">
        <a-button @click="selectAll">
          <CheckSquareOutlined class="w-4 h-4 mr-2" />
          {{ selectedRows.length > 0 ? '取消全选' : '全选' }}
        </a-button>
        <a-button
          type="primary"
          :disabled="selectedRows.length === 0"
          @click="batchOptimize"
        >
          <ZapOutlined class="w-4 h-4 mr-2" />
          批量优化
        </a-button>
      </div>
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
          @keyup.enter="() => fetchPages()"
        >
          <template #prefix>
            <SearchOutlined />
          </template>
        </a-input>
        <a-select
          v-model="filterStatus"
          placeholder="全部状态"
          @change="() => fetchPages()"
        >
          <a-select-option value="">
            全部状态
          </a-select-option>
          <a-select-option value="optimized">
            已优化
          </a-select-option>
          <a-select-option value="pending">
            待优化
          </a-select-option>
          <a-select-option value="failed">
            优化失败
          </a-select-option>
        </a-select>
        <a-button
          type="primary"
          @click="() => fetchPages()"
        >
          搜索
        </a-button>
      </div>
    </a-card>

    <a-card>
      <a-table
        :columns="columns"
        :data-source="pages"
        :pagination="pagination"
        :loading="loading"
        :row-selection="{
          type: 'checkbox',
          selectedRowKeys: selectedRows,
          onChange: handleSelectChange,
        }"
        row-key="id"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'title'">
            <div class="font-medium text-gray-900">
              {{ record.title }}
            </div>
            <div class="text-sm text-gray-400">
              {{ record.meta_title?.slice(0, 50) }}...
            </div>
          </template>
          <template v-else-if="column.key === 'status'">
            <a-tag :color="getStatusColor(record.status)">
              {{ getStatusText(record.status) }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'ai_optimized'">
            <CheckCircleOutlined
              v-if="record.ai_optimized"
              class="text-green-500"
            />
            <CloseCircleOutlined
              v-else
              class="text-gray-400"
            />
          </template>
          <template v-else-if="column.key === 'updated_at'">
            {{ record.updated_at ? formatDate(record.updated_at) : '-' }}
          </template>
          <template v-else-if="column.key === 'actions'">
            <a-space>
              <a-button
                type="text"
                @click="handleEdit(record)"
              >
                <EditOutlined />
              </a-button>
              <a-button
                type="primary"
                text
                @click="handleOptimize(record)"
              >
                <SparklesOutlined />
              </a-button>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <a-modal
      v-model:open="showEditModal"
      :title="editingPage ? '编辑SEO信息' : '添加SEO信息'"
      @ok="handleSavePage"
      @cancel="showEditModal = false"
    >
      <a-form
        :model="pageForm"
        layout="vertical"
      >
        <a-form-item
          label="页面标题"
          :required="true"
        >
          <a-input
            v-model="pageForm.title"
            placeholder="页面标题"
          />
        </a-form-item>
        <a-form-item label="SEO标题">
          <a-input
            v-model="pageForm.meta_title"
            placeholder="建议不超过60字符"
          />
          <p class="text-xs text-gray-400 mt-1">
            {{ pageForm.meta_title.length }}/60
          </p>
        </a-form-item>
        <a-form-item label="SEO描述">
          <a-textarea
            v-model="pageForm.meta_description"
            :rows="2"
            placeholder="建议不超过160字符"
          />
          <p class="text-xs text-gray-400 mt-1">
            {{ pageForm.meta_description.length }}/160
          </p>
        </a-form-item>
        <a-form-item label="SEO关键词">
          <a-input
            v-model="pageForm.meta_keywords"
            placeholder="关键词1, 关键词2, 关键词3"
          />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import {
  CheckSquareOutlined,
  ApiOutlined as ZapOutlined,
  SearchOutlined,
  EditOutlined,
  ShakeOutlined as SparklesOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
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
  Modal as AModal,
  Form as AForm,
  FormItem as AFormItem,
  Textarea as ATextarea,
  Modal,
} from 'ant-design-vue'
import { seoAPI } from '@/api'

const pages = ref<any[]>([])
const loading = ref(false)
const search = ref('')
const filterStatus = ref('')
const selectedRows = ref<string[]>([])
const showEditModal = ref(false)
const editingPage = ref<any>(null)

const pageForm = ref({
  title: '',
  meta_title: '',
  meta_description: '',
  meta_keywords: '',
})

const pagination = ref({
  current: 1,
  pageSize: 20,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total: number) => `共 ${total} 条记录`,
  total: 0,
})

const columns = [
  { title: '页面标题', key: 'title', width: 300 },
  { title: '状态', key: 'status', width: 100 },
  { title: 'AI优化', key: 'ai_optimized', width: 80 },
  { title: '更新时间', key: 'updated_at', width: 150 },
  { title: '操作', key: 'actions', width: 120 },
]

function getStatusColor(status: string) {
  if (status === 'optimized') return 'green'
  if (status === 'pending') return 'gold'
  if (status === 'failed') return 'red'
  return 'default'
}

function getStatusText(status: string) {
  if (status === 'optimized') return '已优化'
  if (status === 'pending') return '待优化'
  if (status === 'failed') return '优化失败'
  return status
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleString('zh-CN')
}

function handleSelectChange(keys: (string | number)[]) {
  selectedRows.value = keys.map(k => String(k))
}

function selectAll() {
  if (selectedRows.value.length > 0) {
    selectedRows.value = []
  } else {
    selectedRows.value = pages.value.map((p) => p.id)
  }
}

async function fetchPages(page = 1) {
  loading.value = true
  pagination.value.current = page
  try {
    const params: Record<string, any> = {
      page,
      page_size: pagination.value.pageSize,
    }
    if (search.value) params.search = search.value
    if (filterStatus.value) params.status = filterStatus.value

    const res = await seoAPI.pages(params)
    pages.value = res.data.items || []
    pagination.value.total = res.data.total || 0
  } catch (e) {
    console.error('Failed to fetch pages:', e)
  } finally {
    loading.value = false
  }
}

function handleEdit(record: any) {
  editingPage.value = record
  pageForm.value = {
    title: record.title || '',
    meta_title: record.meta_title || '',
    meta_description: record.meta_description || '',
    meta_keywords: record.meta_keywords || '',
  }
  showEditModal.value = true
}

async function handleSavePage() {
  if (!pageForm.value.title) {
    Modal.warning({ title: '提示', content: '请输入页面标题' })
    return
  }

  try {
    const data = {
      title: pageForm.value.title,
      meta_title: pageForm.value.meta_title,
      meta_description: pageForm.value.meta_description,
      meta_keywords: pageForm.value.meta_keywords,
    }

    if (editingPage.value) {
      await seoAPI.updatePage(editingPage.value.id, data)
      Modal.success({ title: '修改成功' })
    } else {
      await seoAPI.updatePage('new', data)
      Modal.success({ title: '创建成功' })
    }

    showEditModal.value = false
    editingPage.value = null
    pageForm.value = { title: '', meta_title: '', meta_description: '', meta_keywords: '' }
    await fetchPages()
  } catch (e: any) {
    Modal.error({ title: '操作失败', content: e.message })
  }
}

async function handleOptimize(record: any) {
  Modal.confirm({
    title: '确认优化',
    content: `确定要使用AI优化页面 "${record.title}" 吗？`,
    async onOk() {
      try {
        await seoAPI.optimizePage(record.id, { ai_model: 'gpt-4o' })
        Modal.success({ title: '优化成功' })
        await fetchPages()
      } catch (e: any) {
        Modal.error({ title: '优化失败', content: e.message })
      }
    },
  })
}

async function batchOptimize() {
  if (selectedRows.value.length === 0) return

  Modal.confirm({
    title: '批量优化',
    content: `确定要优化选中的 ${selectedRows.value.length} 个页面吗？`,
    async onOk() {
      try {
        for (const id of selectedRows.value) {
          await seoAPI.optimizePage(id, { ai_model: 'gpt-4o' })
        }
        Modal.success({ title: '批量优化成功' })
        selectedRows.value = []
        await fetchPages()
      } catch (e: any) {
        Modal.error({ title: '批量优化失败', content: e.message })
      }
    },
  })
}

onMounted(() => {
  fetchPages()
})
</script>
