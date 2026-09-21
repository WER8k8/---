/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage
    class="analytics-glass"
    title="数据分析"
    subtitle="与 API §9 对齐：概览、仪表盘、流量与审计日志"
    surface="elevated"
  >
    <template #actions>
      <a-button
        type="primary"
        ghost
        :loading="summaryLoading"
        @click="loadSummary"
      >
        刷新数据
      </a-button>
    </template>

    <a-alert
      v-if="summaryError"
      type="warning"
      show-icon
      class="mb-4 rounded-2xl"
      :message="summaryError"
    />

    <a-row
      :gutter="16"
      class="mb-6"
    >
      <a-col :span="6">
        <a-card class="kpi-card text-center border-0 shadow-lg shadow-slate-200/50">
          <div class="text-3xl font-bold text-primary">
            {{ formatInt(kpi.visitors) }}
          </div>
          <div class="text-gray-500 mt-2">
            总访客
          </div>
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card class="kpi-card text-center border-0 shadow-lg shadow-emerald-200/40">
          <div class="text-3xl font-bold text-emerald-600">
            {{ formatInt(kpi.inquiries) }}
          </div>
          <div class="text-gray-500 mt-2">
            询盘数量
          </div>
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card class="kpi-card text-center border-0 shadow-lg shadow-violet-200/40">
          <div class="text-3xl font-bold text-violet-600">
            {{ kpi.contentAssets }}
          </div>
          <div class="text-gray-500 mt-2">
            内容条目
          </div>
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card class="kpi-card text-center border-0 shadow-lg shadow-amber-200/40">
          <div class="text-3xl font-bold text-amber-600">
            {{ kpi.bounceText }}
          </div>
          <div class="text-gray-500 mt-2">
            跳出率
          </div>
        </a-card>
      </a-col>
    </a-row>

    <a-row :gutter="16">
      <a-col :span="16">
        <a-card
          title="访问趋势"
          class="chart-card border-0 shadow-lg"
        >
          <div class="h-64">
            <v-chart
              :option="visitChartOption"
              autoresize
            />
          </div>
        </a-card>
      </a-col>
      <a-col :span="8">
        <a-card
          title="流量来源"
          class="chart-card border-0 shadow-lg"
        >
          <div class="h-64">
            <v-chart
              :option="sourceChartOption"
              autoresize
            />
          </div>
        </a-card>
      </a-col>
    </a-row>

    <a-card
      title="操作日志"
      class="mt-6 chart-card border-0 shadow-lg"
    >
      <div ref="logTablePanelRef" class="yd-table-panel">
        <div class="table-toolbar-row mb-3">
          <YdTableToolbar
            :loading="loading"
            :target-ref="logTablePanelRef"
            :show-export="false"
            @refresh="() => fetchLogs()"
          />
        </div>
        <YdDataTable
          :columns="logColumns"
          :data-source="logs"
          :pagination="logTablePagination"
          :loading="loading"
          :table-props="{ rowKey: logRowKey, size: tableSize }"
          @page-change="onLogPageChange"
        >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'action'">
            <a-tag :color="getActionColor(record.action)">
              {{ getActionText(record.action) }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'created_at'">
            {{ record.created_at ? formatDate(record.created_at) : '-' }}
          </template>
        </template>
        </YdDataTable>
      </div>
    </a-card>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { storeToRefs } from 'pinia';
import { YdDataTable, YdPage, YdTableToolbar } from '@/components/youding';
import { useUiPreferencesStore } from '@/stores/uiPreferences';
import {
  Card as ACard,
  Tag as ATag,
  Row as ARow,
  Col as ACol,
  Button as AButton,
  Alert as AAlert,
} from 'ant-design-vue';
import VChart from 'vue-echarts';
import { applySnapCursor } from '@/composables/useChartCursor';
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { LineChart, PieChart } from 'echarts/charts';
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
} from 'echarts/components';
import { systemAPI, dataAnalyticsAPI } from '@/api';

use([
  CanvasRenderer,
  LineChart,
  PieChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
]);

const logs = ref<any[]>([]);
const loading = ref(false);
const logTablePanelRef = ref<HTMLElement | null>(null);
const ui = useUiPreferencesStore();
const { antTableSize: tableSize } = storeToRefs(ui);
const summaryLoading = ref(false);
const summaryError = ref('');

const overview = ref<{
  total_visitors?: number;
  page_views?: number;
  bounce_rate?: number;
  avg_session_duration?: string;
} | null>(null);

/** GET `/analytics` 扁平化后的完整体（含 conversions、traffic_sources） */
const analyticsSummary = ref<Record<string, unknown> | null>(null);

const dashboard = ref<{
  inquiries?: { total?: number };
  content?: { total_products?: number; total_cases?: number; total_pages?: number };
} | null>(null);

const trafficSeries = ref<{ labels: string[]; values: number[] } | null>(null);
const sourceBreakdown = ref<{ name: string; value: number }[] | null>(null);

const logPagination = ref({
  current: 1,
  pageSize: 10,
  total: 0,
});

const logTablePagination = computed(() => ({
  current: logPagination.value.current,
  pageSize: logPagination.value.pageSize,
  total: logPagination.value.total,
}));

const logColumns = [
  { title: '用户名', dataIndex: 'username', key: 'username', width: 120 },
  { title: '操作', key: 'action', width: 150 },
  { title: '资源类型', dataIndex: 'resource_type', key: 'resource_type', width: 120 },
  { title: 'IP地址', dataIndex: 'ip_address', key: 'ip_address', width: 150 },
  { title: '时间', key: 'created_at', width: 180 },
];

const kpi = computed(() => {
  const o = overview.value || {};
  const d = dashboard.value || {};
  const root = analyticsSummary.value || {};
  const conv = root.conversions as { inquiries?: number } | undefined;
  const content = d.content || {};
  const assets =
    (content.total_products ?? 0) + (content.total_cases ?? 0) + (content.total_pages ?? 0);
  const inquiries = d.inquiries?.total ?? conv?.inquiries;
  return {
    visitors: o.total_visitors ?? o.page_views ?? 0,
    inquiries: typeof inquiries === 'number' ? inquiries : 0,
    contentAssets: assets,
    bounceText: typeof o.bounce_rate === 'number' ? `${o.bounce_rate.toFixed(1)}%` : '—',
  };
});

const visitChartOption = computed(() => {
  const t = trafficSeries.value;
  const labels = t?.labels?.length ? t.labels : [];
  const values = t?.values?.length ? t.values : [];
  // 磁吸游标：折线图吸附最近数据点（配置见 @/composables/useChartCursor）
  return applySnapCursor({
    tooltip: { trigger: 'axis' },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', boundaryGap: false, data: labels },
    yAxis: { type: 'value' },
    series: [
      {
        name: '访问量',
        type: 'line',
        data: values,
        smooth: true,
        lineStyle: { color: '#0ea5e9' },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(14, 165, 233, 0.35)' },
              { offset: 1, color: 'rgba(14, 165, 233, 0.05)' },
            ],
          },
        },
      },
    ],
  });
});

const sourceChartOption = computed(() => {
  const src = sourceBreakdown.value?.length ? sourceBreakdown.value : [];
  return {
    tooltip: { trigger: 'item' },
    legend: { orient: 'vertical', left: 'left' },
    series: [
      {
        name: '流量来源',
        type: 'pie',
        radius: '50%',
        data: src,
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)',
          },
        },
      },
    ],
  };
});

function formatInt(n: number) {
  if (n == null || Number.isNaN(n)) return '—';
  return n.toLocaleString('zh-CN');
}

function getActionColor(action: string) {
  if (action.includes('CREATE')) return 'green';
  if (action.includes('UPDATE')) return 'blue';
  if (action.includes('DELETE')) return 'red';
  return 'default';
}

function getActionText(action: string) {
  const actionMap: Record<string, string> = {
    CREATE_PRODUCT: '创建产品',
    UPDATE_PRODUCT: '更新产品',
    DELETE_PRODUCT: '删除产品',
    CREATE_CONTENT: '创建内容',
    UPDATE_CONTENT: '更新内容',
    DELETE_CONTENT: '删除内容',
    LOGIN: '登录',
    LOGOUT: '登出',
  };
  return actionMap[action] || action;
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleString('zh-CN');
}

function logRowKey(record: Record<string, unknown>, index?: number) {
  const id = record?.id;
  if (id != null && id !== '') return String(id);
  return `${record?.username ?? 'u'}-${record?.created_at ?? index}-${index}`;
}

function parseTrafficPayload(raw: unknown) {
  if (!raw || typeof raw !== 'object') return;
  const r = raw as Record<string, unknown>;
  const data = r.data;
  if (!Array.isArray(data) || data.length === 0) return;
  const first = data[0] as Record<string, unknown>;
  if (typeof first.date === 'string' && typeof first.views === 'number') {
    trafficSeries.value = {
      labels: data.map((x: any) => x.date),
      values: data.map((x: any) => x.views),
    };
    return;
  }
  if (typeof first.label === 'string' && typeof first.value === 'number') {
    trafficSeries.value = {
      labels: data.map((x: any) => x.label),
      values: data.map((x: any) => x.value),
    };
  }
}

function parseSourcesFromOverview(raw: unknown) {
  if (!raw || typeof raw !== 'object') return;
  const ts = (raw as { traffic_sources?: unknown }).traffic_sources;
  if (!Array.isArray(ts) || ts.length === 0) return;
  const mapped = ts
    .map((item: any) => {
      if (typeof item === 'object' && item !== null) {
        const name = item.name ?? item.source ?? item.label;
        const value = item.value ?? item.count ?? item.share;
        if (typeof name === 'string' && typeof value === 'number') {
          return { name, value };
        }
      }
      return null;
    })
    .filter(Boolean) as { name: string; value: number }[];
  if (mapped.length) sourceBreakdown.value = mapped;
}

async function loadSummary() {
  summaryLoading.value = true;
  summaryError.value = '';
  try {
    const [listRes, dashRes, trafficRes] = await Promise.all([
      dataAnalyticsAPI.list(),
      dataAnalyticsAPI.dashboard(),
      dataAnalyticsAPI.traffic({ period: '7d' }),
    ]);
    const listData = listRes.data as Record<string, unknown> | undefined;
    analyticsSummary.value = listData && typeof listData === 'object' ? listData : null;
    overview.value = (listData?.overview as typeof overview.value) ?? null;
    if (listData && typeof listData === 'object') {
      parseSourcesFromOverview(listData);
    }
    dashboard.value = (dashRes.data as any) ?? null;
    parseTrafficPayload(trafficRes.data);
  } catch (e: any) {
    summaryError.value =
      e?.response?.data?.message || e?.message || '加载分析数据失败（请检查权限与网络）';
  } finally {
    summaryLoading.value = false;
  }
}

async function fetchLogs(page = 1, pageSize?: number) {
  loading.value = true;
  logPagination.value.current = page;
  const ps = pageSize ?? logPagination.value.pageSize;
  try {
    const res = await systemAPI.auditLogs({ page, page_size: ps });
    const d = res.data as { items?: unknown[]; data?: unknown[]; total?: number };
    const rows = Array.isArray(d?.items) ? d.items : Array.isArray(d?.data) ? d.data : [];
    logs.value = rows;
    logPagination.value.total = d?.total ?? rows.length;
    logPagination.value.pageSize = ps;
  } catch (e) {
    if (import.meta.env.DEV) console.error('Failed to fetch logs:', e);
  } finally {
    loading.value = false;
  }
}

function onLogPageChange(p: { current: number; pageSize: number }) {
  void fetchLogs(p.current, p.pageSize);
}

onMounted(() => {
  loadSummary();
  fetchLogs();
});
</script>

<style scoped>
.analytics-glass {
  min-height: 100%;
}

.kpi-card,
.chart-card {
  border-radius: 1.25rem;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(12px);
}
</style>
