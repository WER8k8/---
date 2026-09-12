<template>
  <YdPage surface="elevated">
    <template #actions>
      <a-select v-model:value="period" style="width: 120px" @change="loadReport">
        <a-select-option value="7d">近 7 天</a-select-option>
        <a-select-option value="30d">近 30 天</a-select-option>
        <a-select-option value="90d">近 90 天</a-select-option>
      </a-select>
    </template>

    <div class="attribution-page">
      <!-- KPI Cards -->
      <a-row :gutter="16" class="kpi-row">
        <a-col :span="6">
          <a-card class="kpi-card">
            <a-statistic title="总询盘数" :value="report.total_inquiries" :value-style="{ color: '#1890ff' }">
              <template #prefix><MessageOutlined /></template>
            </a-statistic>
          </a-card>
        </a-col>
        <a-col :span="6">
          <a-card class="kpi-card">
            <a-statistic title="已报价" :value="report.total_quoted" :value-style="{ color: '#52c41a' }">
              <template #prefix><FileTextOutlined /></template>
            </a-statistic>
          </a-card>
        </a-col>
        <a-col :span="6">
          <a-card class="kpi-card">
            <a-statistic title="成交" :value="report.total_closed" :value-style="{ color: '#faad14' }">
              <template #prefix><CheckCircleOutlined /></template>
            </a-statistic>
          </a-card>
        </a-col>
        <a-col :span="6">
          <a-card class="kpi-card">
            <a-statistic title="总营收 (USD)" :value="report.total_revenue" :precision="2" :value-style="{ color: '#722ed1' }">
              <template #prefix><DollarOutlined /></template>
            </a-statistic>
          </a-card>
        </a-col>
      </a-row>

      <!-- Conversion KPIs -->
      <a-row :gutter="16" style="margin-bottom: 24px">
        <a-col :span="12">
          <a-card>
            <a-progress type="dashboard" :percent="report.overall_quote_rate" :stroke-color="'#52c41a'" />
            <div style="text-align: center; margin-top: 8px; font-weight: 600">报价率</div>
          </a-card>
        </a-col>
        <a-col :span="12">
          <a-card>
            <a-progress type="dashboard" :percent="report.overall_close_rate" :stroke-color="'#1890ff'" />
            <div style="text-align: center; margin-top: 8px; font-weight: 600">成交率</div>
          </a-card>
        </a-col>
      </a-row>

      <!-- Charts Row -->
      <a-row :gutter="16" style="margin-bottom: 24px">
        <a-col :span="14">
          <a-card title="各渠道询盘数">
            <v-chart :option="barOption" autoresize style="height: 320px" />
          </a-card>
        </a-col>
        <a-col :span="10">
          <a-card title="渠道分布">
            <v-chart :option="pieOption" autoresize style="height: 320px" />
          </a-card>
        </a-col>
      </a-row>

      <!-- Channel Conversion Table -->
      <a-card title="各渠道转化漏斗" style="margin-bottom: 24px">
        <a-table :columns="channelColumns" :data-source="channelRows" :pagination="false" size="small" row-key="channel" />
      </a-card>

      <!-- Bottom Row: Keywords + AI Engines -->
      <a-row :gutter="16">
        <a-col :span="14">
          <a-card title="Top 搜索关键词">
            <a-table :columns="keywordColumns" :data-source="report.top_keywords" :pagination="{ pageSize: 10 }" size="small" row-key="keyword" />
          </a-card>
        </a-col>
        <a-col :span="10">
          <a-card title="AI 搜索引擎来源">
            <a-table :columns="engineColumns" :data-source="report.top_ai_engines" :pagination="false" size="small" row-key="engine" />
          </a-card>
        </a-col>
      </a-row>
    </div>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import { YdPage } from '@/components/youding';
import {
  MessageOutlined, FileTextOutlined, CheckCircleOutlined, DollarOutlined,
} from '@ant-design/icons-vue';
import VChart from 'vue-echarts';
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { BarChart, PieChart } from 'echarts/charts';
import { GridComponent, TooltipComponent, LegendComponent, TitleComponent } from 'echarts/components';
import { apiGet } from '@/utils/api';

use([CanvasRenderer, BarChart, PieChart, GridComponent, TooltipComponent, LegendComponent, TitleComponent]);

const CHANNEL_LABELS: Record<string, string> = {
  seo: 'SEO',
  customer_finder: '客户开发',
  email: '邮件营销',
  social: '社交媒体',
  ai_search: 'AI 搜索',
  referral: '推荐',
  direct: '直接访问',
};

const CHANNEL_COLORS = ['#1890ff', '#52c41a', '#faad14', '#722ed1', '#eb2f96', '#13c2c2', '#8c8c8c'];

const period = ref('30d');
const loading = ref(false);

interface ChannelData {
  inquiries: number;
  conversion: { inquiries: number; quoted: number; closed: number; quote_rate: number; close_rate: number };
  revenue: number;
}

interface ReportData {
  period: string;
  total_inquiries: number;
  total_quoted: number;
  total_closed: number;
  overall_quote_rate: number;
  overall_close_rate: number;
  total_revenue: number;
  channels: Record<string, ChannelData>;
  top_keywords: { keyword: string; inquiries: number }[];
  top_ai_engines: { engine: string; inquiries: number }[];
}

const report = ref<ReportData>({
  period: '30d', total_inquiries: 0, total_quoted: 0, total_closed: 0,
  overall_quote_rate: 0, overall_close_rate: 0, total_revenue: 0,
  channels: {}, top_keywords: [], top_ai_engines: [],
});

async function loadReport() {
  loading.value = true;
  try {
    const data = await apiGet<ReportData>('/analytics/attribution', { period: period.value });
    report.value = data || report.value;
  } catch {
    message.warning('归因数据加载失败');
  } finally {
    loading.value = false;
  }
}

onMounted(loadReport);

// --- Bar chart option ---
const barOption = computed(() => {
  const chs = report.value.channels || {};
  const keys = Object.keys(chs);
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: 80, right: 20, top: 20, bottom: 40 },
    xAxis: {
      type: 'category',
      data: keys.map(k => CHANNEL_LABELS[k] || k),
      axisLabel: { rotate: 20 },
    },
    yAxis: { type: 'value' },
    series: [{
      type: 'bar',
      data: keys.map((k, i) => ({
        value: chs[k]?.inquiries || 0,
        itemStyle: { color: CHANNEL_COLORS[i % CHANNEL_COLORS.length] },
      })),
      barWidth: '50%',
    }],
  };
});

// --- Pie chart option ---
const pieOption = computed(() => {
  const chs = report.value.channels || {};
  const keys = Object.keys(chs).filter(k => (chs[k]?.inquiries || 0) > 0);
  return {
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { bottom: 0, type: 'scroll' },
    series: [{
      type: 'pie',
      radius: ['35%', '65%'],
      center: ['50%', '45%'],
      data: keys.map((k, i) => ({
        name: CHANNEL_LABELS[k] || k,
        value: chs[k]?.inquiries || 0,
        itemStyle: { color: CHANNEL_COLORS[i % CHANNEL_COLORS.length] },
      })),
      label: { show: true, formatter: '{b}\n{d}%' },
    }],
  };
});

// --- Channel conversion table ---
const channelColumns = [
  { title: '渠道', dataIndex: 'channelLabel', key: 'channelLabel', width: 120 },
  { title: '询盘', dataIndex: 'inquiries', key: 'inquiries', width: 80, sorter: (a: any, b: any) => a.inquiries - b.inquiries },
  { title: '已报价', dataIndex: 'quoted', key: 'quoted', width: 80 },
  { title: '成交', dataIndex: 'closed', key: 'closed', width: 80 },
  { title: '报价率', dataIndex: 'quoteRate', key: 'quoteRate', width: 100 },
  { title: '成交率', dataIndex: 'closeRate', key: 'closeRate', width: 100 },
  { title: '营收 (USD)', dataIndex: 'revenue', key: 'revenue', width: 120, sorter: (a: any, b: any) => a.revenue - b.revenue },
];

const channelRows = computed(() => {
  const chs = report.value.channels || {};
  return Object.entries(chs).map(([ch, d]) => ({
    key: ch,
    channel: ch,
    channelLabel: CHANNEL_LABELS[ch] || ch,
    inquiries: d.inquiries,
    quoted: d.conversion?.quoted || 0,
    closed: d.conversion?.closed || 0,
    quoteRate: `${d.conversion?.quote_rate || 0}%`,
    closeRate: `${d.conversion?.close_rate || 0}%`,
    revenue: `$${(d.revenue || 0).toLocaleString()}`,
  }));
});

// --- Keywords table ---
const keywordColumns = [
  { title: '关键词', dataIndex: 'keyword', key: 'keyword' },
  { title: '询盘数', dataIndex: 'inquiries', key: 'inquiries', width: 100, sorter: (a: any, b: any) => a.inquiries - b.inquiries },
];

// --- AI engine table ---
const engineColumns = [
  { title: 'AI 搜索引擎', dataIndex: 'engine', key: 'engine' },
  { title: '询盘数', dataIndex: 'inquiries', key: 'inquiries', width: 100, sorter: (a: any, b: any) => a.inquiries - b.inquiries },
];
</script>

<style scoped>
.attribution-page {
  padding: 0;
}
.kpi-row {
  margin-bottom: 24px;
}
.kpi-card {
  text-align: center;
}
.kpi-card :deep(.ant-statistic-title) {
  font-size: 14px;
  color: #8c8c8c;
}
</style>
