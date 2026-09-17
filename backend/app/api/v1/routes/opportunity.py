# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Opportunity 路由 — CRM 销售机会管道（管理端）。"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.opportunity import Opportunity, OpportunityStage
from app.models.rfq import RFQ
from app.models.user import User

router = APIRouter()

# 标准销售管道阶段（Technical Spec §6）
PIPELINE_STAGES = ["Lead", "Qualified", "Contacted", "Engaged", "RFQ", "Quotation", "Negotiation", "Won", "Lost"]
# 各阶段默认概率
STAGE_PROBABILITY = {
    "Lead": 10, "Qualified": 20, "Contacted": 30, "Engaged": 40,
    "RFQ": 50, "Quotation": 60, "Negotiation": 75, "Won": 100, "Lost": 0,
}


def _serialize(op: Opportunity) -> dict[str, Any]:
    """执行 serialize 相关逻辑处理。
    
    :param op: 参数 op
    :return: 返回处理结果。
    """
    return {
        "id": str(op.id),
        "rfq_id": str(op.rfq_id) if op.rfq_id else None,
        "quote_id": str(op.quote_id) if op.quote_id else None,
        "name": op.name,
        "company": op.company,
        "contact_name": op.contact_name,
        "contact_email": op.contact_email,
        "value": op.value,
        "currency": op.currency,
        "stage": op.stage,
        "probability": op.probability,
        "expected_close_date": op.expected_close_date.isoformat() if op.expected_close_date else None,
        "country": op.country,
        "application": op.application,
        "notes": op.notes,
        "assigned_to": op.assigned_to,
        "tenant_id": op.tenant_id,
        "source": op.source,
        "source_url": op.source_url,
        "stages": [
            {
                "stage": s.stage,
                "changed_by": s.changed_by,
                "notes": s.notes,
                "changed_at": s.changed_at.isoformat() if s.changed_at else None,
            }
            for s in (op.stages or [])
            if getattr(s, "deleted_at", None) is None
        ],
        "created_at": op.created_at.isoformat() if op.created_at else None,
        "updated_at": op.updated_at.isoformat() if op.updated_at else None,
    }


def _auth_check(current_user: User) -> bool:
    """执行 auth_check 相关逻辑处理。
    
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    return current_user.role in ["admin", "super_admin", "tenant_admin", "sales"]


@router.get("/stats", summary="机会管道统计（看板）")
def opportunity_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理 GET /stats 请求，opportunity相关资源。
    
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    if not _auth_check(current_user):
        return error_response(403, "权限不足")
    from sqlalchemy import func as sa_func
    q = db.query(Opportunity).filter(Opportunity.deleted_at.is_(None))
    if current_user.role == "sales":
        q = q.filter(Opportunity.assigned_to == str(current_user.id))

    total = q.count()
    by_stage = dict(
        db.query(Opportunity.stage, sa_func.count(Opportunity.id))
        .filter(Opportunity.deleted_at.is_(None))
        .group_by(Opportunity.stage)
        .all()
    )
    open_ops = q.filter(Opportunity.stage.notin_(["Won", "Lost"])).all()
    pipeline_value = sum((o.value or 0) * (o.probability or 0) / 100 for o in open_ops)
    total_value = sum(o.value or 0 for o in q.all())
    won_count = int(by_stage.get("Won", 0) or 0)
    won_value = sum(
        o.value or 0
        for o in db.query(Opportunity)
        .filter(Opportunity.deleted_at.is_(None), Opportunity.stage == "Won")
        .all()
    )
    return success_response(
        data={
            "total": total,
            "by_stage": {k: int(v) for k, v in by_stage.items()},
            "pipeline_value": round(pipeline_value, 2),
            "total_value": round(total_value, 2),
            "won_count": won_count,
            "won_value": round(won_value, 2),
            "stages": PIPELINE_STAGES,
        }
    )


@router.get("", summary="机会列表（管理端）")
def list_opportunities(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    stage: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    assigned_to: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """执行 list_opportunities 相关数据处理。
    
    :param page: 页码
    :param page_size: 每页条数
    :param stage: 参数 stage
    :param search: 搜索关键字
    :param assigned_to: 参数 assigned_to
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    if not _auth_check(current_user):
        return error_response(403, "权限不足")
    from app.core.tenant_scope import scope_tenant_query
    q = scope_tenant_query(
        db.query(Opportunity).filter(Opportunity.deleted_at.is_(None)),
        Opportunity, db, current_user,
    )
    if current_user.role == "sales":
        q = q.filter(Opportunity.assigned_to == str(current_user.id))
    if stage:
        q = q.filter(Opportunity.stage == stage)
    if assigned_to:
        q = q.filter(Opportunity.assigned_to == assigned_to)
    if search:
        like = f"%{search}%"
        q = q.filter(
            (Opportunity.company.ilike(like))
            | (Opportunity.name.ilike(like))
            | (Opportunity.contact_name.ilike(like))
            | (Opportunity.application.ilike(like))
        )
    total = q.count()
    items = (
        q.order_by(Opportunity.updated_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return success_response(
        data={"items": [_serialize(o) for o in items], "total": total, "page": page, "page_size": page_size},
        total=total, page=page, page_size=page_size,
    )


@router.get("/{opportunity_id}", summary="机会详情（管理端）")
def get_opportunity(
    opportunity_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理 GET /{opportunity_id} 请求，获取相关资源。
    
    :param opportunity_id: 商机ID
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    if not _auth_check(current_user):
        return error_response(403, "权限不足")
    op = db.query(Opportunity).filter(
        Opportunity.id == opportunity_id, Opportunity.deleted_at.is_(None)
    ).first()
    if not op:
        return error_response(404, "机会不存在")
    from app.core.tenant_scope import tenant_can_access
    if not tenant_can_access(db, current_user, op.tenant_id):
        return error_response(404, "机会不存在")  # 跨租户按不存在处理，不泄露存在性
    if current_user.role == "sales" and op.assigned_to != str(current_user.id):
        return error_response(403, "仅可查看本人负责的机会")
    return success_response(data=_serialize(op))


class OpportunityCreateIn:
    """轻量请求体（不依赖 Pydantic 兼容层，直接解析 dict）。"""


from pydantic import BaseModel, Field


class OpportunityCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=300)
    rfq_id: Optional[str] = Field(None, max_length=36)
    company: Optional[str] = Field(None, max_length=200)
    contact_name: Optional[str] = Field(None, max_length=100)
    contact_email: Optional[str] = Field(None, max_length=200)
    value: Optional[float] = Field(None, ge=0)
    currency: Optional[str] = Field("USD", max_length=10)
    stage: Optional[str] = Field(None, max_length=50)
    probability: Optional[int] = Field(None, ge=0, le=100)
    expected_close_date: Optional[str] = None
    country: Optional[str] = Field(None, max_length=100)
    application: Optional[str] = Field(None, max_length=200)
    notes: Optional[str] = None
    assigned_to: Optional[str] = Field(None, max_length=36)
    source: Optional[str] = Field(None, max_length=50)
    source_url: Optional[str] = Field(None, max_length=1000)


@router.post("", summary="创建机会（从 RFQ 或手动）")
def create_opportunity(
    body: OpportunityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """执行 create_opportunity 相关数据处理。
    
    :param body: 请求体
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    if not _auth_check(current_user):
        return error_response(403, "权限不足")

    rfq = None
    if body.rfq_id:
        rfq = db.query(RFQ).filter(RFQ.id == body.rfq_id, RFQ.deleted_at.is_(None)).first()
        if not rfq:
            return error_response(404, "RFQ 不存在")

    stage = body.stage or "Qualified"
    if stage not in PIPELINE_STAGES:
        stage = "Qualified"
    probability = body.probability if body.probability is not None else STAGE_PROBABILITY.get(stage, 20)
    expected_close = None
    if body.expected_close_date:
        try:
            expected_close = datetime.fromisoformat(body.expected_close_date.replace("Z", "+00:00"))
        except ValueError:
            expected_close = None

    op = Opportunity(
        rfq_id=body.rfq_id,
        name=body.name,
        company=body.company or (rfq.company if rfq else None),
        contact_name=body.contact_name or (rfq.contact_name if rfq else None),
        contact_email=body.contact_email or (rfq.email if rfq else None),
        value=body.value,
        currency=body.currency,
        stage=stage,
        probability=probability,
        expected_close_date=expected_close,
        country=body.country or (rfq.country if rfq else None),
        application=body.application or (rfq.application if rfq else None),
        notes=body.notes,
        assigned_to=body.assigned_to,
        source=body.source or ("rfq" if rfq else "manual"),
        source_url=body.source_url or (rfq.source_url if rfq else None),
        tenant_id=rfq.tenant_id if rfq else None,
    )
    db.add(op)
    db.flush()
    db.add(OpportunityStage(
        opportunity_id=op.id,
        stage=stage,
        changed_by=str(current_user.id),
        notes="创建机会",
    ))
    db.commit()
    db.refresh(op)
    return success_response(data=_serialize(op), message="机会已创建")


class StageUpdate(BaseModel):
    stage: str = Field(..., min_length=1, max_length=50)
    notes: Optional[str] = None


@router.put("/{opportunity_id}/stage", summary="更新机会阶段")
def update_stage(
    opportunity_id: str,
    body: StageUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理 PUT /{opportunity_id}/stage 请求，更新相关资源。
    
    :param opportunity_id: 商机ID
    :param body: 请求体
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    if not _auth_check(current_user):
        return error_response(403, "权限不足")
    op = db.query(Opportunity).filter(
        Opportunity.id == opportunity_id, Opportunity.deleted_at.is_(None)
    ).first()
    if not op:
        return error_response(404, "机会不存在")
    if body.stage not in PIPELINE_STAGES:
        return error_response(400, f"无效阶段，可选 {', '.join(PIPELINE_STAGES)}")
    op.stage = body.stage
    op.probability = STAGE_PROBABILITY.get(body.stage, op.probability)
    db.add(OpportunityStage(
        opportunity_id=op.id,
        stage=body.stage,
        changed_by=str(current_user.id),
        notes=body.notes,
    ))
    db.commit()
    db.refresh(op)
    return success_response(data=_serialize(op), message="阶段已更新")


class AssignIn(BaseModel):
    assigned_to: str = Field(..., min_length=1, max_length=36)


@router.put("/{opportunity_id}/assign", summary="分配机会负责人")
def assign_owner(
    opportunity_id: str,
    body: AssignIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理 PUT /{opportunity_id}/assign 请求，assign相关资源。
    
    :param opportunity_id: 商机ID
    :param body: 请求体
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")
    op = db.query(Opportunity).filter(
        Opportunity.id == opportunity_id, Opportunity.deleted_at.is_(None)
    ).first()
    if not op:
        return error_response(404, "机会不存在")
    op.assigned_to = body.assigned_to
    db.commit()
    db.refresh(op)
    return success_response(data=_serialize(op), message="负责人已更新")
