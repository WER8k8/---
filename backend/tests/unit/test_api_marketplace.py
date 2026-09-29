# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""模块13 · 轨7 API 市场 —— 配对反证测试（契约 §6）。

- 明文只返回一次、库内仅 hash、prefix 脱敏；
- 正向：published + active 订阅 + scope 命中 → 放行且 api.request 计量 +1；
- 负向六连（无效/吊销/过期/scope 不符/产品未发布/订阅非 active）→ 全拒且零计量；
- 配额：quota=2 → 第 3 次 429（前 2 次有计量）；
- 生命周期：产品 forward-only 守卫、deprecated 终态；订阅重复/未发布拒。
"""
from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.models.api_marketplace import ApiKey, ApiProduct, ApiSubscription
from app.models.meter import MeterEvent
from app.services import api_marketplace_service as svc
from app.services.api_marketplace_service import (
    ApiKeyExpired,
    ApiKeyRevoked,
    IllegalTransition,
    InvalidApiKey,
    ProductNotCallable,
    QuotaExceeded,
    ScopeDenied,
    SubscriptionInactive,
)

TENANT_A = "5c333333-3333-4333-8333-333333333333"
TENANT_B = "5c444444-4444-4444-8444-444444444444"


def _published_product(db, **kw) -> ApiProduct:
    p = svc.create_product(db, name=kw.pop("name", f"echo-{uuid.uuid4().hex[:8]}"), **kw)
    svc.transition_product(db, p, "review")
    svc.transition_product(db, p, "published")
    return p


def _issued_key(db, *, scopes="echo:read", **kw) -> dict:
    return svc.issue_key(db, tenant_id=kw.pop("tenant_id", TENANT_A), scopes=scopes, **kw)


def _api_request_count(db, key_id: str) -> int:
    return (
        db.query(MeterEvent)
        .filter(MeterEvent.subject_type == "api_key", MeterEvent.subject_id == key_id)
        .count()
    )


class TestKeyIssuance:
    def test_plaintext_returned_once_hash_only_in_db(self, db_session):
        issued = _issued_key(db_session)
        raw = issued["api_key"]
        assert raw.startswith("ujk_") and len(raw) >= 32

        row = db_session.query(ApiKey).filter(ApiKey.id == issued["id"]).one()
        assert row.key_hash == hashlib.sha256(raw.encode()).hexdigest()
        assert row.key_hash != raw and raw not in (row.key_hash or "")
        # 全行任何字段都不含明文
        for col in ("key_hash", "key_prefix", "label", "scopes"):
            assert raw not in str(getattr(row, col))
        assert issued["key_prefix"] == raw[:12]

    def test_hash_unique_collision_rejected(self, db_session):
        raw = "ujk_" + uuid.uuid4().hex
        from app.models.api_marketplace import ApiKey as K

        db_session.add(K(
            tenant_id=TENANT_A, key_hash=hashlib.sha256(raw.encode()).hexdigest(),
            key_prefix=raw[:12], scopes="",
        ))
        db_session.commit()
        dup = K(
            tenant_id=TENANT_B, key_hash=hashlib.sha256(raw.encode()).hexdigest(),
            key_prefix=raw[:12], scopes="",
        )
        db_session.add(dup)
        with pytest.raises(Exception):
            db_session.commit()
        db_session.rollback()


class TestAuthorizePositive:
    def test_valid_call_bills_api_request(self, db_session):
        product = _published_product(db_session)
        issued = _issued_key(db_session, scopes="echo:read")
        sub = svc.subscribe(db_session, consumer_tenant_id=TENANT_A, api_product=product)

        key = svc.authorize_call(
            db_session, raw_key=issued["api_key"], product=product, scope_required="echo:read"
        )

        assert str(key.id) == issued["id"]
        assert _api_request_count(db_session, issued["id"]) == 1
        ev = (
            db_session.query(MeterEvent)
            .filter(MeterEvent.subject_id == issued["id"])
            .one()
        )
        assert ev.meter_code == "api.request"
        assert ev.meter_type == "api_call"
        assert ev.unit == "call"
        assert ev.quantity == 1
        assert str(ev.tenant_id) == TENANT_A
        assert sub.status == "active"

    def test_no_scope_required_passes_without_scope(self, db_session):
        product = _published_product(db_session)
        issued = _issued_key(db_session, scopes="")
        svc.subscribe(db_session, consumer_tenant_id=TENANT_A, api_product=product)
        svc.authorize_call(db_session, raw_key=issued["api_key"], product=product)
        assert _api_request_count(db_session, issued["id"]) == 1


class TestAuthorizeNegative:
    """负向六连：全部拒绝且零计量（fail-closed）。"""

    def _setup(self, db_session):
        product = _published_product(db_session)
        issued = _issued_key(db_session, scopes="echo:read")
        svc.subscribe(db_session, consumer_tenant_id=TENANT_A, api_product=product)
        return product, issued

    def test_invalid_key_rejected(self, db_session):
        product, _ = self._setup(db_session)
        with pytest.raises(InvalidApiKey):
            svc.authorize_call(db_session, raw_key="short", product=product)
        with pytest.raises(InvalidApiKey):
            svc.authorize_call(db_session, raw_key="ujk_" + "x" * 40, product=product)
        assert _api_request_count(db_session, "any") == 0

    def test_revoked_key_rejected(self, db_session):
        product, issued = self._setup(db_session)
        svc.revoke_key(db_session, issued["id"])
        with pytest.raises(ApiKeyRevoked):
            svc.authorize_call(db_session, raw_key=issued["api_key"], product=product)
        assert _api_request_count(db_session, issued["id"]) == 0

    def test_expired_key_rejected(self, db_session):
        product, issued = self._setup(db_session)
        row = db_session.query(ApiKey).filter(ApiKey.id == issued["id"]).one()
        row.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
        db_session.commit()
        with pytest.raises(ApiKeyExpired):
            svc.authorize_call(db_session, raw_key=issued["api_key"], product=product)
        assert _api_request_count(db_session, issued["id"]) == 0

    def test_scope_denied_rejected(self, db_session):
        product, issued = self._setup(db_session)
        with pytest.raises(ScopeDenied):
            svc.authorize_call(
                db_session, raw_key=issued["api_key"], product=product,
                scope_required="admin:write",
            )
        assert _api_request_count(db_session, issued["id"]) == 0

    def test_unpublished_product_rejected(self, db_session):
        draft = svc.create_product(db_session, name=f"draft-{uuid.uuid4().hex[:8]}")
        issued = _issued_key(db_session)
        with pytest.raises(ProductNotCallable):
            svc.authorize_call(db_session, raw_key=issued["api_key"], product=draft)
        assert _api_request_count(db_session, issued["id"]) == 0

    def test_inactive_subscription_rejected(self, db_session):
        product, issued = self._setup(db_session)
        # 无订阅
        other_key = _issued_key(db_session, tenant_id=TENANT_B)
        with pytest.raises(SubscriptionInactive):
            svc.authorize_call(db_session, raw_key=other_key["api_key"], product=product)
        # 订阅 suspended
        sub = (
            db_session.query(ApiSubscription)
            .filter(ApiSubscription.consumer_tenant_id == TENANT_A)
            .one()
        )
        svc.transition_subscription(db_session, sub, "suspended")
        with pytest.raises(SubscriptionInactive):
            svc.authorize_call(db_session, raw_key=issued["api_key"], product=product)
        assert _api_request_count(db_session, issued["id"]) == 0


class TestQuota:
    def test_daily_quota_enforced_with_metering(self, db_session):
        product = _published_product(db_session)
        issued = _issued_key(db_session)
        svc.subscribe(
            db_session, consumer_tenant_id=TENANT_A, api_product=product, quota_per_day=2
        )
        svc.authorize_call(db_session, raw_key=issued["api_key"], product=product)
        svc.authorize_call(db_session, raw_key=issued["api_key"], product=product)
        assert _api_request_count(db_session, issued["id"]) == 2
        with pytest.raises(QuotaExceeded):
            svc.authorize_call(db_session, raw_key=issued["api_key"], product=product)
        assert _api_request_count(db_session, issued["id"]) == 2, "被拒调用不得计量"

    def test_product_level_limit_applies_when_subscription_unlimited(self, db_session):
        product = _published_product(db_session, rate_limit_per_day=1)
        issued = _issued_key(db_session)
        svc.subscribe(db_session, consumer_tenant_id=TENANT_A, api_product=product)
        svc.authorize_call(db_session, raw_key=issued["api_key"], product=product)
        with pytest.raises(QuotaExceeded):
            svc.authorize_call(db_session, raw_key=issued["api_key"], product=product)


class TestProductLifecycle:
    def test_forward_only_guard(self, db_session):
        p = svc.create_product(db_session, name=f"lc-{uuid.uuid4().hex[:8]}")
        with pytest.raises(IllegalTransition):
            svc.transition_product(db_session, p, "published")  # draft→published 直跳拒绝
        svc.transition_product(db_session, p, "review")
        svc.transition_product(db_session, p, "published")
        svc.transition_product(db_session, p, "suspended")
        svc.transition_product(db_session, p, "published")  # suspended→published 恢复允许
        svc.transition_product(db_session, p, "deprecated")
        with pytest.raises(IllegalTransition):
            svc.transition_product(db_session, p, "published")  # 终态不可再跃迁


class TestSubscriptionRules:
    def test_unpublished_product_cannot_subscribe(self, db_session):
        draft = svc.create_product(db_session, name=f"sub-{uuid.uuid4().hex[:8]}")
        with pytest.raises(ProductNotCallable):
            svc.subscribe(db_session, consumer_tenant_id=TENANT_A, api_product=draft)

    def test_duplicate_subscription_rejected(self, db_session):
        product = _published_product(db_session)
        svc.subscribe(db_session, consumer_tenant_id=TENANT_A, api_product=product)
        with pytest.raises(IllegalTransition):
            svc.subscribe(db_session, consumer_tenant_id=TENANT_A, api_product=product)

    def test_cancelled_is_terminal(self, db_session):
        product = _published_product(db_session)
        sub = svc.subscribe(db_session, consumer_tenant_id=TENANT_A, api_product=product)
        svc.transition_subscription(db_session, sub, "cancelled")
        with pytest.raises(IllegalTransition):
            svc.transition_subscription(db_session, sub, "active")
