# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Robots.txt 路由端点 — 支持 Googlebot 与多租户动态 Sitemap 适配。"""

from fastapi import APIRouter, Request, Response
from app.core.config import settings

ROUTE_PREFIX = ""
ROUTE_TAGS = ["SEO元数据"]

router = APIRouter()


def build_robots_txt(base_url: str) -> str:
    """构建符合 Googlebot 规范的 robots.txt 内容。
    包含搜索引擎爬虫优化规则、Disallow 私密路径、以及动态 Sitemap 定位。
    """
    clean_base = base_url.rstrip("/")
    return f"""# YouDing AEOS Search Engine Crawl Budget Directives
User-agent: Googlebot
Allow: /
Allow: /products
Allow: /products/*
Allow: /cases
Allow: /cases/*
Allow: /news
Allow: /news/*
Allow: /about
Allow: /contact
Allow: /tenant/*
Disallow: /api/
Disallow: /admin/
Disallow: /client/
Disallow: /partner/
Disallow: /agent/
Disallow: /static/temp/
Disallow: /*?*sort=
Disallow: /*?*page=

User-agent: Googlebot-Image
Allow: /uploads/
Allow: /images/
Allow: /products/

User-agent: Mediapartners-Google
Allow: /

User-agent: Bingbot
Allow: /
Disallow: /api/
Disallow: /admin/
Disallow: /client/
Disallow: /partner/
Disallow: /agent/

User-agent: *
Allow: /
Disallow: /api/
Disallow: /admin/
Disallow: /client/
Disallow: /partner/
Disallow: /agent/

# Dynamic Multi-Tenant Sitemaps & LLM Discovery
Sitemap: {clean_base}/sitemap.xml
Sitemap: {clean_base}/api/v1/sitemap.xml
"""


@router.get("/robots.txt", response_class=Response)
async def get_robots_txt(request: Request):
    """返回标准 robots.txt，根据当前请求 Host 动态计算 Sitemap 地址。"""
    host = request.headers.get("x-forwarded-host") or request.headers.get("host") or ""
    proto = request.headers.get("x-forwarded-proto") or request.url.scheme or "https"

    if host:
        base_url = f"{proto}://{host}"
    else:
        base_url = getattr(settings, "SITE_URL", "https://www.youdingjiancai.com")

    content = build_robots_txt(base_url)
    return Response(
        content=content,
        media_type="text/plain; charset=utf-8",
        headers={"Cache-Control": "public, max-age=86400, s-maxage=86400"},
    )
