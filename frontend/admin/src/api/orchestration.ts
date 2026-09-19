/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
/**
 * 统一编排链 API 客户端（Hermes / AiTask）
 *
 * 后端落点：
 *   routes/orchestration.py      ROUTE_PREFIX="/orchestration"
 *   routes/task_control_admin.py ROUTE_PREFIX="/task-control"
 *   完整路径 = /api/v1 + 上述前缀（apiGet/apiPost 已带 /api/v1 baseURL）
 *
 * 与 agent-hub/task-orchestrator（读 DeerflowJob 队列）是**两套不同模型**：
 * 本模块对接的是 AiTask 任务图链（plan 父任务 + hermes_node:* 子节点）。
 */
import { apiGet, apiPost } from '@/utils/api'

/** POST /orchestration/tasks 的请求体 */
export interface OrchestrationTaskRequest {
  /** 任务类型，如 ai_site_build / site_build / hermes_node:site_builder */
  task_type: string
  /** 任务输入（product_name / message / product_images 等） */
  input_data?: Record<string, unknown>
  /** 超管可显式指定租户；普通用户自动解析 */
  tenant_id?: string
  /** 幂等键，(tenant,key) 重复提交返回已有任务 */
  idempotency_key?: string
  /** 优先级 1-10 */
  priority?: number
  /** 创建后立即入 Celery 执行 */
  auto_dispatch?: boolean
}

export interface OrchestrationTaskResponse {
  task_id: string
  status: string
  detail?: string
}

/** 任务控制面返回的任务条目 */
export interface TaskControlItem {
  id: string
  task_type?: string
  status?: string
  priority?: number
  parent_task_id?: string | null
  tenant_id?: string
  created_at?: string
  updated_at?: string
  error_message?: string | null
  output_summary?: string | null
  [k: string]: unknown
}

export interface TaskControlPage {
  total: number
  page: number
  page_size: number
  items: TaskControlItem[]
}

/** 统一解包 {code,message,data} 外壳；非该外壳时原样返回 */
function unwrap<T>(resp: any): T {
  if (resp && typeof resp === 'object' && 'data' in resp && 'code' in resp) {
    return resp.data as T
  }
  return resp as T
}

/** 创建编排任务并（默认）立即派发 */
export async function createOrchestrationTask(
  payload: OrchestrationTaskRequest,
): Promise<OrchestrationTaskResponse> {
  const raw = await apiPost<any>('/orchestration/tasks', payload)
  return unwrap<OrchestrationTaskResponse>(raw)
}

/** 自然语言意图 → 自动拆解成任务图（走后端 planner_service.decompose） */
export interface FromIntentRequest {
  /** 意图描述，如「帮我建站」/「找德国买家并写开发信」 */
  intent: string
  /** 业务参数（product_name / topic / keyword 等） */
  payload?: Record<string, unknown>
  /** 触发渠道 */
  channel?: string
  context?: Record<string, unknown>
  tenant_id?: string
  auto_dispatch?: boolean
}

export interface FromIntentResponse {
  plan_id: string
  /** 图来源：L1_template 模板 / L2_llm 模型出图 / L3_minimal 兜底 */
  graph_source: string
  node_count: number
  node_tasks: string[]
  dispatched: boolean
}

export async function createTaskFromIntent(
  payload: FromIntentRequest,
): Promise<FromIntentResponse> {
  const raw = await apiPost<any>('/orchestration/tasks/from-intent', payload)
  return unwrap<FromIntentResponse>(raw)
}

/** 查询单个编排任务状态 */
export async function getOrchestrationTask(taskId: string): Promise<OrchestrationTaskResponse> {
  const raw = await apiGet<any>(`/orchestration/tasks/${encodeURIComponent(taskId)}`)
  return unwrap<OrchestrationTaskResponse>(raw)
}

/** 待人工审核 / 待干预的任务（status in review / wait_human） */
export async function listPendingReviews(params?: {
  tenant_id?: string
  page?: number
  page_size?: number
}): Promise<TaskControlPage> {
  const qs = new URLSearchParams()
  if (params?.tenant_id) qs.set('tenant_id', params.tenant_id)
  qs.set('page', String(params?.page ?? 1))
  qs.set('page_size', String(params?.page_size ?? 20))
  const raw = await apiGet<any>(`/task-control/pending-reviews?${qs.toString()}`)
  return unwrap<TaskControlPage>(raw)
}

/** 任务详情（含父计划与其子节点） */
export async function getTaskControlDetail(
  taskId: string,
  tenantId?: string,
): Promise<TaskControlItem> {
  const qs = tenantId ? `?tenant_id=${encodeURIComponent(tenantId)}` : ''
  const raw = await apiGet<any>(`/task-control/${encodeURIComponent(taskId)}${qs}`)
  return unwrap<TaskControlItem>(raw)
}

/** 三种干预动作 */
export async function resumeTask(taskId: string): Promise<unknown> {
  return unwrap(await apiPost(`/task-control/${encodeURIComponent(taskId)}/resume`, {}))
}

export async function cancelTask(taskId: string): Promise<unknown> {
  return unwrap(await apiPost(`/task-control/${encodeURIComponent(taskId)}/cancel`, {}))
}

export async function retryTask(taskId: string): Promise<unknown> {
  return unwrap(await apiPost(`/task-control/${encodeURIComponent(taskId)}/retry`, {}))
}

/** SEAM-P0 Hermes 任务中心 */
export interface HermesPlanItem {
  plan_id: string
  task_type?: string
  status?: string
  priority?: number
  child_count?: number
  node_statuses?: string[]
  golden_path?: string | null
  plane?: string
  graph_source?: string | null
  intent?: string
  error_message?: string | null
  source?: string | null
  created_at?: string | null
  started_at?: string | null
  finished_at?: string | null
}

export interface HermesTaskDetail {
  plan: HermesPlanItem
  nodes: Array<{
    id: string
    task_type?: string
    status?: string
    capability?: string | null
    executor?: string | null
    error_message?: string | null
    created_at?: string | null
    finished_at?: string | null
  }>
}

export async function listHermesTasks(params?: {
  status?: string
  golden_path?: string
  limit?: number
  tenant_id?: string
}): Promise<{ total: number; items: HermesPlanItem[]; tenant_id?: string }> {
  const qs = new URLSearchParams()
  if (params?.status) qs.set('status', params.status)
  if (params?.golden_path) qs.set('golden_path', params.golden_path)
  qs.set('limit', String(params?.limit ?? 50))
  if (params?.tenant_id) qs.set('tenant_id', params.tenant_id)
  const raw = await apiGet<any>(`/orchestration/hermes/tasks?${qs.toString()}`)
  return unwrap(raw)
}

export async function getHermesTaskDetail(planId: string, tenantId?: string): Promise<HermesTaskDetail> {
  const qs = tenantId ? `?tenant_id=${encodeURIComponent(tenantId)}` : ''
  const raw = await apiGet<any>(`/orchestration/hermes/tasks/${encodeURIComponent(planId)}${qs}`)
  return unwrap(raw)
}
