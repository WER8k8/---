# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""营销归因模型（修正设计稿 模块6 / Production Gate G5）。

- marketing_touchpoints：平台内容 → 点击 → 回站 的每一次触点
  （channel/platform/campaign/content/landing/utm_*/gclid/external_post_id）。
- inquiry_attributions：询盘的 first-touch / last-touch / conversion-touch 快照，
  **snapshot_json 不可变**——归因历史不随模型调整重算（设计稿 6.3）。

防伪（设计稿 6.6）：前端不直接提交 tenant_id / commission_id；
归属由后端 Host/会话解析 + signed attribution token 校验（服务层）。
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Index, String, Text

from app.core.database import UUID_TYPE, Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class MarketingTouchpoint(Base):
    """一次回站触点（append-only）。"""

    __tablename__ = "marketing_touchpoints"
    __table_args__ = (
        Index("ix_mtp_tenant_session", "tenant_id", "session_id"),
        Index("ix_mtp_platform_content", "platform", "content_id"),
        Index("ix_mtp_occurred", "occurred_at"),
    )

    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(UUID_TYPE, nullable=False, index=True)
    visitor_id = Column(String(64), nullable=True, index=True)
    session_id = Column(String(64), nullable=True)

    channel = Column(String(40), nullable=True)  # seo / geo / video / social / direct
    platform = Column(String(40), nullable=True)  # 分发平台（platforms 目录键）
    campaign_id = Column(String(64), nullable=True)
    content_id = Column(String(64), nullable=True)
    landing_url = Column(String(500), nullable=True)
    referrer = Column(String(500), nullable=True)

    utm_source = Column(String(80), nullable=True)
    utm_medium = Column(String(80), nullable=True)
    utm_campaign = Column(String(120), nullable=True)
    utm_content = Column(String(120), nullable=True)
    utm_term = Column(String(120), nullable=True)
    gclid = Column(String(120), nullable=True)
    external_post_id = Column(String(150), nullable=True)  # 分发侧帖子 ID（归因锚点）

    occurred_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, index=True)


class InquiryAttribution(Base):
    """询盘归因快照（一询盘一行；snapshot 不可变）。"""

    __tablename__ = "inquiry_attributions"
    __table_args__ = (
        Index("ix_inq_attr_inquiry", "inquiry_id"),
    )

    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    inquiry_id = Column(UUID_TYPE, ForeignKey("inquiries.id"), nullable=False, index=True)
    tenant_id = Column(UUID_TYPE, nullable=False, index=True)

    first_touch_id = Column(UUID_TYPE, nullable=True)
    last_touch_id = Column(UUID_TYPE, nullable=True)
    conversion_touch_id = Column(UUID_TYPE, nullable=True)
    attribution_model = Column(String(30), nullable=False, default="last_touch")
    snapshot_json = Column(JSON, default=dict)  # 归因快照（不可变）

    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
