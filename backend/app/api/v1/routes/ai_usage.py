"""AI Token 用量监控与告警路由 - 模块化架构（真实数据库查询，无 mock 回退）"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.ai_config import AIUsageLog
from app.models.alert import AlertEvent, AlertRule
from app.models.user import User


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = ""
ROUTE_TAGS = ["AI用量监控"]

router = APIRouter(prefix="/ai-usage", tags=["AI用量监控"])


@router.get("/overview")
def get_usage_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Token 用量总览（真实数据库查询）"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")

    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = today_start.replace(day=1)
    today_total = _safe_sum(db, AIUsageLog.total_tokens, AIUsageLog.created_at >= today_start)
    month_total = _safe_sum(db, AIUsageLog.total_tokens, AIUsageLog.created_at >= month_start)
    total_all = _safe_sum(db, AIUsageLog.total_tokens)
    month_cost = _safe_sum(db, AIUsageLog.cost, AIUsageLog.created_at >= month_start)
    model_rows = (
        db.query(
            AIUsageLog.model_name,
            func.count(AIUsageLog.id).label("call_count"),
            func.sum(AIUsageLog.total_tokens).label("total_tokens"),
            func.sum(AIUsageLog.cost).label("total_cost"),
        )
        .filter(AIUsageLog.created_at >= month_start)
        .group_by(AIUsageLog.model_name)
        .order_by(func.sum(AIUsageLog.total_tokens).desc())
        .all()
    )
    # 从租户配置获取配额限制（默认 10000K tokens）
    total_quota = 10000
    month_k = round(int(month_total) / 1000, 1)
    return success_response(
        data={
            "monthly_tokens": month_k,
            "today_tokens": round(int(today_total) / 1000, 1),
            "total_tokens": int(total_all),
            "estimated_cost": float(month_cost) if month_cost else 0,
            "remaining_quota": max(0, total_quota - month_k) if month_k else total_quota,
            "total_quota": total_quota,
            "quota_percent": min(100, round(month_k / total_quota * 100, 1)) if month_k else 0,
            "has_data": int(month_total) > 0 or int(today_total) > 0,
            "disclaimer": "统计来自 AIUsageLog；无调用记录时各项为 0，不展示虚构趋势",
            "model_rankings": [
                {
                    "model_name": r.model_name,
                    "call_count": int(r.call_count),
                    "tokens": round(int(r.total_tokens) / 1000, 1),
                    "total_cost": float(r.total_cost) if r.total_cost else 0,
                    "percent": round(
                        int(r.total_tokens) / max(int(month_total), 1) * 100, 1
                    ),
                }
                for r in model_rows
            ],
        }
    )


@router.get("/daily")
def get_daily_usage(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """每日用量趋势"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")

    now = datetime.now(timezone.utc)
    since = now - timedelta(days=days)
    rows = (
        db.query(
            func.date(AIUsageLog.created_at).label("date"),
            func.sum(AIUsageLog.total_tokens).label("tokens"),
            func.count(AIUsageLog.id).label("calls"),
        )
        .filter(AIUsageLog.created_at >= since)
        .group_by(func.date(AIUsageLog.created_at))
        .order_by(func.date(AIUsageLog.created_at))
        .all()
    )
    data_map: dict = {}
    for r in rows:
        d = str(r.date) if not hasattr(r.date, "strftime") else r.date.strftime("%Y-%m-%d")
        data_map[d] = {"date": d, "value": round(int(r.tokens) / 1000, 1)}

    # 仅返回有真实记录的天；禁止补全零值制造「假趋势」
    items = [data_map[d] for d in sorted(data_map.keys())]
    return success_response(
        data={
            "items": items,
            "has_data": len(items) > 0,
            "disclaimer": "仅展示有 AI 调用记录的日期；未上线或无调用时不生成日曲线",
        }
    )


@router.get("/models")
def get_model_ranking(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """模型用量排行"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")

    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    rows = (
        db.query(
            AIUsageLog.model_name,
            func.count(AIUsageLog.id).label("call_count"),
            func.sum(AIUsageLog.total_tokens).label("total_tokens"),
            func.sum(AIUsageLog.cost).label("total_cost"),
        )
        .filter(AIUsageLog.created_at >= month_start)
        .group_by(AIUsageLog.model_name)
        .order_by(func.sum(AIUsageLog.total_tokens).desc())
        .all()
    )
    total = sum((int(r.total_tokens) or 0) for r in rows) or 1
    items = [
        {
            "rank": i + 1,
            "model": r.model_name,
            "provider": r.model_name.split("-")[0] if "-" in r.model_name else r.model_name,
            "calls": int(r.call_count),
            "tokens": f"{round(int(r.total_tokens) / 1000, 1)}K",
            "percent": round(int(r.total_tokens) / total * 100, 1),
        }
        for i, r in enumerate(rows)
    ]
    return success_response(data={"items": items})


@router.get("/logs")
def get_ai_usage_logs(
    task_type: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """AI 调用日志（真实数据库）"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")

    from app.services.ai_config_service import AIConfigService
    service = AIConfigService(db)
    logs = service.get_usage_logs(task_type=task_type, page=page, page_size=page_size)
    provider_names: dict[str, str | None] = {}
    items = []
    for log in logs:
        if log.provider_id not in provider_names:
            provider = service.get_provider_by_id(log.provider_id)
            provider_names[log.provider_id] = provider.name if provider else None
        items.append(
            {
                "id": str(log.id),
                "provider_id": log.provider_id,
                "provider_name": provider_names.get(log.provider_id),
                "model_name": log.model_name,
                "task_type": log.task_type,
                "total_tokens": int(log.total_tokens) if log.total_tokens else 0,
                "duration_ms": int(log.duration_ms) if log.duration_ms else 0,
                "success": bool(log.success),
                "error_message": log.error_message,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
        )

    return success_response(
        data={
            "items": items,
            "total": len(items),
            "page": page,
            "page_size": page_size,
        }
    )


@router.get("/alerts")
def get_alerts(
    status: Optional[str] = Query(None, pattern="^(open|acknowledged|resolved)$"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """告警列表"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")

    q = db.query(AlertEvent).filter(
        AlertEvent.category.in_(["ai_cost", "ai_usage", "ai_error"])
    )
    if status:
        q = q.filter(AlertEvent.status == status)
    else:
        q = q.filter(AlertEvent.status.in_(["open", "acknowledged"]))

    alerts = q.order_by(AlertEvent.created_at.desc()).limit(limit).all()
    return success_response(
        data={
            "items": [
                {
                    "id": str(a.id),
                    "time": a.created_at.strftime("%Y-%m-%d %H:%M") if a.created_at else "",
                    "level": a.level,
                    "message": a.title or a.message,
                    "status": "未处理" if a.status == "open" else "已处理",
                }
                for a in alerts
            ]
        }
    )


@router.post("/alerts/config")
def set_alert_config(
    req: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """设置告警阈值配置"""
    if current_user.role not in ["admin", "super_admin"]:
        return error_response(403, "权限不足")

    thresholds = req.get("thresholds", {})
    enabled = req.get("enabled", True)
    notify_methods = req.get("notify_methods", ["site"])
    rules_map = {
        "50": ("AI 用量达 50%", "ai_usage", "ai_usage_percent"),
        "80": ("AI 用量达 80%", "ai_usage", "ai_usage_percent"),
        "90": ("AI 用量达 90%", "ai_usage", "ai_usage_percent"),
    }
    for pct_str in ["50", "80", "90"]:
        rule_name, cat, metric_key = rules_map[pct_str]
        threshold = thresholds.get(pct_str, int(pct_str))
        existing = (
            db.query(AlertRule)
            .filter(AlertRule.name == rule_name, AlertRule.category == cat)
            .first()
        )
        if existing:
            existing.threshold = float(threshold)
            existing.enabled = enabled
            existing.notify_feishu = "email" in notify_methods or "feishu" in notify_methods
        else:
            db.add(
                AlertRule(
                    name=rule_name,
                    category=cat,
                    metric_key=metric_key,
                    operator="gt",
                    threshold=float(threshold),
                    duration_minutes=60,
                    cooldown_minutes=1440,
                    enabled=enabled,
                    notify_feishu="email" in notify_methods or "feishu" in notify_methods,
                )
            )

    db.commit()
    return success_response(
        data={"success": True, "message": "告警配置已保存"},
        message="告警配置已更新",
    )


@router.get("/alerts/config")
def get_alert_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取告警阈值配置"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")

    rules = db.query(AlertRule).filter(AlertRule.category == "ai_usage").all()
    config = {
        "level50": False,
        "level80": False,
        "level90": False,
    }
    for r in rules:
        for pct in ["50", "80", "90"]:
            if pct in r.name:
                config[f"level{pct}"] = r.enabled

    return success_response(data=config)


@router.get("/trend")
def get_usage_trend(
    days: int = Query(7, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """AI 调用趋势（按天统计调用次数）"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")

    now = datetime.now(timezone.utc)
    since = now - timedelta(days=days)
    rows = (
        db.query(
            func.date(AIUsageLog.created_at).label("date"),
            func.count(AIUsageLog.id).label("count"),
        )
        .filter(AIUsageLog.created_at >= since)
        .group_by(func.date(AIUsageLog.created_at))
        .order_by(func.date(AIUsageLog.created_at))
        .all()
    )
    data_map: dict = {}
    for r in rows:
        d = str(r.date) if not hasattr(r.date, "strftime") else r.date.strftime("%Y-%m-%d")
        data_map[d] = {"date": d, "count": int(r.count)}

    items = [data_map[d] for d in sorted(data_map.keys())]
    return success_response(
        data={
            "items": items,
            "has_data": len(items) > 0,
        }
    )


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------

def _safe_sum(db: Session, column, *filters):
    """安全求和，避免 None 错误"""
    q = db.query(func.sum(column))
    for f in filters:
        q = q.filter(f)
    return q.scalar() or 0
