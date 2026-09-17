/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage surface="elevated">
  <div class="client-dashboard tenant-theme coachpro-tertiary coachpro-tertiary--client">
    <ClientTodayThreeStrip />

    <section class="topbar panel uj-glass-panel">
      <div>
        <p class="kicker">租户工作台 · 建材外贸</p>
        <h1>{{ brand.company_name || '我的工作台' }}</h1>
        <p class="desc">{{ topbarSubtitle }}</p>
      </div>
      <div class="topbar-tools">
        <a-button
          v-for="action in topbarActions"
          :key="action.route"
          size="small"
          :type="action.primary ? 'primary' : 'default'"
          @click="router.push(action.route)"
        >
          {{ action.label }}
        </a-button>
      </div>
    </section>

    <YdTodayWorkbench
      :plan-name="planName"
      :plan-expiry="planExpiry"
      :headline="workbenchHeadline"
      :ai-used="aiQuotaUsed"
      :ai-max="aiQuotaTotal"
      :publish-used="publishInProgressNum"
      :tiles="workbenchTiles"
      :today-items="todayItems"
      @navigate="router.push"
    />

    <section class="kpi-grid">
      <YdStatsCard label="今日海外询盘" :value="stats[0].value" hint="24 小时内全网新增" compact />
      <YdStatsCard label="待响应商机" :value="stats[1].value" hint="建议 30 分钟内 WhatsApp 直连" compact />
      <YdStatsCard label="品类规格建模" :value="stats[2].value" hint="外贸在售与产业带候选" compact />
      <YdStatsCard label="全球关键词矩阵" :value="stats[3].value" hint="Google SEO / GEO 国际词包" compact />
    </section>

    <p v-if="dataHonestyNote" class="honesty-note">{{ dataHonestyNote }}</p>

    <!-- 核心业务中心：左 70% 询盘与外贸转化漏斗 + 右 30% 独立站与出海进展 -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 my-6">
      <div class="lg:col-span-2 space-y-6">
        <!-- 1. 最新买家询盘 (第一优先级) -->
        <div class="panel uj-glass-panel p-5">
          <div class="flex items-center justify-between mb-4">
            <div>
              <h2 class="text-base font-bold text-slate-900">最新海外买家询盘</h2>
              <p class="text-xs text-slate-500 mt-0.5">直接关联西方采购决策流与 WhatsApp 即时跟进</p>
            </div>
            <a class="text-xs text-blue-600 font-medium hover:underline" href="/client/inquiries">全部询盘 ({{ stats[1].value }} 待处理) →</a>
          </div>
          <YdEmptyState v-if="!recentInquiries.length" variant="inquiry" @action="router.push('/client/inquiries')" />
          <div v-else class="space-y-3">
            <div
              v-for="inq in recentInquiries"
              :key="inq.id"
              class="inq-row flex items-center justify-between p-3.5 rounded-xl border border-slate-100 bg-slate-50/50 hover:bg-blue-50/40 hover:border-blue-200 cursor-pointer transition-colors"
              role="button"
              tabindex="0"
              @click="router.push('/client/inquiries')"
              @keydown.enter.prevent="router.push('/client/inquiries')"
            >
              <div class="min-w-0 pr-4">
                <div class="flex items-center gap-2">
                  <p class="text-sm font-semibold text-slate-900 truncate">{{ inq.name }}</p>
                  <span v-if="inq.country" class="text-[10px] px-1.5 py-0.5 bg-slate-200 text-slate-700 rounded font-medium">{{ inq.country }}</span>
                </div>
                <p class="text-xs text-slate-600 truncate mt-1">{{ inq.message?.slice(0, 60) }}</p>
              </div>
              <span class="text-xs text-slate-400 shrink-0">{{ inq.time }}</span>
            </div>
          </div>
        </div>

        <!-- 2. 全球拓客转化漏斗 -->
        <section v-if="funnelSteps.length" class="panel uj-glass-panel funnel-panel">
          <header class="funnel-head">
            <div>
              <h3>全网买家拓客与转化漏斗</h3>
              <p class="funnel-note">基于真实商机、独立站意向与出站分发记录</p>
            </div>
            <a-button size="small" type="link" @click="router.push('/client/inquiries')">去询盘跟进 →</a-button>
          </header>
          <div v-for="step in funnelSteps" :key="step.key" class="funnel-row">
            <span class="funnel-label">{{ step.label }}</span>
            <div class="funnel-track">
              <div class="funnel-fill" :style="{ width: `${step.pct}%` }" />
            </div>
            <span class="funnel-count">{{ step.count }}</span>
          </div>
        </section>
      </div>

      <!-- 右侧 30%：独立站状态与集中收敛的开店进度 -->
      <div class="space-y-6">
        <!-- 我的独立官网状态 -->
        <div class="panel uj-glass-panel p-5">
          <div class="flex items-center justify-between mb-3">
            <h2 class="text-base font-bold text-slate-900">独立站与全球域名</h2>
            <a :href="siteUrl" target="_blank" class="text-blue-600 text-xs font-medium hover:underline">预览网站 ↗</a>
          </div>
          <p class="text-xs text-slate-500 mb-3">Google SEO / GEO 国际排名称重中枢</p>
          <div v-if="httpsProbe" class="https-probe p-3 bg-slate-50 rounded-lg border border-slate-100">
            <div class="flex items-center justify-between gap-2">
              <span class="text-xs font-medium text-slate-700">HTTPS 独立域名探针</span>
              <a-tag :color="httpsTagColor">{{ httpsTagText }}</a-tag>
            </div>
            <p class="text-xs text-slate-500 mt-1">{{ httpsProbeMessage }}</p>
            <div class="https-probe-actions mt-2 flex items-center gap-2">
              <a-button size="small" type="link" class="px-0 text-xs" :loading="httpsLoading" @click="loadHttpsProbe">刷新探针</a-button>
              <a-button v-if="!httpsProbe.ready_for_pilot" size="small" type="link" class="text-xs" @click="router.push('/client/site-editor')">
                去绑定独立域
              </a-button>
            </div>
          </div>
        </div>

        <!-- 统一集中的开户与外贸就绪进度 (收敛替代原先4处重复组件) -->
        <section
          v-if="journeyHealth && journeyHealth.score_pct != null && journeyHealth.score_pct < 100"
          class="panel uj-glass-panel p-5"
        >
          <div class="flex items-start justify-between gap-2 mb-3">
            <div>
              <h3 class="text-base font-bold text-slate-900">外贸开店与合规进度</h3>
              <p class="text-xs text-slate-500 mt-0.5">
                关键就绪度 {{ journeyHealth.score_pct }}%
              </p>
            </div>
            <a-button
              v-if="journeyHealth.next_action?.route"
              size="small"
              type="primary"
              @click="router.push(journeyHealth.next_action.route)"
            >
              {{ journeyHealth.next_action.title || '继续完善' }}
            </a-button>
          </div>
          <ul v-if="journeyInsight.length" class="space-y-2 mt-3">
            <li v-for="item in journeyInsight" :key="item.role" class="p-2.5 bg-slate-50 rounded-lg border border-slate-100">
              <span class="text-xs font-semibold text-blue-600 block">{{ item.label }}</span>
              <p class="text-xs text-slate-600 mt-1">{{ item.insight }}</p>
            </li>
          </ul>
        </section>
      </div>
    </div>
  </div>
  </YdPage>
</template>


<script setup lang="ts">
import { computed, onActivated, onMounted, reactive, ref } from 'vue';
import { useRouter } from 'vue-router';

import {
  YdEmptyState,
  YdOnboardingCard,
  YdPage,
  YdStatsCard,
  YdTodayWorkbench,
} from '@/components/youding';
import type { WorkbenchTile } from '@/components/youding/YdTodayWorkbench.vue';
import type { OnboardingStep, QueueItem } from '@/components/youding/types';
import OnboardingPlainRoadmap, {
  type RoadmapPhase,
} from '@/components/tenant/OnboardingPlainRoadmap.vue';
import JtbdSiteChecklist, {
  type JtbdChecklistItem,
} from '@/components/site-builder/JtbdSiteChecklist.vue';
import ClientTodayThreeStrip from '@/components/client/ClientTodayThreeStrip.vue';
import { useClientTodayThree } from '@/composables/useClientTodayThree';
import { apiGet, getAuthToken } from '@/utils/api';
import { useClientPlanSnapshot } from '@/composables/useClientPlanSnapshot';

interface TenantOnboardingChecklistItem {
  id?: string;
  title?: string;
  status?: string;
}

interface TenantCurrentPayload {
  onboarding?: {
    checklist?: TenantOnboardingChecklistItem[];
    roadmap?: RoadmapPhase[];
  };
}

const router = useRouter();
const planSnapshot = useClientPlanSnapshot();
const {
  payload: todayThreePayload,
  nextStep: todayNextStep,
  allDone: todayAllDone,
  load: loadTodayThree,
} = useClientTodayThree();
const brand = reactive({ company_name: '我的工作台', slogan: '' });
const planName = ref('免费版');
const planExpiry = ref('—');
const aiQuotaUsed = ref(0);
const aiQuotaTotal = ref(0);
const siteUrl = ref('#');
const publishInProgress = ref('0');
const domainStatus = ref<{ has_custom_domain?: boolean; label?: string } | null>(null);

const stats = reactive([
  { label: '今日询盘', value: '0' },
  { label: '待处理', value: '0' },
  { label: '产品数量', value: '0' },
  { label: '关键词', value: '0' },
]);

const recentInquiries = ref<any[]>([]);
const onboardingSteps = ref<OnboardingStep[]>([]);
const onboardingRoadmap = ref<RoadmapPhase[]>([]);
type OnboardingGuide = { id: string; title: string; summary?: string; route?: string };
const onboardingGuides = ref<OnboardingGuide[]>([]);
const jtbdChecklist = ref<JtbdChecklistItem[]>([]);
const roadmapIncomplete = computed(() =>
  onboardingRoadmap.value.some((p) => !p.completed),
);
const jtbdIncomplete = computed(() =>
  jtbdChecklist.value.some((i) => i.status !== 'done'),
);
const todayQueueFromApi = ref<QueueItem[]>([]);
const todayOneThing = ref('');
const autopilotHeadline = ref('');
type FunnelSnap = {
  inquiries_pending?: number
  inquiries_with_phone?: number
  prospects_discovered?: number
  prospects_draft_ready?: number
  publish_pending?: number
  publish_success?: number
}
const funnelSnap = ref<FunnelSnap | null>(null);

type DataHonesty = {
  excluded_inquiries?: number
  note?: string
}
const dataHonesty = ref<DataHonesty | null>(null);
const dataHonestyNote = computed(() => {
  const h = dataHonesty.value;
  if (!h?.excluded_inquiries) return '';
  return h.note || `已排除 ${h.excluded_inquiries} 条本地演示/测试询盘，未上线前不计入。`;
});

type JourneyHealth = {
  score_pct?: number
  checklist_done?: number
  checklist_total?: number
  critical_done?: number
  critical_total?: number
  next_action?: { title?: string; route?: string; reason?: string }
  role_insights?: Array<{ role: string; insight: string; action?: string }>
  data_notes?: { trade_intel_disclaimer?: string; funnel_hint?: string }
}
const journeyHealth = ref<JourneyHealth | null>(null);
const roleLabels: Record<string, string> = {
  pm: '产品经理',
  marketing: '营销',
  strategy: '策略',
  market_research: '市场调研',
  user_research: '用户研究',
  data_analytics: '数据分析',
  ux_research: '体验研究',
  ui_design: '界面设计',
};
const journeyInsight = computed(() =>
  (journeyHealth.value?.role_insights || []).slice(0, 4).map((i) => ({
    ...i,
    label: roleLabels[i.role] || i.role,
  })),
);
const tradeDisclaimer = computed(() => {
  const d = journeyHealth.value?.data_notes?.trade_intel_disclaimer || '';
  return d ? `${d.slice(0, 80)}…` : '';
});

type HttpsProbe = {
  configured?: boolean
  ready_for_pilot?: boolean
  domain?: string
  message?: string
  probe?: { status_code?: number; cert_valid?: boolean; error?: string }
  next_steps?: string[]
}
const httpsProbe = ref<HttpsProbe | null>(null);
const httpsLoading = ref(false);

const httpsTagColor = computed(() => {
  const p = httpsProbe.value;
  if (!p) return 'default';
  if (p.ready_for_pilot) return 'green';
  if (p.configured) return 'orange';
  return 'default';
});

const httpsTagText = computed(() => {
  const p = httpsProbe.value;
  if (!p) return '—';
  if (p.ready_for_pilot) return '可彩排';
  if (p.configured) return '待修复';
  return '未配置';
});

const httpsProbeMessage = computed(() => {
  const p = httpsProbe.value;
  if (!p) return '';
  if (p.ready_for_pilot && p.domain) return `${p.domain} HTTPS 与证书正常，可进行七步②录屏。`;
  if (p.configured && p.domain) {
    const err = p.probe?.error || p.message;
    return err ? `${p.domain}：${err}` : `${p.domain} 尚未通过彩排探针。`;
  }
  return p.message || '请在服务器配置 DEMO_HTTPS_DOMAIN 或在独立域绑定后刷新。';
});

const httpsNextSteps = computed(() => httpsProbe.value?.next_steps?.slice(0, 3) || []);

const funnelSteps = computed(() => {
  const f = funnelSnap.value
  if (!f) return []
  const rows = [
    { key: 'inq', label: '待处理询盘', count: f.inquiries_pending ?? 0 },
    { key: 'phone', label: '带手机号', count: f.inquiries_with_phone ?? 0 },
    { key: 'prospect', label: '待核实候选', count: f.prospects_discovered ?? 0 },
    { key: 'draft', label: '开发信草稿', count: f.prospects_draft_ready ?? 0 },
    { key: 'pub', label: '已发布', count: f.publish_success ?? 0 },
  ]
  const max = Math.max(...rows.map((r) => r.count), 1)
  return rows.map((r) => ({ ...r, pct: Math.round((r.count / max) * 100) }))
});

const tenantAlerts = computed(() => [
  { level: Number(stats[1].value) > 0 ? 'warn' : 'ok', title: '待处理询盘提醒', desc: `当前待处理 ${stats[1].value} 条` },
  { level: Number(publishInProgress.value) > 0 ? 'warn' : 'ok', title: '发布队列状态', desc: `进行中 ${publishInProgress.value} 条` },
  { level: aiQuotaUsed.value / Math.max(aiQuotaTotal.value, 1) > 0.8 ? 'risk' : 'ok', title: 'AI 用量监控', desc: `已用 ${aiQuotaUsed.value}/${aiQuotaTotal.value}` },
]);

const publishInProgressNum = computed(() => Number(publishInProgress.value) || 0);

type TopbarAction = { label: string; route: string; primary?: boolean };

const topbarSubtitle = computed(() => {
  if (todayNextStep.value && !todayAllDone.value) {
    return todayNextStep.value.hint || todayThreePayload.value.headline || '绑域 → 发首条 → 收询盘';
  }
  return '三步已完成 · 继续盯询盘与发品节奏';
});

const topbarActions = computed<TopbarAction[]>(() => {
  const pool: TopbarAction[] = [
    { label: '询盘管理', route: '/client/inquiries' },
    { label: '发布队列', route: '/client/queues/publish' },
    { label: '内容分发', route: '/client/distribute' },
    { label: '今日三步', route: '/client/today' },
  ];
  const actions: TopbarAction[] = [];

  if (todayNextStep.value && !todayAllDone.value) {
    actions.push({
      label: todayNextStep.value.cta,
      route: todayNextStep.value.route,
      primary: true,
    });
    if (todayNextStep.value.alt_route) {
      actions.push({ label: '产业带候选', route: todayNextStep.value.alt_route });
    }
  } else if (todayAllDone.value) {
    actions.push({ label: '查看今日三步', route: '/client/today', primary: true });
  }

  for (const item of pool) {
    if (actions.length >= 3) break;
    if (actions.some((a) => a.route === item.route)) continue;
    actions.push(item);
  }
  return actions.slice(0, 3);
});

const workbenchHeadline = computed(() => {
  if (autopilotHeadline.value) return autopilotHeadline.value;
  if (todayOneThing.value) return todayOneThing.value;
  if (!todayAllDone.value && todayThreePayload.value.headline) {
    return todayThreePayload.value.headline;
  }
  return '';
});

const workbenchTiles = computed<WorkbenchTile[]>(() => {
  const pending = Number(stats[1].value) || 0;
  const publishing = publishInProgressNum.value;
  const domain = domainStatus.value;
  const domainOk = Boolean(domain?.has_custom_domain);
  const tiles: WorkbenchTile[] = [];

  if (todayNextStep.value && !todayAllDone.value) {
    tiles.push({
      id: 'today-next',
      label: todayNextStep.value.title,
      value: `第 ${todayNextStep.value.order} 步`,
      hint: todayNextStep.value.hint,
      route: todayNextStep.value.route,
      tone: 'urgent',
    });
  }

  tiles.push(
    {
      id: 'inquiry',
      label: '待回询盘',
      value: pending,
      hint: pending > 0 ? '建议 24h 内回复' : '暂无积压',
      route: '/client/inquiries',
      tone: pending > 0 ? 'urgent' : 'default',
    },
    {
      id: 'publish',
      label: '待发品 / 发布中',
      value: publishing,
      hint: publishing > 0 ? '查看发布队列' : '选母版发一批',
      route: '/client/queues/publish',
      tone: publishing > 0 ? 'urgent' : 'default',
    },
    {
      id: 'domain',
      label: '独立域',
      value: domainOk ? '已绑定' : '待绑定',
      hint: domain?.label || '绑域 → 发首条 → 收询盘',
      route: domainOk ? '/client/site-editor' : '/client/onboarding',
      tone: domainOk ? 'ok' : 'default',
    },
  );

  return tiles.slice(0, 4);
});

function resolveQueueItemRoute(item: QueueItem): string | undefined {
  if (item.route) return item.route;
  const routes: Record<string, string> = {
    publish: '/client/queues/publish',
    onboarding: journeyHealth.value?.next_action?.route || '/client/onboarding',
    inquiry: '/client/inquiries',
    inquiries: '/client/inquiries',
    blue_ocean: '/client/today',
    product: '/client/products',
  };
  return routes[item.id];
}

const todayItems = computed<QueueItem[]>(() => {
  const items = todayQueueFromApi.value.map((item) => ({
    ...item,
    route: resolveQueueItemRoute(item),
  }));
  if (todayNextStep.value && !todayAllDone.value) {
    items.unshift({
      id: `today-${todayNextStep.value.id}`,
      label: `【今日三步】${todayNextStep.value.cta}：${todayNextStep.value.title}`,
      priority: 'high',
      route: todayNextStep.value.route,
    });
  } else if (onboardingSteps.value.some((s) => !s.done)) {
    const nextOnb = onboardingSteps.value.find((s) => !s.done);
    items.unshift({
      id: 'onb',
      label: '继续体验版三步：绑域 → 发首条 → 收询盘',
      priority: 'high',
      route: nextOnb?.route || '/client/onboarding',
    });
  }
  return items;
});

async function loadDashboard() {
  const tk = getAuthToken();
  if (!tk) return;

  // 并行加载所有不依赖主数据的 API
  const [
    dashboardRes,
    userInfoRes,
    tenantRes,
    snapRes,
    guidesRes,
  ] = await Promise.allSettled([
    fetch('/api/v1/client/dashboard', { headers: { Authorization: `Bearer ${tk}` } }),
    fetch('/api/v1/admin-bff/user/info', { headers: { Authorization: `Bearer ${tk}` } }),
    apiGet<TenantCurrentPayload>('/tenants/current'),
    apiGet<{ funnel?: FunnelSnap }>('/ubrain/ops-snapshot'),
    apiGet<{
      guides?: OnboardingGuide[]
      roadmap?: RoadmapPhase[]
      journey_health?: JourneyHealth
      jtbd_checklist?: JtbdChecklistItem[]
    }>('/client/onboarding-guides'),
  ]);

  // 处理主 Dashboard 数据
  if (dashboardRes.status === 'fulfilled') {
    try {
      const d = await dashboardRes.value.json();
      const data = d.data || d;
      if (data.brand) Object.assign(brand, data.brand);
      if (data.stats) {
        stats[0].value = String(data.stats.today_inquiries ?? '0');
        stats[1].value = String(data.stats.pending_inquiries ?? '0');
        stats[2].value = String(data.stats.total_products ?? '0');
        stats[3].value = String(data.stats.keyword_count ?? '0');
      }
      planName.value = data.plan_name || '免费版';
      planExpiry.value = data.plan_expiry || '—';
      aiQuotaUsed.value = data.ai_quota_used || 0;
      aiQuotaTotal.value = data.ai_quota_total ?? 0;
      siteUrl.value = data.site_url || '#';
      publishInProgress.value = String(data.publish_in_progress ?? '0');
      domainStatus.value = data.domain_status || null;
      if (data.recent_inquiries) recentInquiries.value = data.recent_inquiries;
      if (Array.isArray(data.today_queue)) todayQueueFromApi.value = data.today_queue;
      todayOneThing.value = data.today_one_thing || '';
      if (data.autopilot?.headline) {
        autopilotHeadline.value = data.autopilot.headline;
        localStorage.setItem('tenant_autopilot_headline', data.autopilot.headline);
      } else if (data.autopilot_headline) {
        autopilotHeadline.value = data.autopilot_headline;
      }
      if (data.journey_health) {
        journeyHealth.value = data.journey_health;
      }
      dataHonesty.value = (data.data_honesty as DataHonesty | undefined) ?? null;
    } catch {
      /* offline */
    }
  }

  // 处理用户信息和 on boarding 步骤
  if (userInfoRes.status === 'fulfilled') {
    try {
      const fromBff = await userInfoRes.value.json();
      const steps = fromBff?.data?.onboarding_steps as OnboardingStep[] | undefined;
      if (steps?.length) {
        onboardingSteps.value = steps;
      }
    } catch {
      /* ignore */
    }
  }

  // 处理租户数据
  if (tenantRes.status === 'fulfilled' && tenantRes.value) {
    const tenant = tenantRes.value;
    if (tenant?.onboarding?.roadmap?.length) {
      onboardingRoadmap.value = tenant.onboarding.roadmap;
    }
    if (!onboardingSteps.value.length) {
      const items = tenant?.onboarding?.checklist || [];
      onboardingSteps.value = items.map((c, i) => ({
        id: (c as { key?: string }).key || c.id || `step-${i}`,
        title: c.title || '待办',
        done: c.status === 'done',
        route: (c as { route?: string }).route,
      }));
    }
  }

  // 处理漏斗数据
  if (snapRes.status === 'fulfilled' && snapRes.value) {
    funnelSnap.value = snapRes.value.funnel || null;
  } else {
    funnelSnap.value = null;
  }

  // 处理引导数据
  if (guidesRes.status === 'fulfilled' && guidesRes.value) {
    const guidesData = guidesRes.value;
    onboardingGuides.value = guidesData?.guides || [];
    jtbdChecklist.value = guidesData?.jtbd_checklist || [];
    if (guidesData?.roadmap?.length && !onboardingRoadmap.value.length) {
      onboardingRoadmap.value = guidesData.roadmap;
    }
    if (guidesData?.journey_health && !journeyHealth.value) {
      journeyHealth.value = guidesData.journey_health;
    }
  }

  // 如果还没有 journey_health，单独请求
  if (!journeyHealth.value) {
    try {
      journeyHealth.value = await apiGet<JourneyHealth>('/client/journey-health');
    } catch {
      journeyHealth.value = null;
    }
  }

  // HTTPS 探针和套餐快照（这两个通常较慢，单独处理）
  await loadHttpsProbe();
  await planSnapshot.refresh(true);
}

async function loadHttpsProbe() {
  if (!getAuthToken()) return;
  httpsLoading.value = true;
  try {
    httpsProbe.value = await apiGet<HttpsProbe>('/domains/pilot/demo-https');
  } catch {
    httpsProbe.value = { configured: false, message: 'HTTPS 探针暂不可用' };
  } finally {
    httpsLoading.value = false;
  }
}

onMounted(() => {
  autopilotHeadline.value = localStorage.getItem('tenant_autopilot_headline') || '';
  void loadTodayThree();
  loadDashboard();
});

onActivated(() => {
  void loadTodayThree(true);
});
</script>

<style scoped lang="scss">
@use '@/styles/design-tokens-v2.scss';

.roadmap-panel {
  margin-bottom: 16px;
  padding: var(--uj-space-card);
}
.guide-links {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px dashed var(--uj-border-subtle, #e2e8f0);
}
.guide-links__label {
  font-size: 13px;
  color: #64748b;
  margin: 0 0 8px;
}
.roadmap-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.client-dashboard {
  width: 100%;
  max-width: none;
  margin: 0;
  padding: 4px 2px;
  background: transparent;

  &__onboarding {
    margin-bottom: 16px;
  }
}

.honesty-note {
  margin: 0 0 12px;
  padding: 8px 12px;
  font-size: 12px;
  color: #64748b;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
}

.funnel-panel {
  margin: 12px 0 16px;
  padding: 14px 16px;
}
.funnel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 8px;
  h3 { margin: 0; font-size: 14px; font-weight: 600; }
}
.funnel-note {
  flex: 1 1 100%;
  margin: 0;
  font-size: 11px;
  color: #94a3b8;
}
.journey-health-panel {
  margin: 0 0 16px;
  padding: 14px 16px;
}
.journey-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
  h3 { margin: 0 0 4px; font-size: 14px; font-weight: 600; }
}
.journey-sub {
  margin: 0;
  font-size: 12px;
  color: #64748b;
}
.journey-insights {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 8px;
  li {
    padding: 8px 10px;
    border-radius: 8px;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
  }
  p { margin: 4px 0 0; font-size: 13px; color: #334155; }
  small { color: #64748b; font-size: 11px; }
}
.journey-role {
  font-size: 11px;
  font-weight: 600;
  color: var(--uj-brand, #4a9b8c);
}
.journey-disclaimer {
  margin: 10px 0 0;
  font-size: 11px;
  color: #94a3b8;
}
.funnel-row {
  display: grid;
  grid-template-columns: 88px 1fr 36px;
  gap: 8px;
  align-items: center;
  margin: 4px 0;
}
.funnel-label { font-size: 12px; color: #64748b; }
.funnel-track {
  height: 8px;
  background: #e2e8f0;
  border-radius: 4px;
  overflow: hidden;
}
.funnel-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--uj-brand, #4a9b8c), #60a5fa);
  border-radius: 4px;
}
.funnel-count { font-size: 12px; color: #334155; text-align: right; }

.cell-title {
  font-size: 14px;
  font-weight: 600;
  margin: 0 0 8px;
}
.cell-kpi {
  font-size: 32px;
  font-weight: 700;
  letter-spacing: -0.03em;
  font-variant-numeric: tabular-nums;
  margin: 0 0 8px;
}
.mt-3 {
  margin-top: 12px;
}

/* 玻璃顶栏/卡片见 coachpro-tertiary-pages.scss */

.kicker {
  margin: 0;
  color: #6b7280;
  font-size: 12px;
}

h1 {
  margin: 2px 0 0;
  font-size: 22px;
  font-weight: 700;
  color: #1f2937;
}

.desc {
  margin: 4px 0 0;
  font-size: 12px;
  color: #7e93a3;
}

.today-one {
  margin: 8px 0 0;
  font-size: 13px;
  color: #1e4d63;
  font-weight: 500;
  max-width: 520px;
  line-height: 1.45;
}

.topbar-tools {
  display: flex;
  align-items: start;
  flex-wrap: wrap;
  gap: 8px;
}

.client-dashboard :deep(.topbar-tools .ant-btn-primary) {
  background: linear-gradient(135deg, #1e3a5f, var(--uj-brand, #4a9b8c));
  border: none;
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 10px;
}
.kpi-grid :deep(.yd-stats-card:nth-child(1)) { background: #edf3f7; }
.kpi-grid :deep(.yd-stats-card:nth-child(2)) { background: #e9f4f2; }
.kpi-grid :deep(.yd-stats-card:nth-child(3)) { background: #eef4f7; }
.kpi-grid :deep(.yd-stats-card:nth-child(4)) { background: #eef1f6; }
.client-dashboard :deep(.ant-btn-primary) {
  background: linear-gradient(135deg, #6f97ad, #88acbe);
  border: none;
}

.tenant-alerts {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.tenant-alert {
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

.dot-ok { background: #10b981; }
.dot-warn { background: #f59e0b; }
.dot-risk { background: #ef4444; }

.tenant-alert p {
  margin: 0;
  font-size: 12px;
  color: #1f2937;
  font-weight: 600;
}

.tenant-alert small {
  font-size: 11px;
  color: #6b7280;
}

.https-probe {
  padding: 10px 12px;
  border-radius: 10px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
}
.https-next-steps {
  margin: 6px 0 0;
  padding-left: 18px;
  font-size: 11px;
  color: #64748b;
}
.https-probe-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

@media (max-width: 960px) {
  .topbar {
    flex-direction: column;
  }
  .kpi-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
