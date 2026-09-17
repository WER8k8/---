/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="运行调试" subtitle="多环境运行调试与性能检测" surface="elevated">
  <div class="runtime-overview">
    <a-alert
      v-if="overviewError"
      type="warning"
      show-icon
      class="mb-4"
      :message="overviewError"
    />
    <div class="env-tabs">
      <a-radio-group
        v-model:value="activeEnv"
        button-style="solid"
      >
        <a-radio-button value="development">
          开发环境
        </a-radio-button>
        <a-radio-button value="testing">
          测试环境
        </a-radio-button>
        <a-radio-button value="production">
          生产环境
        </a-radio-button>
      </a-radio-group>
    </div>

    <div class="stats-grid">
      <div
        class="stat-card"
        v-for="stat in runtimeStats"
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
          class="stat-trend"
          :class="stat.trend > 0 ? 'up' : 'down'"
        >
          {{ stat.trend > 0 ? '+' : '' }}{{ stat.trend }}%
        </div>
      </div>
    </div>

    <div class="row">
      <div class="col-3">
        <div class="panel">
          <h3 class="panel-title">
            服务状态
          </h3>
          <div class="services-list">
            <div
              class="service-item"
              v-for="service in services"
              :key="service.name"
            >
              <div class="service-info">
                <div class="service-name">
                  {{ service.name }}
                </div>
                <div class="service-desc">
                  {{ service.desc }}
                </div>
              </div>
              <a-badge
                :status="service.status === 'running' ? 'success' : 'error'"
                :text="service.status === 'running' ? '运行中' : '停止'"
              />
            </div>
          </div>
        </div>
      </div>
      <div class="col-3">
        <div class="panel">
          <h3 class="panel-title">
            内存使用
          </h3>
          <div class="memory-chart">
            <a-progress
              :percent="memoryUsage"
              stroke-color="#10b981"
              show-info
            />
            <div class="memory-info">
              <span>已使用: {{ memoryUsed }} GB</span>
              <span>总计: {{ memoryTotal }} GB</span>
            </div>
          </div>
        </div>
      </div>
      <div class="col-3">
        <div class="panel">
          <h3 class="panel-title">
            CPU使用率
          </h3>
          <div class="cpu-gauge">
            <div
              class="gauge-ring"
              :style="{ '--percent': cpuUsage }"
            >
              <span class="gauge-value">{{ cpuUsage }}%</span>
            </div>
          </div>
          <div class="cpu-cores">
            <div
              class="core-bar"
              v-for="i in 8"
              :key="i"
              :style="{ height: coreBarHeights[i - 1] }"
            />
          </div>
        </div>
      </div>
    </div>

    <div class="action-bar">
      <button
        class="action-btn start"
        @click="startService"
      >
        <PlayCircleOutlined />
        启动服务
      </button>
      <button
        class="action-btn stop"
        @click="stopService"
      >
        <PauseCircleOutlined />
        停止服务
      </button>
      <button
        class="action-btn restart"
        @click="restartService"
      >
        <ReloadOutlined />
        重启服务
      </button>
      <button
        class="action-btn debug"
        @click="startDebug"
      >
        <BugOutlined />
        调试模式
      </button>
    </div>
  </div>
  </YdPage>
</template>

<script setup lang="ts">

import { apiGet } from '@/utils/api'

onMounted(async () => {
  try { await apiGet('/system-health') } catch { /* 空状态 */ }
})
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { message } from 'ant-design-vue';
import { YdPage } from '@/components/youding';
import {
  ThunderboltOutlined,
  CloudServerOutlined,
  LineChartOutlined,
  ClockCircleOutlined,
  ApiOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  ReloadOutlined,
  BugOutlined,
} from '@ant-design/icons-vue';
import { systemHealthAPI } from '@/api';

const router = useRouter();
const actionLoading = ref('');

const overviewError = ref('')
const activeEnv = ref('development');
const memoryUsage = ref(0);
const memoryUsed = ref('0');
const memoryTotal = ref('0');
const cpuUsage = ref(0);
const coreBarHeights = computed(() =>
  Array.from({ length: 8 }, (_, i) => `${40 + (cpuUsage.value / 100) * 50 * (0.85 + (i % 4) * 0.05)}%`)
);

const runtimeStats = ref<any[]>([]);
const services = ref<any[]>([]);

async function loadOverview() {
  overviewError.value = ''
  try {
    const { data } = await systemHealthAPI.overview();
    const payload = data?.data ?? data ?? {};
    if (payload.cpu_usage_percent != null) cpuUsage.value = Math.round(Number(payload.cpu_usage_percent));
    if (payload.memory_usage_percent != null) memoryUsage.value = Math.round(Number(payload.memory_usage_percent));
    if (payload.memory_used_gb != null) memoryUsed.value = String(payload.memory_used_gb);
    if (payload.memory_total_gb != null) memoryTotal.value = String(payload.memory_total_gb);
    const svc = payload.services ?? payload.components;
    if (Array.isArray(svc) && svc.length) {
      services.value = svc.map((s: Record<string, unknown>) => ({
        name: s.name ?? s.service ?? '服务',
        desc: s.desc ?? s.description ?? '',
        status: (s.status === 'running' || s.online) ? 'running' : 'stopped',
      }));
    }
  } catch {
    overviewError.value = '运行数据加载失败，不会展示示意 CPU/内存百分比'
  }
}

async function runHealthAction(kind: 'backup' | 'stress') {
  actionLoading.value = kind;
  try {
    if (kind === 'backup') {
      await systemHealthAPI.triggerBackup();
      message.success('已触发备份任务');
      router.push('/system-health/backup');
    } else {
      router.push('/system-health/stress-test');
    }
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '操作失败');
  } finally {
    actionLoading.value = '';
  }
}

const startService = () => {
  void runHealthAction('stress');
};

const stopService = () => {
  router.push('/system-health/resource-monitor');
};

const restartService = () => {
  void runHealthAction('backup');
};

const startDebug = () => {
  router.push('/system-health/dashboard');
};

onMounted(() => {
  void loadOverview();
});
</script>

<style scoped lang="scss">
.runtime-overview {
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

.env-tabs {
  margin-bottom: 24px;
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

      &.bg-blue {
        background: linear-gradient(135deg, #4a9b8c 0%, #2a6b60 100%);
      }
      &.bg-green {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
      }
      &.bg-red {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
      }
      &.bg-orange {
        background: linear-gradient(135deg, #f97316 0%, #ea580c 100%);
      }
    }

    .stat-content {
      flex: 1;

      .stat-value {
        font-size: 20px;
        font-weight: 600;
        color: #1f2937;
        display: block;
      }

      .stat-label {
        font-size: 12px;
        color: #6b7280;
      }
    }

    .stat-trend {
      font-size: 13px;
      font-weight: 500;

      &.up {
        color: #10b981;
      }

      &.down {
        color: #ef4444;
      }
    }
  }
}

.row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
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

.services-list {
  .service-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 0;
    border-bottom: 1px solid #f3f4f6;

    &:last-child {
      border-bottom: none;
    }

    .service-info {
      .service-name {
        font-size: 14px;
        font-weight: 500;
        color: #1f2937;
        margin-bottom: 2px;
      }

      .service-desc {
        font-size: 12px;
        color: #6b7280;
      }
    }
  }
}

.memory-chart {
  padding: 20px;

  .memory-info {
    display: flex;
    justify-content: space-between;
    margin-top: 12px;
    font-size: 13px;
    color: #6b7280;
  }
}

.cpu-gauge {
  display: flex;
  justify-content: center;
  padding: 20px;

  .gauge-ring {
    width: 100px;
    height: 100px;
    border-radius: 50%;
    background: conic-gradient(#4a9b8c calc(var(--percent) * 1%), #e5e7eb 0);
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;

    &::before {
      content: '';
      position: absolute;
      width: 70px;
      height: 70px;
      border-radius: 50%;
      background: #fff;
    }

    .gauge-value {
      position: relative;
      z-index: 1;
      font-size: 20px;
      font-weight: 600;
      color: #1f2937;
    }
  }
}

.cpu-cores {
  display: flex;
  justify-content: space-around;
  align-items: flex-end;
  height: 60px;
  padding-top: 16px;

  .core-bar {
    width: 12px;
    background: linear-gradient(to top, #4a9b8c 0%, #2a6b60 100%);
    border-radius: 6px;
    min-height: 10px;
    animation: pulse 2s ease-in-out infinite;
  }
}

@keyframes pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.6;
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
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-size: 14px;
    font-weight: 500;
    transition: transform 0.2s;

    &:hover {
      transform: translateY(-2px);
    }

    &.start {
      background: linear-gradient(135deg, #10b981 0%, #059669 100%);
      color: #fff;
    }

    &.stop {
      background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
      color: #fff;
    }

    &.restart {
      background: linear-gradient(135deg, #f97316 0%, #ea580c 100%);
      color: #fff;
    }

    &.debug {
      background: linear-gradient(135deg, #a855f7 0%, #6366f1 100%);
      color: #fff;
    }
  }
}

@media (max-width: 1200px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .row {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }

  .row {
    grid-template-columns: 1fr;
  }

  .action-bar {
    flex-wrap: wrap;
  }
}
</style>
