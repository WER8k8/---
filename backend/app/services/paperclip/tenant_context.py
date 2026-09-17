# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Paperclip 租户业务上下文 — 聚合产品/视频/询盘/行业数据供 220 个 Agent 使用。

每个租户的 220 个 Agent 都通过此模块获取完整的业务上下文，
确保 Agent 越用越懂客户的产品行业。
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def build_tenant_business_context(db: Session, tenant_id: str) -> dict[str, Any]:
    """聚合租户完整业务上下文，供 Agent 执行任务时使用。

    返回结构：
    {
        "tenant": {name, domain, plan, status},
        "products": {total, top_products, categories, primary_product},
        "videos": {total, recent_titles},
        "inquiries": {total, this_week, pending, top_sources, recent_messages},
        "industry": {category, location, belt_info},
        "content": {articles, publish_tasks},
        "learnings": {accumulated_knowledge}
    }
    """
    ctx: dict[str, Any] = {"tenant_id": tenant_id}
    # ── 租户基本信息 ──
    ctx["tenant"] = _build_tenant_info(db, tenant_id)
    # ── 产品目录 ──
    ctx["products"] = _build_product_context(db, tenant_id)
    # ── 视频内容 ──
    ctx["videos"] = _build_video_context(db, tenant_id)
    # ── 询盘数据 ──
    ctx["inquiries"] = _build_inquiry_context(db, tenant_id)
    # ── 行业/产业带 ──
    ctx["industry"] = _build_industry_context(db, tenant_id)
    # ── 内容发布 ──
    ctx["content"] = _build_content_context(db, tenant_id)
    # ── 积累的认知（越用越懂） ──
    ctx["learnings"] = _build_learnings(db, tenant_id)
    return ctx


def build_agent_mission_prompt(db: Session, tenant_id: str) -> str:
    """为 Agent 构建完整的使命提示词，包含租户业务上下文。

    每个 Agent 执行任务时都会带上这段上下文，
    确保 Agent 了解客户的产品、行业、目标市场。
    """
    ctx = build_tenant_business_context(db, tenant_id)
    t = ctx.get("tenant", {})
    p = ctx.get("products", {})
    v = ctx.get("videos", {})
    i = ctx.get("inquiries", {})
    ind = ctx.get("industry", {})
    c = ctx.get("content", {})
    learn = ctx.get("learnings", {})
    lines = [
        "## 客户业务背景",
        f"- 公司：{t.get('name', '未知')}",
        f"- 主营产品：{p.get('primary_product', '未设置')}",
        f"- 产品品类：{ind.get('category', '未分类')}",
        f"- 产地/区域：{ind.get('location', '未设置')}",
        f"- 产品数量：{p.get('total', 0)} 个",
    ]
    if p.get("top_products"):
        lines.append("- 核心产品：")
        for prod in p["top_products"][:5]:
            lines.append(f"  · {prod['name']}（{prod.get('category', '')}）")

    if v.get("total"):
        lines.append(f"- 视频数量：{v['total']} 个")

    if i.get("total"):
        lines.append(f"- 累计询盘：{i['total']} 条，本周 {i.get('this_week', 0)} 条，待处理 {i.get('pending', 0)} 条")
        if i.get("top_sources"):
            lines.append(f"- 询盘来源：{', '.join(i['top_sources'][:3])}")

    if c.get("articles"):
        lines.append(f"- 已发内容：{c['articles']} 篇")

    if ind.get("belt_info"):
        belt = ind["belt_info"]
        lines.append(f"- 产业带：{belt.get('name', '')}（{belt.get('province', '')}）")
        if belt.get("export_angle"):
            lines.append(f"- 出口优势：{belt['export_angle']}")

    if learn.get("key_insights"):
        lines.append("- 积累认知：")
        for insight in learn["key_insights"][:5]:
            lines.append(f"  · {insight}")

    lines.append("")
    lines.append("## 执行要求")
    lines.append("基于以上客户业务背景，精准执行任务。所有输出必须贴合客户的产品和行业。")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 内部构建函数
# ---------------------------------------------------------------------------

def _build_tenant_info(db: Session, tenant_id: str) -> dict[str, Any]:
    """租户基本信息。"""
    try:
        from app.models.tenant import Tenant
        t = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not t:
            return {"name": "未知", "domain": "", "plan": "", "status": ""}
        return {
            "name": t.name or "",
            "domain": t.domain or "",
            "plan": str(getattr(t, "plan_id", "")),
            "status": t.status or "",
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
    except Exception:
        return {"name": "", "domain": "", "plan": "", "status": ""}


def _build_product_context(db: Session, tenant_id: str) -> dict[str, Any]:
    """产品目录上下文。"""
    result: dict[str, Any] = {"total": 0, "top_products": [], "categories": [], "primary_product": ""}
    try:
        from app.models.product import Product, Category
        # 产品总数
        total = db.query(func.count(Product.id)).filter(
            Product.is_active.is_(True),
        ).scalar() or 0
        result["total"] = total
        # 热门产品（按浏览量）
        products = db.query(Product).filter(
            Product.is_active.is_(True),
        ).order_by(Product.view_count.desc()).limit(8).all()
        result["top_products"] = [
            {
                "name": p.name,
                "category": str(p.category_id or ""),
                "description": (p.description or "")[:200],
                "specs": p.specifications_text or "",
                "view_count": p.view_count or 0,
            }
            for p in products
        ]
        # 分类
        cats = db.query(Category).filter(Category.is_active.is_(True)).limit(20).all()
        result["categories"] = [c.name for c in cats]
        # 主营产品（从租户设置）
        try:
            from app.models.tenant import Tenant
            from app.services.tenant_product_context import resolve_tenant_product_hint
            t = db.query(Tenant).filter(Tenant.id == tenant_id).first()
            if t:
                result["primary_product"] = resolve_tenant_product_hint(t)
        except Exception:
            pass

        # 产品画像（如果已构建）
        try:
            from app.services.tenant_product_profile_service import get_tenant_product_profile
            from app.models.tenant import Tenant
            t = db.query(Tenant).filter(Tenant.id == tenant_id).first()
            if t:
                profile = get_tenant_product_profile(db, t)
                if profile:
                    result["profile"] = {
                        "primary_product": profile.get("primary_product", ""),
                        "product_category": profile.get("product_category", ""),
                        "spec_summary": profile.get("spec_summary_zh", ""),
                        "application_summary": profile.get("application_summary_zh", ""),
                        "export_angle": profile.get("export_angle_en", ""),
                    }
        except Exception:
            pass

    except Exception as exc:
        logger.debug("build_product_context failed: %s", exc)
    return result


def _build_video_context(db: Session, tenant_id: str) -> dict[str, Any]:
    """视频内容上下文。"""
    result: dict[str, Any] = {"total": 0, "recent_titles": []}
    try:
        from app.models.media_factory import MediaRenderTask
        total = db.query(func.count(MediaRenderTask.id)).filter(
            MediaRenderTask.tenant_id == tenant_id,
            MediaRenderTask.status == "success",
        ).scalar() or 0
        result["total"] = total
        recent = db.query(MediaRenderTask).filter(
            MediaRenderTask.tenant_id == tenant_id,
            MediaRenderTask.status == "success",
        ).order_by(MediaRenderTask.created_at.desc()).limit(5).all()
        result["recent_titles"] = [v.title or "未命名" for v in recent]
    except Exception as exc:
        logger.debug("build_video_context failed: %s", exc)
    return result


def _build_inquiry_context(db: Session, tenant_id: str) -> dict[str, Any]:
    """询盘数据上下文。"""
    result: dict[str, Any] = {
        "total": 0, "this_week": 0, "pending": 0,
        "top_sources": [], "recent_messages": [],
    }
    try:
        from app.models.inquiry import Inquiry
        # 总询盘
        total = db.query(func.count(Inquiry.id)).filter(
            Inquiry.tenant_id == tenant_id,
        ).scalar() or 0
        result["total"] = total
        # 本周
        week_ago = datetime.now(timezone.utc) - timedelta(days=7)
        this_week = db.query(func.count(Inquiry.id)).filter(
            Inquiry.tenant_id == tenant_id,
            Inquiry.created_at >= week_ago,
        ).scalar() or 0
        result["this_week"] = this_week
        # 待处理
        pending = db.query(func.count(Inquiry.id)).filter(
            Inquiry.tenant_id == tenant_id,
            Inquiry.status == "pending",
        ).scalar() or 0
        result["pending"] = pending
        # 来源渠道统计
        sources = db.query(
            Inquiry.source_channel, func.count(Inquiry.id)
        ).filter(
            Inquiry.tenant_id == tenant_id,
            Inquiry.source_channel.isnot(None),
        ).group_by(Inquiry.source_channel).order_by(func.count(Inquiry.id).desc()).limit(5).all()
        result["top_sources"] = [s[0] for s in sources if s[0]]
        # 最近询盘消息（用于理解客户需求趋势）
        recent = db.query(Inquiry).filter(
            Inquiry.tenant_id == tenant_id,
        ).order_by(Inquiry.created_at.desc()).limit(5).all()
        result["recent_messages"] = [
            {
                "product": r.product or "",
                "message": (r.message or "")[:150],
                "source": r.source_channel or "",
            }
            for r in recent
        ]
    except Exception as exc:
        logger.debug("build_inquiry_context failed: %s", exc)
    return result


def _build_industry_context(db: Session, tenant_id: str) -> dict[str, Any]:
    """行业/产业带上下文。"""
    result: dict[str, Any] = {"category": "", "location": "", "belt_info": {}}
    try:
        from app.models.tenant import Tenant
        t = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not t:
            return result

        settings = {}
        try:
            settings = json.loads(t.settings or "{}") if isinstance(t.settings, str) else (t.settings or {})
        except (json.JSONDecodeError, TypeError):
            pass

        onboarding = settings.get("onboarding", {})
        result["primary_product"] = onboarding.get("primary_product", "")
        result["location"] = onboarding.get("location_hint", "")
        profile = onboarding.get("product_profile", {})
        if profile:
            result["category"] = profile.get("product_category", "")
            belt = profile.get("industry_belt", {})
            if belt:
                result["belt_info"] = {
                    "name": belt.get("name", ""),
                    "province": belt.get("province", ""),
                    "export_angle": belt.get("export_angle", ""),
                    "typical_products": belt.get("typical_products", []),
                    "spec_focus": belt.get("spec_focus", []),
                }
    except Exception as exc:
        logger.debug("build_industry_context failed: %s", exc)
    return result


def _build_content_context(db: Session, tenant_id: str) -> dict[str, Any]:
    """内容发布上下文。"""
    result: dict[str, Any] = {"articles": 0, "publish_tasks": 0}
    try:
        from app.models.content_master import ContentMaster
        articles = db.query(func.count(ContentMaster.id)).filter(
            ContentMaster.tenant_id == tenant_id,
        ).scalar() or 0
        result["articles"] = articles
    except Exception:
        pass

    try:
        from app.models.publish_task import PublishTask
        tasks = db.query(func.count(PublishTask.id)).filter(
            PublishTask.tenant_id == tenant_id,
        ).scalar() or 0
        result["publish_tasks"] = tasks
    except Exception:
        pass
    return result


def _build_learnings(db: Session, tenant_id: str) -> dict[str, Any]:
    """从历史数据中积累的认知 — 越用越懂客户。

    分析询盘趋势、热门产品、客户画像等，
    形成结构化认知供 Agent 使用。
    """
    result: dict[str, Any] = {"key_insights": [], "hot_products": [], "buyer_profiles": []}
    try:
        from app.models.inquiry import Inquiry
        # 热门询盘产品
        hot = db.query(
            Inquiry.product, func.count(Inquiry.id)
        ).filter(
            Inquiry.tenant_id == tenant_id,
            Inquiry.product.isnot(None),
            Inquiry.product != "",
        ).group_by(Inquiry.product).order_by(func.count(Inquiry.id).desc()).limit(5).all()
        result["hot_products"] = [{"product": h[0], "count": h[1]} for h in hot]
        # 买家地区分布
        from app.models.site_analytics import SiteAnalyticsEvent
        regions = db.query(
            SiteAnalyticsEvent.visitor_country, func.count(SiteAnalyticsEvent.id)
        ).filter(
            SiteAnalyticsEvent.tenant_id == tenant_id,
            SiteAnalyticsEvent.visitor_country.isnot(None),
        ).group_by(SiteAnalyticsEvent.visitor_country).order_by(
            func.count(SiteAnalyticsEvent.id).desc()
        ).limit(5).all()
        result["buyer_profiles"] = [{"country": r[0], "visits": r[1]} for r in regions if r[0]]
        # 生成洞察
        insights = []
        if result["hot_products"]:
            top = result["hot_products"][0]
            insights.append(f"最受关注产品是「{top['product']}」（{top['count']} 次询盘），应重点推广")
        if result["buyer_profiles"]:
            top_region = result["buyer_profiles"][0]
            insights.append(f"主要访客来源：{top_region['country']}（{top_region['visits']} 次），应针对性优化内容")
        if result["hot_products"] and len(result["hot_products"]) >= 3:
            names = [h["product"] for h in result["hot_products"][:3]]
            insights.append(f"热门产品组合：{' / '.join(names)}，可打包推广")

        result["key_insights"] = insights
    except Exception as exc:
        logger.debug("build_learnings failed: %s", exc)
    return result
