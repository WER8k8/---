<template>
  <YdPage surface="brand-hero">
    <template #hero>
      <div class="dashboard-hero">
        <div>
          <h2 class="dashboard-hero__title">{{ greeting }}，{{ auth.username }}</h2>
          <p class="dashboard-hero__sub">出海营销运营 cockpit · 平台数据一览</p>
        </div>
        <a-space>
          <a-button @click="loadData">刷新</a-button>
          <a-button type="primary" @click="router.push('/inquiries')">处理询盘</a-button>
        </a-space>
      </div>
    </template>

    <YdStatsRow :cols="5" class="dashboard-kpi-row">
      <YdStatsCard label="总租户数" :value="stats.totalTenants" tone="default" />
      <YdStatsCard label="活跃租户" :value="stats.activeTenants" tone="green" />
      <YdStatsCard label="今日新注册" :value="stats.todayNew" tone="amber" />
      <YdStatsCard label="月收入 MRR" :value="stats.mrr" hint="元" tone="default" />
      <button type="button" class="kpi-link" @click="router.push('/inquiries')">
        <YdStatsCard
          label="待处理询盘"
          :value="pendingInquiryCount"
          tone="green"
          hint="点击进入询盘管理 →"
        />
      </button>
    </YdStatsRow>

    <div class="dashboard-grid">
      <div class="yd-panel">
        <div class="panel-head">
          <span class="panel-title">最近注册租户</span>
          <a-button type="link" size="small" @click="router.push('/admin/tenants')">查看全部</a-button>
        </div>
        <YdDataTable
          :columns="tenantCols"
          :data-source="recentTenants"
          :loading="loading"
          :pagination="false"
          :table-props="{ rowKey: 'id' }"
        >
          <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <a-tag :color="record.status === 'active' ? 'green' : 'red'">
              {{ record.status === 'active' ? '活跃' : '暂停' }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'name'">
            {{ record.name || '--' }}
          </template>
          <template v-else-if="column.key === 'plan'">
            {{ record.plan && record.plan !== '--' ? record.plan : '--' }}
          </template>
          <template v-else-if="column.key === 'created_at'">
              {{ record.created_at ? formatTime(record.created_at) : '--' }}
            </template>
          </template>
        </YdDataTable>
      </div>

      <div class="yd-panel">
        <div class="panel-head">
          <span class="panel-title">系统通知</span>
        </div>
        <div v-if="alerts.length" class="alert-list">
          <div v-for="a in alerts" :key="a.id" class="alert-item" :class="'alert-' + a.level">
            <span class="alert-dot" :class="'dot-' + a.level" />
            <div>
              <div class="alert-title">{{ a.title }}</div>
              <div class="alert-time">{{ a.created_at ? formatTime(a.created_at) : '' }}</div>
            </div>
          </div>
        </div>
        <div v-else class="empty-hint">暂无系统通知</div>
      </div>
    </div>

    <button type="button" class="yd-panel mt-4 pending-card" @click="router.push('/inquiries')">
      <div class="panel-head">
        <span class="panel-title">待跟进询盘</span>
        <a-space @click.stop>
          <a-button size="small" @click="loadPendingCount">刷新</a-button>
          <a-button type="primary" size="small" @click="router.push('/inquiries')">进入询盘管理</a-button>
        </a-space>
      </div>
      <div class="pending-row">
        <span class="pending-count">{{ pendingInquiryCount }}</span>
        <span class="pending-label">待处理询盘（平台汇总）· 点击卡片进入</span>
      </div>
    </button>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';

import { YdDataTable, YdPage, YdStatsCard, YdStatsRow } from '@/components/youding';
import { getAuthToken } from '@/utils/api';
import { useAuthStore } from '@/stores/auth';

const router = useRouter();
const auth = useAuthStore();
const loading = ref(false);

const greeting = computed(() => {
  const h = new Date().getHours();
  if (h < 12) return '上午好';
  if (h < 18) return '下午好';
  return '晚上好';
});

const stats = reactive({
  totalTenants: 0,
  activeTenants: 0,
  todayNew: 0,
  mrr: '0',
});

const tenantCols = [
  { title: '租户名称', dataIndex: 'name', key: 'name', ellipsis: true },
  { title: '套餐', dataIndex: 'plan', key: 'plan', width: 100 },
  { title: '状态', key: 'status', width: 80 },
  { title: '注册时间', dataIndex: 'created_at', key: 'created_at', width: 120 },
];

const recentTenants = ref<any[]>([]);
const alerts = ref<any[]>([]);
const pendingInquiryCount = ref(0);

function formatTime(dateStr: string) {
  try {
    return new Date(dateStr).toLocaleDateString('zh-CN', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return dateStr;
  }
}

async function loadData() {
  loading.value = true;
  const token = getAuthToken();
  const headers = { Authorization: `Bearer ${token}` };

  try {
    const r = await fetch('/api/v1/tenants/', { headers });
    const d = await r.json();
    const items = (d.data?.items || d.items || d.data || []) as any[];
    const now = new Date();
    const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate());

    stats.totalTenants = items.length;
    stats.activeTenants = items.filter((t: any) => (t.status || t.s) === 'active').length;
    stats.todayNew = items.filter((t: any) => {
      const c = t.created_at || t.createdAt;
      return c && new Date(c) >= todayStart;
    }).length;
    const totalMrr = items.reduce(
      (s: number, t: any) => s + (parseInt(String(t.mrr || t.p_mrr || 0).replace(/[^0-9]/g, '')) || 0),
      0,
    );
    stats.mrr = totalMrr.toLocaleString();

    recentTenants.value = [...items]
      .sort((a: any, b: any) => {
        const da = a.created_at || a.createdAt || '';
        const db = b.created_at || b.createdAt || '';
        return da > db ? -1 : da < db ? 1 : 0;
      })
      .slice(0, 5)
      .map((t: any) => ({
        id: t.id,
        name: t.name || t.n,
        plan: t.plan || t.p || '--',
        status: t.status || t.s || 'active',
        created_at: t.created_at || t.createdAt,
      }));
  } catch {
    /* 静默 */
  }

  try {
    const r = await fetch('/api/v1/super-admin/alerts/summary', { headers });
    const d = await r.json();
    alerts.value = ((d.data || d).recent || []).slice(0, 5);
  } catch {
    /* 静默 */
  }

  loading.value = false;
}

async function loadPendingCount() {
  const token = getAuthToken();
  if (!token) return;
  try {
    const r = await fetch('/api/v1/inquiries/unified?page=1&page_size=1&status=pending', {
      headers: { Authorization: `Bearer ${token}` },
    });
    const d = await r.json();
    const data = d.data ?? d;
    pendingInquiryCount.value = Number(data.total ?? data.count ?? 0);
  } catch {
    pendingInquiryCount.value = 0;
  }
}

onMounted(() => {
  void loadData();
  void loadPendingCount();
});
</script>

<style scoped>
.dashboard-hero {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}
.dashboard-hero__title {
  margin: 0;
  font-family: var(--uj-font-display);
  font-size: 24px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  color: var(--uj-text-secondary, #0f172a);
}
.dashboard-hero__sub {
  margin: 6px 0 0;
  font-size: 13px;
  color: var(--uj-text-muted);
}
.dashboard-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
@media (max-width: 1024px) {
  .dashboard-grid {
    grid-template-columns: 1fr;
  }
}
.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.panel-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--uj-text-secondary, #0f172a);
}
.dashboard-kpi-row {
  margin-bottom: 16px;
}
.alert-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.alert-item {
  display: flex;
  gap: 10px;
  padding: 10px;
  border-radius: 8px;
}
.alert-critical { background: rgb(239 68 68 / 0.08); }
.alert-warning { background: rgb(245 158 11 / 0.08); }
.alert-info { background: rgb(88 196 174 / 0.1); }
.alert-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-top: 6px;
  flex-shrink: 0;
}
.dot-critical { background: #ef4444; }
.dot-warning { background: #f59e0b; }
.dot-info { background: var(--uj-brand, #4a9b8c); }
.alert-title { font-size: 13px; font-weight: 500; }
.alert-time { font-size: 11px; color: var(--uj-text-muted); margin-top: 2px; }
.empty-hint { text-align: center; color: var(--uj-text-muted); padding: 24px; font-size: 13px; }
.kpi-link {
  display: block;
  padding: 0;
  border: none;
  background: transparent;
  text-align: inherit;
  cursor: pointer;
  border-radius: var(--uj-radius-lg, 12px);
  transition: box-shadow 0.15s ease, transform 0.15s ease;
}
.kpi-link:hover {
  box-shadow: 0 4px 16px color-mix(in srgb, var(--uj-brand) 18%, transparent);
  transform: translateY(-1px);
}
.kpi-link:focus-visible {
  outline: 2px solid var(--uj-brand);
  outline-offset: 2px;
}
.pending-card {
  display: block;
  width: 100%;
  text-align: left;
  cursor: pointer;
  border: 1px solid var(--uj-border, #e2e8f0);
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}
.pending-card:hover {
  border-color: color-mix(in srgb, var(--uj-brand) 35%, transparent);
  box-shadow: 0 4px 20px color-mix(in srgb, var(--uj-brand) 10%, transparent);
}
.pending-card:focus-visible {
  outline: 2px solid var(--uj-brand);
  outline-offset: 2px;
}
.pending-row { display: flex; align-items: baseline; gap: 12px; }
.pending-count {
  font-family: var(--uj-font-display);
  font-size: 32px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  color: var(--uj-brand);
}
.pending-label { font-size: 13px; color: var(--uj-text-muted); }
.mt-4 { margin-top: 16px; }
</style>
