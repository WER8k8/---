/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage surface="elevated">
    <div class="agent-dashboard coachpro-tertiary coachpro-tertiary--agent">
      <section class="topbar panel uj-glass-panel">
        <div>
          <p class="kicker">{{ greeting }}，{{ auth.username || '市级代理' }}</p>
          <h1>市代执行看板</h1>
          <p class="desc">辖区客户跟进、回款推进与续费执行总览</p>
        </div>
        <div class="topbar-actions">
          <a-tag color="blue">市代视图</a-tag>
          <a-button size="small" @click="router.push('/agent/account-opening')">客户开户</a-button>
          <a-button size="small" type="primary" @click="router.push('/agent/daily-report')">经营日报</a-button>
        </div>
      </section>

      <section class="kpi-grid">
        <YdStatsCard label="客户总数" :value="stats.totalClients" hint="累计开发" tone="blue" compact />
        <YdStatsCard label="本月新增" :value="stats.monthlyNewClients" :hint="`较上月 ${stats.monthlyNewTrend > 0 ? '+' : ''}${stats.monthlyNewTrend}%`" tone="green" compact />
        <YdStatsCard label="本月收款" :value="`¥${stats.monthlyRevenue}`" :hint="`收款 ${stats.monthlyRevenueCount} 笔`" tone="amber" compact />
        <YdStatsCard label="待结算佣金" :value="`¥${stats.pendingCommission}`" :hint="`预计 ${stats.estimatedSettleDate} 结算`" tone="purple" compact />
      </section>

      <section class="main-grid">
        <article class="panel uj-glass-panel trend-card">
          <header class="card-head">
            <h3>近 6 个月趋势</h3>
            <span>{{ trendEmpty ? '暂无数据' : '来自 /agent/trends' }}</span>
          </header>
          <div v-if="trendEmpty" class="trend-empty">暂无近 6 个月趋势数据</div>
          <div v-else class="line-trend">
            <span
              v-for="(item, idx) in monthlyTrend"
              :key="`c-${item.month}-${idx}`"
              class="line-dot line-dot--blue"
              :style="{ left: `${8 + idx * 18}%`, bottom: `${calcBarHeight(item.clients, maxClients)}%` }"
            />
            <span
              v-for="(item, idx) in monthlyTrend"
              :key="`r-${item.month}-${idx}`"
              class="line-dot line-dot--amber"
              :style="{ left: `${8 + idx * 18}%`, bottom: `${calcBarHeight(item.revenue, maxRevenue)}%` }"
            />
          </div>
          <div class="axis-row">
            <span v-for="item in monthlyTrend" :key="item.month">{{ item.month }}</span>
          </div>
        </article>

        <article class="panel uj-glass-panel summary-card">
          <header class="card-head">
            <h3>客户经理汇总</h3>
            <span>{{ subordinateSummary.length }} 个节点</span>
          </header>
          <ul class="summary-list">
            <li v-for="sub in subordinateSummary.slice(0, 6)" :key="sub.name + sub.level">
              <div>
                <p>{{ sub.name }}</p>
                <small>{{ sub.levelLabel }} · 客户 {{ sub.clientCount }}</small>
              </div>
              <strong>¥{{ sub.revenue }}</strong>
            </li>
          </ul>
        </article>
      </section>

      <section class="table-grid">
        <article class="panel uj-glass-panel table-card">
          <header class="card-head">
            <h3>客户列表</h3>
            <a-input-search
              v-model:value="clientSearch"
              placeholder="搜索客户"
              size="small"
              style="width: 200px"
              @search="handleClientSearch"
            />
          </header>
          <div class="toolbar">
            <a-select v-model:value="clientStatusFilter" allow-clear size="small" style="width: 140px" @change="handleClientFilter">
              <a-select-option value="试用中">试用中</a-select-option>
              <a-select-option value="已付费">已付费</a-select-option>
              <a-select-option value="已到期">已到期</a-select-option>
            </a-select>
          </div>
          <a-table
            :data-source="filteredClients"
            :columns="clientColumns"
            :pagination="{ pageSize: 6, size: 'small' }"
            size="small"
            row-key="id"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'status'">
                <a-tag :color="statusColor(record.status)">{{ record.status }}</a-tag>
              </template>
            </template>
          </a-table>
        </article>

        <article class="panel uj-glass-panel side-card">
          <header class="card-head">
            <h3>今日提醒</h3>
            <span>实时</span>
          </header>
          <ul class="alert-list">
            <li v-for="item in roleAlerts" :key="item.title">
              <span class="dot" :class="`dot-${item.level}`" />
              <div>
                <p>{{ item.title }}</p>
                <small>{{ item.desc }}</small>
              </div>
            </li>
          </ul>
          <a-button block @click="router.push('/agent/churn-warning')">查看流失预警</a-button>
        </article>
      </section>
    </div>
  </YdPage>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { YdPage, YdStatsCard } from '@/components/youding';
import { apiGet } from '@/utils/api';
import { useAuthStore } from '@/stores/auth';

interface DashboardStats {
  total_clients?: number;
  monthly_new_clients?: number;
  monthly_revenue?: number;
  monthly_revenue_count?: number;
  pending_commission?: number;
  estimated_settle_date?: string;
  monthly_new_trend?: number;
}

interface SubordinateItem {
  node_id?: string;
  name: string;
  level: string;
  level_label?: string;
  client_count?: number;
  revenue?: string;
  monthly_new?: number;
}

interface TrendItem {
  month: string;
  clients: number;
  revenue: number;
}

interface ClientRow {
  id: string;
  name: string;
  package: string;
  open_date: string;
  first_payment: string;
  status: string;
}

function formatMoney(n: number | undefined): string {
  if (n == null || Number.isNaN(n)) return '0.00';
  return n.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

const router = useRouter();
const auth = useAuthStore();

const greeting = computed(() => {
  const h = new Date().getHours();
  if (h < 12) return '上午好';
  if (h < 18) return '下午好';
  return '晚上好';
});

const stats = ref({
  totalClients: 0,
  monthlyNewClients: 0,
  monthlyNewTrend: 0,
  monthlyRevenue: '0.00',
  monthlyRevenueCount: 0,
  pendingCommission: '0.00',
  estimatedSettleDate: '—',
});

const subordinateSummary = ref<Array<SubordinateItem & { path: string; levelLabel: string; clientCount: number; revenue: string; monthlyNew: number }>>([]);
const monthlyTrend = ref<TrendItem[]>([]);
const trendEmpty = ref(true);

const roleAlerts = ref<{ level: string; title: string; desc: string }[]>([
  { level: 'ok', title: '加载代理业绩中…', desc: '提醒来自真实 API' },
]);

async function loadDashboard() {
  const data = await apiGet<{ stats?: DashboardStats; subordinates?: SubordinateItem[] }>('/agent/dashboard');
  const s = data?.stats;
  if (s) {
    stats.value = {
      totalClients: s.total_clients ?? 0,
      monthlyNewClients: s.monthly_new_clients ?? 0,
      monthlyNewTrend: s.monthly_new_trend ?? 0,
      monthlyRevenue: formatMoney(s.monthly_revenue),
      monthlyRevenueCount: s.monthly_revenue_count ?? 0,
      pendingCommission: formatMoney(s.pending_commission),
      estimatedSettleDate: s.estimated_settle_date ?? '—',
    };
  }
  const subs = data?.subordinates ?? [];
  subordinateSummary.value = subs.map((sub) => ({
    ...sub,
    levelLabel: sub.level_label || sub.level,
    clientCount: sub.client_count ?? 0,
    revenue: sub.revenue ?? '0',
    monthlyNew: sub.monthly_new ?? 0,
    path: `/agent/performance?node=${sub.node_id || ''}`,
  }));
  const alerts: { level: string; title: string; desc: string }[] = [];
  if ((s?.monthly_new_trend ?? 0) < 0) {
    alerts.push({ level: 'warn', title: '本月新增客户环比下降', desc: '建议加强辖区拓客' });
  }
  if ((s?.pending_commission ?? 0) > 0) {
    alerts.push({
      level: 'risk',
      title: `待结算佣金 ¥${formatMoney(s?.pending_commission)}`,
      desc: `预计 ${s?.estimated_settle_date ?? '—'} 结算`,
    });
  }
  roleAlerts.value = alerts.length
    ? alerts
    : [{ level: 'ok', title: '暂无高优先告警', desc: '数据来自 /agent/dashboard' }];
}

async function loadTrends() {
  try {
    const data = await apiGet<{ items?: TrendItem[] }>('/agent/trends', { months: 6 });
    monthlyTrend.value = data?.items ?? [];
    trendEmpty.value = monthlyTrend.value.length === 0;
  } catch {
    monthlyTrend.value = [];
    trendEmpty.value = true;
  }
}

const maxClients = computed(() => Math.max(...monthlyTrend.value.map((i) => i.clients), 1));
const maxRevenue = computed(() => Math.max(...monthlyTrend.value.map((i) => i.revenue), 1));
function calcBarHeight(value: number, max: number): number {
  return 8 + Math.round((value / max) * 72);
}

const clientSearch = ref('');
const clientStatusFilter = ref<string | undefined>(undefined);
const clientColumns = [
  { title: '客户名称', dataIndex: 'name', key: 'name' },
  { title: '套餐', dataIndex: 'package', key: 'package' },
  { title: '开通时间', dataIndex: 'openDate', key: 'openDate' },
  { title: '首付金额', dataIndex: 'firstPayment', key: 'firstPayment' },
  { title: '状态', dataIndex: 'status', key: 'status' },
];
const clients = ref<Array<ClientRow & { openDate: string; firstPayment: string }>>([]);

async function loadClients() {
  const data = await apiGet<{ items?: ClientRow[] }>('/agent/clients', {
    search: clientSearch.value || undefined,
    status: clientStatusFilter.value,
    page: 1,
    page_size: 60,
  });
  clients.value = (data?.items ?? []).map((c) => ({
    ...c,
    openDate: c.open_date,
    firstPayment: c.first_payment,
  }));
}

const filteredClients = computed(() => clients.value);
function handleClientSearch() {
  loadClients();
}
function handleClientFilter() {
  loadClients();
}

function statusColor(status: string): string {
  const map: Record<string, string> = { 试用中: 'blue', 已付费: 'green', 已到期: 'red', 已冻结: 'orange' };
  return map[status] || 'default';
}

onMounted(async () => {
  try {
    await Promise.all([loadDashboard(), loadTrends(), loadClients()]);
  } catch {
    /* 保留静态看板 */
  }
});
</script>

<style scoped lang="scss">
/* 布局与玻璃面板见 coachpro-tertiary-pages.scss */
.agent-dashboard {
  padding: 4px 2px;
}

.kicker {
  margin: 0;
  color: #6b7280;
  font-size: 12px;
}

h1 {
  margin: 2px 0 0;
  font-size: 22px;
  font-weight: 700;
  color: #111827;
}

.desc {
  margin: 4px 0 0;
  font-size: 12px;
  color: #9ca3af;
}

.topbar-actions {
  display: flex;
  align-items: start;
  gap: 8px;
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}
.main-grid {
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 12px;
}

.trend-card,
.summary-card,
.table-card,
.side-card {
  padding: 12px 14px;
}

.card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.card-head h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 700;
  color: #1f2937;
}

.card-head span {
  font-size: 12px;
  color: #9ca3af;
}

.line-trend {
  height: 140px;
  position: relative;
  border: 1px dashed #dbe7ff;
  border-radius: 10px;
  background: linear-gradient(180deg, rgb(74 155 140 / 0.1), rgb(255 255 255 / 0.35));
}

.trend-empty {
  height: 140px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #9ca3af;
  font-size: 13px;
  border: 1px dashed #e5e7eb;
  border-radius: 10px;
}

.line-dot {
  position: absolute;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  transform: translate(-50%, 50%);
}

.line-dot--blue {
  background: var(--uj-brand, #4a9b8c);
}
.line-dot--amber {
  background: #f59e0b;
}

.axis-row {
  margin-top: 6px;
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  font-size: 11px;
  color: #9ca3af;
  text-align: center;
}

.summary-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.summary-list li {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border: 1px solid #eef2f7;
  border-radius: 10px;
  padding: 8px 10px;
}

.summary-list p {
  margin: 0;
  font-size: 13px;
  color: #1f2937;
  font-weight: 600;
}

.summary-list small {
  color: #6b7280;
  font-size: 11px;
}

.summary-list strong {
  color: #0f172a;
  font-size: 13px;
}

.table-grid {
  display: grid;
  grid-template-columns: 1.35fr 0.85fr;
  gap: 12px;
}

.toolbar {
  margin-bottom: 8px;
}

.alert-list {
  list-style: none;
  margin: 0 0 12px;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.alert-list li {
  display: grid;
  grid-template-columns: 8px 1fr;
  gap: 8px;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-top: 5px;
}

.dot-ok {
  background: #10b981;
}
.dot-warn {
  background: #f59e0b;
}
.dot-risk {
  background: #ef4444;
}

.alert-list p {
  margin: 0;
  color: #1f2937;
  font-size: 12px;
  font-weight: 600;
}

.alert-list small {
  color: #6b7280;
  font-size: 11px;
  line-height: 1.4;
}

@media (max-width: 1200px) {
  .kpi-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .main-grid,
  .table-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 900px) {
  .topbar {
    flex-direction: column;
  }
}
</style>
