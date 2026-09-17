# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""双栈集成状态 — FastAPI 主库 + SEO 矩阵 + 可选 Node seo-backend。"""

from __future__ import annotations

import os

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings


def _count_route_prefix(app, prefix: str) -> int:
    """_count_route_prefix。

    参数说明：
    :param app: 参数 app
    :param prefix: 参数 prefix
    :return: 返回处理结果。
    """
    return sum(
        1
        for r in app.routes
        if (getattr(r, "path", "") or "").startswith(prefix)
    )


def _build_acquisition_api_panel() -> dict:
    """获客渠道 API 配置状态面板"""
    ga4_configured = bool(os.getenv("NUXT_PUBLIC_GA4_MEASUREMENT_ID", ""))
    google_cse_configured = bool(settings.GOOGLE_CSE_API_KEY and settings.GOOGLE_CSE_CX)
    whatsapp_configured = bool(
        settings.WHATSAPP_ACCESS_TOKEN and settings.WHATSAPP_PHONE_NUMBER_ID
    )
    total = 3
    configured = sum([ga4_configured, google_cse_configured, whatsapp_configured])
    modules = [
        {
            "id": "ga4",
            "name": "Google Analytics 4",
            "status": "configured" if ga4_configured else "pending",
            "hint": "网站流量分析，判断哪个渠道来的访客有价值",
            "env_key": "NUXT_PUBLIC_GA4_MEASUREMENT_ID",
            "doc_link": "https://support.google.com/analytics/answer/9304153",
            "category": "流量分析",
        },
        {
            "id": "google_cse",
            "name": "Google Custom Search API",
            "status": "configured" if google_cse_configured else "pending",
            "hint": "Google 搜索获客，替换 Mock 用真实搜索结果开发客户",
            "env_key": "GOOGLE_CSE_API_KEY + GOOGLE_CSE_CX",
            "doc_link": "https://developers.google.com/custom-search/v1/introduction",
            "category": "获客搜索",
        },
        {
            "id": "whatsapp",
            "name": "WhatsApp Business Cloud API",
            "status": "configured" if whatsapp_configured else "pending",
            "hint": "WhatsApp 开发信发送，打开率 >90% 的外贸触达渠道",
            "env_key": "WHATSAPP_ACCESS_TOKEN + WHATSAPP_PHONE_NUMBER_ID",
            "doc_link": "https://developers.facebook.com/docs/whatsapp/cloud-api",
            "category": "消息触达",
        },
    ]
    status_label = "未开始"
    if configured == total:
        status_label = "全部就绪"
    elif configured > 0:
        status_label = "部分配置"

    overall_hint = (
        f"获客渠道 API {configured}/{total} 已配置。"
        + ("可以开始用真实数据判断渠道投入了！" if configured == total
           else "建议优先配置 Google CSE + WhatsApp，跑第一批真实客户线索。")
    )
    usage_tips = [
        "配置好 GA4 后，观察 1-2 周流量数据，看哪些国家/关键词带来的访客有询盘",
        "Google CSE 每天免费 100 次查询，建议先跑 3-5 个核心关键词测试线索质量",
        "WhatsApp 先从高意向客户发模板消息破冰，不要上来就群发，避免封号",
        "三个都配好后，可以跑 A/B 测试：邮件 vs WhatsApp 哪个回复率高",
    ]
    return {
        "id": "acquisition_apis",
        "name": "获客渠道 API 配置",
        "total": total,
        "configured": configured,
        "status_label": status_label,
        "overall_hint": overall_hint,
        "modules": modules,
        "usage_tips": usage_tips,
    }


def build_integrations_status(db: Session | None = None) -> dict:
    """build_integrations_status。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    from app.main import app
    seo_backend_url = os.getenv("SEO_BACKEND_URL", "http://localhost:3000").rstrip("/")
    matrix_prefix = f"{settings.API_V1_PREFIX}/seo-matrix"
    advanced_prefix = f"{settings.API_V1_PREFIX}/seo/"
    node_status = "not_configured"
    node_detail = None
    if seo_backend_url and "localhost:3000" not in seo_backend_url:
        try:
            with httpx.Client(timeout=3) as client:
                resp = client.get(f"{seo_backend_url}/api/v1/health")
                node_status = "connected" if resp.status_code == 200 else "degraded"
                node_detail = f"HTTP {resp.status_code}"
        except Exception as exc:
            node_status = "unreachable"
            node_detail = str(exc)[:200]

    return {
        "primary": "fastapi",
        "fastapi_routes": {
            "seo_matrix": _count_route_prefix(app, matrix_prefix),
            "seo_advanced": _count_route_prefix(app, advanced_prefix),
            "total_api": len([p for p in [getattr(r, "path", "") for r in app.routes] if p.startswith("/api")]),
        },
        "seo_backend": {
            "url": seo_backend_url,
            "status": node_status,
            "detail": node_detail,
            "proxy_path": f"{settings.API_V1_PREFIX}/super-admin/seo-proxy/",
        },
        "acquisition_panel": _build_acquisition_api_panel(),
        "guidance": [
            "新功能优先实现于 FastAPI（/api/v1/seo-matrix 与 /api/v1/seo/*）",
            "seo-backend 仅作历史矩阵 Node 服务，通过 super-admin/seo-proxy 代理",
            "生产环境请配置 SEO_BACKEND_URL 并监控 node_status",
        ],
    }
