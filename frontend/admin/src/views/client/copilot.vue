/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage surface="elevated">
  <main class="copilot-page" aria-labelledby="copilot-title">
    <header class="copilot-header">
      <h1 id="copilot-title" class="text-xl font-bold text-gray-900">{{ tenantBrand.flywheelTitle }}</h1>
      <p class="text-sm text-slate-600 mt-1">
        {{ tenantBrand.headerSubtitle }}
      </p>
      <p v-if="memoryHint" class="text-xs text-indigo-600 mt-1">{{ memoryHint }}</p>
      <p class="mt-2 text-sm">
        <router-link to="/client/publish" class="text-indigo-600 hover:underline">统一发布台</router-link>
        ·
        <router-link to="/client/plugin-market" class="text-indigo-600 hover:underline">旺财插件市场</router-link>
        ·
        <router-link to="/client/foreign-trade-team" class="text-indigo-600 hover:underline">AI 外贸团队</router-link>
        ·
        <router-link to="/client/tokens" class="text-indigo-600 hover:underline">AI 流量充值</router-link>
      </p>
    </header>

    <a-alert
      v-if="usagePolicyNotice && aiConnectFreeTier"
      type="warning"
      show-icon
      class="copilot-ai-connect"
      message="英伟达免费通道 · 客户须知"
    >
      <template #description>
        <p class="whitespace-pre-wrap">{{ usagePolicyNotice }}</p>
        <p v-if="probeSummaryLine" class="text-xs text-gray-600 mt-2">{{ probeSummaryLine }}</p>
      </template>
    </a-alert>
    <a-alert
      v-else-if="aiConnectNotice"
      :type="aiConnectAlertType"
      show-icon
      class="copilot-ai-connect"
      :message="aiConnectAlertTitle"
      :description="aiConnectNotice"
    />

    <section v-if="flywheel" class="flywheel-card flywheel-primary">
      <h2 class="text-sm font-semibold text-gray-800">卖货飞轮状态</h2>
      <p class="text-xs text-gray-500">{{ flywheelArchitecture }}</p>
      <div class="pillar-grid">
        <div
          v-for="key in pillarKeys"
          :key="key"
          class="pillar"
          :class="pillarClass(key)"
        >
          <span class="pillar-label">{{ pillarLabel(key) }}</span>
          <span class="pillar-status">{{ pillarStatusText(key) }}</span>
          <span class="pillar-hint">{{ pillarHint(key) }}</span>
        </div>
      </div>
      <p v-if="integrationLine" class="text-xs text-slate-500 mt-1">{{ integrationLine }}</p>
      <p v-if="opsSnapshot" class="text-xs text-slate-700 mt-2">
        经营快照：待处理询盘 {{ opsSnapshot.pending_inquiries ?? 0 }}
        （手机 {{ opsSnapshot.pending_with_phone ?? 0 }}）· 待开发信 {{ opsSnapshot.prospects_draft_ready ?? 0 }}
        <template v-if="opsSnapshot.funnel?.prospects_discovered != null && opsSnapshot.funnel.prospects_discovered > 0">
          · 待核实候选 {{ opsSnapshot.funnel.prospects_discovered }}
        </template>
        <template v-if="opsSnapshot.funnel?.publish_success != null">
          · 已发布 {{ opsSnapshot.funnel.publish_success }}
        </template>
        <template v-if="opsSnapshot.publish_failures != null">
          · 发布失败 {{ opsSnapshot.publish_failures }}
        </template>
        <template v-if="opsSnapshot.ssl_failed != null && opsSnapshot.ssl_failed > 0">
          · SSL 失败 {{ opsSnapshot.ssl_failed }}
        </template>
        <template v-if="opsSnapshot.ssl_expiring_soon != null && opsSnapshot.ssl_expiring_soon > 0">
          · 证书将到期 {{ opsSnapshot.ssl_expiring_soon }}
        </template>
        <template
          v-if="opsSnapshot.platform_accounts_unbound != null && opsSnapshot.platform_accounts_unbound > 0"
        >
          · 未绑平台 {{ opsSnapshot.platform_accounts_unbound }}
        </template>
        <template v-if="opsSnapshot.ai_quota_total != null && opsSnapshot.ai_quota_total > 0">
          · AI {{ opsSnapshot.ai_quota_used ?? 0 }}/{{ opsSnapshot.ai_quota_total }}
        </template>
      </p>
      <ul v-if="opsHints.length" class="text-xs text-amber-800 mt-1">
        <li v-for="(h, i) in opsHints" :key="i">{{ h }}</li>
      </ul>
      <div v-if="funnelSteps.length" class="funnel-wrap mt-3">
        <p class="text-xs font-medium text-gray-700 mb-1">卖货漏斗（只读）</p>
        <div v-for="step in funnelSteps" :key="step.key" class="funnel-row">
          <span class="funnel-label">{{ step.label }}</span>
          <div class="funnel-track">
            <div class="funnel-fill" :style="{ width: `${step.pct}%` }" />
          </div>
          <span class="funnel-count">{{ step.count }}</span>
        </div>
      </div>
      <div class="flywheel-actions">
        <button type="button" class="btn-flywheel" @click="runFullFlywheel">
          跑一轮飞轮（研究→找客）
        </button>
        <button type="button" class="link-btn" @click="syncFeedback">同步反馈</button>
        <button type="button" class="link-btn" @click="refreshFlywheelView">刷新</button>
      </div>
      <ul v-if="recentInsights.length" class="insight-list">
        <li v-for="ins in recentInsights" :key="ins.id">
          <strong>{{ polishCustomerText(String(ins.title || ''), tenantBrand.companyName.value) }}</strong>
          <span class="text-xs text-gray-500"> · {{ ins.intent }} · {{ ins.quality_score }}</span>
        </li>
      </ul>
      <p v-if="lastPipelineText" class="text-xs text-slate-600 mt-2">{{ lastPipelineText }}</p>
      <ul v-if="pipelines.length" class="pipeline-list">
        <li v-for="p in pipelines" :key="p.id" class="pipeline-row">
          <span class="pipeline-status" :class="'st-' + p.status">{{ p.status }}</span>
          <span class="text-xs text-gray-600">
            {{ pipelineStepLabel(p) }}
            · {{ p.job_count }} 任务
            <template v-if="p.finished_at"> · {{ formatTime(p.finished_at) }}</template>
          </span>
        </li>
      </ul>
    </section>

    <section class="brief-card">
      <h2 class="text-sm font-semibold text-gray-800">{{ BRAND.researchBrief }}</h2>
      <form class="brief-form" @submit.prevent="generateBrief()">
        <input
          v-model="briefQuery"
          type="text"
          placeholder="例如：中东保温建材蓝海与出口可行性"
        />
        <button type="submit" :disabled="briefLoading">生成简报</button>
      </form>
      <div v-if="briefTemplates.length" class="template-chips mt-2">
        <span class="text-xs text-gray-500 mr-1">对标模板：</span>
        <button
          v-for="t in briefTemplates"
          :key="t.id"
          type="button"
          class="chip"
          :disabled="briefLoading"
          @click="generateBriefFromTemplate(t)"
        >
          {{ t.title }}
        </button>
      </div>
      <p v-if="briefSummary" class="text-sm text-gray-700 mt-2 whitespace-pre-wrap">{{ briefSummary }}</p>
      <div v-if="briefActions.length" class="action-chips">
        <button
          v-for="(a, idx) in briefActions"
          :key="idx"
          type="button"
          class="chip accent"
          @click="runBriefAction(a)"
        >
          {{ skillLabel(a.skill_id) }}{{ a.requires_confirmation ? ' · 需确认' : '' }}
        </button>
      </div>
    </section>

    <section class="accio-cards">
      <h2 class="text-sm font-semibold text-gray-800">{{ BRAND.executionLayer }}</h2>
      <div class="accio-grid">
        <button type="button" class="accio-card" @click="ask('找中东 8 家保温建材采购商')">
          <span class="accio-title">自动找客</span>
          <span class="accio-desc">区域采购商画像 → 入库待核实</span>
        </button>
        <button type="button" class="accio-card" @click="ask('生成 5 封英文开发信')">
          <span class="accio-title">开发信</span>
          <span class="accio-desc">中英草稿 · 发送前您确认</span>
        </button>
        <button type="button" class="accio-card" @click="ask('客户压价怎么谈，给三轮话术')">
          <span class="accio-title">自动谈单</span>
          <span class="accio-desc">报价/还价/临门 · 不自动改价</span>
        </button>
        <button type="button" class="accio-card" @click="runGeoContentMatrix">
          <span class="accio-title">GEO 内容矩阵</span>
          <span class="accio-desc">SEO 母版 + 多平台变体 → 统一发布台</span>
        </button>
      </div>
    </section>

    <section v-if="weekly" class="weekly-card">
      <h2 class="text-sm font-semibold text-gray-800">线索周报（辅助）</h2>
      <div class="weekly-grid">
        <div class="stat">
          <span class="stat-label">样本线索</span>
          <span class="stat-value">{{ weekly.sample_size ?? 0 }}</span>
        </div>
        <div class="stat">
          <span class="stat-label">带手机号</span>
          <span class="stat-value accent">{{ weekly.with_phone ?? 0 }}</span>
        </div>
      </div>
      <button type="button" class="link-btn" @click="ask('生成本周线索复盘')">刷新周报</button>
      <button type="button" class="link-btn ml-2" @click="exportInquiriesCsv">导出询盘 CSV</button>
      <button type="button" class="link-btn ml-2" @click="exportProspectsCsv">导出候选 CSV</button>
    </section>

    <section v-if="auditSummary.skills?.length" class="audit-card">
      <h2 class="text-sm font-semibold text-gray-800">能力复盘（近 {{ auditSummary.period_days ?? 7 }} 天）</h2>
      <p class="text-xs text-gray-500">共 {{ auditSummary.total_actions ?? 0 }} 次副驾动作</p>
      <div v-for="s in auditSummary.skills" :key="s.intent" class="skill-bar-row">
        <span class="skill-bar-label">{{ s.label }}</span>
        <div class="skill-bar-track">
          <div class="skill-bar-fill" :style="{ width: `${s.pct ?? 0}%` }" />
        </div>
        <span class="skill-bar-count">{{ s.count }}</span>
      </div>
    </section>

    <section v-if="actionAudits.length" class="audit-card">
      <h2 class="text-sm font-semibold text-gray-800">动作记录</h2>
      <p class="text-xs text-gray-500">对话与确认发送记录，不含真实外发内容。</p>
      <ul class="audit-list">
        <li v-for="a in actionAudits" :key="a.id">
          <span class="audit-type">{{ auditTypeLabel(a.action_type) }}</span>
          <span class="text-xs text-gray-600">
            {{ a.intent || '—' }}
            <template v-if="a.needs_confirmation"> · 待确认</template>
            · {{ formatTime(a.created_at!) }}
          </span>
          <span v-if="a.message_preview" class="text-xs text-slate-500 block truncate">
            {{ a.message_preview }}
          </span>
        </li>
      </ul>
    </section>

    <div class="chat-card">
      <div
        ref="listEl"
        class="chat-list"
        role="log"
        aria-live="polite"
        aria-relevant="additions"
        aria-label="对话记录"
      >
        <div
          v-for="(m, i) in messages"
          :key="i"
          class="chat-row"
          :class="m.role"
        >
          <p class="whitespace-pre-wrap">{{ m.text }}</p>
          <p v-if="m.disclaimer" class="disclaimer">{{ m.disclaimer }}</p>
        </div>
      </div>
      <form class="chat-form" @submit.prevent="send" :aria-busy="loading">
        <label for="copilot-input" class="sr-only">向卖货副驾提问</label>
        <textarea
          id="copilot-input"
          v-model="input"
          rows="2"
          placeholder="例如：同步销售反馈；或描述本轮研究目标"
          :disabled="loading"
        />
        <button type="submit" :disabled="loading" :aria-label="loading ? '发送中' : '发送消息'">
          {{ loading ? '发送中…' : '发送' }}
        </button>
      </form>
    </div>

    <div class="quick-chips">
      <button
        v-for="q in samples"
        :key="q"
        type="button"
        class="chip"
        @click="ask(q)"
      >
        {{ q }}
      </button>
    </div>

    <section v-if="partialSkills.length" class="gap-card partial-card">
      <h2 class="text-sm font-semibold text-gray-800">可先试用的能力（MVP）</h2>
      <p class="text-xs text-slate-600">点「试用」走真实 MVP 接口；完整能力仍在排期中。</p>
      <ul class="partial-skill-list">
        <li v-for="g in partialSkills" :key="g.id" class="partial-skill-row">
          <span class="partial-skill-name">{{ gapSkillLabel(g) }}</span>
          <span class="partial-skill-actions">
            <button type="button" class="chip partial" :disabled="partialTrying === g.id" @click="tryPartialSkill(g)">
              {{ partialTrying === g.id ? '试用中…' : '试用' }}
            </button>
            <button type="button" class="chip partial outline" @click="explainGap(g)">说明</button>
          </span>
        </li>
      </ul>
      <div v-if="partialFollowUp" class="partial-follow-up">
        <button type="button" class="link-btn" @click="goPartialFollowUp">
          {{ partialFollowUp.label }} →
        </button>
      </div>
    </section>

    <section v-if="gapSkills.length" class="gap-card">
      <h2 class="text-sm font-semibold text-gray-800">{{ BRAND.roadmap }}</h2>
      <p class="text-xs text-gray-500">以下能力在排期中；已上线功能请直接用上方对话或快捷按钮。</p>
      <div class="quick-chips">
        <button
          v-for="g in gapSkills"
          :key="g.id"
          type="button"
          class="chip gap"
          @click="explainGap(g)"
        >
          {{ gapSkillLabel(g) }}
        </button>
      </div>
    </section>

    <section v-if="pendingConfirm" class="confirm-card">
      <p class="text-sm font-medium text-amber-800">需要您确认后才会执行对外动作</p>
      <p class="text-xs text-gray-600 mt-1">{{ pendingConfirm.summary }}</p>
      <div class="confirm-actions">
        <button type="button" class="btn-primary" @click="confirmPending">确认执行</button>
        <button type="button" class="btn-ghost" @click="pendingConfirm = null">取消</button>
      </div>
    </section>

    <section v-if="lastTask" class="task-card">
      <h2 class="text-sm font-semibold text-gray-800">最近任务</h2>
      <p class="text-xs text-gray-500">工具：{{ lastTask.tool }} · 意图：{{ lastTask.intent }}</p>
      <p v-if="jobStatus" class="text-sm mt-2" :class="jobStatusClass">
        任务 {{ jobStatus.intent || BRAND.deepResearchJob }}
        · {{ jobStatus.id?.slice(0, 8) }}… · {{ jobStatus.status }}
        <span v-if="jobStatus.error_message" class="text-red-600"> · {{ jobStatus.error_message }}</span>
        <button
          v-if="jobStatus.status === 'queued' || jobStatus.status === 'running'"
          type="button"
          class="link-btn ml-2"
          @click="refreshJob"
        >
          刷新状态
        </button>
      </p>
      <div v-if="jobStatus" class="job-progress-wrap">
        <div class="job-progress-track">
          <div class="job-progress-fill" :style="{ width: `${jobProgressPct}%` }" />
        </div>
        <span class="text-xs text-gray-500">{{ jobProgressPct }}%</span>
      </div>
      <ol v-if="jobSteps.length" class="job-steps mt-2">
        <li v-for="s in jobSteps" :key="s.index" :class="['job-step', `job-step--${s.status}`]">
          <span class="job-step-idx">{{ s.index }}</span>
          {{ s.title }}
        </li>
      </ol>
      <button
        v-if="jobStatus?.intent === 'geo_content_matrix' && jobStatus?.status === 'success'"
        type="button"
        class="link-btn mt-2"
        @click="openPublishWithJob"
      >
        打开统一发布台人审 →
      </button>
      <pre
        v-if="jobStatus?.log_tail"
        class="task-json text-xs mt-1 max-h-24 overflow-auto"
      >{{ jobStatus.log_tail }}</pre>
      <p
        v-if="commercialHook"
        class="text-xs text-indigo-700 mt-1"
      >
        卖货飞轮：洞察 {{ commercialHook.insight_id?.slice(0, 8) }}… ·
        编排 {{ commercialHook.pipeline?.status }}
      </p>
      <ul v-if="prospectPreview.length" class="prospect-list">
        <li v-for="p in prospectPreview" :key="p.id">
          <strong>{{ p.title }}</strong>
          <span class="text-xs text-amber-700"> · 待核实候选</span>
          <span class="text-xs text-gray-500"> · {{ p.fit_score }}分 · {{ p.suggested_channel }}</span>
          <button
            v-if="p.id"
            type="button"
            class="link-btn ml-1"
            @click="markProspectContacted(String(p.id))"
          >
            标记已联系
          </button>
        </li>
      </ul>
      <ul v-if="letterPreview.length" class="letter-list">
        <li v-for="(L, idx) in letterPreview" :key="idx">
          <p class="text-xs font-medium text-gray-700">{{ L.subject || L.subject_en || `开发信 ${idx + 1}` }}</p>
          <p class="text-xs text-gray-600 whitespace-pre-wrap">{{ (L.body || L.body_en || '').slice(0, 280) }}…</p>
        </li>
      </ul>
      <div v-if="agentSkillPreview" class="agent-skill-card mt-2">
        <p class="text-xs font-semibold text-indigo-800">
          {{ skillLabel(agentSkillPreview.skillId) }}
          <span v-if="agentSkillPreview.rating" class="text-amber-700"> · {{ agentSkillPreview.rating }}</span>
        </p>
        <p class="text-xs text-gray-700 mt-1">{{ agentSkillPreview.summary }}</p>
        <ul v-if="agentSkillPreview.actions.length" class="text-xs text-gray-600 mt-1 pl-4">
          <li v-for="(a, i) in agentSkillPreview.actions" :key="i">{{ a }}</li>
        </ul>
        <button
          v-if="agentSkillPreview.markdown"
          type="button"
          class="link-btn mt-2"
          @click="downloadPiMarkdown"
        >
          下载 PI Markdown
        </button>
        <button
          v-if="agentSkillPreview.markdown"
          type="button"
          class="link-btn mt-2 ml-2"
          @click="downloadPiPdf"
        >
          下载 PI PDF
        </button>
      </div>
      <div v-if="flywheelDiligenceLine" class="text-xs text-slate-700 mt-2">
        飞轮背调：{{ flywheelDiligenceLine }}
      </div>
      <pre
        v-if="lastTask.tool_result && !prospectPreview.length && !briefInResult && !agentSkillPreview"
        class="task-json"
      >{{ formatResult(lastTask.tool_result) }}</pre>
    </section>

    <section v-if="recentJobs.length" class="task-card">
      <h2 class="text-sm font-semibold text-gray-800">异步任务</h2>
      <ul class="job-list">
        <li v-for="j in recentJobs" :key="j.id" class="job-row">
          <button type="button" class="link-btn" @click="selectJob(j.id)">
            {{ j.intent }} · {{ j.id.slice(0, 8) }}… · {{ j.status }}
          </button>
          <span class="text-xs text-gray-400">{{ formatTime(j.created_at || '') }}</span>
        </li>
      </ul>
    </section>
  </main>
  </YdPage>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { message } from 'ant-design-vue';
import { YdPage } from '@/components/youding';
import { getAuthToken } from '@/utils/api';
import { useTenantBrand } from '@/composables/useTenantBrand'
import { useUbrainChatContext } from '@/composables/useUbrainChatContext'
import { useAiConnect } from '@/composables/useAiConnect'
import {
  BRAND,
  gapSkillLabel,
  polishCustomerText,
  skillLabel,
} from '@/constants/sales-assistant-brand'
import { downloadMarkdown, exportProformaFile } from '@/api/foreign-trade'

const tenantBrand = useTenantBrand()
const router = useRouter()
const route = useRoute()
const ubrainCtx = useUbrainChatContext()
const {
  notice: aiConnectNotice,
  freeTier: aiConnectFreeTier,
  alertType: aiConnectAlertType,
  alertTitle: aiConnectAlertTitle,
  usagePolicyNotice,
  probeSummaryLine,
  refresh: refreshAiConnect,
} = useAiConnect()

type Msg = { role: 'user' | 'assistant'; text: string; disclaimer?: string }
type UBrainReply = {
  reply?: string
  disclaimer?: string
  intent?: string
  tool?: string
  tool_result?: Record<string, unknown>
  needs_confirmation?: boolean
  memory_snapshot?: Record<string, unknown>
}

type BriefAction = {
  skill_id?: string
  priority?: number
  requires_confirmation?: boolean
  params?: { message?: string }
}

const pillarKeys = ['memory', 'execution', 'feedback'] as const

const input = ref('')
const loading = ref(false)
const briefLoading = ref(false)
const briefQuery = ref('中东保温建材市场研究与找客建议')
const briefSummary = ref('')
const briefActions = ref<BriefAction[]>([])
type BriefTemplate = {
  id: string
  title: string
  message_default?: string
}
const briefTemplates = ref<BriefTemplate[]>([])
const listEl = ref<HTMLElement | null>(null)
const lastTask = ref<UBrainReply | null>(null)
const jobStatus = ref<{
  id?: string
  status?: string
  intent?: string
  error_message?: string
  log_tail?: string
  result?: Record<string, unknown>
  steps?: Array<{ index: number; title: string; status: string }>
} | null>(null)
const recentJobs = ref<
  Array<{ id: string; status: string; intent: string; created_at?: string }>
>([])
const pendingConfirm = ref<{ summary: string; message: string; intent?: string } | null>(null)
const weekly = ref<Record<string, unknown> | null>(null)
const memoryHint = ref('')
const flywheel = ref<Record<string, unknown> | null>(null)
type OpsSnapshot = {
  pending_inquiries?: number
  pending_with_phone?: number
  prospects_draft_ready?: number
  publish_failures?: number
  ssl_failed?: number
  ssl_expiring_soon?: number
  platform_accounts_total?: number
  platform_accounts_bound?: number
  platform_accounts_unbound?: number
  funnel?: {
    inquiries_pending?: number
    inquiries_with_phone?: number
    prospects_discovered?: number
    prospects_draft_ready?: number
    publish_pending?: number
    publish_success?: number
  }
  hints?: string[]
  ai_quota_used?: number
  ai_quota_total?: number
}
const opsSnapshot = ref<OpsSnapshot | null>(null)
type GapSkill = {
  id: string
  accio_analog?: string
  group_name?: string
  note?: string
  gap?: string
  mvp?: boolean
}
const gapSkills = ref<GapSkill[]>([])
const partialSkills = ref<GapSkill[]>([])
const partialTrying = ref('')
const partialFollowUp = ref<{ path: string; label: string; askPrompt?: string } | null>(null)
const memoryProduct = ref('建材')
type ActionAudit = {
  id: string
  action_type: string
  intent?: string
  message_preview?: string
  needs_confirmation?: boolean
  created_at?: string
}
const actionAudits = ref<ActionAudit[]>([])
type AuditSummary = {
  period_days?: number
  total_actions?: number
  skills?: Array<{ intent: string; label: string; count: number; pct: number }>
}
const auditSummary = ref<AuditSummary>({})

const opsHints = computed(() => {
  const hints = opsSnapshot.value?.hints
  return Array.isArray(hints) ? (hints as string[]) : []
})

const funnelSteps = computed(() => {
  const f = opsSnapshot.value?.funnel
  if (!f) return []
  const steps = [
    { key: 'inq', label: '待处理询盘', count: f.inquiries_pending ?? 0 },
    { key: 'phone', label: '带手机号', count: f.inquiries_with_phone ?? 0 },
    { key: 'prospect', label: '待核实候选', count: f.prospects_discovered ?? 0 },
    { key: 'draft', label: '待开发信', count: f.prospects_draft_ready ?? 0 },
    { key: 'pub', label: '已发布', count: f.publish_success ?? 0 },
  ]
  const max = Math.max(...steps.map((s) => s.count), 1)
  return steps.map((s) => ({ ...s, pct: Math.round((s.count / max) * 100) }))
})

const flywheelArchitecture = computed(() => {
  const raw = String(flywheel.value?.architecture || '')
  return (
    polishCustomerText(raw, tenantBrand.companyName.value)
    || '记忆（研究沉淀）→ 执行（找客·开发信）→ 反馈（效果回流）'
  )
})

const integrationLine = computed(() => {
  const ig = flywheel.value?.integrations as Record<string, Record<string, unknown>> | undefined
  if (!ig) return ''
  const parts: string[] = []
  if (ig.mem0?.configured) parts.push('Mem0')
  if (ig.posthog?.configured) parts.push('PostHog')
  if (ig.n8n?.configured) parts.push('n8n')
  const df = ig.deerflow_sidecar as Record<string, unknown> | undefined
  if (df?.configured) {
    parts.push(df.healthy ? '深度研究引擎' : '深度研究引擎(离线)')
  }
  if (!parts.length) return '外挂：Mem0 / PostHog / n8n 未配置（本地记忆仍可用）'
  return `外挂已配置：${parts.join(' · ')}`
})
type PipelineStep = { step?: string; enqueue_intent?: string; message?: string }
const pipelines = ref<
  Array<{
    id: string
    status: string
    step_count: number
    job_count: number
    finished_at?: string
    steps?: PipelineStep[]
  }>
>([])
let jobPollTimer: ReturnType<typeof setInterval> | null = null

const jobStatusClass = computed(() => {
  const s = jobStatus.value?.status
  if (s === 'success') return 'text-emerald-700'
  if (s === 'failed') return 'text-red-600'
  if (s === 'running') return 'text-blue-600'
  return 'text-amber-700'
})

const jobProgressPct = computed(() => {
  const s = jobStatus.value?.status
  if (s === 'success') return 100
  if (s === 'failed') return 100
  if (s === 'running') return 65
  if (s === 'queued') return 25
  return 10
})

const jobSteps = computed(() => jobStatus.value?.steps || [])

type Insight = { id: string | number; title?: string; intent?: string; quality_score?: string | number }
const recentInsights = computed((): Insight[] => {
  const list = flywheel.value?.recent_insights as Insight[] | undefined
  return list || []
})

const lastPipelineText = computed(() => {
  const lp = flywheel.value?.last_pipeline as Record<string, unknown> | undefined
  if (!lp) return ''
  const jobs = (lp.created_job_ids as string[] | undefined) || []
  return `最近编排 ${String(lp.status)} · 已排队 ${jobs.length} 个执行任务`
})

type CommercialHook = {
  insight_id?: string
  pipeline?: { status?: string }
}
const commercialHook = computed((): CommercialHook | null => {
  const tr = lastTask.value?.tool_result as Record<string, unknown> | undefined
  const hook = tr?.commercial_os_hook as CommercialHook | undefined
  return hook || null
})

const briefInResult = computed(() => {
  const tr = lastTask.value?.tool_result as Record<string, unknown> | undefined
  return Boolean(tr?.research_brief)
})

const samples = [
  '跑一轮市场研究并自动找客',
  '背调 buyer@example.com',
  '分析官网 ICP',
  '做一份形式发票 PI',
  '回复最新询盘',
  '给最新询盘打分',
  '经营快照',
  '同步销售反馈到研究记忆',
]

type ProspectPreview = { id: string | number; title?: string; fit_score?: number; suggested_channel?: string }
const prospectPreview = computed((): ProspectPreview[] => {
  const tr = lastTask.value?.tool_result as Record<string, unknown> | undefined
  const list = tr?.prospects as ProspectPreview[] | undefined
  return (list || []).slice(0, 5)
})

type LetterPreview = { subject?: string; subject_en?: string; body?: string; body_en?: string }
const letterPreview = computed((): LetterPreview[] => {
  const tr = lastTask.value?.tool_result as Record<string, unknown> | undefined
  const list = tr?.letters as LetterPreview[] | undefined
  return (list || []).slice(0, 3)
})

type AgentPreview = {
  skillId: string
  summary: string
  rating?: string
  actions: string[]
  markdown?: string
}

const agentSkillPreview = computed((): AgentPreview | null => {
  const tr = lastTask.value?.tool_result as Record<string, unknown> | undefined
  if (!tr) return null
  if (tr.summary && tr.skill_id) {
    const data = (tr.data || {}) as Record<string, unknown>
    return {
      skillId: String(tr.skill_id),
      summary: String(tr.summary),
      rating: data.overall_rating ? `风险 ${data.overall_rating} (${data.overall_score ?? '—'}/100)` : undefined,
      actions: Array.isArray(tr.next_actions) ? (tr.next_actions as string[]).slice(0, 4) : [],
      markdown: typeof data.markdown === 'string' ? data.markdown : undefined,
    }
  }
  const data = tr.data as Record<string, unknown> | undefined
  if (data?.overall_rating) {
    return {
      skillId: 'osint_background_check',
      summary: `背调完成：${data.overall_rating}（${data.overall_score ?? '—'}/100）`,
      rating: String(data.overall_rating),
      actions: Array.isArray(data.recommendations) ? (data.recommendations as string[]).slice(0, 3) : [],
    }
  }
  if (typeof tr.markdown === 'string') {
    return {
      skillId: 'trade_doc_pi_contract',
      summary: `PI ${tr.pi_no || ''}`.trim(),
      actions: ['请人工核对后发送'],
      markdown: tr.markdown,
    }
  }
  const icp = (tr.icp || data?.icp) as Record<string, unknown> | undefined
  if (icp?.company_name) {
    return {
      skillId: 'factory_onboarding_icp',
      summary: String(tr.summary || `ICP：${icp.company_name}`),
      actions: Array.isArray(tr.next_steps) ? (tr.next_steps as string[]).slice(0, 3) : [],
    }
  }
  return null
})

const flywheelDiligenceLine = computed(() => {
  const tr = lastTask.value?.tool_result as Record<string, unknown> | undefined
  const diligence = tr?.diligence as Record<string, unknown> | undefined
  if (!diligence) return ''
  const samples = diligence.osint_samples as Array<Record<string, unknown>> | undefined
  if (samples?.length && samples[0]?.summary) return String(samples[0].summary)
  const clean = diligence.prospect_clean as Record<string, unknown> | undefined
  if (clean?.summary) return String(clean.summary)
  return ''
})

function downloadPiMarkdown() {
  const md = agentSkillPreview.value?.markdown
  if (!md) return
  downloadMarkdown(`PI_${new Date().toISOString().slice(0, 10)}.md`, md)
}

async function downloadPiPdf() {
  const tr = lastTask.value?.tool_result as Record<string, unknown> | undefined
  const doc = (tr?.data || tr || {}) as Record<string, unknown>
  if (!doc.lines && !doc.markdown) {
    message.warning('无 PI 数据可导出')
    return
  }
  try {
    await exportProformaFile(
      {
        seller: doc.seller || { name: 'Seller', address: '', email: '' },
        buyer: doc.buyer || { name: 'Buyer', company: 'Buyer Co', email: '', code: 'B1' },
        lines: doc.lines || [{ description: 'Product', quantity: 100, unit_price: 0 }],
        currency: doc.currency || 'USD',
        payment_terms: doc.payment_terms || '30% deposit, 70% before shipment',
        delivery_terms: doc.delivery_terms || 'FOB',
      },
      'pdf',
    )
    message.success('PI PDF 已下载')
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : 'PDF 导出失败')
  }
}

function auditTypeLabel(t: string) {
  const map: Record<string, string> = {
    chat: '对话',
    confirm_send: '确认发送',
    flywheel_brief: '研究简报',
    flywheel_feedback: '反馈同步',
    flywheel_webhook: '自动化回调',
    deerflow_job: BRAND.deepResearchJob,
  }
  return map[t] || t
}

function authHeaders(): Record<string, string> {
  const tk = getAuthToken()
  return tk ? { Authorization: `Bearer ${tk}` } : {}
}

/** 与 admin axios 一致：校验 body.code，成功时返回 data 或裸对象 */
async function parseApiBody<T = Record<string, unknown>>(res: Response): Promise<T> {
  const body = (await res.json()) as Record<string, unknown>
  if (typeof body.code === 'number' && body.code !== 0) {
    const msg = typeof body.message === 'string' ? body.message : `API 错误 ${body.code}`
    throw new Error(msg)
  }
  if (!res.ok && typeof body.code !== 'number') {
    throw new Error(`HTTP ${res.status}`)
  }
  return (body.data ?? body) as T
}

function pillarLabel(key: (typeof pillarKeys)[number]) {
  const pillars = flywheel.value?.pillars as Record<string, Record<string, unknown>> | undefined
  return String(pillars?.[key]?.label || key)
}

function pillarHint(key: (typeof pillarKeys)[number]) {
  const pillars = flywheel.value?.pillars as Record<string, Record<string, unknown>> | undefined
  return polishCustomerText(String(pillars?.[key]?.hint || ''), tenantBrand.companyName.value)
}

function pillarStatusText(key: (typeof pillarKeys)[number]) {
  const pillars = flywheel.value?.pillars as Record<string, Record<string, unknown>> | undefined
  const p = pillars?.[key]
  if (!p) return '—'
  if (key === 'memory') return `${p.count ?? 0} 条洞察`
  if (key === 'execution') {
    const auto = p.auto_pipeline ? '自动编排开' : '自动编排关'
    return `${p.count ?? 0} 次编排 · ${auto}`
  }
  if (key === 'feedback') {
    const m = p.metrics as Record<string, unknown> | undefined
    if (!m) return '待同步'
    return `手机号线索 ${m.inquiries_with_phone ?? 0} · 已外联 ${m.prospects_outreach_sent ?? 0}`
  }
  return String(p.status || '')
}

function pillarClass(key: (typeof pillarKeys)[number]) {
  const pillars = flywheel.value?.pillars as Record<string, Record<string, unknown>> | undefined
  const st = pillars?.[key]?.status
  if (st === 'active') return 'pillar-active'
  if (st === 'pending' || st === 'empty') return 'pillar-warn'
  return ''
}

function pipelineStepLabel(p: { step_count: number; steps?: PipelineStep[] }) {
  const steps = p.steps || []
  if (!steps.length) return `${p.step_count} 步`
  const names = steps
    .map((s) => s.enqueue_intent || s.step || '')
    .filter(Boolean)
    .slice(0, 3)
  return names.length ? names.join(' → ') : `${p.step_count} 步`
}

function formatTime(iso: string) {
  try {
    return new Date(iso).toLocaleString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  } catch {
    return iso.slice(0, 16)
  }
}

function stopJobPoll() {
  if (jobPollTimer) {
    clearInterval(jobPollTimer)
    jobPollTimer = null
  }
}

function startJobPoll() {
  stopJobPoll()
  jobPollTimer = setInterval(() => {
    void refreshJob()
  }, 5000)
}

async function refreshJob() {
  const id = jobStatus.value?.id
  if (!id) return
  if (jobStatus.value?.status === 'queued') {
    try {
      await fetch('/api/v1/ubrain/jobs/run-pending?limit=3', {
        method: 'POST',
        headers: authHeaders(),
      })
    } catch {
      /* worker kick best-effort */
    }
  }
  const res = await fetch(`/api/v1/ubrain/jobs/${id}`, { headers: authHeaders() })
  const data = await parseApiBody<{
    id: string
    status: string
    intent?: string
    error_message?: string
    log_text?: string
    log_tail?: string
    steps?: Array<{ index: number; title: string; status: string }>
    result?: Record<string, unknown>
  }>(res)
  const logTail =
    data.log_tail || (data.log_text || '').trim().split('\n').slice(-6).join('\n')
  jobStatus.value = {
    id: data.id,
    status: data.status,
    intent: data.intent,
    error_message: data.error_message,
    log_tail: logTail || undefined,
    result: data.result,
    steps: data.steps,
  }
  const terminal = data.status === 'success' || data.status === 'failed'
  if (terminal) {
    stopJobPoll()
    if (data.status === 'success' && data.result && lastTask.value) {
      lastTask.value.tool_result = { ...lastTask.value.tool_result, ...data.result }
      const r = data.result as Record<string, unknown>
      if (data.intent === 'geo_content_matrix' && (r.cms_draft_count as number) > 0) {
        messages.value.push({
          role: 'assistant',
          text: `GEO 内容矩阵已完成，已写入 ${r.cms_draft_count} 条草稿。请到「统一发布台」人审后，按平台变体创建发布任务。`,
        })
        void scrollBottom()
      }
      if (
        r.needs_confirmation ||
        r.status === 'awaiting_confirmation' ||
        r.human_review_required
      ) {
        pendingConfirm.value = {
          summary: '矩阵发布计划已就绪，请确认后执行真发',
          message: '确认矩阵发布',
          intent: 'matrix_publish',
        }
      }
    }
    await Promise.all([loadFlywheel(), loadPipelines(), loadActionAudits(), loadRecentJobs()])
  }
}

async function loadRecentJobs() {
  try {
    const res = await fetch('/api/v1/ubrain/jobs?page=1&page_size=8', { headers: authHeaders() })
    const data = await parseApiBody<{ items?: typeof recentJobs.value }>(res)
    recentJobs.value = (data.items || []) as typeof recentJobs.value
  } catch {
    recentJobs.value = []
  }
}

function selectJob(id: string) {
  jobStatus.value = { id, status: 'queued' }
  startJobPoll()
  void refreshJob()
}

const messages = ref<Msg[]>([
  {
    role: 'assistant',
    text: tenantBrand.welcomeMessage.value,
  },
])

watch(
  () => tenantBrand.welcomeMessage.value,
  (text) => {
    if (messages.value[0]?.role === 'assistant') {
      messages.value[0].text = text
    }
  },
)

async function ask(text: string) {
  input.value = text
  await send()
}

async function send() {
  const text = input.value.trim()
  if (!text || loading.value) return
  messages.value.push({ role: 'user', text })
  input.value = ''
  loading.value = true
  await scrollBottom()
  try {
    const res = await fetch('/api/v1/ubrain/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify(ubrainCtx.buildBody(text, messages.value)),
    })
    const data = await parseApiBody<UBrainReply>(res)
    ubrainCtx.applyReply(data)
    lastTask.value = data
    applyToolResult(data)
    messages.value.push({
      role: 'assistant',
      text: data.reply || '暂无回复',
      disclaimer: data.disclaimer,
    })
    updateMemoryHint(data)
    if (data.needs_confirmation) {
      pendingConfirm.value = {
        summary: data.reply || '对外发布或发送',
        message: text,
        intent: data.intent,
      }
    }
    if (data.intent === 'sync_feedback') {
      void loadFlywheel()
    }
    void loadActionAudits()
  } catch {
    messages.value.push({ role: 'assistant', text: '请求失败，请检查网络与登录。' })
  } finally {
    loading.value = false
    await scrollBottom()
  }
}

function applyToolResult(data: UBrainReply) {
  const tr = data.tool_result as Record<string, unknown> | undefined
  if (tr?.job_id) {
    jobStatus.value = {
      id: String(tr.job_id),
      status: String(tr.job_status || 'queued'),
      intent: data.intent,
    }
    if (tr.job_status === 'queued' || tr.job_status === 'running') {
      startJobPoll()
      void refreshJob()
    }
    void loadRecentJobs()
  } else {
    jobStatus.value = null
  }
  const needsMatrixConfirm =
    data.intent === 'matrix_publish' &&
    (tr?.needs_confirmation || tr?.status === 'awaiting_confirmation' || tr?.human_review_required)
  if (needsMatrixConfirm || data.needs_confirmation) {
    pendingConfirm.value = {
      summary: data.reply || '矩阵发布须人工确认后再真发',
      message: '确认矩阵发布',
      intent: data.intent === 'matrix_publish' ? 'matrix_publish' : data.intent,
    }
  }
  if (data.intent === 'weekly_lead_report' && tr?.available) {
    weekly.value = tr
  }
  const brief = tr?.research_brief as Record<string, unknown> | undefined
  if (brief) {
    briefSummary.value = String(brief.executive_summary || tr?.executive_summary || '')
    briefActions.value = (brief.accio_actions as BriefAction[]) || (tr?.accio_actions as BriefAction[]) || []
  }
}

function updateMemoryHint(data: UBrainReply) {
  const mem = data.memory_snapshot
  if (mem?.product_category) {
    const co = String(mem.company_name || tenantBrand.companyName.value || '').trim()
    const regs = (mem.preferred_regions as string[] | undefined)?.join('、') || ''
    memoryHint.value = `${co || '您的公司'} · ${mem.product_category}${regs ? ` · 市场 ${regs}` : ''}`
  }
}

async function generateBrief(templateId?: string) {
  const q = briefQuery.value.trim()
  if (!q || briefLoading.value) return
  briefLoading.value = true
  try {
    const res = await fetch('/api/v1/ubrain/commercial-os/research-brief', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify({
        message: q,
        ...(templateId ? { template_id: templateId } : {}),
      }),
    })
    const data = await parseApiBody<{
      executive_summary?: string
      accio_actions?: BriefAction[]
    }>(res)
    briefSummary.value = String(data.executive_summary || '')
    briefActions.value = data.accio_actions || []
    messages.value.push({
      role: 'assistant',
      text: `【${BRAND.researchBrief}】${briefSummary.value}\n可执行动作 ${briefActions.value.length} 个（点击下方按钮或跑一轮卖货飞轮）。`,
    })
    void loadActionAudits()
  } catch {
    messages.value.push({ role: 'assistant', text: '简报生成失败，请检查登录与租户绑定。' })
  } finally {
    briefLoading.value = false
    await scrollBottom()
  }
}

function generateBriefFromTemplate(t: BriefTemplate) {
  briefQuery.value = t.message_default || t.title
  void generateBrief(t.id)
}

async function loadBriefTemplates() {
  try {
    const res = await fetch('/api/v1/ubrain/commercial-os/research-brief/templates', {
      headers: authHeaders(),
    })
    briefTemplates.value = (await parseApiBody<BriefTemplate[]>(res)) || []
  } catch {
    briefTemplates.value = []
  }
}

function runBriefAction(a: BriefAction) {
  const msg = a.params?.message || `执行 ${a.skill_id}`
  void ask(msg)
}

async function runFullFlywheel() {
  await ask('跑一轮卖货飞轮（研究→找客）')
}

async function runGeoContentMatrix() {
  await ask(
    '写 GEO 内容矩阵 建材出口，关键词 rock wool, fire rating, B2B，平台 LinkedIn,百家号,抖音,小红书',
  )
}

async function openPublishWithJob() {
  const jobId = jobStatus.value?.id || (lastTask.value?.tool_result as Record<string, unknown> | undefined)?.job_id
  await router.push({
    path: '/client/publish',
    query: jobId ? { job_id: String(jobId) } : {},
  })
}

async function syncFeedback() {
  try {
    const res = await fetch('/api/v1/ubrain/commercial-os/feedback/sync?period_days=7', {
      method: 'POST',
      headers: authHeaders(),
    })
    const data = await parseApiBody<{ assistant_prompt?: string; deerflow_next_prompt?: string }>(res)
    messages.value.push({
      role: 'assistant',
      text:
        data.assistant_prompt ||
        data.deerflow_next_prompt ||
        '反馈已同步到研究记忆。',
    })
    void loadFlywheel()
    void loadActionAudits()
  } catch {
    messages.value.push({ role: 'assistant', text: '反馈同步失败。' })
  }
  await scrollBottom()
}

async function confirmPending() {
  const p = pendingConfirm.value
  pendingConfirm.value = null
  if (p?.intent === 'outreach_letter_pack') {
    const tr = lastTask.value?.tool_result as Record<string, unknown> | undefined
    const prospects = (tr?.prospects as Array<{ id?: string }>) || []
    const pid = prospects[0]?.id
    if (pid) {
      const cres = await fetch('/api/v1/ubrain/prospects/confirm-send', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeaders() },
        body: JSON.stringify({ prospect_id: pid, channel: 'email' }),
      })
      await parseApiBody(cres)
    }
    messages.value.push({
      role: 'assistant',
      text: '已记录您的确认。请在本机邮箱/WhatsApp 完成实际发送；系统不会自动外发。',
    })
    void loadActionAudits()
    return
  }
  if (p?.intent === 'matrix_publish') {
    loading.value = true
    try {
      const tr = lastTask.value?.tool_result as Record<string, unknown> | undefined
      const res = await fetch('/api/v1/ubrain/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeaders() },
        body: JSON.stringify({
          message: p.message || '确认矩阵发布',
          context: {
            human_confirmed: true,
            media_task_id: tr?.media_task_id || tr?.ticket_id,
            platforms: tr?.platforms,
          },
        }),
      })
      const data = await parseApiBody<UBrainReply>(res)
      lastTask.value = data
      applyToolResult(data)
      messages.value.push({ role: 'assistant', text: data.reply || '矩阵发布任务已提交。' })
      void loadRecentJobs()
    } catch {
      messages.value.push({ role: 'assistant', text: '矩阵发布确认失败，请重试。' })
    } finally {
      loading.value = false
      await scrollBottom()
    }
    return
  }
  messages.value.push({
    role: 'assistant',
    text: '已记录您的确认。',
  })
  void loadActionAudits()
}

function formatResult(obj: Record<string, unknown>) {
  try {
    return JSON.stringify(obj, null, 2)
  } catch {
    return String(obj)
  }
}

async function scrollBottom() {
  await nextTick()
  listEl.value?.scrollTo({ top: listEl.value.scrollHeight, behavior: 'smooth' })
}

async function loadOpsSnapshot() {
  try {
    const res = await fetch('/api/v1/ubrain/ops-snapshot', { headers: authHeaders() })
    opsSnapshot.value = await parseApiBody(res)
  } catch {
    /* 未登录或业务错误 */
  }
}

async function loadActionAudits() {
  try {
    const res = await fetch('/api/v1/ubrain/action-audit?limit=8', { headers: authHeaders() })
    const data = await parseApiBody<{ items?: ActionAudit[] }>(res)
    actionAudits.value = data.items || []
  } catch {
    actionAudits.value = []
  }
}

async function loadAuditSummary() {
  try {
    const res = await fetch('/api/v1/ubrain/action-audit/summary?days=7', { headers: authHeaders() })
    auditSummary.value = await parseApiBody<AuditSummary>(res)
  } catch {
    auditSummary.value = {}
  }
}

async function markProspectContacted(prospectId: string) {
  try {
    const res = await fetch(`/api/v1/ubrain/prospects/${encodeURIComponent(prospectId)}/mark-contacted`, {
      method: 'POST',
      headers: { ...authHeaders(), 'Content-Type': 'application/json' },
      body: JSON.stringify({ note: '副驾标记已联系' }),
    })
    await parseApiBody(res)
    messages.value.push({
      role: 'assistant',
      text: `已标记候选 ${prospectId.slice(0, 8)}… 为「已联系待回复」。`,
    })
    await refreshFlywheelView()
    await scrollBottom()
  } catch (e) {
    messages.value.push({
      role: 'assistant',
      text: e instanceof Error ? e.message : '标记失败',
    })
    await scrollBottom()
  }
}

async function exportProspectsCsv() {
  try {
    const res = await fetch('/api/v1/ubrain/prospects/export', { headers: authHeaders() })
    const ct = (res.headers.get('content-type') || '').toLowerCase()
    if (!res.ok || ct.includes('application/json')) {
      await parseApiBody(res)
      throw new Error('导出被拒绝或暂无候选数据')
    }
    const blob = await res.blob()
    const href = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = href
    link.download = 'prospects_export.csv'
    link.click()
    URL.revokeObjectURL(href)
  } catch (e) {
    const text =
      e instanceof Error ? e.message : '导出失败：请确认已登录且有找客记录。'
    messages.value.push({ role: 'assistant', text })
    await scrollBottom()
  }
}

async function exportInquiriesCsv() {
  try {
    const res = await fetch('/api/v1/inquiries/export', { headers: authHeaders() })
    const ct = (res.headers.get('content-type') || '').toLowerCase()
    if (!res.ok || ct.includes('application/json')) {
      await parseApiBody(res)
      throw new Error('导出被拒绝或暂无数据')
    }
    const blob = await res.blob()
    const href = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = href
    link.download = 'inquiries_export.csv'
    link.click()
    URL.revokeObjectURL(href)
  } catch (e) {
    const text =
      e instanceof Error ? e.message : '导出失败：请确认已登录且有询盘查看权限。'
    messages.value.push({
      role: 'assistant',
      text,
    })
    await scrollBottom()
  }
}

async function loadGapSkills() {
  try {
    const [gapsRes, partialRes] = await Promise.all([
      fetch('/api/v1/ubrain/commercial-os/gaps', { headers: authHeaders() }),
      fetch('/api/v1/ubrain/commercial-os/partial-skills', { headers: authHeaders() }),
    ])
    const gapsData = await parseApiBody<{ items?: GapSkill[] }>(gapsRes)
    gapSkills.value = (gapsData.items || []).slice(0, 8)
    const partialData = await parseApiBody<{ items?: GapSkill[] }>(partialRes)
    partialSkills.value = partialData.items || []
  } catch {
    gapSkills.value = []
    partialSkills.value = []
  }
}

async function explainGap(g: GapSkill) {
  let detail = g.gap || g.note || '该能力在 P2 路线图，当前仅占位。'
  try {
    const res = await fetch(`/api/v1/ubrain/commercial-os/gap/${encodeURIComponent(g.id)}`, {
      headers: authHeaders(),
    })
    const data = await parseApiBody<Record<string, unknown>>(res)
    detail = String(data.message || data.note || data.gap || detail)
  } catch (e) {
    if (e instanceof Error) detail = e.message
  }
  messages.value.push({
    role: 'assistant',
    text: `【${gapSkillLabel(g)}】\n${polishCustomerText(detail, tenantBrand.companyName.value)}`,
    disclaimer: '路线图说明，非生产外发。',
  })
  await scrollBottom()
}

function formatMvpTrialText(skillId: string, data: Record<string, unknown>): string {
  const lines: string[] = [`【${skillId} · MVP 试用结果】`]
  if (data.mode) lines.push(`模式：${String(data.mode)}`)
  if (Array.isArray(data.platforms)) {
    lines.push(`计划平台：${(data.platforms as string[]).join('、')}`)
  }
  if (Array.isArray(data.matches)) {
    for (const m of data.matches as Array<{ title?: string; confidence?: number }>) {
      lines.push(`· ${m.title || '候选'}${m.confidence != null ? ` (${Math.round(Number(m.confidence) * 100)}%)` : ''}`)
    }
  }
  if (Array.isArray(data.variants)) {
    for (const v of data.variants as Array<{ channel?: string; headline?: string }>) {
      lines.push(`· [${v.channel || 'ad'}] ${v.headline || ''}`)
    }
  }
  if (Array.isArray(data.suppliers)) {
    for (const s of data.suppliers as Array<{ name?: string; unit_price_usd?: number }>) {
      lines.push(`· ${s.name || '供应商'} $${s.unit_price_usd ?? '—'}/u`)
    }
  }
  if (data.site_blueprint) {
    const bp = data.site_blueprint as Record<string, unknown>
    lines.push(`建站蓝图：${bp.template || 'b2b'} · ${bp.product_focus || memoryProduct.value}`)
  }
  if (Array.isArray(data.checklist)) {
    lines.push('清单：' + (data.checklist as string[]).join(' → '))
  }
  if (data.note) lines.push(String(data.note))
  if (data.use_instead) lines.push(`下一步：打开 ${String(data.use_instead)}`)
  if (data.next_step) lines.push(String(data.next_step))
  return lines.join('\n')
}

async function loadMemoryProduct() {
  try {
    const res = await fetch('/api/v1/ubrain/memory', { headers: authHeaders() })
    const mem = await parseApiBody<{ product_category?: string }>(res)
    if (mem?.product_category) memoryProduct.value = mem.product_category
  } catch {
    /* 未登录 */
  }
}

async function goPartialFollowUp() {
  const fu = partialFollowUp.value
  if (!fu) return
  if (fu.askPrompt) {
    partialFollowUp.value = null
    await ask(fu.askPrompt)
    return
  }
  partialFollowUp.value = null
  await router.push(fu.path)
}

function resolvePartialFollowUp(
  skillId: string,
  data: Record<string, unknown>,
): { path: string; label: string; askPrompt?: string } | null {
  const raw = String(data.use_instead || '').trim()
  if (skillId === 'image_sourcing') {
    const kw = memoryProduct.value || '建材'
    return { path: '/client/copilot', label: '继续找买家候选', askPrompt: `找买家 ${kw} 出口，标注待核实候选` }
  }
  if (skillId === 'paid_ads_creative') {
    return {
      path: '/client/copilot',
      label: '生成开发信草稿',
      askPrompt: `写开发信草稿 ${memoryProduct.value || '建材'} 出口，按区域模板`,
    }
  }
  if (skillId === 'supplier_rfq') {
    return {
      path: '/client/copilot',
      label: '生成谈单草稿',
      askPrompt: `根据 RFQ 比价生成谈单话术 ${memoryProduct.value || '建材'}，含成本底线占位`,
    }
  }
  const labels: Record<string, string> = {
    matrix_publish: '打开统一发布台',
    auto_shopify: '打开 AI 建站',
    team_rbac: '团队权限配置',
    supplier_rfq: '继续谈单草稿',
  }
  if (raw.startsWith('/')) {
    const path = raw.replace(/^\/tenants\/site-editor/, '/client/site-editor')
    return { path, label: labels[skillId] || '继续下一步' }
  }
  const defaults: Record<string, { path: string; label: string }> = {
    matrix_publish: { path: '/client/publish', label: labels.matrix_publish },
    auto_shopify: { path: '/client/site-editor', label: labels.auto_shopify },
    team_rbac: { path: '/admin/users', label: labels.team_rbac },
  }
  return defaults[skillId] || null
}

async function tryPartialSkill(g: GapSkill) {
  partialTrying.value = g.id
  partialFollowUp.value = null
  try {
    const params = new URLSearchParams({
      product_hint: memoryProduct.value || '建材',
      locale: 'zh',
    })
    if (g.id === 'image_sourcing') {
      params.set('keywords', memoryProduct.value || '建材')
    }
    if (g.id === 'paid_ads_creative') {
      params.set('budget_usd', '500')
    }
    const res = await fetch(
      `/api/v1/ubrain/commercial-os/gap/${encodeURIComponent(g.id)}?${params.toString()}`,
      { headers: authHeaders() },
    )
    const data = await parseApiBody<Record<string, unknown>>(res)
    messages.value.push({
      role: 'assistant',
      text: polishCustomerText(formatMvpTrialText(g.id, data), tenantBrand.companyName.value),
      disclaimer: 'MVP 试用结果，非自动外发。',
    })
    partialFollowUp.value = resolvePartialFollowUp(g.id, data)
  } catch (e) {
    messages.value.push({
      role: 'assistant',
      text: e instanceof Error ? e.message : 'MVP 试用失败',
    })
  } finally {
    partialTrying.value = ''
    await scrollBottom()
  }
}

async function refreshFlywheelView() {
  await Promise.all([loadFlywheel(), loadPipelines(), loadOpsSnapshot()])
}

async function loadFlywheel() {
  const res = await fetch('/api/v1/ubrain/commercial-os/status', { headers: authHeaders() })
  try {
    flywheel.value = await parseApiBody(res)
  } catch {
    /* 未登录或业务错误时保持空状态 */
  }
}

async function loadPipelines() {
  const res = await fetch('/api/v1/ubrain/commercial-os/pipelines?limit=5', {
    headers: authHeaders(),
  })
  try {
    const data = await parseApiBody<{ items?: typeof pipelines.value }>(res)
    pipelines.value = (data.items || []) as typeof pipelines.value
  } catch {
    pipelines.value = []
  }
}

onMounted(() => {
  void refreshFlywheelView()
  void loadGapSkills()
  void loadMemoryProduct()
  void loadActionAudits()
  void loadAuditSummary()
  void loadRecentJobs()
  void loadBriefTemplates()
  void refreshAiConnect()
  const q = typeof route.query.q === 'string' ? route.query.q.trim() : ''
  if (q) {
    void ask(q)
  }
})

onUnmounted(() => {
  stopJobPoll()
})
</script>

<style scoped>
.copilot-page {
  max-width: 720px;
  margin: 0 auto;
}
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
.chat-form button:focus-visible,
.chip:focus-visible,
.link-btn:focus-visible,
.btn-flywheel:focus-visible {
  outline: 2px solid var(--uj-brand, #4a9b8c);
  outline-offset: 2px;
}
.copilot-header {
  margin-bottom: 16px;
}
.copilot-ai-connect {
  margin-bottom: 16px;
}
.flywheel-primary {
  border-color: #818cf8;
  background: linear-gradient(180deg, #eef2ff 0%, #fff 40%);
}
.pillar-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  margin-top: 10px;
}
@media (max-width: 640px) {
  .pillar-grid {
    grid-template-columns: 1fr;
  }
}
.pillar {
  padding: 10px;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  background: #fff;
}
.pillar-active {
  border-color: #34d399;
}
.pillar-warn {
  border-color: #fcd34d;
}
.pillar-label {
  display: block;
  font-size: 12px;
  font-weight: 700;
  color: #312e81;
}
.pillar-status {
  display: block;
  font-size: 11px;
  color: #0f172a;
  margin-top: 4px;
}
.pillar-hint {
  display: block;
  font-size: 10px;
  color: #64748b;
  margin-top: 4px;
  line-height: 1.3;
}
.flywheel-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  margin-top: 10px;
}
.btn-flywheel {
  background: #4f46e5;
  color: #fff;
  border: none;
  border-radius: 8px;
  padding: 8px 14px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
}
.insight-list,
.pipeline-list {
  margin-top: 10px;
  padding-left: 0;
  list-style: none;
  font-size: 12px;
}
.pipeline-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 0;
  border-top: 1px solid #e2e8f0;
}
.pipeline-status {
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  padding: 2px 6px;
  border-radius: 4px;
  background: #f1f5f9;
  color: #475569;
}
.pipeline-status.st-success {
  background: #d1fae5;
  color: #065f46;
}
.pipeline-status.st-failed {
  background: #fee2e2;
  color: #991b1b;
}
.pipeline-status.st-running,
.pipeline-status.st-partial {
  background: #dbeafe;
  color: #1e40af;
}
.brief-card {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 14px 16px;
  margin-bottom: 16px;
}
.brief-form {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}
.brief-form input {
  flex: 1;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  padding: 8px 10px;
  font-size: 13px;
}
.brief-form button {
  background: #0f766e;
  color: #fff;
  border: none;
  border-radius: 8px;
  padding: 0 12px;
  font-size: 13px;
  cursor: pointer;
}
.action-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}
.chip.accent {
  border-color: #4f46e5;
  color: #312e81;
  background: #eef2ff;
}
.chip.gap {
  border-color: #fcd34d;
  color: #92400e;
  background: #fffbeb;
}
.chip.partial {
  border-color: #93c5fd;
  color: #1e40af;
  background: #eff6ff;
}
.chip.partial.outline {
  background: #fff;
}
.partial-skill-list {
  list-style: none;
  margin: 8px 0 0;
  padding: 0;
}
.partial-skill-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 6px 0;
  border-bottom: 1px solid #e2e8f0;
}
.partial-skill-row:last-child {
  border-bottom: none;
}
.partial-skill-name {
  font-size: 13px;
  color: #334155;
}
.partial-skill-actions {
  display: flex;
  gap: 6px;
}
.partial-follow-up {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px dashed #e2e8f0;
}
.gap-card {
  margin-bottom: 16px;
  padding: 12px;
  border-radius: 12px;
  border: 1px dashed #fcd34d;
  background: #fffbeb;
}
.audit-card {
  margin-bottom: 16px;
  padding: 12px;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  background: #f8fafc;
}
.audit-list {
  list-style: none;
  padding: 0;
  margin: 8px 0 0;
}
.job-list {
  list-style: none;
  padding: 0;
  margin: 8px 0 0;
}
.job-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 0;
  border-bottom: 1px solid #f1f5f9;
}
.job-progress-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
}
.job-progress-track {
  flex: 1;
  height: 6px;
  background: #e2e8f0;
  border-radius: 999px;
  overflow: hidden;
}
.job-progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--uj-brand, #4a9b8c), #10b981);
  transition: width 0.4s ease;
}
.job-steps {
  list-style: none;
  padding: 0;
  margin: 0;
  font-size: 12px;
}
.job-step {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 4px 0;
  color: #64748b;
}
.job-step--success,
.job-step--done {
  color: #059669;
}
.job-step--failed {
  color: #dc2626;
}
.job-step--running {
  color: var(--uj-brand, #4a9b8c);
}
.job-step-idx {
  flex-shrink: 0;
  width: 18px;
  height: 18px;
  border-radius: 999px;
  background: #e2e8f0;
  text-align: center;
  line-height: 18px;
  font-size: 10px;
}
.audit-list li {
  padding: 6px 0;
  border-bottom: 1px solid #e2e8f0;
}
.audit-type {
  font-size: 11px;
  font-weight: 700;
  color: #475569;
  margin-right: 6px;
}
.accio-cards {
  margin-bottom: 16px;
}
.accio-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  margin-top: 8px;
}
@media (max-width: 640px) {
  .accio-grid {
    grid-template-columns: 1fr;
  }
}
.accio-card {
  text-align: left;
  padding: 12px;
  border-radius: 12px;
  border: 1px solid #c7d2fe;
  background: #fff;
  cursor: pointer;
}
.accio-card:hover {
  border-color: #4f46e5;
}
.accio-title {
  display: block;
  font-size: 13px;
  font-weight: 700;
  color: #312e81;
}
.accio-desc {
  display: block;
  font-size: 11px;
  color: #64748b;
  margin-top: 4px;
}
.prospect-list,
.letter-list {
  margin-top: 8px;
  padding-left: 18px;
  font-size: 12px;
  color: #334155;
}
.funnel-wrap { margin-top: 8px; }
.funnel-row {
  display: grid;
  grid-template-columns: 72px 1fr 28px;
  gap: 8px;
  align-items: center;
  margin-bottom: 4px;
}
.funnel-label { font-size: 11px; color: #64748b; }
.funnel-track {
  height: 6px;
  background: #e2e8f0;
  border-radius: 999px;
  overflow: hidden;
}
.funnel-fill {
  height: 100%;
  background: linear-gradient(90deg, #6366f1, #818cf8);
  border-radius: 999px;
}
.funnel-count { font-size: 11px; color: #334155; text-align: right; }
.skill-bar-row {
  display: grid;
  grid-template-columns: 72px 1fr 28px;
  gap: 8px;
  align-items: center;
  margin: 4px 0;
}
.skill-bar-label { font-size: 11px; color: #64748b; }
.skill-bar-track {
  height: 8px;
  background: #e2e8f0;
  border-radius: 4px;
  overflow: hidden;
}
.skill-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--uj-brand, #4a9b8c), #60a5fa);
  border-radius: 4px;
}
.skill-bar-count { font-size: 11px; color: #334155; text-align: right; }
.agent-skill-card {
  border: 1px solid #e0e7ff;
  background: #f5f7ff;
  border-radius: 8px;
  padding: 10px 12px;
}

.flywheel-card,
.weekly-card,
.task-card,
.confirm-card {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 14px 16px;
  margin-bottom: 16px;
}
.weekly-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-top: 10px;
}
.stat-label {
  display: block;
  font-size: 11px;
  color: #64748b;
}
.stat-value {
  font-size: 22px;
  font-weight: 700;
  color: #0f172a;
}
.stat-value.accent {
  color: #059669;
}
.link-btn {
  font-size: 12px;
  color: var(--uj-brand, #4a9b8c);
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
}
.chat-card {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  overflow: hidden;
  min-height: 320px;
  display: flex;
  flex-direction: column;
}
.chat-list {
  flex: 1;
  padding: 16px;
  overflow-y: auto;
  max-height: 380px;
}
.chat-row {
  margin-bottom: 12px;
  padding: 10px 12px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.5;
}
.chat-row.user {
  background: #eff6ff;
  margin-left: 24px;
}
.chat-row.assistant {
  background: #f8fafc;
  margin-right: 24px;
}
.disclaimer {
  margin-top: 6px;
  font-size: 11px;
  color: #94a3b8;
}
.chat-form {
  display: flex;
  gap: 8px;
  padding: 12px;
  border-top: 1px solid #e2e8f0;
}
.chat-form textarea {
  flex: 1;
  border: 1px solid #cbd5e1;
  border-radius: 10px;
  padding: 8px 10px;
  resize: none;
  font-size: 14px;
}
.chat-form button {
  background: var(--uj-brand, #4a9b8c);
  color: #fff;
  border: none;
  border-radius: 10px;
  padding: 0 16px;
  font-weight: 600;
  cursor: pointer;
}
.chat-form button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.quick-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}
.chip {
  font-size: 12px;
  padding: 6px 12px;
  border-radius: 999px;
  border: 1px solid #cbd5e1;
  background: #fff;
  color: #334155;
  cursor: pointer;
}
.chip:hover {
  border-color: var(--uj-brand, #4a9b8c);
  color: var(--uj-brand, #4a9b8c);
}
.task-json {
  margin-top: 8px;
  font-size: 11px;
  background: #f1f5f9;
  padding: 10px;
  border-radius: 8px;
  overflow-x: auto;
  max-height: 200px;
}
.confirm-actions {
  display: flex;
  gap: 8px;
  margin-top: 10px;
}
.btn-primary {
  background: #d97706;
  color: #fff;
  border: none;
  border-radius: 8px;
  padding: 6px 14px;
  font-size: 13px;
  cursor: pointer;
}
.btn-ghost {
  background: #fff;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  padding: 6px 14px;
  font-size: 13px;
  cursor: pointer;
}
</style>
