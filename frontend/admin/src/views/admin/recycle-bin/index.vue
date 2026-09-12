<template>
  <YdPage surface="elevated">
    <div class="recycle-bin">
      <section class="page-header">
        <div>
          <h1>回收站</h1>
          <p class="desc">已删除的内容，30 天内可恢复</p>
        </div>
        <a-button danger :disabled="!selectedRows.length" @click="batchPermanentDelete">
          永久删除选中 ({{ selectedRows.length }})
        </a-button>
      </section>

      <section class="filter-bar">
        <a-segmented v-model:value="activeTab" :options="tabOptions" @change="loadData" />
        <a-input-search
          v-model:value="searchKeyword"
          placeholder="搜索已删除内容..."
          style="max-width: 240px"
          @search="loadData"
        />
      </section>

      <section class="table-section">
        <a-table
          :columns="columns"
          :data-source="tableData"
          :loading="loading"
          :pagination="pagination"
          :row-selection="{ selectedRowKeys: selectedRows, onChange: (keys: any) => selectedRows = keys }"
          row-key="id"
          @change="handleTableChange"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'name'">
              <div class="item-name">
                <span class="item-icon">{{ getIcon(record.type) }}</span>
                <span>{{ record.name }}</span>
              </div>
            </template>
            <template v-if="column.key === 'type'">
              <a-tag :color="getTypeColor(record.type)">{{ getTypeLabel(record.type) }}</a-tag>
            </template>
            <template v-if="column.key === 'deletedAt'">
              <span class="time-ago">{{ formatTimeAgo(record.deletedAt) }}</span>
            </template>
            <template v-if="column.key === 'actions'">
              <div class="action-btns">
                <a-button size="small" type="primary" @click="restoreItem(record as TrashedItem)">
                  恢复
                </a-button>
                <a-button size="small" danger @click="permanentDeleteItem(record as TrashedItem)">
                  永久删除
                </a-button>
              </div>
            </template>
          </template>
        </a-table>
      </section>
    </div>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { message, Modal } from 'ant-design-vue'
import YdPage from '@/components/youding/YdPage.vue'
import { apiGet, apiPost, apiDelete } from '@/utils/api'

interface TrashedItem {
  id: string
  name: string
  type: 'product' | 'inquiry' | 'content'
  deletedAt: string
  originalData?: any
}

const activeTab = ref('all')
const searchKeyword = ref('')
const loading = ref(false)
const tableData = ref<TrashedItem[]>([])
const selectedRows = ref<string[]>([])
const pagination = ref({ current: 1, pageSize: 20, total: 0 })

const tabOptions = [
  { label: '全部', value: 'all' },
  { label: '产品', value: 'product' },
  { label: '询盘', value: 'inquiry' },
  { label: '内容', value: 'content' },
]

const columns = [
  { title: '名称', key: 'name', dataIndex: 'name', ellipsis: true },
  { title: '类型', key: 'type', dataIndex: 'type', width: 100 },
  { title: '删除时间', key: 'deletedAt', dataIndex: 'deletedAt', width: 160 },
  { title: '操作', key: 'actions', width: 180, fixed: 'right' as const },
]

function getIcon(type: string): string {
  const icons: Record<string, string> = { product: '📦', inquiry: '💬', content: '📝' }
  return icons[type] || '📄'
}

function getTypeColor(type: string): string {
  const colors: Record<string, string> = { product: 'blue', inquiry: 'green', content: 'orange' }
  return colors[type] || 'default'
}

function getTypeLabel(type: string): string {
  const labels: Record<string, string> = { product: '产品', inquiry: '询盘', content: '内容' }
  return labels[type] || type
}

function formatTimeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime()
  const minutes = Math.floor(diff / 60000)
  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes} 分钟前`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours} 小时前`
  const days = Math.floor(hours / 24)
  return `${days} 天前`
}

async function loadData() {
  loading.value = true
  try {
    const type = activeTab.value === 'all' ? undefined : activeTab.value
    const res = await apiGet('/recycle-bin', {
      page: pagination.value.current,
      page_size: pagination.value.pageSize,
      type,
      q: searchKeyword.value || undefined,
    })
    tableData.value = (res as any).items || []
    pagination.value.total = (res as any).total || 0
  } catch {
    tableData.value = []
  } finally {
    loading.value = false
  }
}

async function restoreItem(item: TrashedItem) {
  try {
    await apiPost(`/recycle-bin/${item.type}/${item.id}/restore`)
    message.success(`已恢复「${item.name}」`)
    loadData()
  } catch (e: any) {
    message.error(`恢复失败: ${e.message}`)
  }
}

function permanentDeleteItem(item: TrashedItem) {
  Modal.confirm({
    title: '永久删除',
    content: `确定要永久删除「${item.name}」吗？此操作不可撤销。`,
    okType: 'danger',
    okText: '永久删除',
    cancelText: '取消',
    async onOk() {
      try {
        await apiDelete(`/recycle-bin/${item.type}/${item.id}`)
        message.success('已永久删除')
        loadData()
      } catch (e: any) {
        message.error(`删除失败: ${e.message}`)
      }
    },
  })
}

function batchPermanentDelete() {
  Modal.confirm({
    title: '批量永久删除',
    content: `确定要永久删除选中的 ${selectedRows.value.length} 项吗？此操作不可撤销。`,
    okType: 'danger',
    okText: '全部永久删除',
    cancelText: '取消',
    async onOk() {
      try {
        await apiPost('/recycle-bin/batch-delete', { ids: selectedRows.value })
        message.success(`已永久删除 ${selectedRows.value.length} 项`)
        selectedRows.value = []
        loadData()
      } catch (e: any) {
        message.error(`删除失败: ${e.message}`)
      }
    },
  })
}

function handleTableChange(pag: any) {
  pagination.value.current = pag.current
  pagination.value.pageSize = pag.pageSize
  loadData()
}

onMounted(loadData)
</script>

<style scoped>
.recycle-bin {
  max-width: 1200px;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.page-header h1 {
  font-size: 20px;
  font-weight: 700;
  color: #111827;
  margin: 0;
}

.desc {
  font-size: 13px;
  color: #6b7280;
  margin: 4px 0 0;
}

.filter-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.table-section {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  overflow: hidden;
}

.item-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

.item-icon {
  font-size: 16px;
}

.time-ago {
  color: #6b7280;
  font-size: 13px;
}

.action-btns {
  display: flex;
  gap: 8px;
}
</style>
