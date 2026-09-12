"""AI 智能搜索策略 API 路由 — FIX-60"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.security import get_current_user
from app.services.ubrain.search_strategy_builder import (
    SearchIntent,
    search_strategy_builder,
)

router = APIRouter(prefix="/search-strategy", tags=["获客·智能搜索"])


@router.post("/build")
async def build_strategy(
    industry: str,
    target_roles: Optional[list[str]] = None,
    target_countries: Optional[list[str]] = None,
    company_size: str = "",
    intent: str = "find_decision_makers",
    custom_keywords: Optional[list[str]] = None,
    user=Depends(get_current_user),
):
    """构建完整搜索策略"""
    try:
        search_intent = SearchIntent(intent)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"无效搜索意图: {intent}")

    strategy = search_strategy_builder.build_strategy(
        industry=industry,
        target_roles=target_roles,
        target_countries=target_countries,
        company_size=company_size,
        intent=search_intent,
        custom_keywords=custom_keywords,
    )
    return {"code": 0, "data": strategy.to_dict()}


@router.post("/google-dork")
async def build_google_dork(
    role: str,
    industry: str,
    country: str = "",
    exclude_terms: Optional[list[str]] = None,
    user=Depends(get_current_user),
):
    """构建 Google Dork 搜索语法"""
    dork = search_strategy_builder.build_google_dork(
        role=role,
        industry=industry,
        country=country,
        exclude_terms=exclude_terms,
    )
    return {"code": 0, "data": {"dork": dork}}


@router.post("/linkedin-url")
async def build_linkedin_url(
    keywords: str = "",
    title: str = "",
    company: str = "",
    industry: str = "",
    country: str = "",
    user=Depends(get_current_user),
):
    """构建 LinkedIn Sales Navigator 搜索 URL"""
    url = search_strategy_builder.build_linkedin_search_url(
        keywords=keywords,
        title=title,
        company=company,
        industry=industry,
        country=country,
    )
    return {"code": 0, "data": {"url": url}}


@router.get("/industry-insights")
async def get_industry_insights(
    industry: str,
    user=Depends(get_current_user),
):
    """获取行业搜索洞察"""
    insights = search_strategy_builder.get_industry_insights(industry)
    return {"code": 0, "data": insights}


@router.get("/industries")
async def list_industries(user=Depends(get_current_user)):
    """列出所有支持的行业模板"""
    from app.services.ubrain.search_strategy_builder import INDUSTRY_SEARCH_TEMPLATES
    industries = []
    for key, template in INDUSTRY_SEARCH_TEMPLATES.items():
        industries.append({
            "industry": key,
            "role_count": len(template.get("roles", [])),
            "keyword_count": len(template.get("keywords", [])),
            "sample_roles": template.get("roles", [])[:5],
        })

    return {"code": 0, "data": industries}


@router.get("/countries")
async def list_countries(user=Depends(get_current_user)):
    """列出所有支持的国家/地区"""
    from app.services.ubrain.search_strategy_builder import COUNTRY_PATTERNS
    countries = []
    for code, info in COUNTRY_PATTERNS.items():
        countries.append({
            "code": code,
            "tld": info["domain_tld"],
            "linkedin_geo": info["linkedin_geo"],
            "linkedin_geo_id": info["linkedin_geo_id"],
        })

    return {"code": 0, "data": countries}


@router.post("/optimize")
async def optimize_strategy(
    industry: str,
    target_roles: Optional[list[str]] = None,
    target_countries: Optional[list[str]] = None,
    user=Depends(get_current_user),
):
    """优化搜索策略"""
    # 先构建策略
    strategy = search_strategy_builder.build_strategy(
        industry=industry,
        target_roles=target_roles,
        target_countries=target_countries,
    )
    # 优化
    optimization = search_strategy_builder.optimize_strategy(strategy)
    return {"code": 0, "data": optimization}


@router.get("/intents")
async def list_intents(user=Depends(get_current_user)):
    """列出所有搜索意图"""
    return {
        "code": 0,
        "data": [
            {"value": e.value, "name": e.name}
            for e in SearchIntent
        ],
    }
