<template>
  <YdPage surface="elevated">
    <div class="quotes-panel">
      <div class="flex items-center justify-between mb-6">
        <div><h2 class="text-xl font-bold text-gray-900">报价管理</h2><p class="text-sm text-gray-400">Quote 与 RFQ 联动</p></div>
        <a-button type="primary" @click="showCreate = true">+ 从 RFQ 创建报价</a-button>
      </div>
      <a-table :dataSource="items" :columns="columns" :loading="loading" :pagination="{ total, pageSize: 20, current: page }" rowKey="id" @change="handleTableChange" size="middle">
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'total'">${{ (record.total_amount || 0).toLocaleString() }} {{ record.currency }}</template>
          <template v-else-if="column.key === 'status'">
            <a-tag :color="{ draft:'default', sent:'blue', accepted:'green', expired:'orange' }[record.status as string] || 'default'">{{ record.status }}</a-tag>
          </template>
          <template v-else-if="column.key === 'action'">
            <a-button v-if="record.status === 'draft'" type="link" size="small" @click="approve(record.id)">审批</a-button>
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
const items = ref<any[]>([]); const total = ref(0); const page = ref(1); const loading = ref(false); const showCreate = ref(false)
const columns = [
  { title: '客户', dataIndex: 'merchant_id', key: 'merchant_id', width: 120 },
  { title: 'RFQ', dataIndex: 'rfq_id', key: 'rfq_id', width: 120 },
  { title: '金额', key: 'total', width: 130 },
  { title: '状态', key: 'status', width: 90 },
  { title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 170 },
  { title: '操作', key: 'action', width: 70 },
]
async function fetchData() {
  loading.value = true
  try {
    const r = await fetch(`/api/v1/quotes/?page=${page.value}&page_size=20`, { headers: authHeaders() })
    const j = await r.json()
    if (j.code === 0) { items.value = j.data.items || j.data || []; total.value = j.data.total || (j.data || []).length }
  } catch { message.error('加载失败') } finally { loading.value = false }
}
async function approve(id: string) {
  const r = await fetch(`/api/v1/quotes/${id}/status?status=sent`, { method: 'PUT', headers: { ...authHeaders(), 'Content-Type': 'application/json' } })
  const j = await r.json(); j.code === 0 ? (message.success('已发送'), fetchData()) : message.error(j.message)
}
function handleTableChange(p: any) { page.value = p.current; fetchData() }
onMounted(fetchData)
</script>
<style scoped>.quotes-panel { animation: fadeIn .3s ease; } @keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }</style>
