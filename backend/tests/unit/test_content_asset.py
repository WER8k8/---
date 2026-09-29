# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""ContentAsset 统一对象 配对反证 + 边界/越权测试（模块4 契约 §6）。

反证必须**成对**（缺一即空真）：
- 负向（未启用 / 默认路径）：对现网那 1 行 `content_masters`
  （id=57bc30f9-5ca1-4146-9d45-b2913f268bda）**逐字段**整个 dict 做 `==`，
  不抽样、不"约等于"。
- 正向（必须变化）：改真源（租户主域 / asset_meta / 触点 / 行业绑定 /
  preflight & kernel）后指定字段**必须变化**为可断言的期望值。

真源基线（实跑观测，非猜测）：
    content_status == "draft"        （无关联 publish_task、无 preflight、kernel 为 NULL）
    publish_status == "unpublished"  （publish_tasks.content_master_id 为 NULL）
    canonical_url  == SITE_URL 分支   （tenant_canonical_url 与租户主域均空）
    industry_profile_id == building_materials Profile.id
其余 6 个净新增字段 asset_meta 为 NULL → null/[]。

路由边界/越权（401 / 403 / 400 / 409）在 SQLite 会话上覆盖，不写入现网库。
现网库用例全部**自建自清**（测后 content_masters=1 / publish_tasks=2 /
marketing_touchpoints=0 / tenant_domains=0）。
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.attribution import MarketingTouchpoint
from app.models.content import PublishTask
from app.models.content_master import ContentMaster
from app.models.tenant import Tenant, UserTenant
from app.models.tenant_domain import TenantDomain
from app.services import content_asset_service as cas
from app.services import industry_profile_service as ips

# ── 现网真值（实查 youding_dev @5433） ──────────────────────────────
MASTER_ID = "57bc30f9-5ca1-4146-9d45-b2913f268bda"
TENANT_ID = "4ffe5f3d-3811-4c8e-a344-bb89da03c987"
# 平台默认域（canonical 中**禁止**出现）
_FORBIDDEN_DOMAINS = ("youdingjiancai.com", "globaltrade-ai.site")


# ────────────────────────── 现网库 fixture ──────────────────────────


@pytest.fixture
def real_db():
    """现网库会话（PG）。用例负责自建自清；这里只保证关闭。"""
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()


@pytest.fixture
def baseline_guard():
    """用例结束后核对现网基线计数，防止脏数据泄漏。"""
    yield
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        assert db.query(ContentMaster).count() == 1, "content_masters 基线被破坏（应为 1）"
        assert db.query(PublishTask).count() == 2, "publish_tasks 基线被破坏（应为 2）"
        assert db.query(MarketingTouchpoint).count() == 0, "marketing_touchpoints 基线被破坏（应为 0）"
        assert db.query(TenantDomain).count() == 0, "tenant_domains 基线被破坏（应为 0）"
    finally:
        db.close()


def _live_master(db) -> ContentMaster:
    master = db.query(ContentMaster).filter(ContentMaster.id == MASTER_ID).first()
    assert master is not None, "现网母版行缺失，无法做反证基线"
    return master


# ────────────────────────── 负向反证（逐字段 ==） ──────────────────────────


class TestNegativeBaseline:
    def test_live_row_field_by_field_equals(self, real_db, baseline_guard):
        """现网行整体 dict 逐字段 == 基线（证明 facade 纯投影、零漂移）。"""
        master = _live_master(real_db)
        prof = ips.resolve_profile_for_tenant(real_db, TENANT_ID)
        assert prof is not None and prof.code == "building_materials"

        asset = cas.build_content_asset(real_db, master)
        expected = {
            "asset_id": MASTER_ID,
            "tenant_id": TENANT_ID,
            "site_id": "dev.local",
            "industry_profile_id": str(prof.id),
            "product_id": None,
            "market": None,
            "language": "zh",
            "source_refs": [],
            "evidence_refs": [],
            "prompt_version": None,
            "model_version": None,
            "content_status": "draft",
            "publish_status": "unpublished",
            "canonical_url": f"{settings.SITE_URL.rstrip('/')}/zh/content/{MASTER_ID}",
            "attribution_context": {},
        }
        # 整个 dict 相等（不抽样）；同时锁死字段数 15
        assert asset.model_dump() == expected
        assert len(asset.model_dump()) == 15
        # canonical 收口铁律：不得含平台默认域
        for bad in _FORBIDDEN_DOMAINS:
            assert bad not in asset.canonical_url


# ────────────────────────── 正向反证（必须变化） ──────────────────────────


class TestPositiveMustChange:
    def test_primary_domain_switches_canonical(self, real_db, baseline_guard):
        """租户主域（verified+active+primary）+ 清空 tenant_canonical_url → canonical 走租户域。"""
        master = _live_master(real_db)
        original_canonical = master.tenant_canonical_url
        domain = TenantDomain(
            id=str(uuid.uuid4()),
            tenant_id=TENANT_ID,
            hostname="a.example.com",
            normalized_hostname="a.example.com",
            domain_type="custom",
            verification_method="dns_txt",
            verification_status="verified",
            ssl_status="issued",
            is_primary=True,
            is_active=True,
        )
        try:
            master.tenant_canonical_url = None
            real_db.add(master)
            real_db.add(domain)
            real_db.commit()

            asset = cas.build_content_asset(real_db, master)
            assert asset.canonical_url == f"https://a.example.com/zh/content/{MASTER_ID}"
            for bad in _FORBIDDEN_DOMAINS:
                assert bad not in asset.canonical_url
        finally:
            real_db.query(TenantDomain).filter(TenantDomain.id == domain.id).delete()
            real_db.query(ContentMaster).filter(ContentMaster.id == MASTER_ID).update(
                {"tenant_canonical_url": original_canonical}
            )
            real_db.commit()

    def test_master_canonical_url_takes_precedence(self, real_db, baseline_guard):
        """tenant_canonical_url 非空即用（优先级 ① 高于主域）。"""
        master = _live_master(real_db)
        original_canonical = master.tenant_canonical_url
        try:
            master.tenant_canonical_url = "https://brand.example.org/spec/rockwool"
            real_db.add(master)
            real_db.commit()
            asset = cas.build_content_asset(real_db, master)
            assert asset.canonical_url == "https://brand.example.org/spec/rockwool"
        finally:
            real_db.query(ContentMaster).filter(ContentMaster.id == MASTER_ID).update(
                {"tenant_canonical_url": original_canonical}
            )
            real_db.commit()

    def test_asset_meta_six_fields_read(self, real_db, baseline_guard):
        """写 master.asset_meta → 6 个净新增字段必须读出对应值。"""
        master = _live_master(real_db)
        meta = {
            "product_id": "11111111-1111-4111-8111-111111111111",
            "market": "SA",
            "language": "en",
            "source_refs": [{"ref": "doc://rockwool-spec"}],
            "prompt_version": "p-v3",
            "model_version": "m-2026.09",
        }
        try:
            master.asset_meta = meta
            real_db.add(master)
            real_db.commit()

            asset = cas.build_content_asset(real_db, master)
            assert asset.product_id == meta["product_id"]
            assert asset.market == "SA"
            assert asset.language == "en"
            assert asset.source_refs == [{"ref": "doc://rockwool-spec"}]
            assert asset.prompt_version == "p-v3"
            assert asset.model_version == "m-2026.09"
        finally:
            real_db.query(ContentMaster).filter(ContentMaster.id == MASTER_ID).update(
                {"asset_meta": None}
            )
            real_db.commit()

    def test_attribution_context_from_touchpoint(self, real_db, baseline_guard):
        """插入 MarketingTouchpoint(content_id=str(master.id)) → attribution_context 非空。"""
        master = _live_master(real_db)
        tp = MarketingTouchpoint(
            id=str(uuid.uuid4()),
            tenant_id=master.tenant_id,
            content_id=str(master.id),
            platform="linkedin",
            channel="social",
        )
        try:
            real_db.add(tp)
            real_db.commit()

            asset = cas.build_content_asset(real_db, master)
            assert asset.attribution_context != {}
            assert asset.attribution_context["touches"] == 1
            assert asset.attribution_context["platforms"] == ["linkedin"]
            assert asset.attribution_context["content_id"] == MASTER_ID
        finally:
            real_db.query(MarketingTouchpoint).filter(MarketingTouchpoint.id == tp.id).delete()
            real_db.commit()

    def test_industry_profile_binding_switches_profile(self, real_db, baseline_guard):
        """租户绑 machinery → industry_profile_id == machinery.id 且 ≠ building_materials.id。"""
        master = _live_master(real_db)
        tenant = real_db.query(Tenant).filter(Tenant.id == TENANT_ID).first()
        assert tenant is not None
        original_settings = tenant.settings
        try:
            ips.set_tenant_profile_code(real_db, TENANT_ID, "machinery", actor="test_content_asset")
            mach = ips.resolve_profile_for_tenant(real_db, TENANT_ID)
            building = ips.get_active_profile(real_db, "building_materials")
            assert mach is not None and mach.code == "machinery"
            assert building is not None

            asset = cas.build_content_asset(real_db, master)
            assert asset.industry_profile_id == str(mach.id)
            assert asset.industry_profile_id != str(building.id)
        finally:
            real_db.query(Tenant).filter(Tenant.id == TENANT_ID).update(
                {"settings": original_settings}
            )
            real_db.commit()

    def test_content_status_from_preflight_and_kernel(self, real_db, baseline_guard):
        """preflight_approved_at → approved；kernel.schema_ready=True → fact_checked + evidence。"""
        master = _live_master(real_db)
        original_preflight = master.preflight_approved_at
        original_kernel = master.fact_kernel_json
        evidence = [
            {"label": "SGS 报告", "level": "verified", "source": "https://example.com/sgs", "verifiable": True}
        ]
        try:
            # ① preflight 非空 → approved
            master.preflight_approved_at = datetime.now(timezone.utc)
            real_db.add(master)
            real_db.commit()
            a1 = cas.build_content_asset(real_db, master)
            assert a1.content_status == "approved"

            # ② 清 preflight + kernel.schema_ready=True → fact_checked + evidence_refs
            master.preflight_approved_at = None
            master.fact_kernel_json = {"entity_name": "岩棉保温板", "schema_ready": True, "evidence": evidence}
            real_db.add(master)
            real_db.commit()
            a2 = cas.build_content_asset(real_db, master)
            assert a2.content_status == "fact_checked"
            assert a2.evidence_refs == evidence

            # ③ 同内核 schema_ready=False → 回落 draft（未 fact_checked），evidence 不泄漏
            master.fact_kernel_json = {"entity_name": "x", "schema_ready": False, "evidence": []}
            real_db.add(master)
            real_db.commit()
            a3 = cas.build_content_asset(real_db, master)
            assert a3.content_status == "draft"
            assert a3.evidence_refs == []
        finally:
            real_db.query(ContentMaster).filter(ContentMaster.id == MASTER_ID).update(
                {"preflight_approved_at": original_preflight, "fact_kernel_json": original_kernel}
            )
            real_db.commit()

    def test_kernel_null_is_fail_safe(self, real_db, baseline_guard):
        """kernel 为 NULL → 不抛异常，content_status 回落 draft（FAIL-SAFE 铁律）。"""
        master = _live_master(real_db)
        assert master.fact_kernel_json is None
        asset = cas.build_content_asset(real_db, master)  # 不得抛
        assert asset.content_status == "draft"
        assert asset.evidence_refs == []


# ────────────────────────── 路由：越权 / 边界（SQLite） ──────────────────────────


def _mini_app(user, db):
    """最小 app：只挂 content-assets 路由，覆写 get_db / get_current_user。"""
    from app.api.v1.routes.content_assets import router

    app = FastAPI()
    app.include_router(router, prefix="/api/v1/content-assets")
    app.dependency_overrides[get_db] = lambda: db
    if user is not None:
        app.dependency_overrides[get_current_user] = lambda: user
    return TestClient(app)


def _mk_tenant(db, tenant_id, domain):
    db.add(
        Tenant(
            id=tenant_id,
            name=f"t-{str(tenant_id)[:8]}",
            domain=domain,
            plan_id=str(uuid.uuid4()),
            is_active=True,
        )
    )
    db.flush()


def _mk_master(db, master_id, tenant_id, status="draft"):
    db.add(ContentMaster(id=master_id, tenant_id=tenant_id, title="测试内容资产", status=status))
    db.flush()


def _bind_user(db, uid, tenant_id, role="viewer"):
    db.add(
        UserTenant(
            id=str(uuid.uuid4()),
            user_id=str(uid),
            tenant_id=tenant_id,
            role=role,
            is_active=True,
        )
    )
    db.flush()


class TestRoutes:
    def test_requires_auth_401(self, db_session):
        client = _mini_app(None, db_session)
        assert client.get("/api/v1/content-assets").status_code == 401
        assert client.get(f"/api/v1/content-assets/{MASTER_ID}").status_code == 401
        assert (
            client.post(
                f"/api/v1/content-assets/{MASTER_ID}/status",
                json={"content_status": "ready"},
            ).status_code
            == 401
        )

    def test_cross_tenant_get_403(self, db_session):
        other_tenant = "9a111111-1111-4111-8111-111111111111"
        my_tenant = "9a222222-2222-4222-8222-222222222222"
        _mk_tenant(db_session, other_tenant, "other.local")
        _mk_tenant(db_session, my_tenant, "mine.local")
        _mk_master(db_session, MASTER_ID, other_tenant, status="draft")
        uid = str(uuid.uuid4())
        _bind_user(db_session, uid, my_tenant, role="tenant_admin")
        client = _mini_app(SimpleNamespace(id=uid, role="viewer"), db_session)
        resp = client.get(f"/api/v1/content-assets/{MASTER_ID}")
        assert resp.status_code == 403

    def test_cross_tenant_status_write_403(self, db_session):
        other_tenant = "9a333333-3333-4333-8333-333333333333"
        my_tenant = "9a444444-4444-4444-8444-444444444444"
        _mk_tenant(db_session, other_tenant, "other2.local")
        _mk_tenant(db_session, my_tenant, "mine2.local")
        _mk_master(db_session, MASTER_ID, other_tenant, status="draft")
        uid = str(uuid.uuid4())
        _bind_user(db_session, uid, my_tenant, role="tenant_admin")
        client = _mini_app(SimpleNamespace(id=uid, role="tenant_admin"), db_session)
        resp = client.post(
            f"/api/v1/content-assets/{MASTER_ID}/status",
            json={"content_status": "ready"},
        )
        assert resp.status_code == 403

    def test_non_operator_status_write_403(self, db_session):
        """本租户内 view 角色（非运营）改状态 → 403。"""
        tenant_id = "9a555555-5555-4555-8555-555555555555"
        _mk_tenant(db_session, tenant_id, "view.local")
        _mk_master(db_session, MASTER_ID, tenant_id, status="draft")
        uid = str(uuid.uuid4())
        _bind_user(db_session, uid, tenant_id, role="viewer")
        client = _mini_app(SimpleNamespace(id=uid, role="viewer"), db_session)
        resp = client.post(
            f"/api/v1/content-assets/{MASTER_ID}/status",
            json={"content_status": "ready"},
        )
        assert resp.status_code == 403

    def test_bad_asset_id_400(self, db_session):
        client = _mini_app(SimpleNamespace(id=str(uuid.uuid4()), role="admin"), db_session)
        assert client.get("/api/v1/content-assets/not-a-uuid").status_code == 400
        assert (
            client.post(
                "/api/v1/content-assets/not-a-uuid/status",
                json={"content_status": "ready"},
            ).status_code
            == 400
        )

    def test_missing_asset_404(self, db_session):
        client = _mini_app(SimpleNamespace(id=str(uuid.uuid4()), role="admin"), db_session)
        resp = client.get(f"/api/v1/content-assets/{uuid.uuid4()}")
        assert resp.status_code == 404

    @pytest.mark.parametrize("qs", ["page=0", "page=-1", "size=0", "size=99999"])
    def test_pagination_bounds_400(self, db_session, qs):
        client = _mini_app(SimpleNamespace(id=str(uuid.uuid4()), role="admin"), db_session)
        resp = client.get(f"/api/v1/content-assets?{qs}")
        assert resp.status_code == 400
        assert resp.json()["message"]

    def test_list_ok_and_tenant_scoped(self, db_session):
        tenant_id = "9a666666-6666-4666-8666-666666666666"
        _mk_tenant(db_session, tenant_id, "list.local")
        _mk_master(db_session, MASTER_ID, tenant_id, status="published")
        uid = str(uuid.uuid4())
        _bind_user(db_session, uid, tenant_id, role="viewer")
        client = _mini_app(SimpleNamespace(id=uid, role="viewer"), db_session)
        resp = client.get("/api/v1/content-assets")
        assert resp.status_code == 200
        body = resp.json()["data"]
        assert body["total"] == 1
        assert body["page"] == 1
        assert len(body["items"]) == 1
        assert body["items"][0]["asset_id"] == MASTER_ID

    def test_illegal_transition_409(self, db_session):
        """published → draft（回退）非法 → 409 illegal_content_status_transition。"""
        tenant_id = "9a777777-7777-4777-8777-777777777777"
        _mk_tenant(db_session, tenant_id, "trans.local")
        _mk_master(db_session, MASTER_ID, tenant_id, status="published")
        uid = str(uuid.uuid4())
        _bind_user(db_session, uid, tenant_id, role="tenant_admin")
        client = _mini_app(SimpleNamespace(id=uid, role="tenant_admin"), db_session)
        resp = client.post(
            f"/api/v1/content-assets/{MASTER_ID}/status",
            json={"content_status": "draft"},
        )
        assert resp.status_code == 409
        assert resp.json()["message"] == "illegal_content_status_transition"

    def test_archived_value_rejected_400(self, db_session):
        """裁-3：严禁写入 archived / verification_failed → 400。"""
        tenant_id = "9a888888-8888-4888-8888-888888888888"
        _mk_tenant(db_session, tenant_id, "arch.local")
        _mk_master(db_session, MASTER_ID, tenant_id, status="published")
        uid = str(uuid.uuid4())
        _bind_user(db_session, uid, tenant_id, role="tenant_admin")
        client = _mini_app(SimpleNamespace(id=uid, role="tenant_admin"), db_session)
        for bad in ("archived", "verification_failed", "bogus"):
            resp = client.post(
                f"/api/v1/content-assets/{MASTER_ID}/status",
                json={"content_status": bad},
            )
            assert resp.status_code == 400, bad

    def test_legal_transition_persists_status(self, db_session):
        """draft → ready 合法：写入 content_masters.status。"""
        tenant_id = "9a999999-9999-4999-8999-999999999999"
        _mk_tenant(db_session, tenant_id, "ok.local")
        _mk_master(db_session, MASTER_ID, tenant_id, status="draft")
        uid = str(uuid.uuid4())
        _bind_user(db_session, uid, tenant_id, role="tenant_admin")
        client = _mini_app(SimpleNamespace(id=uid, role="tenant_admin"), db_session)
        resp = client.post(
            f"/api/v1/content-assets/{MASTER_ID}/status",
            json={"content_status": "ready"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["asset_id"] == MASTER_ID
        persisted = (
            db_session.query(ContentMaster).filter(ContentMaster.id == MASTER_ID).first()
        )
        assert persisted.status == "ready"


# ────────────────────────── 路由挂载（契约端点存在） ──────────────────────────


class TestRouteMounted:
    def test_route_mounted_in_app(self):
        from app.main import app

        paths = app.openapi()["paths"]
        assert "/api/v1/content-assets" in paths
        assert "get" in paths["/api/v1/content-assets"]
        assert "/api/v1/content-assets/{asset_id}" in paths
        assert "get" in paths["/api/v1/content-assets/{asset_id}"]
        assert "/api/v1/content-assets/{asset_id}/status" in paths
        assert "post" in paths["/api/v1/content-assets/{asset_id}/status"]
