# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""SEO 报告导出。"""

from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.response import success_response
from app.core.security import get_current_user
from app.models.seo import Keyword, KeywordRanking, SiteAudit
from app.models.user import User
from app.services.seo_report_service import build_seo_report_html

router = APIRouter()


@router.get("/report/export")
def export_seo_report(
    format: str = Query("html", pattern="^(html|json)$"),
    site_url: str = Query("", max_length=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """export_seo_report。

    参数说明：
    :param format: 参数 format
    :param site_url: 参数 site_url
    :param db: 参数 db
    :param current_user: 参数 current_user
    :return: 返回处理结果。
    """
    if current_user.role not in ("admin", "super_admin", "tenant_admin"):
        from app.core.response import error_response
        return error_response(403, "权限不足")

    total_kw = db.query(func.count(Keyword.id)).scalar() or 0
    ranked = (
        db.query(func.count(func.distinct(KeywordRanking.keyword)))
        .filter(KeywordRanking.current_position.isnot(None))
        .scalar()
        or 0
    )
    top = (
        db.query(func.count(KeywordRanking.id))
        .filter(
            KeywordRanking.current_position.isnot(None),
            KeywordRanking.current_position <= 10,
        )
        .scalar()
        or 0
    )
    latest_audit = (
        db.query(SiteAudit).order_by(SiteAudit.created_at.desc()).first()
    )
    metrics = {
        "total_keywords": total_kw,
        "ranked_keywords": ranked,
        "top_ranking": top,
        "traffic_estimate": f"{max(ranked * 120, 0)}",
        "audit_score": getattr(latest_audit, "score", None) or 85,
        "issues": getattr(latest_audit, "total_issues", None) or 0,
        "warnings": getattr(latest_audit, "warning_issues", None) or 0,
        "top_keywords": [],
    }
    if format == "json":
        return success_response(data={"metrics": metrics, "site_url": site_url})

    html = build_seo_report_html(metrics, site_url=site_url)
    return HTMLResponse(content=html, media_type="text/html; charset=utf-8")
