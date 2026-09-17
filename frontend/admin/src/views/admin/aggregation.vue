/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="数据中心" subtitle="全平台数据汇总 · 按层级下钻" surface="elevated">
    <template #actions>
      <a-select
        v-model:value="selectedPeriod"
        style="width: 140px"
        size="small"
        :options="periodOptions"
        @change="loadAggregation"
      />
      <a-button type="primary" ghost size="small" @click="loadAggregation">
        <ReloadOutlined /> 刷新
      </a-button>
    </template>
  <div class="aggregation-dashboard">
    <a-alert
      v-if="aggError"
      type="warning"
      show-icon
      class="mb-4"
      :message="aggError"
      closable
      @close="aggError = ''"
    />
    <a-alert
      v-if="dataLoaded && dataHonesty && !dataHonesty.has_production_activity"
      type="info"
      show-icon
      class="mb-4"
      message="当前为开发/测试库汇总"
      :description="honestyDescription"
    />
    <a-alert
      v-if="dataLoaded && isEmpty"
      type="info"
      show-icon
      class="mb-4"
      message="暂无业务数据"
      description="系统尚未上线或未产生访问/交易记录。本页仅展示数据库真实汇总，不会编造每日曲线或示例数字。"
    />
    <!-- 按层级汇总卡片 -->
    <section class="section-card level-summary">
      <h2 class="section-title">
        <ApartmentOutlined class="section-icon" /> 按层级汇总
      </h2>
      <div class="level-cards">
        <div
          v-for="level in levelSummary"
          :key="level.id"
          class="level-card"
          :class="'level-' + level.id"
          @click="selectedLevel = level.id"
        >
          <div class="level-badge">{{ level.id.toUpperCase() }}</div>
          <div class="level-info">
            <span class="level-name">{{ level.name }}</span>
            <span class="level-count">{{ level.count }} 个</span>
          </div>
          <div class="level-metrics">
            <div class="lm-item">
              <span class="lm-value">{{ level.clientCount }}</span>
              <span class="lm-label">客户</span>
            </div>
            <div class="lm-item">
              <span class="lm-value">&yen;{{ level.revenue }}</span>
              <span class="lm-label">本月实收</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 平台整体数据 -->
    <section class="section-card platform-overview">
      <h2 class="section-title">
        <DashboardOutlined class="section-icon" /> 平台整体数据
      </h2>
      <div class="platform-grid">
        <div class="platform-stat">
          <span class="ps-value">{{ platformStats.totalVisitors }}</span>
          <span class="ps-label">独立访客(UV)</span>
        </div>
        <div class="platform-stat">
          <span class="ps-value ps-accent-blue">{{ platformStats.monthlyNewTenants }}</span>
          <span class="ps-label">本月新开户</span>
        </div>
        <div class="platform-stat">
          <span class="ps-value ps-accent-green">{{ platformStats.monthlyRevenue === '—' ? '—' : '¥' + platformStats.monthlyRevenue }}</span>
          <span class="ps-label">本月实收</span>
        </div>
        <div class="platform-stat">
          <span class="ps-value">{{ platformStats.activeTenants }}</span>
          <span class="ps-label">活跃租户</span>
        </div>
        <div class="platform-stat">
          <span class="ps-value ps-accent-orange">{{ platformStats.expiringSoon }}</span>
          <span class="ps-label">到期预警</span>
        </div>
        <div class="platform-stat">
          <span class="ps-value ps-accent-purple">{{ platformStats.arr }}</span>
          <span class="ps-label">ARR（未产生实收）</span>
        </div>
      </div>
    </section>

    <!-- 两栏布局：按省份汇总 + 树形数据下钻 -->
    <div class="two-col-layout">
      <!-- 按省份汇总 -->
      <section class="section-card province-section">
        <h2 class="section-title">
          <EnvironmentOutlined class="section-icon" /> 按省份汇总
        </h2>
        <div class="province-list">
          <div
            v-for="prov in provinceStats"
            :key="prov.province"
            class="province-row"
            @click="toggleProvinceExpand(prov.province)"
          >
            <div class="province-header">
              <span class="province-rank">#{{ prov.rank }}</span>
              <span class="province-name">{{ prov.province }}</span>
              <span class="province-bar-wrap">
                <span class="province-bar" :style="{ width: prov.barPercent + '%' }"></span>
              </span>
              <span class="province-clients">{{ prov.clientCount }} {{ prov.metricLabel }}</span>
              <span v-if="prov.revenue !== '—'" class="province-revenue">&yen;{{ prov.revenue }}</span>
              <CaretDownOutlined
                class="province-arrow"
                :class="{ expanded: expandedProvinces.has(prov.province) }"
              />
            </div>
            <transition name="slide">
              <div v-if="expandedProvinces.has(prov.province)" class="province-detail">
                <div class="pd-metrics">
                  <div class="pd-item">
                    <span class="pd-label">负责人</span>
                    <span class="pd-value">{{ prov.manager }}</span>
                  </div>
                  <div class="pd-item">
                    <span class="pd-label">代理商</span>
                    <span class="pd-value">{{ prov.agentCount }} 家</span>
                  </div>
                  <div class="pd-item">
                    <span class="pd-label">本月新增</span>
                    <span class="pd-value">{{ prov.monthlyNew ?? '—' }}</span>
                  </div>
                  <div class="pd-item">
                    <span class="pd-label">续费率</span>
                    <span class="pd-value">{{ prov.renewalRate != null ? prov.renewalRate + '%' : '—' }}</span>
                  </div>
                </div>
              </div>
            </transition>
          </div>
        </div>
      </section>

      <!-- 树形数据下钻 -->
      <section class="section-card tree-section">
        <h2 class="section-title">
          <NodeIndexOutlined class="section-icon" /> 树形数据下钻
        </h2>
        <div class="tree-container">
          <div
            v-for="node in treeData"
            :key="node.name"
            class="tree-node"
          >
            <div
              class="tree-row"
              :class="'level-' + node.level"
              @click="toggleTreeNode(node.name)"
            >
              <span class="tree-toggle">
                <CaretRightOutlined
                  v-if="node.children?.length"
                  class="tree-caret"
                  :class="{ expanded: expandedTreeNodes.has(node.name) }"
                />
              </span>
              <component :is="nodeIcon(node.level)" class="tree-level-icon" />
              <span class="tree-label">{{ node.label }}</span>
              <span class="tree-client-count">{{ node.clientCount }} 客户</span>
              <span class="tree-revenue">&yen;{{ node.revenue }}</span>
            </div>
            <transition name="tree-slide">
              <div v-if="node.children?.length && expandedTreeNodes.has(node.name)" class="tree-children">
                <div
                  v-for="child in node.children"
                  :key="child.name"
                  class="tree-node tree-node-child"
                >
                  <div
                    class="tree-row"
                    :class="'level-' + child.level"
                    @click="toggleTreeNode(child.name)"
                  >
                    <span class="tree-toggle">
                      <CaretRightOutlined
                        v-if="child.children?.length"
                        class="tree-caret"
                        :class="{ expanded: expandedTreeNodes.has(child.name) }"
                      />
                    </span>
                    <component :is="nodeIcon(child.level)" class="tree-level-icon" />
                    <span class="tree-label">{{ child.label }}</span>
                    <span class="tree-client-count">{{ child.clientCount }} 客户</span>
                    <span class="tree-revenue">&yen;{{ child.revenue }}</span>
                  </div>
                  <transition name="tree-slide">
                    <div v-if="child.children?.length && expandedTreeNodes.has(child.name)" class="tree-children">
                      <div
                        v-for="gc in child.children"
                        :key="gc.name"
                        class="tree-node tree-node-grandchild"
                      >
                        <div class="tree-row" :class="'level-' + gc.level">
                          <span class="tree-toggle"></span>
                          <component :is="nodeIcon(gc.level)" class="tree-level-icon" />
                          <span class="tree-label">{{ gc.label }}</span>
                          <span class="tree-client-count">{{ gc.clientCount }} 客户</span>
                          <span class="tree-revenue">&yen;{{ gc.revenue }}</span>
                        </div>
                      </div>
                    </div>
                  </transition>
                </div>
              </div>
            </transition>
          </div>
        </div>
      </section>
    </div>

    <!-- 月度收入趋势：仅有真实记录时才展示 -->
    <section class="section-card trend-section">
      <h2 class="section-title">
        <LineChartOutlined class="section-icon" /> 流量趋势
      </h2>
      <a-empty
        v-if="!hasTrendData"
        description="暂无按日流量记录。租户站点上线并接入埋点后，此处才会出现真实趋势。"
      />
      <div v-else class="trend-chart">
        <div class="trend-bars">
          <div v-for="(m, i) in monthlyTrend" :key="i" class="trend-column">
            <div
              class="trend-bar"
              :style="{ height: trendBarHeight(m.visitors) + '%' }"
              :title="m.monthLabel + ': ' + m.visitors + ' 访客'"
            >
              <span class="trend-bar-value" v-if="m.visitors > 0">{{ m.visitors }}</span>
            </div>
            <span class="trend-label">{{ m.monthLabel }}</span>
          </div>
        </div>
      </div>
    </section>
  </div>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { YdPage } from '@/components/youding'
import {
  BarChartOutlined,
  ReloadOutlined,
  ApartmentOutlined,
  DashboardOutlined,
  EnvironmentOutlined,
  NodeIndexOutlined,
  LineChartOutlined,
  CaretDownOutlined,
  CaretRightOutlined,
  FolderOutlined,
  UserOutlined,
  CrownOutlined,
} from '@ant-design/icons-vue'
import type { Component } from 'vue'
import { apiGet } from '@/utils/api'

// ==================== 状态 ====================
const selectedPeriod = ref<'month' | 'quarter' | 'year'>('month')
const aggError = ref('')
const periodOptions = [
  { value: 'month', label: '本月' },
  { value: 'quarter', label: '本季度' },
  { value: 'year', label: '本年' },
]
const expandedProvinces = ref<Set<string>>(new Set())
const expandedTreeNodes = ref<Set<string>>(new Set())
const selectedLevel = ref<string | null>(null)
const dataLoaded = ref(false)

interface DataHonesty {
  has_production_activity: boolean
  excluded_inquiries: number
  excluded_analytics_events: number
  raw_inquiries: number
  raw_analytics_events: number
  notes?: string[]
}

const dataHonesty = ref<DataHonesty | null>(null)

const honestyDescription = computed(() => {
  const h = dataHonesty.value
  if (!h) return ''
  const parts = [
    `已过滤 ${h.excluded_inquiries} 条测试询盘、${h.excluded_analytics_events} 条探针埋点。`,
    '页面仅展示真实业务汇总，不会编造曲线或示例数字。',
  ]
  if (h.notes?.length) parts.push(h.notes.join('；'))
  return parts.join(' ')
})

interface LevelItem {
  id: string
  name: string
  count: number
  clientCount: number
  revenue: string
}

const levelSummary = ref<LevelItem[]>([])

interface PlatformStats {
  totalVisitors: number
  monthlyNewTenants: number
  monthlyRevenue: string
  activeTenants: number
  expiringSoon: number | string
  arr: string
}

const platformStats = ref<PlatformStats>({
  totalVisitors: 0,
  monthlyNewTenants: 0,
  monthlyRevenue: '—',
  activeTenants: 0,
  expiringSoon: 0,
  arr: '—',
})

interface ProvinceItem {
  rank: number
  province: string
  clientCount: number
  revenue: string
  barPercent: number
  manager: string
  agentCount: number
  monthlyNew: number | null
  renewalRate: number | null
  metricLabel: string
}

const provinceStats = ref<ProvinceItem[]>([])

interface TreeChild {
  name: string
  label: string
  level: string
  clientCount: number
  revenue: string
  children?: TreeChild[]
}

interface TreeNode extends TreeChild {}

const treeData = ref<TreeNode[]>([])

interface TrendMonth {
  month: string
  monthLabel: string
  visitors: number
  inquiries?: number
  revenue_cents?: number
}

const monthlyTrend = ref<TrendMonth[]>([])

const isEmpty = computed(() =>
  !levelSummary.value.length
  && !provinceStats.value.length
  && !treeData.value.length
  && platformStats.value.totalVisitors === 0
  && platformStats.value.activeTenants === 0,
)

const hasTrendData = computed(() =>
  monthlyTrend.value.some((m) => Number(m.visitors) > 0),
)

const maxTrendVisitors = computed(() => Math.max(...monthlyTrend.value.map(m => m.visitors), 1))

function trendBarHeight(value: number): number {
  return Math.max(5, (value / maxTrendVisitors.value) * 100)
}

// ==================== 工具函数 ====================

function nodeIcon(level: string): Component {
  switch (level) {
    case 'l2': return FolderOutlined
    case 'l3': return FolderOutlined
    case 'l4': return UserOutlined
    case 'l5': return UserOutlined
    default: return FolderOutlined
  }
}

function toggleProvinceExpand(province: string) {
  if (expandedProvinces.value.has(province)) {
    expandedProvinces.value.delete(province)
  } else {
    expandedProvinces.value.add(province)
  }
}

function toggleTreeNode(name: string) {
  if (expandedTreeNodes.value.has(name)) {
    expandedTreeNodes.value.delete(name)
  } else {
    expandedTreeNodes.value.add(name)
  }
}

async function loadAggregation() {
  aggError.value = ''
  dataLoaded.value = false
  dataHonesty.value = null
  levelSummary.value = []
  provinceStats.value = []
  treeData.value = []
  monthlyTrend.value = []
  platformStats.value = {
    totalVisitors: 0,
    monthlyNewTenants: 0,
    monthlyRevenue: '—',
    activeTenants: 0,
    expiringSoon: 0,
    arr: '—',
  }
  try {
    const data = await apiGet<{
      level_summary?: LevelItem[]
      platform_stats?: PlatformStats
      province_stats?: Array<Record<string, unknown>>
      tree_data?: TreeNode[]
      monthly_trend?: TrendMonth[]
      data_honesty?: DataHonesty
    }>('/super-admin/aggregation', { period: selectedPeriod.value })

    levelSummary.value = (data.level_summary ?? []).map((x) => ({
      ...x,
      revenue: String(x.revenue ?? '0'),
    }))
    if (data.platform_stats) {
      const ps = data.platform_stats as unknown as Record<string, string | number>
      platformStats.value = {
        totalVisitors: Number(ps.totalVisitors ?? ps.totalClients ?? 0),
        monthlyNewTenants: Number(ps.monthlyNewTenants ?? ps.monthlyNew ?? 0),
        monthlyRevenue: String(ps.monthlyRevenue ?? '—'),
        activeTenants: Number(ps.activeTenants ?? 0),
        expiringSoon: Number(ps.expiringSoon ?? 0),
        arr: String(ps.arr ?? '—'),
      }
    }
    const provinceRows = data.province_stats ?? []
    const maxC = Math.max(...provinceRows.map((r) => Number(r.clientCount ?? r.inquiryCount ?? 0)), 1)
    provinceStats.value = provinceRows.map((row, i) => ({
      rank: i + 1,
      province: String(row.province ?? row.node_name ?? '—'),
      clientCount: Number(row.clientCount ?? row.inquiryCount ?? 0),
      revenue: String(row.revenue ?? '—'),
      barPercent: Math.round((Number(row.clientCount ?? 0) / maxC) * 100),
      manager: String(row.manager ?? '—'),
      agentCount: Number(row.agentCount ?? 0),
      monthlyNew: row.monthlyNew != null ? Number(row.monthlyNew) : null,
      renewalRate: row.renewalRate != null ? Number(row.renewalRate) : null,
      metricLabel: String(row.metric_label ?? '独立访客'),
    }))
    monthlyTrend.value = (data.monthly_trend ?? []).map((m) => ({
      month: m.month,
      monthLabel: m.monthLabel ?? m.month,
      visitors: Number((m as TrendMonth & { visitors?: number }).visitors ?? 0),
      inquiries: Number((m as { inquiries?: number }).inquiries ?? 0),
      revenue_cents: Number((m as { revenue_cents?: number }).revenue_cents ?? 0),
    }))
    treeData.value = Array.isArray(data.tree_data) ? data.tree_data : []
    dataHonesty.value = data.data_honesty ?? null
  } catch (e: unknown) {
    levelSummary.value = []
    provinceStats.value = []
    treeData.value = []
    monthlyTrend.value = []
    dataHonesty.value = null
    platformStats.value = {
      totalVisitors: 0,
      monthlyNewTenants: 0,
      monthlyRevenue: '—',
      activeTenants: 0,
      expiringSoon: 0,
      arr: '—',
    }
    aggError.value = e instanceof Error ? e.message : '汇总数据加载失败'
  } finally {
    dataLoaded.value = true
  }
}

onMounted(() => {
  void loadAggregation()
})
</script>

<style scoped>
.aggregation-dashboard {
  animation: pageIn 0.35s cubic-bezier(0.4, 0, 0.2, 1);
}
@keyframes pageIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

/* ===== 页面头部 ===== */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1.5rem;
}
.header-left {
  flex: 1;
}
.page-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: #0f172a;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.title-icon {
  color: #0891b2;
}
.page-subtitle {
  margin: 0.35rem 0 0;
  font-size: 0.85rem;
  color: #64748b;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-shrink: 0;
}

/* ===== 通用 Section ===== */
.section-card {
  background: #fff;
  border-radius: 16px;
  padding: 1.25rem 1.5rem;
  margin-bottom: 1.25rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04), 0 4px 12px rgba(0, 0, 0, 0.04);
}
.section-title {
  font-size: 1rem;
  font-weight: 600;
  color: #0f172a;
  margin: 0 0 1rem;
  display: flex;
  align-items: center;
  gap: 0.45rem;
}
.section-icon {
  color: #0891b2;
  font-size: 1.1rem;
}

/* ===== 层级汇总 ===== */
.level-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 0.75rem;
}
.level-card {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  border-radius: 12px;
  background: linear-gradient(135deg, rgba(8, 145, 178, 0.06), rgba(6, 182, 212, 0.04));
  border: 1px solid rgba(8, 145, 178, 0.12);
  cursor: pointer;
  transition: all 0.2s ease;
}
.level-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(8, 145, 178, 0.12);
  border-color: rgba(8, 145, 178, 0.3);
}
.level-card.level-l1 { background: linear-gradient(135deg, rgba(8, 145, 178, 0.1), rgba(6, 182, 212, 0.06)); }
.level-card.level-l2 { background: linear-gradient(135deg, rgba(99, 102, 241, 0.08), rgba(129, 140, 248, 0.05)); }
.level-card.level-l3 { background: linear-gradient(135deg, rgba(16, 185, 129, 0.08), rgba(52, 211, 153, 0.05)); }
.level-card.level-l4 { background: linear-gradient(135deg, rgba(245, 158, 11, 0.08), rgba(251, 191, 36, 0.05)); }
.level-card.level-l5 { background: linear-gradient(135deg, rgba(139, 92, 246, 0.08), rgba(167, 139, 250, 0.05)); }

.level-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 22px;
  border-radius: 6px;
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  color: #fff;
  background: #0891b2;
}
.level-l1 .level-badge { background: #0891b2; }
.level-l2 .level-badge { background: #6366f1; }
.level-l3 .level-badge { background: #10b981; }
.level-l4 .level-badge { background: #f59e0b; }
.level-l5 .level-badge { background: #8b5cf6; }

.level-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.level-name {
  font-size: 0.85rem;
  font-weight: 600;
  color: #1e293b;
}
.level-count {
  font-size: 0.7rem;
  color: #64748b;
  background: rgba(148, 163, 184, 0.15);
  padding: 0.1rem 0.45rem;
  border-radius: 8px;
}
.level-metrics {
  display: flex;
  gap: 0.75rem;
  padding-top: 0.35rem;
  border-top: 1px solid rgba(148, 163, 184, 0.15);
}
.lm-item {
  display: flex;
  flex-direction: column;
  gap: 0.05rem;
}
.lm-value {
  font-size: 0.85rem;
  font-weight: 700;
  color: #0f172a;
}
.lm-label {
  font-size: 0.6rem;
  color: #94a3b8;
}

/* ===== 平台整体数据 ===== */
.platform-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 0.75rem;
}
.platform-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
  padding: 0.85rem 0.5rem;
  border-radius: 12px;
  background: #f8fafc;
  border: 1px solid #f1f5f9;
}
.ps-value {
  font-size: 1.35rem;
  font-weight: 700;
  color: #0f172a;
}
.ps-accent-blue { color: var(--uj-brand, #4a9b8c); }
.ps-accent-green { color: #10b981; }
.ps-accent-orange { color: #f59e0b; }
.ps-accent-purple { color: #8b5cf6; }
.ps-label {
  font-size: 0.7rem;
  color: #94a3b8;
  font-weight: 500;
}

/* ===== 两栏布局 ===== */
.two-col-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.25rem;
  margin-bottom: 1.25rem;
}
@media (max-width: 900px) {
  .two-col-layout {
    grid-template-columns: 1fr;
  }
}

/* ===== 省份汇总 ===== */
.province-list {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}
.province-row {
  border-radius: 10px;
  overflow: hidden;
  transition: all 0.15s ease;
}
.province-row:hover {
  background: #f1f5f9;
}
.province-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.6rem;
  cursor: pointer;
}
.province-rank {
  font-size: 0.7rem;
  font-weight: 700;
  color: #94a3b8;
  min-width: 24px;
}
.province-name {
  font-size: 0.82rem;
  font-weight: 600;
  color: #1e293b;
  min-width: 40px;
}
.province-bar-wrap {
  flex: 1;
  height: 6px;
  background: #f1f5f9;
  border-radius: 3px;
  overflow: hidden;
}
.province-bar {
  display: block;
  height: 100%;
  border-radius: 3px;
  background: linear-gradient(90deg, #06b6d4, #0891b2);
  transition: width 0.4s ease;
}
.province-clients {
  font-size: 0.75rem;
  color: #64748b;
  min-width: 60px;
  text-align: right;
}
.province-revenue {
  font-size: 0.78rem;
  font-weight: 600;
  color: #0f172a;
  min-width: 80px;
  text-align: right;
}
.province-arrow {
  font-size: 0.7rem;
  color: #94a3b8;
  transition: transform 0.2s ease;
}
.province-arrow.expanded {
  transform: rotate(180deg);
  color: #0891b2;
}
.province-detail {
  padding: 0.5rem 0.6rem 0.5rem 2.5rem;
  background: #f8fafc;
  border-top: 1px solid #f1f5f9;
}
.pd-metrics {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.5rem;
}
.pd-item {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
}
.pd-label {
  font-size: 0.6rem;
  color: #94a3b8;
}
.pd-value {
  font-size: 0.8rem;
  font-weight: 600;
  color: #1e293b;
}

/* ===== 树形数据下钻 ===== */
.tree-container {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}
.tree-node {
  display: flex;
  flex-direction: column;
}
.tree-row {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.5rem 0.5rem;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.15s ease;
}
.tree-row:hover {
  background: #f1f5f9;
}
.tree-row.level-l2 { padding: 0.55rem 0.5rem; }
.tree-row.level-l3 { padding-left: 2rem; font-size: 0.88rem; }
.tree-row.level-l4 { padding-left: 4rem; font-size: 0.82rem; }

.tree-toggle {
  width: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.tree-caret {
  font-size: 0.7rem;
  color: #94a3b8;
  transition: transform 0.2s ease;
}
.tree-caret.expanded {
  transform: rotate(90deg);
  color: #0891b2;
}
.tree-level-icon {
  font-size: 0.95rem;
  color: #64748b;
  flex-shrink: 0;
}
.level-l2 .tree-level-icon { color: #0891b2; }
.level-l3 .tree-level-icon { color: #6366f1; }
.level-l4 .tree-level-icon { color: #10b981; }

.tree-label {
  flex: 1;
  font-size: 0.82rem;
  font-weight: 500;
  color: #334155;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.tree-client-count {
  font-size: 0.7rem;
  color: #64748b;
  min-width: 56px;
  text-align: right;
}
.tree-revenue {
  font-size: 0.75rem;
  font-weight: 600;
  color: #0f172a;
  min-width: 70px;
  text-align: right;
}
.tree-children {
  border-left: 2px solid #e2e8f0;
  margin-left: 7px;
}

/* Transition */
.slide-enter-active, .slide-leave-active,
.tree-slide-enter-active, .tree-slide-leave-active {
  transition: all 0.2s ease;
  overflow: hidden;
}
.slide-enter-from, .slide-leave-to,
.tree-slide-enter-from, .tree-slide-leave-to {
  max-height: 0;
  opacity: 0;
}
.slide-enter-to, .slide-leave-from,
.tree-slide-enter-to, .tree-slide-leave-from {
  max-height: 300px;
  opacity: 1;
}

/* ===== 月度收入趋势 ===== */
.trend-chart {
  padding: 0.5rem 0;
}
.trend-bars {
  display: flex;
  align-items: flex-end;
  justify-content: space-around;
  height: 200px;
  gap: 0.5rem;
}
.trend-column {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  flex: 1;
}
.trend-bar {
  width: 100%;
  max-width: 56px;
  border-radius: 6px 6px 0 0;
  background: linear-gradient(180deg, #06b6d4, #0891b2);
  transition: height 0.5s cubic-bezier(0.4, 0, 0.2, 1);
  min-height: 5px;
  position: relative;
  display: flex;
  align-items: flex-start;
  justify-content: center;
}
.trend-bar-value {
  font-size: 0.6rem;
  font-weight: 600;
  color: #fff;
  margin-top: 0.25rem;
  white-space: nowrap;
}
.trend-label {
  font-size: 0.7rem;
  color: #94a3b8;
  font-weight: 500;
}
</style>
