# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""七步⑤ 本地/租户彩排 — 5a 入站、5b 企微推送、5c 评论入库。"""

from __future__ import annotations

import time
from typing import Any

from sqlalchemy.orm import Session

from app.core.no_fake_delivery import is_production_environment
from app.models.inquiry import Inquiry
from app.services.douyin_comment_pull_service import pull_and_ingest_for_tenant
from app.services.inquiries_unified_service import InquiriesUnifiedService
from app.services.inquiry_push_service import notify_new_public_inquiry
from app.services.sales_push_service import dispatch_text_push


def run_inbound_rehearsal(db: Session, *, tenant_id: str) -> dict[str, Any]:
    """5a · 模拟 Webhook 入站询盘并触发推送链。"""
    ts = int(time.time())
    svc = InquiriesUnifiedService(db)
    lead = svc.create_public_lead(
        name="彩排访客",
        phone="13800138000",
        message=f"【5a彩排·{ts}】想了解岩棉板出口报价",
        source_channel="wecom_inquiry_rehearsal",
        tenant_id=tenant_id,
    )
    inquiry_id = lead.get("id")
    inquiry = db.query(Inquiry).filter(Inquiry.id == inquiry_id).first() if inquiry_id else None
    push_result: dict[str, Any] = {"skipped": True}
    if inquiry:
        push_result = notify_new_public_inquiry(db, inquiry)
    return {
        "step": "5a",
        "inquiry_id": inquiry_id,
        "push": push_result,
    }


async def run_comment_rehearsal(db: Session, *, tenant_id: str) -> dict[str, Any]:
    """5c · 开发彩排评论入库（生产须走 AiToEarn/Inbox）。"""
    if is_production_environment():
        return await pull_and_ingest_for_tenant(db, tenant_id, source="auto")
    return await pull_and_ingest_for_tenant(db, tenant_id, source="rehearsal")


def run_wecom_push_rehearsal(db: Session, *, tenant_id: str) -> dict[str, Any]:
    """5b · 发送测试企微推送（租户或开发平台凭证）。"""
    ts = int(time.time())
    return dispatch_text_push(
        db,
        tenant_id=tenant_id,
        event_type="rehearsal",
        ref_type="rehearsal",
        ref_id=f"rehearsal-{ts}",
        title="【5b彩排】销售通知测试",
        body=f"这是一条彩排消息（{ts}）。若收到说明企微推送已通。",
    )
