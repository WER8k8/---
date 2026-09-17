# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""数据导出报表 API"""

import csv
import io
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.admin_auth import get_current_super_admin
from app.core.database import get_db
from app.core.response import success_response
from app.models.ai_config import AIUsageLog
from app.models.inquiry import Inquiry
from app.models.news import NewsArticle
from app.models.product import Product
from app.models.user import OperationLog, User

router = APIRouter()


@router.get("/weekly")
def weekly_report(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_super_admin),
):
    """生成周报数据"""
    now = datetime.now(timezone.utc)
    week_start = now - timedelta(days=now.weekday())
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    return success_response(data={
        "period": f"{week_start.strftime('%Y-%m-%d')} ~ {now.strftime('%Y-%m-%d')}",
        "products": {
            "new": db.query(func.count(Product.id)).filter(Product.created_at >= week_start).scalar() or 0,
            "total": db.query(func.count(Product.id)).scalar() or 0,
        },
        "content": {
            "new_articles": db.query(func.count(NewsArticle.id)).filter(NewsArticle.created_at >= week_start).scalar() or 0,
            "total": db.query(func.count(NewsArticle.id)).scalar() or 0,
        },
        "inquiries": {
            "new": db.query(func.count(Inquiry.id)).filter(Inquiry.created_at >= week_start).scalar() or 0,
            "total": db.query(func.count(Inquiry.id)).scalar() or 0,
        },
        "ai": _get_ai_weekly_stats(db, week_start),
        "generated_at": now.isoformat(),
    })


@router.get("/monthly")
def monthly_report(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_super_admin),
):
    """生成月报数据"""
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    # 本月每日数据
    daily_stats = []
    for d in range((now - month_start).days + 1):
        day_start = month_start + timedelta(days=d)
        day_end = day_start + timedelta(days=1)
        inquiries = db.query(func.count(Inquiry.id)).filter(
            Inquiry.created_at >= day_start, Inquiry.created_at < day_end
        ).scalar() or 0
        ai_calls = db.query(func.count(AIUsageLog.id)).filter(
            AIUsageLog.created_at >= day_start, AIUsageLog.created_at < day_end
        ).scalar() or 0
        daily_stats.append({
            "date": day_start.strftime("%m-%d"),
            "inquiries": inquiries,
            "ai_calls": ai_calls,
        })

    return success_response(data={
        "period": f"{month_start.strftime('%Y-%m')}",
        "daily_stats": daily_stats,
        "summary": {
            "total_inquiries": sum(d["inquiries"] for d in daily_stats),
            "total_ai_calls": sum(d["ai_calls"] for d in daily_stats),
        },
        "generated_at": now.isoformat(),
    })


@router.get("/export/csv")
def export_csv(
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_super_admin),
    type: str = Query("inquiries", pattern="^(inquiries|users|ai_logs)$"),
):
    """导出 CSV 数据"""
    from app.core.data_export_guard import assert_export_allowed
    assert_export_allowed(
        db,
        admin,
        request,
        export_kind=f"super_admin_{type}_csv",
        scope="platform",
    )
    if type == "inquiries":
        rows = db.query(Inquiry).order_by(Inquiry.created_at.desc()).limit(1000).all()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "姓名", "电话", "邮箱", "产品", "留言", "时间"])
        for r in rows:
            writer.writerow([str(r.id), r.name, r.phone, r.email, r.product, r.message,
                             r.created_at.isoformat() if r.created_at else ""])

    elif type == "users":
        rows = db.query(User).order_by(User.created_at.desc()).limit(1000).all()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "用户名", "邮箱", "角色", "状态", "创建时间"])
        for r in rows:
            writer.writerow([str(r.id), r.username, r.email, r.role,
                             "启用" if r.is_active else "禁用",
                             r.created_at.isoformat() if r.created_at else ""])

    elif type == "ai_logs":
        rows = db.query(AIUsageLog).order_by(AIUsageLog.created_at.desc()).limit(1000).all()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["模型", "任务类型", "Token数", "成功", "耗时ms", "时间"])
        for r in rows:
            writer.writerow([r.model_name, r.task_type, r.total_tokens or "0",
                             "是" if r.success else "否", r.duration_ms or "0",
                             r.created_at.isoformat() if r.created_at else ""])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv; charset=utf-8-sig",
        headers={"Content-Disposition": f"attachment; filename={type}_export.csv"},
    )


def _get_ai_weekly_stats(db: Session, since: datetime) -> dict:
    """_get_ai_weekly_stats。

    参数说明：
    :param db: 参数 db
    :param since: 参数 since
    :return: 返回处理结果。
    """
    total = db.query(func.count(AIUsageLog.id)).filter(AIUsageLog.created_at >= since).scalar() or 0
    success = db.query(func.count(AIUsageLog.id)).filter(
        AIUsageLog.created_at >= since, AIUsageLog.success == True
    ).scalar() or 0
    return {
        "total_calls": total,
        "success_calls": success,
        "success_rate": round(success / total * 100, 1) if total else 0,
    }
