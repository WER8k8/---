/**
 * 获客作战台 API（跟单卡 / Playbook / 意图预览）
 * 后端：app/api/v1/routes/acquisition.py  prefix=/acquisition
 */
import { apiGet, apiPost } from '@/utils/api'

function unwrap<T = any>(resp: any): T {
  if (resp && typeof resp === 'object' && 'data' in resp && 'code' in resp) {
    return resp.data as T
  }
  return resp as T
}

export interface OpsCardSummary {
  负责人: string
  货: string
  物流: string
  联系: string
  交代: string
  付款: string
  [k: string]: string
}

export interface OpsCardPayload {
  card_id?: string
  inquiry_id?: string
  buyer_id?: string
  tenant_id?: string
  stage?: string
  owner_user_id?: string
  buyer_display?: string
  buyer_grade?: string
  buyer_grade_reason?: string
  buyer_score?: number
  playbook_tips?: string[]
  last_touch_at?: string
  last_channel?: string
  last_summary?: string
  next_action?: string
  notes?: Array<{ author: string; body: string; at: string; pinned?: boolean }>
  loss_reasons?: string[]
  loss_note?: string
  research_level?: string
  sample?: Record<string, unknown>
  fulfillment_nodes?: Array<Record<string, unknown>>
  [k: string]: unknown
}

export interface ScoreDisplay {
  grade: string
  reason: string
  score?: number | null
  action: string
  large: boolean
}

export interface FulfillmentNodeView {
  key: string
  label: string
  status: string
  status_label: string
  due_at?: string
  done_at?: string
  note?: string
  ref?: string
}

export interface SampleView {
  status: string
  label: string
  product?: string
  spec?: string
  qty?: number
  unit?: string
  fee_amount?: number
  fee_currency?: string
  fee_status?: string
  courier?: string
  tracking_no?: string
  shipped_at?: string
  note?: string
  next_action?: string
  allowed_next?: string[]
  fee_hole_risk?: boolean
  hint?: string
}

export interface ResearchGateView {
  research_level: string
  research_level_label: string
  personalized_allowed: boolean
  deep_personalized_allowed: boolean
  reason: string
  next_step: string
  channels?: Record<string, { allowed: boolean; label: string; must_mark?: boolean; hint?: string }>
  hint?: string
}

export interface OpsCardResponse {
  card: OpsCardPayload
  summary: OpsCardSummary
  score_display?: ScoreDisplay
  fulfillment?: {
    nodes: FulfillmentNodeView[]
    reminders: Array<{ node: string; label: string; status: string; display: string; priority?: number }>
    summary?: string
    hint?: string
  } | null
  sample?: SampleView
  research_gate?: ResearchGateView
  sla?: { sla: string; due_at?: string; overdue?: boolean; display?: string }
  loss_report?: LossReportResponse
}

export interface LossReportResponse {
  tenant_id?: string
  total_lost: number
  total_reason_marks: number
  distribution: Array<{ reason: string; count: number; percent: number; hint: string }>
  items: Array<{
    inquiry_id: string
    buyer_display?: string
    buyer_grade?: string
    stage?: string
    loss_reasons: string[]
    loss_note?: string
    lost_at?: string
    owner_user_id?: string
  }>
  top_reason: string
  plain_summary: string
  hint?: string
}

export interface OrchestrationDictionaryResponse {
  version: string
  count: number
  routes: Array<{
    id: string
    name: string
    intent: string
    order: string
    order_label: string
    nodes: string[]
    must: string[]
    human_review: string[]
    scene: string
    plain: string
  }>
  plain_summary: string
  hint?: string
}

export interface IntentPreviewNode {
  id: string
  executor: string
  capability: string
  depends_on: string[]
  approval_required: boolean
}

export interface IntentPreviewResponse {
  plan_id: string
  source: string
  strategy: string
  approval_required: string[]
  nodes: IntentPreviewNode[]
  skill_refs: Array<Record<string, unknown>>
  playbook_tips: string[]
}

export interface PlaybookItem {
  playbook_id: string
  country: string
  buyer_type: string
  payment_bias: string
  tips: string[]
  warnings: string[]
  talk_tracks: string[]
}

/** 意图 → 任务图预览（不真正派发） */
export function previewIntent(body: {
  intent: string
  tenant_id?: string
  payload?: Record<string, unknown>
}): Promise<IntentPreviewResponse> {
  return apiPost<any>('/acquisition/intent/preview', body).then(unwrap)
}

/** 建档 / 更新买家（身份锁） */
export function upsertBuyer(body: Record<string, unknown>): Promise<{
  buyer: Record<string, unknown>
  is_new: boolean
  alerts: string[]
}> {
  return apiPost<any>('/acquisition/buyers/upsert', body).then(unwrap)
}

/** 生成/读取跟单卡 */
export function materializeOpsCard(body: {
  tenant_id: string
  inquiry_id: string
  buyer_id?: string
  owner_user_id?: string
  grade?: number
  grade_reason?: string
}): Promise<OpsCardResponse> {
  return apiPost<any>('/acquisition/ops-card/materialize', body).then(unwrap)
}

export function getOpsCard(inquiryId: string): Promise<OpsCardResponse> {
  return apiGet<any>(`/acquisition/ops-card/${encodeURIComponent(inquiryId)}`).then(unwrap)
}

/** 记一笔跟进（联系） */
export function touchOpsCard(
  inquiryId: string,
  body: { channel?: string; summary: string; next_action?: string; next_action_at?: string },
): Promise<OpsCardResponse> {
  return apiPost<any>(`/acquisition/ops-card/${encodeURIComponent(inquiryId)}/touch`, body).then(unwrap)
}

export function addOpsCardNote(
  inquiryId: string,
  body: { author?: string; body: string; pinned?: boolean },
): Promise<OpsCardResponse> {
  return apiPost<any>(`/acquisition/ops-card/${encodeURIComponent(inquiryId)}/note`, body).then(unwrap)
}

export function recordOpsCardLoss(
  inquiryId: string,
  body: { reasons: string[]; note?: string },
): Promise<OpsCardResponse> {
  return apiPost<any>(`/acquisition/ops-card/${encodeURIComponent(inquiryId)}/loss`, body).then(unwrap)
}

export function listPlaybooks(country?: string, buyerType?: string): Promise<{ playbooks: PlaybookItem[] }> {
  const q = new URLSearchParams()
  if (country) q.set('country', country)
  if (buyerType) q.set('buyer_type', buyerType)
  const qs = q.toString()
  return apiGet<any>(`/acquisition/playbooks${qs ? `?${qs}` : ''}`).then(unwrap)
}

export function playbookTips(country: string, buyerType = 'new'): Promise<{ tips: string[] }> {
  return apiGet<any>(
    `/acquisition/playbooks/tips?country=${encodeURIComponent(country)}&buyer_type=${encodeURIComponent(buyerType)}`,
  ).then(unwrap)
}

/**
 * 客户回复进线 → 自动建卡并记跟进（傻子都行：一步完成）
 * 后端 acquisition.reply_ingest 或 materialize+touch 组合。
 */
export async function ingestReply(body: {
  tenant_id: string
  inquiry_id: string
  buyer_id?: string
  channel?: string
  message: string
  country?: string
  grade?: number
  owner_user_id?: string
  contact_name?: string
  company_name?: string
  email?: string
}): Promise<
  OpsCardResponse & {
    alerts?: string[]
    playbook_tips?: string[]
    intent_analysis?: {
      intent: string
      stage_suggestion: string
      confidence: number
      reason: string
      next_action: string
      talk_track: string
    }
  }
> {
  const raw = await apiPost<any>('/acquisition/reply-ingest', body).then(unwrap)
  return raw
}

/** 双向翻译（无引擎时 degraded=true，译文=原文） */
export function translateAcquisition(
  text: string,
  fromLang = 'auto',
  toLang = 'zh',
): Promise<{
  original: string
  translated: string
  from_lang: string
  to_lang: string
  provider: string
  degraded: boolean
  message: string
}> {
  return apiPost<any>('/acquisition/translate', {
    text,
    from_lang: fromLang,
    to_lang: toLang,
  }).then(unwrap)
}

/** Token/套餐闸（无账本诚实 unknown） */
export function getWalletStatus(tenantId = 'demo'): Promise<{
  tenant_id: string
  token_balance: number | null
  plan: string | null
  hard_block_enabled: boolean
  status: string
  message: string
  next_step?: string
}> {
  return apiGet<any>(`/acquisition/wallet-status?tenant_id=${encodeURIComponent(tenantId)}`).then(unwrap)
}

/** 作战台一键派发：拆解任务图，auto_dispatch=true 时尝试真派发 */
export function dispatchAcquisition(body: {
  intent: string
  tenant_id?: string
  channel?: string
  payload?: Record<string, unknown>
  inquiry_id?: string
  auto_dispatch?: boolean
}): Promise<{
  plan_id: string
  graph_source: string
  node_count: number
  nodes: Array<Record<string, unknown>>
  approval_required: string[]
  dispatched: boolean
  task_ids: string[]
  plan_task_id: string
  dispatch_error: string
  persistence_note: string
  experience?: Record<string, unknown> | null
  card?: OpsCardPayload | null
}> {
  return apiPost<any>('/acquisition/dispatch', body).then(unwrap)
}

export function listFollowups(tenantId = 'demo', includeLost = false): Promise<{
  tenant_id: string
  total: number
  overdue_count: number
  items: Array<{
    inquiry_id: string
    stage: string
    owner_user_id: string
    buyer_display: string
    buyer_grade: string
    next_action: string
    next_action_at: string
    last_summary: string
    summary: OpsCardSummary
    sla: { sla: string; due_at: string; overdue: boolean; display: string }
  }>
  hint: string
}> {
  return apiGet<any>(
    `/acquisition/followups?tenant_id=${encodeURIComponent(tenantId)}&include_lost=${includeLost ? 'true' : 'false'}`,
  ).then(unwrap)
}

export function updateOpsCardPayment(
  inquiryId: string,
  body: {
    pi_no?: string
    deposit_amount?: number
    deposit_due?: string
    deposit_paid_at?: string
    balance_amount?: number
    balance_status?: string
    voucher_url?: string
    overdue_days?: number
  },
): Promise<OpsCardResponse> {
  return apiPost<any>(`/acquisition/ops-card/${encodeURIComponent(inquiryId)}/payment`, body).then(unwrap)
}

export function updateOpsCardLogistics(
  inquiryId: string,
  body: {
    forwarder?: string
    carrier?: string
    bl_no?: string
    container_no?: string
    etd?: string
    eta?: string
    milestone?: string
  },
): Promise<OpsCardResponse> {
  return apiPost<any>(`/acquisition/ops-card/${encodeURIComponent(inquiryId)}/logistics`, body).then(unwrap)
}

export function updateOpsCardGoods(
  inquiryId: string,
  body: {
    sku_lines?: Array<{ name?: string; spec?: string; qty?: number; unit?: string; price?: number; currency?: string }>
    container_hint?: string
  },
): Promise<OpsCardResponse> {
  return apiPost<any>(`/acquisition/ops-card/${encodeURIComponent(inquiryId)}/goods`, body).then(unwrap)
}

/** 获客渠道健康（real/mock 红标） */
export function listAcquisitionChannels(): Promise<{
  channels: Array<{ id: string; name: string; status: string; reason: string; is_mock: boolean }>
  mock_count?: number
  real_count?: number
  hint?: string
  error?: string
}> {
  return apiGet<any>('/acquisition/channels').then(unwrap)
}

/** P1-5 样品状态机 */
export function updateOpsCardSample(
  inquiryId: string,
  body: {
    status?: string
    product?: string
    spec?: string
    qty?: number
    unit?: string
    fee_amount?: number
    fee_currency?: string
    fee_status?: string
    courier?: string
    tracking_no?: string
    shipped_at?: string
    note?: string
  },
): Promise<OpsCardResponse> {
  return apiPost<any>(`/acquisition/ops-card/${encodeURIComponent(inquiryId)}/sample`, body).then(unwrap)
}

/** P1-2 履约节点（报价/PI/定金/尾款） */
export function updateOpsCardFulfillment(
  inquiryId: string,
  body: { key: string; status?: string; due_at?: string; done_at?: string; note?: string; ref?: string },
): Promise<OpsCardResponse> {
  return apiPost<any>(`/acquisition/ops-card/${encodeURIComponent(inquiryId)}/fulfillment`, body).then(unwrap)
}

/** P1-6 背调深度（千人千面强制序） */
export function updateOpsCardResearch(
  inquiryId: string,
  body: { research_level: string; note?: string },
): Promise<OpsCardResponse> {
  return apiPost<any>(`/acquisition/ops-card/${encodeURIComponent(inquiryId)}/research`, body).then(unwrap)
}

/** P1-3 流失原因报表 */
export function getLossReport(tenantId = 'demo'): Promise<LossReportResponse> {
  return apiGet<any>(`/acquisition/loss-report?tenant_id=${encodeURIComponent(tenantId)}`).then(unwrap)
}

/** P1-9 编排词典 v1 */
export function getOrchestrationDictionary(): Promise<OrchestrationDictionaryResponse> {
  return apiGet<any>('/acquisition/orchestration-dictionary').then(unwrap)
}

/** P1-6 个性化开发信闸 */
export function getOutreachGate(researchLevel = 'none'): Promise<ResearchGateView> {
  return apiGet<any>(
    `/acquisition/outreach-gate?research_level=${encodeURIComponent(researchLevel)}`,
  ).then(unwrap)
}

/** P1-7 内容获客归因 */
export function getContentAttribution(tenantId = 'demo'): Promise<{
  tenant_id?: string
  content_count: number
  total_attributed_inquiries: number
  items: Array<{
    content_id: string
    content_title?: string
    content_type?: string
    channel?: string
    inquiry_count: number
    inquiry_ids: string[]
  }>
  plain_summary: string
  hint?: string
}> {
  return apiGet<any>(`/acquisition/attribution/content?tenant_id=${encodeURIComponent(tenantId)}`).then(unwrap)
}

export function linkContentInquiry(body: {
  content_id: string
  inquiry_id: string
  tenant_id?: string
}): Promise<{ linked: boolean; content_id?: string; inquiry_id?: string; inquiry_count?: number }> {
  return apiPost<any>('/acquisition/attribution/content/link', body).then(unwrap)
}

/** P1-8 IP/指纹槽位只读 */
export function getIpSlots(tenantId = 'demo'): Promise<{
  tenant_id?: string
  slots: Array<{
    slot_id: string
    label: string
    region?: string
    status: string
    status_label: string
    note?: string
  }>
  total: number
  known_count: number
  billing_ready: boolean
  plain_summary: string
  hint?: string
}> {
  return apiGet<any>(`/acquisition/ip-slots?tenant_id=${encodeURIComponent(tenantId)}`).then(unwrap)
}

/** P2-2 成交登记 */
export function recordOpsCardWin(
  inquiryId: string,
  body: { amount?: number; currency?: string; note?: string; reasons?: string[] },
): Promise<OpsCardResponse & { win_loss?: WinLossResponse }> {
  return apiPost<any>(`/acquisition/ops-card/${encodeURIComponent(inquiryId)}/win`, body).then(unwrap)
}

export interface WinLossResponse {
  tenant_id?: string
  won_count: number
  lost_count: number
  win_reasons: Record<string, number>
  loss_reasons: Record<string, number>
  top_win_reason: string
  top_loss_reason: string
  plain_summary: string
  won_items?: Array<{ inquiry_id: string; buyer_display?: string; amount?: number; note?: string }>
  experience_hint?: string
}

export function getWinLoss(tenantId = 'demo'): Promise<WinLossResponse> {
  return apiGet<any>(`/acquisition/win-loss?tenant_id=${encodeURIComponent(tenantId)}`).then(unwrap)
}

export interface OnboardingResponse {
  tenant_id?: string
  steps: Array<{
    id: string
    title: string
    path: string
    plain: string
    done: boolean
    status_label: string
  }>
  done_count: number
  total: number
  percent: number
  next_step: { id: string; title: string; plain: string; path: string } | null
  plain_summary: string
  hint?: string
}

/** P2-4 开通 5 步引导 */
export function getOnboarding(tenantId = 'demo', hasDispatch = false): Promise<OnboardingResponse> {
  return apiGet<any>(
    `/acquisition/onboarding?tenant_id=${encodeURIComponent(tenantId)}&has_dispatch=${hasDispatch ? 'true' : 'false'}`,
  ).then(unwrap)
}

/** P2-3 L1 模板权重建议（只读，人审才生效） */
export function getTemplateWeights(tenantId = 'demo'): Promise<{
  tenant_id?: string
  won: number
  lost: number
  win_rate?: number | null
  suggestions: Array<{
    intent: string
    label: string
    base_weight: number
    suggested_weight: number
    delta: number
    sample_n: number
    status: string
    reasons: string[]
    requires_human_review: boolean
    applied: boolean
  }>
  plain_summary: string
  mode: string
  approved?: { approved: Record<string, { weight: number; approved_by: string }>; plain_summary: string }
}> {
  return apiGet<any>(`/acquisition/template-weights?tenant_id=${encodeURIComponent(tenantId)}`).then(unwrap)
}

export function approveTemplateWeight(body: {
  intent: string
  weight: number
  approved_by?: string
  tenant_id?: string
}): Promise<{ approved: { intent: string; weight: number }; plain_summary: string }> {
  return apiPost<any>('/acquisition/template-weights/approve', body).then(unwrap)
}

/** P2-1 经验真源体检 */
export function getExperienceSource(tenantId = 'demo'): Promise<{
  primary_source: string
  pg_available: boolean
  pg_hints: number
  json_fallback_used: boolean
  plain_summary: string
  hint?: string
}> {
  return apiGet<any>(`/acquisition/experience-source?tenant_id=${encodeURIComponent(tenantId)}`).then(unwrap)
}

/** P2-6 账单可解释 */
export function getBillingExplain(tenantId = 'demo', limit = 20): Promise<{
  tenant_id?: string
  balance: number | null
  items: Array<{ at: string; kind: string; delta: number; balance_after?: number | null; reason: string; plain: string; reference_id?: string }>
  plain_summary: string
  source?: string
  hint?: string
}> {
  return apiGet<any>(
    `/acquisition/billing-explain?tenant_id=${encodeURIComponent(tenantId)}&limit=${limit}`,
  ).then(unwrap)
}

/** P2-7 撞单认领 */
export function claimOpsInquiry(
  inquiryId: string,
  body: { user_id: string; tenant_id?: string; confirm_force?: boolean; note?: string },
): Promise<{
  ok: boolean
  code: string
  message: string
  owner_user_id?: string
  card?: OpsCardPayload
  audit?: Array<Record<string, unknown>>
  hint?: string
}> {
  return apiPost<any>(`/acquisition/ops-card/${encodeURIComponent(inquiryId)}/claim`, body).then(unwrap)
}

export function getCollisionReport(tenantId = 'demo'): Promise<{
  items: Array<{ inquiry_id: string; owner_user_id: string; handoff_count: number; last_handoff?: Record<string, unknown> }>
  total: number
  plain_summary: string
  rule: string
}> {
  return apiGet<any>(`/acquisition/collision-report?tenant_id=${encodeURIComponent(tenantId)}`).then(unwrap)
}

/** P1-10 旺财线B 建站卡壳补救 */
export function getWangcaiRescue(tenantId = 'demo'): Promise<{
  blocked: boolean
  blockers: Array<{ task_id: string; task_type: string; status: string; error?: string }>
  suggested_intent?: string
  alternate_intent?: string
  allow_dispatch: boolean
  repeated: boolean
  plain_summary: string
  next_steps?: string[]
  hint?: string
}> {
  return apiGet<any>(`/acquisition/wangcai-rescue?tenant_id=${encodeURIComponent(tenantId)}`).then(unwrap)
}

/** P2-8 移动端跟单紧凑摘要 */
export function getMobileFollowupBrief(tenantId = 'demo'): Promise<{
  tenant_id: string
  total: number
  overdue_count: number
  brief: string
  top: Array<{ inquiry_id: string; display: string; next: string; sla: string }>
  hint: string
}> {
  return listFollowups(tenantId).then((r) => {
    const top = (r.items || []).slice(0, 5).map((i) => ({
      inquiry_id: i.inquiry_id,
      display: i.buyer_display || i.inquiry_id,
      next: i.next_action || i.last_summary || '—',
      sla: i.sla?.display || '',
    }))
    return {
      tenant_id: r.tenant_id,
      total: r.total,
      overdue_count: r.overdue_count,
      brief: r.overdue_count > 0 ? `手机待办：${r.overdue_count} 个逾期先处理` : `手机待办：共 ${r.total} 个，无逾期`,
      top,
      hint: '六格+今日待办手机可跟；点开即可记跟进。',
    }
  })
}

/** P3-4 制裁名单 */
export function getSanctionsSource(): Promise<{
  configured: boolean
  source: string
  count?: number
  plain_summary: string
  note?: string
}> {
  return apiGet<any>('/acquisition/sanctions/source').then(unwrap)
}

export function screenSanctions(body: {
  name?: string
  email?: string
  company?: string
  domain?: string
  inquiry_id?: string
}): Promise<{
  result: string
  level?: string
  plain: string
  source?: string
  hits?: Array<Record<string, unknown>>
  inquiry_id?: string
}> {
  return apiPost<any>('/acquisition/sanctions/screen', body).then(unwrap)
}

/** P3-7 招投标 */
export function getTender(tenderId: string): Promise<{
  tender_id: string
  inquiry_id?: string
  stage: string
  stage_label?: string
  qualify_ready: boolean
  missing_docs?: string[]
  auto_pi_allowed?: boolean
  plain: string
  next_action?: string
}> {
  return apiGet<any>(`/acquisition/tender/${encodeURIComponent(tenderId)}`).then(unwrap)
}

export function upsertTender(body: {
  tender_id?: string
  inquiry_id?: string
  tenant_id?: string
  buyer_name?: string
  project_name?: string
  amount?: number
  currency?: string
}): Promise<{ tender_id: string; plain?: string; inquiry_id?: string }> {
  return apiPost<any>('/acquisition/tender/upsert', body).then(unwrap)
}

export function advanceTender(body: {
  tender_id: string
  to_stage: string
  note?: string
  payment_terms?: string
  credit_ok?: boolean
  inquiry_id?: string
}): Promise<{ ok: boolean; message?: string; stage?: string; plain?: string }> {
  return apiPost<any>('/acquisition/tender/advance', body).then(unwrap)
}

export function bindTenderToCard(
  inquiryId: string,
  body: Record<string, unknown>,
): Promise<OpsCardResponse & { tender?: Record<string, unknown> }> {
  return apiPost<any>(`/acquisition/ops-card/${encodeURIComponent(inquiryId)}/tender`, body).then(unwrap)
}

/** P2-5 NPS / 低使用挽回 */
export function getNpsRescue(
  tenantId = 'demo',
  npsScore?: number | null,
): Promise<{
  tenant_id?: string
  nps: {
    score: number | null
    collected: boolean
    bucket?: string
    label: string
    plain: string
    suggested_touch?: string
  }
  usage: {
    cards: number
    touches: number
    won: number
    lost: number
    usage_low: boolean
  }
  rescue_actions: string[]
  should_notify: boolean
  plain_summary: string
  hint?: string
}> {
  const q = new URLSearchParams({ tenant_id: tenantId })
  if (npsScore !== null && npsScore !== undefined) q.set('nps_score', String(npsScore))
  return apiGet<any>(`/acquisition/nps-rescue?${q.toString()}`).then(unwrap)
}

/** P3-5 退订/抑制名单 */
export function getSuppressionList(tenantId = 'demo'): Promise<{
  tenant_id?: string
  total: number
  by_reason: Record<string, number>
  items: Array<{ email: string; reason: string; created_at: string }>
  plain_summary: string
}> {
  return apiGet<any>(`/acquisition/suppression?tenant_id=${encodeURIComponent(tenantId)}`).then(unwrap)
}

export function addSuppression(body: {
  email: string
  tenant_id?: string
  reason?: string
  source?: string
}): Promise<{ ok: boolean; code: string; message: string }> {
  return apiPost<any>('/acquisition/suppression/add', body).then(unwrap)
}

export function checkOutreachAllowed(body: {
  email: string
  tenant_id?: string
  channel?: string
  mode?: string
}): Promise<{ allowed: boolean; code: string; message: string }> {
  return apiPost<any>('/acquisition/outreach/allow-check', body).then(unwrap)
}

/** P3-2/3/6 */
export function updateQuoteValidity(
  inquiryId: string,
  body: { quote_at?: string; valid_days?: number; fx_locked?: boolean; fx_note?: string },
): Promise<OpsCardResponse> {
  return apiPost<any>(`/acquisition/ops-card/${encodeURIComponent(inquiryId)}/quote-validity`, body).then(unwrap)
}

export function updateLeadtime(
  inquiryId: string,
  body: {
    promised_days?: number
    has_inventory_evidence?: boolean
    has_capacity_evidence?: boolean
    note?: string
  },
): Promise<OpsCardResponse> {
  return apiPost<any>(`/acquisition/ops-card/${encodeURIComponent(inquiryId)}/leadtime`, body).then(unwrap)
}

export function getPaymentRisk(body: {
  country?: string
  buyer_type?: string
  inquiry_id?: string
  auto_pi?: boolean
  deposit_ratio?: number
  risk_flags?: string[]
}): Promise<{
  level: string
  risk_score: number
  auto_pi_allowed: boolean
  auto_pi_blocked: boolean
  reasons: string[]
  plain: string
  next_action: string
}> {
  return apiPost<any>('/acquisition/payment-risk', body).then(unwrap)
}

/** P3-8 知识队列 */
export function getKnowledgeQueue(tenantId = 'demo'): Promise<{
  tenant_id?: string
  total: number
  done_count: number
  pending_count: number
  next_item: { id: string; title: string; plain: string; why: string; category: string } | null
  items: Array<{ id: string; title: string; category: string; plain: string; why: string; done: boolean }>
  plain_summary: string
}> {
  return apiGet<any>(`/acquisition/knowledge-queue?tenant_id=${encodeURIComponent(tenantId)}`).then(unwrap)
}

export function markKnowledge(body: {
  item_id: string
  action?: 'done' | 'reset'
  tenant_id?: string
}): Promise<{ ok: boolean; code: string; message: string }> {
  return apiPost<any>('/acquisition/knowledge-queue/mark', body).then(unwrap)
}

/** P3-4 制裁/风险重扫 */
export function getRiskRescan(tenantId = 'demo', rescanDays = 90): Promise<{
  tenant_id?: string
  total_tracked: number
  due_count: number
  never_scanned: number
  overdue: number
  external_list_configured: boolean
  source_plain: string
  items: Array<{
    inquiry_id: string
    buyer_display?: string
    status: string
    status_label: string
    due: boolean
    plain: string
    next_action: string
  }>
  plain_summary: string
}> {
  return apiGet<any>(
    `/acquisition/risk-rescan?tenant_id=${encodeURIComponent(tenantId)}&rescan_days=${rescanDays}`,
  ).then(unwrap)
}

export function markRiskScan(body: {
  inquiry_id: string
  result?: string
  source?: string
  note?: string
  country?: string
  risk_flags?: string[]
}): Promise<{ ok: boolean; code: string; message: string }> {
  return apiPost<any>('/acquisition/risk-rescan/mark', body).then(unwrap)
}
