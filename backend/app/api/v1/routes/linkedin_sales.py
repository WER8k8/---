"""LinkedIn Sales Navigator API 路由 — FIX-55"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.security import get_current_user
from app.services.ubrain.linkedin_sales_navigator_service import (
    LinkedInSalesNavigatorClient,
    linkedin_sales_client,
    linkedin_decision_maker_service,
)

router = APIRouter(prefix="/linkedin-sales", tags=["获客·LinkedIn"])


@router.get("/status")
async def linkedin_status(user=Depends(get_current_user)):
    """LinkedIn Sales Navigator 配置状态"""
    return {
        "code": 0,
        "data": {
            "configured": linkedin_sales_client.is_configured,
            "has_access_token": bool(linkedin_sales_client._access_token),
            "has_client_id": bool(linkedin_sales_client._client_id),
            "has_client_secret": bool(linkedin_sales_client._client_secret),
        },
    }


@router.get("/auth/url")
async def get_auth_url(
    redirect_uri: str = Query(..., description="OAuth 回调 URL"),
    state: str = Query("", description="防 CSRF 状态码"),
    user=Depends(get_current_user),
):
    """获取 LinkedIn OAuth 授权 URL"""
    if not linkedin_sales_client._client_id:
        raise HTTPException(status_code=400, detail="LINKEDIN_CLIENT_ID 未配置")

    url = linkedin_sales_client.get_authorization_url(redirect_uri=redirect_uri, state=state)
    return {"code": 0, "data": {"auth_url": url}}


@router.post("/auth/exchange")
async def exchange_code(
    code: str,
    redirect_uri: str,
    user=Depends(get_current_user),
):
    """用 OAuth 授权码换取 Token"""
    if not linkedin_sales_client.is_configured:
        raise HTTPException(status_code=400, detail="LinkedIn 未配置")

    token_data = await linkedin_sales_client.exchange_code(code=code, redirect_uri=redirect_uri)
    return {"code": 0, "data": {"token_obtained": True, "expires_in": token_data.get("expires_in", 0)}}


# ── 人员搜索 ──────────────────────────────────────────────

@router.get("/people/search")
async def search_people(
    keywords: str = "",
    title: str = "",
    company: str = "",
    company_id: str = "",
    location: str = "",
    country: str = "",
    industry: str = "",
    count: int = 25,
    start: int = 0,
    user=Depends(get_current_user),
):
    """搜索 LinkedIn 人员"""
    if not linkedin_sales_client.is_configured:
        raise HTTPException(status_code=400, detail="LinkedIn 未配置")

    result = await linkedin_sales_client.search_people(
        keywords=keywords,
        title=title,
        company=company,
        company_id=company_id,
        location=location,
        country=country,
        industry=industry,
        count=count,
        start=start,
    )
    return {"code": 0, "data": result.to_dict()}


@router.get("/people/{person_id}")
async def get_person(
    person_id: str,
    user=Depends(get_current_user),
):
    """获取人员详细档案"""
    if not linkedin_sales_client.is_configured:
        raise HTTPException(status_code=400, detail="LinkedIn 未配置")

    person = await linkedin_sales_client.get_person(person_id)
    return {"code": 0, "data": person.to_dict()}


@router.get("/people/me")
async def get_my_profile(user=Depends(get_current_user)):
    """获取当前授权用户档案"""
    if not linkedin_sales_client.is_configured:
        raise HTTPException(status_code=400, detail="LinkedIn 未配置")

    profile = await linkedin_sales_client.get_my_profile()
    return {"code": 0, "data": profile.to_dict()}


# ── 公司搜索 ──────────────────────────────────────────────

@router.get("/companies/search")
async def search_companies(
    keywords: str = "",
    industry: str = "",
    company_size: str = "",
    location: str = "",
    country: str = "",
    count: int = 25,
    start: int = 0,
    user=Depends(get_current_user),
):
    """搜索 LinkedIn 公司"""
    if not linkedin_sales_client.is_configured:
        raise HTTPException(status_code=400, detail="LinkedIn 未配置")

    result = await linkedin_sales_client.search_companies(
        keywords=keywords,
        industry=industry,
        company_size=company_size,
        location=location,
        country=country,
        count=count,
        start=start,
    )
    return {"code": 0, "data": result.to_dict()}


@router.get("/companies/{company_id}")
async def get_company(
    company_id: str,
    user=Depends(get_current_user),
):
    """获取公司详细档案"""
    if not linkedin_sales_client.is_configured:
        raise HTTPException(status_code=400, detail="LinkedIn 未配置")

    company = await linkedin_sales_client.get_company(company_id)
    return {"code": 0, "data": company.to_dict()}


@router.get("/companies/{company_id}/employees")
async def get_company_employees(
    company_id: str,
    title: str = "",
    count: int = 25,
    start: int = 0,
    user=Depends(get_current_user),
):
    """获取公司员工列表"""
    if not linkedin_sales_client.is_configured:
        raise HTTPException(status_code=400, detail="LinkedIn 未配置")

    result = await linkedin_sales_client.get_company_employees(
        company_id=company_id,
        title=title,
        count=count,
        start=start,
    )
    return {"code": 0, "data": result.to_dict()}


# ── 决策人识别 ────────────────────────────────────────────

@router.get("/decision-makers")
async def find_decision_makers(
    company_id: str,
    count: int = 25,
    user=Depends(get_current_user),
):
    """查找公司决策人"""
    if not linkedin_sales_client.is_configured:
        raise HTTPException(status_code=400, detail="LinkedIn 未配置")

    result = await linkedin_sales_client.find_decision_makers(
        company_id=company_id,
        count=count,
    )
    return {"code": 0, "data": result.to_dict()}


# ── 获客清单 ──────────────────────────────────────────────

@router.post("/buyers/find")
async def find_buyers_for_company(
    company_name: str,
    company_domain: str = "",
    max_results: int = 25,
    user=Depends(get_current_user),
):
    """为目标公司找到采购决策人"""
    if not linkedin_decision_maker_service.is_configured:
        raise HTTPException(status_code=400, detail="LinkedIn 未配置")

    result = await linkedin_decision_maker_service.find_buyers_for_company(
        company_name=company_name,
        company_domain=company_domain,
        max_results=max_results,
    )
    return {"code": 0, "data": result}


@router.post("/target-list/build")
async def build_target_list(
    industry: str = "",
    company_size: str = "",
    country: str = "",
    title_keywords: Optional[list[str]] = None,
    max_companies: int = 10,
    max_people_per_company: int = 10,
    user=Depends(get_current_user),
):
    """构建目标获客清单"""
    if not linkedin_decision_maker_service.is_configured:
        raise HTTPException(status_code=400, detail="LinkedIn 未配置")

    result = await linkedin_decision_maker_service.build_target_list(
        industry=industry,
        company_size=company_size,
        country=country,
        title_keywords=title_keywords,
        max_companies=max_companies,
        max_people_per_company=max_people_per_company,
    )
    return {"code": 0, "data": result}
