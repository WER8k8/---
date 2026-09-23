# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""支付模块模型 - 支付订单与支付渠道配置"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import UUID_TYPE, Base


class PaymentOrder(Base):
    """支付订单"""
    __tablename__ = "payment_orders"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(UUID_TYPE, ForeignKey("tenants.id"), nullable=False, index=True)
    subscription_id = Column(UUID_TYPE, ForeignKey("tenant_subscriptions.id"), nullable=True, index=True)
    order_no = Column(String(100), unique=True, nullable=False, index=True)  # 商户订单号
    amount = Column(Integer, nullable=False, default=0)  # 分
    currency = Column(String(10), default="CNY", nullable=False)
    channel = Column(String(20), nullable=False, index=True)  # wechat/alipay/stripe
    subject = Column(String(200), nullable=False)  # 商品描述
    status = Column(String(20), nullable=False, default="pending", index=True)  # pending/paid/failed/refunded/cancelled/closed/reconciled
    paid_at = Column(DateTime(timezone=True))
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    tenant = relationship("Tenant", lazy="joined")
    subscription = relationship("TenantSubscription", lazy="joined")


class PaymentOpsAudit(Base):
    """支付运维操作审计（探针 / 证书刷新 / staging 自检等）。"""
    __tablename__ = "payment_ops_audit"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    actor_user_id = Column(UUID_TYPE, ForeignKey("users.id"), nullable=True, index=True)
    action = Column(String(64), nullable=False, index=True)
    ok = Column(Boolean, default=False, nullable=False)
    detail = Column(Text, default="{}")
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True
    )


class PaymentChannel(Base):
    """支付渠道配置"""
    __tablename__ = "payment_channels"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    channel = Column(String(20), unique=True, nullable=False, index=True)  # wechat/alipay/stripe
    config = Column(Text, default="{}")  # JSON 配置
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


# 有向迁移：from → 允许的 to（禁止 frozenset 无序边表）
PAYMENT_ORDER_TRANSITIONS: dict[str, frozenset[str]] = {
    "pending": frozenset({"paid", "failed", "cancelled", "closed"}),
    "paid": frozenset({"refunded", "reconciled", "closed"}),
    "failed": frozenset({"pending", "cancelled", "closed"}),
    "reconciled": frozenset({"refunded"}),
    "cancelled": frozenset(),
    "closed": frozenset(),
    "refunded": frozenset(),
}


def payment_order_can_transition(from_status: str, to_status: str) -> bool:
    """有向状态机判定。"""
    return to_status in PAYMENT_ORDER_TRANSITIONS.get(from_status, frozenset())


# 退款单有向迁移
REFUND_STATUSES = frozenset(
    {
        "pending_review",
        "approved",
        "rejected",
        "processing",
        "completed",
        "failed",
        "cancelled",
    }
)

REFUND_TRANSITIONS: dict[str, frozenset[str]] = {
    "pending_review": frozenset({"approved", "rejected", "cancelled"}),
    "approved": frozenset({"processing", "cancelled"}),
    "processing": frozenset({"completed", "failed"}),
    "failed": frozenset({"processing", "cancelled"}),
    "completed": frozenset(),
    "rejected": frozenset(),
    "cancelled": frozenset(),
}


def refund_can_transition(from_status: str, to_status: str) -> bool:
    """退款单有向状态机判定。"""
    return to_status in REFUND_TRANSITIONS.get(from_status, frozenset())


class PaymentRefund(Base):
    """退款申请单 — 超管审核 approve/reject 后再触达通道，禁止跳过人审假成功。"""
    __tablename__ = "payment_refunds"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id = Column(UUID_TYPE, ForeignKey("payment_orders.id"), nullable=False, index=True)
    order_no = Column(String(100), nullable=False, index=True)
    tenant_id = Column(UUID_TYPE, ForeignKey("tenants.id"), nullable=False, index=True)
    amount = Column(Integer, nullable=False, default=0)  # 分
    currency = Column(String(10), default="CNY", nullable=False)
    reason = Column(Text)
    status = Column(String(20), nullable=False, default="pending_review", index=True)
    reject_reason = Column(Text)
    channel = Column(String(20))
    channel_refund_id = Column(String(120))
    result_message = Column(Text)
    requested_by = Column(UUID_TYPE, ForeignKey("users.id"), nullable=True)
    reviewed_by = Column(UUID_TYPE, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True))
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class PaymentCompensationTask(Base):
    """支付权益发放补偿任务（BUG-02 修复）。

    当支付回调处理成功（订单置为 paid）但权益发放失败时，
    创建此任务记录，供定时巡检重试直到发放成功。
    """
    __tablename__ = "payment_compensation_tasks"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    order_no = Column(String(100), nullable=False, index=True)
    source = Column(String(32), nullable=False, default="unknown")  # wechat_notify / alipay_notify / mock_pay
    status = Column(String(16), nullable=False, default="pending")  # pending / processing / completed / failed
    attempts = Column(Integer, nullable=False, default=0)
    max_attempts = Column(Integer, nullable=False, default=10)
    last_error = Column(Text, nullable=True)
    scheduled_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
