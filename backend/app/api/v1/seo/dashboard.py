import json
import re
from datetime import datetime, timedelta, timezone
from ipaddress import ip_address, ip_network
from typing import Optional, Tuple
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.response import success_response
from app.core.security import optional_auth
from app.models.content import ContentPage
from app.models.seo_metadata import SeoMetadata
from app.models.inquiry import Inquiry
from app.models.product import Product
from app.models.seo import (AiOptimizationLog, Keyword, KeywordRanking,
                            LlmsConfig, SiteAudit)
from app.models.user import User
from app.services.finance_honesty import is_excluded_inquiry
from app.services.seo_analyzer import SeoAnalyzer
from app.services.site_audit import SiteAuditEngine

router = APIRouter()


PRIVATE_NETWORKS = [
    ip_network("127.0.0.0/8"),
    ip_network("10.0.0.0/8"),
    ip_network("172.16.0.0/12"),
    ip_network("192.168.0.0/16"),
    ip_network("::1/128"),
    ip_network("fc00::/7"),
]

BLOCKED_HOSTS = {
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "[::1]",
    "metadata.google.internal"}


def validate_audit_url(url: str) -> str:
    """validate_audit_url。

    参数说明：
    :param url: 参数 url
    :return: 返回处理结果。
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise HTTPException(status_code=400, detail="仅支持 http/https 协议的URL")
    hostname = parsed.hostname.lower()
    if hostname in BLOCKED_HOSTS:
        raise HTTPException(status_code=400, detail="不允许审计内部地址")
    try:
        ip = ip_address(hostname)
        for net in PRIVATE_NETWORKS:
            if ip in net:
                raise HTTPException(status_code=400, detail="不允许审计内网地址")
    except ValueError:
        if re.search(
            r"(10\.|172\.(1[6-9]|2\d|3[01])\.|192\.168\.|127\.)",
                hostname):
            raise HTTPException(status_code=400, detail="不允许审计内网地址")
    return url


class AuditRunRequest(BaseModel):
    url: str = Field(..., description="要审计的页面URL")
    audit_type: str = Field(default="full", pattern="^(quick|full)$")


def _keyword_stats(db: Session) -> Tuple[int, int, Optional[float]]:
    """_keyword_stats。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    total_kw = db.query(
        func.count(
            Keyword.id)).filter(
        Keyword.is_active).scalar() or 0
    ranked_kw = (
        db.query(
            func.count(
                Keyword.id)).filter(
            Keyword.is_active,
            Keyword.current_ranking.isnot(None)).scalar() or 0)
    avg_rank_result = (
        db.query(func.avg(Keyword.current_ranking))
        .filter(Keyword.is_active, Keyword.current_ranking.isnot(None))
        .scalar()
    )
    avg_rank = round(float(avg_rank_result),
                     1) if avg_rank_result is not None else None

    if total_kw == 0:
        total_kw = db.query(
            func.count(
                func.distinct(
                    KeywordRanking.keyword))).scalar() or 0
        ranked_kw = (db.query(func.count(KeywordRanking.id)).filter(
            KeywordRanking.current_position.isnot(None)).scalar() or 0)
        avg_rr = (
            db.query(func.avg(KeywordRanking.current_position))
            .filter(KeywordRanking.current_position.isnot(None))
            .scalar()
        )
        avg_rank = round(float(avg_rr), 1) if avg_rr is not None else avg_rank

    return int(total_kw), int(ranked_kw), avg_rank


def _keyword_trend(db: Session, days: int) -> list[dict]:
    """_keyword_trend。

    参数说明：
    :param db: 参数 db
    :param days: 参数 days
    :return: 返回处理结果。
    """
    since = datetime.now(timezone.utc) - timedelta(days=days)
    rows = (
        db.query(
            func.date(KeywordRanking.last_checked_at),
            func.avg(KeywordRanking.current_position),
        )
        .filter(
            KeywordRanking.last_checked_at.isnot(None),
            KeywordRanking.last_checked_at >= since,
            KeywordRanking.current_position.isnot(None),
        )
        .group_by(func.date(KeywordRanking.last_checked_at))
        .order_by(func.date(KeywordRanking.last_checked_at))
        .all()
    )
    row_map = {str(r[0]): float(r[1])
               for r in rows if r[0] is not None and r[1] is not None}

    avg_fallback = (
        db.query(
            func.avg(
                KeywordRanking.current_position)).filter(
            KeywordRanking.current_position.isnot(None)).scalar())
    fb = round(float(avg_fallback), 1) if avg_fallback is not None else None
    out: list[dict] = []
    for i in range(days - 1, -1, -1):
        d = (datetime.now(timezone.utc) - timedelta(days=i)).date().isoformat()
        # 无当日探测记录时用 null，禁止用全局均值冒充日趋势
        v = row_map.get(d)
        out.append({"date": d, "avg_rank": v})
    return out


def _page_seo_distribution(db: Session) -> list[dict]:
    """_page_seo_distribution。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    n_pages = db.query(
        func.count(
            ContentPage.id)).filter(
        ContentPage.is_active).scalar() or 0
    published = (
        db.query(func.count(ContentPage.id))
        .filter(ContentPage.is_active, ContentPage.status == "published")
        .scalar()
        or 0
    )
    full_seo = (
        db.query(func.count(SeoMetadata.id))
        .filter(
            SeoMetadata.resource_type.in_(("page", "content_page")),
            SeoMetadata.meta_title.isnot(None),
            SeoMetadata.meta_title != "",
            SeoMetadata.meta_description.isnot(None),
            SeoMetadata.meta_description != "",
        )
        .scalar()
        or 0
    )
    since = datetime.now(timezone.utc) - timedelta(days=10)
    in_progress = (
        db.query(
            func.count(
                func.distinct(
                    AiOptimizationLog.resource_id))) .filter(
            AiOptimizationLog.created_at >= since,
            AiOptimizationLog.resource_type.in_(
                ("page",
                 "content_page",
                 "content")),
        ) .scalar() or 0)

    optimized = min(int(full_seo), int(n_pages)) if n_pages else 0
    in_progress = min(int(in_progress), max(0, n_pages - optimized))
    pending = max(0, min(published - optimized,
                  n_pages - optimized - in_progress))
    none = max(0, n_pages - optimized - in_progress - pending)
    total = optimized + pending + in_progress + none or 1
    def pct(n: int) -> float:
        """pct。

        参数说明：
        :param n: 参数 n
        :return: 返回处理结果。
        """
        return round(100.0 * n / total, 1)

    return [
        {"type": "已优化", "count": optimized, "percent": pct(optimized)},
        {"type": "待优化", "count": pending, "percent": pct(pending)},
        {"type": "优化中", "count": in_progress, "percent": pct(in_progress)},
        {"type": "未优化", "count": none, "percent": pct(none)},
    ]


def _real_inquiries(db: Session, *, tenant_id: Optional[str] = None) -> list[Inquiry]:
    """排除 dev_seed / E2E / 冒烟询盘，避免数据看板误计。"""
    q = db.query(Inquiry).filter(Inquiry.is_active.is_(True))
    if tenant_id:
        q = q.filter(Inquiry.tenant_id == tenant_id)
    return [row for row in q.all() if not is_excluded_inquiry(row)]


def _build_dashboard_recent_inquiries(real_inq_rows):
    """取最近 6 条询盘并格式化。"""
    recent_inq = sorted(
        real_inq_rows,
        key=lambda r: r.created_at or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )[:6]
    return [
        {
            "company": r.name,
            "product": r.product or "",
            "contact": r.phone or r.email or "",
            "time": r.created_at.isoformat() if r.created_at else "",
            "status": "new" if r.status == "pending" else "processed",
        }
        for r in recent_inq
    ]


def _build_dashboard_hot_keywords(db: Session):
    """构建热门关键词列表（优先 KeywordRanking，回退 Keyword）。"""
    hot_kw_rows = db.query(KeywordRanking).order_by(
        KeywordRanking.search_volume.desc()).limit(6).all()
    if not hot_kw_rows:
        hot_kw_rows = (
            db.query(Keyword).filter(
                Keyword.is_active).order_by(
                Keyword.search_volume.desc()).limit(6).all())
        return [
            {
                "name": k.keyword,
                "rank": k.current_ranking or 0,
                "search": k.search_volume or 0,
                "change": 0,
            }
            for k in hot_kw_rows
        ]
    hot_keywords = []
    for r in hot_kw_rows:
        cur = r.current_position if r.current_position is not None else 0
        prev = r.previous_position
        if prev is not None and r.current_position is not None:
            change = int(prev - cur)
        else:
            change = 0
        hot_keywords.append(
            {
                "name": r.keyword,
                "rank": cur,
                "search": r.search_volume or 0,
                "change": change,
            }
        )
    return hot_keywords


def _build_dashboard_product_stats(db: Session, real_inq_rows):
    """按询盘分布构建 Top 产品转化统计。"""
    inq_by_product: dict[str, int] = {}
    for row in real_inq_rows:
        name = (row.product or "").strip()
        if not name:
            continue
        inq_by_product[name] = inq_by_product.get(name, 0) + 1

    top_products_orm = (
        db.query(Product)
        .options(joinedload(Product.category))
        .filter(Product.is_active)
        .order_by(Product.view_count.desc())
        .limit(8)
        .all()
    )
    product_stats = []
    for p in top_products_orm:
        views = p.view_count or 0
        iq = int(inq_by_product.get(p.name, 0))
        conversion = round(100.0 * iq / views, 1) if views else 0.0
        product_stats.append(
            {
                "name": p.name,
                "category": p.category.name if p.category else "",
                "views": views,
                "inquiries": iq,
                "conversion": conversion,
            }
        )
    return product_stats


@router.get("/dashboard")
def get_seo_dashboard(
    time_range: str = Query("week", alias="range"),
    db: Session = Depends(get_db),
):
    """管理端数据概览：聚合 SEO、产品、询盘、内容（与 `/api/v1/analytics/dashboard` 互补，统一前端入口）。"""
    if time_range not in ("today", "week", "month"):
        time_range = "week"
    trend_days = {"today": 7, "week": 7, "month": 30}[time_range]
    total_products = db.query(
        func.count(
            Product.id)).filter(
        Product.is_active).scalar() or 0
    real_inq_rows = _real_inquiries(db)
    raw_inquiry_count = db.query(
        func.count(
            Inquiry.id)).filter(
        Inquiry.is_active).scalar() or 0
    total_inquiries = len(real_inq_rows)
    total_keywords, ranked_keywords, avg_rank = _keyword_stats(db)
    ai_optimized_pages = db.query(
        func.count(
            func.distinct(
                AiOptimizationLog.resource_id))).scalar() or 0

    last_audit = db.query(SiteAudit).order_by(
        SiteAudit.created_at.desc()).first()
    last_audit_score = float(
        last_audit.score) if last_audit and last_audit.score is not None else None

    llms_txt_generated = (
        db.query(func.count(ContentPage.id))
        .filter(ContentPage.slug == "llms-txt", ContentPage.is_active)
        .scalar()
        or 0
    ) > 0
    if not llms_txt_generated:
        llms_txt_generated = (
            db.query(
                func.count(
                    LlmsConfig.id)).filter(
                LlmsConfig.is_active).scalar() or 0) > 0

    keyword_trend = _keyword_trend(db, trend_days)
    page_rows = _page_seo_distribution(db)
    recent_inquiries = _build_dashboard_recent_inquiries(real_inq_rows)
    hot_keywords = _build_dashboard_hot_keywords(db)
    product_stats = _build_dashboard_product_stats(db, real_inq_rows)
    payload = {
        "total_products": int(total_products),
        "total_inquiries": int(total_inquiries),
        "total_keywords": int(total_keywords),
        "ranked_keywords": int(ranked_keywords),
        "avg_rank": avg_rank,
        "ai_optimized_pages": int(ai_optimized_pages),
        "llms_txt_generated": llms_txt_generated,
        "last_audit_score": last_audit_score,
        "keyword_trend": keyword_trend,
        "page_coverage": page_rows,
        "recent_inquiries": recent_inquiries,
        "hot_keywords": hot_keywords,
        "product_stats": product_stats,
        "data_honesty": {
            "has_production_activity": bool(
                total_products or total_inquiries or total_keywords or product_stats
            ),
            "excluded_inquiries": max(0, int(raw_inquiry_count) - int(total_inquiries)),
            "raw_inquiries": int(raw_inquiry_count),
        },
    }
    return success_response(data=payload)


@router.get("/keyword-ranking/{keyword_id}")
def get_keyword_ranking(keyword_id: str, db: Session = Depends(get_db)):
    """get_keyword_ranking。

    参数说明：
    :param keyword_id: 参数 keyword_id
    :param db: 参数 db
    :return: 返回处理结果。
    """
    analyzer = SeoAnalyzer(db)
    return analyzer.analyze_keyword_rankings(keyword_id)


@router.get("/keyword-groups")
def get_keyword_groups(db: Session = Depends(get_db)):
    """get_keyword_groups。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    analyzer = SeoAnalyzer(db)
    return analyzer.get_keyword_groups()


@router.get("/seo-pages-summary")
def get_seo_pages_summary(db: Session = Depends(get_db)):
    """get_seo_pages_summary。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    analyzer = SeoAnalyzer(db)
    return analyzer.get_seo_pages_summary()


@router.post("/run-audit")
async def run_audit(
        req: AuditRunRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(optional_auth)):
    """run_audit。

    参数说明：
    :param req: 参数 req
    :param db: 参数 db
    :param current_user: 参数 current_user
    :return: 返回处理结果。
    """
    validate_audit_url(req.url)
    engine = SiteAuditEngine()
    result = await engine.run_audit(url=req.url, audit_type=req.audit_type)
    now = datetime.now(timezone.utc)
    report_data = json.dumps(
        {
            "url": req.url,
            "issues": result.get("issues", []),
            "recommendations": result.get("recommendations", []),
        },
        ensure_ascii=False,
        default=str,
    )
    audit_record = SiteAudit(
        status="completed",
        audit_type=req.audit_type,
        score=result.get("score", 0),
        total_issues=result.get("total_issues", 0),
        critical_issues=result.get("critical_issues", 0),
        warning_issues=result.get("warning_issues", 0),
        report_data=report_data,
        completed_at=now,
    )
    db.add(audit_record)
    db.commit()
    db.refresh(audit_record)
    return {
        "id": str(audit_record.id),
        "url": req.url,
        "status": "completed",
        "score": result.get("score", 0),
        "total_issues": result.get("total_issues", 0),
        "critical_issues": result.get("critical_issues", 0),
        "warning_issues": result.get("warning_issues", 0),
        "dimension_scores": result.get("dimension_scores", {}),
        "issues": result.get("issues", []),
        "recommendations": result.get("recommendations", []),
    }
