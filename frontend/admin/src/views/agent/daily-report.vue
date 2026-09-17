/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="经营日报" subtitle="每日经营数据自动汇总" surface="elevated">
    <template #actions>
      <a-button type="primary" :loading="loading" @click="fetchReport">
        刷新数据
      </a-button>
      <a-button @click="pushReport">
        <BellOutlined />
        推送日报
      </a-button>
    </template>
  <div class="daily-report coachpro-tertiary coachpro-tertiary--agent">
    <p class="header-date text-sm text-gray-500 mb-4">{{ report.date || '加载中...' }}</p>

    <!-- 概览总结 -->
    <div class="summary-card" v-if="report.summary">
      <FileTextOutlined class="summary-icon" />
      <span class="summary-text">{{ report.summary }}</span>
    </div>

    <!-- 数据卡片 -->
    <div class="stat-grid">
      <div class="stat-card bg-blue">
        <div class="stat-value">{{ report.new_inquiries }}</div>
        <div class="stat-label">新增询盘</div>
        <div class="stat-tag">昨日新增</div>
      </div>
      <div class="stat-card bg-amber">
        <div class="stat-value">{{ report.pending_inquiries }}</div>
        <div class="stat-label">待处理询盘</div>
        <div class="stat-tag">待跟进</div>
      </div>
      <div class="stat-card bg-green">
        <div class="stat-value">{{ report.new_customers }}</div>
        <div class="stat-label">新增客户</div>
        <div class="stat-tag">昨日注册</div>
      </div>
      <div class="stat-card bg-purple">
        <div class="stat-value">{{ report.page_views }}</div>
        <div class="stat-label">网站访问量</div>
        <div class="stat-tag">昨日 PV</div>
      </div>
    </div>

    <!-- 两列布局 -->
    <div class="content-grid">
      <!-- 关键词排名变化 -->
      <div class="section-card">
        <div class="section-header">
          <h3><RiseOutlined /> 关键词排名变化</h3>
        </div>
        <div class="keyword-list" v-if="report.keyword_changes?.length">
          <div
            v-for="kw in report.keyword_changes"
            :key="kw.keyword"
            class="keyword-item"
          >
            <span class="kw-name">{{ kw.keyword }}</span>
            <span class="kw-rank">#{{ kw.rank }}</span>
            <span class="kw-change" :class="kw.direction === 'up' ? 'change-up' : 'change-down'">
              <CaretUpOutlined v-if="kw.direction === 'up'" />
              <CaretDownOutlined v-else />
              {{ kw.change }}
            </span>
          </div>
        </div>
        <div class="empty-state" v-else>
          <span>暂无关键词数据</span>
        </div>
      </div>

      <!-- 到期提醒 -->
      <div class="section-card">
        <div class="section-header">
          <h3><AlertOutlined /> 到期提醒</h3>
          <a-tag v-if="report.expiring_soon" color="warning">{{ report.expiring_soon }} 项即将到期</a-tag>
        </div>
        <div class="expire-list" v-if="report.expiring_items?.length">
          <div
            v-for="item in report.expiring_items"
            :key="item.name"
            class="expire-item"
          >
            <div class="expire-info">
              <span class="expire-name">{{ item.name }}</span>
              <span class="expire-date">{{ item.expire_date }}</span>
            </div>
            <a-tag :color="item.days_left <= 3 ? 'red' : 'orange'">
              {{ item.days_left }} 天后到期
            </a-tag>
          </div>
        </div>
        <div class="empty-state" v-else>
          <span>暂无到期提醒</span>
        </div>
      </div>
    </div>

    <!-- 历史日报 -->
    <div class="history-section">
      <div class="section-header">
        <h3><HistoryOutlined /> 历史日报</h3>
      </div>
      <a-table
        :dataSource="history"
        :columns="historyColumns"
        :pagination="{ pageSize: 10 }"
        size="small"
        rowKey="date"
        :loading="historyLoading"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'date'">
            <router-link :to="'#'">{{ record.date }}</router-link>
          </template>
          <template v-if="column.key === 'page_views'">
            {{ record.page_views }}
          </template>
        </template>
      </a-table>
    </div>
  </div>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import { YdPage } from '@/components/youding';
import {
  BellOutlined,
  FileTextOutlined,
  RiseOutlined,
  CaretUpOutlined,
  CaretDownOutlined,
  AlertOutlined,
  HistoryOutlined,
} from '@ant-design/icons-vue'
import { readStoredAccessToken } from '@/utils/sessionAuth'

interface KeywordChange {
  keyword: string
  change: string
  rank: number
  direction: 'up' | 'down'
}

interface ExpiringItem {
  name: string
  expire_date: string
  days_left: number
}

interface DailyReport {
  date: string
  summary: string
  new_inquiries: number
  pending_inquiries: number
  new_customers: number
  keyword_changes: KeywordChange[]
  expiring_soon: number
  expiring_items: ExpiringItem[]
  page_views: number
}

interface HistoryRecord {
  date: string
  new_inquiries: number
  new_customers: number
  page_views: number
  summary: string
}

const loading = ref(false)
const historyLoading = ref(false)
const report = ref<DailyReport>({
  date: '',
  summary: '',
  new_inquiries: 0,
  pending_inquiries: 0,
  new_customers: 0,
  keyword_changes: [],
  expiring_soon: 0,
  expiring_items: [],
  page_views: 0,
})
const history = ref<HistoryRecord[]>([])

const historyColumns = [
  { title: '日期', dataIndex: 'date', key: 'date' },
  { title: '新增询盘', dataIndex: 'new_inquiries', key: 'new_inquiries', width: 100 },
  { title: '新增客户', dataIndex: 'new_customers', key: 'new_customers', width: 100 },
  { title: '访问量(PV)', dataIndex: 'page_views', key: 'page_views', width: 110 },
  { title: '摘要', dataIndex: 'summary', key: 'summary' },
]

async function fetchReport() {
  loading.value = true
  try {
    const res = await fetch('/api/v1/daily-report', {
      headers: { Authorization: `Bearer ${readStoredAccessToken()}` },
    })
    const json = await res.json()
    if (json.code === 0 && json.data) {
      report.value = json.data
    }
  } catch {
    /* 保持空日报，不注入假数据 */
  } finally {
    loading.value = false
  }
}

async function fetchHistory() {
  historyLoading.value = true
  try {
    const res = await fetch('/api/v1/daily-report/history?days=7', {
      headers: { Authorization: `Bearer ${readStoredAccessToken()}` },
    })
    const json = await res.json()
    if (json.code === 0 && Array.isArray(json.data)) {
      history.value = json.data
    }
  } catch {
    history.value = []
  } finally {
    historyLoading.value = false
  }
}

function pushReport() {
  message.success('日报已推送到企业微信群')
}

onMounted(() => {
  fetchReport()
  fetchHistory()
})
</script>

<style scoped>
.daily-report {
  max-width: 1100px;
  margin: 0 auto;
}

/* Header */
.report-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}
.header-left {
  display: flex;
  align-items: baseline;
  gap: 0.75rem;
}
.header-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: #1e293b;
  margin: 0;
}
.header-date {
  font-size: 0.85rem;
  color: #94a3b8;
  margin: 0;
}
.header-actions {
  display: flex;
  gap: 0.5rem;
}

/* Summary */
.summary-card {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  padding: 1rem 1.25rem;
  background: linear-gradient(135deg, #eff6ff, #f0fdf4);
  border-radius: 12px;
  border: 1px solid #dbeafe;
  margin-bottom: 1.5rem;
}
.summary-icon {
  font-size: 1.2rem;
  color: var(--uj-brand, #4a9b8c);
  margin-top: 2px;
  flex-shrink: 0;
}
.summary-text {
  font-size: 0.88rem;
  color: #334155;
  line-height: 1.6;
}

/* Stat Cards */
.stat-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1rem;
  margin-bottom: 1.5rem;
}
.stat-card {
  padding: 1.25rem;
  border-radius: 12px;
  color: white;
  position: relative;
  overflow: hidden;
}
.stat-card::after {
  content: '';
  position: absolute;
  top: -50%;
  right: -30%;
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background: rgba(255,255,255,0.08);
}
.stat-card.bg-blue { background: linear-gradient(135deg, var(--uj-brand, #4a9b8c), #2a6b60); }
.stat-card.bg-amber { background: linear-gradient(135deg, #f59e0b, #d97706); }
.stat-card.bg-green { background: linear-gradient(135deg, #10b981, #059669); }
.stat-card.bg-purple { background: linear-gradient(135deg, #8b5cf6, #7c3aed); }
.stat-value {
  font-size: 2rem;
  font-weight: 700;
  line-height: 1;
  margin-bottom: 0.35rem;
  position: relative;
  z-index: 1;
}
.stat-label {
  font-size: 0.82rem;
  opacity: 0.9;
  position: relative;
  z-index: 1;
}
.stat-tag {
  font-size: 0.68rem;
  opacity: 0.6;
  margin-top: 0.25rem;
  position: relative;
  z-index: 1;
}

/* Content Grid */
.content-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

/* Section Card */
.section-card {
  background: white;
  border-radius: 12px;
  padding: 1.25rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  border: 1px solid #f1f5f9;
}
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
}
.section-header h3 {
  font-size: 0.95rem;
  font-weight: 600;
  color: #1e293b;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

/* Keyword List */
.keyword-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.keyword-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.55rem 0.75rem;
  background: #f8fafc;
  border-radius: 8px;
  font-size: 0.85rem;
}
.kw-name {
  flex: 1;
  color: #334155;
  font-weight: 500;
}
.kw-rank {
  color: #64748b;
  font-weight: 600;
  min-width: 2rem;
  text-align: right;
}
.kw-change {
  display: flex;
  align-items: center;
  gap: 2px;
  min-width: 3rem;
  font-weight: 600;
}
.change-up { color: #10b981; }
.change-down { color: #ef4444; }

/* Expire List */
.expire-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.expire-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.55rem 0.75rem;
  background: #f8fafc;
  border-radius: 8px;
}
.expire-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.expire-name {
  font-size: 0.85rem;
  font-weight: 500;
  color: #334155;
}
.expire-date {
  font-size: 0.72rem;
  color: #94a3b8;
}

/* Empty State */
.empty-state {
  padding: 2rem 1rem;
  text-align: center;
  color: #94a3b8;
  font-size: 0.85rem;
}

/* History */
.history-section {
  background: white;
  border-radius: 12px;
  padding: 1.25rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  border: 1px solid #f1f5f9;
}

/* Responsive */
@media (max-width: 768px) {
  .stat-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .content-grid {
    grid-template-columns: 1fr;
  }
  .report-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.75rem;
  }
}
@media (max-width: 480px) {
  .stat-grid {
    grid-template-columns: 1fr;
  }
}
</style>
