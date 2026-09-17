/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="分润结算" subtitle="审核代理分润计提并标记已结算" surface="elevated">
    <template #actions>
      <YdTableToolbar
        :loading="loading"
        :target-ref="tablePanelRef"
        show-export
        @refresh="load"
        @export="exportCsv"
      />
    </template>

    <YdFinanceNav />

    <YdStatsRow :cols="3">
      <YdStatsCard label="待结算" :value="`¥${centsToYuan(stats.pending_cents)}`" tone="amber" compact />
      <YdStatsCard label="已结算" :value="`¥${centsToYuan(stats.settled_cents)}`" tone="green" compact />
      <YdStatsCard label="合计" :value="`¥${centsToYuan(stats.total_cents)}`" compact />
    </YdStatsRow>

    <a-tabs v-model:activeKey="statusFilter" class="mt-4" @change="load">
      <a-tab-pane key="pending" tab="待结算" />
      <a-tab-pane key="settled" tab="已结算" />
      <a-tab-pane key="" tab="全部" />
    </a-tabs>

    <div ref="tablePanelRef" class="yd-panel yd-table-panel">
      <YdDataTable
        :columns="columns"
        :data-source="items"
        :loading="loading"
        :pagination="{ current: 1, pageSize: 20, total }"
        :table-props="{ rowKey: 'id' }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'revenue'">
            ¥{{ centsToYuan(record.revenue_cents) }}
          </template>
          <template v-else-if="column.key === 'commission'">
            ¥{{ centsToYuan(record.commission_cents) }}
          </template>
          <template v-else-if="column.key === 'rate'">
            {{ (record.commission_rate_bp / 100).toFixed(1) }}%
          </template>
          <template v-else-if="column.key === 'status'">
            <a-tag :color="record.status === 'settled' ? 'green' : 'orange'">
              {{ record.status === 'settled' ? '已结算' : '待结算' }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'actions'">
            <a-button
              v-if="record.status === 'pending'"
              type="link"
              size="small"
              :loading="settlingId === record.id"
              @click="settle(record.id)"
            >
              标记已结算
            </a-button>
          </template>
        </template>
      </YdDataTable>
    </div>
  </YdPage>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { message } from 'ant-design-vue'

import {
  YdDataTable,
  YdFinanceNav,
  YdPage,
  YdStatsCard,
  YdStatsRow,
  YdTableToolbar,
} from '@/components/youding'
import api from '@/api'
import { downloadTableCsv } from '@/utils/exportCsv'

type Row = {
  id: string
  agent_node_id: string
  period: string
  revenue_cents: number
  commission_cents: number
  commission_rate_bp: number
  status: string
  settled_at?: string
}

const tablePanelRef = ref<HTMLElement | null>(null)
const loading = ref(false)
const settlingId = ref('')
const items = ref<Row[]>([])
const total = ref(0)
const statusFilter = ref('pending')
const stats = reactive({ pending_cents: 0, settled_cents: 0, total_cents: 0 })

const columns = [
  { title: '代理节点', dataIndex: 'agent_node_id', key: 'agent_node_id', ellipsis: true, align: 'center' as const },
  { title: '周期', dataIndex: 'period', key: 'period', width: 100, align: 'center' as const },
  { title: '营收', key: 'revenue', width: 110, align: 'center' as const },
  { title: '分润', key: 'commission', width: 110, align: 'center' as const },
  { title: '比例', key: 'rate', width: 80, align: 'center' as const },
  { title: '状态', key: 'status', width: 90, align: 'center' as const },
  { title: '结算时间', dataIndex: 'settled_at', key: 'settled_at', width: 170, align: 'center' as const },
  { title: '操作', key: 'actions', width: 120, align: 'center' as const },
]

function centsToYuan(cents: number) {
  return ((cents || 0) / 100).toFixed(2)
}

async function load() {
  loading.value = true
  try {
    const params: Record<string, string> = {}
    if (statusFilter.value) params.status = statusFilter.value
    const res = (await api.get('/finance/commissions', { params })) as {
      items?: Row[]
      total?: number
      stats?: { pending_cents: number; settled_cents: number; total_cents: number }
    }
    items.value = res?.items ?? []
    total.value = res?.total ?? items.value.length
    if (res?.stats) Object.assign(stats, res.stats)
  } finally {
    loading.value = false
  }
}

function exportCsv() {
  downloadTableCsv(
    'commissions.csv',
    ['代理节点', '周期', '营收', '分润', '比例', '状态', '结算时间'],
    items.value.map((r) => [
      r.agent_node_id,
      r.period,
      centsToYuan(r.revenue_cents),
      centsToYuan(r.commission_cents),
      `${(r.commission_rate_bp / 100).toFixed(1)}%`,
      r.status === 'settled' ? '已结算' : '待结算',
      r.settled_at || '',
    ]),
  )
}

async function settle(id: string) {
  settlingId.value = id
  try {
    await api.post(`/finance/commissions/${id}/settle`)
    message.success('已标记为已结算')
    await load()
  } catch (e: unknown) {
    const err = e as { message?: string }
    message.error(err.message || '结算失败')
  } finally {
    settlingId.value = ''
  }
}

onMounted(load)
</script>

<style scoped>
.mt-4 {
  margin-top: 16px;
}
</style>
