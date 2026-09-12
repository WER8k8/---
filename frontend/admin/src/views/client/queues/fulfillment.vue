<template>
  <YdPage title="履约队列" subtitle="订单与发货跟进" surface="elevated">
    <YdSearchBar @search="onSearch" @reset="onReset">
      <a-input v-model:value="query.search" placeholder="订单号/客户" allow-clear style="width: 180px" />
      <a-select v-model:value="query.status" placeholder="状态" allow-clear style="width: 120px">
        <a-select-option value="pending">待处理</a-select-option>
        <a-select-option value="shipped">已发货</a-select-option>
      </a-select>
      <template #extra>
        <YdTableColumnSettings
          :columns="orderedColumns"
          :hidden-keys="hiddenColumnKeys"
          @toggle="toggleColumnVisibility"
          @move-up="moveColumnUp"
          @move-down="moveColumnDown"
          @reset="resetColumnLayout"
        />
        <YdTableToolbar
          :loading="loading"
          :target-ref="tablePanelRef"
          show-export
          @refresh="reload"
          @export="exportCsv"
        />
      </template>
    </YdSearchBar>

    <YdEmptyState
      v-if="!loading && !items.length"
      variant="inquiry"
      title="暂无履约任务"
      @action="goInquiries"
    />

    <div v-else ref="tablePanelRef" class="yd-panel yd-table-panel">
      <YdDataTable
        :columns="visibleColumns"
        :data-source="items"
        :loading="loading"
        :pagination="pagination"
        @page-change="(p) => onPageChange(p.current, p.pageSize)"
      />
    </div>
  </YdPage>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { message } from 'ant-design-vue';

import {
  YdDataTable,
  YdEmptyState,
  YdPage,
  YdSearchBar,
  YdTableColumnSettings,
  YdTableToolbar,
} from '@/components/youding';
import { useYoudingTable } from '@/composables/useYoudingTableBridge';
import { apiGet } from '@/utils/api';
import { downloadTableCsv } from '@/utils/exportCsv';
import { adaptPaginatedResponse } from '@/utils/ydTableUtils';

const router = useRouter();
const tablePanelRef = ref<HTMLElement | null>(null);

const baseColumns = [
  { key: 'order_no', title: '订单号', dataIndex: 'order_no', align: 'center' },
  { key: 'buyer', title: '客户', dataIndex: 'buyer', align: 'center' },
  { key: 'status', title: '状态', dataIndex: 'status', align: 'center' },
  { key: 'updated_at', title: '更新时间', dataIndex: 'updated_at', align: 'center' },
];

const {
  loading,
  items,
  pagination,
  orderedColumns,
  visibleColumns,
  hiddenColumnKeys,
  query,
  search,
  reset,
  reload,
  onPageChange,
  toggleColumnVisibility,
  moveColumnUp,
  moveColumnDown,
  resetColumnLayout,
} = useYoudingTable<Record<string, unknown>, { search?: string; status?: string }>({
  columnOrderKey: 'client-fulfillment-queue-cols',
  columns: baseColumns,
  fetcher: async (q) => {
    const raw = await apiGet('/orders', {
      page: q.page,
      page_size: q.pageSize,
      search: q.search,
      status: q.status,
      role: 'merchant',
    });
    const { rows, total } = adaptPaginatedResponse<Record<string, unknown>>(raw);
    return { items: rows, total };
  },
});

function onSearch() {
  void search();
}

function onReset() {
  query.status = undefined;
  void reset();
}

function goInquiries() {
  router.push('/client/inquiries');
}

function exportCsv() {
  if (!items.value.length) {
    message.warning('暂无数据可导出');
    return;
  }
  downloadTableCsv(
    `fulfillment_queue_${new Date().toISOString().slice(0, 10)}.csv`,
    ['订单号', '客户', '状态', '更新时间'],
    items.value.map((r) => [
      String(r.order_no ?? ''),
      String(r.buyer ?? ''),
      String(r.status ?? ''),
      String(r.updated_at ?? ''),
    ]),
  );
  message.success(`已导出 ${items.value.length} 条`);
}
</script>
