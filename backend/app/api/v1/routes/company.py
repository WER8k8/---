# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Company 360 路由 — 公司主数据 + 联系人 + 信号聚合（Account 360 后端）。"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.company import Company, CompanyContact, CompanySignal, IntentEngineRun
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()

# Intent 信号权重（Master Spec §13，可配置化）
SIGNAL_WEIGHTS = {
    "RFQ_SUBMITTED": 40,
    "TENDER_PROCUREMENT": 35,
    "NEW_PROJECT": 30,
    "CERTIFICATE_DOWNLOAD": 15,
    "TDS_DOWNLOAD": 10,
    "QUOTE_REQUEST": 10,
    "CONTACT_PAGE": 8,
    "PRODUCT_VIEW": 5,
    "REPEAT_VISIT": 5,
}


def _serialize_company(c: Company) -> dict[str, Any]:
    """
    处理 _serialize_company 相关业务逻辑。

    :param c: 入参 (Company)。

    :return: 返回 dict[str, Any] 类型的结果。
    """
    return {
        "id": str(c.id),
        "name": c.name,
        "legal_name": c.legal_name,
        "domain": c.domain,
        "website": c.website,
        "country": c.country,
        "region": c.region,
        "city": c.city,
        "industry": c.industry,
        "sub_industry": c.sub_industry,
        "employees": c.employees,
        "revenue_range": c.revenue_range,
        "linkedin": c.linkedin,
        "icp_score": c.icp_score,
        "intent_score": c.intent_score,
        "account_score": c.account_score,
        "source": c.source,
        "source_url": c.source_url,
        "confidence": c.confidence,
        "contacts": [
            {
                "id": str(ct.id),
                "name": ct.name,
                "title": ct.title,
                "department": ct.department,
                "email": ct.email,
                "phone": ct.phone,
                "influence_score": ct.influence_score,
                "contactability_score": ct.contactability_score,
            }
            for ct in (c.contacts or [])
            if getattr(ct, "deleted_at", None) is None
        ],
        "signals": [
            {
                "id": str(s.id),
                "signal_type": s.signal_type,
                "title": s.title,
                "source_url": s.source_url,
                "weight": s.weight,
                "confidence": s.confidence,
                "occurred_at": s.occurred_at.isoformat() if s.occurred_at else None,
            }
            for s in (c.signals or [])
            if getattr(s, "deleted_at", None) is None
        ],
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "updated_at": c.updated_at.isoformat() if c.updated_at else None,
    }


def _auth_check(user: User) -> bool:
    """
    处理 _auth_check 相关业务逻辑。

    :param user: 入参 (User)。

    :return: 返回 bool 类型的结果。
    """
    return user.role in ["admin", "super_admin", "tenant_admin", "sales"]


@router.get("", summary="公司列表（Account 360）")
def list_companies(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    country: Optional[str] = Query(None),
    min_intent: Optional[int] = Query(None, ge=0, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    列出（list_companies）：处理相关业务逻辑并返回结果。

    :param page: 入参 (int)。
    :param page_size: 入参 (int)。
    :param search: 入参 (Optional[str])。
    :param country: 入参 (Optional[str])。
    :param min_intent: 入参 (Optional[int])。
    :param db: 入参 (Session)。
    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    if not _auth_check(current_user):
        return error_response(403, "权限不足")
    from app.core.tenant_scope import scope_tenant_query, tenant_can_access
    q = scope_tenant_query(db.query(Company).filter(Company.deleted_at.is_(None)), Company, db, current_user)
    if search:
        like = f"%{search}%"
        q = q.filter((Company.name.ilike(like)) | (Company.domain.ilike(like)))
    if country:
        q = q.filter(Company.country == country)
    if min_intent is not None:
        q = q.filter(Company.intent_score >= min_intent)
    total = q.count()
    items = (
        q.order_by(Company.intent_score.desc(), Company.account_score.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return success_response(
        data={"items": [_serialize_company(c) for c in items], "total": total, "page": page, "page_size": page_size},
        total=total, page=page, page_size=page_size,
    )


@router.get("/{company_id}", summary="公司详情（Account 360）")
def get_company(
    company_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取（get_company）：处理相关业务逻辑并返回结果。

    :param company_id: 入参 (str)。
    :param db: 入参 (Session)。
    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    if not _auth_check(current_user):
        return error_response(403, "权限不足")
    c = db.query(Company).filter(Company.id == company_id, Company.deleted_at.is_(None)).first()
    if not c:
        return error_response(404, "公司不存在")
    from app.core.tenant_scope import tenant_can_access
    if not tenant_can_access(db, current_user, c.tenant_id):
        return error_response(404, "公司不存在")  # 跨租户按不存在处理，不泄露存在性
    return success_response(data=_serialize_company(c))


from pydantic import BaseModel, Field


class CompanyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=300)
    domain: Optional[str] = Field(None, max_length=300)
    website: Optional[str] = Field(None, max_length=500)
    country: Optional[str] = Field(None, max_length=100)
    city: Optional[str] = Field(None, max_length=100)
    industry: Optional[str] = Field(None, max_length=100)
    employees: Optional[str] = Field(None, max_length=50)
    revenue_range: Optional[str] = Field(None, max_length=50)
    source: Optional[str] = Field(None, max_length=50)
    source_url: Optional[str] = Field(None, max_length=1000)
    confidence: Optional[float] = Field(None, ge=0, le=1)


@router.post("", summary="创建公司")
def create_company(
    body: CompanyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    创建（create_company）：处理相关业务逻辑并返回结果。

    :param body: 入参 (CompanyCreate)。
    :param db: 入参 (Session)。
    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")
    c = Company(
        name=body.name,
        domain=body.domain,
        website=body.website,
        country=body.country,
        city=body.city,
        industry=body.industry,
        employees=body.employees,
        revenue_range=body.revenue_range,
        source=body.source,
        source_url=body.source_url,
        confidence=body.confidence,
        retrieved_at=datetime.now(timezone.utc),
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    # P0-7: 公司落库即激活 ICP/Intent/Account 评分（此前三列恒为 0）
    try:
        from app.services.company_scoring_service import score_company
        score_company(db, c)
    except Exception as _score_err:
        logger.warning("company scoring failed for %s: %s", getattr(c, "id", "?"), _score_err)
    return success_response(data=_serialize_company(c), message="公司已创建")


class SignalCreate(BaseModel):
    signal_type: str = Field(..., min_length=1, max_length=50)
    title: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    source: Optional[str] = Field(None, max_length=50)
    source_url: Optional[str] = Field(None, max_length=1000)
    occurred_at: Optional[str] = None
    weight: Optional[int] = Field(None, ge=0, le=100)


@router.post("/{company_id}/signals", summary="记录公司信号")
def add_signal(
    company_id: str,
    body: SignalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    新增（add_signal）：处理相关业务逻辑并返回结果。

    :param company_id: 入参 (str)。
    :param body: 入参 (SignalCreate)。
    :param db: 入参 (Session)。
    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    if current_user.role not in ["admin", "super_admin", "tenant_admin", "sales"]:
        return error_response(403, "权限不足")
    c = db.query(Company).filter(Company.id == company_id, Company.deleted_at.is_(None)).first()
    if not c:
        return error_response(404, "公司不存在")
    occurred = None
    if body.occurred_at:
        try:
            occurred = datetime.fromisoformat(body.occurred_at.replace("Z", "+00:00"))
        except ValueError:
            occurred = None
    weight = body.weight if body.weight is not None else SIGNAL_WEIGHTS.get(body.signal_type, 5)
    s = CompanySignal(
        company_id=company_id,
        signal_type=body.signal_type,
        title=body.title,
        description=body.description,
        source=body.source,
        source_url=body.source_url,
        weight=weight,
        confidence=1.0,
        occurred_at=occurred or datetime.now(timezone.utc),
    )
    db.add(s)
    db.flush()
    # 重算 Intent Score（Σ weight，封顶 100）
    total_weight = sum(sig.weight or 0 for sig in c.signals if getattr(sig, "deleted_at", None) is None)
    c.intent_score = min(100, total_weight)
    db.add(IntentEngineRun(
        company_id=company_id,
        intent_score=c.intent_score,
        icp_score=c.icp_score,
        account_score=c.account_score,
        signal_breakdown=repr({"total_weight": total_weight}),
    ))
    db.commit()
    db.refresh(c)
    return success_response(data=_serialize_company(c), message="信号已记录，Intent 分已更新")
