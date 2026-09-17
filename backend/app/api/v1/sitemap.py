# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""动态多租户 Sitemap 路由端点 — 支持 Google Image/Video 扩展与 12 语种 xhtml:link hreflang。"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.case_study import CaseStudy
from app.models.content import ContentPage
from app.models.product import Product, ProductImage
from app.services.geo.geo_matrix_landing_service import COUNTRY_PROFILES

ROUTE_PREFIX = ""
ROUTE_TAGS = ["SEO站点地图"]
router = APIRouter()

SUPPORTED_LOCALES = [
    ("zh-CN", ""),
    ("en-US", "/en"),
    ("de-DE", "/de"),
    ("fr-FR", "/fr"),
    ("es-ES", "/es"),
    ("ar-SA", "/ar"),
    ("ja-JP", "/ja"),
    ("ko-KR", "/ko"),
    ("ru-RU", "/ru"),
    ("pt-PT", "/pt"),
    ("th-TH", "/th"),
    ("vi-VN", "/vi"),
]


def _escape(s: str) -> str:
    """XML 实体转义"""
    if not s:
        return ""
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def _resolve_base_url(request: Request) -> str:
    """根据请求头解析当前站点 Base URL，避免硬编码"""
    host = request.headers.get("x-forwarded-host") or request.headers.get("host") or ""
    proto = request.headers.get("x-forwarded-proto") or request.url.scheme or "https"
    if host:
        return f"{proto}://{host}".rstrip("/")
    return getattr(settings, "SITE_URL", "https://www.youdingjiancai.com").rstrip("/")


@router.get("/sitemap.xml")
async def generate_sitemap(
    request: Request,
    tenant_id: Optional[str] = Query(None, description="租户ID过滤，支持多租户独立站"),
    db: Session = Depends(get_db),
):
    """生成全功能动态 Sitemap.xml。
    涵盖：静态核心页、多语言 hreflang 声明、产品详情页（附带图片与视频搜索标签）、工程案例及内容页面。
    """
    base_url = _resolve_base_url(request)

    # 产品查询
    p_query = select(Product).where(Product.is_active)
    if tenant_id:
        p_query = p_query.where(Product.tenant_id == tenant_id)
    products = db.execute(p_query).scalars().all()

    # 案例查询
    c_query = select(CaseStudy).where(CaseStudy.is_active)
    cases = db.execute(c_query).scalars().all()

    # 内容页查询
    pages_query = select(ContentPage).where(ContentPage.is_active)
    pages = db.execute(pages_query).scalars().all()

    today = "2026-09-13"

    urls: list[str] = []

    # 1. 静态主路由（附带 12 语种 alternate）
    static_routes = [
        ("/", "1.0", "daily"),
        ("/products", "0.9", "weekly"),
        ("/cases", "0.8", "weekly"),
        ("/calculators", "0.8", "weekly"),
        ("/about", "0.7", "monthly"),
        ("/contact", "0.7", "monthly"),
        ("/news", "0.8", "daily"),
    ]

    for path, priority, freq in static_routes:
        url_xml = [f"  <url>\n    <loc>{_escape(base_url + path)}</loc>"]
        for hreflang, prefix in SUPPORTED_LOCALES:
            lang_path = f"{base_url}{prefix}{path}" if path != "/" else f"{base_url}{prefix or '/'}"
            url_xml.append(f'    <xhtml:link rel="alternate" hreflang="{hreflang}" href="{_escape(lang_path)}" />')
        url_xml.append(f'    <xhtml:link rel="alternate" hreflang="x-default" href="{_escape(base_url + path)}" />')
        url_xml.append(f"    <lastmod>{today}</lastmod>\n    <changefreq>{freq}</changefreq>\n    <priority>{priority}</priority>\n  </url>")
        urls.append("\n".join(url_xml))

    # 2. 产品详情页（附带 Google Image 与 Video 标签）
    for p in products:
        if not p.slug:
            continue
        lastmod = p.updated_at.strftime("%Y-%m-%d") if p.updated_at else today
        p_url = f"{base_url}/products/{p.slug}"
        p_xml = [f"  <url>\n    <loc>{_escape(p_url)}</loc>"]

        # Hreflang
        for hreflang, prefix in SUPPORTED_LOCALES:
            lang_p_url = f"{base_url}{prefix}/products/{p.slug}"
            p_xml.append(f'    <xhtml:link rel="alternate" hreflang="{hreflang}" href="{_escape(lang_p_url)}" />')
        p_xml.append(f'    <xhtml:link rel="alternate" hreflang="x-default" href="{_escape(p_url)}" />')

        p_xml.append(f"    <lastmod>{lastmod}</lastmod>\n    <changefreq>weekly</changefreq>\n    <priority>0.9</priority>")

        # Google 图片扩展
        if p.image_url:
            p_xml.append("    <image:image>")
            p_xml.append(f"      <image:loc>{_escape(p.image_url)}</image:loc>")
            p_xml.append(f"      <image:title>{_escape(p.name)}</image:title>")
            if p.description:
                p_xml.append(f"      <image:caption>{_escape(p.description[:150])}</image:caption>")
            p_xml.append("    </image:image>")

        p_xml.append("  </url>")
        urls.append("\n".join(p_xml))

        # 2.1 全球出海国家矩阵方案着陆页 (Programmatic Geo-Matrix Landing Pages)
        for c_code, c_profile in COUNTRY_PROFILES.items():
            geo_url = f"{base_url}/solutions/{c_code}/{p.slug}"
            geo_xml = [
                f"  <url>",
                f"    <loc>{_escape(geo_url)}</loc>",
                f"    <lastmod>{lastmod}</lastmod>",
                f"    <changefreq>weekly</changefreq>",
                f"    <priority>0.85</priority>",
            ]
            if p.image_url:
                geo_xml.append("    <image:image>")
                geo_xml.append(f"      <image:loc>{_escape(p.image_url)}</image:loc>")
                geo_xml.append(f"      <image:title>{_escape(p.name)} - {c_profile.get('country_name_zh', '')}工程方案</image:title>")
                geo_xml.append("    </image:image>")
            geo_xml.append("  </url>")
            urls.append("\n".join(geo_xml))

    # 3. 案例页面
    for c in cases:
        if not c.slug:
            continue
        lastmod = c.updated_at.strftime("%Y-%m-%d") if c.updated_at else today
        c_url = f"{base_url}/cases/{c.slug}"
        urls.append(
            f"  <url>\n    <loc>{_escape(c_url)}</loc>\n    <lastmod>{lastmod}</lastmod>\n    <priority>0.7</priority>\n    <changefreq>monthly</changefreq>\n  </url>"
        )

    # 4. 内容单页
    for pg in pages:
        if not pg.slug:
            continue
        lastmod = pg.updated_at.strftime("%Y-%m-%d") if pg.updated_at else today
        pg_url = f"{base_url}/content/{pg.slug}"
        urls.append(
            f"  <url>\n    <loc>{_escape(pg_url)}</loc>\n    <lastmod>{lastmod}</lastmod>\n    <priority>0.6</priority>\n    <changefreq>monthly</changefreq>\n  </url>"
        )

    xml_body = "\n".join(urls)
    full_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:xhtml="http://www.w3.org/1999/xhtml"
        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1"
        xmlns:video="http://www.google.com/schemas/sitemap-video/1.1">
{xml_body}
</urlset>"""

    return Response(
        content=full_xml,
        media_type="application/xml; charset=utf-8",
        headers={"Cache-Control": "public, max-age=3600, s-maxage=7200"},
    )


@router.get("/sitemap-index.xml")
async def generate_sitemap_index(request: Request):
    """Sitemap 索引文件 — 针对大型站点的多 Sitemap 聚合。"""
    base_url = _resolve_base_url(request)
    today = "2026-09-13"

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap>
    <loc>{_escape(base_url)}/sitemap.xml</loc>
    <lastmod>{today}</lastmod>
  </sitemap>
</sitemapindex>"""
    return Response(
        content=xml,
        media_type="application/xml; charset=utf-8",
        headers={"Cache-Control": "public, max-age=86400, s-maxage=86400"},
    )
