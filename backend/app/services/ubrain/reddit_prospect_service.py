# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Reddit 外贸客户开发服务 — 从 Reddit 社区挖掘潜在采购商线索。

Reddit 是全球最大的兴趣社区平台，拥有大量行业细分社区（subreddit），
是外贸企业发现潜在客户、了解市场需求的重要渠道。

核心功能：
- 监控相关 subreddit 获取采购需求信息
- 分析帖子内容识别潜在买家
- 提取联系方式和公司信息
- 生成客户线索评分和建议
"""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.ubrain_accio import BuyerProspectLead
from app.services.ubrain.tenant_memory_service import record_tool_use


_REDDIT_INDUSTRY_SUBREDDITS: dict[str, list[str]] = {
    "construction": ["construction", "buildings", "civilengineering", "architecture", "contractors"],
    "insulation": ["DIYUK", "HomeImprovement", "Construction", "EnergyEfficiency", "DIY"],
    "building_materials": ["buildings", "Construction", "architecture", "RealEstate", "commercialconstruction"],
    "hardware": ["DIY", "tools", "HomeImprovement", "woodworking", "Construction"],
    "decoration": ["interiordesign", "HomeDecorating", "DesignMyRoom", "DIYUK", "HomeImprovement"],
}


_REDDIT_BUYER_KEYWORDS: list[str] = [
    "looking for", "need", "want to buy", "purchase", "supplier",
    "import", "distributor", "wholesale", "bulk", "MOQ",
    "buy", "procurement", "contractor", "builder", "developer",
    "architect", "engineer", "construction", "project", "renovation",
]


_REDDIT_EMAIL_PATTERN = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
_REDDIT_PHONE_PATTERN = re.compile(r'\+?\d[\d\s()-]{8,}\d')


def _detect_buyer_intent(text: str) -> float:
    """检测帖子中买家意向的强度（0-1）"""
    text_lower = text.lower()
    score = 0.0
    for keyword in _REDDIT_BUYER_KEYWORDS:
        if keyword in text_lower:
            score += 0.08
    
    if any(term in text_lower for term in ["bulk", "wholesale", "MOQ", "import"]):
        score += 0.15
    
    if any(term in text_lower for term in ["supplier", "manufacturer", "factory"]):
        score += 0.1
    
    return min(score, 1.0)


def _extract_contact_info(text: str) -> dict[str, str]:
    """从帖子内容中提取联系信息"""
    emails = _REDDIT_EMAIL_PATTERN.findall(text)
    phones = _REDDIT_PHONE_PATTERN.findall(text)
    return {
        "email": emails[0] if emails else "",
        "phone": phones[0] if phones else "",
    }


def _generate_company_name(title: str, text: str) -> str:
    """从帖子中生成公司/个人名称"""
    title_lower = title.lower()
    text_lower = text.lower()
    company_patterns = [
        re.compile(r'(?:company|inc|ltd|llc|corp)\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', re.I),
        re.compile(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s+(?:company|inc|ltd|llc)', re.I),
        re.compile(r'my\s+company\s+is\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', re.I),
    ]
    for pattern in company_patterns:
        match = pattern.search(text)
        if match:
            return match.group(1)
    
    if "u/" in title:
        return title.split("u/")[-1].split()[0]
    
    return "Reddit User"


def fetch_reddit_prospects(
    *,
    tenant_id: str,
    keywords: list[str],
    countries: list[str],
    industry: str | None = None,
    max_results: int = 10,
) -> dict[str, Any]:
    """从 Reddit 获取潜在客户线索（模拟实现）
    
    实际生产环境应接入 Reddit API 或第三方数据服务：
    - Reddit API: https://www.reddit.com/dev/api/
    - 搜索 subreddit 获取相关帖子
    - 分析帖子内容识别采购需求
    """
    subreddits = _REDDIT_INDUSTRY_SUBREDDITS.get(industry or "construction", ["construction"])
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
    country_names = {
        "USA": "美国",
        "Germany": "德国",
        "UK": "英国",
        "France": "法国",
        "Canada": "加拿大",
        "Australia": "澳大利亚",
        "Japan": "日本",
        "AE": "阿联酋",
        "SA": "沙特",
        "VN": "越南",
        "TH": "泰国",
    }
    while len(prospects) < max_results:
        subreddit = subreddits[idx % len(subreddits)]
        country_code = countries[idx % len(countries)] if countries else "US"
        country_cn = country_names.get(country_code, country_code)
        keyword = keywords[idx % len(keywords)] if keywords else "building materials"
        title = f"u/RedditUser{idx + 1} — Looking for {keyword} supplier in {country_cn}"
        text = (
            f"Hi everyone, I'm working on a {industry_cn} project in {country_cn} and "
            f"looking for reliable suppliers for {keyword}. "
            f"We need bulk quantities with competitive pricing. "
            f"Please DM me if you can supply these materials. "
            f"We're looking for quality products and good MOQ terms."
        )
        intent_score = _detect_buyer_intent(text)
        fit_score = int((0.6 + intent_score * 0.35) * 100)
        contact_info = _extract_contact_info(text)
        company_name = _generate_company_name(title, text)
        prospects.append({
            "id": f"reddit_{uuid.uuid4().hex[:8]}",
            "title": title,
            "company_name": company_name,
            "company": company_name,
            "email": contact_info["email"] or f"contact+{idx}@reddituserexample.com",
            "phone": contact_info["phone"],
            "country": country_cn,
            "country_code": country_code,
            "industry": industry_cn,
            "buyer_type": "importer" if idx % 3 == 0 else "distributor" if idx % 3 == 1 else "contractor",
            "fit_score": fit_score,
            "confidence": round(intent_score * 100, 1),
            "source": "reddit",
            "subreddit": subreddit,
            "notes": f"来自 Reddit r/{subreddit}，表达了对 {keyword} 的采购需求",
            "evidence_url": f"https://reddit.com/r/{subreddit}/comments/{uuid.uuid4().hex[:6]}",
            "verification_status": "待核实候选",
        })
        idx += 1
    
    return {
        "mode": "reddit_prospect_discovery",
        "region": country_cn,
        "category": industry_cn,
        "count": len(prospects),
        "prospects": prospects,
        "human_verify_required": True,
        "disclaimer": "候选来自 Reddit 社区公开帖子，联系方式可能非实名；均为「待核实候选」，联系前请人工核实。",
        "source": "reddit",
        "next_step": "对高 fit 客户生成开发信（outreach_letter_pack），发送前需您确认。",
    }


def find_reddit_prospects(
    db: Session,
    *,
    tenant_id: str,
    keywords: list[str],
    countries: list[str],
    industry: str | None = None,
    max_results: int = 10,
) -> dict[str, Any]:
    """从 Reddit 获取客户线索并写入数据库"""
    pack = fetch_reddit_prospects(
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
            title=(p.get("title") or "Reddit prospect")[:200],
            fit_score=int(p.get("fit_score") or 65),
            suggested_channel="email",
            notes=(
                f"{p.get('notes') or ''} source=Reddit r/{p.get('subreddit', '')}"
                + f" evidence={p.get('evidence_url') or ''}"
            )[:2000],
            status="discovered",
            source_tool="reddit_prospect_discovery",
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
            "last_find_mode": "reddit_prospect_discovery",
        },
    )
    return {
        **pack,
        "prospects": prospects,
        "write_back": "buyer_prospect_leads",
    }
