/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage class="ai-analytics" title="智能分析" subtitle="SEO 分析 · 转化漏斗 · 用户行为分析" surface="elevated">
    <template #actions>
      <a-button :loading="loading" @click="refresh">
        <ReloadOutlined />
        刷新数据
      </a-button>
    </template>

    <a-tabs v-model:activeKey="activeTab">
      <!-- Tab 1: SEO Analysis -->
      <a-tab-pane key="seo" tab="SEO 分析报告">
        <template v-if="seoLoading">
          <SkeletonCard variant="kpi" />
          <div class="mt-4">
            <SkeletonCard variant="table" :rows="5" />
          </div>
        </template>
        <template v-else>
          <a-row :gutter="[16, 16]">
            <a-col :span="6" v-for="s in seoStats" :key="s.label">
              <a-card size="small" hoverable>
                <a-statistic :title="s.label" :value="s.value" :value-style="{ color: s.color }" />
              </a-card>
            </a-col>
          </a-row>
          <a-card title="SEO 指标详情" class="section-card" style="margin-top:16px">
            <div ref="seoPanelRef" class="yd-panel yd-table-panel">
              <YdTableToolbar :loading="seoLoading" :target-ref="seoPanelRef" :show-export="false" @refresh="loadSeoData" />
              <YdDataTable
                :columns="seoCols"
                :data-source="seoDetails"
                :loading="seoLoading"
                :pagination="false"
                :table-props="{ size: tableSize, rowKey: 'id' }"
              />
            </div>
          </a-card>
        </template>
      </a-tab-pane>

      <!-- Tab 2: Conversion Funnel -->
      <a-tab-pane key="funnel" tab="转化漏斗">
        <div class="flex items-center justify-between mb-4">
          <p class="text-gray-500">访问→浏览→询盘→成交 全链路转化分析</p>
          <a-select v-model:value="period" style="width:120px" @change="buildFunnel">
            <a-select-option value="7d">近7天</a-select-option>
            <a-select-option value="30d">近30天</a-select-option>
          </a-select>
        </div>
        <a-alert
          type="info"
          show-icon
          message="数据说明"
          description="未上线或无访客时，漏斗为空，不会生成虚构日曲线。"
          style="margin-bottom: 12px"
        />
        <a-empty
          v-if="!funnel.length"
          description="暂无访问埋点数据。租户站点上线后才会产生真实漏斗。"
        />
        <template v-else>
        <a-row :gutter="[16, 16]">
          <a-col :span="6" v-for="(l, i) in funnel" :key="l.name">
            <a-card class="text-center funnel-card" :class="'border-t-4 ' + l.border">
              <div class="funnel-icon">{{ l.icon }}</div>
              <a-statistic :title="l.name" :value="l.count" />
              <div class="funnel-loss" v-if="i > 0">流失 {{ l.loss }}%</div>
              <div class="funnel-rate">转化率 {{ l.rate }}%</div>
            </a-card>
          </a-col>
        </a-row>
        <a-card title="漏斗可视化" class="section-card" style="margin-top:16px">
          <div class="funnel-visual">
            <div v-for="(l, i) in funnel" :key="l.name" class="funnel-bar-wrap">
              <div class="flex justify-between text-sm mb-1">
                <span>{{ l.name }}</span>
                <span class="font-medium">{{ l.count }} 人 ({{ l.rate }}%)</span>
              </div>
              <a-progress :percent="l.rate" :stroke-color="funnelColors[i]" size="small" />
            </div>
          </div>
        </a-card>
        <a-card title="流失原因分析" class="section-card" style="margin-top:16px">
          <div ref="lossPanelRef" class="yd-panel yd-table-panel">
            <YdTableToolbar :loading="loading" :target-ref="lossPanelRef" :show-export="false" @refresh="buildFunnel" />
            <YdDataTable
              :columns="lossCols"
              :data-source="lossReasons"
              :pagination="false"
              :table-props="{ size: tableSize, rowKey: 'id' }"
            />
          </div>
        </a-card>
        </template>
      </a-tab-pane>

      <!-- Tab 3: User Behavior -->
      <a-tab-pane key="behavior" tab="用户行为分析">
        <a-row :gutter="[16, 16]">
          <a-col :span="6" v-for="s in behaviorStats" :key="s.label">
            <a-card size="small" hoverable>
              <a-statistic :title="s.label" :value="s.value" :value-style="{ color: s.color }" />
            </a-card>
          </a-col>
        </a-row>
        <a-row :gutter="16" style="margin-top:16px">
          <a-col :span="12">
            <a-card title="页面停留时长分布" size="small">
              <div class="space-y-3">
                <a-progress v-for="d in dwellTime" :key="d.label" :percent="d.value" :stroke-color="d.color" size="small" :format="() => `${d.label}: ${d.value}%`" />
              </div>
            </a-card>
          </a-col>
          <a-col :span="12">
            <a-card title="核心指标" size="small">
              <div class="space-y-4">
                <div v-for="m in behaviorMetrics" :key="m.label">
                  <div class="flex justify-between text-sm mb-1">
                    <span>{{ m.label }}</span>
                    <span class="font-semibold">{{ m.value }}</span>
                  </div>
                  <a-progress :percent="m.percent" :stroke-color="m.color" size="small" :status="m.warn ? 'exception' : undefined" />
                </div>
              </div>
            </a-card>
          </a-col>
        </a-row>
        <a-card title="页面访问排行" class="section-card" style="margin-top:16px">
          <div ref="pagePanelRef" class="yd-panel yd-table-panel">
            <YdTableToolbar :loading="loading" :target-ref="pagePanelRef" :show-export="false" @refresh="refresh" />
            <YdDataTable
              :columns="pageCols"
              :data-source="pageRankings"
              :pagination="false"
              :table-props="{ size: tableSize, rowKey: 'id' }"
            >
              <template #bodyCell="{ column, record }">
                <template v-if="column.key === 'heat'">
                  <div class="heat-bar-bg">
                    <div class="heat-bar-fill" :style="{ width: record.heat + '%' }" />
                  </div>
                </template>
              </template>
            </YdDataTable>
          </div>
        </a-card>
      </a-tab-pane>
    </a-tabs>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { YdDataTable, YdPage, YdTableToolbar } from '@/components/youding'
import SkeletonCard from '@/components/common/SkeletonCard.vue'
import { useUiPreferencesStore } from '@/stores/uiPreferences'
import { ReloadOutlined } from '@ant-design/icons-vue'
import { seoAPI, unwrapApiData } from '@/api'
import { apiGet } from '@/utils/api'

const loading = ref(false)
const seoLoading = ref(false)
const activeTab = ref('seo')
const period = ref('7d')
const seoPanelRef = ref<HTMLElement | null>(null)
const lossPanelRef = ref<HTMLElement | null>(null)
const pagePanelRef = ref<HTMLElement | null>(null)
const ui = useUiPreferencesStore()
const { antTableSize: tableSize } = storeToRefs(ui)

// ====== SEO Analysis ======
const seoStats = ref([
  { label: '产品总数', value: '--', color: '#3b82f6' },
  { label: '询盘总数', value: '--', color: '#8b5cf6' },
  { label: 'AI 优化页', value: '--', color: '#22c55e' },
  { label: '关键词总数', value: '--', color: '#f59e0b' },
])

const seoCols = [
  { title: '指标', dataIndex: 'metric' },
  { title: '当前值', dataIndex: 'current' },
  { title: '上周', dataIndex: 'lastWeek' },
  { title: '环比', dataIndex: 'change', key: 'change' },
]

const seoDetails = ref<Array<{ id: number; metric: string; current: string; lastWeek: string; change: string }>>([])

// ====== Conversion Funnel ======
const funnelColors = ['#3b82f6', '#818cf8', '#a78bfa', '#f472b6']
const funnel = ref<any[]>([])
const lossCols = [
  { title: '流失环节', dataIndex: 'stage' },
  { title: '原因', dataIndex: 'reason' },
  { title: '影响用户数', dataIndex: 'count' },
  { title: '建议', dataIndex: 'suggestion' },
]
const lossReasons = ref<Array<{ id: number; stage: string; reason: string; count: number; suggestion: string }>>([])

async function buildFunnel() {
  try {
    const data = await apiGet<{
      funnel?: Array<{ name: string; count: number; loss?: number; rate?: number; border?: string }>
      is_empty?: boolean
      loss_reasons?: Array<{ id: number; s: string; r: string; n: number; a: string }>
    }>('/ai-learning/conversion-funnel', { period: period.value })

    if (data.is_empty) {
      funnel.value = []
      lossReasons.value = []
      return
    }

    const stages = data.funnel || []
    const icons = ['👁', '📖', '📧', '💰']
    funnel.value = stages.map((stage, i) => ({
      name: stage.name,
      icon: icons[i] || '•',
      count: stage.count,
      loss: stage.loss ?? 0,
      rate: stage.rate ?? 0,
      border: stage.border || 'border-gray-300',
    }))
    lossReasons.value = (data.loss_reasons || []).map((row) => ({
      id: row.id,
      stage: row.s,
      reason: row.r,
      count: row.n,
      suggestion: row.a,
    }))
  } catch {
    funnel.value = []
    lossReasons.value = []
  }
}

// ====== User Behavior ======
const behaviorStats = ref([
  { label: '独立访客', value: '0', color: '#3b82f6' },
  { label: '页面浏览', value: '0', color: '#8b5cf6' },
  { label: '总点击', value: '0', color: '#22c55e' },
  { label: '跳出率', value: '—', color: '#ef4444' },
])

const dwellTime = ref<Array<{ label: string; value: number; color: string }>>([])

const behaviorMetrics = ref<Array<{ label: string; value: string; percent: number; color: string; warn: boolean }>>([])

const pageCols = [
  { title: '页面', dataIndex: 'page' },
  { title: '浏览量', dataIndex: 'views' },
  { title: '平均停留', dataIndex: 'dwell' },
  { title: '热力', dataIndex: 'heat', key: 'heat' },
  { title: '跳出率', dataIndex: 'bounce' },
]

const pageRankings = ref<Array<{ id: number; page: string; views: string; dwell: string; heat: number; bounce: string }>>([])

async function loadBehaviorData() {
  try {
    const data = await apiGet<{
      summary?: Record<string, number>
      bounce_rate?: number
      heatmap_data?: Array<{ path?: string; label?: string; clicks?: number }>
    }>('/ai-learning/behavior', { period: period.value })
    const s = data.summary || {}
    behaviorStats.value = [
      { label: '独立访客', value: String(s.unique_visitors || 0), color: '#3b82f6' },
      { label: '页面浏览', value: String(s.page_views || 0), color: '#8b5cf6' },
      { label: '总点击', value: String(s.total_clicks || 0), color: '#22c55e' },
      { label: '跳出率', value: typeof data.bounce_rate === 'number' ? `${data.bounce_rate}%` : '—', color: '#ef4444' },
    ]
    const conv = Number(s.conversion_rate || 0)
    behaviorMetrics.value = [
      { label: '转化率', value: conv ? `${conv}%` : '—', percent: Math.min(100, conv), color: '#f59e0b', warn: false },
      { label: '询盘数', value: String(s.inquiries || 0), percent: Math.min(100, Number(s.inquiries || 0)), color: '#3b82f6', warn: false },
    ]
    dwellTime.value = []
    const heat = data.heatmap_data || []
    const maxClicks = Math.max(...heat.map((h) => Number(h.clicks || 0)), 1)
    pageRankings.value = heat.map((row, i) => ({
      id: i + 1,
      page: row.path || row.label || '—',
      views: String(row.clicks || 0),
      dwell: '—',
      heat: Math.round((Number(row.clicks || 0) / maxClicks) * 100),
      bounce: '—',
    }))
  } catch {
    behaviorStats.value = behaviorStats.value.map((s) => ({ ...s, value: s.label === '跳出率' ? '—' : '0' }))
    behaviorMetrics.value = []
    pageRankings.value = []
    dwellTime.value = []
  }
}

async function loadSeoData() {
  seoLoading.value = true
  try {
    const res = await seoAPI.dashboard({ range: 'week' })
    const d = unwrapApiData<any>(res) || {}
    seoStats.value = [
      { label: '产品总数', value: d.total_products ?? '—', color: '#3b82f6' },
      { label: '询盘总数', value: d.total_inquiries ?? '—', color: '#8b5cf6' },
      { label: 'AI 优化页', value: d.ai_optimized_pages ?? '—', color: '#22c55e' },
      { label: '关键词总数', value: d.total_keywords ?? '—', color: '#f59e0b' },
    ]
    seoDetails.value = []
  } catch {
    seoStats.value = seoStats.value.map((s) => ({ ...s, value: '—' }))
    seoDetails.value = []
  } finally {
    seoLoading.value = false
  }
}

function refresh() {
  loading.value = true
  Promise.all([loadSeoData(), buildFunnel(), loadBehaviorData()]).finally(() => { loading.value = false })
}

onMounted(() => {
  refresh()
})
</script>

<style scoped lang="scss">
.ai-analytics {
  .section-card {
    border-radius: 12px;
  }

  .funnel-card {
    text-align: center;
    border-radius: 12px;

    .funnel-icon {
      font-size: 32px;
      margin-bottom: 8px;
    }
    .funnel-loss {
      font-size: 12px;
      color: #ef4444;
      margin-top: 4px;
    }
    .funnel-rate {
      font-size: 12px;
      color: #94a3b8;
      margin-top: 2px;
    }
  }

  .funnel-visual {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .heat-bar-bg {
    width: 100%;
    height: 8px;
    background: #f1f5f9;
    border-radius: 4px;
    overflow: hidden;
  }
  .heat-bar-fill {
    height: 100%;
    border-radius: 4px;
    background: linear-gradient(90deg, #22c55e, #f59e0b, #ef4444);
    transition: width 0.3s;
  }
}
</style>
