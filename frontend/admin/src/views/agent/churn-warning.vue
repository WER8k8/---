/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="客户流失预警" subtitle="自动检测有流失风险的客户，及时跟进挽回" surface="elevated">
    <template #actions>
      <a-button @click="loadData">刷新</a-button>
    </template>
  <div class="churn-warning coachpro-tertiary coachpro-tertiary--agent">
    <!-- 统计卡片 -->
    <div class="cw-stats">
      <div class="cw-stat-card total">
        <div class="cw-stat-num">{{ summary.total }}</div>
        <div class="cw-stat-label">风险客户</div>
      </div>
      <div class="cw-stat-card high">
        <div class="cw-stat-num">{{ summary.high }}</div>
        <div class="cw-stat-label">高危</div>
      </div>
      <div class="cw-stat-card medium">
        <div class="cw-stat-num">{{ summary.medium }}</div>
        <div class="cw-stat-label">中危</div>
      </div>
      <div class="cw-stat-card low">
        <div class="cw-stat-num">{{ summary.low }}</div>
        <div class="cw-stat-label">低危</div>
      </div>
    </div>

    <!-- 风险客户列表 -->
    <section class="cw-section">
      <h2 class="cw-section-title">
        <span>风险客户列表</span>
        <button class="cw-refresh-btn" @click="loadData">刷新</button>
      </h2>

      <!-- 高危 -->
      <div v-if="highRisk.length" class="cw-risk-group">
        <div class="cw-risk-label high">高危</div>
        <div v-for="t in highRisk" :key="t.id" class="cw-risk-card high">
          <div class="cw-risk-left">
            <div class="cw-risk-name">{{ t.name }}</div>
            <div class="cw-risk-reason">{{ t.reason }}</div>
          </div>
          <div class="cw-risk-mid">
            <div class="cw-risk-info">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
              {{ t.last_login }}
            </div>
            <div class="cw-risk-info">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
              {{ t.contact }}
            </div>
          </div>
          <div class="cw-risk-right">
            <button
              class="cw-contact-btn"
              :class="{ contacted: t.contacted }"
              :disabled="t.contacted"
              @click="markContacted(t)"
            >
              {{ t.contacted ? '已联系' : '标记已联系' }}
            </button>
          </div>
        </div>
      </div>

      <!-- 中危 -->
      <div v-if="mediumRisk.length" class="cw-risk-group">
        <div class="cw-risk-label medium">中危</div>
        <div v-for="t in mediumRisk" :key="t.id" class="cw-risk-card medium">
          <div class="cw-risk-left">
            <div class="cw-risk-name">{{ t.name }}</div>
            <div class="cw-risk-reason">{{ t.reason }}</div>
          </div>
          <div class="cw-risk-mid">
            <div class="cw-risk-info">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
              {{ t.last_login }}
            </div>
            <div class="cw-risk-info">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
              {{ t.contact }}
            </div>
          </div>
          <div class="cw-risk-right">
            <button
              class="cw-contact-btn"
              :class="{ contacted: t.contacted }"
              :disabled="t.contacted"
              @click="markContacted(t)"
            >
              {{ t.contacted ? '已联系' : '标记已联系' }}
            </button>
          </div>
        </div>
      </div>

      <!-- 低危 -->
      <div v-if="lowRisk.length" class="cw-risk-group">
        <div class="cw-risk-label low">低危</div>
        <div v-for="t in lowRisk" :key="t.id" class="cw-risk-card low">
          <div class="cw-risk-left">
            <div class="cw-risk-name">{{ t.name }}</div>
            <div class="cw-risk-reason">{{ t.reason }}</div>
          </div>
          <div class="cw-risk-mid">
            <div class="cw-risk-info">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
              {{ t.last_login }}
            </div>
            <div class="cw-risk-info">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
              {{ t.contact }}
            </div>
          </div>
          <div class="cw-risk-right">
            <button
              class="cw-contact-btn"
              :class="{ contacted: t.contacted }"
              :disabled="t.contacted"
              @click="markContacted(t)"
            >
              {{ t.contacted ? '已联系' : '标记已联系' }}
            </button>
          </div>
        </div>
      </div>

      <div v-if="!tenants.length" class="cw-empty">暂无风险客户数据</div>
    </section>

    <div class="cw-bottom-row">
      <!-- 挽留建议 -->
      <section class="cw-section cw-tips-section">
        <h2 class="cw-section-title">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
          挽留建议
        </h2>
        <div v-for="tip in tips" :key="tip.tenant" class="cw-tip-item" :class="tip.priority">
          <div class="cw-tip-icon">
            <YdNavIcon
              :name="tip.priority === 'high' ? 'PhoneOutlined' : tip.priority === 'medium' ? 'MailOutlined' : 'FileTextOutlined'"
              size="sm"
            />
          </div>
          <div class="cw-tip-body">
            <span class="cw-tip-tenant">{{ tip.tenant }}</span>
            <span class="cw-tip-action">→ {{ tip.action }}</span>
          </div>
          <span class="cw-tip-priority" :class="tip.priority">{{ tip.priority === 'high' ? '优先' : '建议' }}</span>
        </div>
        <div v-if="!tips.length" class="cw-empty">暂无挽留建议</div>
      </section>

      <!-- 流失趋势 -->
      <section class="cw-section cw-trend-section">
        <h2 class="cw-section-title">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
          流失趋势（近6个月）
        </h2>
        <div class="cw-chart">
          <div v-for="(item, i) in trend" :key="i" class="cw-bar-wrap">
            <div class="cw-bar-label">{{ item.month.slice(5) }}月</div>
            <div class="cw-bar-track">
              <div
                class="cw-bar-fill"
                :style="{ height: barHeight(item.lost) + '%' }"
              ></div>
            </div>
            <div class="cw-bar-value">{{ item.lost }}</div>
          </div>
        </div>
        <div v-if="!trend.length" class="cw-empty">暂无趋势数据</div>
      </section>
    </div>
  </div>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { YdNavIcon, YdPage } from '@/components/youding';
import { readStoredAccessToken } from '@/utils/sessionAuth';

interface Tenant {
  id: number
  name: string
  risk: string
  reason: string
  last_login: string
  contact: string
  contacted: boolean
}

interface Summary {
  total: number
  high: number
  medium: number
  low: number
}

interface Tip {
  tenant: string
  action: string
  priority: string
}

interface TrendItem {
  month: string
  lost: number
}

const tenants = ref<Tenant[]>([])
const tips = ref<Tip[]>([])
const trend = ref<TrendItem[]>([])
const summary = ref<Summary>({ total: 0, high: 0, medium: 0, low: 0 })

const highRisk = computed(() => tenants.value.filter(t => t.risk === 'high'))
const mediumRisk = computed(() => tenants.value.filter(t => t.risk === 'medium'))
const lowRisk = computed(() => tenants.value.filter(t => t.risk === 'low'))

function barHeight(lost: number): number {
  const maxVal = Math.max(...trend.value.map(t => t.lost), 1)
  return (lost / maxVal) * 100
}

async function loadData() {
  try {
    const token = readStoredAccessToken()
    const headers = { Authorization: `Bearer ${token}` }

    const riskRes = await fetch('/api/v1/churn/at-risk', { headers })
    const riskJson = await riskRes.json()
    const riskData = riskJson.data || riskJson
    tenants.value = riskData.tenants || []
    summary.value = riskData.summary || { total: 0, high: 0, medium: 0, low: 0 }

    const tipsRes = await fetch('/api/v1/churn/tips', { headers })
    const tipsJson = await tipsRes.json()
    tips.value = tipsJson.data || tipsJson || []

    const trendRes = await fetch('/api/v1/churn/trend', { headers })
    const trendJson = await trendRes.json()
    trend.value = trendJson.data || trendJson || []
  } catch (e) {
    if (import.meta.env.DEV) console.error('加载流失预警数据失败', e)
  }
}

async function markContacted(t: Tenant) {
  try {
    const token = readStoredAccessToken()
    const res = await fetch(`/api/v1/churn/mark-contacted/${t.id}`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
    })
    const json = await res.json()
    if (json.code === 0 || json.data) {
      t.contacted = true
    }
  } catch (e) {
    if (import.meta.env.DEV) console.error('标记已联系失败', e)
  }
}

onMounted(loadData)
</script>

<style scoped>
.churn-warning {
  max-width: 1100px;
  margin: 0 auto;
}

.cw-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.cw-header-icon {
  font-size: 2rem;
  line-height: 1;
}

.cw-title {
  font-size: 1.4rem;
  font-weight: 700;
  color: #1e293b;
  margin: 0;
}

.cw-subtitle {
  font-size: 0.82rem;
  color: #94a3b8;
  margin: 0.15rem 0 0;
}

/* Stats */
.cw-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.cw-stat-card {
  background: white;
  border-radius: 12px;
  padding: 1.25rem 1rem;
  text-align: center;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
  border: 1px solid #f1f5f9;
  transition: transform 0.15s;
}

.cw-stat-card:hover {
  transform: translateY(-2px);
}

.cw-stat-num {
  font-size: 2rem;
  font-weight: 800;
  line-height: 1.2;
}

.cw-stat-label {
  font-size: 0.78rem;
  color: #64748b;
  margin-top: 0.3rem;
}

.cw-stat-card.total .cw-stat-num { color: var(--uj-brand, #4a9b8c); }
.cw-stat-card.high .cw-stat-num { color: #ef4444; }
.cw-stat-card.medium .cw-stat-num { color: #f59e0b; }
.cw-stat-card.low .cw-stat-num { color: #10b981; }

/* Sections */
.cw-section {
  background: white;
  border-radius: 12px;
  padding: 1.25rem;
  margin-bottom: 1.25rem;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
  border: 1px solid #f1f5f9;
}

.cw-section-title {
  font-size: 0.95rem;
  font-weight: 600;
  color: #1e293b;
  margin: 0 0 1rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  justify-content: space-between;
}

.cw-refresh-btn {
  padding: 0.3rem 0.75rem;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  background: #f8fafc;
  color: #64748b;
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.15s;
}

.cw-refresh-btn:hover {
  border-color: var(--uj-brand, #4a9b8c);
  color: var(--uj-brand, #4a9b8c);
}

/* Risk Group */
.cw-risk-group {
  margin-bottom: 0.75rem;
}

.cw-risk-label {
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 0.3rem 0.6rem;
  border-radius: 6px;
  display: inline-block;
  margin-bottom: 0.5rem;
}

.cw-risk-label.high { background: #fef2f2; color: #ef4444; }
.cw-risk-label.medium { background: #fffbeb; color: #f59e0b; }
.cw-risk-label.low { background: #f0fdf4; color: #10b981; }

/* Risk Card */
.cw-risk-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.85rem 1rem;
  border-radius: 10px;
  margin-bottom: 0.4rem;
  background: #fafbfc;
  transition: background 0.15s;
  gap: 1rem;
}

.cw-risk-card:hover {
  background: #f1f5f9;
}

.cw-risk-card.high { border-left: 3px solid #ef4444; }
.cw-risk-card.medium { border-left: 3px solid #f59e0b; }
.cw-risk-card.low { border-left: 3px solid #10b981; }

.cw-risk-left {
  flex: 1;
  min-width: 0;
}

.cw-risk-name {
  font-size: 0.88rem;
  font-weight: 600;
  color: #1e293b;
}

.cw-risk-reason {
  font-size: 0.75rem;
  color: #94a3b8;
  margin-top: 0.15rem;
}

.cw-risk-mid {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  flex-shrink: 0;
}

.cw-risk-info {
  font-size: 0.72rem;
  color: #64748b;
  display: flex;
  align-items: center;
  gap: 0.3rem;
  white-space: nowrap;
}

.cw-contact-btn {
  padding: 0.4rem 0.9rem;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  background: white;
  color: var(--uj-brand, #4a9b8c);
  font-size: 0.75rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
  white-space: nowrap;
}

.cw-contact-btn:hover:not(:disabled) {
  background: var(--uj-brand, #4a9b8c);
  color: white;
  border-color: var(--uj-brand, #4a9b8c);
}

.cw-contact-btn.contacted {
  color: #10b981;
  border-color: #10b981;
  background: #f0fdf4;
  cursor: default;
}

/* Bottom Row */
.cw-bottom-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.25rem;
}

@media (max-width: 768px) {
  .cw-stats { grid-template-columns: repeat(2, 1fr); }
  .cw-bottom-row { grid-template-columns: 1fr; }
  .cw-risk-mid { display: none; }
}

/* Tips */
.cw-tip-item {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.7rem 0;
  border-bottom: 1px solid #f1f5f9;
}

.cw-tip-item:last-child {
  border-bottom: none;
}

.cw-tip-icon {
  font-size: 1.1rem;
  flex-shrink: 0;
}

.cw-tip-body {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 0.4rem;
  flex-wrap: wrap;
}

.cw-tip-tenant {
  font-weight: 600;
  font-size: 0.82rem;
  color: #1e293b;
}

.cw-tip-action {
  font-size: 0.8rem;
  color: #64748b;
}

.cw-tip-priority {
  font-size: 0.65rem;
  font-weight: 600;
  padding: 0.15rem 0.5rem;
  border-radius: 10px;
  white-space: nowrap;
}

.cw-tip-priority.high { background: #fef2f2; color: #ef4444; }
.cw-tip-priority.medium { background: #fffbeb; color: #f59e0b; }

/* Chart */
.cw-chart {
  display: flex;
  align-items: flex-end;
  justify-content: space-around;
  height: 160px;
  padding: 0.5rem 0;
  gap: 0.5rem;
}

.cw-bar-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.3rem;
  flex: 1;
}

.cw-bar-label {
  font-size: 0.65rem;
  color: #94a3b8;
  order: 2;
}

.cw-bar-track {
  width: 100%;
  max-width: 36px;
  height: 100px;
  background: #f1f5f9;
  border-radius: 6px;
  position: relative;
  overflow: hidden;
  order: 0;
}

.cw-bar-fill {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: linear-gradient(180deg, var(--uj-brand, #4a9b8c), #8b5cf6);
  border-radius: 6px 6px 0 0;
  transition: height 0.5s ease;
  min-height: 4px;
}

.cw-bar-value {
  font-size: 0.75rem;
  font-weight: 700;
  color: #1e293b;
  order: 1;
}

.cw-empty {
  text-align: center;
  color: #94a3b8;
  font-size: 0.8rem;
  padding: 2rem;
}
</style>
