<template>
  <div class="traffic-board">
    <div class="flex flex-wrap items-center justify-between gap-3 mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">{{ title }}</h1>
        <p class="text-sm text-gray-500 mt-1">{{ subtitle }}</p>
      </div>
      <div class="flex items-center gap-2">
        <a-select
          v-model:value="period"
          style="width: 120px"
          size="small"
          :options="periodOptions"
          @change="load"
        />
        <a-button type="primary" ghost size="small" :loading="loading" @click="load">
          刷新
        </a-button>
        <a-button size="small" @click="exportCsv">导出 CSV</a-button>
      </div>
    </div>

    <a-alert v-if="error" type="warning" show-icon class="mb-4" :message="error" />
    <a-alert
      v-if="dataHonesty && !dataHonesty.has_production_activity"
      type="info"
      show-icon
      class="mb-4"
      message="当前无真实业务流量"
      :description="honestyDescription"
    />

    <a-row :gutter="16" class="mb-6">
      <a-col v-for="kpi in kpiCards" :key="kpi.label" :xs="12" :sm="8" :lg="4">
        <a-card class="text-center rounded-2xl border-0 shadow-sm">
          <div class="text-2xl font-bold" :class="kpi.color">{{ kpi.value }}</div>
          <div class="text-gray-500 text-sm mt-1">{{ kpi.label }}</div>
        </a-card>
      </a-col>
    </a-row>

    <a-row :gutter="16" class="mb-6">
      <a-col :span="16">
        <a-card title="每日访问趋势" class="rounded-2xl">
          <a-table
            :columns="dailyColumns"
            :data-source="board?.daily || []"
            :pagination="false"
            size="small"
            row-key="date"
          />
        </a-card>
      </a-col>
      <a-col :span="8">
        <a-card title="转化漏斗" class="rounded-2xl">
          <div v-for="step in board?.conversion_funnel || []" :key="step.stage" class="mb-3">
            <div class="flex justify-between text-sm mb-1">
              <span>{{ step.stage }}</span>
              <span class="font-medium">{{ step.count }}</span>
            </div>
            <a-progress
              :percent="funnelPercent(step.count)"
              :show-info="false"
              stroke-color="#0ea5e9"
            />
          </div>
        </a-card>
      </a-col>
    </a-row>

    <a-row :gutter="16" class="mb-6">
      <a-col :span="12">
        <a-card title="点击最多（哪条入口）" class="rounded-2xl">
          <a-table
            :columns="clickColumns"
            :data-source="board?.top_clicks || []"
            :pagination="{ pageSize: 8 }"
            size="small"
            row-key="label"
          />
        </a-card>
      </a-col>
      <a-col :span="12">
        <a-card title="带来客户/电话的内容" class="rounded-2xl">
          <a-table
            :columns="contentColumns"
            :data-source="board?.top_content || []"
            :pagination="{ pageSize: 8 }"
            size="small"
            row-key="content_ref"
          />
        </a-card>
      </a-col>
    </a-row>

    <a-card
      v-if="board?.subordinate_traffic?.length"
      title="下级代理流量汇总"
      class="rounded-2xl mb-6"
    >
      <a-table
        :columns="subColumns"
        :data-source="board.subordinate_traffic"
        size="small"
        row-key="node_id"
      />
    </a-card>

    <a-card
      v-if="board?.by_tenant?.length"
      title="各租户流量（平台汇总）"
      class="rounded-2xl mb-6"
    >
      <a-table
        :columns="tenantColumns"
        :data-source="board.by_tenant"
        size="small"
        row-key="tenant_id"
      />
    </a-card>

    <a-card title="最近转化（询盘/电话）" class="rounded-2xl">
      <a-table
        :columns="convColumns"
        :data-source="board?.recent_conversions || []"
        :pagination="{ pageSize: 10 }"
        size="small"
        row-key="inquiry_id"
      />
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { apiGet, getAuthToken } from '@/utils/api'

const props = withDefaults(
  defineProps<{
    apiPath: string
    title?: string
    subtitle?: string
  }>(),
  {
    title: '流量看板',
    subtitle: '每日访客 · 点击排行 · 哪条内容带来询盘与电话',
  },
)

const period = ref('7d')
const loading = ref(false)
const error = ref('')
const board = ref<Record<string, any> | null>(null)

interface DataHonesty {
  has_production_activity?: boolean
  excluded_inquiries?: number
  excluded_analytics_events?: number
}

const dataHonesty = computed<DataHonesty | null>(() => board.value?.data_honesty ?? null)

const honestyDescription = computed(() => {
  const h = dataHonesty.value
  if (!h) return '本看板仅统计已归属租户的真实访问与转化，已过滤测试询盘与探针埋点。'
  const parts = ['本看板仅统计已归属租户的真实访问与转化。']
  if (h.excluded_inquiries || h.excluded_analytics_events) {
    parts.push(
      `已过滤 ${h.excluded_inquiries ?? 0} 条测试询盘、${h.excluded_analytics_events ?? 0} 条探针埋点。`,
    )
  }
  return parts.join(' ')
})

const periodOptions = [
  { label: '今日', value: '1d' },
  { label: '7天', value: '7d' },
  { label: '30天', value: '30d' },
  { label: '90天', value: '90d' },
]

const summary = computed(() => board.value?.summary || {})

const kpiCards = computed(() => [
  { label: '独立访客', value: summary.value.unique_visitors ?? '—', color: 'text-sky-600' },
  { label: '页面浏览', value: summary.value.page_views ?? '—', color: 'text-indigo-600' },
  { label: '总点击', value: summary.value.total_clicks ?? '—', color: 'text-violet-600' },
  { label: '打开表单', value: summary.value.form_opens ?? '—', color: 'text-amber-600' },
  { label: '询盘/电话', value: summary.value.inquiries ?? '—', color: 'text-emerald-600' },
  {
    label: '转化率',
    value: summary.value.conversion_rate != null ? `${summary.value.conversion_rate}%` : '—',
    color: 'text-rose-600',
  },
])

const dailyColumns = [
  { title: '日期', dataIndex: 'date', key: 'date' },
  { title: '访客', dataIndex: 'visitors', key: 'visitors' },
  { title: '浏览', dataIndex: 'page_views', key: 'page_views' },
  { title: '点击', dataIndex: 'clicks', key: 'clicks' },
  { title: '询盘', dataIndex: 'inquiries', key: 'inquiries' },
]

const clickColumns = [
  { title: '入口/按钮', dataIndex: 'label', key: 'label', ellipsis: true },
  { title: '页面', dataIndex: 'path', key: 'path', ellipsis: true },
  { title: '点击', dataIndex: 'clicks', key: 'clicks', width: 80 },
]

const contentColumns = [
  { title: '内容', dataIndex: 'content_ref', key: 'content_ref', ellipsis: true },
  { title: '浏览', dataIndex: 'views', key: 'views', width: 70 },
  { title: '点击', dataIndex: 'clicks', key: 'clicks', width: 70 },
  { title: '询盘', dataIndex: 'inquiries', key: 'inquiries', width: 70 },
]

const subColumns = [
  { title: '代理', dataIndex: 'name', key: 'name' },
  { title: '层级', dataIndex: 'level', key: 'level', width: 70 },
  { title: '访客', dataIndex: 'unique_visitors', key: 'uv', width: 80 },
  { title: '点击', dataIndex: 'total_clicks', key: 'clicks', width: 80 },
  { title: '询盘', dataIndex: 'inquiries', key: 'inq', width: 80 },
]

const tenantColumns = [
  { title: '租户', dataIndex: 'tenant_name', key: 'name' },
  { title: '域名', dataIndex: 'domain', key: 'domain', ellipsis: true },
  { title: '访客', dataIndex: 'unique_visitors', key: 'uv' },
  { title: '询盘', dataIndex: 'inquiries', key: 'inq' },
]

const convColumns = [
  { title: '姓名', dataIndex: 'name', key: 'name', width: 100 },
  { title: '电话', dataIndex: 'phone', key: 'phone', width: 120 },
  { title: '落地页', dataIndex: 'landing_path', key: 'landing', ellipsis: true },
  { title: '最后点击', dataIndex: 'last_click_label', key: 'click', ellipsis: true },
  { title: '产品/内容', dataIndex: 'product', key: 'product', ellipsis: true },
  { title: '时间', dataIndex: 'created_at', key: 'time', width: 160 },
]

function funnelPercent(count: number) {
  const first = board.value?.conversion_funnel?.[0]?.count || 1
  return Math.min(100, Math.round((count / first) * 100))
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const sep = props.apiPath.includes('?') ? '&' : '?'
    board.value = await apiGet(`${props.apiPath}${sep}period=${period.value}`)
  } catch (e: unknown) {
    const err = e as { message?: string }
    error.value = err.message || '加载失败'
    board.value = null
  } finally {
    loading.value = false
  }
}

async function exportCsv() {
  const tk = getAuthToken()
  const url = `/api/v1/analytics/export?format=csv&period=${encodeURIComponent(period.value)}`
  try {
    const res = await fetch(url, { headers: tk ? { Authorization: `Bearer ${tk}` } : {} })
    if (!res.ok) throw new Error('导出失败')
    const blob = await res.blob()
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = `traffic_${period.value}.csv`
    a.click()
    URL.revokeObjectURL(a.href)
  } catch {
    error.value = 'CSV 导出失败，请稍后重试'
  }
}

watch(() => props.apiPath, load, { immediate: true })
</script>

<style scoped>
.traffic-board {
  min-height: 100%;
}
</style>
