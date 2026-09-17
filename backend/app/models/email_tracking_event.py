# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""邮件追踪事件模型（P1-3）—— 打开/点击/回复事件记录。"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, JSON, String

from app.core.database import Base, UUID_TYPE


class EmailEventType(str, enum.Enum):
    """邮件事件类型"""
    SENT = "sent"
    OPEN = "open"
    CLICK = "click"
    REPLY = "reply"


class EmailTrackingEvent(Base):
    """邮件追踪事件 —— 像素回调 / 链接点击 / 回复检测。"""
    __tablename__ = "email_tracking_events"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    message_id = Column(String(100), nullable=False, index=True)  # 关联发送记录
    lead_id = Column(UUID_TYPE, ForeignKey("prospect_leads.id"), nullable=True, index=True)
    tenant_id = Column(UUID_TYPE, ForeignKey("tenants.id"), nullable=True, index=True)
    user_id = Column(UUID_TYPE, ForeignKey("users.id"), nullable=True, index=True)
    # 事件类型：sent / open / click / reply
    event_type = Column(
        Enum(EmailEventType, name="email_event_type_enum"),
        nullable=False,
        index=True,
    )
    # 请求信息
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    referer = Column(String(500), nullable=True)
    # 点击专用
    clicked_url = Column(String(1000), nullable=True)
    # 元数据
    event_metadata = Column(JSON, default=dict)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
