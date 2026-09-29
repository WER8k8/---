# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""第二层缺口 P · 租户退出与注销生命周期单元测试。"""
from __future__ import annotations

import uuid
import pytest

from app.models.tenant import Tenant, TenantPlan
from app.models.user import User
from app.models.order import Order
from app.models.api_marketplace import ApiKey
from app.services.api_marketplace_service import issue_key
from app.services.tenant_lifecycle_service import (
    initiate_tenant_exit,
    export_tenant_package,
    cancel_tenant_exit,
    TenantExitError,
)


def _make_tenant(db_session, name: str = "Exit Test Tenant") -> Tenant:
    plan = db_session.query(TenantPlan).first()
    if not plan:
        plan = TenantPlan(
            name="Test Plan",
            code=f"plan_{uuid.uuid4().hex[:6]}",
            price_monthly=0,
            price_yearly=0,
        )
        db_session.add(plan)
        db_session.flush()

    t = Tenant(
        id=str(uuid.uuid4()),
        name=name,
        domain=f"exit-{uuid.uuid4().hex[:8]}.com",
        plan_id=plan.id,
        status="active",
    )
    db_session.add(t)
    db_session.commit()
    return t


def _make_user(db_session, username_prefix: str = "u") -> User:
    u = User(
        id=str(uuid.uuid4()),
        username=f"{username_prefix}_{uuid.uuid4().hex[:8]}",
        email=f"{username_prefix}_{uuid.uuid4().hex[:8]}@example.com",
        hashed_password="pw",
        is_active=True,
    )
    db_session.add(u)
    db_session.commit()
    return u


def test_tenant_exit_lifecycle(db_session):
    t = _make_tenant(db_session, "Exit Test Tenant")
    tenant_id = str(t.id)

    # 签发一个 API Key
    key = issue_key(db_session, tenant_id=tenant_id, scopes="test:read")

    # 1. 成功发起注销
    res = initiate_tenant_exit(
        db_session,
        tenant_id=tenant_id,
        operator_id="admin_op",
        reason="Testing clean exit",
    )
    assert res["status"] == "pending_deletion"
    assert res["revoked_keys"] == 1

    # 验证 Key 已被吊销
    db_k = db_session.query(ApiKey).filter(ApiKey.id == key["id"]).first()
    assert db_k.revoked_at is not None

    # 2. 生成导出包
    pkg = export_tenant_package(db_session, tenant_id=tenant_id)
    assert pkg["tenant"]["id"] == tenant_id
    assert "export_id" in pkg
    db_session.refresh(t)
    assert t.status == "export_available"

    # 3. 撤回注销申请
    canc = cancel_tenant_exit(db_session, tenant_id=tenant_id)
    assert canc["status"] == "active"
    db_session.refresh(t)
    assert t.status == "active"


def test_tenant_exit_blocked_by_open_orders(db_session):
    t = _make_tenant(db_session, "Order Blocked Tenant")
    tenant_id = str(t.id)

    u = _make_user(db_session, "buyer")

    # 增加一笔履约中的订单
    order = Order(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        buyer_id=u.id,
        merchant_id=u.id,
        order_number=f"ORD-{uuid.uuid4().hex[:6]}",
        status="in_production",
        total_amount=500.0,
    )
    db_session.add(order)
    db_session.commit()

    # 未加 force 时应抛出 TenantExitError
    with pytest.raises(TenantExitError) as exc:
        initiate_tenant_exit(
            db_session,
            tenant_id=tenant_id,
            operator_id="admin_op",
            reason="Exit with open order",
        )
    assert "未结履约订单" in str(exc.value)

    # 传入 force=True 时强行注销放行
    res = initiate_tenant_exit(
        db_session,
        tenant_id=tenant_id,
        operator_id="admin_op",
        reason="Force exit with open order",
        force=True,
    )
    assert res["status"] == "pending_deletion"
