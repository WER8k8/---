/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="财务中台" subtitle="营收 / 成本 / 分润 / 净利润（单位：元）" surface="elevated">
    <template #actions>
      <YdTableToolbar
        :loading="loading"
        show-density
        :show-fullscreen="false"
        show-export
        @refresh="load"
        @export="exportCsv"
      />
    </template>

    <YdFinanceNav />

    <template v-if="loading">
      <div class="mb-4">
        <SkeletonCard variant="kpi" />
      </div>
      <SkeletonCard variant="table" :rows="5" />
    </template>
    <template v-else>
      <a-alert
        type="info"
        show-icon
        class="mb-4"
        message="收款与支付接口"
        description="更换微信/支付宝商户、查看收款二维码探针、配置回调地址，请进入「支付码与接口」；全平台付款单见「租户支付订单」；静态 IP 池使用率见「静态 IP 池」。"
      >
        <template #action>
          <a-button size="small" type="primary" @click="router.push('/admin/finance/payment-ops')">
            支付码与接口
          </a-button>
        </template>
      </a-alert>

      <a-alert
        v-if="summary && summary.revenue_cents <= 0"
        type="info"
        show-icon
        class="mb-4"
        message="暂无实收记录"
        description="营收仅统计支付成功写入财务台账或已付款订单；未上线或未发生真实付款时，各指标为 0，不会用套餐价冒充收入。"
      />

      <YdStatsRow :cols="3">
        <YdStatsCard
          v-for="card in cards"
          :key="card.key"
          :label="card.label"
          :value="card.value"
          :tone="card.tone"
          compact
        />
      </YdStatsRow>

      <div ref="topTableRef" class="yd-panel yd-table-panel mt-4">
        <div class="panel-head">
          <span class="panel-title">营收 Top 租户</span>
          <YdTableToolbar
            :show-density="false"
            :show-refresh="false"
            :target-ref="topTableRef"
          />
        </div>
        <YdDataTable
          :columns="topColumns"
          :data-source="topTenants"
          :pagination="false"
          :table-props="{ rowKey: 'tenant_id' }"
        />
      </div>

      <div ref="expTableRef" class="yd-panel yd-table-panel mt-4">
        <div class="panel-head">
          <span class="panel-title">7 日内到期租户</span>
          <YdTableToolbar
            :loading="loadingExpiring"
            :show-density="false"
            :target-ref="expTableRef"
            @refresh="loadExpiring"
          />
        </div>
        <YdDataTable
          :columns="expiringCols"
          :data-source="expiringTenants"
          :loading="loadingExpiring"
          :pagination="false"
          :table-props="{ rowKey: 'id' }"
        />
      </div>
    </template>
  </YdPage>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { message } from 'ant-design-vue';

import {
  YdDataTable,
  YdFinanceNav,
  YdPage,
  YdStatsCard,
  YdStatsRow,
  YdTableToolbar,
} from '@/components/youding';
import api from '@/api';
import SkeletonCard from '@/components/common/SkeletonCard.vue';

const router = useRouter();

type Summary = {
  revenue_cents: number;
  cost_cents: number;
  profit_cents: number;
  commission_settled_cents?: number;
  commission_pending_cents?: number;
  net_profit_cents?: number;
  top_tenants_by_revenue?: { tenant_id: string; revenue_cents: number }[];
};

const loading = ref(false);
const loadingExpiring = ref(false);
const summary = ref<Summary | null>(null);
const expiringTenants = ref<{ id: string; name: string; expires_at: string; status: string }[]>([]);
const topTableRef = ref<HTMLElement | null>(null);
const expTableRef = ref<HTMLElement | null>(null);

const expiringCols = [
  { title: '租户', dataIndex: 'name', key: 'name', ellipsis: true, align: 'center' as const },
  { title: '状态', dataIndex: 'status', key: 'status', width: 80, align: 'center' as const },
  { title: '到期时间', dataIndex: 'expires_at', key: 'expires_at', width: 180, align: 'center' as const },
];

const topColumns = [
  { title: '租户 ID', dataIndex: 'tenant_id', key: 'tenant_id', ellipsis: true, align: 'center' as const },
  { title: '营收（元）', dataIndex: 'revenue_yuan', key: 'revenue_yuan', align: 'center' as const },
];

function centsToYuan(cents: number) {
  return (cents / 100).toFixed(2);
}

const cards = computed(() => {
  const s = summary.value;
  if (!s) return [];
  return [
    { key: 'rev', label: '营收', value: centsToYuan(s.revenue_cents), tone: 'green' as const },
    { key: 'cost', label: '成本', value: centsToYuan(s.cost_cents), tone: 'amber' as const },
    { key: 'profit', label: '毛利', value: centsToYuan(s.profit_cents), tone: 'blue' as const },
    { key: 'comm', label: '已结分润', value: centsToYuan(s.commission_settled_cents || 0), tone: 'purple' as const },
    { key: 'pend', label: '待结分润', value: centsToYuan(s.commission_pending_cents || 0), tone: 'default' as const },
    { key: 'net', label: '净利润', value: centsToYuan(s.net_profit_cents ?? s.profit_cents), tone: 'default' as const },
  ];
});

const topTenants = computed(() =>
  (summary.value?.top_tenants_by_revenue ?? []).map((row) => ({
    ...row,
    revenue_yuan: centsToYuan(row.revenue_cents),
  })),
);

async function loadExpiring() {
  loadingExpiring.value = true;
  try {
    const exp = (await api.get('/finance/expiring-tenants')) as { tenants?: typeof expiringTenants.value };
    expiringTenants.value = exp?.tenants ?? [];
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '加载到期租户失败');
  } finally {
    loadingExpiring.value = false;
  }
}

async function load() {
  loading.value = true;
  try {
    const res = await api.get('/finance/summary');
    summary.value = ((res as { data?: Summary }).data ?? res) as Summary ?? null;
    await loadExpiring();
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '加载失败');
  } finally {
    loading.value = false;
  }
}

async function exportCsv() {
  try {
    const res = await api.get('/finance/export.csv', { responseType: 'blob' });
    const blob = new Blob([res.data], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'finance_ledger.csv';
    a.click();
    URL.revokeObjectURL(url);
    message.success('财务 CSV 已下载');
  } catch {
    message.error('导出失败');
  }
}

onMounted(load);
</script>

<style scoped>
.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.panel-title {
  font-size: 14px;
  font-weight: 600;
}
.mt-4 {
  margin-top: 16px;
}
</style>
