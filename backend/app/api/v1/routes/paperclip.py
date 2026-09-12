"""Paperclip Agent 编排 API — 公司 / Agent / 目标 / 任务 / 心跳 / 预算 / 审批"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Any

from app.api.v1.routes.ubrain import _resolve_tenant_id
from app.core.admin_auth import get_current_super_admin
from app.core.response import success_response
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = ""

router = APIRouter(prefix="/paperclip", tags=["Paperclip Agent 编排"])


def _get_or_create_company_id(db: Session, current_user: User) -> str:
    """从当前登录用户解析 tenant_id，找到或自动创建对应 Paperclip 公司。"""
    tenant_id = _resolve_tenant_id(current_user, db)
    if not tenant_id:
        raise HTTPException(status_code=400, detail="无法解析当前租户身份")
    from app.services.paperclip.orchestrator import get_or_create_company_for_tenant
    return get_or_create_company_for_tenant(db, tenant_id)


# ────────────────────────────────────────────
# Pydantic 请求体
# ────────────────────────────────────────────

class CompanyCreateBody(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    mission: str | None = Field(default=None, max_length=2000)


class CompanyUpdateBody(BaseModel):
    name: str | None = Field(default=None, max_length=200)
    mission: str | None = Field(default=None, max_length=2000)
    status: str | None = Field(default=None, max_length=40)


class AgentHireBody(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    role: str = Field(..., min_length=1, max_length=120)
    title: str | None = Field(default=None, max_length=120)
    budget_cents: int | None = Field(default=None, ge=0)
    heartbeat_interval_sec: int | None = Field(default=None, ge=10, le=86400)
    manager_agent_id: str | None = None


class AgentUpdateBody(BaseModel):
    title: str | None = Field(default=None, max_length=120)
    budget_cents: int | None = Field(default=None, ge=0)
    heartbeat_interval_sec: int | None = Field(default=None, ge=10, le=86400)


class GoalCreateBody(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    description: str | None = Field(default=None, max_length=4000)
    level: str = Field(default="company", max_length=40)
    parent_goal_id: str | None = None
    owner_agent_id: str | None = None
    metric_target: float | None = None
    deadline: str | None = None


class GoalUpdateBody(BaseModel):
    title: str | None = Field(default=None, max_length=300)
    description: str | None = Field(default=None, max_length=4000)
    status: str | None = Field(default=None, max_length=40)
    metric_target: float | None = None
    deadline: str | None = None


class TaskCreateBody(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    description: str | None = Field(default=None, max_length=4000)
    goal_id: str | None = None
    priority: str = Field(default="normal", max_length=20)


class TaskAssignBody(BaseModel):
    agent_id: str = Field(..., min_length=1)
    instructions: str | None = Field(default=None, max_length=2000)


class BudgetAdjustBody(BaseModel):
    monthly_budget_cents: int = Field(..., ge=0)
    reason: str | None = Field(default=None, max_length=500)


class ApproveBody(BaseModel):
    comment: str | None = Field(default=None, max_length=1000)


# ────────────────────────────────────────────
# 公司管理
# ────────────────────────────────────────────

@router.post("/companies")
def create_company(
    body: CompanyCreateBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin),
):
    """创建公司（超管）"""
    from app.services.paperclip.orchestrator import create_company
    result = create_company(db, name=body.name, mission=body.mission, created_by=str(current_user.id))
    return success_response(data=result)


@router.get("/companies")
def list_companies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin),
):
    """列出公司（超管）"""
    from app.services.paperclip.orchestrator import list_companies
    return success_response(data=list_companies(db))


@router.get("/companies/{company_id}")
def get_company(
    company_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """公司详情"""
    from app.services.paperclip.orchestrator import get_company_detail
    result = get_company_detail(db, company_id)
    if not result:
        raise HTTPException(status_code=404, detail="公司不存在")
    return success_response(data=result)


@router.put("/companies/{company_id}")
def update_company(
    company_id: str,
    body: CompanyUpdateBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin),
):
    """更新公司（使命、状态）"""
    from app.services.paperclip.orchestrator import update_company
    result = update_company(
        db,
        company_id,
        name=body.name,
        mission=body.mission,
        status=body.status,
    )
    if not result:
        raise HTTPException(status_code=404, detail="公司不存在")
    return success_response(data=result)


# ────────────────────────────────────────────
# Agent 管理
# ────────────────────────────────────────────

@router.post("/companies/{company_id}/agents")
def hire_agent(
    company_id: str,
    body: AgentHireBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """雇佣 Agent（创建审批）"""
    from app.services.paperclip.orchestrator import hire_agent as _hire_agent
    result = _hire_agent(
        db,
        company_id=company_id,
        name=body.name,
        role=body.role,
        title=body.title,
        budget_cents=body.budget_cents,
        heartbeat_interval_sec=body.heartbeat_interval_sec,
        manager_agent_id=body.manager_agent_id,
        requested_by=str(current_user.id),
    )
    return success_response(data=result)


@router.get("/companies/{company_id}/agents")
def list_agents(
    company_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """列出 Agent"""
    from app.services.paperclip.orchestrator import list_company_agents
    return success_response(data=list_company_agents(db, company_id))


@router.get("/agents/{agent_id}")
def get_agent(
    agent_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Agent 详情"""
    from app.services.paperclip.orchestrator import get_agent_detail
    result = get_agent_detail(db, agent_id)
    if not result:
        raise HTTPException(status_code=404, detail="Agent 不存在")
    return success_response(data=result)


@router.put("/agents/{agent_id}")
def update_agent(
    agent_id: str,
    body: AgentUpdateBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新 Agent（头衔、预算、心跳间隔）"""
    from app.services.paperclip.orchestrator import update_agent as _update_agent
    result = _update_agent(
        db,
        agent_id,
        title=body.title,
        budget_cents=body.budget_cents,
        heartbeat_interval_sec=body.heartbeat_interval_sec,
    )
    if not result:
        raise HTTPException(status_code=404, detail="Agent 不存在")
    return success_response(data=result)


@router.post("/agents/{agent_id}/pause")
def pause_agent(
    agent_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """暂停 Agent"""
    from app.services.paperclip.orchestrator import pause_agent as _pause_agent
    result = _pause_agent(db, agent_id)
    if not result:
        raise HTTPException(status_code=404, detail="Agent 不存在")
    return success_response(data=result)


@router.post("/agents/{agent_id}/resume")
def resume_agent(
    agent_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """恢复 Agent"""
    from app.services.paperclip.orchestrator import resume_agent as _resume_agent
    result = _resume_agent(db, agent_id)
    if not result:
        raise HTTPException(status_code=404, detail="Agent 不存在")
    return success_response(data=result)


@router.post("/agents/{agent_id}/terminate")
def terminate_agent(
    agent_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """终止 Agent"""
    from app.services.paperclip.orchestrator import terminate_agent as _terminate_agent
    result = _terminate_agent(db, agent_id)
    if not result:
        raise HTTPException(status_code=404, detail="Agent 不存在")
    return success_response(data=result)


@router.get("/companies/{company_id}/org-chart")
def get_org_chart(
    company_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """组织架构树"""
    from app.services.paperclip.orchestrator import build_org_chart
    return success_response(data=build_org_chart(db, company_id))


# ────────────────────────────────────────────
# 目标管理
# ────────────────────────────────────────────

@router.post("/companies/{company_id}/goals")
def create_goal(
    company_id: str,
    body: GoalCreateBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建目标"""
    from app.services.paperclip.goal_chain import create_goal as _create_goal
    result = _create_goal(
        db,
        company_id=company_id,
        title=body.title,
        description=body.description,
        level=body.level,
        parent_goal_id=body.parent_goal_id,
        owner_agent_id=body.owner_agent_id,
        metric_target=body.metric_target,
        deadline=body.deadline,
    )
    return success_response(data=result)


@router.get("/companies/{company_id}/goals")
def list_goals(
    company_id: str,
    level: str | None = Query(None, description="目标层级筛选"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """列出目标（支持 level 筛选）"""
    from app.services.paperclip.goal_chain import list_company_goals
    return success_response(data=list_company_goals(db, company_id, level=level))


@router.get("/goals/{goal_id}")
def get_goal(
    goal_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """目标详情（含对齐链）"""
    from app.services.paperclip.goal_chain import get_goal_detail
    result = get_goal_detail(db, goal_id)
    if not result:
        raise HTTPException(status_code=404, detail="目标不存在")
    return success_response(data=result)


@router.put("/goals/{goal_id}")
def update_goal(
    goal_id: str,
    body: GoalUpdateBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新目标"""
    from app.services.paperclip.goal_chain import update_goal as _update_goal
    result = _update_goal(
        db,
        goal_id,
        title=body.title,
        description=body.description,
        status=body.status,
        metric_target=body.metric_target,
        deadline=body.deadline,
    )
    if not result:
        raise HTTPException(status_code=404, detail="目标不存在")
    return success_response(data=result)


@router.get("/goals/{goal_id}/chain")
def get_goal_chain(
    goal_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取目标对齐链"""
    from app.services.paperclip.goal_chain import get_alignment_chain
    result = get_alignment_chain(db, goal_id)
    if not result:
        raise HTTPException(status_code=404, detail="目标不存在")
    return success_response(data=result)


# ────────────────────────────────────────────
# 任务管理
# ────────────────────────────────────────────

@router.post("/companies/{company_id}/tasks")
def create_task(
    company_id: str,
    body: TaskCreateBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建任务"""
    from app.services.paperclip.orchestrator import create_task as _create_task
    result = _create_task(
        db,
        company_id=company_id,
        title=body.title,
        description=body.description,
        goal_id=body.goal_id,
        priority=body.priority,
    )
    return success_response(data=result)


@router.get("/companies/{company_id}/tasks")
def list_tasks(
    company_id: str,
    status: str | None = Query(None, description="任务状态筛选"),
    agent_id: str | None = Query(None, description="执行 Agent 筛选"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """列出任务（支持 status/agent_id 筛选）"""
    from app.services.paperclip.orchestrator import list_company_tasks
    return success_response(
        data=list_company_tasks(db, company_id, status=status, agent_id=agent_id)
    )


@router.post("/tasks/{task_id}/assign")
def assign_task(
    task_id: str,
    body: TaskAssignBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """委派任务给 Agent"""
    from app.services.paperclip.orchestrator import assign_task as _assign_task
    result = _assign_task(
        db,
        task_id,
        agent_id=body.agent_id,
        instructions=body.instructions,
    )
    if not result:
        raise HTTPException(status_code=404, detail="任务不存在")
    return success_response(data=result)


@router.post("/tasks/{task_id}/execute")
def execute_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """立即执行任务"""
    from app.services.paperclip.orchestrator import execute_task_now
    result = execute_task_now(db, task_id)
    if not result:
        raise HTTPException(status_code=404, detail="任务不存在")
    return success_response(data=result)


# ────────────────────────────────────────────
# 心跳
# ────────────────────────────────────────────

@router.get("/companies/{company_id}/heartbeats")
def list_heartbeats(
    company_id: str,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """心跳记录列表"""
    from app.services.paperclip.heartbeat_engine import list_company_heartbeats
    return success_response(data=list_company_heartbeats(db, company_id, limit=limit))


@router.post("/agents/{agent_id}/heartbeat")
def trigger_heartbeat(
    agent_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """手动触发心跳"""
    from app.services.paperclip.heartbeat_engine import trigger_manual_heartbeat
    result = trigger_manual_heartbeat(db, agent_id)
    if not result:
        raise HTTPException(status_code=404, detail="Agent 不存在")
    return success_response(data=result)


@router.get("/heartbeat-engine/status")
def heartbeat_engine_status(
    current_user: User = Depends(get_current_user),
):
    """心跳引擎状态"""
    from app.services.paperclip.heartbeat_engine import engine_status
    return success_response(data=engine_status())


@router.post("/heartbeat-engine/start")
def start_heartbeat_engine(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin),
):
    """启动心跳引擎（超管）"""
    from app.services.paperclip.heartbeat_engine import start_engine
    return success_response(data=start_engine(db))


@router.post("/heartbeat-engine/stop")
def stop_heartbeat_engine(
    current_user: User = Depends(get_current_super_admin),
):
    """停止心跳引擎（超管）"""
    from app.services.paperclip.heartbeat_engine import stop_engine
    return success_response(data=stop_engine())


# ────────────────────────────────────────────
# 预算
# ────────────────────────────────────────────

@router.get("/companies/{company_id}/budget")
def get_budget(
    company_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """预算总览"""
    from app.services.paperclip.budget_guard import budget_overview
    return success_response(data=budget_overview(db, company_id))


@router.put("/agents/{agent_id}/budget")
def adjust_agent_budget(
    agent_id: str,
    body: BudgetAdjustBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """调整预算（创建审批）"""
    from app.services.paperclip.budget_guard import adjust_budget
    result = adjust_budget(
        db,
        agent_id,
        monthly_budget_cents=body.monthly_budget_cents,
        reason=body.reason,
        requested_by=str(current_user.id),
    )
    if not result:
        raise HTTPException(status_code=404, detail="Agent 不存在")
    return success_response(data=result)


@router.post("/budget/reset-monthly")
def reset_monthly_budget(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin),
):
    """月度重置（超管 cron）"""
    from app.services.paperclip.budget_guard import run_monthly_reset
    return success_response(data=run_monthly_reset(db))


# ────────────────────────────────────────────
# 审批
# ────────────────────────────────────────────

@router.get("/companies/{company_id}/approvals")
def list_approvals(
    company_id: str,
    status: str | None = Query(None, description="审批状态筛选"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """审批列表"""
    from app.services.paperclip.approval_gate import list_company_approvals
    return success_response(data=list_company_approvals(db, company_id, status=status))


@router.post("/approvals/{approval_id}/approve")
def approve(
    approval_id: str,
    body: ApproveBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """批准"""
    from app.services.paperclip.approval_gate import approve_request
    result = approve_request(
        db,
        approval_id,
        approved_by=str(current_user.id),
        comment=body.comment,
    )
    if not result:
        raise HTTPException(status_code=404, detail="审批不存在")
    return success_response(data=result)


@router.post("/approvals/{approval_id}/reject")
def reject(
    approval_id: str,
    body: ApproveBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """拒绝"""
    from app.services.paperclip.approval_gate import reject_request
    result = reject_request(
        db,
        approval_id,
        rejected_by=str(current_user.id),
        comment=body.comment,
    )
    if not result:
        raise HTTPException(status_code=404, detail="审批不存在")
    return success_response(data=result)


# ────────────────────────────────────────────
# 仪表盘
# ────────────────────────────────────────────

@router.get("/companies/{company_id}/dashboard")
def get_dashboard(
    company_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """综合仪表盘"""
    from app.services.paperclip.orchestrator import build_company_dashboard
    return success_response(data=build_company_dashboard(db, company_id))


# ────────────────────────────────────────────
# 同步
# ────────────────────────────────────────────

@router.post("/sync/hermes")
def sync_from_hermes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin),
):
    """从 Hermes 同步 Agent（超管）"""
    from app.services.paperclip.orchestrator import sync_agents_from_hermes
    tenant_id = _resolve_tenant_id(current_user, db)
    return success_response(data=sync_agents_from_hermes(db, tenant_id=tenant_id))


# ────────────────────────────────────────────
# 当前租户快捷入口（前端无需知道 company_id）
# ────────────────────────────────────────────

@router.get("/my/company")
def get_my_company(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取当前租户的 Paperclip 公司（不存在则自动创建）"""
    from app.services.paperclip.orchestrator import get_company_detail, get_or_create_company_for_tenant
    tenant_id = _resolve_tenant_id(current_user, db)
    if not tenant_id:
        raise HTTPException(status_code=400, detail="无法解析当前租户身份")
    company_id = get_or_create_company_for_tenant(db, tenant_id)
    return success_response(data=get_company_detail(db, company_id))


@router.post("/my/sync-hermes")
def my_sync_hermes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """为当前租户同步 Hermes Agent（自动创建公司）"""
    from app.services.paperclip.orchestrator import sync_agents_from_hermes
    tenant_id = _resolve_tenant_id(current_user, db)
    if not tenant_id:
        raise HTTPException(status_code=400, detail="无法解析当前租户身份")
    return success_response(data=sync_agents_from_hermes(db, tenant_id=tenant_id))
