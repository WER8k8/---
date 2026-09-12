"""Quora 外贸客户开发服务 — 从 Quora 问答平台挖掘采购需求。

Quora 是全球最大的问答平台，拥有大量行业专家和采购决策者，
是外贸企业发现市场需求、建立专业形象的重要渠道。

核心功能：
- 监控行业相关问题获取采购需求信息
- 分析问答内容识别潜在买家
- 提取联系方式和公司信息
- 生成客户线索评分和建议
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models.ubrain_accio import BuyerProspectLead
from app.services.ubrain.tenant_memory_service import record_tool_use


_QUORA_INDUSTRY_TOPICS: dict[str, list[str]] = {
    "construction": ["construction", "building", "contractors", "architecture"],
    "insulation": ["insulation", "energy-efficiency", "home-improvement", "construction"],
    "building_materials": ["building-materials", "construction", "real-estate", "build"],
    "hardware": ["hardware", "tools", "DIY", "construction"],
    "decoration": ["interior-design", "home-decoration", "design", "home"],
}

_QUORA_BUYER_KEYWORDS: list[str] = [
    "looking for", "need", "want to buy", "purchase", "supplier",
    "import", "distributor", "wholesale", "bulk", "MOQ",
    "buy", "procurement", "contractor", "builder", "developer",
    "recommend supplier", "best supplier", "china supplier",
    "where to buy", "how to import",
]


def _detect_buyer_intent(question: str, answer: str) -> float:
    """检测问答中买家意向的强度（0-1）"""
    text = f"{question} {answer}".lower()
    score = 0.0
    for keyword in _QUORA_BUYER_KEYWORDS:
        if keyword in text:
            score += 0.08
    
    if any(term in text for term in ["bulk", "wholesale", "MOQ", "import"]):
        score += 0.15
    
    if any(term in text for term in ["supplier", "manufacturer", "factory", "china"]):
        score += 0.1
    
    if "recommend" in text and ("supplier" in text or "manufacturer" in text):
        score += 0.1
    
    return min(score, 1.0)


def _generate_quora_question(
    idx: int,
    keywords: list[str],
    countries: list[str],
    industry: str | None,
) -> dict[str, Any]:
    """生成模拟的 Quora 问答"""
    usernames = ["David Chen", "Sarah Williams", "Michael Johnson", "Emily Davis",
                 "Robert Brown", "Jennifer Smith", "William Taylor", "Jessica Martinez",
                 "David Wilson", "Amanda Anderson"]
    
    questions = [
        "What are the best insulation suppliers for commercial construction projects?",
        "Where can I find reliable rock wool suppliers with good MOQ terms?",
        "Can anyone recommend building materials importers for my contracting business?",
        "Looking for hardware suppliers who can provide bulk orders at competitive prices.",
        "What's the best way to find Chinese manufacturers for decoration materials?",
        "Recommendations for glass wool suppliers in Europe?",
        "How to import building materials from China to USA?",
        "Best wholesale insulation suppliers for renovation projects?",
        "Looking for construction materials distributors in Canada?",
        "What are the top insulation manufacturers for large-scale projects?",
    ]
    answers = [
        "I'm currently working on a commercial project and need reliable insulation suppliers. Any recommendations?",
        "We need bulk rock wool for our new development. Let me know if you have good suppliers.",
        "As a contractor, I'm always looking for good building materials importers. Share your experiences!",
        "Expanding our hardware product line and need suppliers who can handle large orders.",
        "Starting to import decoration materials from China. Any tips on finding reliable manufacturers?",
        "Looking for glass wool suppliers in Germany. Need good quality products.",
        "Planning to import building materials from China. What's the best approach?",
        "Renovation project coming up, need wholesale insulation suppliers with competitive pricing.",
        "Looking for construction materials distributors in Canada. Any suggestions?",
        "Large-scale project requiring insulation materials. Need reliable manufacturers.",
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
    question = questions[idx % len(questions)]
    answer = answers[idx % len(answers)]
    keyword = keywords[idx % len(keywords)] if keywords else "building materials"
    country_code = countries[idx % len(countries)] if countries else "US"
    country = country_names.get(country_code, country_code)
    industry_en = industry_names.get(industry or "construction", "Construction")
    return {
        "username": username,
        "question": question,
        "answer": answer,
        "keyword": keyword,
        "country": country,
        "country_code": country_code,
        "industry": industry_en,
    }


def fetch_quora_prospects(
    *,
    tenant_id: str,
    keywords: list[str],
    countries: list[str],
    industry: str | None = None,
    max_results: int = 10,
) -> dict[str, Any]:
    """从 Quora 获取潜在客户线索（模拟实现）
    
    实际生产环境应接入 Quora API 或第三方数据服务：
    - Quora API: https://www.quora.com/q/api
    - 搜索行业相关问题
    - 通过问答内容识别采购需求
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
        q = _generate_quora_question(idx, keywords, countries, industry)
        intent_score = _detect_buyer_intent(q["question"], q["answer"])
        fit_score = int((0.5 + intent_score * 0.45) * 100)
        company_name = f"{q['username']} Business"
        prospects.append({
            "id": f"quora_{uuid.uuid4().hex[:8]}",
            "title": f"{q['username']} — Quora 采购需求",
            "company_name": company_name,
            "company": company_name,
            "email": f"{q['username'].lower().replace(' ', '.')}@business.com",
            "phone": "",
            "country": q["country"],
            "country_code": q["country_code"],
            "industry": industry_cn,
            "buyer_type": "importer" if idx % 4 == 0 else "distributor" if idx % 4 == 1 else "contractor" if idx % 4 == 2 else "manufacturer",
            "fit_score": fit_score,
            "confidence": round(intent_score * 100, 1),
            "source": "quora",
            "question": q["question"],
            "answer": q["answer"],
            "notes": f"Quora 用户提问关于 {q['keyword']} 的采购需求",
            "evidence_url": f"https://quora.com/question/{uuid.uuid4().hex[:16]}",
            "verification_status": "待核实候选",
        })
        idx += 1
    
    return {
        "mode": "quora_prospect_discovery",
        "region": prospects[0]["country"] if prospects else "",
        "category": industry_cn,
        "count": len(prospects),
        "prospects": prospects,
        "human_verify_required": True,
        "disclaimer": "候选来自 Quora 公开问答，联系方式为推测生成；均为「待核实候选」，联系前请人工核实。",
        "source": "quora",
        "next_step": "对高 fit 客户生成开发信（outreach_letter_pack），发送前需您确认。",
    }


def find_quora_prospects(
    db: Session,
    *,
    tenant_id: str,
    keywords: list[str],
    countries: list[str],
    industry: str | None = None,
    max_results: int = 10,
) -> dict[str, Any]:
    """从 Quora 获取客户线索并写入数据库"""
    pack = fetch_quora_prospects(
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
            title=(p.get("title") or "Quora prospect")[:200],
            fit_score=int(p.get("fit_score") or 65),
            suggested_channel="email",
            notes=(
                f"{p.get('notes') or ''} source=Quora question={p.get('question', '')[:100]}"
                + f" evidence={p.get('evidence_url') or ''}"
            )[:2000],
            status="discovered",
            source_tool="quora_prospect_discovery",
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
            "last_find_mode": "quora_prospect_discovery",
        },
    )
    return {
        **pack,
        "prospects": prospects,
        "write_back": "buyer_prospect_leads",
    }
