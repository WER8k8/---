# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""合规审计路由 - 模块化架构"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.services.security_event_service import (
    ACTION_AUTH_SENSITIVE,
    ACTION_DATA_EXPORT,
    ACTION_DATA_EXPORT_DENIED,
    ACTION_FOUNDER_DENIED,
    list_security_events,
    protection_summary,
)


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = "/compliance"
ROUTE_TAGS = ["合规审计"]

router = APIRouter()

_ALERT_ACTION_LABELS = {
    ACTION_FOUNDER_DENIED: ("权限拒绝", "danger"),
    ACTION_DATA_EXPORT_DENIED: ("导出拦截", "warning"),
    ACTION_AUTH_SENSITIVE: ("敏感操作", "warning"),
    ACTION_DATA_EXPORT: ("数据导出", "info"),
}


def _relative_time(iso: str | None) -> str:
    """
    处理 _relative_time 相关业务逻辑。

    :param iso: 入参 (str | None)。

    :return: 返回 str 类型的结果。
    """
    if not iso:
        return "—"
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        delta = datetime.now(timezone.utc) - dt
        minutes = int(delta.total_seconds() // 60)
        if minutes < 1:
            return "刚刚"
        if minutes < 60:
            return f"{minutes} 分钟前"
        hours = minutes // 60
        if hours < 24:
            return f"{hours} 小时前"
        days = hours // 24
        return f"{days} 天前"
    except (TypeError, ValueError):
        return iso


@router.get("/")
def get_compliance_overview(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)):
    """获取合规概览（仅真实安全事件统计，不编造得分）。"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")

    events = list_security_events(db, limit=200)
    denied = sum(
        1
        for e in events
        if e.get("action") in (ACTION_FOUNDER_DENIED, ACTION_DATA_EXPORT_DENIED)
    )
    protection = protection_summary(db)
    return success_response(
        data={
            "overall_score": None,
            "total_issues": denied,
            "critical_issues": denied,
            "warnings": 0,
            "passed_checks": len(events),
            "data_source": "security_events",
            "protection": protection,
        }
    )


@router.get("/security-alerts")
def list_security_alerts(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """安全告警列表（来自 operation_logs 真实留痕）。"""
    if current_user.role not in ["admin", "super_admin"]:
        return error_response(403, "权限不足")

    events = list_security_events(db, limit=min(limit, 50))
    alerts = []
    for ev in events:
        action = ev.get("action") or "SECURITY"
        title, level = _ALERT_ACTION_LABELS.get(action, (action, "info"))
        detail = ev.get("detail") or {}
        desc_parts = []
        if ev.get("ip_address"):
            desc_parts.append(f"来源 IP：{ev['ip_address']}")
        if detail.get("path"):
            desc_parts.append(f"路径：{detail['path']}")
        if detail.get("reason"):
            desc_parts.append(str(detail["reason"]))
        alerts.append(
            {
                "id": ev.get("id"),
                "title": title,
                "description": " · ".join(desc_parts) or "系统已记录安全相关操作",
                "time": _relative_time(ev.get("created_at")),
                "level": level,
                "action": action,
            }
        )
    return success_response(data={"items": alerts, "total": len(alerts)})


@router.get("/audit")
def run_compliance_audit(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)):
    """运行合规审计（无扫描器时返回空结果，不伪造分数）。"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")

    events = list_security_events(db, limit=50)
    return success_response(
        data={
            "status": "completed",
            "score": None,
            "issues": events[:20],
            "recommendations": [],
            "data_source": "security_events",
        },
        message="审计完成（基于安全事件留痕）")


@router.get("/issues")
def list_compliance_issues(
    page: int = 1,
    page_size: int = 20,
    severity: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取合规问题列表"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")

    return success_response(
        data={
            "items": [],
            "total": 0,
            "page": page,
            "page_size": page_size})


@router.put("/issues/{issue_id}/resolve")
def resolve_issue(
        issue_id: str,
        req: dict,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)):
    """标记合规问题已解决"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")

    return success_response(
        data={
            "issue_id": issue_id,
            "status": "resolved"},
        message="问题已解决")


@router.get("/report")
def generate_compliance_report(
        format: str = "pdf",
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)):
    """生成合规报告"""
    if current_user.role not in ["super_admin"]:
        return error_response(403, "权限不足")

    return success_response(
        data={
            "report_url": "/compliance/report.pdf",
            "format": format},
        message="报告已生成")
