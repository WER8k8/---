/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="发布队列" subtitle="多平台发布任务进度 · 含 SAU 定时排期" surface="elevated">
    <section v-if="scheduledItems.length" class="scheduled-panel yd-panel">
      <header class="scheduled-head">
        <h3>定时排期（SAU / 矩阵）</h3>
        <a-button size="small" :loading="scheduledLoading" @click="loadScheduled">刷新</a-button>
      </header>
      <ul class="scheduled-list">
        <li v-for="row in scheduledItems" :key="String(row.id)">
          <span class="sch-plat">{{ row.platform_name || '—' }}</span>
          <span class="sch-time">{{ formatTime(String(row.scheduled_time)) }}</span>
          <a-tag size="small" :color="row.is_future ? 'blue' : 'default'">{{ row.status }}</a-tag>
        </li>
      </ul>
    </section>
    <YdSearchBar @search="onSearch" @reset="onReset">
      <a-input v-model:value="query.search" placeholder="任务/平台" allow-clear style="width: 180px" />
      <a-select v-model:value="query.status" placeholder="状态" allow-clear style="width: 120px">
        <a-select-option value="pending">待发布</a-select-option>
        <a-select-option value="running">进行中</a-select-option>
        <a-select-option value="done">已完成</a-select-option>
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

    <YdEmptyState v-if="!loading && !items.length" variant="product" @action="goPublish" />

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
import { onMounted, ref } from 'vue';
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
const scheduledItems = ref<Array<Record<string, unknown>>>([]);
const scheduledLoading = ref(false);

async function loadScheduled() {
  scheduledLoading.value = true;
  try {
    const data = await apiGet<{ items?: Array<Record<string, unknown>> }>('/publish/video/scheduled-queue');
    scheduledItems.value = data.items || [];
  } catch {
    scheduledItems.value = [];
  } finally {
    scheduledLoading.value = false;
  }
}

function formatTime(iso?: string) {
  if (!iso) return '—';
  try {
    return new Date(iso).toLocaleString('zh-CN', { hour12: false });
  } catch {
    return iso;
  }
}

onMounted(() => {
  void loadScheduled();
});

const baseColumns = [
  { key: 'title', title: '任务', dataIndex: 'title', align: 'center' },
  { key: 'platform', title: '平台', dataIndex: 'platform', align: 'center' },
  { key: 'status', title: '状态', dataIndex: 'status', align: 'center' },
  { key: 'scheduled_time', title: '定时', dataIndex: 'scheduled_time', align: 'center' },
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
  columnOrderKey: 'client-publish-queue-cols',
  columns: baseColumns,
  fetcher: async (q) => {
    const raw = await apiGet('/publish-tasks', {
      page: q.page,
      page_size: q.pageSize,
      search: q.search,
      status: q.status,
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

function goPublish() {
  router.push('/client/seo-publish');
}

function exportCsv() {
  if (!items.value.length) {
    message.warning('暂无数据可导出');
    return;
  }
  downloadTableCsv(
    `publish_queue_${new Date().toISOString().slice(0, 10)}.csv`,
    ['任务', '平台', '状态', '定时', '更新时间'],
    items.value.map((r) => [
      String(r.title ?? ''),
      String(r.platform ?? ''),
      String(r.status ?? ''),
      String(r.scheduled_time ?? ''),
      String(r.updated_at ?? ''),
    ]),
  );
  message.success(`已导出 ${items.value.length} 条`);
}
</script>

<style scoped>
.scheduled-panel {
  margin-bottom: 16px;
  padding: 12px 16px;
}
.scheduled-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.scheduled-head h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
}
.scheduled-list {
  margin: 0;
  padding: 0;
  list-style: none;
}
.scheduled-list li {
  display: flex;
  gap: 12px;
  align-items: center;
  padding: 6px 0;
  border-bottom: 1px dashed #e2e8f0;
  font-size: 13px;
}
.sch-plat {
  min-width: 72px;
  font-weight: 500;
}
.sch-time {
  flex: 1;
  color: #64748b;
}
</style>
