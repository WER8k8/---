"""Campaign 路由 — ABM / AI Outbound 活动管理（Phase 5）。"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload

from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.campaign import Campaign, CampaignEvent, CampaignRecipient, CampaignStep
from app.models.user import User


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = "/campaign"
ROUTE_TAGS = ["活动管理"]

router = APIRouter()


def _serialize(c: Campaign) -> dict[str, Any]:
    """
    处理 _serialize 相关业务逻辑。

    :param c: 入参 (Campaign)。

    :return: 返回 dict[str, Any] 类型的结果。
    """
    return {
        "id": str(c.id),
        "name": c.name,
        "campaign_type": c.campaign_type,
        "tier": c.tier,
        "status": c.status,
        "target_count": c.target_count,
        "sent_count": c.sent_count,
        "reply_count": c.reply_count,
        "positive_reply_count": c.positive_reply_count,
        "steps": [
            {"step_order": s.step_order, "day_delay": s.day_delay, "subject": s.subject, "action_type": s.action_type}
            for s in (c.steps or []) if getattr(s, "deleted_at", None) is None
        ],
        "recipients": [
            {"email": r.email, "status": r.status, "last_step_sent": r.last_step_sent}
            for r in (c.recipients or [])[:10] if getattr(r, "deleted_at", None) is None
        ],
        "created_at": c.created_at.isoformat() if c.created_at else None,
    }


@router.get("", summary="活动列表")
def list_campaigns(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    campaign_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    列出（list_campaigns）：处理相关业务逻辑并返回结果。

    :param page: 入参 (int)。
    :param page_size: 入参 (int)。
    :param campaign_type: 入参 (Optional[str])。
    :param status: 入参 (Optional[str])。
    :param db: 入参 (Session)。
    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")
    from app.core.tenant_scope import scope_tenant_query
    q = db.query(Campaign).filter(Campaign.deleted_at.is_(None)).options(
        joinedload(Campaign.steps),
        joinedload(Campaign.recipients),
    )
    q = scope_tenant_query(q, Campaign, db, current_user)
    if campaign_type:
        q = q.filter(Campaign.campaign_type == campaign_type)
    if status:
        q = q.filter(Campaign.status == status)
    total = q.count()
    items = q.order_by(Campaign.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return success_response(data={"items": [_serialize(c) for c in items], "total": total, "page": page, "page_size": page_size})


@router.get("/{campaign_id}", summary="活动详情")
def get_campaign(campaign_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    获取（get_campaign）：处理相关业务逻辑并返回结果。

    :param campaign_id: 入参 (str)。
    :param db: 入参 (Session)。
    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")
    c = db.query(Campaign).filter(Campaign.id == campaign_id, Campaign.deleted_at.is_(None)).first()
    if not c:
        return error_response(404, "活动不存在")
    from app.core.tenant_scope import tenant_can_access
    if not tenant_can_access(db, current_user, c.tenant_id):
        return error_response(404, "活动不存在")  # 跨租户按不存在处理
    return success_response(data=_serialize(c))


from pydantic import BaseModel, Field


class CampaignCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=300)
    campaign_type: str = Field(..., max_length=50)
    tier: Optional[str] = Field(None, max_length=10)
    target_count: Optional[int] = None


@router.post("", summary="创建活动")
def create_campaign(body: CampaignCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    创建（create_campaign）：处理相关业务逻辑并返回结果。

    :param body: 入参 (CampaignCreate)。
    :param db: 入参 (Session)。
    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")
    c = Campaign(name=body.name, campaign_type=body.campaign_type, tier=body.tier, target_count=body.target_count)
    db.add(c)
    db.commit()
    db.refresh(c)
    return success_response(data=_serialize(c), message="活动已创建")
