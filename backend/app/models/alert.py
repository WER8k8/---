# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""告警中心模型"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (Boolean, Column, DateTime, Float, Integer, String,
                        Text)
from sqlalchemy import JSON

from app.core.database import UUID_TYPE, Base


class AlertRule(Base):
    """告警规则"""
    __tablename__ = "alert_rules"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    category = Column(String(30), nullable=False, index=True)
    # cc_switch_down, cost_spike, indexing_drop, ai_error_rate
    metric_key = Column(String(50), nullable=False)
    operator = Column(String(10), nullable=False, default="gt")  # gt, lt, eq
    threshold = Column(Float, nullable=False)
    duration_minutes = Column(Integer, default=5)
    cooldown_minutes = Column(Integer, default=30)
    enabled = Column(Boolean, default=True, nullable=False)
    notify_feishu = Column(Boolean, default=True)
    notify_webhook_url = Column(String(300))
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


class AlertEvent(Base):
    """告警事件记录"""
    __tablename__ = "alert_events"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    rule_id = Column(UUID_TYPE, nullable=True, index=True)
    rule_name = Column(String(100), nullable=False)
    category = Column(String(30), nullable=False, index=True)
    level = Column(String(20), nullable=False, default="warning")  # info, warning, critical
    title = Column(String(200), nullable=False)
    message = Column(Text)
    metric_value = Column(Float)
    threshold = Column(Float)
    status = Column(String(20), default="open", index=True)  # open, acknowledged, resolved
    acknowledged_by = Column(String(100))
    acknowledged_at = Column(DateTime(timezone=True))
    resolved_at = Column(DateTime(timezone=True))
    extra_json = Column(JSON, default=dict)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
