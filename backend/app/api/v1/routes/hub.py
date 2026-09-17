# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""公开内容枢纽 API — 租户站聚合页只读数据"""

import os
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.content_master import ContentMaster
from app.models.tenant import Tenant
from app.models.user import User
from app.services.hub_urls import build_hub_page_url
from app.services.tenant_settings_service import hide_hub_backlink


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = ""

router = APIRouter(prefix="/hub", tags=["内容枢纽"])


@router.get("/pages/{tenant_slug}/{content_id}")
def get_hub_page(
    tenant_slug: str,
    content_id: str,
    db: Session = Depends(get_db),
):
    """按租户 slug（domain）与内容 ID 返回枢纽展示字段。"""
    tenant = (
        db.query(Tenant)
        .filter(Tenant.domain == tenant_slug, Tenant.is_active)
        .first()
    )
    if not tenant:
        return error_response(404, "租户不存在")

    row = (
        db.query(ContentMaster)
        .filter(
            ContentMaster.id == content_id,
            ContentMaster.tenant_id == tenant.id,
            ContentMaster.show_on_hub.is_(True),
        )
        .first()
    )
    if not row:
        return error_response(404, "内容不存在或未公开")

    return success_response(
        data={
            "title": row.title,
            "hub_summary": row.hub_summary,
            "tenant_canonical_url": row.tenant_canonical_url,
            "hub_url": build_hub_page_url(tenant, content_id),
            "hide_hub_backlink": hide_hub_backlink(tenant),
        }
    )


@router.get("/sitemap.xml", response_class=Response)
def hub_sitemap_xml(db: Session = Depends(get_db)):
    """总站枢纽页 sitemap（仅 show_on_hub 的母版）。"""
    rows = (
        db.query(ContentMaster, Tenant)
        .join(Tenant, ContentMaster.tenant_id == Tenant.id)
        .filter(ContentMaster.show_on_hub.is_(True), Tenant.is_active)
        .order_by(ContentMaster.updated_at.desc())
        .limit(5000)
        .all()
    )
    base = settings.SITE_URL.rstrip("/")
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for master, tenant in rows:
        loc = build_hub_page_url(tenant, master.id)
        lastmod = ""
        if master.updated_at:
            lastmod = master.updated_at.strftime("%Y-%m-%d")
        lines.append("  <url>")
        lines.append(f"    <loc>{loc}</loc>")
        if lastmod:
            lines.append(f"    <lastmod>{lastmod}</lastmod>")
        lines.append("  </url>")
    lines.append("</urlset>")
    xml = "\n".join(lines)
    return Response(content=xml, media_type="application/xml")


def _hub_url_count(db: Session) -> int:
    """
    处理 _hub_url_count 相关业务逻辑。

    :param db: 入参 (Session)。

    :return: 返回 int 类型的结果。
    """
    return (
        db.query(ContentMaster.id)
        .join(Tenant, ContentMaster.tenant_id == Tenant.id)
        .filter(ContentMaster.show_on_hub.is_(True), Tenant.is_active)
        .count()
    )


@router.get("/search-console/checklist")
def hub_search_console_checklist(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """GSC 提交检查清单（sitemap URL + 条目数）。"""
    if current_user.role not in ("admin", "super_admin"):
        return error_response(403, "仅超管可访问")
    base = settings.SITE_URL.rstrip("/")
    api_base = os.getenv("PUBLIC_API_BASE", base).rstrip("/")
    sitemap_url = f"{api_base}/api/v1/hub/sitemap.xml"
    return success_response(
        data={
            "sitemap_url": sitemap_url,
            "url_count": _hub_url_count(db),
            "steps": [
                "在 Google Search Console 添加资源（总站域名）",
                f"提交 Sitemap：{sitemap_url}",
                "确认 /industry/{{tenantSlug}}/{{contentId}} 前台页可 200",
            ],
            "gsc_api_enabled": bool(os.getenv("GSC_SERVICE_ACCOUNT_JSON")),
        }
    )


@router.post("/search-console/ping")
def hub_search_console_ping(
    dry_run: bool = Query(True, description="未配置 GSC API 时仅返回待提交信息"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """触发枢纽 sitemap 推送登记（配置 GSC_SERVICE_ACCOUNT_JSON 后可扩展为真实 API）。"""
    if current_user.role not in ("admin", "super_admin"):
        return error_response(403, "仅超管可访问")
    count = _hub_url_count(db)
    base = settings.SITE_URL.rstrip("/")
    api_base = os.getenv("PUBLIC_API_BASE", base).rstrip("/")
    sitemap_url = f"{api_base}/api/v1/hub/sitemap.xml"
    payload = {
        "sitemap_url": sitemap_url,
        "url_count": count,
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "mode": "dry_run" if dry_run or not os.getenv("GSC_SERVICE_ACCOUNT_JSON") else "api",
    }
    if payload["mode"] == "dry_run":
        payload["message"] = "未配置 GSC API，请按 checklist 在 Search Console 手动提交"
    else:
        payload["message"] = "GSC API 占位：请接入 google-api-python-client 后在此提交"
    return success_response(data=payload, message="枢纽 sitemap 登记完成")
