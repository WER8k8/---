/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage class="dashboard-page space-y-6 animate-fade-in" surface="brand-hero">
    <template #hero>
      <div class="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
        <div>
          <h1 class="text-2xl font-bold text-gray-900">数据概览</h1>
          <p class="text-gray-400 mt-1 text-sm">欢迎回来，{{ authStore.username || '管理员' }}。以下是今日数据总览。</p>
        </div>
        <div class="flex items-center gap-2">
          <button
            v-for="range in timeRanges"
            :key="range.value"
            class="px-4 py-2 text-[13px] font-medium rounded-lg transition-colors"
            :class="
              timeRange === range.value
                ? 'bg-brand-500 text-white'
                : 'bg-white text-gray-500 border border-gray-200 hover:border-gray-300'
            "
            :disabled="loadState === 'loading'"
            @click="changeTimeRange(range.value)"
          >
            {{ range.label }}
          </button>
        </div>
      </div>
    </template>

    <!-- Alerts for degraded/empty states -->
    <a-alert
      v-if="loadState === 'degraded'"
      type="warning"
      show-icon
      class="rounded-xl border border-amber-100"
      :message="degradedTitle"
      :description="degradedDetail"
    />
    <a-alert
      v-else-if="loadState === 'ok' && dataHonesty && !dataHonesty.has_production_activity"
      type="info"
      show-icon
      class="rounded-xl"
      message="当前无真实业务数据"
      :description="honestyDescription"
    />
    <a-alert
      v-else-if="loadState === 'ok' && isEmptyDataset"
      type="info"
      show-icon
      class="rounded-xl"
      message="暂无汇总数据"
      description="后端已连通，当前库中尚无足够记录；图表与卡片已显示为 0。接入内容、询盘与关键词后将自动填充。"
    />

    <!-- Stat Cards Row: 4 columns with top color accent bar -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
      <div
        v-for="(stat, index) in statCards"
        :key="index"
        class="stat-card cursor-pointer group"
        @click="handleStatClick(stat.key)"
      >
        <!-- Top color bar -->
        <div class="h-1 rounded-t-xl -mx-6 -mt-6 mb-4" :class="stat.barColor"></div>
        <div class="flex items-center justify-between">
          <div>
            <p class="text-[12px] text-gray-400 font-medium uppercase tracking-wide">{{ stat.label }}</p>
            <p class="text-[28px] font-bold text-gray-900 mt-1 leading-tight">
              {{ stat.value }}
              <span v-if="stat.unit" class="text-[14px] font-normal text-gray-400 ml-0.5">{{ stat.unit }}</span>
            </p>
          </div>
          <div class="w-10 h-10 rounded-lg flex items-center justify-center bg-gray-50 group-hover:bg-blue-50 transition-colors">
            <component :is="stat.icon" class="w-5 h-5 text-gray-400 group-hover:text-brand-500 transition-colors" />
          </div>
        </div>
      </div>
    </div>

    <!-- Charts Row -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Keyword Trend Chart -->
      <div class="lg:col-span-2 bg-white rounded-xl border border-[#f1f5f9] p-6 card-hover">
        <div class="flex items-center justify-between mb-5">
          <div>
            <h3 class="text-base font-semibold text-gray-900">关键词排名趋势</h3>
            <p class="text-[13px] text-gray-400 mt-0.5">近7天排名变化</p>
          </div>
          <div class="flex items-center gap-2">
            <span class="w-2.5 h-2.5 rounded-full bg-[#0ea5e9]"></span>
            <span class="text-[13px] text-gray-400">平均排名</span>
          </div>
        </div>
        <div class="h-64">
          <v-chart class="h-full w-full" :option="keywordTrendChart" autoresize />
        </div>
      </div>

      <!-- Page Status Pie -->
      <div class="bg-white rounded-xl border border-[#f1f5f9] p-6 card-hover">
        <div class="mb-5">
          <h3 class="text-base font-semibold text-gray-900">页面SEO状态</h3>
          <p class="text-[13px] text-gray-400 mt-0.5">各状态占比</p>
        </div>
        <div class="h-56 flex items-center justify-center">
          <v-chart class="h-full w-full" :option="pageStatusChart" autoresize />
        </div>
        <div class="mt-4 space-y-2.5">
          <div v-for="(item, index) in statusItems" :key="index" class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <span class="w-2.5 h-2.5 rounded-full" :class="item.color"></span>
              <span class="text-[13px] text-gray-600">{{ item.label }}</span>
            </div>
            <span class="text-[13px] font-medium text-gray-900">{{ item.value }}%</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Admin KPI Row -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div class="bg-white rounded-xl border border-[#f1f5f9] p-5 card-hover flex items-center gap-4">
        <div class="w-10 h-10 rounded-lg bg-amber-50 flex items-center justify-center">
          <DollarOutlined class="text-amber-500 text-lg" />
        </div>
        <div>
          <p class="text-[11px] text-gray-400 uppercase tracking-wide">AI 本月成本</p>
          <p class="text-xl font-bold text-gray-900">{{ adminStats.aiCost }}</p>
          <p class="text-[11px] text-gray-400 mt-0.5">{{ adminStats.aiCalls }} 次调用</p>
        </div>
      </div>
      <div class="bg-white rounded-xl border border-[#f1f5f9] p-5 card-hover flex items-center gap-4 cursor-pointer" @click="$router.push('/admin')">
        <div class="w-10 h-10 rounded-lg bg-red-50 flex items-center justify-center">
          <AlertOutlined class="text-red-500 text-lg" />
        </div>
        <div>
          <p class="text-[11px] text-gray-400 uppercase tracking-wide">系统告警</p>
          <p class="text-xl font-bold" :class="adminStats.alertOpen > 0 ? 'text-red-600' : 'text-green-600'">{{ adminStats.alertOpen }}</p>
          <p class="text-[11px] text-gray-400 mt-0.5">待处理</p>
        </div>
      </div>
      <div class="bg-white rounded-xl border border-[#f1f5f9] p-5 card-hover flex items-center gap-4">
        <div class="w-10 h-10 rounded-lg bg-green-50 flex items-center justify-center">
          <CheckCircleOutlined class="text-green-500 text-lg" />
        </div>
        <div>
          <p class="text-[11px] text-gray-400 uppercase tracking-wide">系统状态</p>
          <p class="text-xl font-bold text-green-600">正常</p>
          <p class="text-[11px] text-gray-400 mt-0.5">后端 · Redis · SEO Backend</p>
        </div>
      </div>
    </div>

    <!-- Inquiries + Keywords Row -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Recent Inquiries -->
      <div class="bg-white rounded-xl border border-[#f1f5f9] p-6 card-hover">
        <div class="flex items-center justify-between mb-5">
          <div>
            <h3 class="text-base font-semibold text-gray-900">最新询盘</h3>
            <p class="text-[13px] text-gray-400 mt-0.5">最近收到的客户询盘</p>
          </div>
          <router-link to="/inquiries" class="text-[13px] text-brand-500 hover:text-[#2a6b60] font-medium no-underline">查看全部</router-link>
        </div>
        <div class="space-y-1">
          <div
            v-for="(inquiry, index) in recentInquiries"
            :key="index"
            class="flex items-center justify-between p-3 rounded-lg hover:bg-gray-50 transition-colors cursor-pointer"
          >
            <div class="flex items-center gap-3 min-w-0">
              <div class="w-9 h-9 rounded-lg bg-blue-50 flex items-center justify-center flex-shrink-0">
                <MessageOutlined class="w-4 h-4 text-brand-500" />
              </div>
              <div class="min-w-0">
                <p class="font-medium text-[14px] text-gray-900 truncate">{{ inquiry.company }}</p>
                <p class="text-[12px] text-gray-400 truncate">{{ inquiry.product }} &middot; {{ inquiry.contact }}</p>
              </div>
            </div>
            <div class="text-right flex-shrink-0 ml-3">
              <p class="text-[12px] text-gray-400">{{ inquiry.time }}</p>
              <span class="text-[11px] px-2 py-0.5 rounded-full" :class="inquiry.status === 'new' ? 'bg-green-50 text-green-600' : 'bg-gray-100 text-gray-500'">
                {{ inquiry.status === 'new' ? '新询盘' : '已处理' }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Hot Keywords -->
      <div class="bg-white rounded-xl border border-[#f1f5f9] p-6 card-hover">
        <div class="flex items-center justify-between mb-5">
          <div>
            <h3 class="text-base font-semibold text-gray-900">热门关键词</h3>
            <p class="text-[13px] text-gray-400 mt-0.5">搜索量最高的关键词</p>
          </div>
          <router-link to="/seo" class="text-[13px] text-brand-500 hover:text-[#2a6b60] font-medium no-underline">查看全部</router-link>
        </div>
        <div class="space-y-1">
          <div
            v-for="(keyword, index) in hotKeywords"
            :key="index"
            class="flex items-center justify-between p-3 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <div class="flex items-center gap-3">
              <div class="w-8 h-8 rounded-lg flex items-center justify-center text-[12px] font-bold" :class="index < 3 ? 'bg-brand-500 text-white' : 'bg-gray-100 text-gray-500'">
                {{ index + 1 }}
              </div>
              <div>
                <p class="font-medium text-[14px] text-gray-900">{{ keyword.name }}</p>
                <p class="text-[11px] text-gray-400">排名: {{ keyword.rank }} | 搜索量: {{ formatSearchVolume(keyword.search) }}</p>
              </div>
            </div>
            <div class="flex items-center gap-1">
              <ArrowUpOutlined class="w-3.5 h-3.5" :class="keyword.change > 0 ? 'text-green-500' : 'text-red-500'" />
              <span class="text-[13px] font-medium" :class="keyword.change > 0 ? 'text-green-500' : 'text-red-500'">
                {{ keyword.change > 0 ? '+' : '' }}{{ keyword.change }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Product Stats Table + Todos Sidebar -->
    <div class="grid grid-cols-1 lg:grid-cols-4 gap-6">
      <!-- Product Table -->
      <div class="lg:col-span-3 bg-white rounded-xl border border-[#f1f5f9] p-6 card-hover">
        <div class="flex items-center justify-between mb-5">
          <div>
            <h3 class="text-base font-semibold text-gray-900">产品访问统计</h3>
            <p class="text-[13px] text-gray-400 mt-0.5">各产品页面访问情况</p>
          </div>
          <router-link to="/products" class="text-[13px] text-brand-500 hover:text-[#2a6b60] font-medium no-underline">查看全部</router-link>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full">
            <thead>
              <tr class="border-b border-gray-100">
                <th class="text-left py-3 px-3 text-[12px] font-semibold text-gray-400 uppercase tracking-wide">产品名称</th>
                <th class="text-left py-3 px-3 text-[12px] font-semibold text-gray-400 uppercase tracking-wide">分类</th>
                <th class="text-center py-3 px-3 text-[12px] font-semibold text-gray-400 uppercase tracking-wide">浏览量</th>
                <th class="text-center py-3 px-3 text-[12px] font-semibold text-gray-400 uppercase tracking-wide">询盘数</th>
                <th class="text-center py-3 px-3 text-[12px] font-semibold text-gray-400 uppercase tracking-wide">转化率</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(product, index) in productStats" :key="index" class="border-b border-gray-50 hover:bg-gray-50/50 transition-colors">
                <td class="py-3 px-3">
                  <div class="flex items-center gap-3">
                    <div class="w-9 h-9 rounded-lg bg-gray-100 flex items-center justify-center">
                      <PauseOutlined class="w-4 h-4 text-gray-400" />
                    </div>
                    <span class="font-medium text-[14px] text-gray-900">{{ product.name }}</span>
                  </div>
                </td>
                <td class="py-3 px-3 text-[13px] text-gray-500">{{ product.category }}</td>
                <td class="py-3 px-3 text-center text-[14px] text-gray-900">{{ product.views }}</td>
                <td class="py-3 px-3 text-center text-[14px] text-gray-900">{{ product.inquiries }}</td>
                <td class="py-3 px-3">
                  <div class="flex items-center justify-center gap-2">
                    <div class="w-20 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        class="h-full rounded-full transition-all duration-500"
                        :class="product.conversion >= 10 ? 'bg-green-500' : product.conversion >= 5 ? 'bg-amber-400' : 'bg-red-400'"
                        :style="{ width: `${product.conversion * 10}%` }"
                      />
                    </div>
                    <span class="text-[13px] text-gray-600">{{ product.conversion }}%</span>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Todos Sidebar -->
      <div class="bg-white rounded-xl border border-[#f1f5f9] p-5 card-hover">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-base font-semibold text-gray-900">今日待办</h3>
          <span class="text-[12px] text-gray-400">{{ todayTodos.filter((t) => !t.completed).length }} 项</span>
        </div>
        <div class="space-y-2">
          <div
            v-for="(todo, index) in todayTodos"
            :key="index"
            class="flex items-center gap-3 p-2.5 rounded-lg transition-colors"
            :class="todo.completed ? 'opacity-50' : 'hover:bg-gray-50'"
          >
            <button
              class="w-5 h-5 rounded-full border-2 flex items-center justify-center transition-all flex-shrink-0"
              :class="todo.completed ? 'bg-brand-500 border-brand-500' : 'border-gray-300 hover:border-brand-500'"
              @click="toggleTodo(index)"
            >
              <CheckOutlined v-if="todo.completed" class="w-3 h-3 text-white" />
            </button>
            <span class="text-[13px] text-gray-700 flex-1" :class="todo.completed ? 'line-through' : ''">{{ todo.title }}</span>
            <span
              class="text-[10px] px-1.5 py-0.5 rounded-full font-medium"
              :class="todo.priority === 'high' ? 'bg-red-50 text-red-500' : todo.priority === 'medium' ? 'bg-amber-50 text-amber-500' : 'bg-gray-100 text-gray-500'"
            >
              {{ todo.priority === 'high' ? '紧急' : todo.priority === 'medium' ? '中等' : '普通' }}
            </span>
          </div>
        </div>
        <button class="w-full mt-4 py-2.5 rounded-lg border border-dashed border-gray-200 text-[13px] text-gray-400 hover:text-brand-500 hover:border-brand-500 transition-colors flex items-center justify-center gap-2">
          <PlusOutlined class="w-3.5 h-3.5" />
          <span>添加任务</span>
        </button>
      </div>
    </div>
  </YdPage>
</template>

<script setup lang="ts">
import { getAuthToken } from '@/utils/api'
import { YdPage } from '@/components/youding';
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import 'dayjs/locale/zh-cn';
import {
  PauseOutlined, MessageOutlined, SearchOutlined, BarChartOutlined,
  ArrowUpOutlined, CheckOutlined, PlusOutlined, BarsOutlined,
  ApiOutlined, TagOutlined, DollarOutlined, AlertOutlined, CheckCircleOutlined,
} from '@ant-design/icons-vue';
import VChart from 'vue-echarts';
import { applySnapCursor } from '@/composables/useChartCursor';
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { LineChart, PieChart } from 'echarts/charts';
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components';
import { seoAPI, unwrapApiData } from '@/api';
import { useAuthStore } from '@/stores/auth';

dayjs.extend(relativeTime);
dayjs.locale('zh-cn');

use([CanvasRenderer, LineChart, PieChart, GridComponent, TooltipComponent, LegendComponent]);

const router = useRouter();
const authStore = useAuthStore();

const timeRange = ref('week');

/** idle | loading | ok | degraded */
const loadState = ref<'idle' | 'loading' | 'ok' | 'degraded'>('idle');
const degradedTitle = ref('无法加载实时看板');
const degradedDetail = ref('');

const timeRanges = [
  { label: '今日', value: 'today' },
  { label: '本周', value: 'week' },
  { label: '本月', value: 'month' },
];

const stats = ref({
  totalProducts: 0,
  totalInquiries: 0,
  aiOptimizedPages: 0,
  totalKeywords: 0,
  rankedKeywords: 0,
  avgRank: 0 as number | string,
});

const keywordTrendPoints = ref<{ date: string; avg_rank: number | null }[]>([]);
const pageCoverageRows = ref<{ type: string; count: number; percent?: number }[]>([]);

interface DataHonesty {
  has_production_activity?: boolean
  excluded_inquiries?: number
  raw_inquiries?: number
}

const dataHonesty = ref<DataHonesty | null>(null)

const honestyDescription = computed(() => {
  const h = dataHonesty.value
  if (!h) return '已过滤开发/测试询盘，仅展示真实业务汇总。'
  const parts = ['已过滤开发/测试询盘，仅展示真实业务汇总。']
  if (h.excluded_inquiries) {
    parts.push(`本次已排除 ${h.excluded_inquiries} 条测试询盘。`)
  }
  return parts.join(' ')
})

// Status cards with clean design - top color accent bars
const barColors = [
  'bg-brand-500', // blue
  'bg-[#8b5cf6]', // violet
  'bg-[#f97316]', // orange
  'bg-[#0ea5e9]', // sky
  'bg-[#22c55e]', // green
  'bg-[#a855f7]', // purple
];

const statCards = computed(() => [
  {
    key: 'products',
    label: '总产品数',
    value: stats.value.totalProducts,
    unit: '件',
    icon: BarsOutlined,
    barColor: barColors[0],
  },
  {
    key: 'inquiries',
    label: '询盘数量',
    value: stats.value.totalInquiries,
    unit: '条',
    icon: MessageOutlined,
    barColor: barColors[1],
  },
  {
    key: 'aiOptimized',
    label: 'AI优化页面',
    value: stats.value.aiOptimizedPages,
    unit: '页',
    icon: ApiOutlined,
    barColor: barColors[2],
  },
  {
    key: 'keywords',
    label: '关键词总数',
    value: stats.value.totalKeywords,
    unit: '个',
    icon: SearchOutlined,
    barColor: barColors[3],
  },
  {
    key: 'ranked',
    label: '已排名关键词',
    value: stats.value.rankedKeywords,
    unit: '个',
    icon: TagOutlined,
    barColor: barColors[4],
  },
  {
    key: 'avgRank',
    label: '平均排名',
    value: stats.value.avgRank,
    unit: '',
    icon: BarChartOutlined,
    barColor: barColors[5],
  },
]);

const statusColorMap: Record<string, string> = {
  已优化: 'bg-green-500',
  待优化: 'bg-amber-400',
  优化中: 'bg-blue-500',
  未优化: 'bg-gray-400',
};

const isEmptyDataset = computed(() => {
  if (loadState.value !== 'ok') return false;
  const s = stats.value;
  return (
    !keywordTrendPoints.value.length &&
    !pageCoverageRows.value.length &&
    !recentInquiries.value.length &&
    !hotKeywords.value.length &&
    !productStats.value.length &&
    !s.totalProducts &&
    !s.totalInquiries
  );
});

const statusItems = computed(() => {
  const rows = pageCoverageRows.value;
  if (!rows.length) {
    return [
      { label: '已优化', value: 0, color: 'bg-green-500' },
      { label: '待优化', value: 0, color: 'bg-amber-400' },
      { label: '优化中', value: 0, color: 'bg-blue-500' },
      { label: '未优化', value: 0, color: 'bg-gray-400' },
    ];
  }
  return rows.map((r) => ({
    label: r.type,
    value: Math.round(r.percent ?? 0),
    color: statusColorMap[r.type] || 'bg-gray-400',
  }));
});

const recentInquiries = ref<
  { company: string; product: string; contact: string; time: string; status: string }[]
>([]);

const hotKeywords = ref<{ name: string; rank: number; search: number | string; change: number }[]>([]);

const productStats = ref<
  { name: string; category: string; views: number; inquiries: number; conversion: number }[]
>([]);

const adminStats = ref({ aiCost: '—', aiCalls: 0, alertOpen: 0 })

async function fetchAdminStats() {
  try {
    const [costRes, alertRes] = await Promise.all([
      fetch('/api/v1/super-admin/ai-cost/summary', { headers: { Authorization: `Bearer ${getAuthToken()}` } }),
      fetch('/api/v1/super-admin/alerts/summary', { headers: { Authorization: `Bearer ${getAuthToken()}` } }),
    ])
    const cost = await costRes.json()
    const alert = await alertRes.json()
    const cd = cost.data || cost
    const ad = alert.data || alert
    adminStats.value = {
      aiCost: `¥${cd.total_cost || 0}`,
      aiCalls: cd.total_calls || 0,
      alertOpen: ad.open_count || 0,
    }
  } catch {}
}

const todayTodos = ref<{ title: string; completed: boolean; priority: string }[]>([])

// ECharts: Keyword trend
const keywordTrendChart = computed(() => {
  const pts = keywordTrendPoints.value;
  const labels = pts.length ? pts.map((p) => dayjs(p.date).format('MM-DD')) : ['—'];
  const values = pts.length ? pts.map((p) => (p.avg_rank != null ? p.avg_rank : 0)) : [0];
  // 磁吸游标：折线图吸附最近数据点（配置见 @/composables/useChartCursor）
  return applySnapCursor({
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255, 255, 255, 0.96)',
      borderColor: '#f1f5f9',
      borderWidth: 1,
      textStyle: { color: '#334155', fontSize: 12 },
      formatter: (params: any) => {
        const data = params[0];
        return `<div class="font-medium">${data.name}</div><div style="color:#0ea5e9;">平均排名: ${data.value}</div>`;
      },
    },
    grid: { left: '3%', right: '4%', bottom: '3%', top: '10%', containLabel: true },
    xAxis: {
      type: 'category',
      data: labels,
      axisLine: { lineStyle: { color: '#f1f5f9' } },
      axisTick: { show: false },
      axisLabel: { color: '#94a3b8', fontSize: 11 },
    },
    yAxis: {
      type: 'value',
      name: '平均排名',
      nameTextStyle: { color: '#94a3b8', fontSize: 11 },
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: '#94a3b8', fontSize: 11 },
      splitLine: { lineStyle: { color: '#f8fafc', type: 'dashed' as const } },
      inverse: true,
    },
    series: [{
      data: values,
      type: 'line',
      smooth: true,
      symbol: 'circle',
      symbolSize: 6,
      lineStyle: { width: 2.5, color: '#0ea5e9' },
      itemStyle: { color: '#0ea5e9', borderWidth: 2, borderColor: '#fff' },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(14,165,233,0.15)' },
            { offset: 1, color: 'rgba(14,165,233,0.01)' },
          ],
        },
      },
    }],
  });
});

// ECharts: Page status pie
const pieColors: Record<string, string> = {
  已优化: '#22c55e',
  待优化: '#f59e0b',
  优化中: '#0ea5e9',
  未优化: '#94a3b8',
};

const pageStatusChart = computed(() => {
  const rows = pageCoverageRows.value;
  const data = rows.length > 0
    ? rows.map((r) => ({
        value: Math.round(r.percent ?? 0),
        name: r.type,
        itemStyle: { color: pieColors[r.type] || '#94a3b8' },
      }))
    : [
        { value: 0, name: '已优化', itemStyle: { color: '#22c55e' } },
        { value: 0, name: '待优化', itemStyle: { color: '#f59e0b' } },
        { value: 0, name: '优化中', itemStyle: { color: '#0ea5e9' } },
        { value: 0, name: '未优化', itemStyle: { color: '#94a3b8' } },
      ];
  return {
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(255, 255, 255, 0.96)',
      borderColor: '#f1f5f9',
      borderWidth: 1,
      textStyle: { color: '#334155', fontSize: 12 },
      formatter: (params: any) => `<div class="font-medium">${params.name}</div><div>占比: ${params.value}%</div>`,
    },
    series: [{
      type: 'pie',
      radius: ['55%', '78%'],
      center: ['50%', '50%'],
      avoidLabelOverlap: false,
      itemStyle: { borderRadius: 8, borderColor: '#fff', borderWidth: 2 },
      label: { show: false },
      emphasis: {
        label: { show: true, fontSize: 13, fontWeight: 'bold', color: '#334155' },
        itemStyle: { shadowBlur: 16, shadowOffsetX: 0, shadowColor: 'rgba(0, 0, 0, 0.1)' },
      },
      data,
    }],
  };
});

function changeTimeRange(range: string) {
  timeRange.value = range;
  fetchDashboard();
}

function handleStatClick(key: string) {
  const routes: Record<string, string> = {
    products: '/products',
    inquiries: '/inquiries',
    aiOptimized: '/seo/content-optimizer',
    keywords: '/seo',
    ranked: '/seo/keyword-ranking',
    avgRank: '/analytics',
  };
  const path = routes[key];
  if (path) router.push(path);
}

function formatSearchVolume(v: number | string) {
  if (typeof v === 'string') return v;
  return v.toLocaleString('zh-CN');
}

function formatInquiryTime(iso: string) {
  if (!iso) return '—';
  const d = dayjs(iso);
  if (!d.isValid()) return iso;
  return d.fromNow();
}

function toggleTodo(index: number) {
  todayTodos.value[index].completed = !todayTodos.value[index].completed;
}

function applyEmptyDashboard(reason: string, detail: string) {
  degradedTitle.value = reason;
  degradedDetail.value = detail;
  loadState.value = 'degraded';
  dataHonesty.value = null;
  stats.value = {
    totalProducts: 0, totalInquiries: 0, aiOptimizedPages: 0,
    totalKeywords: 0, rankedKeywords: 0, avgRank: '—',
  };
  keywordTrendPoints.value = [];
  pageCoverageRows.value = [];
  recentInquiries.value = [];
  hotKeywords.value = [];
  productStats.value = [];
}

async function fetchDashboard() {
  loadState.value = 'loading';
  dataHonesty.value = null;
  try {
    const res = await seoAPI.dashboard({ range: timeRange.value });
    const data = unwrapApiData<Record<string, unknown>>(res) || {};
    const ar = data.avg_rank;
    stats.value = {
      totalProducts: Number(data.total_products) || 0,
      totalInquiries: Number(data.total_inquiries) || 0,
      aiOptimizedPages: Number(data.ai_optimized_pages) || 0,
      totalKeywords: Number(data.total_keywords) || 0,
      rankedKeywords: Number(data.ranked_keywords) || 0,
      avgRank: ar != null && ar !== '' ? (ar as string | number) : '—',
    };
    keywordTrendPoints.value = Array.isArray(data.keyword_trend) ? data.keyword_trend : [];
    pageCoverageRows.value = Array.isArray(data.page_coverage) ? data.page_coverage : [];
    const rawInq = data.recent_inquiries;
    recentInquiries.value = Array.isArray(rawInq)
      ? rawInq.map((r: Record<string, unknown>) => ({
          company: String(r.company ?? ''),
          product: String(r.product ?? ''),
          contact: String(r.contact ?? ''),
          time: formatInquiryTime(String(r.time ?? '')),
          status: String(r.status ?? 'processed'),
        }))
      : [];
    hotKeywords.value = Array.isArray(data.hot_keywords) ? data.hot_keywords : [];
    productStats.value = Array.isArray(data.product_stats) ? data.product_stats : [];
    dataHonesty.value = (data.data_honesty as DataHonesty | undefined) ?? null;
    loadState.value = 'ok';
  } catch (e: unknown) {
    if (import.meta.env.DEV) console.error('Failed to fetch dashboard:', e);
    const status = (e as { response?: { status?: number } })?.response?.status;
    const is401 = status === 401;
    applyEmptyDashboard(
      is401 ? '登录已失效' : '无法连接 SEO 看板接口',
      is401
        ? '请重新登录后再试；页面已降级为空数据。'
        : '请确认后端已启动且 Vite 将 /api 代理到正确端口；页面已降级为空数据，避免白屏。'
    );
  }
}

onMounted(() => {
  fetchDashboard();
  fetchAdminStats();
});
</script>
