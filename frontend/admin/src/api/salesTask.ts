/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 * 销售待办任务 + 跟进提醒（follow-up 引擎）API 客户端
 */
import { apiGet, apiPost, apiPut } from '@/utils/api'

/** 模型真相：open / done / cancelled（后端写入时兼容别名） */
export type SalesTaskStatus = 'open' | 'done' | 'cancelled'

export interface SalesTaskItem {
  id: string
  title: string
  description?: string | null
  task_type?: string
  priority?: string
  status?: string
  due_at?: string | null
  assigned_to?: string | null
  rfq_id?: string | null
  opportunity_id?: string | null
  company_id?: string | null
  lead_id?: string | null
  created_at?: string | null
}

export interface SalesTaskPage {
  items: SalesTaskItem[]
  total: number
  page?: number
  page_size?: number
}

export interface SalesTaskCreateBody {
  title: string
  description?: string
  task_type?: string
  priority?: string
  due_at?: string
  assigned_to?: string
  rfq_id?: string
  opportunity_id?: string
  company_id?: string
  lead_id?: string
}

function unwrapData<T>(raw: unknown): T {
  // apiGet/apiPost unwrapApiBody 已在 code==0 时抽出 data；此处仅兜底
  if (raw && typeof raw === 'object' && 'data' in (raw as Record<string, unknown>) && 'code' in (raw as Record<string, unknown>)) {
    return (raw as { data: T }).data
  }
  return raw as T
}

export async function listSalesTasks(params: {
  page?: number
  page_size?: number
  status?: string
  task_type?: string
}): Promise<SalesTaskPage> {
  const qs = new URLSearchParams()
  qs.set('page', String(params.page ?? 1))
  qs.set('page_size', String(params.page_size ?? 20))
  if (params.status) qs.set('status', params.status)
  if (params.task_type) qs.set('task_type', params.task_type)
  const raw = await apiGet<unknown>(`/tasks?${qs.toString()}`)
  return unwrapData<SalesTaskPage>(raw)
}

export async function updateSalesTaskStatus(id: string, status: SalesTaskStatus): Promise<SalesTaskItem> {
  const raw = await apiPut<unknown>(`/tasks/${encodeURIComponent(id)}/status`, { status })
  return unwrapData<SalesTaskItem>(raw)
}

export async function createSalesTask(body: SalesTaskCreateBody): Promise<SalesTaskItem> {
  const raw = await apiPost<unknown>('/tasks', body)
  return unwrapData<SalesTaskItem>(raw)
}

export interface FollowUpActionDict {
  channel?: string
  subject?: string
  body_template?: string
  delay?: string
  priority?: number
  reason?: string
  expected_effect?: number
}

/** next-action：FastAPI 用 query 参数 */
export async function fetchFollowUpNextAction(q: {
  trigger: string
  current_stage: string
  company_name?: string
}): Promise<FollowUpActionDict | { action: null; message?: string }> {
  const qs = new URLSearchParams({
    trigger: q.trigger,
    current_stage: q.current_stage,
  })
  if (q.company_name) qs.set('company_name', q.company_name)
  const raw = await apiPost<unknown>(`/follow-up/next-action?${qs.toString()}`, {})
  return unwrapData(raw)
}

export async function fetchBestSendTime(timezone = 'default'): Promise<{
  best_time_utc?: string
  timezone?: string
}> {
  const raw = await apiGet<unknown>(`/follow-up/best-send-time?lead_timezone=${encodeURIComponent(timezone)}`)
  return unwrapData(raw)
}

export async function fetchShouldStop(q: {
  current_stage: string
  trigger: string
  total_attempts?: number
  max_attempts?: number
}): Promise<{ should_stop?: boolean; reason?: string }> {
  const qs = new URLSearchParams({
    current_stage: q.current_stage,
    trigger: q.trigger,
    total_attempts: String(q.total_attempts ?? 0),
    max_attempts: String(q.max_attempts ?? 5),
  })
  const raw = await apiPost<unknown>(`/follow-up/should-stop?${qs.toString()}`, {})
  return unwrapData(raw)
}

export async function fetchFollowUpAnalyze(): Promise<{
  strategies?: Record<string, { label?: string; steps?: number; total_effect?: number }>
  best_send_times?: Record<string, string[]>
}> {
  const raw = await apiPost<unknown>('/follow-up/analyze', {})
  return unwrapData(raw)
}

export const FOLLOW_UP_STAGES = [
  { value: 'initial', label: '首次触达' },
  { value: 'follow_up_1', label: '第1次跟进' },
  { value: 'follow_up_2', label: '第2次跟进' },
  { value: 'follow_up_3', label: '第3次跟进' },
  { value: 'breakup', label: '最后告别' },
  { value: 'stopped', label: '已停止' },
] as const

export const FOLLOW_UP_TRIGGERS = [
  { value: 'no_response', label: '无响应' },
  { value: 'opened_no_reply', label: '已打开未回复' },
  { value: 'clicked_no_reply', label: '已点击未回复' },
  { value: 'replied', label: '已回复' },
  { value: 'bounced', label: '退信' },
  { value: 'unsubscribed', label: '退订' },
  { value: 'scheduled', label: '定时触发' },
] as const

export const TASK_TYPE_LABELS: Record<string, string> = {
  followup: '跟进',
  rfq_response: 'RFQ 响应',
  quote_approval: '报价审批',
  outbound: '外联',
  review: '复核',
}
