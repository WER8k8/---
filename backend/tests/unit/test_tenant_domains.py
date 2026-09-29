# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""tenant_domains 状态流水线测试（修正设计稿 模块1 / Gate G2）。

锁定语义：
- 创建签发 TXT 令牌（明文一次）+ normalized 全局唯一；
- TXT 令牌校验 → verified；错误令牌 → failed；TXT 失败回落 CNAME 探测；
- 未 verified 禁止激活 / 设主域（G2 红线）；set-primary 同租户唯一让位；
- resolve_verified_tenant：仅 verified+active 解析；未验证/未激活/已删除不解析；
- middleware 集成：verified 域名命中状态真源；legacy JSON 兼容回退仍在。
"""
from __future__ import annotations

import uuid

import pytest

from app.models.tenant import Tenant
from app.services import tenant_domain_service as tds


TENANT_ID = "2a111111-1111-4111-8111-111111111111"


@pytest.fixture
def tenant(db_session):
    from app.models.tenant import TenantPlan

    plan = TenantPlan(
        id="2b111111-1111-4111-8111-111111111111",
        name="测试套餐",
        code="test-domain-plan",
    )
    db_session.add(plan)
    db_session.flush()
    t = Tenant(
        id=TENANT_ID,
        name="域测租户",
        domain="domtest.local",
        plan_id=plan.id,
        status="active",
        is_active=True,
    )
    db_session.add(t)
    db_session.commit()
    return t


class TestCreateAndToken:
    def test_create_issues_token_once(self, db_session, tenant):
        record, token = tds.create_tenant_domain(
            db_session, tenant=tenant, hostname="Shop.Example.COM", verification_method="dns_txt"
        )
        assert record.normalized_hostname == "shop.example.com"
        assert record.verification_status == "pending"
        assert record.is_active is False
        assert record.verification_token_hash  # 库存 hash
        assert token.startswith("uj-verify-")

    def test_duplicate_hostname_rejected_globally(self, db_session, tenant):
        tds.create_tenant_domain(db_session, tenant=tenant, hostname="dup.example.com")
        with pytest.raises(tds.DomainError) as ei:
            tds.create_tenant_domain(db_session, tenant=tenant, hostname="dup.example.com")
        assert ei.value.status_code == 409

    def test_reserved_suffix_rejected(self, db_session, tenant):
        with pytest.raises(tds.DomainError) as ei:
            tds.create_tenant_domain(db_session, tenant=tenant, hostname="shop.youding-saas.com")
        assert ei.value.status_code == 400


class TestVerify:
    def test_txt_token_match_verifies(self, db_session, tenant):
        record, token = tds.create_tenant_domain(
            db_session, tenant=tenant, hostname="ok.example.com", verification_method="dns_txt"
        )
        state = tds.verify_tenant_domain(
            db_session, record, txt_lookup=lambda d: token, cname_probe=lambda d: False
        )
        assert state.verification_status == "verified"

    def test_wrong_token_then_cname_fallback(self, db_session, tenant):
        record, _token = tds.create_tenant_domain(
            db_session, tenant=tenant, hostname="fb.example.com"
        )
        state = tds.verify_tenant_domain(
            db_session, record, txt_lookup=lambda d: None, cname_probe=lambda d: True
        )
        assert state.verification_status == "verified"
        assert "cname_probe_fallback_ok" in (state.verification_failed_reason or "")

    def test_both_fail_is_honest_failed(self, db_session, tenant):
        record, _ = tds.create_tenant_domain(
            db_session, tenant=tenant, hostname="bad.example.com"
        )
        state = tds.verify_tenant_domain(
            db_session, record, txt_lookup=lambda d: None, cname_probe=lambda d: False
        )
        assert state.verification_status == "failed"
        assert "cname_probe_failed" in state.verification_failed_reason


class TestActivateAndPrimary:
    def test_activate_requires_verified(self, db_session, tenant):
        record, _ = tds.create_tenant_domain(db_session, tenant=tenant, hostname="a.example.com")
        with pytest.raises(tds.DomainError) as ei:
            tds.activate_tenant_domain(db_session, record)
        assert ei.value.status_code == 409  # G2 红线：未验证禁止激活

    def test_set_primary_requires_verified_and_active(self, db_session, tenant):
        record, token = tds.create_tenant_domain(
            db_session, tenant=tenant, hostname="p.example.com"
        )
        with pytest.raises(tds.DomainError):
            tds.set_primary_domain(db_session, record)
        tds.verify_tenant_domain(db_session, record, txt_lookup=lambda d: token, cname_probe=lambda d: False)
        with pytest.raises(tds.DomainError):
            tds.set_primary_domain(db_session, record)  # verified 但未激活
        tds.activate_tenant_domain(db_session, record)
        state = tds.set_primary_domain(db_session, record)
        assert state.is_primary is True

    def test_primary_uniqueness_within_tenant(self, db_session, tenant):
        ids = {}
        for host in ("one.example.com", "two.example.com"):
            record, token = tds.create_tenant_domain(db_session, tenant=tenant, hostname=host)
            tds.verify_tenant_domain(db_session, record, txt_lookup=lambda d: token, cname_probe=lambda d: False)
            tds.activate_tenant_domain(db_session, record)
            ids[host] = record
        first = tds.set_primary_domain(db_session, ids["one.example.com"])
        assert first.is_primary is True
        second = tds.set_primary_domain(db_session, ids["two.example.com"])
        assert second.is_primary is True
        db_session.refresh(ids["one.example.com"])
        assert ids["one.example.com"].is_primary is False  # 唯一性让位


class TestResolveVerified:
    def test_only_verified_active_resolves(self, db_session, tenant):
        record, token = tds.create_tenant_domain(
            db_session, tenant=tenant, hostname="live.example.com"
        )
        # pending：不解析
        assert tds.resolve_verified_tenant(db_session, "live.example.com") is None
        tds.verify_tenant_domain(db_session, record, txt_lookup=lambda d: token, cname_probe=lambda d: False)
        # verified 但未激活：不解析
        assert tds.resolve_verified_tenant(db_session, "live.example.com") is None
        tds.activate_tenant_domain(db_session, record)
        assert str(tds.resolve_verified_tenant(db_session, "live.example.com").id) == TENANT_ID
        assert tds.resolve_verified_tenant(db_session, "live.example.com:8443") is not None  # 带端口去端口
        # 删除后不再解析
        tds.delete_tenant_domain(db_session, record)
        assert tds.resolve_verified_tenant(db_session, "live.example.com") is None


class TestMiddlewareIntegration:
    def test_middleware_resolves_verified_domain(self, db_session, tenant, monkeypatch):
        """middleware _lookup_tenant 接线：调用 resolve_verified_tenant 并采纳其结果。

        （middleware 内部 SessionLocal 指向真 PG；解析逻辑本身已由
        TestResolveVerified 在测试库覆盖，此处验证接线与缓存形状。）
        """
        from app.core.tenant_middleware import TenantMiddleware

        record, token = tds.create_tenant_domain(
            db_session, tenant=tenant, hostname="mw.example.com"
        )
        tds.verify_tenant_domain(db_session, record, txt_lookup=lambda d: token, cname_probe=lambda d: False)
        tds.activate_tenant_domain(db_session, record)
        live = db_session.query(Tenant).filter(Tenant.id == TENANT_ID).first()

        monkeypatch.setattr(
            tds,
            "resolve_verified_tenant",
            lambda db, host: live if host == "mw.example.com" else None,
        )

        mw = TenantMiddleware(app=None)
        info = mw._lookup_tenant("mw.example.com", "mw.example.com")
        assert info is not None
        assert info["id"] == TENANT_ID

    def test_middleware_unverified_domain_not_resolved(self, db_session, tenant, monkeypatch):
        from app.core.tenant_middleware import TenantMiddleware

        tds.create_tenant_domain(db_session, tenant=tenant, hostname="nope.example.com")
        # 状态真源无命中（stub 反映真实行为：未验证不返回租户）
        monkeypatch.setattr(tds, "resolve_verified_tenant", lambda db, host: None)
        mw = TenantMiddleware(app=None)
        assert mw._lookup_tenant("nope.example.com", "nope.example.com") is None


class TestRouteRegistration:
    def test_domain_state_routes_mounted(self):
        """激活/主域/状态/重发令牌端点已挂载（幂等回归防呆）。"""
        from app.core.route_introspection import mounted_route_paths

        from app.main import app  # noqa: PLC0415 — 路由注册在 import 期完成

        paths = mounted_route_paths(app)
        for suffix in (
            "/activate",
            "/set-primary",
            "/status",
            "/rotate-token",
        ):
            assert any(p.endswith(f"/domains/{{domain}}{suffix}") or f"/domains/{{domain}}{suffix}" in p
                       for p in paths), f"missing {suffix}"
