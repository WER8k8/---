"""附属票据 · 租户归属透传回归测试。

守卫的缺陷：ticket_service.issue_annex_ticket 支持 tenant_id，但路由曾未传，
导致所有票据 tenant_id 恒为空串，附属侧（GoodJob / TradeAI）拿不到租户归属。
多租户 SaaS 下票据必须带租户作用域，本用例锁死这条装配链。

用内存 SQLite 只建 users / tenants / user_tenants 三表，避开全库 create_all。
"""

from __future__ import annotations

import base64
import json
import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.v1.routes.annex import AnnexTicketBody, issue_annex_ticket
from app.models.tenant import Tenant, TenantPlan, UserTenant
from app.models.user import User
from app.services.annex import ticket_service


@pytest.fixture()
def session():
    engine = create_engine("sqlite://")
    for model in (User, TenantPlan, Tenant, UserTenant):
        model.__table__.create(engine)
    # expire_on_commit=False：User.role_rel 是 lazy="joined"，默认过期会让 commit 后
    # 读任一字段都去 JOIN admin_roles，这里不需要那张表。
    maker = sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)
    db = maker()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def _ticket_secret(monkeypatch):
    monkeypatch.setenv("ANNEX_TICKET_SECRET", "unit-test-annex-secret")


# 角色取真实词表（库里主力是 tenant_admin），不用假想值
def _user(db, *, role: str = "tenant_admin") -> User:
    row = User(
        id=str(uuid.uuid4()),
        username=f"u_{uuid.uuid4().hex[:8]}",
        email=f"{uuid.uuid4().hex[:8]}@example.com",
        hashed_password="not-a-real-hash",
        display_name="租户用户",
        role=role,
    )
    db.add(row)
    db.commit()
    return row


def _tenant(db) -> Tenant:
    plan = TenantPlan(id=str(uuid.uuid4()), name="基础版", code=f"basic_{uuid.uuid4().hex[:8]}")
    tenant = Tenant(
        id=str(uuid.uuid4()),
        name="优丁测试租户",
        domain=f"t{uuid.uuid4().hex[:8]}.example.com",
        plan_id=plan.id,
    )
    db.add_all([plan, tenant])
    db.commit()
    return tenant


def _link(db, user: User, tenant: Tenant, *, is_active: bool = True) -> UserTenant:
    link = UserTenant(
        id=str(uuid.uuid4()),
        user_id=user.id,
        tenant_id=tenant.id,
        role="admin",
        is_active=is_active,
    )
    db.add(link)
    db.commit()
    return link


def _payload(ticket: str) -> dict:
    _, payload_b64, _ = ticket.split(".")
    return json.loads(base64.urlsafe_b64decode(payload_b64 + "=="))


def _issue(db, user) -> dict:
    """调用路由函数本体（不经 HTTP），验证装配层确实把租户作用域传下去。"""
    response = issue_annex_ticket(AnnexTicketBody(annex="goodjob"), current_user=user, db=db)
    data = response.data
    assert data["annex"] == "goodjob"
    return _payload(data["annex_ticket"])


def test_tenant_user_ticket_carries_tenant_id(session):
    user = _user(session, role="tenant_admin")
    tenant = _tenant(session)
    _link(session, user, tenant)

    payload = _issue(session, user)
    assert payload["tenant_id"] == str(tenant.id)
    assert payload["sub"] == str(user.id)
    assert payload["annex_role"] == "sales"
    assert payload["uj_role"] == "tenant_admin"


def test_platform_admin_ticket_has_empty_tenant_id(session):
    """平台级（super_admin/admin）= 跨租户，租户归属必须留空而非误挂某租户。"""
    user = _user(session, role="super_admin")
    tenant = _tenant(session)
    _link(session, user, tenant)

    assert _issue(session, user)["tenant_id"] == ""


def test_user_without_active_link_yields_empty_tenant_id(session):
    user = _user(session, role="tenant_admin")
    tenant = _tenant(session)
    _link(session, user, tenant, is_active=False)

    assert _issue(session, user)["tenant_id"] == ""


def test_redeem_roundtrip_preserves_tenant_id(session):
    user = _user(session, role="tenant_admin")
    tenant = _tenant(session)
    _link(session, user, tenant)

    issued = ticket_service.issue_annex_ticket(
        user_id=str(user.id),
        user_name=user.display_name,
        user_email=user.email,
        uj_role=user.role,
        annex="goodjob",
        tenant_id=str(tenant.id),
    )
    redeemed = ticket_service.redeem_annex_ticket(issued["annex_ticket"], annex="goodjob")
    assert redeemed["user"]["tenant_id"] == str(tenant.id)
    assert redeemed["user"]["email"] == user.email


def test_multi_tenant_user_never_leaks_foreign_tenant(session):
    """挂了多个租户的用户：归属不确定（UserTenant 无 primary 标记，全站同此口径），
    但必须落在他自己关联的租户集合内，绝不能漂到无关租户。
    """
    user = _user(session, role="tenant_admin")
    tenants = [_tenant(session) for _ in range(3)]
    for tenant in tenants:
        _link(session, user, tenant)

    allowed = {str(t.id) for t in tenants}
    payload = _issue(session, user)
    assert payload["tenant_id"] in allowed
