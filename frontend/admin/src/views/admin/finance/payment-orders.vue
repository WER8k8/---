<template>
  <YdPage title="租户支付订单" subtitle="全平台租户付款单 · 与分润/财务台账同源" surface="elevated">
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

    <a-space wrap class="mb-4">
      <a-select
        v-model:value="statusFilter"
        allow-clear
        placeholder="订单状态"
        style="min-width: 140px"
        @change="load"
      >
        <a-select-option value="paid">已支付</a-select-option>
        <a-select-option value="pending">待支付</a-select-option>
        <a-select-option value="failed">失败</a-select-option>
        <a-select-option value="cancelled">已取消</a-select-option>
      </a-select>
    </a-space>

    <div ref="tablePanelRef" class="yd-panel yd-table-panel">
      <YdDataTable
        :columns="columns"
        :data-source="items"
        :loading="loading"
        :pagination="{ current: 1, pageSize: 100, total }"
        :table-props="{ rowKey: 'id' }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'amount'">
            ¥{{ centsToYuan(record.amount) }}
          </template>
          <template v-else-if="column.key === 'status'">
            <a-tag :color="statusColor(record.status)">{{ statusLabel(record.status) }}</a-tag>
          </template>
        </template>
      </YdDataTable>
    </div>
  </YdPage>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { YdPage, YdDataTable, YdTableToolbar } from '@/components/youding';
import YdFinanceNav from '@/components/youding/YdFinanceNav.vue';
import { apiGet } from '@/utils/api';

type OrderRow = {
  id: string;
  order_no: string;
  tenant_id: string;
  tenant_name: string;
  amount: number;
  channel: string;
  subject: string;
  status: string;
  paid_at?: string;
  created_at: string;
};

const loading = ref(false);
const items = ref<OrderRow[]>([]);
const total = ref(0);
const statusFilter = ref<string | undefined>(undefined);
const tablePanelRef = ref<HTMLElement | null>(null);

const columns = [
  { title: '订单号', dataIndex: 'order_no', key: 'order_no', width: 200 },
  { title: '租户', dataIndex: 'tenant_name', key: 'tenant_name', width: 160 },
  { title: '主题', dataIndex: 'subject', key: 'subject', ellipsis: true },
  { title: '金额', key: 'amount', width: 100 },
  { title: '渠道', dataIndex: 'channel', key: 'channel', width: 90 },
  { title: '状态', key: 'status', width: 100 },
  { title: '支付时间', dataIndex: 'paid_at', key: 'paid_at', width: 170 },
  { title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 170 },
];

function centsToYuan(cents: number) {
  return (Number(cents || 0) / 100).toFixed(2);
}

function statusLabel(s: string) {
  const map: Record<string, string> = {
    paid: '已支付',
    pending: '待支付',
    failed: '失败',
    cancelled: '已取消',
  };
  return map[s] || s;
}

function statusColor(s: string) {
  const map: Record<string, string> = {
    paid: 'green',
    pending: 'orange',
    failed: 'red',
    cancelled: 'default',
  };
  return map[s] || 'default';
}

async function load() {
  loading.value = true;
  try {
    const data = await apiGet<OrderRow[]>('/payment/orders', {
      page: 1,
      page_size: 100,
      status: statusFilter.value || undefined,
    });
    items.value = Array.isArray(data) ? data : [];
    total.value = items.value.length;
  } finally {
    loading.value = false;
  }
}

function exportCsv() {
  const header = ['订单号', '租户', '主题', '金额(元)', '渠道', '状态', '支付时间', '创建时间'];
  const rows = items.value.map((r) => [
    r.order_no,
    r.tenant_name,
    r.subject,
    centsToYuan(r.amount),
    r.channel,
    statusLabel(r.status),
    r.paid_at || '',
    r.created_at,
  ]);
  const csv = [header, ...rows].map((row) => row.map((c) => `"${String(c).replace(/"/g, '""')}"`).join(',')).join('\n');
  const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `payment-orders-${Date.now()}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

onMounted(() => {
  void load();
});
</script>
