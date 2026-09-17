# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""站点流量与行为埋点（租户站 → 运营看板）。"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Index, String, Text

from app.core.database import UUID_TYPE, Base


class SiteAnalyticsEvent(Base):
    """访客行为事件（无需登录上报）。

    清理策略：生产环境建议通过 PostgreSQL pg_cron 或 Celery Beat
    每日凌晨清理 90 天前的数据（按 created_at 索引裁剪）。
    参见 performance_optimization_service.DataRetentionPolicy。
    """
    __tablename__ = "site_analytics_events"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(UUID_TYPE, index=True, nullable=True)
    agent_node_id = Column(String(64), index=True, nullable=True)
    session_id = Column(String(64), index=True, nullable=False)
    event_type = Column(String(64), nullable=False, index=True)
    page_path = Column(String(500), nullable=True)
    page_title = Column(String(300), nullable=True)
    element_id = Column(String(200), nullable=True)
    element_label = Column(String(300), nullable=True)
    content_ref = Column(String(200), nullable=True, index=True)
    product_id = Column(String(64), nullable=True, index=True)
    merchant_id = Column(String(64), nullable=True, index=True)
    visitor_country = Column(String(64), nullable=True)
    visitor_language = Column(String(16), nullable=True)
    inquiry_id = Column(UUID_TYPE, nullable=True, index=True)
    meta_json = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    __table_args__ = (
        Index("ix_site_analytics_tenant_created", "tenant_id", "created_at"),
        Index("ix_site_analytics_session_created", "session_id", "created_at"),
    )
