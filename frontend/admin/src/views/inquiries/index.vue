<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">
          询盘管理
        </h1>
        <p class="text-gray-500 mt-1">
          管理客户咨询和询价信息
        </p>
      </div>
    </div>

    <a-card
      :loading="loading"
      class="mb-6"
    >
      <div class="flex flex-wrap items-center gap-3">
        <a-input
          v-model="search"
          placeholder="搜索客户姓名或电话..."
          class="flex-1 min-w-[200px]"
          @keyup.enter="() => fetchInquiries()"
        >
          <template #prefix>
            <SearchOutlined />
          </template>
        </a-input>
        <a-select
          v-model="filterStatus"
          placeholder="全部状态"
          @change="() => fetchInquiries()"
        >
          <a-select-option value="">
            全部状态
          </a-select-option>
          <a-select-option value="pending">
            待处理
          </a-select-option>
          <a-select-option value="contacted">
            已联系
          </a-select-option>
          <a-select-option value="converted">
            已转化
          </a-select-option>
          <a-select-option value="rejected">
            已拒绝
          </a-select-option>
        </a-select>
        <a-button
          type="primary"
          @click="() => fetchInquiries()"
        >
          搜索
        </a-button>
      </div>
    </a-card>

    <a-card>
      <a-table
        :columns="columns"
        :data-source="inquiries"
        :pagination="pagination"
        :loading="loading"
        row-key="id"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'customer'">
            <div class="font-medium text-gray-900">
              {{ record.customer_name }}
            </div>
            <div class="text-sm text-gray-400">
              {{ record.phone }}
            </div>
          </template>
          <template v-else-if="column.key === 'status'">
            <a-tag :color="getStatusColor(record.status)">
              {{ getStatusText(record.status) }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'created_at'">
            {{ record.created_at ? formatDate(record.created_at) : '-' }}
          </template>
          <template v-else-if="column.key === 'actions'">
            <a-space>
              <a-button
                type="text"
                @click="handleView(record)"
              >
                <EyeOutlined />
              </a-button>
              <a-button
                type="text"
                @click="handleUpdateStatus(record)"
              >
                <EditOutlined />
              </a-button>
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

    <a-modal
      v-model:open="showDetailModal"
      title="询盘详情"
      :footer="null"
    >
      <div
        v-if="selectedInquiry"
        class="space-y-4"
      >
        <div class="flex justify-between items-center py-2 border-b">
          <span class="text-gray-500">客户姓名</span>
          <span class="font-medium">{{ selectedInquiry.customer_name }}</span>
        </div>
        <div class="flex justify-between items-center py-2 border-b">
          <span class="text-gray-500">联系电话</span>
          <span>{{ selectedInquiry.phone }}</span>
        </div>
        <div class="flex justify-between items-center py-2 border-b">
          <span class="text-gray-500">邮箱</span>
          <span>{{ selectedInquiry.email || '-' }}</span>
        </div>
        <div class="flex justify-between items-center py-2 border-b">
          <span class="text-gray-500">公司名称</span>
          <span>{{ selectedInquiry.company_name || '-' }}</span>
        </div>
        <div class="flex justify-between items-center py-2 border-b">
          <span class="text-gray-500">感兴趣的产品</span>
          <span>{{ selectedInquiry.product_interest || '-' }}</span>
        </div>
        <div class="py-2">
          <span class="text-gray-500 block mb-2">咨询内容</span>
          <p class="text-gray-700">
            {{ selectedInquiry.message }}
          </p>
        </div>
      </div>
    </a-modal>

    <a-modal
      v-model:open="showStatusModal"
      title="更新状态"
      @ok="handleSaveStatus"
    >
      <a-form
        :model="statusForm"
        layout="vertical"
      >
        <a-form-item label="状态">
          <a-select v-model="statusForm.status">
            <a-select-option value="pending">
              待处理
            </a-select-option>
            <a-select-option value="contacted">
              已联系
            </a-select-option>
            <a-select-option value="converted">
              已转化
            </a-select-option>
            <a-select-option value="rejected">
              已拒绝
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="备注">
          <a-textarea
            v-model="statusForm.note"
            :rows="3"
          />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import {
  SearchOutlined,
  EyeOutlined,
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
  Modal as AModal,
  Form as AForm,
  FormItem as AFormItem,
  Textarea as ATextarea,
} from 'ant-design-vue'
import { inquiriesAPI } from '@/api'

const inquiries = ref<any[]>([])
const loading = ref(false)
const search = ref('')
const filterStatus = ref('')
const showDetailModal = ref(false)
const showStatusModal = ref(false)
const selectedInquiry = ref<any>(null)

const statusForm = ref({
  status: '',
  note: '',
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
  { title: '客户信息', key: 'customer', width: 200 },
  { title: '咨询产品', key: 'product_interest', width: 150 },
  { title: '状态', key: 'status', width: 100 },
  { title: '提交时间', key: 'created_at', width: 150 },
  { title: '操作', key: 'actions', width: 150 },
]

function getStatusColor(status: string) {
  if (status === 'pending') return 'orange'
  if (status === 'contacted') return 'blue'
  if (status === 'converted') return 'green'
  if (status === 'rejected') return 'red'
  return 'default'
}

function getStatusText(status: string) {
  if (status === 'pending') return '待处理'
  if (status === 'contacted') return '已联系'
  if (status === 'converted') return '已转化'
  if (status === 'rejected') return '已拒绝'
  return status
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleString('zh-CN')
}

async function fetchInquiries(page = 1) {
  loading.value = true
  pagination.value.current = page
  try {
    const params: Record<string, any> = {
      page,
      page_size: pagination.value.pageSize,
    }
    if (search.value) params.search = search.value
    if (filterStatus.value) params.status = filterStatus.value

    const res = await inquiriesAPI.list(params)
    inquiries.value = res.data.items || []
    pagination.value.total = res.data.total || 0
  } catch (e) {
    console.error('Failed to fetch inquiries:', e)
  } finally {
    loading.value = false
  }
}

function handleView(record: any) {
  selectedInquiry.value = record
  showDetailModal.value = true
}

function handleUpdateStatus(record: any) {
  selectedInquiry.value = record
  statusForm.value = {
    status: record.status,
    note: record.note || '',
  }
  showStatusModal.value = true
}

async function handleSaveStatus() {
  if (!selectedInquiry.value) return
  try {
    await inquiriesAPI.update(selectedInquiry.value.id, {
      status: statusForm.value.status,
      note: statusForm.value.note,
    })
    await fetchInquiries()
    showStatusModal.value = false
    AModal.success({ title: '更新成功' })
  } catch (e: any) {
    AModal.error({ title: '更新失败', content: e.message })
  }
}

function handleDelete(record: any) {
  AModal.confirm({
    title: '确认删除',
    content: `确定要删除此询盘记录吗？`,
    okType: 'danger',
    async onOk() {
      try {
        await inquiriesAPI.delete(record.id)
        await fetchInquiries()
        AModal.success({ title: '删除成功' })
      } catch (e: any) {
        AModal.error({ title: '删除失败', content: e.message })
      }
    },
  })
}

onMounted(() => {
  fetchInquiries()
})
</script>