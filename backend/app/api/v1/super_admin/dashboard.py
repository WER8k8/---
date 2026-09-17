# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""控制台大盘接口"""

import time
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.admin_auth import get_current_super_admin
from app.core.database import get_db
from app.core.response import success_response
from app.models.ai_config import AIUsageLog
from app.models.inquiry import Inquiry
from app.models.news import NewsArticle
from app.models.product import Product
from app.models.user import User
from app.services.finance_honesty import count_real_inquiries

router = APIRouter()

_SYSTEM_STATUS_CACHE: dict[str, object] = {"ts": 0.0, "payload": None}
_SYSTEM_STATUS_TTL_SEC = 30.0


@router.get("/stats")
def get_dashboard_stats(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_super_admin),
):
    """控制台核心统计数据"""
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    raw_inquiry_count = (
        db.query(func.count(Inquiry.id))
        .filter(Inquiry.is_active.is_(True))
        .scalar()
        or 0
    )
    total_inquiries = count_real_inquiries(db)
    today_inquiries = count_real_inquiries(db, today_start=today_start)
    stats = {
        "total_products": db.query(func.count(Product.id)).scalar() or 0,
        "total_news": db.query(func.count(NewsArticle.id)).scalar() or 0,
        "total_inquiries": total_inquiries,
        "total_users": db.query(func.count(User.id)).scalar() or 0,
        "today_inquiries": today_inquiries,
        "data_honesty": {
            "excluded_inquiries": max(0, int(raw_inquiry_count) - total_inquiries),
            "raw_inquiries": int(raw_inquiry_count),
        },
    }
    return success_response(data=stats)


@router.get("/ai-usage")
def get_ai_usage_stats(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_super_admin),
):
    """AI 调用统计"""
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = now - timedelta(days=7)
    # 今日调用次数
    today_calls = db.query(func.count(AIUsageLog.id)).filter(
        AIUsageLog.created_at >= today_start
    ).scalar() or 0
    # 今日成功率
    today_success = db.query(func.count(AIUsageLog.id)).filter(
        AIUsageLog.created_at >= today_start,
        AIUsageLog.success == True,
    ).scalar() or 0
    # 本周调用趋势（按天）
    daily_usage = (
        db.query(
            func.date(AIUsageLog.created_at).label("date"),
            func.count(AIUsageLog.id).label("count"),
        )
        .filter(AIUsageLog.created_at >= week_start)
        .group_by("date")
        .order_by("date")
        .all()
    )
    return success_response(data={
        "today_calls": today_calls,
        "today_success_rate": round(today_success / today_calls * 100, 1) if today_calls else 0,
        "daily_trend": [
            {"date": str(d[0]), "count": d[1]} for d in daily_usage
        ],
    })


@router.get("/system-status")
def get_system_status(
    admin: User = Depends(get_current_super_admin),
):
    """系统运行状态（短缓存 + 非阻塞 CPU 采样，避免每次刷新卡 1 秒）。"""
    import platform
    import psutil
    now = time.monotonic()
    cached = _SYSTEM_STATUS_CACHE.get("payload")
    if cached and now - float(_SYSTEM_STATUS_CACHE["ts"]) < _SYSTEM_STATUS_TTL_SEC:
        return success_response(data=cached)

    status = {
        "cpu_percent": psutil.cpu_percent(interval=0.1),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage("/").percent,
        "python_version": platform.python_version(),
        "system": platform.system(),
    }
    _SYSTEM_STATUS_CACHE["ts"] = now
    _SYSTEM_STATUS_CACHE["payload"] = status
    return success_response(data=status)


@router.post("/score-content")
def score_content_endpoint(
    body: dict,
    admin: User = Depends(get_current_super_admin),
):
    """内容质量评分"""
    from app.services.content_scorer import score_content
    title = body.get("title", "")
    content = body.get("body", body.get("content", ""))
    keywords = body.get("keywords", [])
    result = score_content(title, content, keywords)
    return success_response(data=result)
