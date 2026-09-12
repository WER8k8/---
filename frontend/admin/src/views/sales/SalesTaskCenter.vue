<template>
  <YdPage surface="elevated">
    <div class="task-center">
      <div class="flex items-center justify-between mb-6">
        <div><h2 class="text-xl font-bold text-gray-900">销售任务中心</h2><p class="text-sm text-gray-400">RFQ 响应 / 报价审批 / 跟进提醒</p></div>
        <a-select v-model:value="filterStatus" placeholder="筛选状态" allow-clear style="width:140px" @change="fetchData">
          <a-select-option value="open">待处理</a-select-option>
          <a-select-option value="done">已完成</a-select-option>
          <a-select-option value="cancelled">已取消</a-select-option>
        </a-select>
      </div>
      <a-table :dataSource="items" :columns="columns" :loading="loading" :pagination="{ total, pageSize: 20, current: page }" rowKey="id" @change="handleTableChange" size="middle">
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'priority'">
            <a-tag :color="{ high:'red', normal:'blue', low:'default' }[record.priority as string] || 'default'">{{ record.priority }}</a-tag>
          </template>
          <template v-else-if="column.key === 'status'">
            <a-select :value="record.status" size="small" style="width:110px" @change="(v) => updateStatus(record.id, v as string)">
              <a-select-option value="open">待处理</a-select-option>
              <a-select-option value="done">已完成</a-select-option>
              <a-select-option value="cancelled">已取消</a-select-option>
            </a-select>
          </template>
        </template>
      </a-table>
    </div>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { YdPage } from '@/components/youding'
import { message } from 'ant-design-vue'
const authHeaders = () => ({ Authorization: `Bearer ${localStorage.getItem('admin_token') || sessionStorage.getItem('admin_token')}` })
const items = ref<any[]>([]); const total = ref(0); const page = ref(1); const loading = ref(false); const filterStatus = ref<string | undefined>(undefined)
const columns = [
  { title: '任务', dataIndex: 'title', key: 'title', width: 280 },
  { title: '类型', dataIndex: 'task_type', key: 'task_type', width: 110 },
  { title: '优先级', key: 'priority', width: 80 },
  { title: '状态', key: 'status', width: 120 },
  { title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 170 },
]
async function fetchData() {
  loading.value = true
  try {
    const params = new URLSearchParams({ page: String(page.value), page_size: '20' })
    if (filterStatus.value) params.set('status', filterStatus.value)
    const r = await fetch(`/api/v1/tasks?${params}`, { headers: authHeaders() })
    const j = await r.json()
    if (j.code === 0) { items.value = j.data.items; total.value = j.data.total }
  } catch { message.error('加载失败') } finally { loading.value = false }
}
async function updateStatus(id: string, status: string) {
  const r = await fetch(`/api/v1/tasks/${id}/status`, { method: 'PUT', headers: { ...authHeaders(), 'Content-Type': 'application/json' }, body: JSON.stringify({ status }) })
  const j = await r.json(); j.code === 0 ? (message.success('已更新'), fetchData()) : message.error(j.message)
}
function handleTableChange(p: any) { page.value = p.current; fetchData() }
onMounted(fetchData)
</script>
<style scoped>.task-center { animation: fadeIn .3s ease; } @keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }</style>
