# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""出海计 App — 推送设备注册。"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, String

from app.core.database import UUID_TYPE, Base


class AppDevice(Base):
    __tablename__ = "app_devices"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(UUID_TYPE, nullable=False, index=True)
    tenant_id = Column(UUID_TYPE, nullable=True, index=True)
    device_token = Column(String(512), nullable=False)
    platform = Column(String(32), nullable=False, default="web")  # ios | android | web
    app_version = Column(String(32), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
