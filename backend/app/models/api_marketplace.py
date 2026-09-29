# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""轨7 API 市场三表（模块13 / 修正设计稿 13.2）。

- 密钥只存 sha256 hash（明文仅签发响应返回一次，绝不落库）；
- 产品生命周期 draft→review→published→suspended→deprecated（forward-only 守卫）；
- 订阅一租户一产品一条（唯一约束），active/suspended/cancelled；
- 计量走统一链：调用 → meter_events(api_call/api.request) → finance_ledger（无第二账本）。
契约：docs/模块13-轨7API市场收口契约-2026-09-28.md
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)

from app.core.database import UUID_TYPE, Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


PRODUCT_STATUSES = ("draft", "review", "published", "suspended", "deprecated")

LEGAL_PRODUCT_TRANSITIONS: dict[str, tuple[str, ...]] = {
    "draft": ("review",),
    "review": ("published",),
    "published": ("suspended", "deprecated"),
    "suspended": ("published", "deprecated"),
    "deprecated": (),
}

SUBSCRIPTION_STATUSES = ("active", "suspended", "cancelled")

LEGAL_SUBSCRIPTION_TRANSITIONS: dict[str, tuple[str, ...]] = {
    "active": ("suspended", "cancelled"),
    "suspended": ("active", "cancelled"),
    "cancelled": (),
}


class ApiProduct(Base):
    """对外销售的 API 产品（轨7 商品面）。"""

    __tablename__ = "api_products"
    __table_args__ = (
        UniqueConstraint("name", "version", name="uq_api_products_name_version"),
    )

    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_tenant_id = Column(UUID_TYPE, nullable=True, index=True)  # 空 = 平台自营
    name = Column(String(120), nullable=False)
    version = Column(String(20), nullable=False, default="v1")
    status = Column(String(20), nullable=False, default="draft", index=True)
    pricing_rule_id = Column(String(60), nullable=True)  # billing_pricing_rules.rule_id
    scope = Column(String(200), nullable=False, default="")
    rate_limit_per_day = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class ApiKey(Base):
    """消费方 API Key（只存 hash，明文不落库）。"""

    __tablename__ = "api_keys"
    __table_args__ = (
        Index("ix_api_keys_tenant", "tenant_id"),
    )

    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(UUID_TYPE, nullable=False)
    key_hash = Column(String(64), nullable=False, unique=True)  # sha256 hex
    key_prefix = Column(String(16), nullable=False)  # 明文前 12 位（脱敏展示）
    label = Column(String(120), nullable=True)
    scopes = Column(String(500), nullable=False, default="")
    expires_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class ApiSubscription(Base):
    """消费方 ↔ 产品的订阅关系（一租户一产品一条）。"""

    __tablename__ = "api_subscriptions"
    __table_args__ = (
        UniqueConstraint(
            "consumer_tenant_id", "api_product_id", name="uq_api_subscriptions_tenant_product"
        ),
        Index("ix_api_subscriptions_consumer", "consumer_tenant_id"),
    )

    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    consumer_tenant_id = Column(UUID_TYPE, nullable=False)
    api_product_id = Column(
        UUID_TYPE,
        ForeignKey("api_products.id", name="fk_api_subscriptions_product", ondelete="CASCADE"),
        nullable=False,
    )
    plan = Column(String(30), nullable=False, default="free")
    quota_per_day = Column(Integer, nullable=True)
    status = Column(String(20), nullable=False, default="active", index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)
