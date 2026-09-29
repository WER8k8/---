# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""物流轨迹事件与 Provider 账户（修正设计稿 模块8.4/8.5 / Production Gate G8）。

红线（Gate G8 / 设计稿 8.5）：
- 物流状态必须来自**真实承运商事件**（tracking_events，provider + external_event_id
  幂等唯一）或**人工录入且有操作审计**（source=manual + operator/reason）；
- 没有真实数据 → 展示 tracking_unavailable，**不允许把订单/发运单改成 in_transit**；
- 回归事件（delivered 之后又来 in_transit）被秩序守卫拒绝，不回退状态。
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)

from app.core.database import UUID_TYPE, Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# 规范化物流状态（设计稿 8.5，秩序 = 不可回退顺序）
CANONICAL_TRACKING_STATUSES: tuple[str, ...] = (
    "unknown",
    "label_created",
    "picked_up",
    "departed",
    "in_transit",
    "arrived",
    "customs",
    "out_for_delivery",
    "delivered",
    "exception",
)

TRACKING_STATUS_RANK: dict[str, int] = {s: i for i, s in enumerate(CANONICAL_TRACKING_STATUSES)}


class TrackingEvent(Base):
    """一次真实承运商事件（provider + external_event_id 幂等）。"""

    __tablename__ = "tracking_events"
    __table_args__ = (
        UniqueConstraint("provider", "external_event_id", name="uq_tracking_events_provider_event"),
    )

    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    shipment_id = Column(UUID_TYPE, ForeignKey("logistics_shipments.id"), nullable=True, index=True)
    tracking_no = Column(String(100), nullable=True, index=True)
    tenant_id = Column(UUID_TYPE, nullable=True, index=True)

    provider = Column(String(40), nullable=False)  # kuaidi100 / dhl / manual / …
    external_event_id = Column(String(150), nullable=False)  # 承运商事件唯一 ID（幂等键）
    status = Column(String(30), nullable=False, default="unknown")  # 规范化状态
    location = Column(String(200), nullable=True)
    event_time = Column(DateTime(timezone=True), nullable=True)

    raw_payload_ref = Column(String(255), nullable=True)  # 原始报文落盘引用（可选）
    normalized_payload = Column(JSON, default=dict)
    raw_payload = Column(JSON, default=dict)

    source = Column(String(20), nullable=False, default="provider")  # provider / manual
    operator = Column(String(100), nullable=True)  # manual 审计：操作人
    operator_reason = Column(String(255), nullable=True)  # manual 审计：录入原因

    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class TrackingProviderAccount(Base):
    """Provider 账户登记（凭据引用 + 健康状态；凭据本体存 Vault/环境，不落明文）。"""

    __tablename__ = "tracking_accounts"
    __table_args__ = (
        UniqueConstraint("tenant_id", "provider", name="uq_tracking_accounts_tenant_provider"),
    )

    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(UUID_TYPE, nullable=True, index=True)  # NULL = 平台级账户
    provider = Column(String(40), nullable=False)  # kuaidi100 / dhl / …
    account_ref = Column(String(150), nullable=True)  # 凭据引用（env 键名 / vault 路径）
    status = Column(String(20), nullable=False, default="not_configured")  # not_configured/ready/blocked
    last_health_check_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)
