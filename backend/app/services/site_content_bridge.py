# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""site_content ↔ 旧版 brand 字段桥接（公开站与编辑器兼容）。"""

from __future__ import annotations

from typing import Any


def sync_site_content_to_brand(brand: dict[str, Any], site_content: dict[str, Any]) -> dict[str, Any]:
    """保存 site_content 时同步到 brand 旧字段，供未升级的读取路径使用。"""
    if not isinstance(site_content, dict):
        return brand

    pages = site_content.get("pages") if isinstance(site_content.get("pages"), dict) else {}
    home = pages.get("home") if isinstance(pages.get("home"), dict) else {}
    products_page = pages.get("products") if isinstance(pages.get("products"), dict) else {}
    about = pages.get("about") if isinstance(pages.get("about"), dict) else {}
    contact = pages.get("contact") if isinstance(pages.get("contact"), dict) else {}
    brand_info = site_content.get("brand") if isinstance(site_content.get("brand"), dict) else {}
    footer = site_content.get("footer") if isinstance(site_content.get("footer"), dict) else {}
    theme = site_content.get("theme") if isinstance(site_content.get("theme"), dict) else {}
    out = dict(brand)
    out["site_content"] = site_content
    if brand_info.get("name"):
        out["company_name"] = brand_info["name"]
    if brand_info.get("tagline"):
        out["slogan"] = brand_info["tagline"]
    if home.get("title"):
        out["site_title"] = home["title"]
    if about.get("aboutText"):
        out["about_summary"] = about["aboutText"]
    if contact.get("phone"):
        out["contact_phone"] = contact["phone"]
    if contact.get("email"):
        out["contact_email"] = contact["email"]
    if footer.get("text"):
        out["footer_text"] = footer["text"]

    categories = home.get("categories")
    if isinstance(categories, list) and categories:
        names = [str(c.get("name", "")).strip() for c in categories if isinstance(c, dict)]
        out["product_categories"] = [n for n in names if n]
    else:
        items = products_page.get("productItems")
        if isinstance(items, list) and items:
            out["product_categories"] = [
                str(i.get("name", "")).strip()
                for i in items
                if isinstance(i, dict) and i.get("name")
            ]
        elif isinstance(products_page.get("products"), list):
            out["product_categories"] = [str(p) for p in products_page["products"] if p]

    colors = out.get("brand_colors") if isinstance(out.get("brand_colors"), dict) else {}
    if theme.get("headerBg"):
        colors = {**colors, "primary": theme["headerBg"]}
    if theme.get("heroBg"):
        colors = {**colors, "secondary": theme["heroBg"]}
    out["brand_colors"] = colors
    return out


def enrich_brand_from_site_content(brand_data: dict[str, Any]) -> dict[str, Any]:
    """公开 API 返回前：确保 site_content 存在且 legacy 字段已填充。"""
    site = brand_data.get("site_content")
    if isinstance(site, dict) and site:
        return sync_site_content_to_brand(brand_data, site)
    return brand_data
