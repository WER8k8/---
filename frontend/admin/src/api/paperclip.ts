/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
/** Paperclip Agent 编排管理 API 客户端 */
import { apiGet, apiPost, apiPut } from '@/utils/api'

const BASE = '/paperclip'

/* ========== 类型定义 ========== */

export interface Company {
  id: string
  name: string
  mission: string
  created_at: string
  updated_at: string
}

export interface Agent {
  id: string
  company_id: string
  name: string
  title: string
  provider: string
  status: 'active' | 'paused' | 'offline' | 'error'
  parent_id: string | null
  skills: string[]
  budget_used: number
  budget_limit: number
  last_heartbeat: string | null
  created_at: string
}

export interface Goal {
  id: string
  company_id: string
  parent_id: string | null
  level: 'mission' | 'project' | 'goal' | 'task'
  title: string
  description: string
  assigned_agent_id: string | null
  assigned_agent_name?: string
  status: 'pending' | 'in_progress' | 'completed' | 'blocked'
  progress: number
  priority: 'low' | 'medium' | 'high' | 'critical'
  created_at: string
}

export interface Task {
  id: string
  goal_id: string
  agent_id: string
  title: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  result: string | null
  created_at: string
}

export interface HeartbeatLog {
  id: string
  agent_id: string
  agent_name: string
  trigger_type: 'auto' | 'manual'
  result: 'success' | 'failure' | 'timeout'
  message: string
  created_at: string
}

export interface Approval {
  id: string
  agent_id: string
  agent_name: string
  action_type: string
  content: string
  status: 'pending' | 'approved' | 'rejected'
  reviewer_comment: string | null
  created_at: string
  reviewed_at: string | null
}

export interface DashboardData {
  company: Company
  stats: {
    total_agents: number
    active_agents: number
    monthly_task_completion_rate: number
    budget_usage_rate: number
    pending_approvals: number
  }
  org_tree: AgentNode[]
  alignment_chain: AlignmentNode[]
  recent_heartbeats: HeartbeatLog[]
}

export interface AgentNode {
  id: string
  name: string
  title: string
  status: string
  provider: string
  children: AgentNode[]
}

export interface AlignmentNode {
  id: string
  title: string
  level: string
}

export interface HeartbeatEngineStatus {
  running: boolean
  next_heartbeat: string | null
  active_agents: number
}

export interface BudgetInfo {
  total: number
  used: number
  remaining: number
}

/* ========== API 调用 ========== */

/* --- 公司 --- */
export const companyAPI = {
  list: () => apiGet<Company[]>(`${BASE}/companies`),
  get: (id: string) => apiGet<Company>(`${BASE}/companies/${id}`),
  create: (data: Partial<Company>) => apiPost<Company>(`${BASE}/companies`, data),
  update: (id: string, data: Partial<Company>) => apiPut<Company>(`${BASE}/companies/${id}`, data),
}

/* --- Agent --- */
export const agentAPI = {
  list: (companyId: string) => apiGet<Agent[]>(`${BASE}/companies/${companyId}/agents`),
  get: (id: string) => apiGet<Agent>(`${BASE}/agents/${id}`),
  hire: (companyId: string, data: Partial<Agent>) => apiPost<Agent>(`${BASE}/companies/${companyId}/agents`, data),
  update: (id: string, data: Partial<Agent>) => apiPut<Agent>(`${BASE}/agents/${id}`, data),
  pause: (id: string) => apiPost<Agent>(`${BASE}/agents/${id}/pause`),
  resume: (id: string) => apiPost<Agent>(`${BASE}/agents/${id}/resume`),
  terminate: (id: string) => apiPost<Agent>(`${BASE}/agents/${id}/terminate`),
  orgTree: (companyId: string) => apiGet<AgentNode[]>(`${BASE}/companies/${companyId}/org-chart`),
}

/* --- 目标 --- */
export const goalAPI = {
  list: (companyId: string, params?: { level?: string; status?: string }) =>
    apiGet<Goal[]>(`${BASE}/companies/${companyId}/goals`, params as Record<string, string>),
  get: (id: string) => apiGet<Goal>(`${BASE}/goals/${id}`),
  create: (companyId: string, data: Partial<Goal>) => apiPost<Goal>(`${BASE}/companies/${companyId}/goals`, data),
  update: (id: string, data: Partial<Goal>) => apiPut<Goal>(`${BASE}/goals/${id}`, data),
  alignmentChain: (id: string) => apiGet<AlignmentNode[]>(`${BASE}/goals/${id}/chain`),
}

/* --- 任务 --- */
export const taskAPI = {
  list: (companyId: string, params?: { goal_id?: string; agent_id?: string; status?: string }) =>
    apiGet<Task[]>(`${BASE}/companies/${companyId}/tasks`, params as Record<string, string>),
  create: (companyId: string, data: Partial<Task>) => apiPost<Task>(`${BASE}/companies/${companyId}/tasks`, data),
  assign: (taskId: string, agentId: string) => apiPost<Task>(`${BASE}/tasks/${taskId}/assign`, { agent_id: agentId }),
  execute: (id: string) => apiPost<Task>(`${BASE}/tasks/${id}/execute`),
}

/* --- 心跳 --- */
export const heartbeatAPI = {
  status: () => apiGet<HeartbeatEngineStatus>(`${BASE}/heartbeat-engine/status`),
  startEngine: () => apiPost<HeartbeatEngineStatus>(`${BASE}/heartbeat-engine/start`),
  stopEngine: () => apiPost<HeartbeatEngineStatus>(`${BASE}/heartbeat-engine/stop`),
  trigger: (agentId: string) =>
    apiPost<HeartbeatLog>(`${BASE}/agents/${agentId}/heartbeat`),
  logs: (companyId: string, params?: { agent_id?: string; limit?: number }) =>
    apiGet<HeartbeatLog[]>(`${BASE}/companies/${companyId}/heartbeats`, params as Record<string, string | number>),
}

/* --- 预算 --- */
export const budgetAPI = {
  get: (companyId: string) => apiGet<BudgetInfo>(`${BASE}/companies/${companyId}/budget`),
  adjust: (agentId: string, monthlyBudgetCents: number, reason?: string) =>
    apiPut<BudgetInfo>(`${BASE}/agents/${agentId}/budget`, { monthly_budget_cents: monthlyBudgetCents, reason }),
  resetMonthly: () => apiPost(`${BASE}/budget/reset-monthly`),
}

/* --- 审批 --- */
export const approvalAPI = {
  list: (companyId: string, params?: { status?: string }) =>
    apiGet<Approval[]>(`${BASE}/companies/${companyId}/approvals`, params as Record<string, string>),
  approve: (id: string, comment?: string) =>
    apiPost<Approval>(`${BASE}/approvals/${id}/approve`, { comment }),
  reject: (id: string, comment: string) =>
    apiPost<Approval>(`${BASE}/approvals/${id}/reject`, { comment }),
}

/* --- 仪表盘 --- */
export const dashboardAPI = {
  get: (companyId: string) => apiGet<DashboardData>(`${BASE}/companies/${companyId}/dashboard`),
}

/* --- 同步 --- */
export const syncAPI = {
  syncHermes: () => apiPost<{ synced: number }>(`${BASE}/sync/hermes`),
  mySyncHermes: () => apiPost<{ synced: number }>(`${BASE}/my/sync-hermes`),
}

/* --- 当前租户快捷入口（自动解析 tenant → company） --- */
export const myPaperclipAPI = {
  getCompany: () => apiGet<Company>(`${BASE}/my/company`),
}
