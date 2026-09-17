# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Full-Funnel Attribution Report API — Connection ⑥

GET /api/v1/analytics/attribution
POST /api/v1/analytics/attribution/email-reply   (Connection ④)
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.response import error_response, success_response
from app.core.security import get_current_user, get_current_user_optional
from app.db.session import get_db
from app.models.user import User
from app.services.attribution_service import (
    build_attribution_report,
    create_negotiation_from_email_reply,
)
from app.services.traffic_analytics_service import resolve_tenant_id


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = "/analytics"
ROUTE_TAGS = ["全链路归因"]

router = APIRouter()

BOARD_ROLES = frozenset(
    {"admin", "super_admin", "tenant_admin", "sales", "agent", "l2", "l3"}
)


# ---------------------------------------------------------------------------
# Connection ⑥: GET /attribution
# ---------------------------------------------------------------------------

@router.get("/attribution")
def get_attribution_report(
    period: str = Query("30d", description="1d / 7d / 30d / 90d"),
    tenant_id: Optional[str] = Query(None, description="超管可指定租户"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取（get_attribution_report）：处理相关业务逻辑并返回结果。

    :param period: 入参 (str)。
    :param tenant_id: 入参 (Optional[str])。
    :param db: 入参 (Session)。
    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    if current_user.role not in BOARD_ROLES:
        return error_response(403, "权限不足")

    # Resolve tenant scope
    tid = tenant_id
    if not tid:
        tid = resolve_tenant_id(db, user=current_user)

    report = build_attribution_report(db, tenant_id=tid, period=period)
    return success_response(data=report)


# ---------------------------------------------------------------------------
# Connection ④: POST /attribution/email-reply
# ---------------------------------------------------------------------------

class EmailReplyBody(BaseModel):
    """Inbound email reply payload."""
    sender_email: str = Field(..., min_length=3, max_length=200, description="Reply sender email")
    subject: str = Field("", max_length=500, description="Email subject")
    body: str = Field("", max_length=10000, description="Email body text")
    tenant_id: Optional[str] = Field(None, description="Tenant ID (optional)")


@router.post("/attribution/email-reply")
def handle_email_reply(
    payload: EmailReplyBody,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    """
    处理（handle_email_reply）：处理相关业务逻辑并返回结果。

    :param payload: 入参 (EmailReplyBody)。
    :param db: 入参 (Session)。
    :param current_user: 入参 (User | None)。

    :return: 返回处理结果（或 None）。
    """
    if current_user is not None and payload.tenant_id:
        from app.services.tenant_scenario_service import resolve_tenant_id_for_user
        user_tenant_id = resolve_tenant_id_for_user(db, current_user)
        if user_tenant_id and payload.tenant_id != user_tenant_id:
            return error_response(403, "无权访问该租户的数据")

    result = create_negotiation_from_email_reply(
        db,
        sender_email=payload.sender_email,
        subject=payload.subject,
        body=payload.body,
        tenant_id=payload.tenant_id,
    )
    if result.get("created"):
        return success_response(data=result, message="谈判会话已创建")
    return error_response(400, result.get("error", "无法创建谈判会话"))
