/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="SEO 矩阵数据看板" subtitle="全国县域建材关键词智能监控中心" surface="elevated">
    <template #actions>
      <a-button @click="refreshData">
        <ReloadOutlined class="w-4 h-4 mr-2" />
        刷新数据
      </a-button>
      <a-button type="primary" class="gradient-primary" @click="exportReport">
        <DownloadOutlined class="w-4 h-4 mr-2" />
        导出报告
      </a-button>
    </template>
  <div class="space-y-6 animate-fade-in">
    <template v-if="initialLoading">
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
        <SkeletonCard v-for="i in 4" :key="`kpi-skel-${i}`" variant="kpi" />
      </div>
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <SkeletonCard variant="chart" />
        <SkeletonCard variant="chart" />
      </div>
    </template>
    <template v-else>
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
      <div class="stat-card bg-gradient-to-br from-primary-500 to-primary-600 text-white">
        <div class="absolute top-0 right-0 w-24 h-24 bg-white/10 rounded-full -mr-8 -mt-8" />
        <div class="relative z-10 flex items-center justify-between">
          <div>
            <p class="text-primary-100 text-sm font-medium">
              已生成关键词
            </p>
            <p class="text-3xl font-bold mt-2">
              {{ stats.keyword_stats.total || 0 }}
            </p>
          </div>
          <div class="w-14 h-14 bg-white/20 rounded-2xl flex items-center justify-center">
            <KeyOutlined class="w-7 h-7" />
          </div>
        </div>
      </div>

      <div class="stat-card bg-gradient-to-br from-success-500 to-success-600 text-white">
        <div class="absolute top-0 right-0 w-24 h-24 bg-white/10 rounded-full -mr-8 -mt-8" />
        <div class="relative z-10 flex items-center justify-between">
          <div>
            <p class="text-success-100 text-sm font-medium">
              已发布内容
            </p>
            <p class="text-3xl font-bold mt-2">
              {{ stats.content_stats.published || 0 }}
            </p>
          </div>
          <div class="w-14 h-14 bg-white/20 rounded-2xl flex items-center justify-center">
            <FileTextOutlined class="w-7 h-7" />
          </div>
        </div>
      </div>

      <div class="stat-card bg-gradient-to-br from-blue-500 to-blue-600 text-white">
        <div class="absolute top-0 right-0 w-24 h-24 bg-white/10 rounded-full -mr-8 -mt-8" />
        <div class="relative z-10 flex items-center justify-between">
          <div>
            <p class="text-blue-100 text-sm font-medium">
              收录成功
            </p>
            <p class="text-3xl font-bold mt-2">
              {{ stats.inclusion_stats.included || 0 }}
            </p>
          </div>
          <div class="w-14 h-14 bg-white/20 rounded-2xl flex items-center justify-center">
            <EyeOutlined class="w-7 h-7" />
          </div>
        </div>
      </div>

      <div class="stat-card bg-gradient-to-br from-purple-500 to-purple-600 text-white">
        <div class="absolute top-0 right-0 w-24 h-24 bg-white/10 rounded-full -mr-8 -mt-8" />
        <div class="relative z-10 flex items-center justify-between">
          <div>
            <p class="text-purple-100 text-sm font-medium">
              覆盖区县
            </p>
            <p class="text-3xl font-bold mt-2">
              {{ stats.region_stats.covered || 0 }}
            </p>
          </div>
          <div class="w-14 h-14 bg-white/20 rounded-2xl flex items-center justify-center">
            <GlobalOutlined class="w-7 h-7" />
          </div>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div class="lg:col-span-2 bg-white rounded-2xl shadow-card p-6">
        <div class="flex items-center justify-between mb-6">
          <h3 class="text-lg font-semibold text-gray-900">
            发布趋势
          </h3>
          <div class="flex items-center space-x-2">
            <span class="flex items-center">
              <span class="w-3 h-3 rounded-full bg-primary-500 mr-2" />
              <span class="text-sm text-gray-500">发布量</span>
            </span>
          </div>
        </div>
        <v-chart
          class="h-72"
          :option="publishTrendChart"
          autoresize
        />
      </div>

      <div class="bg-white rounded-2xl shadow-card p-6">
        <h3 class="text-lg font-semibold text-gray-900 mb-6">
          平台分布
        </h3>
        <v-chart
          class="h-64"
          :option="platformChart"
          autoresize
        />
        <div class="mt-4 space-y-3">
          <div
            v-for="platform in platformStats"
            :key="platform.name"
            class="flex items-center justify-between"
          >
            <span class="text-sm text-gray-600">{{ platform.name }}</span>
            <span class="text-sm font-medium text-gray-900">{{ platform.count }}</span>
          </div>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div class="bg-white rounded-2xl shadow-card p-6">
        <div class="flex items-center justify-between mb-6">
          <h3 class="text-lg font-semibold text-gray-900">
            热门关键词
          </h3>
          <router-link
            to="/seo-matrix/keywords"
            class="text-sm text-primary-500"
          >
            查看全部
          </router-link>
        </div>
        <a-table
          :columns="keywordColumns"
          :data-source="hotKeywords"
          :pagination="false"
          row-key="id"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'rank'">
              <span
                :class="
                  record.rank <= 10
                    ? 'text-success-500'
                    : record.rank <= 20
                      ? 'text-warning-500'
                      : 'text-gray-400'
                "
                class="font-medium"
              >
                {{ record.rank || '-' }}
              </span>
            </template>
          </template>
        </a-table>
      </div>

      <div class="bg-white rounded-2xl shadow-card p-6">
        <div class="flex items-center justify-between mb-6">
          <h3 class="text-lg font-semibold text-gray-900">
            最新发布任务
          </h3>
          <router-link
            to="/seo-matrix/publish"
            class="text-sm text-primary-500"
          >
            查看全部
          </router-link>
        </div>
        <a-table
          :columns="taskColumns"
          :data-source="recentTasks"
          :pagination="false"
          row-key="id"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'status'">
              <span
                :class="getStatusClass(record.status)"
                class="px-3 py-1 rounded-full text-sm font-medium"
              >
                {{ getStatusText(record.status) }}
              </span>
            </template>
            <template v-if="column.key === 'created_at'">
              <span class="text-gray-500 text-sm">{{ formatTime(record.created_at) }}</span>
            </template>
          </template>
        </a-table>
      </div>
    </div>
    </template>
  </div>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import {
  KeyOutlined,
  FileTextOutlined,
  EyeOutlined,
  GlobalOutlined,
  ReloadOutlined,
  DownloadOutlined,
} from '@ant-design/icons-vue';
import VChart from 'vue-echarts';
import { applySnapCursor } from '@/composables/useChartCursor';
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { LineChart, PieChart } from 'echarts/charts';
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components';
import { message } from 'ant-design-vue';
import { YdPage } from '@/components/youding';
import SkeletonCard from '@/components/common/SkeletonCard.vue';
import { downloadTableCsv } from '@/utils/exportCsv';
import { seoMatrixAPI, unwrapApiData } from '@/api';

use([CanvasRenderer, LineChart, PieChart, GridComponent, TooltipComponent, LegendComponent]);

const stats = ref({
  keyword_stats: { total: 0, used: 0 },
  content_stats: { total: 0, published: 0 },
  publish_stats: { total: 0, success: 0, failed: 0 },
  inclusion_stats: { total: 0, included: 0 },
  region_stats: { covered: 0, total: 2800 },
  platform_stats: [] as any[],
});

const hotKeywords = ref<any[]>([]);
const recentTasks = ref<any[]>([]);
const initialLoading = ref(true);

const platformStats = computed(() => {
  return stats.value.platform_stats.map((p: any) => ({
    name: p.name,
    count: p.published_count,
  }));
});

const keywordColumns = [
  { title: '关键词', key: 'keyword', width: 200 },
  { title: '排名', key: 'rank', width: 80, align: 'center' as const },
  { title: '搜索量', key: 'search_volume', width: 100 },
  { title: '状态', key: 'status', width: 100 },
];

const taskColumns = [
  { title: '关键词', key: 'keyword', width: 150 },
  { title: '平台', key: 'platform', width: 100 },
  { title: '状态', key: 'status', width: 100 },
  { title: '发布时间', key: 'created_at', width: 120 },
];

const publishTrendChart = computed(() => applySnapCursor({
  tooltip: {
    trigger: 'axis',
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
    borderColor: '#e2e8f0',
    textStyle: { color: '#334155' },
  },
  grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
  xAxis: {
    type: 'category',
    data: ['1日', '2日', '3日', '4日', '5日', '6日', '7日'],
    axisLine: { lineStyle: { color: '#e2e8f0' } },
    axisLabel: { color: '#64748b' },
  },
  yAxis: {
    type: 'value',
    axisLine: { show: false },
    axisLabel: { color: '#64748b' },
    splitLine: { lineStyle: { color: '#f1f5f9' } },
  },
  series: [
    {
      data: [120, 156, 98, 203, 178, 234, 189],
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
            { offset: 0, color: 'rgba(59, 130, 246, 0.3)' },
            { offset: 1, color: 'rgba(59, 130, 246, 0.05)' },
          ],
        },
      },
      lineStyle: { color: '#4a9b8c', width: 3 },
      itemStyle: { color: '#4a9b8c' },
    },
  ],
}));

const platformChart = computed(() => ({
  tooltip: {
    trigger: 'item',
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
    borderColor: '#e2e8f0',
    textStyle: { color: '#334155' },
  },
  series: [
    {
      type: 'pie',
      radius: ['45%', '75%'],
      center: ['50%', '50%'],
      avoidLabelOverlap: false,
      itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
      label: { show: false },
      emphasis: { label: { show: true, fontSize: 14, fontWeight: 'bold' } },
      data: [
        { value: 35, name: '百度', itemStyle: { color: '#22c55e' } },
        { value: 25, name: '搜狗', itemStyle: { color: '#4a9b8c' } },
        { value: 20, name: '360', itemStyle: { color: '#f59e0b' } },
        { value: 20, name: '其他', itemStyle: { color: '#9ca3af' } },
      ],
    },
  ],
}));

function getStatusClass(status: string) {
  if (status === 'success') return 'bg-success-50 text-success-600';
  if (status === 'failed') return 'bg-danger-50 text-danger-600';
  if (status === 'pending') return 'bg-warning-50 text-warning-600';
  return 'bg-gray-100 text-gray-500';
}

function getStatusText(status: string) {
  const map: Record<string, string> = {
    success: '成功',
    failed: '失败',
    pending: '待发布',
    processing: '处理中',
  };
  return map[status] || status;
}

function formatTime(timeStr: string) {
  if (!timeStr) return '-';
  const date = new Date(timeStr);
  return date.toLocaleString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

async function fetchDashboard() {
  try {
    const res = await seoMatrixAPI.dashboard();
    const d = unwrapApiData<Record<string, any>>(res);
    if (!d) return;
    if (d.keyword_stats)
      stats.value.keyword_stats = { ...stats.value.keyword_stats, ...d.keyword_stats };
    if (d.content_stats)
      stats.value.content_stats = { ...stats.value.content_stats, ...d.content_stats };
    if (d.publish_stats)
      stats.value.publish_stats = { ...stats.value.publish_stats, ...d.publish_stats };
    if (d.inclusion_stats)
      stats.value.inclusion_stats = { ...stats.value.inclusion_stats, ...d.inclusion_stats };
    if (Array.isArray(d.platform_stats)) stats.value.platform_stats = d.platform_stats;
    hotKeywords.value = d.hot_keywords || [];
    recentTasks.value = d.recent_tasks || [];
  } catch (e) {
    if (import.meta.env.DEV) console.error('Failed to fetch dashboard:', e);
  } finally {
    initialLoading.value = false;
  }
}

function refreshData() {
  fetchDashboard();
}

function exportReport() {
  const s = stats.value;
  downloadTableCsv(
    `seo-matrix-dashboard-${new Date().toISOString().slice(0, 10)}.csv`,
    ['指标', '数值'],
    [
      ['关键词总数', s.keyword_stats.total],
      ['已用关键词', s.keyword_stats.used],
      ['文案总数', s.content_stats.total],
      ['已发布文案', s.content_stats.published],
      ['发布任务总数', s.publish_stats.total],
      ['发布成功', s.publish_stats.success],
      ['发布失败', s.publish_stats.failed],
      ['收录监控总数', s.inclusion_stats.total],
      ['已收录', s.inclusion_stats.included],
      ['覆盖区县', s.region_stats.covered],
      ['区县总数', s.region_stats.total],
    ],
  );
  message.success('看板报表已导出 CSV');
}

onMounted(() => {
  fetchDashboard();
});
</script>
