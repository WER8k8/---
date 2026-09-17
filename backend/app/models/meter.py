# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""统一计量埋点（总纲 §4.6-8 / §6.6 P4 / 迁移总表 086）

meter_events：append-only 计量事件表，只增不改。
7 类埋点动作（§4.6-8）：ai_generation / content_publish / lead_generated /
rfq_created / api_call / export / video_job。
Celery beat 周期汇总进既有计费四表（红线 R3：禁止重建计费）；配额走 plan_gate_service。
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
)

from app.core.database import UUID_TYPE, Base

# §4.6-8：7 类埋点动作
METER_TYPES = (
    "ai_generation",
    "content_publish",
    "lead_generated",
    "rfq_created",
    "api_call",
    "export",
    "video_job",
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class MeterEvent(Base):
    """计量事件（append-only）。event_key 幂等去重；aggregated_at 标记已并入账本。"""
    __tablename__ = "meter_events"
    __table_args__ = (
        Index("ix_meter_events_tenant_occurred", "tenant_id", "occurred_at"),
        Index("ix_meter_events_type_occurred", "meter_type", "occurred_at"),
        Index("ix_meter_events_source", "source_ref_type", "source_ref_id"),
        CheckConstraint(
            "meter_type IN ('ai_generation', 'content_publish', 'lead_generated', "
            "'rfq_created', 'api_call', 'export', 'video_job')",
            name="ck_meter_events_type",
        ),
    )
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(UUID_TYPE, ForeignKey("tenants.id"), nullable=True, index=True)
    event_key = Column(String(100), unique=True, nullable=True, index=True)  # 幂等键
    meter_type = Column(String(30), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)  # 计量数量
    unit = Column(String(20), nullable=False, default="count")
    token_delta = Column(Integer, nullable=False, default=0)  # ai_generation 扣减 token
    cost_cents = Column(Integer, nullable=False, default=0)  # 金额（分），对账锚点
    currency = Column(String(8), nullable=False, default="CNY")
    source_ref_type = Column(String(30), nullable=True)  # task/order/content/lead/rfq/export/video
    source_ref_id = Column(String(100), nullable=True)
    model_name = Column(String(100), nullable=True)
    metadata_json = Column("metadata", JSON, default=dict)
    # 已并入计费账本的时间；NULL=尚未汇总（对账 pending 数依据）
    aggregated_at = Column(DateTime(timezone=True), nullable=True, index=True)
    occurred_at = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
