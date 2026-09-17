# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Lane P · 销售推送事件（企微应用消息 / 群机器人）。"""

from __future__ import annotations

import uuid as _uuid_lib

from sqlalchemy import Column, DateTime, Integer, String, Text, JSON
from sqlalchemy.sql import func

from app.core.database import Base


class PushEvent(Base):
    __tablename__ = "push_events"
    id = Column(String(36), primary_key=True, default=lambda: str(_uuid_lib.uuid4()))
    tenant_id = Column(String(36), nullable=True, index=True)
    event_type = Column(String(50), nullable=False, index=True)  # social_comment | inquiry_new
    ref_type = Column(String(50), nullable=False)  # social_interaction | inquiry
    ref_id = Column(String(36), nullable=False, index=True)
    channel = Column(String(32), nullable=False, default="wecom_app")  # wecom_app | wecom_webhook
    recipient = Column(String(200), nullable=True)
    title = Column(String(200), nullable=False, default="")
    body = Column(Text, nullable=False, default="")
    status = Column(String(20), nullable=False, default="pending", index=True)  # pending|sent|failed
    upstream_msgid = Column(String(128), nullable=True)
    upstream_receipt = Column(JSON, nullable=True)
    error_code = Column(String(64), nullable=True)
    error_message = Column(String(500), nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
