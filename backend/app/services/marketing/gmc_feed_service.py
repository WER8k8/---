# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Google Merchant Center (GMC) 官方规范商品 XML/RSS 2.0 数据流生成服务。

符合 Google 官方 Merchant Center 规范（命名空间 xmlns:g="http://base.google.com/ns/1.0"）。
支持免费产品陈列（Free Product Listings）与 Google Shopping 商业广告投放。
"""

from __future__ import annotations

from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.product import Product, Category
from app.models.tenant import Tenant


def _escape_xml(s: str) -> str:
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


class GmcFeedService:
    """GMC 商品 Feed 生成器 — 支持多租户独立站隔离与工业建材参数映射。"""

    def __init__(self, db: Session):
        self.db = db

    def generate_feed_xml(self, base_url: str, tenant_id: Optional[str] = None) -> str:
        """生成符合 Google Merchant Center 规范的 RSS 2.0 XML 字符串。"""
        clean_base = base_url.rstrip("/")

        # 确定品牌与租户上下文
        brand_name = getattr(settings, "SITE_NAME", "优丁建材")
        if tenant_id:
            tenant = self.db.query(Tenant).filter(Tenant.id == tenant_id).first()
            if tenant and tenant.name:
                brand_name = tenant.name

        # 查询活跃产品
        stmt = select(Product).where(Product.is_active.is_(True))
        if tenant_id:
            stmt = stmt.where(Product.tenant_id == tenant_id)
        products = self.db.execute(stmt).scalars().all()

        items_xml: list[str] = []

        for p in products:
            if not p.slug:
                continue

            prod_id = f"YD-{str(p.id)[:8].upper()}"
            title = _escape_xml(f"{p.name_en or p.name} ({p.density or '350kg/m³'}, {p.strength or '3.5MPa'})")
            desc = _escape_xml((p.description_en or p.description or "Industrial grade building and thermal insulation material.")[:450])
            link = f"{clean_base}/products/{p.slug}"
            image_link = p.image_url or f"{clean_base}/images/product-default.jpg"
            density_label = _escape_xml(p.density or "Standard Density")
            fire_label = _escape_xml(p.fire_rating or "Class A1")

            item_str = f"""    <item>
      <g:id>{prod_id}</g:id>
      <g:title>{title}</g:title>
      <g:description>{desc}</g:description>
      <g:link>{_escape_xml(link)}</g:link>
      <g:image_link>{_escape_xml(image_link)}</g:image_link>
      <g:condition>new</g:condition>
      <g:availability>in_stock</g:availability>
      <g:price>55.00 USD</g:price>
      <g:brand>{_escape_xml(brand_name)}</g:brand>
      <g:mpn>{_escape_xml(p.slug.upper())}</g:mpn>
      <g:identifier_exists>yes</g:identifier_exists>
      <g:google_product_category>Hardware &gt; Building Materials</g:google_product_category>
      <g:custom_label_0>{density_label}</g:custom_label_0>
      <g:custom_label_1>{fire_label}</g:custom_label_1>
      <g:shipping>
        <g:country>US</g:country>
        <g:service>Ocean Freight to Major Ports (FOB/CIF)</g:service>
        <g:price>0.00 USD</g:price>
      </g:shipping>
      <g:shipping>
        <g:country>DE</g:country>
        <g:service>Ocean Freight (Hamburg/Bremerhaven)</g:service>
        <g:price>0.00 USD</g:price>
      </g:shipping>
      <g:shipping>
        <g:country>AE</g:country>
        <g:service>Ocean Freight (Jebel Ali/Dubai)</g:service>
        <g:price>0.00 USD</g:price>
      </g:shipping>
    </item>"""
            items_xml.append(item_str)

        items_body = "\n".join(items_xml)

        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:g="http://base.google.com/ns/1.0">
  <channel>
    <title>{_escape_xml(brand_name)} Official Google Shopping Product Catalog</title>
    <link>{_escape_xml(clean_base)}</link>
    <description>Live export-ready building material feed generated for Google Merchant Center and Free Listings.</description>
{items_body}
  </channel>
</rss>"""
        return xml
