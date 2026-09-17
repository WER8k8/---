# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Hermes 插件安装态（租户级）。"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text, UniqueConstraint

from app.core.database import UUID_TYPE, Base


class HermesPluginInstall(Base):
    __tablename__ = "hermes_plugin_installs"
    __table_args__ = (
        UniqueConstraint("tenant_id", "plugin_id", name="uq_hermes_plugin_tenant"),
    )
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(UUID_TYPE, ForeignKey("tenants.id"), nullable=False, index=True)
    plugin_id = Column(String(64), nullable=False, index=True)
    plugin_version = Column(String(32), nullable=False, default="1.0.0")
    enabled = Column(Boolean, nullable=False, default=True)
    config_json = Column(Text, default="{}")
    installed_by = Column(UUID_TYPE, ForeignKey("users.id"), nullable=True)
    installed_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
