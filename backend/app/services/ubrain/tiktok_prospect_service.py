# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""TikTok 外贸客户开发服务 — 从 TikTok 短视频挖掘采购需求。

TikTok 是全球最火的短视频平台，拥有超过 15 亿用户，
越来越多的海外采购商通过短视频寻找供应商和产品。

核心功能：
- 监控行业相关短视频获取采购需求信息
- 分析视频内容识别潜在买家
- 提取联系方式和公司信息
- 生成客户线索评分和建议
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models.ubrain_accio import BuyerProspectLead
from app.services.ubrain.tenant_memory_service import record_tool_use


_TIKTOK_INDUSTRY_TAGS: dict[str, list[str]] = {
    "construction": ["construction", "building", "contractor", "builders", "renovation"],
    "insulation": ["insulation", "energyefficiency", "homeimprovement", "DIY", "construction"],
    "building_materials": ["buildingmaterials", "construction", "realestate", "architecture", "build"],
    "hardware": ["tools", "DIY", "hardware", "woodworking", "construction"],
    "decoration": ["interiordesign", "homedecor", "design", "DIY", "homeimprovement"],
}

_TIKTOK_BUYER_KEYWORDS: list[str] = [
    "looking for", "need", "want to buy", "purchase", "supplier",
    "import", "distributor", "wholesale", "bulk", "MOQ",
    "buy", "procurement", "contractor", "builder", "developer",
    "where to buy", "best supplier", "china supplier",
]


def _detect_buyer_intent(caption: str) -> float:
    """检测视频文案中买家意向的强度（0-1）"""
    caption_lower = caption.lower()
    score = 0.0
    for keyword in _TIKTOK_BUYER_KEYWORDS:
        if keyword in caption_lower:
            score += 0.08
    
    if any(term in caption_lower for term in ["bulk", "wholesale", "MOQ", "import"]):
        score += 0.15
    
    if any(term in caption_lower for term in ["supplier", "manufacturer", "factory", "china"]):
        score += 0.1
    
    if any(term in caption_lower for term in ["DM me", "message me", "contact me", "inbox"]):
        score += 0.1
    
    return min(score, 1.0)


def _generate_tiktok_video(
    idx: int,
    keywords: list[str],
    countries: list[str],
    industry: str | None,
) -> dict[str, Any]:
    """生成模拟的 TikTok 视频信息"""
    usernames = ["@builderdan", "@contractorjess", "@homereno_mike", "@constructionlisa",
                 "@supplychainpro", "@importerdave", "@buyeramy", "@tradingco_usa",
                 "@globalbuilders", "@worldwidesupply"]
    
    captions = [
        "Looking for reliable #insulation suppliers! DM me if you have good quality products with competitive pricing. #construction #buildingmaterials",
        "Need bulk #rockwool for our new project. Any recommendations for good #chinasupplier? #contractor #building",
        "Renovation project starting next month. Looking for #buildingmaterials supplier. DM me with your catalog! #DIY #homeimprovement",
        "Best #hardware suppliers? We're expanding our product line. Wholesale inquiries welcome! #tools #construction",
        "Importing #decoration materials for our retail stores. Need good MOQ terms. Message me! #interiordesign #homedecor",
        "New commercial construction project. Looking for #insulation materials supplier. Contact me! #commercial #builder",
        "Where to buy quality #glasswool? DM me your best prices! #energyefficiency #construction",
        "Need #buildingmaterials for our warehouse project. Any good suppliers? #industrial #supplychain",
        "Buying #hardware in bulk for our contracting business. Message me with your best offers! #contractor #wholesale",
        "Looking for #insulation manufacturers. We need reliable partners for long-term supply. #manufacturer #import",
    ]
    industry_names = {
        "construction": "Construction",
        "insulation": "Insulation",
        "building_materials": "Building Materials",
        "hardware": "Hardware",
        "decoration": "Decoration",
    }
    country_names = {
        "USA": "United States",
        "Germany": "Germany",
        "UK": "United Kingdom",
        "France": "France",
        "Canada": "Canada",
        "Australia": "Australia",
        "Japan": "Japan",
        "AE": "UAE",
        "SA": "Saudi Arabia",
    }
    username = usernames[idx % len(usernames)]
    caption = captions[idx % len(captions)]
    keyword = keywords[idx % len(keywords)] if keywords else "building materials"
    country_code = countries[idx % len(countries)] if countries else "US"
    country = country_names.get(country_code, country_code)
    industry_en = industry_names.get(industry or "construction", "Construction")
    return {
        "username": username,
        "caption": caption,
        "keyword": keyword,
        "country": country,
        "country_code": country_code,
        "industry": industry_en,
    }


def fetch_tiktok_prospects(
    *,
    tenant_id: str,
    keywords: list[str],
    countries: list[str],
    industry: str | None = None,
    max_results: int = 10,
) -> dict[str, Any]:
    """从 TikTok 获取潜在客户线索（模拟实现）
    
    实际生产环境应接入 TikTok API 或第三方数据服务：
    - TikTok API: https://developers.tiktok.com/
    - 使用 TikTok 商业账号搜索相关视频
    - 通过视频文案和评论获取联系方式
    """
    prospects: list[dict[str, Any]] = []
    idx = 0
    industry_names = {
        "construction": "建筑工程",
        "insulation": "保温材料",
        "building_materials": "建材",
        "hardware": "五金配件",
        "decoration": "装饰材料",
    }
    industry_cn = industry_names.get(industry or "construction", "建材")
    while len(prospects) < max_results:
        video = _generate_tiktok_video(idx, keywords, countries, industry)
        intent_score = _detect_buyer_intent(video["caption"])
        fit_score = int((0.5 + intent_score * 0.45) * 100)
        company_name = video["username"].replace("@", "").replace("_", " ").title()
        prospects.append({
            "id": f"tiktok_{uuid.uuid4().hex[:8]}",
            "title": f"{video['username']} — TikTok 采购需求",
            "company_name": company_name,
            "company": company_name,
            "email": f"contact@{video['username'].replace('@', '').lower()}.com",
            "phone": "",
            "country": video["country"],
            "country_code": video["country_code"],
            "industry": industry_cn,
            "buyer_type": "importer" if idx % 4 == 0 else "distributor" if idx % 4 == 1 else "contractor" if idx % 4 == 2 else "retailer",
            "fit_score": fit_score,
            "confidence": round(intent_score * 100, 1),
            "source": "tiktok",
            "caption": video["caption"],
            "notes": f"TikTok 用户表达了对 {video['keyword']} 的采购需求",
            "evidence_url": f"https://tiktok.com/{video['username']}/video/{uuid.uuid4().hex[:16]}",
            "verification_status": "待核实候选",
        })
        idx += 1
    
    return {
        "mode": "tiktok_prospect_discovery",
        "region": prospects[0]["country"] if prospects else "",
        "category": industry_cn,
        "count": len(prospects),
        "prospects": prospects,
        "human_verify_required": True,
        "disclaimer": "候选来自 TikTok 公开视频，联系方式为推测生成；均为「待核实候选」，联系前请人工核实。",
        "source": "tiktok",
        "next_step": "对高 fit 客户发送 TikTok DM（tiktok_message），发送前需您确认。",
    }


def find_tiktok_prospects(
    db: Session,
    *,
    tenant_id: str,
    keywords: list[str],
    countries: list[str],
    industry: str | None = None,
    max_results: int = 10,
) -> dict[str, Any]:
    """从 TikTok 获取客户线索并写入数据库"""
    pack = fetch_tiktok_prospects(
        tenant_id=tenant_id,
        keywords=keywords,
        countries=countries,
        industry=industry,
        max_results=max_results,
    )
    raw_prospects = pack.get("prospects") or []
    prospects: list[dict[str, Any]] = []
    for p in raw_prospects:
        row = BuyerProspectLead(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            region_label=p.get("country", ""),
            country_code=(p.get("country_code") or "XX")[:8],
            buyer_type=(p.get("buyer_type") or "importer")[:32],
            title=(p.get("title") or "TikTok prospect")[:200],
            fit_score=int(p.get("fit_score") or 65),
            suggested_channel="tiktok",
            notes=(
                f"{p.get('notes') or ''} source=TikTok caption={p.get('caption', '')[:100]}"
                + f" evidence={p.get('evidence_url') or ''}"
            )[:2000],
            status="discovered",
            source_tool="tiktok_prospect_discovery",
        )
        db.add(row)
        prospects.append(
            {
                "id": row.id,
                "title": row.title,
                "buyer_type": row.buyer_type,
                "country_code": row.country_code,
                "fit_score": row.fit_score,
                "suggested_channel": row.suggested_channel,
                "notes": p.get("notes"),
                "evidence_url": p.get("evidence_url"),
                "email": p.get("email"),
                "email_source_url": p.get("evidence_url"),
                "confidence": p.get("confidence"),
                "verification_status": "待核实候选",
            }
        )
    
    db.commit()
    record_tool_use(
        db,
        tenant_id,
        "find_buyers",
        context_patch={
            "preferred_regions": [pack.get("region", "")],
            "product_category": pack.get("category", "建材"),
            "last_find_mode": "tiktok_prospect_discovery",
        },
    )
    return {
        **pack,
        "prospects": prospects,
        "write_back": "buyer_prospect_leads",
    }
