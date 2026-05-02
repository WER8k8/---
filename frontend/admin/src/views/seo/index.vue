<template>
  <div>
    <div class="flex items-center justify-between mb-8">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">
          SEO概览
        </h1>
        <p class="text-gray-500 mt-1">
          监控网站SEO表现和关键词排名
        </p>
      </div>
      <div class="flex items-center space-x-3">
        <a-button
          type="primary"
          @click="refreshData"
        >
          <RefreshOutlined class="w-4 h-4 mr-2" />
          刷新数据
        </a-button>
      </div>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      <a-card class="bg-gradient-to-br from-green-500 to-green-600 text-white">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-green-100 text-sm">
              总关键词数
            </p>
            <p class="text-3xl font-bold mt-1">
              {{ stats.total_keywords || 0 }}
            </p>
          </div>
          <div class="w-12 h-12 bg-white/20 rounded-lg flex items-center justify-center">
            <SearchOutlined class="w-6 h-6" />
          </div>
        </div>
      </a-card>
      <a-card class="bg-gradient-to-br from-blue-500 to-blue-600 text-white">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-blue-100 text-sm">
              已排名关键词
            </p>
            <p class="text-3xl font-bold mt-1">
              {{ stats.ranked_keywords || 0 }}
            </p>
          </div>
          <div class="w-12 h-12 bg-white/20 rounded-lg flex items-center justify-center">
            <TrendingUpOutlined class="w-6 h-6" />
          </div>
        </div>
      </a-card>
      <a-card class="bg-gradient-to-br from-purple-500 to-purple-600 text-white">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-purple-100 text-sm">
              平均排名
            </p>
            <p class="text-3xl font-bold mt-1">
              {{ stats.avg_rank || '-' }}
            </p>
          </div>
          <div class="w-12 h-12 bg-white/20 rounded-lg flex items-center justify-center">
            <BarChartOutlined class="w-6 h-6" />
          </div>
        </div>
      </a-card>
      <a-card>
        <div class="flex items-center justify-between">
          <div>
            <p class="text-gray-500 text-sm">
              审计得分
            </p>
            <p class="text-3xl font-bold mt-1 text-gray-900">
              {{ stats.last_audit_score || 0 }}
            </p>
          </div>
          <div class="w-12 h-12 bg-orange-50 rounded-lg flex items-center justify-center">
            <AuditOutlined class="w-6 h-6 text-orange-500" />
          </div>
        </div>
      </a-card>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
      <a-card title="关键词排名趋势">
        <v-chart
          class="h-64"
          :option="keywordTrendChart"
          autoresize
        />
      </a-card>
      <a-card title="页面SEO状态分布">
        <v-chart
          class="h-64"
          :option="pageCoverageChart"
          autoresize
        />
      </a-card>
    </div>

    <a-card title="最近优化的页面">
      <a-table
        :columns="pageColumns"
        :data-source="recentPages"
        :pagination="false"
        row-key="id"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <a-tag :color="getStatusColor(record.status)">
              {{ getStatusText(record.status) }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'optimized_at'">
            {{ record.optimized_at ? formatDate(record.optimized_at) : '-' }}
          </template>
        </template>
      </a-table>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import {
  SearchOutlined,
  ArrowUpOutlined as TrendingUpOutlined,
  BarChartOutlined,
  AuditOutlined,
  RestOutlined as RefreshOutlined,
} from '@ant-design/icons-vue'
import { Card as ACard, Button as AButton, Table as ATable, Tag as ATag } from 'ant-design-vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, PieChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import { seoAPI } from '@/api'

use([CanvasRenderer, LineChart, PieChart, GridComponent, TooltipComponent, LegendComponent])

const stats = ref({
  total_keywords: 0,
  ranked_keywords: 0,
  avg_rank: null,
  ai_optimized_pages: 0,
  last_audit_score: 0,
})

const recentPages = ref<any[]>([])

const pageColumns = [
  { title: '页面标题', key: 'title', width: 300 },
  { title: 'SEO标题', key: 'meta_title', width: 250 },
  { title: '状态', key: 'status', width: 100 },
  { title: '优化时间', key: 'optimized_at', width: 150 },
]

const keywordTrendChart = computed(() => ({
  xAxis: {
    type: 'category',
    data: ['1月', '2月', '3月', '4月', '5月', '6月'],
  },
  yAxis: {
    type: 'value',
    name: '平均排名',
    inverse: true,
  },
  tooltip: {
    trigger: 'axis',
  },
  series: [
    {
      data: [15, 13, 11, 9, 8, 7],
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
      lineStyle: {
        color: '#22c55e',
      },
    },
  ],
}))

const pageCoverageChart = computed(() => ({
  tooltip: {
    trigger: 'item',
  },
  legend: {
    orient: 'vertical',
    right: '5%',
    top: 'center',
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
      label: {
        show: false,
      },
      emphasis: {
        label: {
          show: true,
          fontSize: 14,
          fontWeight: 'bold',
        },
      },
      data: [
        { value: 45, name: '已优化', itemStyle: { color: '#22c55e' } },
        { value: 30, name: '待优化', itemStyle: { color: '#f59e0b' } },
        { value: 15, name: '优化中', itemStyle: { color: '#3b82f6' } },
        { value: 10, name: '未优化', itemStyle: { color: '#9ca3af' } },
      ],
    },
  ],
}))

function getStatusColor(status: string) {
  if (status === 'optimized') return 'green'
  if (status === 'pending') return 'gold'
  if (status === 'failed') return 'red'
  return 'default'
}

function getStatusText(status: string) {
  if (status === 'optimized') return '已优化'
  if (status === 'pending') return '待优化'
  if (status === 'failed') return '优化失败'
  return status
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleString('zh-CN')
}

async function fetchDashboard() {
  try {
    const res = await seoAPI.dashboard()
    stats.value = res.data
  } catch (e) {
    console.error('Failed to fetch SEO dashboard:', e)
  }
}

async function fetchRecentPages() {
  try {
    const res = await seoAPI.pages({ page_size: 10 })
    recentPages.value = res.data.items || []
  } catch (e) {
    console.error('Failed to fetch recent pages:', e)
  }
}

function refreshData() {
  fetchDashboard()
  fetchRecentPages()
}

onMounted(async () => {
  await fetchDashboard()
  await fetchRecentPages()
})
</script>
