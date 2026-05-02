<template>
  <div>
    <div class="flex items-center justify-between mb-8">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">
          数据概览
        </h1>
        <p class="text-gray-500 mt-1">
          欢迎回来，查看今日数据统计
        </p>
      </div>
      <div class="flex items-center space-x-4">
        <a-select
          v-model="timeRange"
          class="w-40"
          @change="() => fetchDashboard()"
        >
          <a-select-option value="today">
            今日
          </a-select-option>
          <a-select-option value="week">
            本周
          </a-select-option>
          <a-select-option value="month">
            本月
          </a-select-option>
        </a-select>
      </div>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
      <a-card class="bg-gradient-to-br from-primary-500 to-primary-600 text-white">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-primary-100 text-sm">
              总产品数
            </p>
            <p class="text-3xl font-bold mt-1">
              {{ stats.totalProducts || 0 }}
            </p>
          </div>
          <div class="w-12 h-12 bg-white/20 rounded-lg flex items-center justify-center">
            <PauseOutlined class="w-6 h-6" />
          </div>
        </div>
      </a-card>
      <a-card class="bg-gradient-to-br from-secondary-500 to-secondary-600 text-white">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-secondary-100 text-sm">
              询盘数量
            </p>
            <p class="text-3xl font-bold mt-1">
              {{ stats.totalInquiries || 0 }}
            </p>
          </div>
          <div class="w-12 h-12 bg-white/20 rounded-lg flex items-center justify-center">
            <MessageOutlined class="w-6 h-6" />
          </div>
        </div>
      </a-card>
      <a-card class="bg-gradient-to-br from-purple-500 to-purple-600 text-white">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-purple-100 text-sm">
              AI优化页面
            </p>
            <p class="text-3xl font-bold mt-1">
              {{ stats.aiOptimizedPages || 0 }}
            </p>
          </div>
          <div class="w-12 h-12 bg-white/20 rounded-lg flex items-center justify-center">
            <MailOutlined class="w-6 h-6" />
          </div>
        </div>
      </a-card>
      <a-card>
        <div class="flex items-center justify-between">
          <div>
            <p class="text-gray-500 text-sm">
              关键词总数
            </p>
            <p class="text-3xl font-bold mt-1 text-gray-900">
              {{ stats.totalKeywords || 0 }}
            </p>
          </div>
          <div class="w-12 h-12 bg-blue-50 rounded-lg flex items-center justify-center">
            <SearchOutlined class="w-6 h-6 text-blue-500" />
          </div>
        </div>
      </a-card>
      <a-card>
        <div class="flex items-center justify-between">
          <div>
            <p class="text-gray-500 text-sm">
              已排名关键词
            </p>
            <p class="text-3xl font-bold mt-1 text-gray-900">
              {{ stats.rankedKeywords || 0 }}
            </p>
          </div>
          <div class="w-12 h-12 bg-green-50 rounded-lg flex items-center justify-center">
            <TrendingUpOutlined class="w-6 h-6 text-green-500" />
          </div>
        </div>
      </a-card>
      <a-card>
        <div class="flex items-center justify-between">
          <div>
            <p class="text-gray-500 text-sm">
              平均排名
            </p>
            <p class="text-3xl font-bold mt-1 text-gray-900">
              {{ stats.avgRank || '-' }}
            </p>
          </div>
          <div class="w-12 h-12 bg-orange-50 rounded-lg flex items-center justify-center">
            <BarChartOutlined class="w-6 h-6 text-orange-500" />
          </div>
        </div>
      </a-card>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
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
          :option="pageStatusChart"
          autoresize
        />
      </a-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import {
  PauseOutlined,
  MessageOutlined,
  MailOutlined,
  SearchOutlined,
  BarChartOutlined,
} from '@ant-design/icons-vue'
import { Select as ASelect, SelectOption as ASelectOption, Card as ACard } from 'ant-design-vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, PieChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import { seoAPI } from '@/api'

use([CanvasRenderer, LineChart, PieChart, GridComponent, TooltipComponent, LegendComponent])

const timeRange = ref('week')
const loading = ref(false)

const stats = ref({
  totalProducts: 0,
  totalInquiries: 0,
  aiOptimizedPages: 0,
  totalKeywords: 0,
  rankedKeywords: 0,
  avgRank: null,
})

const keywordTrendChart = computed(() => ({
  xAxis: {
    type: 'category',
    data: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'],
  },
  yAxis: {
    type: 'value',
    name: '平均排名',
  },
  series: [
    {
      data: [12, 10, 11, 9, 8, 8, 7],
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
    },
  ],
}))

const pageStatusChart = computed(() => ({
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

async function fetchDashboard() {
  loading.value = true
  try {
    const res = await seoAPI.dashboard()
    const data = res.data || {}
    stats.value = {
      totalProducts: data.total_products || 0,
      totalInquiries: data.total_inquiries || 0,
      aiOptimizedPages: data.ai_optimized_pages || 0,
      totalKeywords: data.total_keywords || 0,
      rankedKeywords: data.ranked_keywords || 0,
      avgRank: data.avg_rank || null,
    }
  } catch (e) {
    console.error('Failed to fetch dashboard:', e)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchDashboard()
})
</script>