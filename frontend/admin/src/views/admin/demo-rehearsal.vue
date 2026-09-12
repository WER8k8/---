<template>

  <YdPage title="90 秒送检彩排" subtitle="融资 / 鉴定演示路径 · 顺序不可改" surface="brand-hero">

    <template #actions>

      <a-button size="small" :loading="loading" @click="loadChecklist">刷新就绪度</a-button>

      <a-button
        v-if="sevenStepAudit && !sevenStepReady"
        size="small"
        :loading="hermesFixing"
        @click="runHermesFix"
      >
        Hermes 尝试修复
      </a-button>

      <a-button type="primary" size="small" @click="router.push('/admin/platform-zones')">三区与送检开关</a-button>

    </template>



    <YdStatsRow :cols="4">

      <YdStatsCard label="总步骤" :value="String(steps.length)" tone="blue" compact />

      <YdStatsCard label="预计时长" value="90s" tone="purple" compact />

      <YdStatsCard

        label="就绪度"

        :value="readinessLabel"

        :tone="readinessTone"

        compact

      />

      <YdStatsCard label="路径版本" value="LOCKED v1" tone="green" compact />

    </YdStatsRow>



    <div v-if="readiness" class="yd-panel mt-4 readiness-banner" :class="readiness.ready ? 'readiness-banner--ok' : 'readiness-banner--warn'">

      <div class="readiness-banner__head">

        <span class="readiness-banner__title">API 就绪探针</span>

        <a-tag :color="readiness.ready ? 'success' : 'warning'">

          {{ readiness.ready ? '可送检' : '待修复' }}

        </a-tag>

      </div>

      <p class="readiness-banner__score">

        pass {{ readiness.score?.pass ?? 0 }}

        · warn {{ readiness.score?.warn ?? 0 }}

        · fail {{ readiness.score?.fail ?? 0 }}

        <span v-if="readiness.environment" class="readiness-banner__env">· {{ readiness.environment }}</span>

      </p>

    </div>



    <div v-if="sevenStepAudit" class="yd-panel mt-4 seven-step-audit">

      <div class="readiness-banner__head">

        <span class="readiness-banner__title">商用七步自动探针（MOD-04）</span>

        <a-tag
          :color="sevenStepReady ? 'success' : 'warning'"
          class="seven-step-status-tag"
          :class="{ 'seven-step-status-tag--action': !sevenStepReady }"
          @click="!sevenStepReady && openFirstFix()"
        >

          {{ sevenStepReady ? '可录屏' : '待修复' }}

        </a-tag>

      </div>

      <p class="readiness-banner__score">

        pass {{ sevenStepAudit.summary?.pass ?? 0 }}

        · warn {{ sevenStepAudit.summary?.warn ?? 0 }}

        · fail {{ sevenStepAudit.summary?.fail ?? 0 }}

      </p>

      <ul class="seven-step-list">

        <li v-for="row in sevenStepAudit.steps || []" :key="row.step" class="seven-step-row">

          <span class="seven-step-idx">{{ row.step }}</span>

          <span class="seven-step-name">{{ row.name }}</span>

          <a-tag :color="stepStatusColor(row.status)">{{ row.status }}</a-tag>

          <span class="seven-step-msg">{{ row.message }}</span>

          <a-button
            v-if="row.status !== 'pass'"
            type="link"
            size="small"
            class="seven-step-fix"
            @click="openStepFix(row)"
          >
            修复
          </a-button>

          <ul v-if="row.step === 5 && row.substeps?.length" class="seven-step-sublist">
            <li v-for="sub in row.substeps" :key="sub.id">
              <strong>{{ sub.id }}</strong> {{ sub.name }}
              <router-link v-if="isAppRoute(sub.route!)" :to="sub.route!" class="demo-link">{{ sub.route }}</router-link>
            </li>
          </ul>

        </li>

      </ul>

    </div>

    <div v-if="step5Substeps.length" class="yd-panel mt-4">
      <h3 class="demo-section-title">七步⑤ 子任务彩排（ITER-03c）</h3>
      <ul class="seven-step-sublist">
        <li v-for="sub in step5Substeps" :key="sub.id">
          <strong>{{ sub.id }}</strong> {{ sub.name }}
          <router-link v-if="isAppRoute(sub.route!)" :to="sub.route!" class="demo-link">打开 →</router-link>
        </li>
      </ul>
      <p class="demo-footnote">截图归档：docs/mod-04-rehearsal/step5/</p>
    </div>



    <div class="yd-panel mt-4">

      <div class="demo-timeline">

        <article

          v-for="s in steps"

          :key="s.id"

          class="demo-step"

          :class="{ 'demo-step--hero': s.phase === 'hero' }"

        >

          <div class="demo-step__time">{{ s.time }}</div>

          <div class="demo-step__body">

            <p class="demo-step__phase">{{ s.phaseLabel }}</p>

            <h3 class="demo-step__title">{{ s.name }}</h3>

            <p class="demo-step__check">{{ s.check }}</p>

            <div class="demo-step__actions">

              <router-link v-if="isAppRoute(s.path)" :to="s.path" class="demo-link">

                打开页面 →

              </router-link>

              <span v-else class="demo-code">{{ s.path }}</span>

            </div>

          </div>

        </article>

      </div>

    </div>



    <a-alert v-if="hint" class="mt-4" type="info" show-icon :message="hint" />

    <a-modal
      v-model:open="httpsFixOpen"
      title="独立域 HTTPS 修复"
      ok-text="探测并刷新"
      cancel-text="关闭"
      :confirm-loading="httpsProbing"
      @ok="probeDemoHttps"
    >
      <p class="fix-modal-lead">
        Hermes 不能代写服务器环境变量。请填写已解析的演示域做真实 HTTPS 探测；生产送检仍须在服务器配置
        <code>DEMO_HTTPS_DOMAIN</code>。
      </p>
      <a-input
        v-model:value="demoDomainInput"
        placeholder="例如 www.example-insulation.com"
        allow-clear
      />
      <a-alert
        v-if="httpsProbeHint"
        class="mt-3"
        :type="httpsProbeHint.type"
        show-icon
        :message="httpsProbeHint.message"
      />
      <ul v-if="httpsNextSteps.length" class="fix-next-steps">
        <li v-for="(line, idx) in httpsNextSteps" :key="idx">{{ line }}</li>
      </ul>
    </a-modal>

  </YdPage>

</template>



<script setup lang="ts">

import { computed, onMounted, ref } from 'vue';

import { useRouter } from 'vue-router';

import { message } from 'ant-design-vue';



import { YdPage, YdStatsCard, YdStatsRow } from '@/components/youding';

import { apiPost, getAuthToken } from '@/utils/api';



/** [锁定] 90 秒路径 — docs/youding-omni-pro-design-LOCKED.md §10 */

const LOCKED_DEMO_STEPS = [

  {

    id: 1,

    time: '0–15s',

    phase: 'hero',

    phaseLabel: '登录',

    name: '分屏登录 + brand-hero',

    check: '无 placeholder；登录后进入运营看板',

    path: '/login',

  },

  {

    id: 2,

    time: '15–30s',

    phase: 'kpi',

    phaseLabel: 'Dashboard',

    name: 'Dashboard KPI + 待办询盘可点击',

    check: 'KPI 有数；待处理询盘卡片可进询盘',

    path: '/admin/dashboard',

  },

  {

    id: 3,

    time: '30–50s',

    phase: 'table',

    phaseLabel: '核心业务',

    name: '租户 / 询盘：列设置 + Drawer + 操作',

    check: 'YdPage + 列设置 + 工具栏；禁止裸 a-table 主列表',

    path: '/admin/tenants',

  },

  {

    id: 4,

    time: '30–50s',

    phase: 'table',

    phaseLabel: '核心业务',

    name: '询盘管理完整链路',

    check: '展开行、导出、审计入口可用',

    path: '/inquiries',

  },

  {

    id: 5,

    time: '50–70s',

    phase: 'theme',

    phaseLabel: '主题',

    name: '主题抽屉：暗色 + 换主色',

    check: '同页不闪崩；表格密度可切换',

    path: '/admin/dashboard',

  },

  {

    id: 6,

    time: '70–90s',

    phase: 'shell',

    phaseLabel: '三角色',

    name: 'Client 壳 · 同布局不同 accent',

    check: '侧栏/Worktab/顶栏结构一致，仅 accent 与菜单不同',

    path: '/client/dashboard',

  },

  {

    id: 7,

    time: '70–90s',

    phase: 'shell',

    phaseLabel: '三角色',

    name: 'Agent 壳 · 业绩与开户',

    check: '一壳三角色叙事闭环',

    path: '/agent/performance',

  },

] as const;



type DemoStep = (typeof LOCKED_DEMO_STEPS)[number];



type ReadinessPayload = {

  ready?: boolean;

  environment?: string;

  score?: { pass?: number; warn?: number; fail?: number };

};



type SevenStepRow = {

  step: number;

  name: string;

  status: string;

  message?: string;

  fix?: { type?: string; hermes_eligible?: boolean; hint?: string };

  substeps?: Array<{ id: string; name: string; route?: string }>;

};



type SevenStepAudit = {

  steps?: SevenStepRow[];

  summary?: { pass?: number; warn?: number; fail?: number; ready_for_recording?: boolean };

  demo_https?: {

    configured?: boolean;

    ready_for_pilot?: boolean;

    message?: string;

    next_steps?: string[];

  };

};



const router = useRouter();

const loading = ref(false);

const readiness = ref<ReadinessPayload | null>(null);

const sevenStepAudit = ref<SevenStepAudit | null>(null);

const demoChecklistSteps = ref<Array<{ step: number; substeps?: Array<{ id: string; name: string; route?: string }> }>>([]);

const hint = ref('');

const hermesFixing = ref(false);

const httpsFixOpen = ref(false);

const httpsProbing = ref(false);

const demoDomainInput = ref('');

const demoDomainOverride = ref('');

const httpsProbeHint = ref<{ type: 'success' | 'warning' | 'error' | 'info'; message: string } | null>(null);

const httpsNextSteps = ref<string[]>([]);

const DEMO_DOMAIN_STORAGE_KEY = 'uj_demo_https_domain_override';

const step5Substeps = computed(() => {
  const fromAudit = sevenStepAudit.value?.steps?.find((s: { step?: number }) => s.step === 5) as
    | { substeps?: Array<{ id: string; name: string; route?: string }> }
    | undefined;
  if (fromAudit?.substeps?.length) return fromAudit.substeps;
  const fromDemo = demoChecklistSteps.value.find((s) => s.step === 5);
  return fromDemo?.substeps || [];
});



const steps = computed<DemoStep[]>(() => [...LOCKED_DEMO_STEPS]);



const readinessLabel = computed(() => {

  if (!readiness.value) return '加载中';

  if (readiness.value.ready) return '就绪';

  return '未就绪';

});



const readinessTone = computed(() => {

  if (!readiness.value) return 'default' as const;

  return readiness.value.ready ? ('green' as const) : ('amber' as const);

});



const sevenStepReady = computed(() => Boolean(sevenStepAudit.value?.summary?.ready_for_recording));

const failedSevenSteps = computed(() =>
  (sevenStepAudit.value?.steps || []).filter((row) => row.status !== 'pass'),
);



function stepStatusColor(status: string) {

  if (status === 'pass') return 'success';

  if (status === 'fail') return 'error';

  return 'warning';

}



function isAppRoute(path: string): boolean {

  return path.startsWith('/') && !path.startsWith('/api/');

}



function openHttpsFixModal(prefill?: string) {

  httpsProbeHint.value = null;

  httpsNextSteps.value = sevenStepAudit.value?.demo_https?.next_steps?.slice(0, 4) || [];

  demoDomainInput.value = (prefill || demoDomainOverride.value || '').trim();

  httpsFixOpen.value = true;

}



function openFirstFix() {

  const first = failedSevenSteps.value[0];

  if (first) {

    openStepFix(first);

    return;

  }

  openHttpsFixModal();

}



function openStepFix(row: SevenStepRow) {

  if (row.step === 2 || row.fix?.type === 'demo_https_domain') {

    openHttpsFixModal();

    return;

  }

  if (row.step === 5) {

    router.push('/inquiries/im-routing');

    return;

  }

  message.info(row.message || `${row.name} 需人工处理，Hermes 无法自动修复此项。`);

}



async function probeDemoHttps() {

  const domain = demoDomainInput.value.trim().toLowerCase();

  if (!domain) {

    httpsProbeHint.value = { type: 'warning', message: '请先填写演示独立域。' };

    return;

  }

  httpsProbing.value = true;

  httpsProbeHint.value = null;

  try {

    demoDomainOverride.value = domain;

    if (typeof localStorage !== 'undefined') {

      localStorage.setItem(DEMO_DOMAIN_STORAGE_KEY, domain);

    }

    await loadSevenStepAudit(domain);

    const https = sevenStepAudit.value?.demo_https;

    httpsNextSteps.value = https?.next_steps?.slice(0, 4) || [];

    if (https?.ready_for_pilot) {

      httpsProbeHint.value = {

        type: 'success',

        message: `${domain} HTTPS 探针已通过。生产环境请同时在服务器配置 DEMO_HTTPS_DOMAIN。`,

      };

      message.success('独立域 HTTPS 已通过探针');

      httpsFixOpen.value = false;

      return;

    }

    httpsProbeHint.value = {

      type: https?.configured ? 'warning' : 'error',

      message: https?.message || 'HTTPS 探针未通过，请检查 DNS / 证书 / 反代。',

    };

  } catch {

    httpsProbeHint.value = { type: 'error', message: '探测失败，请确认 API 可用并已登录。' };

  } finally {

    httpsProbing.value = false;

  }

}



async function runHermesFix() {

  hermesFixing.value = true;

  try {

    const report = await apiPost<{

      remediation?: { attempted?: boolean; reason?: string; summary?: string; actions?: Array<{ action?: string; ok?: boolean }> };

      fail_count?: number;

    }>('/ops/hermes-ops/run');

    const remediation = report?.remediation;

    if (!remediation?.attempted) {

      const reason = remediation?.reason || 'auto_remediation_disabled';

      if (reason === 'auto_remediation_disabled') {

        message.warning('Hermes 自愈未开启（开发环境默认关）。独立域 HTTPS 须人工配置 DEMO_HTTPS_DOMAIN。');

      } else {

        message.info(remediation?.summary || 'Hermes 暂无可自动处理项。');

      }

    } else {

      const ok = remediation.actions?.filter((a) => a.ok).length ?? 0;

      const total = remediation.actions?.length ?? 0;

      message.success(remediation.summary || `Hermes 已执行 ${ok}/${total} 项安全自愈`);

    }

    await loadChecklist();

    if (failedSevenSteps.value.some((row) => row.step === 2)) {

      message.info('② 独立域 HTTPS 不在 Hermes 白名单内，请点「待修复」或行内「修复」配置演示域。');

    }

  } catch {

    message.error('Hermes 运维循环调用失败');

  } finally {

    hermesFixing.value = false;

  }

}



async function loadSevenStepAudit(domainOverride?: string) {

  const tk = getAuthToken();

  if (!tk) return;

  const domain = (domainOverride ?? demoDomainOverride.value).trim();

  const auditUrl = domain

    ? `/api/v1/ops/seven-steps/audit?demo_domain=${encodeURIComponent(domain)}`

    : '/api/v1/ops/seven-steps/audit';

  const auditRes = await fetch(auditUrl, { headers: { Authorization: `Bearer ${tk}` } });

  if (auditRes.ok) {

    const auditBody = await auditRes.json();

    sevenStepAudit.value = auditBody.data || auditBody;

  } else {

    sevenStepAudit.value = null;

  }

}



async function loadChecklist() {

  loading.value = true;

  try {

    const tk = getAuthToken();

    if (!tk) {

      hint.value = '请先登录后再刷新就绪度。';

      readiness.value = null;

      return;

    }

    const res = await fetch('/api/v1/ops/demo-checklist', {

      headers: { Authorization: `Bearer ${tk}` },

    });

    if (!res.ok) throw new Error(`HTTP ${res.status}`);

    const body = await res.json();

    const data = body.data || body;

    demoChecklistSteps.value = Array.isArray(data.steps) ? data.steps : [];
    readiness.value = data.readiness || null;

    hint.value =

      data.recording_hint ||

      '录屏时按 LOCKED 路径顺序演示；送检模式下水印已开启。';

    try {

      await loadSevenStepAudit();

    } catch {

      sevenStepAudit.value = null;

    }

  } catch {

    hint.value = '使用内置 LOCKED 90 秒路径；API 彩排清单暂不可用。';

    readiness.value = null;

  } finally {

    loading.value = false;

  }

}



onMounted(() => {

  if (typeof localStorage !== 'undefined') {

    demoDomainOverride.value = localStorage.getItem(DEMO_DOMAIN_STORAGE_KEY) || '';

  }

  void loadChecklist();

});

</script>



<style scoped>

.mt-4 {

  margin-top: 16px;

}

.readiness-banner {

  padding: 14px 16px;

}

.readiness-banner--ok {

  border-color: rgb(22 163 74 / 0.25);

  background: linear-gradient(135deg, rgb(22 163 74 / 0.06), rgb(22 163 74 / 0.02));

}

.readiness-banner--warn {

  border-color: rgb(217 119 6 / 0.25);

  background: linear-gradient(135deg, rgb(217 119 6 / 0.06), rgb(217 119 6 / 0.02));

}

.readiness-banner__head {

  display: flex;

  align-items: center;

  justify-content: space-between;

  gap: 12px;

}

.readiness-banner__title {

  font-size: 14px;

  font-weight: 600;

  color: var(--uj-text-secondary, #0f172a);

}

.readiness-banner__score {

  margin: 8px 0 0;

  font-size: 13px;

  color: var(--uj-text-muted, #64748b);

}

.readiness-banner__env {

  color: var(--uj-text-muted, #94a3b8);

}

.demo-timeline {

  display: flex;

  flex-direction: column;

  gap: 12px;

}

.demo-step {

  display: grid;

  grid-template-columns: 72px 1fr;

  gap: 16px;

  padding: 16px;

  border: 1px solid var(--uj-border, #e2e8f0);

  border-radius: var(--uj-radius-lg, 12px);

  background: var(--uj-bg-card, #fff);

}

.demo-step--hero {

  border-color: rgb(37 99 235 / 0.2);

  background: linear-gradient(135deg, rgb(37 99 235 / 0.04), rgb(139 92 246 / 0.03));

}

.demo-step__time {

  font-size: 11px;

  font-weight: 600;

  color: var(--uj-brand, #4a9b8c);

  padding-top: 2px;

}

.demo-step__phase {

  font-size: 11px;

  color: var(--uj-text-muted, #94a3b8);

  margin-bottom: 4px;

}

.demo-step__title {

  font-size: 15px;

  font-weight: 600;

  color: var(--uj-text-secondary, #0f172a);

  margin: 0 0 6px;

}

.demo-step__check {

  font-size: 13px;

  color: var(--uj-text-muted, #64748b);

  margin: 0 0 10px;

  line-height: 1.5;

}

.demo-link {

  font-size: 13px;

  color: var(--uj-brand-deep, var(--uj-brand, #4a9b8c));

  text-decoration: none;

}

.demo-link:hover {

  text-decoration: underline;

}

.demo-code {

  font-size: 12px;

  color: var(--uj-text-muted, #64748b);

  font-family: ui-monospace, monospace;

}

.seven-step-audit {

  padding: 14px 16px;

}

.seven-step-list {

  list-style: none;

  margin: 12px 0 0;

  padding: 0;

  display: flex;

  flex-direction: column;

  gap: 8px;

}

.seven-step-row {

  display: grid;

  grid-template-columns: 28px 88px 64px minmax(0, 1fr) auto;

  gap: 8px;

  align-items: center;

  font-size: 12px;

}

.seven-step-idx {

  font-weight: 700;

  color: var(--uj-brand, #4a9b8c);

}

.seven-step-name {

  font-weight: 600;

  color: var(--uj-text-secondary, #334155);

}

.seven-step-msg {

  color: var(--uj-text-secondary, #475569);

  overflow: hidden;

  text-overflow: ellipsis;

  white-space: nowrap;

}

.seven-step-fix {

  padding: 0 4px;

  font-size: 12px;

  color: var(--uj-brand-deep, var(--uj-brand, #4a9b8c));

}

.seven-step-status-tag--action {

  cursor: pointer;

}

.seven-step-status-tag--action:hover {

  opacity: 0.88;

}

.fix-modal-lead {

  margin: 0 0 12px;

  font-size: 13px;

  line-height: 1.55;

  color: var(--uj-text-secondary, #475569);

}

.fix-modal-lead code {

  font-size: 12px;

  color: var(--uj-brand-deep, var(--uj-brand, #4a9b8c));

}

.fix-next-steps {

  margin: 12px 0 0;

  padding-left: 18px;

  font-size: 12px;

  color: var(--uj-text-muted, #64748b);

  line-height: 1.6;

}

.seven-step-sublist {

  grid-column: 1 / -1;

  list-style: none;

  margin: 8px 0 0 28px;

  padding: 0;

  display: flex;

  flex-direction: column;

  gap: 6px;

  font-size: 12px;

  color: var(--uj-text-muted, #64748b);

}

.seven-step-sublist strong {

  color: var(--uj-text-secondary, #334155);

  font-weight: 600;

}

.demo-section-title {

  font-size: 16px;

  font-weight: 600;

  color: var(--uj-text-secondary, #0f172a);

  margin: 0 0 8px;

}

.demo-footnote {

  font-size: 12px;

  color: var(--uj-text-muted, #64748b);

  margin-top: 8px;

}

</style>


