# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Outbox / Inbox / DLQ —— 统一消息可靠性层（修正设计稿 模块17 / Production Gate G11）。

目的：
- 业务成功与消息投递解耦：业务事务内追加写 outbox_events（与业务同 commit/rollback），
  派发器异步投递；下游不可用不拖垮业务，业务成功不因消息丢失而断链。
- 消费侧幂等：inbox_events 以 (consumer, event_id) 唯一约束去重，
  重试 / 重放 / 重复回调不会产生重复业务副作用（重复扣费、重复发布）。
- 死信可运营：超过最大重试次数的事件留档 dead_letter_events，可人工复核后重放。

红线：
- outbox 追加写（append-only）：业务侧只 record，不修改 payload；
- 状态推进只允许经 `services.outbox_service`（dispatch_pending / requeue_dead_letter）；
- 无注册消费者的 event_type 保持 pending —— 不伪造"投递成功"（NoFakeDelivery 同纪律）。

首批接入（设计稿）：Inquiry → Billing → Publish → Fulfillment → Logistics → Referral → API Usage；
当前已接：inquiry.created（routes/system.py contact，事务内写入）。
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)

from app.core.database import UUID_TYPE, Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# outbox 事件状态机：pending → processing → published；失败退避回 pending，超限转 dead
OUTBOX_STATUSES = ("pending", "processing", "published", "dead")


class OutboxEvent(Base):
    """待投递业务事件（业务事务内追加写，append-only）。"""
    __tablename__ = "outbox_events"
    __table_args__ = (
        # 派发器领取索引：status + next_retry_at
        Index("ix_outbox_status_next_retry", "status", "next_retry_at"),
        Index("ix_outbox_aggregate", "aggregate_type", "aggregate_id"),
    )

    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(UUID_TYPE, nullable=True, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    aggregate_type = Column(String(60), nullable=True)
    aggregate_id = Column(String(100), nullable=True)
    payload = Column(JSON, default=dict)
    status = Column(String(20), nullable=False, default="pending")
    attempts = Column(Integer, nullable=False, default=0)
    next_retry_at = Column(DateTime(timezone=True), nullable=True)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    published_at = Column(DateTime(timezone=True), nullable=True)


class InboxEvent(Base):
    """消费幂等登记：同一 (consumer, event_id) 只允许成功处理一次。"""
    __tablename__ = "inbox_events"
    __table_args__ = (
        UniqueConstraint("consumer", "event_id", name="uq_inbox_consumer_event"),
    )

    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    consumer = Column(String(100), nullable=False)
    event_id = Column(String(100), nullable=False)  # = outbox_events.id
    event_type = Column(String(100), nullable=True)
    result = Column(String(255), nullable=True)
    processed_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class DeadLetterEvent(Base):
    """死信留档：投递超限事件（payload 内嵌，运营可复核/重放）。"""
    __tablename__ = "dead_letter_events"

    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id = Column(String(100), nullable=False, index=True)  # = outbox_events.id
    event_type = Column(String(100), nullable=True)
    tenant_id = Column(UUID_TYPE, nullable=True)
    reason = Column(String(255), nullable=True)
    payload = Column(JSON, default=dict)
    last_error = Column(Text, nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
