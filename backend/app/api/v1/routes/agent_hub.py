# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""智能体协同中心路由 - 模块化架构"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.core.tenant_access import is_platform_admin, is_tenant_staff
from app.db.session import get_db
from app.models.user import User
from app.services.agent_hub_service import (
    build_execution_review,
    build_job_logs,
    build_mcp_bridge_status,
    build_mcp_tool_catalog,
    build_task_orchestrator,
    probe_mcp_server_health,
    register_custom_mcp_server,
    run_orchestrator_job,
)
from app.services.traffic_analytics_service import resolve_tenant_id


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = "/agent-hub"
ROUTE_TAGS = ["智能体协同"]

router = APIRouter()


def _admin_roles(user: User) -> bool:
    """
    处理 _admin_roles 相关业务逻辑。

    :param user: 入参 (User)。

    :return: 返回 bool 类型的结果。
    """
    return is_tenant_staff(user)


def _tenant_scope(db: Session, user: User) -> str | None:
    """
    处理 _tenant_scope 相关业务逻辑。

    :param db: 入参 (Session)。
    :param user: 入参 (User)。

    :return: 返回 str | None 类型的结果。
    """
    if user.role in ("super_admin", "admin"):
        return None
    return resolve_tenant_id(db, user=user)


@router.get("/")
def get_agent_hub_overview(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)):
    """获取智能体协同概览"""
    if not _admin_roles(current_user):
        return error_response(403, "权限不足")
    orch = build_task_orchestrator(db, tenant_id=_tenant_scope(db, current_user))
    review = build_execution_review(db, tenant_id=_tenant_scope(db, current_user), page_size=5)
    return success_response(
        data={
            "active_tasks": orch["active_tasks"],
            "queued_tasks": orch["queued_tasks"],
            "completed_today": orch["completed_today"],
            "completed_tasks": review["total"],
            "pending_tasks": orch["queued_tasks"],
            "failed_tasks": review["summary"].get("failed_count", 0),
            "agents": [],
            "data_source": "deerflow_jobs",
        }
    )


@router.get("/mcp-bridge")
def get_mcp_bridge_status(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)):
    """获取MCP桥接状态"""
    if not _admin_roles(current_user):
        return error_response(403, "权限不足")
    return success_response(data=build_mcp_bridge_status(db))


@router.post("/mcp-bridge")
def register_mcp_bridge_server(
        req: dict,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)):
    """登记外部 MCP 服务（进程内缓存）"""
    if not _admin_roles(current_user):
        return error_response(403, "权限不足")
    name = str(req.get("name") or "").strip()
    url = str(req.get("url") or "").strip()
    if not name or not url:
        return error_response(400, "缺少 name 或 url")
    entry = register_custom_mcp_server(
        name=name,
        url=url,
        protocol=str(req.get("protocol") or "http"),
    )
    return success_response(data=entry, message="MCP 服务已登记")


@router.get("/mcp-bridge/tools")
def list_mcp_tools(db: Session = Depends(get_db),
                   current_user: User = Depends(get_current_user)):
    """列出MCP工具清单"""
    if not _admin_roles(current_user):
        return error_response(403, "权限不足")
    return success_response(data=build_mcp_tool_catalog())


@router.get("/mcp-bridge/health")
def mcp_bridge_health(
        name: str = "",
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)):
    """MCP 服务健康探测"""
    if not _admin_roles(current_user):
        return error_response(403, "权限不足")
    return success_response(data=probe_mcp_server_health(name=name))


@router.get("/task-orchestrator")
def get_task_orchestrator(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)):
    """获取任务调度状态（DeerFlow 队列）"""
    if not _admin_roles(current_user):
        return error_response(403, "权限不足")
    return success_response(data=build_task_orchestrator(db, tenant_id=_tenant_scope(db, current_user)))


@router.get("/task-orchestrator/logs")
def get_task_orchestrator_logs(
        job_id: str = "",
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)):
    """任务执行日志"""
    if not _admin_roles(current_user):
        return error_response(403, "权限不足")
    if not job_id:
        return error_response(400, "缺少 job_id")
    return success_response(data=build_job_logs(db, job_id))


@router.post("/task-orchestrator/run")
def run_task_orchestrator(
        req: dict,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)):
    """执行任务编排"""
    if not _admin_roles(current_user):
        return error_response(403, "权限不足")
    job_id = str(req.get("id") or "")
    if not job_id:
        return error_response(400, "缺少任务 id")
    result = run_orchestrator_job(db, job_id)
    if result.get("error"):
        return error_response(404, result["error"])
    return success_response(
        data={
            "id": job_id,
            "name": req.get("name"),
            "status": result.get("status", "done"),
        },
        message="编排执行完成",
    )


@router.get("/execution-review")
def get_execution_review(
        page: int = 1,
        page_size: int = 20,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)):
    """获取执行复盘记录（DeerFlow 历史）"""
    if not _admin_roles(current_user):
        return error_response(403, "权限不足")
    return success_response(
        data=build_execution_review(
            db,
            tenant_id=_tenant_scope(db, current_user),
            page=page,
            page_size=page_size,
        )
    )
