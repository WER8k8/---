/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="佣金管理" subtitle="佣金记录、结算状态与本月预估" surface="elevated">
  <div class="agent-commission coachpro-tertiary coachpro-tertiary--agent">
    <section class="coachpro-kpi-grid mb-2">
      <YdStatsCard label="总佣金" :value="`¥${commissionStats.total}`" tone="blue" compact />
      <YdStatsCard label="已结算" :value="`¥${commissionStats.settled}`" tone="green" compact />
      <YdStatsCard label="待结算" :value="`¥${commissionStats.pending}`" tone="amber" compact />
      <YdStatsCard label="本月预估" :value="`¥${commissionStats.estimatedThisMonth}`" tone="purple" compact />
    </section>

    <div class="coachpro-panel p-6 mb-2">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-lg font-semibold text-gray-900">佣金记录</h3>
        <a-select v-model:value="settleFilter" placeholder="结算状态" style="width: 130px" size="small" allow-clear @change="handleFilter">
          <a-select-option value="已结算">已结算</a-select-option>
          <a-select-option value="待结算">待结算</a-select-option>
        </a-select>
      </div>
      <a-table
        :data-source="filteredRecords"
        :columns="columns"
        :pagination="{ pageSize: 8, size: 'small' }"
        size="small"
        row-key="id"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'settleStatus'">
            <a-tag :color="record.settleStatus === '已结算' ? 'green' : 'orange'">{{ record.settleStatus }}</a-tag>
          </template>
        </template>
      </a-table>
    </div>

    <!-- 结算规则说明 -->
    <div class="bg-gradient-to-br from-slate-50 to-blue-50 rounded-2xl border border-blue-100 p-6">
      <h3 class="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--uj-brand, #4a9b8c)" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/></svg>
        结算规则说明
      </h3>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div class="bg-white rounded-xl p-4 border border-gray-100">
          <p class="text-sm text-gray-400 mb-1">首次付款佣金比例</p>
          <p class="text-2xl font-bold text-blue-600">30%</p>
          <p class="text-xs text-gray-400 mt-1">客户首次付款金额的 30% 作为佣金</p>
        </div>
        <div class="bg-white rounded-xl p-4 border border-gray-100">
          <p class="text-sm text-gray-400 mb-1">续费佣金比例</p>
          <p class="text-2xl font-bold text-emerald-600">10%</p>
          <p class="text-xs text-gray-400 mt-1">客户续费金额的 10% 作为佣金</p>
        </div>
        <div class="bg-white rounded-xl p-4 border border-gray-100">
          <p class="text-sm text-gray-400 mb-1">结算周期</p>
          <p class="text-2xl font-bold text-amber-600">月度结算</p>
          <p class="text-xs text-gray-400 mt-1">每月 15 日结算上月佣金</p>
        </div>
      </div>
    </div>
  </div>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { YdPage, YdStatsCard } from '@/components/youding';
import api from '@/api/index';

function centsToYuan(cents: number): string {
  return (cents / 100).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

// ===== 佣金统计 =====
const commissionStats = ref({
  total: '0.00',
  settled: '0.00',
  pending: '0.00',
  estimatedThisMonth: '0.00',
})

// ===== 佣金记录 =====
interface CommissionRecord {
  id: number
  clientName: string
  package: string
  amount: string
  rate: string
  commission: string
  settleStatus: string
  settleTime: string
}
const settleFilter = ref<string | undefined>(undefined)
const columns = [
  { title: '客户名称', dataIndex: 'clientName', key: 'clientName' },
  { title: '套餐', dataIndex: 'package', key: 'package' },
  { title: '金额', dataIndex: 'amount', key: 'amount' },
  { title: '佣金比例', dataIndex: 'rate', key: 'rate' },
  { title: '佣金金额', dataIndex: 'commission', key: 'commission' },
  { title: '结算状态', dataIndex: 'settleStatus', key: 'settleStatus' },
  { title: '结算时间', dataIndex: 'settleTime', key: 'settleTime' },
]
const records = ref<CommissionRecord[]>([])

async function loadCommissions() {
  try {
    const res = await api.get('/finance/commissions', { params: { page: 1, page_size: 50 } })
    const body = res.data as { data?: { items?: unknown[]; stats?: Record<string, number> } }
    const payload = body.data ?? res.data
    const stats = (payload as { stats?: Record<string, number> }).stats
    if (stats) {
      commissionStats.value = {
        total: centsToYuan(Number(stats.total_cents || 0)),
        settled: centsToYuan(Number(stats.settled_cents || 0)),
        pending: centsToYuan(Number(stats.pending_cents || 0)),
        estimatedThisMonth: centsToYuan(Number(stats.pending_cents || 0)),
      }
    }
    const items = (payload as { items?: Array<Record<string, unknown>> }).items || []
    records.value = items.map((i, idx) => ({
      id: idx + 1,
      clientName: String(i.agent_node_id || '').slice(0, 12) || '代理节点',
      package: String(i.period || '—'),
      amount: `¥${centsToYuan(Number(i.revenue_cents || 0))}`,
      rate: `${(Number(i.commission_rate_bp || 0) / 100).toFixed(0)}%`,
      commission: `¥${centsToYuan(Number(i.commission_cents || 0))}`,
      settleStatus: i.status === 'settled' ? '已结算' : '待结算',
      settleTime: i.settled_at ? String(i.settled_at).slice(0, 10) : '—',
    }))
  } catch {
    /* 无数据时保持空表 */
  }
}

onMounted(() => {
  loadCommissions()
})

const filteredRecords = computed(() => {
  if (!settleFilter.value) return records.value
  return records.value.filter((r) => r.settleStatus === settleFilter.value)
})
function handleFilter() {
  // reactive
}
</script>

