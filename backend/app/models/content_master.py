# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""统一发布母版 — 一篇内容多发各平台"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, String, Text

from app.core.database import UUID_TYPE, Base


class ContentMaster(Base):
    __tablename__ = "content_masters"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(UUID_TYPE, ForeignKey("tenants.id"), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    body = Column(Text)
    media_urls = Column(JSON, default=list)
    content_type = Column(String(30), default="article")  # article | video_script
    tenant_canonical_url = Column(String(1000))
    status = Column(String(20), default="draft")  # draft | ready | published
    hub_slug = Column(String(200))
    hub_summary = Column(Text)
    show_on_hub = Column(Boolean, default=True)
    hub_published_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(UUID_TYPE, ForeignKey("users.id"), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    preflight_checklist_json = Column(Text, nullable=True)
    preflight_approved_at = Column(DateTime(timezone=True), nullable=True)
    preflight_approved_by = Column(UUID_TYPE, ForeignKey("users.id"), nullable=True)
    # 一核多形的事实内核快照（母版级唯一真源，发布/投影时落库；缺硬事实时如实存降级值）
    fact_kernel_json = Column(JSON, nullable=True)
