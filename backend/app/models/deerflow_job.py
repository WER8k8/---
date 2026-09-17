# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""DeerFlow / UBrain-X 异步任务队列。"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, String, Text

from app.core.database import UUID_TYPE, Base


class DeerflowJob(Base):
    __tablename__ = "deerflow_jobs"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(UUID_TYPE, ForeignKey("tenants.id"), nullable=False, index=True)
    intent = Column(String(64), nullable=False, index=True)
    status = Column(
        String(20),
        default="queued",
        nullable=False,
        index=True,
    )  # queued | running | success | failed
    payload_json = Column(Text, default="{}")
    result_json = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    log_text = Column(Text, default="")
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
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)
