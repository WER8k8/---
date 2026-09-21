/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="space-y-6 animate-fade-in">
    <div class="flex items-center justify-between">
      <div class="flex flex-col">
        <h1 class="text-3xl font-bold text-gray-900">
          SEO概览
        </h1>
        <p class="text-gray-500 mt-1">
          实时监控网站SEO表现和关键词排名
        </p>
      </div>
      <a-button
        type="primary"
        class="gradient-primary shadow-md"
        @click="refreshData"
      >
        <ReloadOutlined class="w-4 h-4 mr-2" />
        刷新数据
      </a-button>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
      <div
        class="stat-card bg-gradient-to-br from-green-500 to-green-600 text-white cursor-pointer hover:shadow-lg hover:shadow-green-500/30"
      >
        <div class="absolute top-0 right-0 w-24 h-24 bg-white/10 rounded-full -mr-8 -mt-8" />
        <div class="relative z-10 flex items-center justify-between">
          <div>
            <p class="text-green-100 text-sm font-medium">
              总关键词数
            </p>
            <p class="text-3xl font-bold mt-2">
              {{ stats.total_keywords || 0 }}
            </p>
          </div>
          <div class="w-14 h-14 bg-white/20 rounded-2xl flex items-center justify-center">
            <SearchOutlined class="w-7 h-7" />
          </div>
        </div>
      </div>

      <div
        class="stat-card bg-gradient-to-br from-blue-500 to-blue-600 text-white cursor-pointer hover:shadow-lg hover:shadow-blue-500/30"
      >
        <div class="absolute top-0 right-0 w-24 h-24 bg-white/10 rounded-full -mr-8 -mt-8" />
        <div class="relative z-10 flex items-center justify-between">
          <div>
            <p class="text-blue-100 text-sm font-medium">
              已排名关键词
            </p>
            <p class="text-3xl font-bold mt-2">
              {{ stats.ranked_keywords || 0 }}
            </p>
          </div>
          <div class="w-14 h-14 bg-white/20 rounded-2xl flex items-center justify-center">
            <ArrowUpOutlined class="w-7 h-7" />
          </div>
        </div>
      </div>

      <div
        class="stat-card bg-gradient-to-br from-purple-500 to-purple-600 text-white cursor-pointer hover:shadow-lg hover:shadow-purple-500/30"
      >
        <div class="absolute top-0 right-0 w-24 h-24 bg-white/10 rounded-full -mr-8 -mt-8" />
        <div class="relative z-10 flex items-center justify-between">
          <div>
            <p class="text-purple-100 text-sm font-medium">
              平均排名
            </p>
            <p class="text-3xl font-bold mt-2">
              {{ stats.avg_rank || '-' }}
            </p>
          </div>
          <div class="w-14 h-14 bg-white/20 rounded-2xl flex items-center justify-center">
            <BarChartOutlined class="w-7 h-7" />
          </div>
        </div>
      </div>

      <div
        class="stat-card bg-white text-gray-900 cursor-pointer hover:shadow-lg border border-gray-100"
      >
        <div
          class="absolute top-0 right-0 w-24 h-24 bg-gradient-to-br from-orange-50 to-orange-100 rounded-full -mr-8 -mt-8"
        />
        <div class="relative z-10 flex items-center justify-between">
          <div>
            <p class="text-gray-500 text-sm font-medium">
              审计得分
            </p>
            <p class="text-3xl font-bold mt-2">
              {{ stats.last_audit_score || 0 }}
            </p>
          </div>
          <div class="w-14 h-14 bg-orange-50 rounded-2xl flex items-center justify-center">
            <AuditOutlined class="w-7 h-7 text-orange-500" />
          </div>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div class="bg-white rounded-2xl shadow-card p-6">
        <h3 class="text-lg font-semibold text-gray-900 mb-4">
          关键词排名趋势
        </h3>
        <v-chart
          class="h-64"
          :option="keywordTrendChart"
          autoresize
        />
      </div>
      <div class="bg-white rounded-2xl shadow-card p-6">
        <h3 class="text-lg font-semibold text-gray-900 mb-4">
          页面SEO状态分布
        </h3>
        <v-chart
          class="h-64"
          :option="pageCoverageChart"
          autoresize
        />
      </div>
    </div>

    <div class="bg-white rounded-2xl shadow-card overflow-hidden">
      <div class="p-6 border-b border-gray-100">
        <h3 class="text-lg font-semibold text-gray-900">
          最近优化的页面
        </h3>
      </div>
      <YdDataTable
        :columns="pageColumns"
        :data-source="recentPages"
        :pagination="false"
        :table-props="{ size: tableSize, rowKey: 'id' }"
        class="seo-table"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <span
              class="px-3 py-1 rounded-full text-sm font-medium"
              :class="getStatusClass(record.status)"
            >
              {{ getStatusText(record.status) }}
            </span>
          </template>
          <template v-else-if="column.key === 'optimized_at'">
            <span class="text-gray-500">{{
              record.optimized_at ? formatDate(record.optimized_at) : '-'
            }}</span>
          </template>
        </template>
      </YdDataTable>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { storeToRefs } from 'pinia';
import {
  SearchOutlined,
  ArrowUpOutlined,
  BarChartOutlined,
  AuditOutlined,
  ReloadOutlined,
} from '@ant-design/icons-vue';
import { YdDataTable } from '@/components/youding';
import { useUiPreferencesStore } from '@/stores/uiPreferences';
import VChart from 'vue-echarts';
import { applySnapCursor } from '@/composables/useChartCursor';
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { LineChart, PieChart } from 'echarts/charts';
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components';
import dayjs from 'dayjs';
import { seoAPI, unwrapApiData } from '@/api';

use([CanvasRenderer, LineChart, PieChart, GridComponent, TooltipComponent, LegendComponent]);

const ui = useUiPreferencesStore();
const { antTableSize: tableSize } = storeToRefs(ui);

const stats = ref({
  total_keywords: 0,
  ranked_keywords: 0,
  avg_rank: null as number | string | null,
  ai_optimized_pages: 0,
  last_audit_score: null as number | null,
});

const keywordTrendPoints = ref<{ date: string; avg_rank: number | null }[]>([]);
const pageCoverageRows = ref<{ type: string; count: number; percent?: number }[]>([]);

const recentPages = ref<any[]>([]);

const pageColumns = [
  { title: '页面标题', key: 'title', width: 300 },
  { title: 'SEO标题', key: 'meta_title', width: 250 },
  { title: '状态', key: 'status', width: 100 },
  { title: '优化时间', key: 'optimized_at', width: 150 },
];

const pieColors: Record<string, string> = {
  已优化: '#22c55e',
  待优化: '#f59e0b',
  优化中: '#4a9b8c',
  未优化: '#9ca3af',
};

const keywordTrendChart = computed(() => {
  const pts = keywordTrendPoints.value;
  const labels = pts.length ? pts.map((p) => dayjs(p.date).format('MM-DD')) : ['—'];
  const values = pts.length ? pts.map((p) => (p.avg_rank != null ? p.avg_rank : 0)) : [0];
  // 磁吸游标：折线图吸附最近数据点（配置见 @/composables/useChartCursor）
  return applySnapCursor({
    xAxis: {
      type: 'category',
      data: labels,
      axisLine: { lineStyle: { color: '#e2e8f0' } },
      axisLabel: { color: '#64748b' },
    },
    yAxis: {
      type: 'value',
      name: '平均排名',
      inverse: true,
      axisLine: { lineStyle: { color: '#e2e8f0' } },
      axisLabel: { color: '#64748b' },
      splitLine: { lineStyle: { color: '#f1f5f9' } },
    },
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#e2e8f0',
      textStyle: { color: '#1e293b' },
    },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    series: [
      {
        data: values,
        type: 'line',
        smooth: true,
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(34, 197, 94, 0.3)' },
              { offset: 1, color: 'rgba(34, 197, 94, 0.05)' },
            ],
          },
        },
        lineStyle: { color: '#22c55e', width: 3 },
        itemStyle: { color: '#22c55e' },
      },
    ],
  });
});

const pageCoverageChart = computed(() => {
  const rows = pageCoverageRows.value;
  const data =
    rows.length > 0
      ? rows.map((r) => ({
          value: Math.round(r.percent ?? 0),
          name: r.type,
          itemStyle: { color: pieColors[r.type] || '#9ca3af' },
        }))
      : [
          { value: 0, name: '已优化', itemStyle: { color: '#22c55e' } },
          { value: 0, name: '待优化', itemStyle: { color: '#f59e0b' } },
          { value: 0, name: '优化中', itemStyle: { color: '#4a9b8c' } },
          { value: 0, name: '未优化', itemStyle: { color: '#9ca3af' } },
        ];
  return {
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#e2e8f0',
      textStyle: { color: '#1e293b' },
    },
    legend: {
      orient: 'vertical',
      right: '5%',
      top: 'center',
      textStyle: { color: '#64748b' },
    },
    series: [
      {
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2,
        },
        label: { show: false },
        emphasis: {
          label: { show: true, fontSize: 14, fontWeight: 'bold' },
        },
        data,
      },
    ],
  };
});

function getStatusClass(status: string) {
  if (status === 'optimized') return 'bg-success-50 text-success-600';
  if (status === 'pending') return 'bg-warning-50 text-warning-600';
  if (status === 'failed') return 'bg-danger-50 text-danger-600';
  return 'bg-gray-100 text-gray-500';
}

function getStatusText(status: string) {
  if (status === 'optimized') return '已优化';
  if (status === 'pending') return '待优化';
  if (status === 'failed') return '优化失败';
  return status;
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleString('zh-CN');
}

async function fetchDashboard() {
  try {
    const res = await seoAPI.dashboard({ range: 'week' });
    const data = unwrapApiData<Record<string, any>>(res) || {};
    stats.value = {
      total_keywords: Number(data.total_keywords) || 0,
      ranked_keywords: Number(data.ranked_keywords) || 0,
      avg_rank: data.avg_rank != null && data.avg_rank !== '' ? data.avg_rank : null,
      ai_optimized_pages: Number(data.ai_optimized_pages) || 0,
      last_audit_score:
        data.last_audit_score != null && data.last_audit_score !== ''
          ? Number(data.last_audit_score)
          : null,
    };
    keywordTrendPoints.value = Array.isArray(data.keyword_trend) ? data.keyword_trend : [];
    pageCoverageRows.value = Array.isArray(data.page_coverage) ? data.page_coverage : [];
  } catch (e) {
    if (import.meta.env.DEV) console.error('Failed to fetch SEO dashboard:', e);
  }
}

async function fetchRecentPages() {
  try {
    const res = await seoAPI.seoPagesSummary();
    const raw = unwrapApiData<unknown[]>(res);
    const list = Array.isArray(raw) ? raw : [];
    recentPages.value = list.slice(0, 10);
  } catch (e) {
    if (import.meta.env.DEV) console.error('Failed to fetch recent pages:', e);
  }
}

function refreshData() {
  fetchDashboard();
  fetchRecentPages();
}

onMounted(async () => {
  await fetchDashboard();
  await fetchRecentPages();
});
</script>

<style scoped>
.seo-table :deep(.ant-table-thead > tr > th) {
  background: #f8fafc;
  font-weight: 600;
  color: #64748b;
  border-bottom: 1px solid #e2e8f0;
}

.seo-table :deep(.ant-table-tbody > tr:hover > td) {
  background: #f8fafc;
}

.seo-table :deep(.ant-table-tbody > tr > td) {
  border-bottom: 1px solid #f1f5f9;
  padding: 16px;
}
</style>
