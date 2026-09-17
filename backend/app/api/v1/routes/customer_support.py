# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""多渠道海外客服路由。"""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.core.security import get_current_user
from app.models.user import User
from app.services.omnichannel_support_service import OmnichannelSupportService

router = APIRouter(prefix="/support/omnichannel", tags=["Customer Support"])

ROUTE_PREFIX = ""
ROUTE_TAGS = ["Customer Support"]


class MessageInboundRequest(BaseModel):
    tenant_id: str
    channel: str = Field(default="livechat", description="livechat / whatsapp")
    sender_id: str
    message: str


@router.post("/message", summary="处理买家多渠道进线咨询")
def handle_message(
    req: MessageInboundRequest,
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    svc = OmnichannelSupportService()
    res = svc.handle_visitor_inquiry(
        tenant_id=req.tenant_id,
        channel=req.channel,
        sender_id=req.sender_id,
        message=req.message,
    )
    return {"code": 0, "msg": "ok", "data": res}
