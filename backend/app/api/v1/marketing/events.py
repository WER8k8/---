# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""营销转化事件与服务端离线回传 API。

捕获外贸核心商业漏斗事件：
- generate_lead（询盘提交）
- whatsapp_click（WhatsApp 沟通）
- boq_calculated（BOQ 22参数配载测算）
- doc_downloaded（资质报告下载）
- view_item（高净值产品查看）
"""

import logging
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.response import success_response

router = APIRouter(prefix="/marketing", tags=["外贸营销转化打点"])
logger = logging.getLogger(__name__)


class MarketingEventRequest(BaseModel):
    event_name: str
    tenant_id: Optional[str] = None
    product_slug: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None
    page_url: Optional[str] = None


@router.post("/events")
async def collect_marketing_event(
    event: MarketingEventRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """接收前端或服务端的营销高价值转化事件，沉淀离线归因与智能出价真值。"""
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "")

    logger.info(
        "MarketingEventCaptured: event=%s product=%s tenant=%s ip=%s",
        event.event_name,
        event.product_slug,
        event.tenant_id,
        client_ip,
    )

    # 返回记录成功（未来可直接对接 Google Ads Offline Conversion API）
    return success_response(
        data={
            "received": True,
            "event_name": event.event_name,
            "product_slug": event.product_slug,
        },
        message="营销事件已记录",
    )
