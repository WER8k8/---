<template>
  <YdPage title="系统概览" subtitle="查看系统整体运行状态和关键指标" surface="elevated">
  <div class="system-overview">
      <nav
        class="quick-links"
        aria-label="系统套件快捷入口"
      >
        <button
          v-for="item in quickLinks"
          :key="item.path"
          type="button"
          class="ql"
          @click="openPage(item.path)"
        >
          {{ item.label }}
        </button>
      </nav>

    <a-alert
      v-if="loadError"
      type="warning"
      show-icon
      :message="loadError"
      style="margin-bottom: 16px"
    />

    <a-alert
      v-if="honestyHint"
      type="info"
      show-icon
      :message="honestyHint"
      style="margin-bottom: 16px"
    />

    <template v-if="loading">
      <div class="stats-grid">
        <SkeletonCard v-for="i in 4" :key="i" variant="kpi" />
      </div>
    </template>
    <template v-else>
    <div class="stats-grid">
      <div
        class="stat-card"
        v-for="stat in systemStats"
        :key="stat.title"
      >
        <div
          class="stat-icon"
          :class="stat.iconBg"
        >
          <component :is="stat.icon" />
        </div>
        <div class="stat-content">
          <span class="stat-value">{{ stat.value }}</span>
          <span class="stat-label">{{ stat.title }}</span>
        </div>
        <div
          v-if="stat.trend"
          class="stat-trend"
          :class="stat.trendClass"
        >
          {{ stat.trend }}
        </div>
      </div>
      <a-empty
        v-if="!loading && !systemStats.length"
        description="暂无统计数据"
        class="stats-empty"
      />
    </div>

    <div class="row">
      <div class="col-2">
        <div class="panel">
          <h3 class="panel-title">
            系统状态
          </h3>
          <template v-if="statusLoading">
            <SkeletonCard variant="card" />
          </template>
          <template v-else>
          <div
            v-if="systemStatus.length"
            class="status-list"
          >
            <div
              class="status-item"
              v-for="item in systemStatus"
              :key="item.name"
            >
              <span
                class="status-dot"
                :class="item.statusClass"
              />
              <span class="status-name">{{ item.name }}</span>
              <span class="status-text">{{ item.status }}</span>
            </div>
          </div>
          <a-empty
            v-else
            description="无法获取系统状态"
          />
          </template>
        </div>
      </div>
      <div class="col-2">
        <div class="panel">
          <h3 class="panel-title">
            最近活动
          </h3>
          <div
            v-if="recentActivities.length"
            class="activity-list"
          >
            <div
              class="activity-item"
              v-for="activity in recentActivities"
              :key="activity.id"
            >
              <component
                :is="activity.icon"
                class="activity-icon"
              />
              <div class="activity-content">
                <p class="activity-text">
                  {{ activity.text }}
                </p>
                <span class="activity-time">{{ activity.time }}</span>
              </div>
            </div>
          </div>
          <a-empty
            v-else-if="!loading"
            description="暂无操作记录，可在各模块操作后在此查看"
          />
        </div>
      </div>
    </div>
    </template>
  </div>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, markRaw } from 'vue';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import 'dayjs/locale/zh-cn';
import { apiGet } from '@/utils/api';
import { useWorkTabNavigation } from '@/composables/useWorkTabNavigation';
import { YdPage } from '@/components/youding';
import SkeletonCard from '@/components/common/SkeletonCard.vue';
import {
  TeamOutlined,
  ApiOutlined,
  HddOutlined,
  FileTextOutlined,
  SettingOutlined,
  UserOutlined,
  MonitorOutlined,
  SafetyCertificateOutlined,
  ExportOutlined,
} from '@ant-design/icons-vue';

dayjs.extend(relativeTime);
dayjs.locale('zh-cn');

interface StatCard {
  title: string;
  value: string;
  icon: object;
  iconBg: string;
  trend?: string;
  trendClass?: string;
}

interface StatusRow {
  name: string;
  status: string;
  statusClass: string;
}

interface ActivityRow {
  id: string;
  icon: object;
  text: string;
  time: string;
}

interface DataHonesty {
  excluded_inquiries?: number;
  raw_inquiries?: number;
}

interface DashboardStats {
  total_products?: number;
  total_news?: number;
  total_inquiries?: number;
  total_users?: number;
  today_inquiries?: number;
  data_honesty?: DataHonesty;
}

interface SystemStatusPayload {
  cpu_percent?: number;
  memory_percent?: number;
  disk_percent?: number;
  python_version?: string;
  system?: string;
}

interface AuditLogRow {
  id: string;
  action?: string;
  resource_type?: string;
  detail?: string | null;
  created_at?: string | null;
}

const { go: openPage } = useWorkTabNavigation();

const quickLinks = [
  { label: '用户管理', path: '/admin/system/users' },
  { label: '权限管理', path: '/admin/system/permissions' },
  { label: '代理能力划拨', path: '/admin/system/agent-capabilities' },
  { label: '系统日志', path: '/admin/system/logs' },
  { label: '系统配置', path: '/admin/system/config' },
];

const loading = ref(false);
const statusLoading = ref(false);
const loadError = ref('');
const dataHonesty = ref<DataHonesty | null>(null);
const systemStats = ref<StatCard[]>([]);
const systemStatus = ref<StatusRow[]>([]);
const recentActivities = ref<ActivityRow[]>([]);

const honestyHint = computed(() => {
  const h = dataHonesty.value;
  if (!h?.excluded_inquiries) return '';
  return `本地开发库含 ${h.excluded_inquiries} 条测试询盘，已从「询盘总数」中排除，未上线前对外展示为 0。`;
});

function fmtNum(n: number | undefined): string {
  if (n === undefined || n === null) return '—';
  return n.toLocaleString('zh-CN');
}

function usageStatusClass(pct: number): string {
  if (pct >= 90) return 'status-offline';
  if (pct >= 75) return 'status-warning';
  return 'status-online';
}

function usageLabel(pct: number): string {
  return `${pct.toFixed(1)}%`;
}

const EXPORT_KIND_LABELS: Record<string, string> = {
  inquiries_csv: '询盘列表',
  inquiry_assignment_audit_csv: '询盘分配审计',
  products_csv: '产品列表',
  traffic_analytics_csv: '流量分析',
  finance_ledger_csv: '财务台账',
};

const ACTION_LABELS: Record<string, string> = {
  DATA_EXPORT: '导出数据',
  DATA_EXPORT_DENIED: '导出被拦截',
  FOUNDER_ACCESS: '访问创始人运维入口',
  FOUNDER_DENIED: '创始人运维入口访问被拒',
  AUTH_SENSITIVE: '敏感认证操作',
};

function parseAuditDetail(detail?: string | null): Record<string, unknown> | null {
  const raw = (detail || '').trim();
  if (!raw || raw[0] !== '{') return null;
  try {
    const parsed = JSON.parse(raw) as unknown;
    return parsed && typeof parsed === 'object' ? (parsed as Record<string, unknown>) : null;
  } catch {
    return null;
  }
}

function exportKindLabel(kind: unknown): string {
  if (typeof kind !== 'string' || !kind) return '数据';
  return EXPORT_KIND_LABELS[kind] || kind.replace(/_/g, ' ');
}

function activityIcon(log: AuditLogRow) {
  const action = (log.action || '').toUpperCase();
  const type = (log.resource_type || '').toLowerCase();
  if (action.includes('EXPORT') || action === 'DATA_EXPORT') return markRaw(ExportOutlined);
  if (action.includes('FOUNDER') || action.includes('AUTH') || type === 'security_event') {
    return markRaw(SafetyCertificateOutlined);
  }
  if (type.includes('user')) return markRaw(UserOutlined);
  if (type.includes('config') || type.includes('setting')) return markRaw(SettingOutlined);
  if (type.includes('product') || type.includes('content')) return markRaw(FileTextOutlined);
  if (type.includes('api') || type.includes('system')) return markRaw(ApiOutlined);
  return markRaw(FileTextOutlined);
}

function activityText(log: AuditLogRow): string {
  const action = (log.action || '').toUpperCase();
  const parsed = parseAuditDetail(log.detail);
  const label = ACTION_LABELS[action] || log.action || '系统操作';

  if (parsed && log.resource_type === 'security_event') {
    if (action === 'DATA_EXPORT') {
      const kind = exportKindLabel(parsed.export_kind);
      const rows =
        typeof parsed.row_count === 'number' ? `，共 ${parsed.row_count} 条` : '';
      const scope = typeof parsed.scope === 'string' ? `（${parsed.scope}）` : '';
      return `${label}：${kind}${scope}${rows}`;
    }
    if (action === 'DATA_EXPORT_DENIED') {
      const kind = exportKindLabel(parsed.export_kind);
      const reason = typeof parsed.reason === 'string' ? `：${parsed.reason}` : '';
      return `${label}：${kind}${reason}`;
    }
    if (action === 'FOUNDER_ACCESS' || action === 'FOUNDER_DENIED') {
      const gate = typeof parsed.gate === 'string' ? `（${parsed.gate} 校验）` : '';
      return `${label}${gate}`;
    }
    if (action === 'AUTH_SENSITIVE' && typeof parsed.path === 'string') {
      return `${label}：${parsed.path}`;
    }
    if (typeof parsed.path === 'string') {
      return `${label}：${parsed.path}`;
    }
  }

  const detail = (log.detail || '').trim();
  if (detail && detail.length <= 80 && detail[0] !== '{') {
    return `${label}：${detail}`;
  }
  if (detail && detail[0] === '{') {
    return label;
  }
  const type = log.resource_type || '资源';
  return type === 'security_event' ? label : `${label} · ${type}`;
}

function formatActivityTime(iso?: string | null): string {
  if (!iso) return '—';
  const d = dayjs(iso);
  return d.isValid() ? d.fromNow() : iso;
}

function buildStats(data: DashboardStats): StatCard[] {
  return [
    {
      title: '用户总数',
      value: fmtNum(data.total_users),
      icon: markRaw(TeamOutlined),
      iconBg: 'bg-blue',
      trend: '平台账号',
      trendClass: 'up',
    },
    {
      title: '产品数量',
      value: fmtNum(data.total_products),
      icon: markRaw(HddOutlined),
      iconBg: 'bg-green',
    },
    {
      title: '询盘总数',
      value: fmtNum(data.total_inquiries),
      icon: markRaw(ApiOutlined),
      iconBg: 'bg-yellow',
    },
    {
      title: '今日询盘',
      value: fmtNum(data.today_inquiries),
      icon: markRaw(MonitorOutlined),
      iconBg: 'bg-purple',
      trend: '今日新增',
      trendClass: (data.today_inquiries ?? 0) > 0 ? 'up' : undefined,
    },
  ];
}

function buildStatusRows(
  payload: SystemStatusPayload,
  ready: { database?: string; redis?: string } | null,
): StatusRow[] {
  const rows: StatusRow[] = [];

  if (typeof payload.cpu_percent === 'number') {
    rows.push({
      name: 'CPU 使用率',
      status: usageLabel(payload.cpu_percent),
      statusClass: usageStatusClass(payload.cpu_percent),
    });
  }
  if (typeof payload.memory_percent === 'number') {
    rows.push({
      name: '内存使用率',
      status: usageLabel(payload.memory_percent),
      statusClass: usageStatusClass(payload.memory_percent),
    });
  }
  if (typeof payload.disk_percent === 'number') {
    rows.push({
      name: '磁盘使用率',
      status: usageLabel(payload.disk_percent),
      statusClass: usageStatusClass(payload.disk_percent),
    });
  }

  if (ready) {
    const dbOk = ready.database === 'ok';
    rows.push({
      name: '数据库',
      status: dbOk ? '连接正常' : String(ready.database || '未知'),
      statusClass: dbOk ? 'status-online' : 'status-offline',
    });
    const redisVal = ready.redis;
    const redisOk = redisVal === 'ok' || redisVal === 'disabled';
    rows.push({
      name: 'Redis 缓存',
      status:
        redisVal === 'disabled'
          ? '未启用（开发模式）'
          : redisOk
            ? '连接正常'
            : String(redisVal || '未知'),
      statusClass: redisOk ? 'status-online' : 'status-warning',
    });
  }

  if (payload.system || payload.python_version) {
    rows.push({
      name: '运行环境',
      status: [payload.system, payload.python_version ? `Python ${payload.python_version}` : '']
        .filter(Boolean)
        .join(' · '),
      statusClass: 'status-online',
    });
  }

  return rows;
}

async function fetchReadyChecks(): Promise<{ database?: string; redis?: string } | null> {
  try {
    const res = await fetch('/health/ready');
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      return {
        database: body?.checks?.database ?? 'fail',
        redis: body?.checks?.redis ?? 'fail',
      };
    }
    const body = await res.json();
    return body?.checks ?? null;
  } catch {
    return null;
  }
}

async function loadOverview() {
  loading.value = true;
  statusLoading.value = true;
  loadError.value = '';
  const errors: string[] = [];

  const [statsRes, auditRes] = await Promise.allSettled([
    apiGet<DashboardStats>('/super-admin/dashboard/stats'),
    apiGet<AuditLogRow[]>('/super-admin/audit', { page: 1, page_size: 8 }),
  ]);

  if (statsRes.status === 'fulfilled') {
    dataHonesty.value = statsRes.value.data_honesty ?? null;
    systemStats.value = buildStats(statsRes.value);
  } else {
    dataHonesty.value = null;
    errors.push('统计数据');
    systemStats.value = [];
  }

  if (auditRes.status === 'fulfilled') {
    const logs = Array.isArray(auditRes.value) ? auditRes.value : [];
    recentActivities.value = logs.map((log) => ({
      id: log.id,
      icon: activityIcon(log),
      text: activityText(log),
      time: formatActivityTime(log.created_at),
    }));
  } else {
    errors.push('最近活动');
    recentActivities.value = [];
  }

  loading.value = false;

  const [statusRes, readyChecks] = await Promise.allSettled([
    apiGet<SystemStatusPayload>('/super-admin/dashboard/system-status'),
    fetchReadyChecks(),
  ]);

  if (statusRes.status === 'fulfilled') {
    const ready = readyChecks.status === 'fulfilled' ? readyChecks.value : null;
    systemStatus.value = buildStatusRows(statusRes.value, ready);
  } else {
    errors.push('系统状态');
    systemStatus.value = [];
  }

  statusLoading.value = false;

  if (errors.length) {
    loadError.value = `部分数据加载失败：${errors.join('、')}。请确认已用超管账号登录且后端已启动。`;
  }
}

onMounted(() => {
  void loadOverview();
});
</script>

<style scoped lang="scss">
.system-overview {
  padding: 24px;
}

.page-header {
  margin-bottom: 24px;

  .page-title {
    font-size: 24px;
    font-weight: 600;
    color: #1f2937;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .page-desc {
    font-size: 14px;
    color: #6b7280;
    margin-top: 4px;
  }
}

.quick-links {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 14px;
  margin-bottom: 20px;
}

.ql {
  font-size: 13px;
  font-weight: 500;
  color: #4f46e5;
  text-decoration: none;
  padding: 6px 12px;
  border-radius: 8px;
  background: #eef2ff;
  border: 1px solid #e0e7ff;
  cursor: pointer;
  font-family: inherit;
  transition:
    background 0.15s,
    border-color 0.15s;
}

.ql:hover {
  background: #e0e7ff;
  border-color: #c7d2fe;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;

  .stats-empty {
    grid-column: 1 / -1;
    padding: 24px 0;
  }

  .stat-card {
    background: #fff;
    border-radius: 12px;
    padding: 20px;
    display: flex;
    align-items: center;
    gap: 16px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);

    .stat-icon {
      width: 48px;
      height: 48px;
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 24px;
      color: #fff;

      &.bg-blue {
        background: linear-gradient(135deg, #4a9b8c 0%, #2a6b60 100%);
      }
      &.bg-green {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
      }
      &.bg-yellow {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
      }
      &.bg-purple {
        background: linear-gradient(135deg, #a855f7 0%, #6366f1 100%);
      }
    }

    .stat-content {
      flex: 1;

      .stat-value {
        font-size: 24px;
        font-weight: 600;
        color: #1f2937;
        display: block;
      }

      .stat-label {
        font-size: 13px;
        color: #6b7280;
      }
    }

    .stat-trend {
      font-size: 13px;
      font-weight: 500;
      padding: 4px 8px;
      border-radius: 12px;

      &.up {
        color: #10b981;
        background: #dcfce7;
      }
      &.down {
        color: #ef4444;
        background: #fee2e2;
      }
    }
  }
}

.row {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px;
}

.panel {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  min-height: 200px;

  .panel-title {
    font-size: 16px;
    font-weight: 600;
    color: #1f2937;
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid #f3f4f6;
  }
}

.status-list {
  .status-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 0;
    border-bottom: 1px solid #f3f4f6;

    &:last-child {
      border-bottom: none;
    }

    .status-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;

      &.status-online {
        background: #10b981;
        box-shadow: 0 0 8px rgba(16, 185, 129, 0.5);
      }
      &.status-offline {
        background: #ef4444;
      }
      &.status-warning {
        background: #f59e0b;
      }
    }

    .status-name {
      flex: 1;
      font-size: 14px;
      color: #1f2937;
    }

    .status-text {
      font-size: 13px;
      color: #6b7280;
    }
  }
}

.activity-list {
  .activity-item {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    padding: 12px 0;
    border-bottom: 1px solid #f3f4f6;

    &:last-child {
      border-bottom: none;
    }

    .activity-icon {
      width: 32px;
      height: 32px;
      border-radius: 8px;
      background: #f3f4f6;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 16px;
      color: #6b7280;
      flex-shrink: 0;
    }

    .activity-content {
      flex: 1;

      .activity-text {
        font-size: 14px;
        color: #1f2937;
        margin: 0;
        margin-bottom: 4px;
      }

      .activity-time {
        font-size: 12px;
        color: #9ca3af;
      }
    }
  }
}

@media (max-width: 1024px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .row {
    grid-template-columns: 1fr;
  }
}
</style>
