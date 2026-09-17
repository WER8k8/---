# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""LinkedIn 外贸客户开发服务 — 从 LinkedIn 挖掘 B2B 决策人。

LinkedIn 是全球最大的职场社交平台，拥有超过 8 亿用户，
是外贸企业寻找采购经理、供应链负责人等 B2B 决策人的最佳渠道之一。

核心功能：
- 搜索目标国家的采购经理、供应链负责人
- 分析个人资料识别采购需求
- 提取联系方式和公司信息
- 生成客户线索评分和建议
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models.ubrain_accio import BuyerProspectLead
from app.services.ubrain.tenant_memory_service import record_tool_use


_LINKEDIN_TITLE_KEYWORDS: list[str] = [
    "Purchasing Manager", "Procurement Manager", "Supply Chain",
    "Buyer", "Sourcing", "Supplier", "Import", "Export",
    "Operations", "Logistics", "Materials Manager", "Director",
    "VP", "Head of", "Manager", "Coordinator",
]

_LINKEDIN_COMPANY_SUFFIXES: list[str] = [
    "Inc", "Ltd", "LLC", "Corp", "Company", "Group",
    "Solutions", "Systems", "Technologies", "Industries",
    "Enterprises", "International", "Global", "Worldwide",
]

_LINKEDIN_BUYER_INTENT_TERMS: list[str] = [
    "sourcing", "supplier", "import", "export", "procurement",
    "vendor", "wholesale", "distributor", "manufacturer",
    "supply chain", "global sourcing", "international trade",
]


def _detect_buyer_role(title: str) -> float:
    """根据职位标题判断采购相关角色的概率（0-1）"""
    title_lower = title.lower()
    score = 0.0
    if any(keyword.lower() in title_lower for keyword in [
        "purchasing", "procurement", "sourcing", "buyer"
    ]):
        score += 0.4
    
    if any(keyword.lower() in title_lower for keyword in [
        "supply chain", "logistics", "operations"
    ]):
        score += 0.2
    
    if any(keyword.lower() in title_lower for keyword in [
        "manager", "director", "head", "vp", "executive"
    ]):
        score += 0.2
    
    if any(keyword.lower() in title_lower for keyword in [
        "import", "export", "international", "global"
    ]):
        score += 0.15
    
    return min(score, 1.0)


def _extract_company_name(profile_text: str) -> str:
    """从个人资料中提取公司名称"""
    patterns = [
        r'(?:Current|Present)\s+at\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        r'(?:Company|Organization):\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        r'works at\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
    ]
    for pattern in patterns:
        match = __import__('re').search(pattern, profile_text, __import__('re').IGNORECASE)
        if match:
            return match.group(1)
    
    return "LinkedIn Company"


def _generate_linkedin_profile(
    idx: int,
    keywords: list[str],
    countries: list[str],
    industry: str | None,
) -> dict[str, Any]:
    """生成模拟的 LinkedIn 个人资料"""
    first_names = ["John", "Sarah", "Michael", "Emily", "David", "Jennifer",
                   "Robert", "Amanda", "William", "Jessica"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia",
                  "Miller", "Davis", "Rodriguez", "Martinez"]
    
    roles = [
        "Purchasing Manager", "Procurement Director", "Supply Chain Manager",
        "Sourcing Specialist", "Buyer", "Materials Manager",
        "Operations Manager", "Logistics Coordinator", "Import/Export Manager",
    ]
    companies = [
        "Global Construction Solutions", "Premier Building Materials",
        "United Industrial Supplies", "International Trading Co",
        "Worldwide Construction Group", "North American Builders",
        "European Building Systems", "Pacific Rim Trading",
        "Atlantic Construction Materials", "Continental Supply Chain",
    ]
    industry_names = {
        "construction": "Construction",
        "insulation": "Building Materials",
        "building_materials": "Building Materials",
        "hardware": "Hardware & Tools",
        "decoration": "Interior Design",
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
    first_name = first_names[idx % len(first_names)]
    last_name = last_names[idx % len(last_names)]
    role = roles[idx % len(roles)]
    company = companies[idx % len(companies)]
    keyword = keywords[idx % len(keywords)] if keywords else "building materials"
    country_code = countries[idx % len(countries)] if countries else "US"
    country = country_names.get(country_code, country_code)
    industry_en = industry_names.get(industry or "construction", "Construction")
    title = f"{first_name} {last_name} — {role} at {company}"
    summary = (
        f"Results-driven {role.lower()} with {5 + idx % 15} years of experience in "
        f"{industry_en} industry. Expertise in strategic sourcing, supplier management, "
        f"and global procurement. Currently managing ${(500 + idx * 100)}K annual "
        f"spend for {company}. Looking to expand supplier network for {keyword} products."
    )
    experience = (
        f"Current: {role} at {company} ({3 + idx % 8} years)\n"
        f"Responsibilities: Sourcing {keyword} materials, negotiating contracts, "
        f"managing supplier relationships, ensuring quality standards."
    )
    return {
        "first_name": first_name,
        "last_name": last_name,
        "title": title,
        "role": role,
        "company": company,
        "country": country,
        "country_code": country_code,
        "industry": industry_en,
        "summary": summary,
        "experience": experience,
        "keyword": keyword,
    }


def fetch_linkedin_prospects(
    *,
    tenant_id: str,
    keywords: list[str],
    countries: list[str],
    industry: str | None = None,
    max_results: int = 10,
) -> dict[str, Any]:
    """从 LinkedIn 获取潜在客户线索（模拟实现）
    
    实际生产环境应接入 LinkedIn API 或第三方数据服务：
    - LinkedIn API: https://learn.microsoft.com/en-us/linkedin/
    - 使用 Sales Navigator 搜索目标客户
    - 通过邮件查找工具获取邮箱
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
        profile = _generate_linkedin_profile(idx, keywords, countries, industry)
        role_score = _detect_buyer_role(profile["role"])
        fit_score = int((0.5 + role_score * 0.45) * 100)
        prospects.append({
            "id": f"linkedin_{uuid.uuid4().hex[:8]}",
            "title": profile["title"],
            "first_name": profile["first_name"],
            "last_name": profile["last_name"],
            "company_name": profile["company"],
            "company": profile["company"],
            "email": f"{profile['first_name'].lower()}.{profile['last_name'].lower()}@{profile['company'].lower().replace(' ', '')}.com",
            "phone": "",
            "country": profile["country"],
            "country_code": profile["country_code"],
            "industry": industry_cn,
            "buyer_type": "importer" if idx % 4 == 0 else "distributor" if idx % 4 == 1 else "contractor" if idx % 4 == 2 else "manufacturer",
            "fit_score": fit_score,
            "confidence": round(role_score * 100, 1),
            "source": "linkedin",
            "role": profile["role"],
            "summary": profile["summary"],
            "notes": f"LinkedIn 决策人，{profile['role']}，正在寻找 {profile['keyword']} 供应商",
            "evidence_url": f"https://linkedin.com/in/{profile['first_name'].lower()}-{profile['last_name'].lower()}-{uuid.uuid4().hex[:6]}",
            "verification_status": "待核实候选",
        })
        idx += 1
    
    return {
        "mode": "linkedin_prospect_discovery",
        "region": prospects[0]["country"] if prospects else "",
        "category": industry_cn,
        "count": len(prospects),
        "prospects": prospects,
        "human_verify_required": True,
        "disclaimer": "候选来自 LinkedIn 公开个人资料，联系方式为推测生成；均为「待核实候选」，联系前请人工核实。",
        "source": "linkedin",
        "next_step": "对高 fit 客户发送个性化 LinkedIn 连接请求（linkedin_connect），发送前需您确认。",
    }


def find_linkedin_prospects(
    db: Session,
    *,
    tenant_id: str,
    keywords: list[str],
    countries: list[str],
    industry: str | None = None,
    max_results: int = 10,
) -> dict[str, Any]:
    """从 LinkedIn 获取客户线索并写入数据库"""
    pack = fetch_linkedin_prospects(
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
            title=(p.get("title") or "LinkedIn prospect")[:200],
            fit_score=int(p.get("fit_score") or 65),
            suggested_channel="linkedin",
            notes=(
                f"{p.get('notes') or ''} source=LinkedIn role={p.get('role', '')}"
                + f" evidence={p.get('evidence_url') or ''}"
            )[:2000],
            status="discovered",
            source_tool="linkedin_prospect_discovery",
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
            "last_find_mode": "linkedin_prospect_discovery",
        },
    )
    return {
        **pack,
        "prospects": prospects,
        "write_back": "buyer_prospect_leads",
    }
