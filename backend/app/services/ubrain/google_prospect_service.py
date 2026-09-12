"""Google 搜索客户开发服务 — 通过 Google 搜索引擎地毯式开发海外客户。

Google 是全球最大的搜索引擎，每天处理数十亿次搜索请求，
是外贸企业主动开发客户的重要渠道。

核心功能：
- 使用 Google Custom Search API 高级搜索定位目标客户网站
- 从网站提取联系方式和公司信息
- 分析网站内容识别采购需求
- 生成客户线索评分和建议
"""

from __future__ import annotations

import asyncio
import logging
import re
import uuid
from typing import Any
from urllib.parse import quote_plus

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.ubrain_accio import BuyerProspectLead
from app.services.ubrain.tenant_memory_service import record_tool_use

logger = logging.getLogger(__name__)


_GOOGLE_SEARCH_TEMPLATES: list[str] = [
    "{keyword} importer {country}",
    "{keyword} distributor {country}",
    "{keyword} wholesaler {country}",
    "{keyword} supplier {country}",
    "{keyword} buyer {country}",
    "{keyword} procurement {country}",
    "{keyword} sourcing {country}",
    "{keyword} import {country}",
]

_GOOGLE_INDUSTRY_SITES: dict[str, list[str]] = {
    "construction": ["construction", "building", "contractors", "architecture"],
    "insulation": ["insulation", "energy", "homeimprovement", "construction"],
    "building_materials": ["buildingmaterials", "construction", "realestate", "build"],
    "hardware": ["hardware", "tools", "DIY", "construction"],
    "decoration": ["interiordesign", "homedecor", "design", "home"],
}


def _extract_domain_from_url(url: str) -> str:
    """从 URL 中提取域名"""
    from urllib.parse import urlparse
    try:
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path
        domain = domain.replace("www.", "")
        return domain.lower().strip("/")
    except Exception:
        return url


def _extract_company_from_domain(domain: str) -> str:
    """从域名中提取公司名称"""
    parts = domain.split(".")
    if len(parts) >= 2:
        name = parts[0].replace("-", " ").replace("_", " ").title()
        if name.lower() in ["www", "web", "site", "online", "store"]:
            if len(parts) >= 3:
                return parts[1].replace("-", " ").replace("_", " ").title()
        return name
    return "Google Company"


def _extract_email_from_snippet(snippet: str, domain: str) -> str:
    """从搜索摘要中尝试提取邮箱，找不到则用域名生成推测邮箱"""
    if snippet:
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        matches = re.findall(email_pattern, snippet)
        if matches:
            return matches[0].lower()
    return f"contact@{domain}"


def _cse_api_available() -> bool:
    """检查 Google Custom Search API 是否已配置"""
    return bool(settings.GOOGLE_CSE_API_KEY and settings.GOOGLE_CSE_CX)


async def _search_google_cse(
    query: str,
    *,
    num: int = 10,
    start: int = 1,
    country_code: str | None = None,
    language_code: str = "lang_en",
) -> list[dict[str, Any]]:
    """调用 Google Custom Search API 搜索

    Args:
        query: 搜索查询
        num: 结果数量 (1-10)
        start: 起始偏移
        country_code: 国家代码（用于 gl 参数）
        language_code: 语言代码（用于 lr 参数）

    Returns:
        搜索结果列表
    """
    if not _cse_api_available():
        return []

    params: dict[str, Any] = {
        "key": settings.GOOGLE_CSE_API_KEY,
        "cx": settings.GOOGLE_CSE_CX,
        "q": query,
        "num": min(num, 10),
        "start": start,
        "lr": language_code,
    }
    if country_code:
        params["gl"] = country_code.lower()

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(settings.GOOGLE_CSE_BASE_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
            items = data.get("items", []) or []
            return [
                {
                    "title": item.get("title", ""),
                    "description": item.get("snippet", ""),
                    "url": item.get("link", ""),
                    "display_link": item.get("displayLink", ""),
                }
                for item in items
            ]
    except httpx.HTTPError as e:
        logger.warning(f"Google CSE API 请求失败: {e}")
        return []
    except Exception as e:
        logger.warning(f"Google CSE API 异常: {e}")
        return []


def fetch_google_prospects(
    *,
    tenant_id: str,
    keywords: list[str],
    countries: list[str],
    industry: str | None = None,
    max_results: int = 10,
) -> dict[str, Any]:
    """通过 Google 搜索获取潜在客户线索

    优先使用 Google Custom Search API 真实搜索，未配置时降级为模拟数据。
    """
    if _cse_api_available():
        try:
            return asyncio.run(_fetch_google_prospects_real(
                tenant_id=tenant_id,
                keywords=keywords,
                countries=countries,
                industry=industry,
                max_results=max_results,
            ))
        except Exception as e:
            logger.warning(f"Google CSE 真实搜索失败: {e}")

    # FIX-19: 生产代码不再返回 Mock 数据
    return {
        "mode": "google_prospect_discovery",
        "region": "",
        "category": industry or "",
        "count": 0,
        "prospects": [],
        "human_verify_required": True,
        "disclaimer": "Google CSE 未配置或搜索失败。请在 .env 中配置 GOOGLE_CSE_API_KEY 和 GOOGLE_CSE_CX。",
        "source": "google",
        "next_step": "配置 Google CSE 后重试，或使用「零成本获客引擎」。",
    }


def _generate_google_result(
    idx: int,
    keywords: list[str],
    countries: list[str],
    industry: str | None,
) -> dict[str, Any]:
    """生成模拟的 Google 搜索结果"""
    domain_suffixes = ["com", "co.uk", "de", "fr", "ca", "au", "jp", "ae"]
    country_suffix_map = {
        "USA": "com",
        "Germany": "de",
        "UK": "co.uk",
        "France": "fr",
        "Canada": "ca",
        "Australia": "au",
        "Japan": "jp",
        "AE": "ae",
        "SA": "com.sa",
    }
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
    company_prefixes = ["global", "premier", "united", "international", "worldwide",
                        "northamerican", "european", "pacific", "atlantic", "continental"]

    keyword = keywords[idx % len(keywords)] if keywords else "building materials"
    country_code = countries[idx % len(countries)] if countries else "US"
    country = country_names.get(country_code, country_code)
    suffix = country_suffix_map.get(country_code, "com")
    industry_en = industry_names.get(industry or "construction", "Construction")
    prefix = company_prefixes[idx % len(company_prefixes)]
    domain = f"{prefix}{keyword.replace(' ', '')}.{suffix}"
    titles = [
        f"{prefix.title()} {industry_en} - {keyword.capitalize()} Importer and Distributor",
        f"{prefix.title()} Trading - {keyword.capitalize()} Wholesale Supplier",
        f"{prefix.title()} Supplies - {keyword.capitalize()} Procurement Specialists",
        f"{prefix.title()} Industries - {keyword.capitalize()} Import and Export",
        f"{prefix.title()} Builders - {keyword.capitalize()} Contractor Supplies",
    ]
    descriptions = [
        f"Leading {keyword} importer in {country}. Wholesale distribution, competitive pricing, fast delivery.",
        f"Specialized {keyword} supplier for contractors and builders. Bulk orders welcome.",
        f"Professional {keyword} procurement services. Sourcing from reliable manufacturers worldwide.",
        f"Trusted {keyword} distributor with {5 + idx % 20} years experience. Quality products at affordable prices.",
        f"{keyword} import and export specialists. Connecting global suppliers with local buyers.",
    ]
    return {
        "title": titles[idx % len(titles)],
        "description": descriptions[idx % len(descriptions)],
        "domain": domain,
        "url": f"https://www.{domain}",
        "keyword": keyword,
        "country": country,
        "country_code": country_code,
        "industry": industry_en,
    }


async def _fetch_google_prospects_real(
    *,
    tenant_id: str,
    keywords: list[str],
    countries: list[str],
    industry: str | None = None,
    max_results: int = 10,
) -> dict[str, Any]:
    """通过 Google Custom Search API 真实搜索获取潜在客户线索"""
    prospects: list[dict[str, Any]] = []
    seen_domains: set[str] = set()
    industry_names = {
        "construction": "建筑工程",
        "insulation": "保温材料",
        "building_materials": "建材",
        "hardware": "五金配件",
        "decoration": "装饰材料",
    }
    industry_cn = industry_names.get(industry or "construction", "建材")
    country_gl_map = {
        "USA": "us",
        "Germany": "de",
        "UK": "uk",
        "France": "fr",
        "Canada": "ca",
        "Australia": "au",
        "Japan": "jp",
        "AE": "ae",
        "SA": "sa",
    }
    buyer_types = ["importer", "distributor", "wholesaler", "supplier", "trading company"]
    for keyword in keywords:
        if len(prospects) >= max_results:
            break

        for country in countries:
            if len(prospects) >= max_results:
                break

            for buyer_type in buyer_types[:2]:
                if len(prospects) >= max_results:
                    break

                query = f"{keyword} {buyer_type} {country}"
                gl_code = country_gl_map.get(country)
                items = await _search_google_cse(
                    query,
                    num=min(10, max_results - len(prospects)),
                    country_code=gl_code,
                )
                for item in items:
                    if len(prospects) >= max_results:
                        break

                    url = item.get("url", "")
                    domain = _extract_domain_from_url(url)
                    if not domain or domain in seen_domains:
                        continue
                    seen_domains.add(domain)
                    company_name = _extract_company_from_domain(domain)
                    email = _extract_email_from_snippet(item.get("description", ""), domain)
                    fit_score = _calc_fit_score(
                        title=item.get("title", ""),
                        description=item.get("description", ""),
                        keyword=keyword,
                        buyer_type=buyer_type,
                    )
                    prospects.append({
                        "id": f"google_{uuid.uuid4().hex[:8]}",
                        "title": item.get("title", company_name),
                        "company_name": company_name,
                        "company": company_name,
                        "email": email,
                        "phone": "",
                        "country": country,
                        "country_code": country_gl_map.get(country, "XX").upper(),
                        "industry": industry_cn,
                        "buyer_type": buyer_type,
                        "fit_score": fit_score,
                        "confidence": round(0.6 + fit_score / 300, 2),
                        "source": "google",
                        "domain": domain,
                        "notes": f"Google 搜索结果：{item.get('description', '')[:150]}",
                        "evidence_url": url,
                        "verification_status": "待核实候选",
                    })

    if not prospects:
        logger.warning("Google CSE 搜索无结果")
        # FIX-19: 生产代码不再返回 Mock 数据
        return {
            "mode": "google_prospect_discovery",
            "region": "",
            "category": industry_cn,
            "count": 0,
            "prospects": [],
            "human_verify_required": True,
            "disclaimer": "Google CSE 搜索无结果。请尝试不同的关键词。",
            "source": "google",
            "next_step": "调整关键词后重试，或使用「零成本获客引擎」。",
        }

    return {
        "mode": "google_prospect_discovery",
        "region": prospects[0]["country"] if prospects else "",
        "category": industry_cn,
        "count": len(prospects),
        "prospects": prospects,
        "human_verify_required": True,
        "disclaimer": "候选来自 Google Custom Search 真实搜索结果，邮箱为域名推测或摘要提取；均为「待核实候选」，联系前请人工核实。",
        "source": "google",
        "next_step": "对高 fit 客户生成开发信（outreach_letter_pack），发送前需您确认。",
    }


def _calc_fit_score(*, title: str, description: str, keyword: str, buyer_type: str) -> int:
    """根据搜索结果内容计算匹配度分数"""
    score = 50
    title_lower = title.lower()
    desc_lower = description.lower()
    keyword_lower = keyword.lower()
    buyer_lower = buyer_type.lower()
    if keyword_lower in title_lower:
        score += 15
    if keyword_lower in desc_lower:
        score += 10
    if buyer_lower in title_lower:
        score += 15
    if buyer_lower in desc_lower:
        score += 10

    bonus_keywords = ["import", "export", "wholesale", "distributor", "supplier", "trading"]
    for bk in bonus_keywords:
        if bk in title_lower or bk in desc_lower:
            score += 3

    return min(score, 98)


def _fetch_google_prospects_mock(
    *,
    tenant_id: str,
    keywords: list[str],
    countries: list[str],
    industry: str | None = None,
    max_results: int = 10,
) -> dict[str, Any]:
    """通过 Google 搜索获取潜在客户线索（模拟实现）"""
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
        result = _generate_google_result(idx, keywords, countries, industry)
        company_name = _extract_company_from_domain(result["domain"])
        fit_score = 55 + (idx % 35)
        prospects.append({
            "id": f"google_{uuid.uuid4().hex[:8]}",
            "title": result["title"],
            "company_name": company_name,
            "company": company_name,
            "email": f"contact@{result['domain']}",
            "phone": "",
            "country": result["country"],
            "country_code": result["country_code"],
            "industry": industry_cn,
            "buyer_type": "importer" if idx % 4 == 0 else "distributor" if idx % 4 == 1 else "contractor" if idx % 4 == 2 else "retailer",
            "fit_score": fit_score,
            "confidence": round(0.5 + (idx % 30) / 100, 1),
            "source": "google",
            "domain": result["domain"],
            "notes": f"Google 搜索结果，公司网站显示为 {result['keyword']} 相关业务",
            "evidence_url": result["url"],
            "verification_status": "待核实候选",
        })
        idx += 1
    
    return {
        "mode": "google_prospect_discovery",
        "region": prospects[0]["country"] if prospects else "",
        "category": industry_cn,
        "count": len(prospects),
        "prospects": prospects,
        "human_verify_required": True,
        "disclaimer": "候选来自 Google 搜索结果，联系方式为网站域名生成；均为「待核实候选」，联系前请人工核实。",
        "source": "google",
        "next_step": "对高 fit 客户生成开发信（outreach_letter_pack），发送前需您确认。",
    }


def find_google_prospects(
    db: Session,
    *,
    tenant_id: str,
    keywords: list[str],
    countries: list[str],
    industry: str | None = None,
    max_results: int = 10,
) -> dict[str, Any]:
    """通过 Google 搜索获取客户线索并写入数据库"""
    pack = fetch_google_prospects(
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
            title=(p.get("title") or "Google prospect")[:200],
            fit_score=int(p.get("fit_score") or 65),
            suggested_channel="email",
            notes=(
                f"{p.get('notes') or ''} source=Google domain={p.get('domain', '')}"
                + f" evidence={p.get('evidence_url') or ''}"
            )[:2000],
            status="discovered",
            source_tool="google_prospect_discovery",
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
            "last_find_mode": "google_prospect_discovery",
        },
    )
    return {
        **pack,
        "prospects": prospects,
        "write_back": "buyer_prospect_leads",
    }
