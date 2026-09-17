"""Token 服务单元测试 — 配额、扣减、充值、暂停/恢复"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from app.services.token_service import TokenService, InsufficientTokenError


# ── Fixtures ──────────────────────────────────────────────


def _make_tenant(
    *,
    tenant_id: str = "tenant-1",
    status: str = "active",
    plan_max_ai_quota: int = 1000,
    ai_quota_used: int = 0,
    purchased_token_bonus: int = 0,
    settings_dict: dict | None = None,
):
    """构造一个轻量级 Tenant mock，用于 TokenService 测试。"""
    tenant = MagicMock()
    tenant.id = tenant_id
    tenant.status = status
    tenant.plan = MagicMock()
    tenant.plan.max_ai_quota = plan_max_ai_quota
    tenant.ai_quota_used = ai_quota_used
    tenant.purchased_token_bonus = purchased_token_bonus
    tenant.settings = "{}" if settings_dict is None else __import__("json").dumps(settings_dict)
    return tenant


def _make_service(tenant) -> TokenService:
    """构造一个使用内存 dict 作为查询的 TokenService（跳过真实 DB）。"""
    db = MagicMock()
    tenant_id = tenant.id

    def query_side_effect(model, /, *filters, **kwargs):
        if model.__name__ == "Tenant":
            q = MagicMock()
            q.filter.return_value = q
            q.first.return_value = tenant
            q.with_for_update.return_value = q
            return q
        if model.__name__ == "TokenLedgerEntry":
            q = MagicMock()
            q.filter.return_value = q
            q.first.return_value = None
            return q
        return MagicMock()

    db.query.side_effect = query_side_effect
    db.add = MagicMock()
    db.commit = MagicMock()
    return TokenService(db)


# ── balance() ──────────────────────────────────────────────


class TestBalance:
    def test_active_tenant_full_balance(self):
        t = _make_tenant(status="active", plan_max_ai_quota=1000, ai_quota_used=0)
        svc = _make_service(t)
        assert svc.balance(t.id) == 1000

    def test_active_tenant_partial_usage(self):
        t = _make_tenant(status="active", plan_max_ai_quota=1000, ai_quota_used=300)
        svc = _make_service(t)
        assert svc.balance(t.id) == 700

    def test_active_tenant_with_bonus(self):
        t = _make_tenant(
            status="active",
            plan_max_ai_quota=1000,
            ai_quota_used=200,
            purchased_token_bonus=500,
        )
        svc = _make_service(t)
        assert svc.balance(t.id) == 1300

    def test_suspended_tenant_returns_zero(self):
        t = _make_tenant(status="suspended", plan_max_ai_quota=1000, ai_quota_used=0)
        svc = _make_service(t)
        assert svc.balance(t.id) == 0

    def test_unknown_tenant_returns_zero(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        svc = TokenService(db)
        assert svc.balance("nonexistent") == 0

    def test_ai_quota_used_none_treated_as_zero(self):
        t = _make_tenant(status="active", plan_max_ai_quota=500, ai_quota_used=None)
        svc = _make_service(t)
        assert svc.balance(t.id) == 500

    def test_quota_limit_with_none_plan(self):
        t = _make_tenant(status="active", plan_max_ai_quota=None)
        t.plan = None
        svc = _make_service(t)
        assert svc.balance(t.id) == 0


# ── ensure_can_consume() ───────────────────────────────────


class TestEnsureCanConsume:
    def test_zero_amount_no_raise(self):
        t = _make_tenant(status="active", plan_max_ai_quota=100)
        svc = _make_service(t)
        svc.ensure_can_consume(t.id, 0)  # 不应抛异常

    def test_negative_amount_no_raise(self):
        t = _make_tenant(status="active", plan_max_ai_quota=100)
        svc = _make_service(t)
        svc.ensure_can_consume(t.id, -5)  # 不应抛异常

    def test_sufficient_balance_no_raise(self):
        t = _make_tenant(status="active", plan_max_ai_quota=100, ai_quota_used=20)
        svc = _make_service(t)
        svc.ensure_can_consume(t.id, 50)  # 余额 80 >= 50，不抛

    def test_insufficient_balance_raises(self):
        t = _make_tenant(status="active", plan_max_ai_quota=100, ai_quota_used=90)
        svc = _make_service(t)
        with pytest.raises(InsufficientTokenError, match="余额不足"):
            svc.ensure_can_consume(t.id, 20)

    def test_exact_balance_insufficient_by_one(self):
        t = _make_tenant(status="active", plan_max_ai_quota=100, ai_quota_used=0)
        svc = _make_service(t)
        svc.ensure_can_consume(t.id, 100)  # 恰好够用
        with pytest.raises(InsufficientTokenError):
            svc.ensure_can_consume(t.id, 101)  # 多一个就不够


# ── consume() ──────────────────────────────────────────────


class TestConsume:
    def test_consume_success_updates_ledger(self):
        t = _make_tenant(status="active", plan_max_ai_quota=1000, ai_quota_used=0)
        svc = _make_service(t)
        result = svc.consume(t.id, 100, reason="api_call", reference_id="ref-001")
        assert result == 900
        svc.db.commit.assert_called_once()
        svc.db.add.assert_called()

    def test_consume_depletes_balance_triggers_suspend(self):
        t = _make_tenant(status="active", plan_max_ai_quota=100, ai_quota_used=0)
        svc = _make_service(t)
        svc.consume(t.id, 100, reason="exhaust")
        assert t.status == "suspended"
        import json
        settings = json.loads(t.settings)
        assert settings.get("suspend_reason") == "token_depleted"

    def test_consume_does_not_suspend_already_suspended(self):
        t = _make_tenant(status="suspended", plan_max_ai_quota=100, ai_quota_used=0)
        svc = _make_service(t)
        # 余额为0，ensure_can_consume 会抛异常
        with pytest.raises(InsufficientTokenError):
            svc.consume(t.id, 1, reason="x")

    def test_consume_nonexistent_tenant_raises(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        svc = TokenService(db)
        with pytest.raises((ValueError, InsufficientTokenError)):
            svc.consume("fake-id", 10, reason="x")

    def test_consume_records_ledger_entry(self):
        t = _make_tenant(status="active", plan_max_ai_quota=500, ai_quota_used=0)
        svc = _make_service(t)
        svc.consume(t.id, 50, reason="test_reason", reference_id="ref-42")
        captured = svc.db.add.call_args
        entry = captured[0][0]
        assert entry.tenant_id == t.id
        assert entry.delta == -50
        assert entry.reason == "test_reason"
        assert entry.reference_id == "ref-42"
        assert entry.balance_after == 450


# ── credit() ───────────────────────────────────────────────


class TestCredit:
    def test_credit_adds_bonus(self):
        t = _make_tenant(status="active", plan_max_ai_quota=1000, ai_quota_used=0, purchased_token_bonus=0)
        svc = _make_service(t)
        result = svc.credit(t.id, 200, reason="purchase")
        assert result == 1200
        assert t.purchased_token_bonus == 200

    def test_credit_restores_from_suspend(self):
        t = _make_tenant(
            status="suspended",
            plan_max_ai_quota=100,
            ai_quota_used=100,
            purchased_token_bonus=0,
            settings_dict={"suspend_reason": "token_depleted"},
        )
        svc = _make_service(t)
        result = svc.credit(t.id, 50, reason="topup")
        assert t.status == "active"
        import json
        settings = json.loads(t.settings)
        assert "suspend_reason" not in settings

    def test_credit_nonexistent_tenant_raises(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        svc = TokenService(db)
        with pytest.raises(ValueError, match="租户不存在"):
            svc.credit("fake-id", 10, reason="x")

    def test_credit_with_existing_bonus(self):
        t = _make_tenant(status="active", plan_max_ai_quota=1000, ai_quota_used=0, purchased_token_bonus=50)
        svc = _make_service(t)
        result = svc.credit(t.id, 30, reason="bonus")
        assert t.purchased_token_bonus == 80
        assert result == 1080

    def test_credit_no_restore_if_not_suspended(self):
        t = _make_tenant(status="active", plan_max_ai_quota=1000, ai_quota_used=0)
        svc = _make_service(t)
        svc.credit(t.id, 100, reason="bonus")
        assert t.status == "active"
        import json
        settings = json.loads(t.settings)
        assert "suspend_reason" not in settings


# ── 辅助方法 ──────────────────────────────────────────────


class TestSettingsIO:
    def test_read_settings_valid_json(self):
        t = MagicMock()
        t.settings = '{"key": "value"}'
        result = TokenService._read_settings(t)
        assert result == {"key": "value"}

    def test_read_settings_invalid_json(self):
        t = MagicMock()
        t.settings = "not-json"
        result = TokenService._read_settings(t)
        assert result == {}

    def test_read_settings_none(self):
        t = MagicMock()
        t.settings = None
        result = TokenService._read_settings(t)
        assert result == {}

    def test_write_settings_serializes(self):
        import json
        t = MagicMock()
        t.settings = None
        TokenService._write_settings(t, {"k": "v"})
        parsed = json.loads(t.settings)
        assert parsed == {"k": "v"}
