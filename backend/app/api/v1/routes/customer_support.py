"""多渠道海外客服路由。"""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.omnichannel_support_service import OmnichannelSupportService

router = APIRouter(prefix="/support/omnichannel", tags=["Customer Support"])

ROUTE_PREFIX = "/support/omnichannel"
ROUTE_TAGS = ["Customer Support"]


class MessageInboundRequest(BaseModel):
    tenant_id: str
    channel: str = Field(default="livechat", description="livechat / whatsapp")
    sender_id: str
    message: str


@router.post("/message", summary="处理买家多渠道进线咨询")
def handle_message(req: MessageInboundRequest) -> dict[str, Any]:
    svc = OmnichannelSupportService()
    res = svc.handle_visitor_inquiry(
        tenant_id=req.tenant_id,
        channel=req.channel,
        sender_id=req.sender_id,
        message=req.message,
    )
    return {"code": 0, "msg": "ok", "data": res}
