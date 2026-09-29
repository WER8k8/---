# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""第二层补充缺口 E · 成本事件与单位经济模型（Cost Event）。

记录 AI Token、Browser 运行、IP 代理、第三方 API 等直接成本，与 Meter Event 形成收入与成本对称账本。
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Index,
    JSON,
    String,
)

from app.core.database import UUID_TYPE, Base


class CostEvent(Base):
    """直接成本事件表（append-only 账本）。"""

    __tablename__ = "cost_events"

    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(UUID_TYPE, nullable=True, index=True)
    # cost.ai.token / cost.browser.runtime / cost.egress.proxy / cost.platform.api / cost.logistics.tracking
    cost_code = Column(String(80), nullable=False, index=True)
    cost_category = Column(String(30), nullable=False, index=True)  # ai, browser, platform, logistics, infra
    amount = Column(Float, nullable=False, default=0.0)  # 成本金额（USD）
    currency = Column(String(10), default="USD", nullable=False)
    quantity = Column(Float, default=1.0, nullable=False)
    unit = Column(String(30), default="unit", nullable=False)  # tokens, seconds, calls, mb
    subject_type = Column(String(50), nullable=True)  # task, inquiry, boq, shipment
    subject_id = Column(String(100), nullable=True, index=True)
    provider = Column(String(50), nullable=True)  # deepseek, openrouter, brightdata, kuaidi100
    meta_json = Column("metadata", JSON, default=dict)
    occurred_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        Index("idx_cost_events_tenant_occurred", "tenant_id", "occurred_at"),
        Index("idx_cost_events_category", "cost_category", "cost_code"),
    )
