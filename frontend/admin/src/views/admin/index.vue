/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage surface="elevated">
    <div class="admin-dashboard platform-theme coachpro-dashboard">
      <section class="topbar panel uj-glass-panel">
        <div class="topbar__title">
          <p class="kicker">{{ greeting }}，{{ displayName }}</p>
          <h1>{{ workbenchTitle }}</h1>
          <p class="desc">全站模块快照、待办与异常入口</p>
        </div>
        <div class="topbar__tools">
          <a-input-search
            v-model:value="searchKeyword"
            size="small"
            placeholder="搜索模块、路由、关键词"
            @search="onSearch"
          />
          <a-select
            v-model:value="sessionLevelModel"
            size="small"
            class="level-select"
            :options="levelSelectOptions"
          />
          <a-button size="small" @click="router.push('/admin/system/agent-capabilities')">能力划拨</a-button>
        </div>
      </section>

      <section class="kpi-grid">
        <template v-if="dashboardLoading">
          <SkeletonCard v-for="i in 4" :key="`kpi-skel-${i}`" variant="kpi" />
        </template>
        <template v-else>
          <YdStatsCard label="功能域" :value="kpi.functionalDomains" hint="已加载业务域" tone="blue" compact to="/admin/capability-hub" />
          <YdStatsCard label="入口总数" :value="kpi.totalEntries" hint="可访问入口" tone="green" compact to="/admin/capability-hub" />
          <YdStatsCard label="高优先待办" :value="kpi.urgentTodo" hint="需今日处理" tone="amber" compact to="/inquiries" />
          <YdStatsCard label="系统健康" :value="kpi.health" hint="最近 24 小时" tone="blue" compact to="/admin/system/logs" />
        </template>
      </section>

      <section class="chart-grid">
        <template v-if="dashboardLoading">
          <SkeletonCard variant="chart" />
          <SkeletonCard variant="chart" />
        </template>
        <template v-else>
          <article class="panel uj-glass-panel chart-card">
            <header class="card-head">
              <h3>模块活跃趋势</h3>
              <!-- 游标联动读数：静止显示 7 日均值，游标停某天则切当天值；数字由码表补间 -->
              <span
                v-if="!trendEmpty"
                class="cursor-readout"
                :class="{ 'is-live': cursorActive }"
                :title="readoutTitle"
              >
                <em class="cursor-src">{{ readoutLabel }}</em>
                <b class="cursor-num">{{ readoutText }}<i>%</i></b>
              </span>
              <span v-else>暂无近 7 日流量</span>
            </header>
            <div v-if="trendEmpty" class="trend-empty">
              暂无近 7 日流量数据，请先在站点产生访问
            </div>
            <v-chart
              v-else
              ref="trendChartRef"
              class="echart-trend"
              :option="trendChartOption"
              autoresize
            />
          </article>

          <article class="panel uj-glass-panel chart-card">
            <header class="card-head">
              <h3>业务域占比</h3>
              <span>按工作台入口数汇总</span>
            </header>
            <v-chart
              class="echart-bar"
              :option="barChartOption"
              autoresize
            />
          </article>
        </template>
      </section>

      <section class="bottom-grid">
        <article class="panel uj-glass-panel todo-card">
          <header class="card-head">
            <h3>今日待办</h3>
            <a-button size="small" type="link" @click="router.push('/admin/demo-rehearsal')">90 秒彩排</a-button>
          </header>
          <ul>
            <li v-for="todo in dashboardTodos" :key="todo.title">
              <span class="todo-level" :class="`level-${todo.level}`">{{ todo.levelText }}</span>
              <div class="todo-body">
                <p>{{ todo.title }}</p>
                <button type="button" @click="navigateTo(todo.path)">进入</button>
              </div>
            </li>
          </ul>
        </article>

        <article class="panel uj-glass-panel quick-card">
          <header class="card-head">
            <h3>高频入口</h3>
            <a-button size="small" type="link" @click="router.push('/admin/capability-hub')">全部能力</a-button>
          </header>
          <div class="quick-grid">
            <button
              v-for="entry in quickEntries"
              :key="entry.path"
              type="button"
              class="quick-item"
              @click="navigateTo(entry.path)"
            >
              <YdReliefIcon :icon="entry.icon" size="sm" />
              <span>{{ entry.label }}</span>
            </button>
          </div>
        </article>
      </section>

      <section class="ops-grid">
        <template v-if="dashboardLoading">
          <SkeletonCard variant="table" :rows="4" />
          <SkeletonCard variant="text" />
        </template>
        <template v-else>
          <article class="panel uj-glass-panel table-card">
            <header class="card-head">
              <h3>模块运行概览</h3>
              <a-button size="small" type="link" @click="router.push('/admin/system/logs')">查看日志</a-button>
            </header>
            <div class="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>模块</th>
                    <th>状态</th>
                    <th>今日请求</th>
                    <th>错误率</th>
                    <th>动作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="row in runtimeRows" :key="row.module">
                    <td>{{ row.module }}</td>
                    <td>
                      <span class="status-pill" :class="`status-${row.status}`">{{ row.statusText }}</span>
                    </td>
                    <td>{{ row.requests }}</td>
                    <td>{{ row.errorRate }}</td>
                    <td>
                      <button type="button" class="row-action" @click="navigateTo(row.path)">进入</button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </article>

          <article class="panel uj-glass-panel side-card">
            <header class="card-head">
              <h3>重点提醒</h3>
              <span>今日</span>
            </header>
            <ul class="alert-list">
              <li v-for="item in focusAlerts" :key="item.title" :class="{ 'alert-clickable': item.path }" @click="item.path && router.push(item.path)">
                <span class="dot" :class="`dot-${item.level}`" />
                <div class="alert-body">
                  <p>{{ item.title }}</p>
                  <small>{{ item.desc }}</small>
                </div>
                <span v-if="item.path" class="alert-arrow">›</span>
              </li>
            </ul>
            <a-button block type="primary" class="risk-cta" @click="router.push('/admin/platform-zones')">
              去处理风险项
            </a-button>
          </article>
        </template>
      </section>
    </div>
  </YdPage>
</template>

<script setup lang="ts">

import { apiGet } from '@/utils/api'

onMounted(async () => {
  try { await apiGet('/dashboard') } catch { /* 空状态 */ }
})
import type { Component } from 'vue';
import { computed, onMounted, ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import { message } from 'ant-design-vue';
import { YdPage, YdReliefIcon, YdStatsCard } from '@/components/youding';
import SkeletonCard from '@/components/common/SkeletonCard.vue';
import { getAuthToken } from '@/utils/api';
import { useAuthStore } from '@/stores/auth';
import { useEffectivePlatformRole } from '@/composables/useEffectivePlatformRole';
import VChart from 'vue-echarts';
import { applySnapCursor, useChartCursor } from '@/composables/useChartCursor';
import { useCountUp } from '@/composables/useCountUp';
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { LineChart, BarChart } from 'echarts/charts';
import { GridComponent, TooltipComponent } from 'echarts/components';
import {
  useAgentCapabilitiesStore,
  AGENT_LEVEL_IDS,
  AGENT_LEVEL_LABELS,
  type AgentLevelId,
} from '@/stores/agentCapabilities';
import { WORKBENCH_CAPABILITY_REGISTRY } from '@/constants/workbenchCapabilityRegistry';
import { WORKBENCH_ICONS } from '@/constants/workbenchIcons';

use([CanvasRenderer, LineChart, BarChart, GridComponent, TooltipComponent]);

const router = useRouter();
const auth = useAuthStore();
const { workbenchTitle } = useEffectivePlatformRole();
const capStore = useAgentCapabilitiesStore();
const searchKeyword = ref('');
const healthOk = ref<boolean | null>(null);
const healthLabel = ref('探测中…');
const urgentTodo = ref<number | string>('—');
const tenantTotal = ref<number | string>('—');
const publishQueue = ref<number | string>('—');
const aitoearnHint = ref('');
const trendData = ref<number[]>([]);
const trendLabels = ref<string[]>([]);
const trendEmpty = ref(true);
const runtimeRows = ref<
  { module: string; status: string; statusText: string; requests: string; errorRate: string; path: string }[]
>([]);
const focusAlerts = ref<{ level: string; title: string; desc: string; path?: string }[]>([]);
const dashboardLoading = ref(true);

async function loadWorkbenchProbes(token: string) {
  const headers = { Authorization: `Bearer ${token}` };
  try {
    const [dashRes, trafficRes, healthRes, bffRes] = await Promise.all([
      fetch('/api/v1/analytics/dashboard', { headers }),
      fetch('/api/v1/analytics/traffic?period=7d', { headers }),
      fetch('/api/v1/system-health/', { headers }),
      fetch('/api/v1/bff/platform/overview', { headers }),
    ]);
    healthOk.value = dashRes.ok && healthRes.ok;

    let bffData: {
      tenant_stats?: Record<string, number>;
      queues?: { pending_inquiries?: number; publish_in_progress?: number };
      alerts?: { frozen_tenants?: number };
      aitoearn?: { enabled?: boolean; hint?: string };
    } | null = null;
    if (bffRes.ok) {
      const bj = await bffRes.json();
      bffData = bj.data || bj;
    }

    if (healthRes.ok) {
      const hj = await healthRes.json();
      const hs = hj.data?.status || 'unknown';
      healthLabel.value = hs === 'healthy' ? '正常' : hs === 'degraded' ? '降级' : '—';
    } else {
      healthLabel.value = '—';
    }

    let dashData: { inquiries?: { pending?: number } } | null = null;
    if (dashRes.ok) {
      const dj = await dashRes.json();
      dashData = dj.data || dj;
    }

    const pendingFromBff = bffData?.queues?.pending_inquiries;
    const pendingFromDash = dashData?.inquiries?.pending;
    const pending =
      typeof pendingFromBff === 'number'
        ? pendingFromBff
        : typeof pendingFromDash === 'number'
          ? pendingFromDash
          : undefined;

    if (typeof pending === 'number') {
      urgentTodo.value = pending;
    }

    if (bffData?.tenant_stats) {
      const total = bffData.tenant_stats.total_tenants ?? bffData.tenant_stats.total;
      if (typeof total === 'number') tenantTotal.value = total;
    }
    if (typeof bffData?.queues?.publish_in_progress === 'number') {
      publishQueue.value = bffData.queues.publish_in_progress;
    }
    aitoearnHint.value = bffData?.aitoearn?.hint || '';

    const alerts: { level: string; title: string; desc: string; path?: string }[] = [];
    if (typeof pending === 'number' && pending > 0) {
      alerts.push({
        level: 'warn',
        title: `待回复询盘 ${pending} 条`,
        desc: '建议优先处理高意向询盘，避免跨日流失',
        path: '/client/inquiries',
      });
    }
    if ((bffData?.alerts?.frozen_tenants || 0) > 0) {
      alerts.push({
        level: 'risk',
        title: `冻结租户 ${bffData!.alerts!.frozen_tenants} 个`,
        desc: '请在租户管理检查冻结原因并恢复',
        path: '/admin/tenants',
      });
    }
    if (typeof bffData?.queues?.publish_in_progress === 'number' && bffData.queues.publish_in_progress > 0) {
      alerts.push({
        level: 'warn',
        title: `发布队列进行中 ${bffData.queues.publish_in_progress} 条`,
        desc: '可在进度看板查看各平台发布状态',
        path: '/admin/system/greedy-publish-queue',
      });
    }
    if (bffData?.aitoearn && !bffData.aitoearn.enabled) {
      alerts.push({
        level: 'warn',
        title: 'AiToEarn 未配置',
        desc: bffData.aitoearn.hint || '请在 backend/.env 配置 AITOEARN_API_KEY',
        path: '/admin/platform-zones',
      });
    }
    if (!alerts.length) {
      alerts.push({ level: 'ok', title: '暂无高优先待办', desc: '可在数据中心查看全站转化' });
    }
    focusAlerts.value = alerts.slice(0, 4);

    if (trafficRes.ok) {
      const tj = await trafficRes.json();
      const rows = tj.data?.data || [];
      if (rows.length) {
        const maxV = Math.max(...rows.map((r: { views?: number }) => r.views || 0), 1);
        trendData.value = rows.map((r: { views?: number }) =>
          Math.max(4, Math.round(((r.views || 0) / maxV) * 100)),
        );
        trendLabels.value = rows.map((r: { date?: string }) => {
          if (r.date) {
            const d = new Date(r.date);
            return `${d.getMonth() + 1}/${d.getDate()}`;
          }
          return '';
        });
        trendEmpty.value = false;
      }
    }

    runtimeRows.value = [
      {
        module: '租户 SaaS',
        status: bffRes.ok ? 'ok' : 'warn',
        statusText: bffRes.ok ? 'BFF 已接' : '未接',
        requests: String(tenantTotal.value),
        errorRate: String(publishQueue.value),
        path: '/tenants/dashboard',
      },
      { module: '数据分析', status: dashRes.ok ? 'ok' : 'warn', statusText: dashRes.ok ? '已接' : '未接', requests: '—', errorRate: '—', path: '/admin/aggregation' },
      { module: '系统健康', status: healthRes.ok ? 'ok' : 'warn', statusText: healthRes.ok ? '已接' : '未接', requests: '—', errorRate: '—', path: '/system-health/dashboard' },
      { module: '发布队列', status: 'ok', statusText: '入口', requests: String(publishQueue.value), errorRate: '—', path: '/admin/system/progress-board' },
    ];
  } catch {
    healthOk.value = false;
    healthLabel.value = '—';
  }
}

onMounted(async () => {
  const token = getAuthToken();
  if (!token) { dashboardLoading.value = false; return; }
  await loadWorkbenchProbes(token);
  dashboardLoading.value = false;
});

const displayName = computed(() => auth.username || '管理员');
const greeting = computed(() => {
  const h = new Date().getHours();
  if (h < 12) return '上午好';
  if (h < 18) return '下午好';
  return '晚上好';
});

function resolveIcon(key: string): Component {
  return WORKBENCH_ICONS[key] ?? WORKBENCH_ICONS.DashboardOutlined;
}

const sections = computed(() =>
  WORKBENCH_CAPABILITY_REGISTRY.map((sec) => ({
    key: sec.key,
    title: sec.title,
    items: sec.items.filter((i) => !i.guardOnly && capStore.canAccess(i.id)),
  })).filter((s) => s.items.length > 0),
);

const totalEntries = computed(() => sections.value.reduce((n, s) => n + s.items.length, 0));

const kpi = computed(() => ({
  functionalDomains: sections.value.length,
  totalEntries: totalEntries.value,
  urgentTodo: urgentTodo.value,
  health: healthLabel.value,
}));

const quickEntries = computed(() => {
  const rows: { label: string; path: string; icon: Component }[] = [];
  for (const sec of WORKBENCH_CAPABILITY_REGISTRY) {
    for (const item of sec.items) {
      if (!item.guardOnly && item.quick && capStore.canAccess(item.id)) {
        rows.push({
          label: item.name,
          path: item.path,
          icon: resolveIcon(item.itemIcon),
        });
      }
    }
  }
  return rows.slice(0, 8);
});

const domainDistribution = computed(() => {
  const sum = totalEntries.value || 1;
  return sections.value.slice(0, 5).map((s) => ({
    name: s.title,
    value: Math.max(6, Math.round((s.items.length / sum) * 100)),
  }));
});

/* ---- ECharts: trend line/area ---- */
const trendChartOption = computed(() => applySnapCursor({
  tooltip: {
    trigger: 'axis',
    backgroundColor: '#fff',
    borderColor: '#e8faf4',
    borderWidth: 1,
    textStyle: { color: '#1f2937', fontSize: 12 },
    formatter: (params: { name: string; value: number }[]) => {
      const p = params[0];
      return `${p.name}<br/><b style="color:var(--uj-brand, #4a9b8c)">${p.value}%</b> 活跃度`;
    },
  },
  grid: { left: 8, right: 12, top: 12, bottom: 4, containLabel: true },
  xAxis: {
    type: 'category',
    data: trendLabels.value.length ? trendLabels.value : ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
    boundaryGap: false,
    axisLine: { show: false },
    axisTick: { show: false },
    axisLabel: { color: '#9ca3af', fontSize: 11 },
  },
  yAxis: {
    type: 'value',
    show: false,
    max: 100,
  },
  series: [
    {
      type: 'line',
      data: trendData.value,
      smooth: true,
      symbol: 'circle',
      symbolSize: 6,
      lineStyle: { color: '#4a9b8c', width: 2.5 },
      itemStyle: { color: '#4a9b8c', borderColor: '#fff', borderWidth: 2 },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(74,155,140,0.25)' },
            { offset: 1, color: 'rgba(74,155,140,0.02)' },
          ],
        },
      },
    },
  ],
}));

/* ══════════════════════════════════════════════════════════════
   游标联动读数（图表游标 → 顶部码表）
   ──────────────────────────────────────────────────────────────
   本页是「读数联动」的**样板页**，另外 5 个折线页按同一模式接入。
   三个必须逐页拍板的设计决策，本页的答案与理由：

     1) **联动哪条 series** —— 本页只有 1 条「活跃度」折线，取它的 y 值，无歧义。
        多 series 的页面必须先指定「主 series」，否则读数会随 tooltip 的
        条目顺序漂移，看起来像随机跳数。
     2) **读数放哪** —— 卡片头部右侧。那里原本是一句静态提示
        「来自 analytics/traffic」，信息价值低且白占位；改为读数区后把数据源
        降级为 hover 的 title，**零布局改动**，也不会与图表内的 tooltip 打架。
     3) **离开图表后显示什么** —— 回到「近 7 日均值」，而不是留空。
        好处：数字区始终有含义；且能看见码表往回收，而不是数字突然消失。
   ══════════════════════════════════════════════════════════════ */

/** 图表容器 ref：vue-echarts 通过 expose 的 `chart` getter 暴露底层实例 */
const trendChartRef = ref<unknown>(null);

const trendAverage = computed(() => {
  const d = trendData.value;
  return d.length ? Math.round(d.reduce((a, b) => a + b, 0) / d.length) : 0;
});

const {
  activeIndex: cursorIndex,
  activeValue: cursorValue,
  bindWhenReady,
} = useChartCursor<number>((info) => {
  const v = trendData.value[info.dataIndex];
  return typeof v === 'number' ? v : null;
});

const cursorActive = computed(() => cursorIndex.value >= 0);

const cursorDay = computed(() => {
  const i = cursorIndex.value;
  if (i < 0) return '';
  const labels = trendLabels.value.length
    ? trendLabels.value
    : ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
  return labels[i] ?? '';
});

const readoutLabel = computed(() =>
  cursorActive.value && cursorDay.value ? cursorDay.value : '近 7 日均值',
);

/** 码表目标：有游标读游标，无游标读均值 —— 两者共用同一个码表，切换时才看得到翻滚 */
const readoutTarget = computed(() => cursorValue.value ?? trendAverage.value);
const readoutText = useCountUp(() => readoutTarget.value, {
  changeDuration: 220,
  decimals: 0,
});

const readoutTitle = computed(() =>
  cursorActive.value
    ? `游标停在 ${cursorDay.value || '该点'} · ${readoutText.value}% 活跃度`
    : '近 7 日活跃度均值 · 数据源：analytics/traffic',
);

/**
 * 绑定图表实例。**必须走有界重试**，原因有两条（都是实测结构决定的）：
 *   · 图表被 `v-if="trendEmpty"` 的骨架屏包着，挂载时机不由本组件决定；
 *   · vue-echarts 的实例初始化走 `initDeferred` + `nextTick`，比 ref 赋值再晚一帧。
 * `flush: 'post'` 保证回调在本次 DOM 更新之后执行。
 */
watch(
  trendChartRef,
  (el) => {
    if (el) void bindWhenReady(() => trendChartRef.value);
  },
  { flush: 'post' },
);

/* ---- ECharts: domain bar chart ---- */
const barChartOption = computed(() => {
  const data = domainDistribution.value;
  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: '#fff',
      borderColor: '#e8faf4',
      borderWidth: 1,
      textStyle: { color: '#1f2937', fontSize: 12 },
      formatter: (params: { name: string; value: number }[]) => {
        const p = params[0];
        return `${p.name}<br/><b style="color:var(--uj-brand, #4a9b8c)">${p.value}%</b>`;
      },
    },
    grid: { left: 8, right: 16, top: 8, bottom: 4, containLabel: true },
    xAxis: {
      type: 'value',
      max: 100,
      axisLine: { show: false },
      axisTick: { show: false },
      splitLine: { lineStyle: { color: '#f0f0f0', type: 'dashed' } },
      axisLabel: { color: '#9ca3af', fontSize: 11, formatter: '{value}%' },
    },
    yAxis: {
      type: 'category',
      data: data.map((d) => d.name),
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: '#4b5563', fontSize: 12 },
    },
    series: [
      {
        type: 'bar',
        data: data.map((d) => d.value),
        barWidth: 14,
        itemStyle: {
          borderRadius: [0, 7, 7, 0],
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 1, y2: 0,
            colorStops: [
              { offset: 0, color: '#8ed4c4' },
              { offset: 1, color: '#4a9b8c' },
            ],
          },
        },
      },
    ],
  };
});

const dashboardTodos = computed(() => {
  const rows: { level: string; levelText: string; title: string; path: string }[] = [];
  if (typeof urgentTodo.value === 'number' && urgentTodo.value > 0) {
    rows.push({
      level: 'p0',
      levelText: 'P0',
      title: `处理 ${urgentTodo.value} 条待回复询盘`,
      path: '/inquiries',
    });
  }
  if (healthOk.value === false) {
    rows.push({
      level: 'p0',
      levelText: 'P0',
      title: '系统健康探针异常，请检查服务',
      path: '/system-health/dashboard',
    });
  }
  if (trendEmpty.value && healthOk.value === true) {
    rows.push({
      level: 'p1',
      levelText: 'P1',
      title: '站点暂无流量数据，可检查埋点或推广',
      path: '/admin/aggregation',
    });
  }
  rows.push({
    level: 'p1',
    levelText: 'P1',
    title: '完成今日七步彩排截图',
    path: '/admin/demo-rehearsal',
  });
  return rows.slice(0, 4);
});

const levelSelectOptions = AGENT_LEVEL_IDS.map((id) => ({
  value: id,
  label: AGENT_LEVEL_LABELS[id],
}));

const sessionLevelModel = computed({
  get: () => capStore.currentLevelId,
  set: (v: AgentLevelId | string) => {
    if (AGENT_LEVEL_IDS.includes(v as AgentLevelId)) capStore.setCurrentLevel(v as AgentLevelId);
  },
});

function navigateTo(path: string) {
  router.push(path);
}

function onSearch(raw: string) {
  const q = raw.trim();
  if (!q) return;
  const found = WORKBENCH_CAPABILITY_REGISTRY.flatMap((s) => s.items).find(
    (i) => capStore.canAccess(i.id) && `${i.name} ${i.description} ${i.path}`.toLowerCase().includes(q.toLowerCase()),
  );
  if (found) {
    router.push(found.path);
    return;
  }
  message.info('未匹配到入口，请换个关键词');
}
</script>

<style scoped lang="scss">
.admin-dashboard {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 4px 4px 8px;
  border-radius: 0;
  background: transparent;
}

.panel {
  background: var(--uj-glass-bg-strong, rgb(255 255 255 / 0.96));
  border: 1px solid var(--uj-border, rgb(255 255 255 / 0.85));
  border-radius: 20px;
  box-shadow: var(--uj-glass-shadow);
}

.topbar.panel {
  background: var(--uj-glass-bg-strong, rgb(255 255 255 / 0.98));
}

.admin-dashboard .topbar {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  padding: 16px;
}

.topbar__title h1 {
  margin: 0;
  font-size: var(--uj-font-size-h1, 24px);
  font-weight: 700;
  color: #111827;
}

.kicker {
  margin: 0;
  color: #667085;
  font-size: var(--uj-font-size-sm, 13px);
}

.desc {
  margin: 2px 0 0;
  color: #98a2b3;
  font-size: var(--uj-text-body, 15px);
}

.kpi-grid :deep(.yd-stats-card:nth-child(1)) { background: var(--uj-mint-pastel-1, #e8faf4); }
.kpi-grid :deep(.yd-stats-card:nth-child(2)) { background: var(--uj-mint-pastel-2, #dff5ee); }
.kpi-grid :deep(.yd-stats-card:nth-child(3)) { background: #e8faf4; }
.kpi-grid :deep(.yd-stats-card:nth-child(4)) { background: var(--uj-mint-pastel-4, #f0fdf9); }

.topbar__tools {
  display: grid;
  grid-template-columns: 220px 170px auto;
  align-items: start;
  gap: 8px;
}

.level-select {
  width: 100%;
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
}

.chart-grid {
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 12px;
}

.trend-empty {
  padding: 24px 0;
  text-align: center;
  color: #64748b;
  font-size: 13px;
}

.chart-card {
  padding: 12px 16px;
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
  color: #9ca3af;
  font-size: 12px;
}

/* ── 游标联动读数 ──
   ⚠️ 特异性：上面的 `.card-head span`(0,1,1) 会给这里所有 span 染上灰色提示色 + 12px，
      所以必须用 `.card-head .cursor-readout`(0,2,0) 盖住，
      否则读数会被当成脚注染灰，读数与提示分不出主次。
   字重只用 400/500（符合设计规范）：靠**字号 + 颜色**而非粗体做强调。 */
.card-head .cursor-readout {
  display: inline-flex;
  align-items: baseline;
  gap: 6px;
  color: var(--uj-text-secondary-strong, #55706b);
  transition: color 0.24s ease;
}

.card-head .cursor-readout .cursor-src {
  font-style: normal;
  font-size: 12px;
  color: inherit;
}

.card-head .cursor-readout .cursor-num {
  font-size: 16px;
  font-weight: 500;
  line-height: 1;
  color: var(--uj-text, #1f2937);
  /* ★ 等宽数字：缺了这行，码表翻滚时数字宽度会左右抖动 */
  font-variant-numeric: tabular-nums;
  letter-spacing: -0.2px;
  transition: color 0.24s ease;
}

.card-head .cursor-readout .cursor-num i {
  font-style: normal;
  font-size: 11px;
  font-weight: 400;
  margin-left: 1px;
  opacity: 0.55;
}

/* 游标激活：整个读数区切到品牌色，提示「这个数字正在跟着图表走」 */
.card-head .cursor-readout.is-live,
.card-head .cursor-readout.is-live .cursor-num {
  color: var(--uj-brand-strong, #367469);
}

.echart-trend {
  width: 100%;
  height: 160px;
}

.echart-bar {
  width: 100%;
  height: 200px;
}

.bottom-grid {
  display: grid;
  grid-template-columns: 1.1fr 1fr;
  gap: 12px;
}

.ops-grid {
  display: grid;
  grid-template-columns: 1.35fr 0.85fr;
  gap: 12px;
}

.todo-card, .quick-card {
  padding: 12px 16px;
}

.todo-card ul {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.todo-card li {
  display: grid;
  grid-template-columns: 44px 1fr;
  gap: 8px;
  align-items: stretch;
  border: 1px solid #edf1f7;
  border-radius: 10px;
  padding: 8px;
}

.todo-level {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  font-weight: 700;
  font-size: 12px;
}

.level-p0 { background: #fee2e2; color: #b91c1c; }
.level-p1 { background: #ffedd5; color: #c2410c; }
.level-p2 { background: #d1f5e9; color: #0369a1; }

.todo-body {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.todo-body p {
  margin: 0;
  color: #1f2937;
  font-size: 13px;
}

.todo-body button {
  border: 1px solid #d1f5e9;
  background: #e8faf4;
  color: var(--uj-brand, #4a9b8c);
  border-radius: 8px;
  padding: 4px 8px;
  font-size: 12px;
  cursor: pointer;
}

.quick-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
}

.quick-item {
  border: 1px solid #e8edf5;
  background: #fff;
  border-radius: 10px;
  min-height: 72px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  font-size: 12px;
  color: #374151;
  cursor: pointer;
}

.quick-item :deep(svg) {
  color: var(--uj-brand, #4a9b8c);
  font-size: 16px;
}

.table-card,
.side-card {
  padding: 12px 16px;
}

.table-wrap {
  overflow: auto;
}

.table-wrap table {
  width: 100%;
  border-collapse: collapse;
  min-width: 560px;
}

.table-wrap th,
.table-wrap td {
  text-align: left;
  padding: 8px;
  border-bottom: 1px solid #eef2f7;
  font-size: 12px;
}

.table-wrap th {
  color: #6b7280;
  font-weight: 600;
}

.table-wrap td {
  color: #1f2937;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 2px 8px;
  font-size: 11px;
  font-weight: 600;
}

.status-ok {
  color: #15803d;
  background: #dcfce7;
}

.status-warn {
  color: #b45309;
  background: #ffedd5;
}

.status-risk {
  color: #b91c1c;
  background: #fee2e2;
}

.row-action {
  border: 1px solid #d1f5e9;
  background: #e8faf4;
  color: var(--uj-brand, #4a9b8c);
  border-radius: 8px;
  padding: 2px 8px;
  font-size: 11px;
  cursor: pointer;
}

.alert-list {
  list-style: none;
  margin: 0 0 12px;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.alert-list li {
  display: grid;
  grid-template-columns: 8px 1fr;
  gap: 8px;
  align-items: start;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-top: 6px;
}

.dot-risk { background: #ef4444; }
.dot-warn { background: #f59e0b; }
.dot-ok { background: #10b981; }

.alert-body p {
  margin: 0;
  font-size: 12px;
  font-weight: 600;
  color: #1f2937;
}

.alert-body small {
  display: block;
  margin-top: 2px;
  font-size: 11px;
  color: #6b7280;
  line-height: 1.4;
}

.alert-clickable {
  cursor: pointer;
  grid-template-columns: 8px 1fr auto;
}

.alert-clickable:hover {
  background: rgba(42, 107, 96, 0.06);
  border-radius: 6px;
}

.alert-arrow {
  font-size: 18px;
  color: #9ca3af;
  align-self: center;
  transition: transform 0.2s;
}

.alert-clickable:hover .alert-arrow {
  color: #2a6b60;
  transform: translateX(2px);
}

/* 主按钮：深蓝灰底 + 白字，避免高饱和紫对比不足 */
.risk-cta:deep(.ant-btn) {
  height: 40px;
  font-size: 14px;
  font-weight: 600;
  letter-spacing: 0.02em;
  background: var(--uj-brand-deep, #2a6b60) !important;
  border-color: var(--uj-brand-deep, #2a6b60) !important;
  color: #fff !important;
  box-shadow: 0 4px 14px rgb(42 107 96 / 0.28);
}
.risk-cta:deep(.ant-btn:hover) {
  background: var(--uj-brand-hover, #3d8578) !important;
  border-color: var(--uj-brand-hover, #3d8578) !important;
  color: #fff !important;
}

@media (max-width: 1200px) {
  .kpi-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .chart-grid,
  .bottom-grid,
  .ops-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 900px) {
  .topbar {
    flex-direction: column;
  }
  .topbar__tools {
    grid-template-columns: 1fr;
  }
  .quick-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
