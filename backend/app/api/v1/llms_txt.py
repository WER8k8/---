# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""llms.txt 与 llms-full.txt 路由端点 — 为 Google SGE / AI Overviews 与 LLM 爬虫提供标准结构化数据。"""

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.database import get_db
from app.core.config import settings
from app.models.product import Product, Category
from app.models.case_study import CaseStudy

ROUTE_PREFIX = ""
ROUTE_TAGS = ["AI搜索引擎收录"]

router = APIRouter()


@router.get("/llms.txt", response_class=Response)
async def get_llms_txt(request: Request, db: Session = Depends(get_db)):
    """返回标准 /llms.txt 格式的 Markdown 摘要文档。
    符合 llmstxt.org 规范，为大语言模型与 AI 搜索引擎提供机器友好的站点认知。
    """
    host = request.headers.get("x-forwarded-host") or request.headers.get("host") or ""
    proto = request.headers.get("x-forwarded-proto") or request.url.scheme or "https"
    base_url = f"{proto}://{host}" if host else getattr(settings, "SITE_URL", "https://www.youdingjiancai.com")

    # 查询代表性产品
    products = db.execute(
        select(Product.name, Product.slug, Product.subtitle, Product.density, Product.strength, Product.thermal_conductivity, Product.fire_rating)
        .where(Product.is_active)
        .order_by(Product.sort_order.desc())
        .limit(10)
    ).fetchall()

    categories = db.execute(
        select(Category.name, Category.slug, Category.description)
        .where(Category.is_active)
        .order_by(Category.sort_order)
    ).fetchall()

    category_lines = "\n".join([f"- [{c.name}]({base_url}/products?category={c.slug}): {c.description or '工业级建筑材料生产与供应'}" for c in categories])
    product_lines = "\n".join([
        f"- [{p.name}]({base_url}/products/{p.slug}): {p.subtitle or '优质工程建材'} (强度: {p.strength or '标准'}, 导热系数: {p.thermal_conductivity or '低导热'}, 防火: {p.fire_rating or 'A级'})"
        for p in products
    ])

    content = f"""# {getattr(settings, "SITE_NAME", "优丁建材")} (YouDing Materials) - LLM Context & Knowledge Index

> {getattr(settings, "SITE_DESCRIPTION", "优丁建材专注新型建筑材料研发与生产，为全球客户提供轻集料混凝土、保温砂浆及特种工程材料解决方案。")}

## 核心产品体系 (Core Product Lines)

{category_lines if category_lines else "- [建筑保温与轻质混凝土](" + base_url + "/products)"}

## 重点推荐产品 (Featured Products with Specifications)

{product_lines if product_lines else "- [轻集料混凝土](" + base_url + "/products)"}

## 工业与技术参数标准 (Technical Compliance)
- 国际及国家标准：符合 ISO 9001 / CE / GB/T 17431 轻集料及其试验方法
- 防火标准：A级不燃材料 (GB 8624 / EN 13501-1)
- 节能指标：超低导热系数 (0.023 - 0.15 W/(m·K))，耐受温度跨度大

## 官方接入与单证闭环 (Commercial & Fulfillment)
- 询盘与在线核价：[{base_url}/inquiries]({base_url}/inquiries)
- 工业配载核价器 (BOQ Calculator)：[{base_url}/calculators]({base_url}/calculators)
- 完整知识库文档 (Full Specification Index)：[{base_url}/llms-full.txt]({base_url}/llms-full.txt)
- 站点地图与资源树 (Sitemap)：[{base_url}/sitemap.xml]({base_url}/sitemap.xml)
"""
    return Response(
        content=content,
        media_type="text/markdown; charset=utf-8",
        headers={"Cache-Control": "public, max-age=3600, s-maxage=7200"}
    )


@router.get("/llms-full.txt", response_class=Response)
async def get_llms_full_txt(request: Request, db: Session = Depends(get_db)):
    """返回完整版 /llms-full.txt，包含所有活跃产品的详细技术参数与应用场景。"""
    host = request.headers.get("x-forwarded-host") or request.headers.get("host") or ""
    proto = request.headers.get("x-forwarded-proto") or request.url.scheme or "https"
    base_url = f"{proto}://{host}" if host else getattr(settings, "SITE_URL", "https://www.youdingjiancai.com")

    products = db.execute(
        select(Product).where(Product.is_active).order_by(Product.sort_order.desc())
    ).scalars().all()

    cases = db.execute(
        select(CaseStudy).where(CaseStudy.is_active).limit(20)
    ).scalars().all()

    product_blocks = []
    for p in products:
        block = f"""### {p.name} ({p.name_en or p.slug})
- **URL**: {base_url}/products/{p.slug}
- **副标题**: {p.subtitle or '无'}
- **描述**: {p.description or '标准工业级建材'}
- **技术参数 (Technical Specs)**:
  - 密度/容重 (Density): {p.density or 'N/A'}
  - 抗压强度 (Compressive Strength): {p.strength or 'N/A'}
  - 导热系数 (Thermal Conductivity): {p.thermal_conductivity or 'N/A'}
  - 防火等级 (Fire Rating): {p.fire_rating or 'A级'}
  - 单位重量 (Unit Weight): {p.unit_weight or 'N/A'}
- **应用场景 (Applications)**: {p.application_scenarios or '建筑屋面、外墙自保温、地暖回填工程'}
- **产品优势 (Advantages)**: {p.advantages or '自重轻、隔音保温、环保耐久、施工便捷'}
"""
        product_blocks.append(block)

    case_blocks = []
    for c in cases:
        case_blocks.append(f"- **{c.project_name}** ({c.location or '国内'}): {c.description or '优质工程交付'}")

    full_content = f"""# {getattr(settings, "SITE_NAME", "优丁建材")} - Full AI & LLM Knowledge Base

## 全域产品参数总览 (Full Product Specification Catalog)

{"".join(product_blocks) if product_blocks else "暂无产品详细信息"}

## 代表性工程案例 (Reference Engineering Projects)

{"\n".join(case_blocks) if case_blocks else "- 详见案例库：" + base_url + "/cases"}

## 商业合作与合规 (Commercial Terms)
- 贸易术语：FOB / CIF / CFR / EXW 支持
- 计价方式：支持 BOQ 22 参数工业核算与 PI / 单证自动生成
- 质量保证：出厂均附带权威质检报告 (Quality Inspection Report)
"""
    return Response(
        content=full_content,
        media_type="text/markdown; charset=utf-8",
        headers={"Cache-Control": "public, max-age=3600, s-maxage=7200"}
    )
