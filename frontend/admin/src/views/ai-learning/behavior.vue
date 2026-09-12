<template>
  <YdPage title="用户行为分析" subtitle="页面停留 · 点击热力图 · 行为模式挖掘（真实流量埋点）" surface="elevated">
    <template #actions>
      <a-select v-model:value="period" style="width: 120px" @change="loadBehavior">
        <a-select-option value="7d">近 7 天</a-select-option>
        <a-select-option value="30d">近 30 天</a-select-option>
      </a-select>
    </template>
    <a-alert
      v-if="loadError"
      type="warning"
      show-icon
      :message="loadError"
      style="margin-bottom: 16px"
    />
    <div class="space-y-6">
      <a-row :gutter="16">
        <a-col :span="6" v-for="s in stats" :key="s.l">
          <a-card hoverable size="small">
            <a-statistic :title="s.l" :value="s.v" :value-style="{ color: s.c }" />
          </a-card>
        </a-col>
      </a-row>
      <a-row :gutter="16">
        <a-col :span="12">
          <a-card title="转化漏斗" size="small">
            <a-empty v-if="!funnel.length" description="暂无漏斗数据" />
            <div v-else class="space-y-3">
              <div v-for="row in funnel" :key="row.stage" class="flex justify-between text-sm">
                <span>{{ row.stage }}</span>
                <span class="font-semibold">{{ row.count }}</span>
              </div>
            </div>
          </a-card>
        </a-col>
        <a-col :span="12">
          <a-card title="核心指标" size="small">
            <a-empty v-if="!summary.unique_visitors && !summary.page_views" description="暂无访问数据" />
            <div v-else class="space-y-4">
              <div v-for="m in metrics" :key="m.l">
                <div class="flex justify-between text-sm mb-1">
                  <span>{{ m.l }}</span>
                  <span class="font-semibold">{{ m.v }}</span>
                </div>
                <a-progress :percent="m.p" :stroke-color="m.c" size="small" :show-info="false" />
              </div>
            </div>
          </a-card>
        </a-col>
      </a-row>
      <a-card title="页面点击排行" size="small">
        <a-empty v-if="!pages.length" description="暂无页面点击记录" />
        <div v-else ref="tablePanelRef" class="yd-panel yd-table-panel">
          <YdTableToolbar :loading="loading" :target-ref="tablePanelRef" :show-export="false" @refresh="loadBehavior" />
          <YdDataTable
            :columns="c"
            :data-source="pages"
            :pagination="false"
            :table-props="{ size: tableSize, rowKey: 'id' }"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'heat'">
                <div class="w-full h-2 bg-gray-100 rounded overflow-hidden">
                  <div
                    class="h-full rounded"
                    :style="{ width: record.heat + '%', background: 'linear-gradient(90deg,#22c55e,#f59e0b,#ef4444)' }"
                  />
                </div>
              </template>
            </template>
          </YdDataTable>
        </div>
      </a-card>
    </div>
  </YdPage>
</template>
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { YdDataTable, YdPage, YdTableToolbar } from '@/components/youding'
import { useUiPreferencesStore } from '@/stores/uiPreferences'
import { apiGet } from '@/utils/api'

const period = ref('7d')
const loading = ref(false)
const loadError = ref('')
const tablePanelRef = ref<HTMLElement | null>(null)
const ui = useUiPreferencesStore()
const { antTableSize: tableSize } = storeToRefs(ui)

const stats = ref([
  { l: '独立访客', v: '0', c: '#4a9b8c' },
  { l: '页面浏览', v: '0', c: '#8b5cf6' },
  { l: '总点击', v: '0', c: '#22c55e' },
  { l: '跳出率', v: '—', c: '#ef4444' },
])
const summary = ref<Record<string, number>>({})
const funnel = ref<Array<{ stage: string; count: number }>>([])
const metrics = ref<Array<{ l: string; v: string; p: number; c: string }>>([])
const c = [
  { title: '页面', dataIndex: 'p', key: 'p' },
  { title: '点击量', dataIndex: 'v', key: 'v' },
  { title: '热力', dataIndex: 'heat', key: 'heat' },
]
const pages = ref<Array<{ id: number; p: string; v: string; heat: number }>>([])

async function loadBehavior() {
  loading.value = true
  loadError.value = ''
  try {
    const data = await apiGet<{
      summary?: Record<string, number>
      bounce_rate?: number
      conversion_funnel?: Array<{ stage: string; count: number }>
      heatmap_data?: Array<{ path?: string; label?: string; clicks?: number }>
    }>('/ai-learning/behavior', { period: period.value })

    const s = data.summary || {}
    summary.value = s
    const visitors = Number(s.unique_visitors || 0)
    const pageViews = Number(s.page_views || 0)
    const clicks = Number(s.total_clicks || 0)
    const bounce = typeof data.bounce_rate === 'number' ? `${data.bounce_rate}%` : '—'

    stats.value = [
      { l: '独立访客', v: visitors.toLocaleString('zh-CN'), c: '#4a9b8c' },
      { l: '页面浏览', v: pageViews.toLocaleString('zh-CN'), c: '#8b5cf6' },
      { l: '总点击', v: clicks.toLocaleString('zh-CN'), c: '#22c55e' },
      { l: '跳出率', v: bounce, c: '#ef4444' },
    ]

    funnel.value = (data.conversion_funnel || []).map((row) => ({
      stage: row.stage,
      count: Number(row.count || 0),
    }))

    const conv = Number(s.conversion_rate || 0)
    metrics.value = [
      { l: '转化率', v: conv ? `${conv}%` : '—', p: Math.min(100, conv), c: '#f59e0b' },
      { l: '询盘数', v: String(s.inquiries || 0), p: Math.min(100, Number(s.inquiries || 0)), c: '#4a9b8c' },
      { l: '表单打开', v: String(s.form_opens || 0), p: Math.min(100, Number(s.form_opens || 0)), c: '#8b5cf6' },
    ]

    const heat = data.heatmap_data || []
    const maxClicks = Math.max(...heat.map((h) => Number(h.clicks || 0)), 1)
    pages.value = heat.map((row, i) => ({
      id: i + 1,
      p: row.path || row.label || '—',
      v: String(row.clicks || 0),
      heat: Math.round((Number(row.clicks || 0) / maxClicks) * 100),
    }))
  } catch (e: unknown) {
    loadError.value = e instanceof Error ? e.message : '行为数据加载失败'
    funnel.value = []
    pages.value = []
    metrics.value = []
    stats.value = stats.value.map((s) => ({ ...s, v: s.l === '跳出率' ? '—' : '0' }))
  } finally {
    loading.value = false
  }
}

onMounted(loadBehavior)
</script>
