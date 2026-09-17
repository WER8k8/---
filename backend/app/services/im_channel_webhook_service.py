# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""七步⑤：企微 / 抖音私信 → 统一询盘入库（框架 webhook 入口）。"""

from __future__ import annotations

from typing import Any, Optional

from sqlalchemy.orm import Session

from app.services.inquiries_unified_service import InquiriesUnifiedService


def ingest_channel_inquiry(
    db: Session,
    *,
    channel: str,
    name: str,
    phone: str,
    message: str,
    merchant_id: Optional[str] = None,
    extra: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """将第三方渠道消息写入统一询盘表。"""
    prefix = f"[{channel}]"
    body = message or "渠道私信询盘"
    if extra:
        body = f"{body}\nmeta={extra}"
    svc = InquiriesUnifiedService(db)
    return svc.create_public_lead(
        name=name[:120] or "渠道访客",
        message=body,
        phone=phone,
        email=None,
        product=None,
        source_channel=channel,
        merchant_id=merchant_id,
    )
