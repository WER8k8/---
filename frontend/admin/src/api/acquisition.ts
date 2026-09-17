/**
 * 获客作战台 API（跟单卡 / Playbook / 意图预览）
 * 后端：app/api/v1/routes/acquisition.py  prefix=/acquisition
 */
import { apiGet, apiPost } from '@/utils/api'

function unwrap<T>(resp: any): T {
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
  playbook_tips?: string[]
  last_touch_at?: string
  last_channel?: string
  last_summary?: string
  next_action?: string
  notes?: Array<{ author: string; body: string; at: string; pinned?: boolean }>
  loss_reasons?: string[]
  [k: string]: unknown
}

export interface OpsCardResponse {
  card: OpsCardPayload
  summary: OpsCardSummary
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
