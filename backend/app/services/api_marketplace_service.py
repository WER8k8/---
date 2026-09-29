# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""轨7 API 市场（模块13 / T13）——产品、密钥、订阅与 api.request 统一计量。

红线：
- 密钥只存 sha256 hash，明文仅在签发响应中返回一次，绝不落库/入日志；
- 计量走统一链：调用 → meter_events(meter_type=api_call, meter_code=api.request)
  → aggregate_to_billing → finance_ledger（api_call ∈ REVENUE_METER_TYPES），
  禁止第二套计费账本（R3）；
- 鉴权 fail-closed：hash 不匹配 / 吊销 / 过期 / scope 不符 / 产品未发布 /
  订阅非 active / 超每日期量 → 一律拒绝且**零计量**。

契约：docs/模块13-轨7API市场收口契约-2026-09-28.md
"""

from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.api_marketplace import (
    LEGAL_PRODUCT_TRANSITIONS,
    LEGAL_SUBSCRIPTION_TRANSITIONS,
    ApiKey,
    ApiProduct,
    ApiSubscription,
)
from app.services.billing.meter_event import MeterEventService

_API_REQUEST_METER_CODE = "api.request"
_API_KEY_SUBJECT_TYPE = "api_key"
_KEY_SECRET_LENGTH = 32  # 生成 32 字节 → 43 字符 url-safe base64


class ApiMarketError(Exception):
    """轨7 市场域错误基类（路由层映射 4xx）。"""


class InvalidApiKey(ApiMarketError):
    pass


class ApiKeyRevoked(ApiMarketError):
    pass


class ApiKeyExpired(ApiMarketError):
    pass


class ScopeDenied(ApiMarketError):
    pass


class ProductNotCallable(ApiMarketError):
    pass


class SubscriptionInactive(ApiMarketError):
    pass


class QuotaExceeded(ApiMarketError):
    pass


class IllegalTransition(ApiMarketError):
    pass


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _aware(dt: Optional[datetime]) -> Optional[datetime]:
    """naive（sqlite 存储）视为 UTC，避免 naive/aware 比较抛 TypeError。"""
    if dt is None:
        return None
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)


def _hash_key(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def generate_api_key() -> tuple[str, str]:
    """生成 (明文, 展示前缀)。明文只在签发响应返回一次。"""
    raw = "ujk_" + secrets.token_urlsafe(_KEY_SECRET_LENGTH)
    return raw, raw[:12]


# ---------------------------------------------------------------- 产品

def create_product(
    db: Session,
    *,
    name: str,
    version: str = "v1",
    owner_tenant_id: Optional[str] = None,
    scope: str = "",
    rate_limit_per_day: Optional[int] = None,
    description: Optional[str] = None,
    pricing_rule_id: Optional[str] = None,
) -> ApiProduct:
    product = ApiProduct(
        name=(name or "").strip(),
        version=(version or "v1").strip(),
        owner_tenant_id=owner_tenant_id,
        scope=(scope or "").strip(),
        rate_limit_per_day=rate_limit_per_day,
        description=description,
        pricing_rule_id=pricing_rule_id,
        status="draft",
    )
    if not product.name:
        raise ValueError("产品名不可为空")
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def transition_product(db: Session, product: ApiProduct, to_status: str) -> ApiProduct:
    allowed = LEGAL_PRODUCT_TRANSITIONS.get(product.status, ())
    if to_status not in allowed:
        raise IllegalTransition(
            f"产品状态流转被拒绝: {product.status} → {to_status}（允许: {list(allowed)}）"
        )
    product.status = to_status
    db.commit()
    db.refresh(product)
    return product


# ---------------------------------------------------------------- Key

def issue_key(
    db: Session,
    *,
    tenant_id: str,
    label: Optional[str] = None,
    scopes: str = "",
    expires_at: Optional[datetime] = None,
) -> dict:
    """签发 API Key。返回含明文（api_key）的 dict——明文仅此一次，不落库。"""
    raw, prefix = generate_api_key()
    row = ApiKey(
        tenant_id=tenant_id,
        key_hash=_hash_key(raw),
        key_prefix=prefix,
        label=label,
        scopes=(scopes or "").strip(),
        expires_at=expires_at,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": str(row.id), "api_key": raw, "key_prefix": prefix, "scopes": row.scopes}


def revoke_key(db: Session, key_id: str, *, tenant_id: Optional[str] = None) -> ApiKey:
    row = db.query(ApiKey).filter(ApiKey.id == key_id).first()
    if row is None:
        raise InvalidApiKey(f"API Key 不存在: {key_id}")
    if tenant_id is not None and str(row.tenant_id) != str(tenant_id):
        raise ScopeDenied("无权吊销他人租户的 Key")
    if row.revoked_at is None:
        row.revoked_at = _utcnow()
        db.commit()
        db.refresh(row)
    return row


def list_keys(db: Session, tenant_id: str) -> list[ApiKey]:
    return (
        db.query(ApiKey)
        .filter(ApiKey.tenant_id == tenant_id)
        .order_by(ApiKey.created_at.desc())
        .all()
    )


def resolve_api_key(db: Session, raw_key: str) -> ApiKey:
    """X-API-Key → ApiKey 行（fail-closed）。"""
    raw = (raw_key or "").strip()
    if len(raw) < 20:
        raise InvalidApiKey("API Key 缺失或格式非法")
    row = db.query(ApiKey).filter(ApiKey.key_hash == _hash_key(raw)).first()
    if row is None:
        raise InvalidApiKey("API Key 无效")
    if row.revoked_at is not None:
        raise ApiKeyRevoked("API Key 已吊销")
    expires = _aware(row.expires_at)
    if expires is not None and expires < _utcnow():
        raise ApiKeyExpired("API Key 已过期")
    return row


# ---------------------------------------------------------------- 订阅

def subscribe(
    db: Session,
    *,
    consumer_tenant_id: str,
    api_product: ApiProduct,
    plan: str = "free",
    quota_per_day: Optional[int] = None,
) -> ApiSubscription:
    if api_product.status != "published":
        raise ProductNotCallable(
            f"产品不可订阅（status={api_product.status}，须 published）"
        )
    exists = (
        db.query(ApiSubscription)
        .filter(
            ApiSubscription.consumer_tenant_id == consumer_tenant_id,
            ApiSubscription.api_product_id == api_product.id,
        )
        .first()
    )
    if exists is not None:
        raise IllegalTransition("同一租户对同一产品已有订阅（不可重复订阅）")
    row = ApiSubscription(
        consumer_tenant_id=consumer_tenant_id,
        api_product_id=api_product.id,
        plan=plan,
        quota_per_day=quota_per_day,
        status="active",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def transition_subscription(
    db: Session, subscription: ApiSubscription, to_status: str
) -> ApiSubscription:
    allowed = LEGAL_SUBSCRIPTION_TRANSITIONS.get(subscription.status, ())
    if to_status not in allowed:
        raise IllegalTransition(
            f"订阅状态流转被拒绝: {subscription.status} → {to_status}（允许: {list(allowed)}）"
        )
    subscription.status = to_status
    db.commit()
    db.refresh(subscription)
    return subscription


# ---------------------------------------------------------------- 鉴权 + 计量

def _effective_daily_quota(
    product: ApiProduct, subscription: ApiSubscription
) -> Optional[int]:
    limits = [v for v in (product.rate_limit_per_day, subscription.quota_per_day) if v]
    return min(limits) if limits else None


def _api_request_count_today(db: Session, key_id: str) -> int:
    from app.models.meter import MeterEvent

    day_start = _utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    return int(
        db.query(func.count(MeterEvent.id))
        .filter(
            MeterEvent.subject_type == _API_KEY_SUBJECT_TYPE,
            MeterEvent.subject_id == key_id,
            MeterEvent.meter_code == _API_REQUEST_METER_CODE,
            MeterEvent.occurred_at >= day_start,
        )
        .scalar()
        or 0
    )


def authorize_call(
    db: Session,
    *,
    raw_key: str,
    product: ApiProduct,
    scope_required: Optional[str] = None,
) -> ApiKey:
    """鉴权 + 配额 + 计量（一次真实调用 = 一条 api.request 计量）。

    任一环节失败即抛错且**零计量**；全部通过才 emit。
    """
    key = resolve_api_key(db, raw_key)

    scopes = [s.strip() for s in (key.scopes or "").split(",") if s.strip()]
    if scope_required is not None and scope_required not in scopes:
        raise ScopeDenied(f"Key scopes 不含 {scope_required!r}")

    if product.status != "published":
        raise ProductNotCallable(f"产品不可调用（status={product.status}）")

    subscription = (
        db.query(ApiSubscription)
        .filter(
            ApiSubscription.consumer_tenant_id == key.tenant_id,
            ApiSubscription.api_product_id == product.id,
        )
        .first()
    )
    if subscription is None or subscription.status != "active":
        raise SubscriptionInactive("无有效订阅（不存在或非 active）")

    quota = _effective_daily_quota(product, subscription)
    if quota is not None and _api_request_count_today(db, str(key.id)) >= quota:
        raise QuotaExceeded(f"超出每日期量 {quota}")

    # 计量（统一链）：api.request，append-only，每次真实调用一条
    MeterEventService(db).emit(
        meter_type="api_call",
        tenant_id=str(key.tenant_id),
        event_key=f"api_req:{uuid.uuid4().hex}",
        quantity=1,
        unit="call",
        meter_code=_API_REQUEST_METER_CODE,
        subject_type=_API_KEY_SUBJECT_TYPE,
        subject_id=str(key.id),
        metadata={
            "product_id": str(product.id),
            "product_name": product.name,
            "subscription_id": str(subscription.id),
            "plan": subscription.plan,
        },
    )
    key.last_used_at = _utcnow()
    db.commit()
    return key


def meter_request(
    db: Session,
    *,
    raw_key: str,
    product_name: str,
    scope_required: Optional[str] = None,
) -> ApiKey:
    """便捷入口：按产品名取 published 产品并 authorize_call（echo 端点用）。"""
    product = (
        db.query(ApiProduct)
        .filter(ApiProduct.name == product_name, ApiProduct.status == "published")
        .order_by(ApiProduct.created_at.desc())
        .first()
    )
    if product is None:
        raise ProductNotCallable(f"产品不存在或未发布: {product_name}")
    return authorize_call(db, raw_key=raw_key, product=product, scope_required=scope_required)


def daily_quota_remaining(db: Session, key: ApiKey, product: ApiProduct) -> Optional[int]:
    """剩余配额（运维/展示用；None = 不限）。"""
    subscription = (
        db.query(ApiSubscription)
        .filter(
            ApiSubscription.consumer_tenant_id == key.tenant_id,
            ApiSubscription.api_product_id == product.id,
        )
        .first()
    )
    quota = _effective_daily_quota(product, subscription) if subscription else product.rate_limit_per_day
    if quota is None:
        return None
    return max(0, quota - _api_request_count_today(db, str(key.id)))


def expire_check_purge_candidates(db: Session, *, older_than_days: int = 30) -> list[str]:
    """（运维辅助）列出早已过期且吊销超过 N 天的 Key id——只读，不删。"""
    cutoff = _utcnow() - timedelta(days=older_than_days)
    rows = (
        db.query(ApiKey.id)
        .filter(ApiKey.expires_at.isnot(None), ApiKey.expires_at < cutoff)
        .all()
    )
    return [str(r[0]) for r in rows]
