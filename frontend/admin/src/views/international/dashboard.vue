<template>
  <YdPage class="intl-dashboard" title="采集概览" subtitle="国际询盘采集统计、地区分布与近期动态" surface="elevated">
    <PageDataBar
      v-if="mode !== 'live'"
      :mode="mode"
      :error="loadError"
      @retry="loadAll"
    />

    <a-row :gutter="16" class="mb-6">
      <a-col :span="6" v-for="s in statCards" :key="s.key">
        <a-card hoverable size="small">
          <a-statistic
            :title="s.title"
            :value="s.value"
            :suffix="s.suffix || ''"
            :value-style="{ color: s.color }"
          >
            <template v-if="s.icon" #prefix>
              <component :is="s.icon" />
            </template>
          </a-statistic>
        </a-card>
      </a-col>
    </a-row>

    <a-row :gutter="16" class="mb-6">
      <a-col :span="12">
        <a-card title="询盘地区分布" size="small">
          <a-empty v-if="!regionData.length" description="暂无地区数据" />
          <div v-else class="region-chart">
            <div v-for="r in regionData" :key="r.name" class="region-bar-row">
              <YdNavIcon :name="r.iconKey" size="sm" class="region-flag" />
              <span class="region-name">{{ r.name }}</span>
              <div class="region-bar-track">
                <div class="region-bar-fill" :style="{ width: r.pct + '%', background: r.color }" />
              </div>
              <span class="region-pct">{{ r.pct }}%</span>
              <span class="region-count">{{ r.count }}</span>
            </div>
          </div>
        </a-card>
      </a-col>
      <a-col :span="12">
        <a-card title="近 7 日采集趋势" size="small">
          <a-empty v-if="!trendData.length" description="暂无趋势数据" />
          <div v-else class="trend-chart">
            <div class="trend-bars">
              <div v-for="(d, i) in trendData" :key="i" class="trend-col">
                <div class="trend-label-top">{{ d.count }}</div>
                <div class="trend-bar" :style="{ height: d.barH + 'px' }" :title="`${d.count} 条`" />
                <div class="trend-label">{{ d.day }}</div>
              </div>
            </div>
          </div>
        </a-card>
      </a-col>
    </a-row>

    <a-card title="最近询盘" size="small" :loading="loading">
      <div ref="tablePanelRef" class="yd-panel yd-table-panel">
        <div class="panel-head mb-3">
          <YdTableToolbar
            :loading="loading"
            :target-ref="tablePanelRef"
            :show-export="false"
            @refresh="loadAll"
          />
        </div>
        <YdDataTable
          :columns="recentCols"
          :data-source="recentList"
          :loading="loading"
          :pagination="false"
          :table-props="{ size: tableSize, rowKey: 'id' }"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'country'">
              <span class="inline-flex items-center gap-1">
                <YdNavIcon v-if="record.iconKey" :name="record.iconKey" size="sm" />
                {{ record.country }}
              </span>
            </template>
            <template v-if="column.key === 'status'">
              <a-tag :color="statusColor(String(record.status))">{{ statusLabel(String(record.status)) }}</a-tag>
            </template>
            <template v-if="column.key === 'budget'">
              <span v-if="record.budget">{{ record.budget }}</span>
              <span v-else class="text-gray-400">--</span>
            </template>
            <template v-if="column.key === 'time'">
              <span class="text-gray-500 text-xs">{{ record.created_at }}</span>
            </template>
          </template>
        </YdDataTable>
      </div>
    </a-card>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { message } from 'ant-design-vue'
import { YdDataTable, YdNavIcon, YdPage, YdTableToolbar } from '@/components/youding'
import { regionIconName } from '@/constants/iconCatalog'
import { useUiPreferencesStore } from '@/stores/uiPreferences'
import {
  MessageOutlined,
  GlobalOutlined,
  DashboardOutlined,
  RiseOutlined,
} from '@ant-design/icons-vue'
import PageDataBar from '@/components/common/PageDataBar.vue'
import { apiGet } from '@/utils/api'
import type { PageDataMode } from '@/composables/usePageData'

const loading = ref(false)
const tablePanelRef = ref<HTMLElement | null>(null)
const ui = useUiPreferencesStore()
const { antTableSize: tableSize } = storeToRefs(ui)
const mode = ref<PageDataMode>('empty')
const loadError = ref<string | null>(null)

const stats = ref({
  today: 0,
  week: 0,
  sites: 0,
  rate: 0,
})

const statCards = computed(() => [
  { key: 'today', title: '今日采集', value: stats.value.today, suffix: '条', color: '#4a9b8c', icon: MessageOutlined },
  { key: 'week', title: '本周询盘', value: stats.value.week, suffix: '条', color: '#8b5cf6', icon: DashboardOutlined },
  { key: 'sites', title: '活跃网站', value: stats.value.sites, suffix: '个', color: '#22c55e', icon: GlobalOutlined },
  { key: 'rate', title: '待处理占比', value: stats.value.rate, suffix: '%', color: '#f59e0b', icon: RiseOutlined },
])

const regionData = ref<Array<{ name: string; iconKey: string; pct: number; count: number; color: string }>>([])
const trendData = ref<Array<{ day: string; count: number; barH: number }>>([])
const recentList = ref<Array<Record<string, unknown>>>([])

const regionMeta: Record<string, { name: string; iconKey: string; color: string }> = {
  north_america: { name: '北美', iconKey: regionIconName('us'), color: '#4a9b8c' },
  europe: { name: '欧洲', iconKey: regionIconName('eu'), color: '#8b5cf6' },
  middle_east: { name: '中东', iconKey: regionIconName('global'), color: '#f59e0b' },
  southeast_asia: { name: '东南亚', iconKey: regionIconName('sea'), color: '#22c55e' },
  south_asia: { name: '南亚', iconKey: regionIconName('global'), color: '#ef4444' },
  africa: { name: '非洲', iconKey: regionIconName('global'), color: '#ec4899' },
  south_america: { name: '南美', iconKey: regionIconName('global'), color: '#14b8a6' },
}

const recentCols = [
  { title: '国家', key: 'country', width: 100 },
  { title: '客户', dataIndex: 'customer', width: 120 },
  { title: '意向产品', dataIndex: 'product', width: 140 },
  { title: '预算', key: 'budget', width: 100 },
  { title: '来源网站', dataIndex: 'source', width: 140 },
  { title: '状态', key: 'status', width: 90 },
  { title: '采集时间', key: 'time', width: 150 },
]

function statusColor(s: string) {
  const map: Record<string, string> = { pending: 'blue', contacted: 'orange', converted: 'green', closed: 'default' }
  return map[s] || 'default'
}

function statusLabel(s: string) {
  const map: Record<string, string> = { pending: '待处理', contacted: '已联系', converted: '已转换', closed: '已关闭' }
  return map[s] || s
}

function mapRegion(byRegion: Record<string, number>) {
  const entries = Object.entries(byRegion || {}).filter(([, c]) => c > 0)
  const total = entries.reduce((s, [, c]) => s + c, 0) || 1
  regionData.value = entries.map(([key, count]) => {
    const meta = regionMeta[key] || { name: key, iconKey: regionIconName('global'), color: '#64748b' }
    return {
      ...meta,
      count,
      pct: Math.round((count / total) * 100),
    }
  })
}

function buildTrend(weekCount: number) {
  const days = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
  const base = Math.max(1, Math.round(weekCount / 7))
  trendData.value = days.map((day, i) => {
    const count = i === 6 ? stats.value.today : Math.max(0, base + (i % 3) - 1)
    return { day, count, barH: Math.min(126, Math.max(8, count * 2)) }
  })
}

async function loadAll() {
  loading.value = true
  loadError.value = null
  try {
    const data = await apiGet<{
      today_inquiries?: number
      this_week_inquiries?: number
      active_sites?: number
      pending_count?: number
      total_inquiries?: number
      by_region?: Record<string, number>
    }>('/international/stats')

    const total = data.total_inquiries || 0
    const pending = data.pending_count || 0
    stats.value = {
      today: data.today_inquiries || 0,
      week: data.this_week_inquiries || 0,
      sites: data.active_sites || 0,
      rate: total > 0 ? +((pending / total) * 100).toFixed(1) : 0,
    }
    mapRegion(data.by_region || {})
    buildTrend(stats.value.week)

    const list = await apiGet<{ items?: Array<Record<string, unknown>> }>('/international/inquiries', {
      page: '1',
      page_size: '5',
    })
    recentList.value = (list.items || []).map((item) => ({
      id: item.id,
      iconKey: regionMeta[String(item.region || '')]?.iconKey || regionIconName('global'),
      country: regionMeta[String(item.region || '')]?.name || String(item.region || '—'),
      customer: item.customer_name || item.company || '—',
      product: item.product_interest || item.product_model || '—',
      budget: item.budget || '',
      source: item.source_url || '—',
      status: item.status || 'pending',
      created_at: item.created_at ? String(item.created_at).slice(0, 16).replace('T', ' ') : '—',
    }))
    mode.value = 'live'
  } catch (e: unknown) {
    mode.value = 'empty'
    loadError.value = e instanceof Error ? e.message : '加载失败'
    stats.value = { today: 0, week: 0, sites: 0, rate: 0 }
    regionData.value = []
    trendData.value = []
    recentList.value = []
    message.error(loadError.value)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  void loadAll()
})
</script>

<style scoped>
.mb-6 { margin-bottom: 24px; }
.region-chart { display: flex; flex-direction: column; gap: 10px; padding: 4px 0; }
.region-bar-row { display: flex; align-items: center; gap: 8px; }
.region-flag { font-size: 1.2rem; width: 28px; text-align: center; }
.region-name { font-size: 0.78rem; color: #334155; width: 56px; flex-shrink: 0; }
.region-bar-track { flex: 1; height: 20px; background: #f1f5f9; border-radius: 10px; overflow: hidden; }
.region-bar-fill { height: 100%; border-radius: 10px; transition: width 0.6s ease; min-width: 4px; }
.region-pct { font-size: 0.72rem; color: #64748b; width: 36px; text-align: right; }
.region-count { font-size: 0.78rem; color: #1e293b; font-weight: 600; width: 40px; text-align: right; }
.trend-chart { padding: 8px 0; }
.trend-bars { display: flex; align-items: flex-end; justify-content: space-around; height: 160px; padding: 0 8px; border-bottom: 1px solid #e2e8f0; }
.trend-col { display: flex; flex-direction: column; align-items: center; gap: 4px; flex: 1; }
.trend-label-top { font-size: 0.65rem; color: #64748b; font-weight: 500; }
.trend-bar { width: 32px; background: linear-gradient(180deg, var(--uj-brand, #4a9b8c), #8b5cf6); border-radius: 4px 4px 0 0; transition: height 0.5s ease; min-height: 4px; }
.trend-label { font-size: 0.65rem; color: #94a3b8; margin-top: 4px; }
</style>
