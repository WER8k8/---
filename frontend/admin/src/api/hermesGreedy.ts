/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
import { apiGet, apiPost } from '@/utils/api'

export type GreedyPersonality = {
  mood: string
  line: string
  codename?: string
  vs_last?: string
  delta_settlement_pct?: number | null
  traits?: string[]
}

export type GreedyCumulative = {
  week_key?: string
  month_key?: string
  year_key?: string
  week_revenue_minor?: number
  month_revenue_minor?: number
  year_revenue_minor?: number
  lifetime_revenue_minor?: number
  personality?: GreedyPersonality
  display?: {
    week_cny?: number
    month_cny?: number
    year_cny?: number
    lifetime_cny?: number
    last_settlement_cny?: number
    prev_settlement_cny?: number
  }
  global_revenue_policy?: { scope?: string; markets_note?: string }
  personality_mood?: string
  redemption_streak?: number
  settlements_count?: number
}

export type GreedyContestRow = {
  role_id: string
  name?: string
  emoji?: string
  total_score?: number
  score_30d?: number
  score_arena?: number
  score_year?: number
  experience_points?: number
  deployments?: number
  revenue_attributed_cny_minor?: number
  contest_tier?: string
  protected?: boolean
  never_offline?: boolean
  lessons_count?: number
}

export type GreedyLeaderboard = {
  season?: string | { id?: string; label?: string; name?: string }
  title?: string
  tagline?: string
  leaderboard?: GreedyContestRow[]
  protected_count?: number
  champion_count?: number
  current_arena?: Record<string, unknown>
  endurance?: Record<string, unknown>
  mojin?: Record<string, unknown>
  recent_rounds?: GreedyContestRound[]
}

export type GreedyContestRound = {
  loop_id?: string
  trigger?: string
  participants?: string[]
  skus?: string[]
  kpi_pct?: number | null
  settled_at?: string
}

export type GreedyProjectBoardItem = {
  sku: string
  label: string
  revenue_cny_minor: number
  rounds: number
  participant_count: number
  completion_pct?: number | null
  completion_source?: 'publish_review' | 'loop_kpi' | null
  primary_roles?: string[]
}

export type GreedyProjectEmployee = {
  role_id: string
  name?: string
  emoji?: string
  revenue_cny_minor: number
  deployments: number
  project_count: number
  project_skus?: string[]
  contest_tier?: string
  lessons?: string[]
  latest_lesson?: string | null
}

export type GreedyLessonsDigest = {
  mojin_lessons: string[]
  by_employee: Array<{
    role_id?: string
    name?: string
    emoji?: string
    lessons?: string[]
    latest_lesson?: string
  }>
  extra_voices?: Array<{
    role_id?: string
    name?: string
    emoji?: string
    lessons?: string[]
    latest_lesson?: string
  }>
  highlights: string[]
  loops_completed?: number
}

export type GreedyEvolutionDirection = {
  priority: 'P0' | 'P1' | 'P2' | string
  theme: string
  action: string
  signals?: string[]
}

export type GreedyEvolutionPlan = {
  headline: string
  directions: GreedyEvolutionDirection[]
  next_loop_hints: string[]
  data_source: string
}

export type GreedyProjectBoard = {
  projects: GreedyProjectBoardItem[]
  top_employees: GreedyProjectEmployee[]
  lessons_digest?: GreedyLessonsDigest
  evolution?: GreedyEvolutionPlan
  summary: {
    total_revenue_cny_minor: number
    avg_completion_pct?: number | null
    active_project_count: number
    rounds_tracked: number
  }
  data_source: string
}

export type GreedyPublishItem = {
  sku?: string
  locale?: string
  publish_channels?: string[]
  cta?: string
  queued_at?: string
  queue_index?: number
  body?: string
  body_preview?: string
  title?: string
  label?: string
  primary_roles?: string[]
}

export type GreedyPublishReviewHistory = {
  action?: string
  sku?: string
  locale?: string
  reason?: string
  reviewer?: string
  reviewed_at?: string
  publish_plan?: Record<string, unknown>
}

export type GreedyPublishQueue = {
  queue_key?: string
  depth?: number
  auto_publish_enabled?: boolean
  items?: GreedyPublishItem[]
}

export type GreedyDigestPreview = {
  title?: string
  body_md?: string
  mood?: string
  generated_at?: string
}

export type GreedyReadinessCheck = {
  id: string
  ok: boolean
  message: string
  severity: 'required' | 'recommended' | 'optional'
}

export type GreedyReadiness = {
  ready?: boolean
  environment?: string
  checks?: GreedyReadinessCheck[]
  publish_tenant_id?: string
  publish_tenant_domain?: string
  worldfirst_setup?: Record<string, unknown>
  env_template_path?: string
  admin_hub?: string
}

/** 后端 season 可能是 { label, id } 对象，统一成展示字符串 */
export function formatGreedySeason(raw: unknown): string {
  if (raw == null || raw === '') return '—'
  if (typeof raw === 'string') return raw
  if (typeof raw === 'object') {
    const o = raw as Record<string, unknown>
    for (const key of ['label', 'id', 'name', 'title']) {
      const v = o[key]
      if (typeof v === 'string' && v.trim()) return v.trim()
    }
  }
  return '—'
}

export type GreedyBootstrapResult = {
  tenant?: {
    ok?: boolean
    tenant_id?: string
    source?: string
    domain?: string
    env_hint?: string
  }
  accounts?: Record<string, unknown>
}

function unwrap<T>(res: unknown): T {
  if (res && typeof res === 'object' && 'data' in res) {
    return (res as { data: T }).data
  }
  return res as T
}

export async function fetchGreedyHub(): Promise<Record<string, unknown>> {
  const res = await apiGet('/hermes/greedy/hub')
  return unwrap<Record<string, unknown>>(res)
}

export async function fetchGreedyReadiness(): Promise<GreedyReadiness> {
  const res = await apiGet('/hermes/greedy/readiness')
  return unwrap<GreedyReadiness>(res)
}

export async function bootstrapGreedyTenant(bootstrapAccounts = true): Promise<GreedyBootstrapResult> {
  const qs = bootstrapAccounts ? '?bootstrap_accounts=true' : '?bootstrap_accounts=false'
  const res = await apiPost(`/hermes/greedy/ops/bootstrap-tenant${qs}`)
  return unwrap<GreedyBootstrapResult>(res)
}

export async function fetchGreedySurvivalPublishTasks(limit = 20): Promise<{
  items: Record<string, unknown>[]
  total?: number
}> {
  const res = await apiGet('/hermes/greedy/publish-queue/tasks', { limit })
  return unwrap<{ items: Record<string, unknown>[]; total?: number }>(res)
}

export async function retryPublishTask(taskId: string): Promise<void> {
  await apiPost(`/platforms/publish/tasks/${taskId}/retry`)
}

export async function recordSurvivalSettlement(payload: {
  amount_minor: number
  currency?: string
  channel: string
  payment_provider: string
  provider_payment_id: string
  note?: string
}): Promise<Record<string, unknown>> {
  const res = await apiPost('/hermes/ops/survival/record', payload)
  return unwrap<Record<string, unknown>>(res)
}

export async function fetchGreedyCumulative(): Promise<GreedyCumulative> {
  const res = await apiGet('/hermes/greedy/contest/cumulative')
  return unwrap<GreedyCumulative>(res)
}

export async function fetchGreedyContestStatus(): Promise<Record<string, unknown>> {
  const res = await apiGet('/hermes/greedy/contest/status')
  return unwrap<Record<string, unknown>>(res)
}

export async function fetchGreedyEndurance(): Promise<Record<string, unknown>> {
  const res = await apiGet('/hermes/greedy/contest/endurance')
  return unwrap<Record<string, unknown>>(res)
}

export async function fetchGreedyLeaderboard(limit = 30): Promise<GreedyLeaderboard> {
  const res = await apiGet('/hermes/greedy/contest/leaderboard', { limit })
  return unwrap<GreedyLeaderboard>(res)
}

export async function fetchGreedyProjectBoard(limit = 80): Promise<GreedyProjectBoard> {
  const res = await apiGet('/hermes/greedy/contest/project-board', { limit })
  return unwrap<GreedyProjectBoard>(res)
}

export async function fetchGreedyPublishQueue(limit = 50): Promise<GreedyPublishQueue> {
  const res = await apiGet('/hermes/greedy/publish-queue', { limit })
  return unwrap<GreedyPublishQueue>(res)
}

export async function fetchGreedyPublishHistory(limit = 30): Promise<GreedyPublishReviewHistory[]> {
  const res = await apiGet('/hermes/greedy/publish-queue/history', { limit })
  const data = unwrap<{ history?: GreedyPublishReviewHistory[] }>(res)
  return data.history || []
}

export async function reviewGreedyPublishItem(payload: {
  queue_index: number
  action: 'approve' | 'reject'
  reason?: string
}): Promise<Record<string, unknown>> {
  const res = await apiPost('/hermes/greedy/publish-queue/review', payload)
  return unwrap<Record<string, unknown>>(res)
}

export async function runGreedyRevenueLoop(payload?: {
  message?: string
  locale?: string
  survival_goal_cny?: number
}): Promise<Record<string, unknown>> {
  const res = await apiPost('/hermes/greedy/revenue-loop/run?background=true', payload || {})
  return unwrap<Record<string, unknown>>(res)
}

export async function fetchSurvivalStatus(): Promise<Record<string, unknown>> {
  const res = await apiGet('/hermes/ops/survival')
  return unwrap<Record<string, unknown>>(res)
}

export async function recordWorldfirstInbound(payload: {
  amount_minor: number
  currency?: string
  transaction_id: string
  inbound_type?: string
  note?: string
}): Promise<Record<string, unknown>> {
  const res = await apiPost('/hermes/ops/survival/worldfirst/record', payload)
  return unwrap<Record<string, unknown>>(res)
}

export async function fetchGreedyRoleMemory(roleId: string): Promise<Record<string, unknown>> {
  const rid = encodeURIComponent(roleId.replace(/^\/+/, ''))
  const res = await apiGet(`/hermes/greedy/memory/roles/${rid}`)
  return unwrap<Record<string, unknown>>(res)
}

export async function fetchGreedyEconomicsCoverage(): Promise<Record<string, unknown>> {
  const res = await apiGet('/hermes/greedy/agency/economics/coverage')
  return unwrap<Record<string, unknown>>(res)
}

export async function fetchGreedyEconomicsRank(limit = 12): Promise<Record<string, unknown>[]> {
  const res = await apiGet('/hermes/greedy/agency/economics/rank', { limit })
  const data = unwrap<{ roles?: Record<string, unknown>[] }>(res)
  return data.roles || []
}

export async function fetchGreedyDigestPreview(): Promise<GreedyDigestPreview> {
  const res = await apiGet('/hermes/greedy/survival-digest/preview')
  return unwrap<GreedyDigestPreview>(res)
}

export async function sendGreedyDigest(): Promise<Record<string, unknown>> {
  const res = await apiPost('/hermes/greedy/survival-digest/send')
  return unwrap<Record<string, unknown>>(res)
}

export async function fetchGreedyDigestScheduler(): Promise<Record<string, unknown>> {
  const res = await apiGet('/hermes/greedy/survival-digest/scheduler')
  return unwrap<Record<string, unknown>>(res)
}

export function moodColor(mood?: string): string {
  if (mood === 'ashamed') return 'orange'
  if (mood === 'redemption') return 'green'
  if (mood === 'ambitious') return 'blue'
  if (mood === 'conquest') return 'purple'
  return 'default'
}

export function moodLabel(mood?: string): string {
  const map: Record<string, string> = {
    ashamed: '羞耻',
    redemption: '救赎',
    ambitious: '奋发',
    conquest: '打江山',
  }
  return map[mood || ''] || mood || '—'
}

export function tierColor(tier?: string): string {
  if (tier === 'champion') return 'gold'
  if (tier === 'veteran') return 'blue'
  if (tier === 'contender') return 'cyan'
  return 'default'
}

/** 专家分类 → 中文（示例标签、列表展示） */
const EXPERT_CATEGORY_ZH: Record<string, string> = {
  design: '设计',
  finance: '财务',
  game: '游戏',
  marketing: '营销',
  engineering: '工程',
  product: '产品',
  sales: '销售',
  support: '客服',
  specialized: '专项',
}

/** 常见专家英文代号 → 中文职责名（无中文 name 时兜底） */
const EXPERT_SLUG_ZH: Record<string, string> = {
  'ui-designer': 'UI 设计师',
  'fpa-analyst': '财务分析师',
  'game-designer': '游戏策划',
  'technical-artist': '技术美术',
  'seo-specialist': 'SEO 专家',
  'content-creator': '内容创作',
  'growth-hacker': '增长专家',
  'douyin-strategist': '抖音运营',
  'instagram-curator': 'Instagram 运营',
  'linkedin-content-creator': 'LinkedIn 内容',
  'ai-citation-strategist': 'AI 引用优化',
  'cross-border-ecommerce': '跨境电商',
  'kuaishou-strategist': '快手运营',
  'wechat-official-account-manager': '微信公众号',
  'xiaohongshu-specialist': '小红书运营',
  'bilibili-content-strategist': 'B站内容',
  'paid-media-auditor': '广告投放审计',
  'ppc-campaign-strategist': '搜索广告投放',
}

export function expertCategoryLabelZh(category?: string): string {
  const key = (category || '').trim().toLowerCase()
  return EXPERT_CATEGORY_ZH[key] || '其他'
}

/** 优先用后端中文 name；否则把英文代号翻成可读中文 */
export function expertRoleLabelZh(roleId: string, name?: string): string {
  const trimmed = (name || '').trim()
  if (trimmed && /[\u4e00-\u9fff]/.test(trimmed)) return trimmed
  const slug = (roleId.split('/').pop() || roleId).trim().toLowerCase()
  if (EXPERT_SLUG_ZH[slug]) return EXPERT_SLUG_ZH[slug]
  const cat = (roleId.split('/')[0] || '').toLowerCase()
  const bare = slug.replace(new RegExp(`^${cat}-`), '')
  if (EXPERT_SLUG_ZH[bare]) return EXPERT_SLUG_ZH[bare]
  if (trimmed) return trimmed
  return slug
    .split('-')
    .map((w) => EXPERT_SLUG_ZH[w] || w)
    .join(' ')
    .replace(/\b\w/g, (c) => c.toUpperCase())
}

export function formatCnyMinor(minor?: number | null): string {
  const n = Number(minor || 0) / 100
  return `¥${n.toFixed(2)}`
}

export function evolutionPriorityColor(priority?: string): string {
  if (priority === 'P0') return 'red'
  if (priority === 'P1') return 'orange'
  return 'blue'
}

export function completionStatus(pct?: number | null): 'success' | 'active' | 'exception' | 'normal' {
  if (pct == null) return 'normal'
  if (pct >= 100) return 'success'
  if (pct >= 60) return 'active'
  if (pct < 30) return 'exception'
  return 'normal'
}
