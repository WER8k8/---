/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage surface="elevated">
    <div class="rfq-panel">
      <div class="flex items-center justify-between mb-6">
        <div><h2 class="text-xl font-bold text-gray-900">RFQ 需求单</h2><p class="text-sm text-gray-400">共 {{ total }} 条 | 高意向 {{ highIntent }}</p></div>
        <a-input-search v-model:value="searchText" placeholder="搜索公司/邮箱/应用" style="width:240px" @search="fetchData" />
      </div>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div class="stat bg-blue-600"><p class="text-xs text-white/70">总数</p><p class="text-2xl font-bold text-white">{{ total }}</p></div>
        <div class="stat bg-emerald-600"><p class="text-xs text-white/70">高意向 (≥60)</p><p class="text-2xl font-bold text-white">{{ highIntent }}</p></div>
        <div class="stat bg-amber-500"><p class="text-xs text-white/70">未分配</p><p class="text-2xl font-bold text-white">{{ unassigned }}</p></div>
        <div class="stat bg-purple-600"><p class="text-xs text-white/70">平均分</p><p class="text-2xl font-bold text-white">{{ avgScore }}</p></div>
      </div>
      <a-table :dataSource="items" :columns="columns" :loading="loading" :pagination="{ total, pageSize: 20, current: page }" rowKey="id" @change="handleTableChange" size="middle">
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'score'">
            <a-tag :color="record.rfq_score >= 60 ? 'success' : record.rfq_score >= 40 ? 'orange' : 'default'">{{ record.rfq_score }}</a-tag>
          </template>
          <template v-else-if="column.key === 'status'">
            <a-select :value="record.status" size="small" style="width:130px" @change="(v) => updateStatus(record.id, v as string)">
              <a-select-option value="pending">待处理</a-select-option>
              <a-select-option value="qualified">已合格</a-select-option>
              <a-select-option value="contacted">已联系</a-select-option>
              <a-select-option value="engaged">已互动</a-select-option>
              <a-select-option value="quoting">报价中</a-select-option>
              <a-select-option value="won">已成交</a-select-option>
              <a-select-option value="lost">已流失</a-select-option>
            </a-select>
          </template>
          <template v-else-if="column.key === 'action'">
            <a-button type="link" size="small" @click="createOpp(record)">转机会</a-button>
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
const items = ref<any[]>([])
const total = ref(0); const highIntent = ref(0); const unassigned = ref(0); const avgScore = ref(0)
const page = ref(1); const loading = ref(false); const searchText = ref('')

const columns = [
  { title: '公司', dataIndex: 'company', key: 'company', width: 170 },
  { title: '国家', dataIndex: 'country', key: 'country', width: 80 },
  { title: '应用', dataIndex: 'application', key: 'application', width: 140 },
  { title: '联系人', dataIndex: 'contact_name', key: 'contact_name', width: 100 },
  { title: '评分', key: 'score', width: 70 },
  { title: '状态', key: 'status', width: 140 },
  { title: '操作', key: 'action', width: 70 },
]

async function fetchData() {
  loading.value = true
  try {
    const params = new URLSearchParams({ page: String(page.value), page_size: '20' })
    if (searchText.value) params.set('search', searchText.value)
    const [list, stats] = await Promise.all([
      fetch(`/api/v1/rfq?${params}`, { headers: authHeaders() }),
      fetch('/api/v1/rfq/stats', { headers: authHeaders() }),
    ])
    const l = await list.json(); const s = await stats.json()
    if (l.code === 0) { items.value = l.data.items; total.value = l.data.total }
    if (s.code === 0) { highIntent.value = s.data.high_intent; unassigned.value = s.data.unassigned; avgScore.value = total.value ? Math.round((l.data.items.reduce((a:any,b:any)=>a+b.rfq_score,0))/ (l.data.items.length||1)) : 0 }
  } catch { message.error('加载失败') } finally { loading.value = false }
}

async function updateStatus(id: string, status: string) {
  const r = await fetch(`/api/v1/rfq/${id}/status`, { method: 'PUT', headers: { ...authHeaders(), 'Content-Type': 'application/json' }, body: JSON.stringify({ status }) })
  const j = await r.json(); j.code === 0 ? (message.success('已更新'), fetchData()) : message.error(j.message)
}

async function createOpp(record: any) {
  const r = await fetch('/api/v1/opportunity', { method: 'POST', headers: { ...authHeaders(), 'Content-Type': 'application/json' }, body: JSON.stringify({ name: record.project || record.application, rfq_id: record.id, company: record.company, contact_name: record.contact_name, contact_email: record.email, value: 0, country: record.country, application: record.application, stage: 'Qualified' }) })
  const j = await r.json(); j.code === 0 ? message.success('已转机会') : message.error(j.message)
}

function handleTableChange(p: any) { page.value = p.current; fetchData() }
onMounted(fetchData)
</script>
<style scoped>
.rfq-panel { animation: fadeIn .3s ease; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
.stat { padding: 1rem; border-radius: 12px; }
</style>
