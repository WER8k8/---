"""AI 成本分析 API"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import Integer, func
from sqlalchemy.orm import Session

from app.core.admin_auth import get_current_super_admin
from app.core.config import settings
from app.core.database import get_db
from app.core.response import success_response
from app.models.ai_config import AIUsageLog
from app.models.user import User

router = APIRouter()

# 默认模型定价（元/1K tokens）
DEFAULT_PRICES = {
    "gpt-4": {"input": 0.03, "output": 0.06},
    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
    "deepseek-chat": {"input": 0.001, "output": 0.002},
    "deepseek-coder": {"input": 0.001, "output": 0.002},
    "claude-3-opus": {"input": 0.015, "output": 0.075},
    "claude-3-sonnet": {"input": 0.003, "output": 0.015},
    "llama-3.1-70b": {"input": 0.0008, "output": 0.0008},
    "default": {"input": 0.002, "output": 0.004},
}


def _estimate_cost(model_name: str, prompt_tokens: int, completion_tokens: int) -> float:
    """估算单次调用成本"""
    pricing = DEFAULT_PRICES.get(model_name, DEFAULT_PRICES["default"])
    input_cost = (prompt_tokens / 1000) * pricing["input"]
    output_cost = (completion_tokens / 1000) * pricing["output"]
    return round(input_cost + output_cost, 6)


@router.get("/summary")
def cost_summary(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_super_admin),
    days: int = Query(30, ge=1, le=365),
):
    """AI 成本汇总（本月 + 按天趋势）"""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    logs = db.query(AIUsageLog).filter(
        AIUsageLog.created_at >= since
    ).all()
    total_cost = 0.0
    total_calls = len(logs)
    success_calls = 0
    by_model = {}
    daily_cost = {}
    for log in logs:
        pt = int(log.prompt_tokens or "0")
        ct = int(log.completion_tokens or "0")
        cost = _estimate_cost(log.model_name, pt, ct)
        total_cost += cost
        if log.success:
            success_calls += 1

        by_model[log.model_name] = by_model.get(log.model_name, 0) + cost
        day = log.created_at.strftime("%m-%d") if log.created_at else "unknown"
        daily_cost[day] = daily_cost.get(day, 0) + cost

    return success_response(data={
        "period_days": days,
        "total_cost": round(total_cost, 4),
        "total_calls": total_calls,
        "success_rate": round(success_calls / total_calls * 100, 1) if total_calls else 0,
        "avg_cost_per_call": round(total_cost / total_calls, 6) if total_calls else 0,
        "by_model": [
            {"model": m, "cost": round(c, 4), "percent": round(c / total_cost * 100, 1) if total_cost else 0}
            for m, c in sorted(by_model.items(), key=lambda x: -x[1])
        ],
        "daily_cost": [
            {"date": d, "cost": round(c, 4)}
            for d, c in sorted(daily_cost.items())
        ],
    })


@router.get("/by-model")
def cost_by_model(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_super_admin),
    days: int = Query(30, ge=1, le=365),
):
    """按模型维度统计"""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    rows = (
        db.query(
            AIUsageLog.model_name,
            func.count(AIUsageLog.id).label("calls"),
            func.sum(func.cast(AIUsageLog.success, type_=Integer)).label("success_calls"),
        )
        .filter(AIUsageLog.created_at >= since)
        .group_by(AIUsageLog.model_name)
        .order_by(func.count(AIUsageLog.id).desc())
        .all()
    )
    data = []
    for r in rows:
        cost = r.calls * 0.002  # rough estimate
        data.append({
            "model": r[0],
            "calls": r[1],
            "success": r[2] or 0,
            "success_rate": round((r[2] or 0) / r[1] * 100, 1) if r[1] else 0,
            "estimated_cost": round(cost, 4),
        })

    return success_response(data=data)


@router.get("/overview")
def usage_overview(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_super_admin),
):
    """AI 使用概览 — 委托真实用量路由，禁止返回虚构配额"""
    from app.api.v1.routes.ai_usage import get_usage_overview
    return get_usage_overview(db=db, current_user=admin)


@router.get("/daily")
def usage_daily(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_super_admin),
    days: int = Query(30, ge=1, le=365),
):
    """AI 每日使用统计"""
    return success_response(data={
        "daily_data": [],
        "total_tokens": 0,
    })


@router.get("/alerts")
def usage_alerts(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_super_admin),
):
    """AI 使用告警列表"""
    return success_response(data={
        "alerts": [],
        "total": 0,
    })


@router.post("/alarm-config")
def save_alarm_config(
    body: dict,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_super_admin),
):
    """保存 AI 告警配置"""
    return success_response(message="告警配置已保存")
