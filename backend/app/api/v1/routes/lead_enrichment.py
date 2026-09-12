"""Hunter.io / Apollo.io 付费 API 路由 — FIX-53"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.security import get_current_user
from app.services.ubrain.hunter_service import lead_enrichment_service

router = APIRouter(prefix="/lead-enrichment", tags=["获客·付费API"])


@router.get("/status")
async def enrichment_status(user=Depends(get_current_user)):
    """获取数据源状态（Hunter/Apollo 配置 + 配额）"""
    status = await lead_enrichment_service.account_status()
    return {
        "code": 0,
        "data": {
            "available_sources": lead_enrichment_service.available_sources,
            **status,
        },
    }


@router.get("/hunter/domain-search")
async def hunter_domain_search(
    domain: str = Query(..., description="公司域名"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    department: str = Query(""),
    seniority: str = Query(""),
    user=Depends(get_current_user),
):
    """Hunter.io 域名搜索"""
    from app.services.ubrain.hunter_service import HunterClient
    client = HunterClient()
    if not client.is_configured:
        raise HTTPException(status_code=400, detail="HUNTER_API_KEY 未配置")

    result = await client.domain_search(
        domain=domain,
        limit=limit,
        offset=offset,
        department=department,
        seniority=seniority,
    )
    return {"code": 0, "data": result.to_dict()}


@router.get("/hunter/email-verify")
async def hunter_email_verify(
    email: str = Query(..., description="邮箱地址"),
    user=Depends(get_current_user),
):
    """Hunter.io 邮箱验证"""
    result = await lead_enrichment_service.verify_email(email)
    return {"code": 0, "data": result}


@router.post("/hunter/batch-verify")
async def hunter_batch_verify(
    emails: list[str],
    user=Depends(get_current_user),
):
    """Hunter.io 批量邮箱验证"""
    from app.services.ubrain.hunter_service import HunterClient
    client = HunterClient()
    if not client.is_configured:
        raise HTTPException(status_code=400, detail="HUNTER_API_KEY 未配置")

    results = await client.batch_verify(emails)
    return {"code": 0, "data": [r.to_dict() for r in results]}


@router.get("/hunter/email-finder")
async def hunter_email_finder(
    domain: str = Query(...),
    first_name: str = Query(...),
    last_name: str = Query(...),
    user=Depends(get_current_user),
):
    """Hunter.io 按姓名+域名查找邮箱"""
    from app.services.ubrain.hunter_service import HunterClient
    client = HunterClient()
    if not client.is_configured:
        raise HTTPException(status_code=400, detail="HUNTER_API_KEY 未配置")

    result = await client.email_finder(domain=domain, first_name=first_name, last_name=last_name)
    return {"code": 0, "data": result.to_dict()}


@router.get("/hunter/account")
async def hunter_account(user=Depends(get_current_user)):
    """Hunter.io 账户信息"""
    from app.services.ubrain.hunter_service import HunterClient
    client = HunterClient()
    if not client.is_configured:
        raise HTTPException(status_code=400, detail="HUNTER_API_KEY 未配置")

    info = await client.account_info()
    return {"code": 0, "data": info}


@router.post("/apollo/people-search")
async def apollo_people_search(
    q_organization_name: str = "",
    q_keywords: str = "",
    titles: Optional[list[str]] = None,
    seniorities: Optional[list[str]] = None,
    page: int = 1,
    per_page: int = 25,
    user=Depends(get_current_user),
):
    """Apollo.io 人员搜索"""
    from app.services.ubrain.hunter_service import ApolloClient
    client = ApolloClient()
    if not client.is_configured:
        raise HTTPException(status_code=400, detail="APOLLO_API_KEY 未配置")

    result = await client.search_people(
        q_organization_name=q_organization_name,
        q_keywords=q_keywords,
        titles=titles,
        seniorities=seniorities,
        page=page,
        per_page=per_page,
    )
    return {"code": 0, "data": result}


@router.post("/apollo/people-enrich")
async def apollo_people_enrich(
    first_name: str = "",
    last_name: str = "",
    email: str = "",
    domain: str = "",
    linkedin_url: str = "",
    user=Depends(get_current_user),
):
    """Apollo.io 人员富化"""
    result = await lead_enrichment_service.enrich_lead(
        email=email,
        first_name=first_name,
        last_name=last_name,
        domain=domain,
        linkedin_url=linkedin_url,
    )
    return {"code": 0, "data": result}


@router.post("/apollo/organization-search")
async def apollo_organization_search(
    q_name: str = "",
    q_keywords: str = "",
    page: int = 1,
    per_page: int = 25,
    user=Depends(get_current_user),
):
    """Apollo.io 公司搜索"""
    from app.services.ubrain.hunter_service import ApolloClient
    client = ApolloClient()
    if not client.is_configured:
        raise HTTPException(status_code=400, detail="APOLLO_API_KEY 未配置")

    result = await client.organization_search(
        q_name=q_name,
        q_keywords=q_keywords,
        page=page,
        per_page=per_page,
    )
    return {"code": 0, "data": result}


@router.post("/find-emails")
async def find_emails_by_domain(
    domain: str = Query(..., description="公司域名"),
    title_keywords: Optional[list[str]] = Query(None),
    max_results: int = Query(50, ge=1, le=200),
    user=Depends(get_current_user),
):
    """统一邮箱查找（自动选择最佳数据源）"""
    result = await lead_enrichment_service.find_emails_by_domain(
        domain=domain,
        title_keywords=title_keywords,
        max_results=max_results,
    )
    return {"code": 0, "data": result}
