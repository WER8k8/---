"""RAG 客户洞察 API 路由 — FIX-56"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.security import get_current_user
from app.services.ubrain.prospect_research_engine import (
    EmailTone,
    prospect_research_engine,
)

router = APIRouter(prefix="/prospect-research", tags=["获客·RAG洞察"])


@router.post("/research")
async def research_company(
    website: str,
    company_name: str = "",
    industry: str = "",
    user=Depends(get_current_user),
):
    """研究目标公司（RAG 客户洞察）"""
    research = await prospect_research_engine.research_company(
        website=website,
        company_name=company_name,
        industry=industry,
    )
    return {"code": 0, "data": research.to_dict()}


@router.post("/generate-email")
async def generate_personalized_email(
    website: str = "",
    company_name: str = "",
    industry: str = "",
    recipient_name: str = "",
    recipient_title: str = "",
    sender_name: str = "",
    sender_company: str = "",
    tone: str = "consultative",
    value_prop: str = "",
    user=Depends(get_current_user),
):
    """生成个性化开发信（基于 RAG 洞察）"""
    # 先研究
    research = await prospect_research_engine.research_company(
        website=website,
        company_name=company_name,
        industry=industry,
    )
    # 生成邮件
    try:
        email_tone = EmailTone(tone)
    except ValueError:
        email_tone = EmailTone.CONSULTATIVE

    email = await prospect_research_engine.generate_personalized_email(
        research=research,
        recipient_name=recipient_name,
        recipient_title=recipient_title,
        sender_name=sender_name,
        sender_company=sender_company,
        tone=email_tone,
        value_prop=value_prop,
    )
    return {
        "code": 0,
        "data": {
            "research": research.to_dict(),
            "email": email.to_dict(),
        },
    }


@router.post("/generate-email/from-research")
async def generate_email_from_research(
    company_name: str,
    industry: str = "",
    description: str = "",
    pain_points: Optional[list[str]] = None,
    growth_signals: Optional[list[str]] = None,
    recipient_name: str = "",
    recipient_title: str = "",
    sender_name: str = "",
    sender_company: str = "",
    tone: str = "consultative",
    value_prop: str = "",
    user=Depends(get_current_user),
):
    """从已有研究数据生成个性化邮件（跳过网站抓取）"""
    from app.services.ubrain.prospect_research_engine import (
        ProspectResearch,
        CompanyInsight,
        InsightCategory,
        CompanyGrowthSignal,
    )
    research = ProspectResearch(
        company_name=company_name,
        website="",
        industry=industry,
        description=description,
        pain_points=pain_points or [],
        growth_signals=[CompanyGrowthSignal(s) for s in (growth_signals or []) if s in [e.value for e in CompanyGrowthSignal]],
    )
    try:
        email_tone = EmailTone(tone)
    except ValueError:
        email_tone = EmailTone.CONSULTATIVE

    email = await prospect_research_engine.generate_personalized_email(
        research=research,
        recipient_name=recipient_name,
        recipient_title=recipient_title,
        sender_name=sender_name,
        sender_company=sender_company,
        tone=email_tone,
        value_prop=value_prop,
    )
    return {"code": 0, "data": email.to_dict()}
