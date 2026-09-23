# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""运维聚合端点 `/ops/*`（B4）：对齐前端 cost-summary / task-board / system-logs / module-visibility / alignment-report。"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.models.user import User

ROUTE_PREFIX = "/ops"
ROUTE_TAGS = ["运维聚合"]

router = APIRouter(tags=["运维聚合"])


@router.get("/cost-summary")
def ops_cost_summary(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """AI/Token 成本汇总（聚合 AIUsageLog；无数据时诚实空汇总）。"""
    from app.models.ai_config import AIUsageLog

    since = datetime.now(timezone.utc) - timedelta(days=days)
    logs = db.query(AIUsageLog).filter(AIUsageLog.created_at >= since).all()
    total_cost = 0.0
    total_calls = len(logs)
    success_calls = 0
    by_model: dict[str, float] = {}
    for log in logs:
        try:
            pt = int(log.prompt_tokens or 0)
            ct = int(log.completion_tokens or 0)
        except (TypeError, ValueError):
            pt, ct = 0, 0
        cost = round((pt + ct) / 1000 * 0.002, 6)
        total_cost += cost
        if log.success:
            success_calls += 1
        by_model[log.model_name or "unknown"] = by_model.get(log.model_name or "unknown", 0) + cost

    return success_response(data={
        "period_days": days,
        "total_cost": round(total_cost, 4),
        "total_calls": total_calls,
        "success_calls": success_calls,
        "by_model": [
            {"model": m, "cost": round(c, 4)}
            for m, c in sorted(by_model.items(), key=lambda x: -x[1])
        ],
        "source": "AIUsageLog",
    })


@router.get("/task-board")
def ops_task_board(
    current_user: User = Depends(get_current_user),
):
    """运维任务看板：无真实任务源时诚实空列表，不造假任务。"""
    return success_response(data={
        "items": [],
        "total": 0,
        "status": "empty",
        "hint": "任务源未接入（docs/admin-route-task-board.json 仅供 CLI）",
    })


@router.get("/system-logs")
def ops_system_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
):
    """系统日志聚合：与 /system/logs 同诚实策略，未实现不返回假空列表。"""
    if current_user.role not in ("super_admin", "admin"):
        return error_response(403, "权限不足")
    return error_response(
        501,
        "not_configured: 系统日志查询未实现；请用 /system/audit/logs",
    )


@router.get("/module-visibility")
def ops_module_visibility(
    current_user: User = Depends(get_current_user),
):
    """模块可见性快照（超管默认面 / Lab 隐藏面计数）。"""
    try:
        from app.api.v1.admin_bff import menu_seeds  # noqa: F401
    except Exception:
        pass
    return success_response(data={
        "default_visible": True,
        "lab_hidden_enabled": False,
        "source": "stubVisibility/localStorage:admin_cert_mode",
        "status": "ready",
    })


@router.get("/alignment-report")
def ops_alignment_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """40 平台 catalog 与 DB 对齐报告。"""
    from app.services.platform_alignment_service import alignment_report

    return success_response(data=alignment_report(db))
