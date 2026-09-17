/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage surface="elevated">
    <div class="company-360">
      <div class="flex items-center justify-between mb-6">
        <div><h2 class="text-xl font-bold text-gray-900">Company 360 / Account 360</h2><p class="text-sm text-gray-400">目标公司主数据与采购信号</p></div>
        <a-button type="primary" @click="showCreate = true">+ 新建公司</a-button>
      </div>
      <a-table :dataSource="items" :columns="columns" :loading="loading" :pagination="{ total, pageSize: 20, current: page }" rowKey="id" @change="handleTableChange" size="middle">
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'scores'">
            <a-tag color="blue">ICP {{ record.icp_score }}</a-tag>
            <a-tag :color="record.intent_score >= 30 ? 'success' : 'default'">Intent {{ record.intent_score }}</a-tag>
            <a-tag color="purple">Account {{ record.account_score }}</a-tag>
          </template>
          <template v-else-if="column.key === 'contacts'">{{ record.contacts?.length || 0 }}</template>
          <template v-else-if="column.key === 'signals'">{{ record.signals?.length || 0 }}</template>
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
const items = ref<any[]>([]); const total = ref(0); const page = ref(1); const loading = ref(false)
const showCreate = ref(false)
const columns = [
  { title: '公司', dataIndex: 'name', key: 'name', width: 180 },
  { title: '域名', dataIndex: 'domain', key: 'domain', width: 150 },
  { title: '国家', dataIndex: 'country', key: 'country', width: 90 },
  { title: '行业', dataIndex: 'industry', key: 'industry', width: 140 },
  { title: '评分', key: 'scores', width: 150 },
  { title: '联系人', key: 'contacts', width: 70 },
  { title: '信号', key: 'signals', width: 60 },
]
async function fetchData() {
  loading.value = true
  try {
    const r = await fetch(`/api/v1/company?page=${page.value}&page_size=20`, { headers: authHeaders() })
    const j = await r.json()
    if (j.code === 0) { items.value = j.data.items; total.value = j.data.total }
  } catch { message.error('加载失败') } finally { loading.value = false }
}
function handleTableChange(p: any) { page.value = p.current; fetchData() }
onMounted(fetchData)
</script>
<style scoped>.company-360 { animation: fadeIn .3s ease; } @keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }</style>
