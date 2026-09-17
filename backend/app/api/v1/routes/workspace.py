# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""搜客执行台 + 写信台 路由（P1-1 + P1-2）。"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.response import success_response, error_response
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.prospect_lead import ProspectLead, LeadStatus
from app.services.prospect_scorer import score_lead, batch_score_leads


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = ""

router = APIRouter(prefix="/workspace", tags=["工作台"])


# ── 搜客执行台 ──

@router.post("/prospecting/search")
def prospecting_search(
    req: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建搜客任务（调用搜客服务）。"""
    keywords = req.get("keywords", [])
    countries = req.get("countries", [])
    customer_type = req.get("customerType", "")
    exclude_words = req.get("excludeWords", [])
    if not keywords:
        return error_response(400, "请至少输入一个产品关键词")

    # 查询当前租户已有线索（搜客任务通过 lead_generation 路由单独创建）
    tenant_id = str(current_user.tenant_id)
    query = db.query(ProspectLead).filter(ProspectLead.tenant_id == tenant_id)
    if countries:
        query = query.filter(ProspectLead.country.in_(countries))
    query = query.order_by(ProspectLead.overall_score.desc()).limit(50)
    leads = query.all()
    # 批量重算评分
    for lead in leads:
        score_lead(lead, keywords, persist=True, db=db)
    db.commit()
    return success_response(data={
        "leads": [_lead_to_dict(l) for l in leads],
        "total": len(leads),
    })


@router.get("/prospecting/leads")
def list_leads(
    page: int = 1,
    page_size: int = 20,
    status: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取当前租户的线索列表。"""
    query = db.query(ProspectLead).filter(
        ProspectLead.tenant_id == current_user.tenant_id
    )
    if status:
        query = query.filter(ProspectLead.status == status)
    query = query.order_by(ProspectLead.overall_score.desc())
    total = query.count()
    leads = query.offset((page - 1) * page_size).limit(page_size).all()
    return success_response(data={
        "items": [_lead_to_dict(l) for l in leads],
        "total": total,
        "page": page,
    })


@router.get("/prospecting/leads/{lead_id}")
def get_lead(
    lead_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取线索详情（含 evidence_chain 和 score_breakdown）。"""
    lead = db.query(ProspectLead).filter(
        ProspectLead.id == lead_id,
        ProspectLead.tenant_id == current_user.tenant_id,
    ).first()
    if not lead:
        raise HTTPException(status_code=404, detail="线索不存在")

    data = _lead_to_dict(lead)
    data["evidenceChain"] = lead.evidence_chain or []
    data["scoreBreakdown"] = {
        "match": lead.score_match,
        "email": lead.score_email,
        "evidence": lead.score_evidence,
        "contact": lead.score_contact,
        "overall": lead.overall_score,
    }
    return success_response(data=data)


@router.post("/prospecting/leads/{lead_id}/convert")
def convert_lead(
    lead_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """将线索转为客户。"""
    lead = db.query(ProspectLead).filter(
        ProspectLead.id == lead_id,
        ProspectLead.tenant_id == current_user.tenant_id,
    ).first()
    if not lead:
        raise HTTPException(status_code=404, detail="线索不存在")

    lead.status = LeadStatus.QUALIFIED
    db.commit()
    return success_response(message="已转为客户")


# ── 写信台 ──

@router.post("/outreach/ai-generate")
def ai_generate_email(
    req: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """AI 生成开发信。"""
    lead_id = req.get("lead_id")
    if not lead_id:
        return error_response(400, "请提供 lead_id")

    # 租户隔离
    lead = db.query(ProspectLead).filter(
        ProspectLead.id == lead_id,
        ProspectLead.tenant_id == current_user.tenant_id,
    ).first()
    if not lead:
        raise HTTPException(status_code=404, detail="线索不存在")

    # 使用 AIEngine 生成开发信
    from app.services.ai_engine import AIEngine
    engine = AIEngine()
    company = lead.company_name or "your company"
    country = lead.country or "your market"
    industry = lead.industry or "your industry"
    contact = f"{lead.first_name or ''} {lead.last_name or ''}".strip() or "team"
    prompt = f"""Write a professional B2B outreach email for:
Company: {company}
Country: {country}
Industry: {industry}
Contact: {contact}

Requirements:
- Subject line under 60 chars
- Professional but warm tone
- Reference their industry/market
- Offer instrumentation/industrial products
- Clear CTA

Return JSON: {{"subject": "...", "body": "..."}}"""

    try:
        llm = engine.llms.get("cost_optimized") or engine.llms.get("deepseek") or engine.llms.get("general")
        if not llm:
            return error_response(503, "AI 服务未配置")
        result = llm.invoke(prompt)
        import json
        parsed = json.loads(result.content)
        return success_response(data={"subject": parsed.get("subject", ""), "body": parsed.get("body", "")})
    except Exception as e:
        return error_response(500, f"AI 生成失败: {str(e)}")


@router.post("/outreach/drafts")
def save_draft(
    req: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """保存邮件草稿。"""
    # 简化实现：存到 lead 的 metadata 中
    lead_id = req.get("lead_id")
    if lead_id:
        # 租户隔离
        lead = db.query(ProspectLead).filter(
            ProspectLead.id == lead_id,
            ProspectLead.tenant_id == current_user.tenant_id,
        ).first()
        if lead:
            meta = lead.lead_metadata or {}
            meta[f"draft_{req.get('version', 'a')}"] = {
                "subject": req.get("subject"),
                "body": req.get("body"),
                "to": req.get("to"),
            }
            lead.lead_metadata = meta
            db.commit()

    return success_response(message="草稿已保存")


@router.get("/outreach/drafts")
def get_draft(
    lead_id: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取邮件草稿。"""
    if lead_id:
        # 租户隔离
        lead = db.query(ProspectLead).filter(
            ProspectLead.id == lead_id,
            ProspectLead.tenant_id == current_user.tenant_id,
        ).first()
        if lead and lead.metadata:
            draft = lead.metadata.get("draft_a", {})
            return success_response(data=draft)

    return success_response(data={})


@router.post("/outreach/send")
def send_email(
    req: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """发送邮件（调用邮件服务）。"""
    from app.services.email_tracking_service import send_tracked_email
    try:
        result = send_tracked_email(
            db=db,
            to=req.get("to"),
            subject=req.get("subject"),
            body=req.get("body"),
            lead_id=req.get("lead_id"),
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            track_opens=req.get("trackOpens", True),
            track_clicks=req.get("trackClicks", True),
        )
        db.commit()
        return success_response(data=result, message="邮件已发送")
    except Exception as e:
        return error_response(500, f"发送失败: {str(e)}")


# ── 辅助函数 ──

def _lead_to_dict(lead: ProspectLead) -> dict:
    """执行 lead_to_dict 相关逻辑处理。
    
    :param lead: 参数 lead
    :return: 返回处理结果。
    """
    return {
        "id": str(lead.id),
        "companyName": lead.company_name,
        "country": lead.country,
        "industry": lead.industry,
        "email": lead.email,
        "phone": lead.phone,
        "website": lead.website,
        "linkedinUrl": lead.linkedin_url,
        "contactName": f"{lead.first_name or ''} {lead.last_name or ''}".strip(),
        "overallScore": lead.overall_score,
        "scoreMatch": lead.score_match,
        "scoreEmail": lead.score_email,
        "scoreEvidence": lead.score_evidence,
        "scoreContact": lead.score_contact,
        "evidenceCount": len(lead.evidence_chain) if lead.evidence_chain else 0,
        "status": lead.status.value if lead.status else None,
        "createdAt": lead.created_at.isoformat() if lead.created_at else None,
    }
