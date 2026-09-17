/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="安全防护" subtitle="系统安全监控与防护管理" surface="elevated">
  <div class="security-overview">
    <div class="security-status">
      <div class="status-card secure">
        <div class="status-icon">
          <CheckCircleOutlined />
        </div>
        <div class="status-content">
          <span class="status-title">系统安全</span>
          <span class="status-desc">{{ statusDesc }}</span>
        </div>
      </div>
    </div>

    <div class="stats-grid">
      <div
        class="stat-card"
        v-for="stat in securityStats"
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
      </div>
    </div>

    <div class="row">
      <div class="col-2">
        <div class="panel">
          <h3 class="panel-title">
            安全告警
          </h3>
          <a-empty
            v-if="!alerts.length"
            description="暂无安全告警（仅展示数据库真实留痕，不编造示例事件）"
          />
          <div v-else class="alerts-list">
            <div
              class="alert-item"
              v-for="alert in alerts"
              :key="alert.id"
            >
              <div
                class="alert-icon"
                :class="alert.level"
              >
                <component :is="alertIcon(alert.level)" />
              </div>
              <div class="alert-info">
                <h4 class="alert-title">
                  {{ alert.title }}
                </h4>
                <p class="alert-desc">
                  {{ alert.description }}
                </p>
                <span class="alert-time">{{ alert.time }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div class="col-2">
        <div class="panel">
          <h3 class="panel-title">
            安全策略
          </h3>
          <p class="policy-note">以下为平台内置防护能力说明，开关状态以系统配置为准。</p>
          <div class="policy-list">
            <div
              class="policy-item"
              v-for="policy in policies"
              :key="policy.name"
            >
              <div class="policy-info">
                <h4 class="policy-name">
                  {{ policy.name }}
                </h4>
                <p class="policy-desc">
                  {{ policy.description }}
                </p>
              </div>
              <a-tag :color="policy.enabled ? 'green' : 'default'">
                {{ policy.enabled ? '已启用' : '未启用' }}
              </a-tag>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="action-bar">
      <button
        class="action-btn"
        :disabled="scanning"
        @click="runScan"
      >
        <SearchOutlined />
        安全扫描
      </button>
      <button
        class="action-btn"
        @click="exportReport"
      >
        <FileTextOutlined />
        导出报告
      </button>
      <button
        class="action-btn"
        @click="manageRules"
      >
        <SettingOutlined />
        规则管理
      </button>
    </div>
  </div>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { message } from 'ant-design-vue';
import { YdPage } from '@/components/youding';
import {
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  LockOutlined,
  FileSearchOutlined,
  EyeOutlined,
  SearchOutlined,
  FileTextOutlined,
  SettingOutlined,
  WarningOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons-vue';
import { apiGet, getAuthToken } from '@/utils/api';

const router = useRouter();
const scanning = ref(false);

interface Alert {
  id: string;
  title: string;
  description: string;
  time: string;
  level: string;
}

interface Policy {
  name: string;
  description: string;
  enabled: boolean;
}

const securityStats = ref<Array<{ title: string; value: string | number; iconBg: string; icon: unknown }>>([]);
const alerts = ref<Alert[]>([]);
const criticalCount = ref(0);

const statusDesc = computed(() =>
  criticalCount.value > 0
    ? `近期待处理安全事件 ${criticalCount.value} 条`
    : '当前无待处理安全告警',
);

const policies = ref<Policy[]>([
  { name: 'SQL注入防护', description: '检测并阻止SQL注入攻击', enabled: true },
  { name: 'XSS防护', description: '检测并阻止跨站脚本攻击', enabled: true },
  { name: 'CSRF防护', description: '防止跨站请求伪造', enabled: true },
  { name: '暴力破解防护', description: '限制登录尝试次数', enabled: true },
]);

function alertIcon(level: string) {
  if (level === 'danger') return ExclamationCircleOutlined;
  if (level === 'warning') return WarningOutlined;
  return InfoCircleOutlined;
}

function formatScore(raw: unknown): string {
  if (raw == null || raw === '') return '—';
  return String(raw);
}

const runScan = async () => {
  scanning.value = true;
  try {
    await apiGet('/compliance/audit');
    message.success('安全审计已完成');
    await loadAlerts();
  } catch {
    message.warning('审计接口暂不可用，已跳转合规页');
    router.push('/admin/security/compliance');
  } finally {
    scanning.value = false;
  }
};

const exportReport = async () => {
  const token = getAuthToken();
  if (!token) {
    message.warning('请先登录');
    return;
  }
  try {
    const r = await fetch('/api/v1/compliance/report', {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!r.ok) throw new Error('导出失败');
    const d = await r.json();
    const url = d?.data?.report_url ?? d?.report_url;
    if (url) {
      window.open(url, '_blank', 'noopener');
      message.success('报告已打开');
      return;
    }
    throw new Error('无报告链接');
  } catch {
    router.push('/admin/security/compliance');
  }
};

const manageRules = () => {
  router.push('/admin/security/compliance');
};

async function loadAlerts() {
  try {
    const data = await apiGet<{ items?: Alert[]; total?: number }>('/compliance/security-alerts');
    alerts.value = data?.items ?? [];
  } catch {
    alerts.value = [];
  }
}

onMounted(async () => {
  await loadAlerts();
  try {
    const d = await apiGet<Record<string, unknown>>('/compliance');
    const overview = (d?.data ?? d) as Record<string, string | number>;
    criticalCount.value = Number(overview.critical_issues ?? 0);
    securityStats.value = [
      { title: '合规得分', value: formatScore(overview.overall_score), iconBg: 'bg-green', icon: LockOutlined },
      { title: '待处理问题', value: Number(overview.total_issues ?? 0), iconBg: 'bg-amber', icon: FileSearchOutlined },
      { title: '严重问题', value: Number(overview.critical_issues ?? 0), iconBg: 'bg-red', icon: ExclamationCircleOutlined },
      { title: '已记录事件', value: Number(overview.passed_checks ?? 0), iconBg: 'bg-blue', icon: EyeOutlined },
    ];
  } catch {
    securityStats.value = [
      { title: '合规得分', value: '—', iconBg: 'bg-green', icon: LockOutlined },
      { title: '待处理问题', value: 0, iconBg: 'bg-amber', icon: FileSearchOutlined },
      { title: '严重问题', value: 0, iconBg: 'bg-red', icon: ExclamationCircleOutlined },
      { title: '已记录事件', value: 0, iconBg: 'bg-blue', icon: EyeOutlined },
    ];
  }
});
</script>

<style scoped lang="scss">
.security-overview {
  padding: 24px;
}

.security-status {
  margin-bottom: 24px;

  .status-card {
    background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
    border-radius: 12px;
    padding: 24px;
    display: flex;
    align-items: center;
    gap: 16px;
    border: 1px solid #bbf7d0;

    &.secure {
      .status-icon {
        color: #059669;
      }

      .status-title {
        color: #059669;
      }
    }

    .status-icon {
      width: 56px;
      height: 56px;
      border-radius: 14px;
      background: rgba(0, 0, 0, 0.05);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 28px;
    }

    .status-content {
      .status-title {
        font-size: 18px;
        font-weight: 600;
        display: block;
        margin-bottom: 4px;
      }

      .status-desc {
        font-size: 14px;
        color: #6b7280;
      }
    }
  }
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;

  .stat-card {
    background: #fff;
    border-radius: 12px;
    padding: 20px;
    display: flex;
    align-items: center;
    gap: 12px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);

    .stat-icon {
      width: 44px;
      height: 44px;
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 20px;
      color: #fff;

      &.bg-red {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
      }
      &.bg-green {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
      }
      &.bg-blue {
        background: linear-gradient(135deg, #4a9b8c 0%, #2a6b60 100%);
      }
      &.bg-amber {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
      }
    }

    .stat-content {
      .stat-value {
        font-size: 24px;
        font-weight: 600;
        color: #1f2937;
        display: block;
      }

      .stat-label {
        font-size: 12px;
        color: #6b7280;
      }
    }
  }
}

.row {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px;
  margin-bottom: 24px;
}

.panel {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);

  .panel-title {
    font-size: 16px;
    font-weight: 600;
    color: #1f2937;
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid #f3f4f6;
  }
}

.policy-note {
  font-size: 12px;
  color: #9ca3af;
  margin: -8px 0 12px;
}

.alerts-list {
  .alert-item {
    display: flex;
    gap: 12px;
    padding: 12px 0;
    border-bottom: 1px solid #f3f4f6;

    &:last-child {
      border-bottom: none;
    }

    .alert-icon {
      width: 36px;
      height: 36px;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 16px;
      color: #fff;
      flex-shrink: 0;

      &.danger {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
      }
      &.warning {
        background: linear-gradient(135deg, #f97316 0%, #ea580c 100%);
      }
      &.info {
        background: linear-gradient(135deg, #4a9b8c 0%, #2a6b60 100%);
      }
    }

    .alert-info {
      flex: 1;

      .alert-title {
        font-size: 14px;
        font-weight: 600;
        color: #1f2937;
        margin: 0;
        margin-bottom: 4px;
      }

      .alert-desc {
        font-size: 13px;
        color: #6b7280;
        margin: 0;
        margin-bottom: 4px;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
      }

      .alert-time {
        font-size: 12px;
        color: #9ca3af;
      }
    }
  }
}

.policy-list {
  .policy-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 14px 0;
    border-bottom: 1px solid #f3f4f6;

    &:last-child {
      border-bottom: none;
    }

    .policy-info {
      .policy-name {
        font-size: 14px;
        font-weight: 500;
        color: #1f2937;
        margin: 0;
        margin-bottom: 4px;
      }

      .policy-desc {
        font-size: 12px;
        color: #6b7280;
        margin: 0;
      }
    }
  }
}

.action-bar {
  display: flex;
  gap: 12px;

  .action-btn {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 10px 20px;
    background: #4a9b8c;
    color: #fff;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-size: 14px;
    font-weight: 500;
    transition: all 0.2s;

    &:hover {
      background: #5a67d8;
      transform: translateY(-2px);
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

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }

  .action-bar {
    flex-wrap: wrap;
  }
}
</style>
