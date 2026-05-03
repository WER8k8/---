<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">
          数据分析
        </h1>
        <p class="text-gray-500 mt-1">
          查看系统数据统计和分析
        </p>
      </div>
    </div>

    <a-row
      :gutter="16"
      class="mb-6"
    >
      <a-col :span="6">
        <a-card class="text-center">
          <div class="text-3xl font-bold text-primary">
            1,234
          </div>
          <div class="text-gray-500 mt-2">
            总访问量
          </div>
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card class="text-center">
          <div class="text-3xl font-bold text-green-500">
            56
          </div>
          <div class="text-gray-500 mt-2">
            询盘数量
          </div>
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card class="text-center">
          <div class="text-3xl font-bold text-blue-500">
            85%
          </div>
          <div class="text-gray-500 mt-2">
            SEO覆盖率
          </div>
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card class="text-center">
          <div class="text-3xl font-bold text-orange-500">
            12
          </div>
          <div class="text-gray-500 mt-2">
            活跃用户
          </div>
        </a-card>
      </a-col>
    </a-row>

    <a-row :gutter="16">
      <a-col :span="16">
        <a-card title="访问趋势">
          <div class="h-64">
            <v-chart
              :option="visitChartOption"
              autoresize
            />
          </div>
        </a-card>
      </a-col>
      <a-col :span="8">
        <a-card title="流量来源">
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
      class="mt-6"
    >
      <a-table
        :columns="logColumns"
        :data-source="logs"
        :pagination="logPagination"
        :loading="loading"
        row-key="id"
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
      </a-table>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import {
  Card as ACard,
  Table as ATable,
  Tag as ATag,
  Row as ARow,
  Col as ACol,
} from 'ant-design-vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, PieChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
} from 'echarts/components'
import { systemAPI } from '@/api'

use([
  CanvasRenderer,
  LineChart,
  PieChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
])

const logs = ref<any[]>([])
const loading = ref(false)

const logPagination = ref({
  current: 1,
  pageSize: 10,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total: number) => `共 ${total} 条记录`,
  total: 0,
})

const logColumns = [
  { title: '用户名', key: 'username', width: 120 },
  { title: '操作', key: 'action', width: 150 },
  { title: '资源类型', key: 'resource_type', width: 120 },
  { title: 'IP地址', key: 'ip_address', width: 150 },
  { title: '时间', key: 'created_at', width: 150 },
]

const visitChartOption = computed(() => ({
  tooltip: {
    trigger: 'axis',
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '3%',
    containLabel: true,
  },
  xAxis: {
    type: 'category',
    boundaryGap: false,
    data: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'],
  },
  yAxis: {
    type: 'value',
  },
  series: [
    {
      name: '访问量',
      type: 'line',
      data: [120, 200, 150, 250, 180, 300, 280],
      smooth: true,
      lineStyle: {
        color: '#1890ff',
      },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0,
          y: 0,
          x2: 0,
          y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(24, 144, 255, 0.3)' },
            { offset: 1, color: 'rgba(24, 144, 255, 0.05)' },
          ],
        },
      },
    },
  ],
}))

const sourceChartOption = computed(() => ({
  tooltip: {
    trigger: 'item',
  },
  legend: {
    orient: 'vertical',
    left: 'left',
  },
  series: [
    {
      name: '流量来源',
      type: 'pie',
      radius: '50%',
      data: [
        { value: 35, name: '搜索引擎' },
        { value: 25, name: '直接访问' },
        { value: 20, name: '社交媒体' },
        { value: 15, name: '外部链接' },
        { value: 5, name: '其他' },
      ],
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowOffsetX: 0,
          shadowColor: 'rgba(0, 0, 0, 0.5)',
        },
      },
    },
  ],
}))

function getActionColor(action: string) {
  if (action.includes('CREATE')) return 'green'
  if (action.includes('UPDATE')) return 'blue'
  if (action.includes('DELETE')) return 'red'
  return 'default'
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
  }
  return actionMap[action] || action
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleString('zh-CN')
}

async function fetchLogs(page = 1) {
  loading.value = true
  logPagination.value.current = page
  try {
    const res = await systemAPI.auditLogs({ page, page_size: logPagination.value.pageSize })
    logs.value = res.data.data || []
    logPagination.value.total = res.data.total || 0
  } catch (e) {
    console.error('Failed to fetch logs:', e)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchLogs()
})
</script>