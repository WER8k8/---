# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""客户侧新增/自填平台与租户的关联审计（仅超管可见，客户 API 不暴露）。"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, JSON, String

from app.core.database import UUID_TYPE, Base


class PlatformTenantOrigin(Base):
    __tablename__ = "platform_tenant_origins"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(UUID_TYPE, ForeignKey("tenants.id"), nullable=False, index=True)
    platform_id = Column(UUID_TYPE, ForeignKey("platforms.id"), nullable=False, index=True)
    source = Column(String(64), nullable=False, index=True)
    tenant_name = Column(String(200), nullable=True)
    platform_name = Column(String(200), nullable=False)
    is_new_platform = Column(Boolean, default=False, nullable=False)
    nurture_rules = Column(JSON, nullable=True)
    browser_profile_id = Column(UUID_TYPE, ForeignKey("browser_profiles.id"), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )


# 兼容重导出：PlatformAccount 物理定义在 app.models.content
try:
    from app.models.content import PlatformAccount  # noqa: F401
except ImportError:
    pass
