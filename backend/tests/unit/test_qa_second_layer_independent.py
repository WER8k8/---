# -*- coding: utf-8 -*-
"""QA 第二层独立验证（秦戈）—— 模块4 ContentAsset / 模块10 轨2计费 / 模块5 501。
独立构例，不复用作者断言。仅读/自建自清式隔离库操作，不写生产库。
"""
from __future__ import annotations

import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.content import InclusionStatus, PublishTask
from app.models.content_master import ContentMaster
from app.models.inquiry import Inquiry
from app.models.meter import MeterEvent
from app.models.tenant import Tenant, UserTenant
from app.services import content_asset_service as cas


# ══════════════════════════════════════════════════════════════════
# ① 模块4 ContentAsset —— 路由越权/边界 + 派生优先级 + canonical
# ══════════════════════════════════════════════════════════════════

def _m4_client(user, db):
    from app.api.v1.routes.content_assets import router
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/content-assets")
    app.dependency_overrides[get_db] = lambda: db
    if user is not None:
        app.dependency_overrides[get_current_user] = lambda: user
    return TestClient(app)


def _tenant(db, tid, dom):
    db.add(Tenant(id=tid, name=f"t-{tid[:8]}", domain=dom, plan_id=str(uuid.uuid4()), is_active=True))
    db.flush()


def _master(db, mid, tid, **kw):
    db.add(ContentMaster(id=mid, tenant_id=tid, title="qa-asset", **kw))
    db.flush()


def _bind(db, uid, tid, role="viewer"):
    db.add(UserTenant(id=str(uuid.uuid4()), user_id=str(uid), tenant_id=tid, role=role, is_active=True))
    db.flush()


# 运营者：tenant_admin ∈ _ADMIN_ROLES → is_tenant_operator() 为真（满足跃迁权限）
M4_USER = SimpleNamespace(id=str(uuid.uuid4()), role="tenant_admin")
# 纯 viewer：content 仅有 read 权限 → is_tenant_operator() 为假（权限门禁反证）
M4_VIEWER = SimpleNamespace(id=str(uuid.uuid4()), role="viewer")


def _seed_m4(db):
    ta, tb = str(uuid.uuid4()), str(uuid.uuid4())
    _tenant(db, ta, f"a-{ta[:6]}.com")
    _tenant(db, tb, f"b-{tb[:6]}.com")
    ma, mb = str(uuid.uuid4()), str(uuid.uuid4())
    _master(db, ma, ta, status="draft")
    _master(db, mb, tb, status="draft")
    _bind(db, M4_USER.id, ta)
    _bind(db, M4_VIEWER.id, ta)
    return ta, tb, ma, mb


class TestM4Routes:
    def test_unauth_401_all_three(self, db_session):
        c = _m4_client(None, db_session)
        assert c.get("/api/v1/content-assets").status_code == 401
        assert c.get(f"/api/v1/content-assets/{uuid.uuid4()}").status_code == 401
        assert c.post(f"/api/v1/content-assets/{uuid.uuid4()}/status", json={"content_status": "ready"}).status_code == 401

    def test_cross_tenant_get_403(self, db_session):
        _, _, ma, mb = _seed_m4(db_session)
        c = _m4_client(M4_USER, db_session)
        assert c.get(f"/api/v1/content-assets/{ma}").status_code == 200
        assert c.get(f"/api/v1/content-assets/{mb}").status_code == 403      # 非成员 → 403

    def test_cross_tenant_post_status_403(self, db_session):
        _, _, ma, mb = _seed_m4(db_session)
        c = _m4_client(M4_USER, db_session)
        r = c.post(f"/api/v1/content-assets/{mb}/status", json={"content_status": "ready"})
        assert r.status_code == 403, r.text                                    # 越权改他人资产状态

    def test_viewer_member_not_operator_403(self, db_session):
        """同租户成员但非运营（viewer）→ 跃迁被权限门禁拦下 403（非 409/200）。"""
        _, _, ma, _ = _seed_m4(db_session)
        c = _m4_client(M4_VIEWER, db_session)
        r = c.post(f"/api/v1/content-assets/{ma}/status", json={"content_status": "ready"})
        assert r.status_code == 403, r.text
        # 且未发生写入：GET 仍为 draft
        assert c.get(f"/api/v1/content-assets/{ma}").json()["data"]["content_status"] == "draft"

    def test_non_uuid_400(self, db_session):
        _seed_m4(db_session)
        c = _m4_client(M4_USER, db_session)
        assert c.get("/api/v1/content-assets/not-a-uuid").status_code == 400
        assert c.post("/api/v1/content-assets/not-a-uuid/status", json={"content_status": "ready"}).status_code == 400

    def test_pagination_bounds_400(self, db_session):
        _seed_m4(db_session)
        c = _m4_client(M4_USER, db_session)
        assert c.get("/api/v1/content-assets?page=0").status_code == 400
        assert c.get("/api/v1/content-assets?page=-3").status_code == 400
        assert c.get("/api/v1/content-assets?size=0").status_code == 400
        assert c.get("/api/v1/content-assets?size=101").status_code == 400
        assert c.get("/api/v1/content-assets?size=99999").status_code == 400
        assert c.get("/api/v1/content-assets?page=1&size=100").status_code == 200
        assert c.get("/api/v1/content-assets?page=99999&size=20").status_code == 200

    def test_illegal_transition_409_and_valid_200(self, db_session):
        _, _, ma, _ = _seed_m4(db_session)
        c = _m4_client(M4_USER, db_session)
        # draft → published（跨跳）应 409
        assert c.post(f"/api/v1/content-assets/{ma}/status", json={"content_status": "published"}).status_code == 409
        # 非法目标值 archived → 400（白名单）
        assert c.post(f"/api/v1/content-assets/{ma}/status", json={"content_status": "archived"}).status_code == 400
        # draft → ready 合法 200
        assert c.post(f"/api/v1/content-assets/{ma}/status", json={"content_status": "ready"}).status_code == 200
        # ready → published 合法
        assert c.post(f"/api/v1/content-assets/{ma}/status", json={"content_status": "published"}).status_code == 200
        # published → draft 回退 → 409
        assert c.post(f"/api/v1/content-assets/{ma}/status", json={"content_status": "draft"}).status_code == 409

    def test_admin_bad_tenant_id_400(self, db_session):
        admin = SimpleNamespace(id=str(uuid.uuid4()), role="super_admin")
        _seed_m4(db_session)
        c = _m4_client(admin, db_session)
        assert c.get("/api/v1/content-assets?tenant_id=not-a-uuid").status_code == 400
        assert c.get("/api/v1/content-assets?tenant_id=" + str(uuid.uuid4())).status_code == 200

    def test_payload_has_15_fields(self, db_session):
        _, _, ma, _ = _seed_m4(db_session)
        c = _m4_client(M4_USER, db_session)
        body = c.get(f"/api/v1/content-assets/{ma}").json()["data"]
        assert len(body) == 15, sorted(body.keys())


class TestM4Derivation:
    def test_content_status_priority(self, db_session):
        ta = str(uuid.uuid4())
        _tenant(db_session, ta, f"p-{ta[:6]}.com")
        # draft（默认）
        m = str(uuid.uuid4()); _master(db_session, m, ta, status="draft")
        assert cas.derive_content_status(db_session, db_session.get(ContentMaster, m)) == "draft"
        # fact_checked（kernel.schema_ready）
        m2 = str(uuid.uuid4()); _master(db_session, m2, ta, status="draft", fact_kernel_json={"schema_ready": True})
        assert cas.derive_content_status(db_session, db_session.get(ContentMaster, m2)) == "fact_checked"
        # approved（preflight_approved_at）
        from datetime import datetime, timezone
        m3 = str(uuid.uuid4()); _master(db_session, m3, ta, status="draft", preflight_approved_at=datetime.now(timezone.utc))
        assert cas.derive_content_status(db_session, db_session.get(ContentMaster, m3)) == "approved"
        # queued（有 task 无 success）
        m4 = str(uuid.uuid4()); _master(db_session, m4, ta, status="ready")
        db_session.add(PublishTask(id=str(uuid.uuid4()), tenant_id=ta, content_master_id=m4,
                                   status="pending", platform_id=str(uuid.uuid4()),
                                   account_id=str(uuid.uuid4())))
        db_session.flush()
        assert cas.derive_content_status(db_session, db_session.get(ContentMaster, m4)) == "queued"
        # published（有 success task）
        m5 = str(uuid.uuid4()); _master(db_session, m5, ta, status="ready")
        db_session.add(PublishTask(id=str(uuid.uuid4()), tenant_id=ta, content_master_id=m5,
                                   status="success", platform_id=str(uuid.uuid4()),
                                   account_id=str(uuid.uuid4())))
        db_session.flush()
        assert cas.derive_content_status(db_session, db_session.get(ContentMaster, m5)) == "published"
        # archived（deleted_at 优先于一切）
        m6 = str(uuid.uuid4())
        _master(db_session, m6, ta, status="published", deleted_at=datetime.now(timezone.utc),
                fact_kernel_json={"schema_ready": True})
        assert cas.derive_content_status(db_session, db_session.get(ContentMaster, m6)) == "archived"

    def test_verification_failed(self, db_session):
        ta = str(uuid.uuid4()); _tenant(db_session, ta, f"v-{ta[:6]}.com")
        m = str(uuid.uuid4()); _master(db_session, m, ta, status="ready")
        tid = str(uuid.uuid4())
        db_session.add(PublishTask(id=tid, tenant_id=ta, content_master_id=m, status="success",
                                   platform_id=str(uuid.uuid4()), account_id=str(uuid.uuid4())))
        db_session.add(InclusionStatus(id=str(uuid.uuid4()), task_id=tid, is_included=False,
                                       url="https://ex.example/x"))
        db_session.flush()
        assert cas.derive_content_status(db_session, db_session.get(ContentMaster, m)) == "verification_failed"

    def test_canonical_three_levels(self, db_session):
        ta = str(uuid.uuid4()); _tenant(db_session, ta, f"c-{ta[:6]}.com")
        # ① 显式 tenant_canonical_url 优先
        m = str(uuid.uuid4()); _master(db_session, m, ta, tenant_canonical_url="https://explicit.example/x")
        t = db_session.get(Tenant, ta)
        assert cas.build_canonical_url(db_session, t, db_session.get(ContentMaster, m)) == "https://explicit.example/x"
        # ② 无显式 → SITE_URL 分支（无主域）
        m2 = str(uuid.uuid4()); _master(db_session, m2, ta)
        url = cas.build_canonical_url(db_session, t, db_session.get(ContentMaster, m2))
        from app.core.config import settings
        assert url.startswith(settings.SITE_URL.rstrip("/"))
        # 禁止平台默认域
        assert "youdingjiancai.com" not in url and "globaltrade-ai.site" not in url


# ══════════════════════════════════════════════════════════════════
# ② 模块10 轨2计费
# ══════════════════════════════════════════════════════════════════

def _inquiry(db, *, status="pending", tenant=True, contact=True):
    iid = str(uuid.uuid4())
    db.add(Inquiry(
        id=iid,
        name="qa",
        message="qa",
        status=status,
        tenant_id=(str(uuid.uuid4()) if tenant else None),
        phone=("13800000000" if contact else None),
        email=("qa@example.com" if contact else None),
    ))
    db.flush()
    return iid


def _meters(db, iid):
    return db.query(MeterEvent).filter(MeterEvent.event_key == f"inquiry:{iid}:qualified").all()


class TestM10Billing:
    def test_archived_never_billed(self, db_session):
        from app.services.inquiry_status_service import advance_inquiry_status
        iid = _inquiry(db_session, status="pending")
        i = db_session.get(Inquiry, iid)
        advance_inquiry_status(db_session, i, "lost", source="qa")   # lost → archived
        assert i.status == "archived"
        assert _meters(db_session, iid) == [], "archived 不得计费"

    def test_new_to_quoted_direct_billed(self, db_session):
        from app.services.inquiry_status_service import advance_inquiry_status
        iid = _inquiry(db_session, status="new")
        i = db_session.get(Inquiry, iid)
        advance_inquiry_status(db_session, i, "quoted", source="qa")  # 直跳 quoted
        ms = _meters(db_session, iid)
        assert len(ms) == 1, "new→quoted 直跳必须计费（修漏收）"
        assert ms[0].meter_code == "usage.qualified_inquiry"

    def test_idempotent_single_meter(self, db_session):
        from app.services.inquiry_status_service import advance_inquiry_status
        iid = _inquiry(db_session, status="new")
        i = db_session.get(Inquiry, iid)
        advance_inquiry_status(db_session, i, "in_progress", source="qa")
        advance_inquiry_status(db_session, i, "quoted", source="qa")   # 已在计费阶段，第二次不重复
        assert len(_meters(db_session, iid)) == 1

    def test_no_tenant_not_billed(self, db_session):
        from app.services.inquiry_status_service import advance_inquiry_status
        iid = _inquiry(db_session, status="new", tenant=False)
        i = db_session.get(Inquiry, iid)
        advance_inquiry_status(db_session, i, "quoted", source="qa")
        assert _meters(db_session, iid) == []

    def test_no_contact_not_billed(self, db_session):
        from app.services.inquiry_status_service import advance_inquiry_status
        iid = _inquiry(db_session, status="new", contact=False)
        i = db_session.get(Inquiry, iid)
        advance_inquiry_status(db_session, i, "quoted", source="qa")
        assert _meters(db_session, iid) == []

    def test_invalid_status_valueerror(self, db_session):
        from app.services.inquiry_status_service import advance_inquiry_status
        iid = _inquiry(db_session, status="new")
        i = db_session.get(Inquiry, iid)
        with pytest.raises(ValueError):
            advance_inquiry_status(db_session, i, "totally_bogus", source="qa")

    def test_illegal_transition(self, db_session):
        from app.services.billing.reservation_service import IllegalTransition
        from app.services.inquiry_status_service import advance_inquiry_status
        iid = _inquiry(db_session, status="closed")
        i = db_session.get(Inquiry, iid)
        with pytest.raises(IllegalTransition):
            advance_inquiry_status(db_session, i, "quoted", source="qa")   # closed→quoted 回退

    def test_single_write_point(self):
        """AST 级：`inquiry.status = <x>` 写入点全服务唯一（排除 docstring/注释的字符串误计）。"""
        import ast
        import inspect
        from app.services import inquiry_status_service as iss
        src = inspect.getsource(iss)
        hits = []
        for node in ast.walk(ast.parse(src)):
            targets = []
            if isinstance(node, ast.Assign):
                targets = node.targets
            elif isinstance(node, ast.AugAssign):
                targets = [node.target]
            for tgt in targets:
                if (
                    isinstance(tgt, ast.Attribute)
                    and tgt.attr == "status"
                    and isinstance(tgt.value, ast.Name)
                    and tgt.value.id == "inquiry"
                ):
                    hits.append(node.lineno)
        assert hits == [222], f"inquiry.status 写入点应唯一且仅 :222，实测 {hits}"

    def test_other_writers_delegate_only(self):
        """全服务模块内不得存在第二套 `inquiry.status` 直写（仅 SSOT 函数可写）。"""
        import ast
        import inspect
        from app.services import inquiry_status_service as iss
        from app.services.inquiry_funnel_state_machine import FUNNEL_STAGES, _ALIASES
        # 9 条别名（任务书口径）
        assert len(_ALIASES) == 9, sorted(_ALIASES)
        # 计费集合与漏斗阶段互斥于 archived
        from app.services.inquiry_status_service import BILLABLE_QUALIFIED_STAGES
        assert "archived" not in BILLABLE_QUALIFIED_STAGES
        assert "archived" in FUNNEL_STAGES
        # 代码级：全服务唯一赋值出现在 advance_inquiry_status 内
        tree = ast.parse(inspect.getsource(iss))
        func = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
                    and n.name == "advance_inquiry_status")
        a = func.body[0].lineno
        b = max(getattr(n, "lineno", a) for n in ast.walk(func))
        assigns = [n.lineno for n in ast.walk(func)
                   if isinstance(n, ast.Assign)
                   and any(isinstance(t, ast.Attribute) and t.attr == "status"
                           and isinstance(t.value, ast.Name) and t.value.id == "inquiry"
                           for t in n.targets)]
        assert len(assigns) == 1 and a <= assigns[0] <= b


# ══════════════════════════════════════════════════════════════════
# ③ 模块5 501（当前真实为 3 个会话端点；发布面已实装）
# ══════════════════════════════════════════════════════════════════

def _p_client(db, user):
    from app.api.v1.routes.platform import router
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: user
    return TestClient(app)


class TestM5_501:
    BASE = "/api/v1/platforms"
    STILL_501 = [
        ("post", f"{BASE}/accounts/a1/refresh"),
        ("post", f"{BASE}/accounts/a1/relogin"),
        ("post", f"{BASE}/keepalive"),
    ]

    @pytest.fixture
    def dbu(self):
        db = MagicMock()
        db.query.return_value.filter_by.return_value.first.return_value = None
        return db, SimpleNamespace(id="u1", role="super_admin")

    def test_three_endpoints_real_501_uniform(self, dbu):
        db, u = dbu
        c = _p_client(db, u)
        shapes = set()
        reasons = []
        for method, path in self.STILL_501:
            r = getattr(c, method)(path, json={})
            assert r.status_code == 501, f"{path} 非 501：{r.status_code} {r.text}"
            assert r.status_code not in (200, 500)
            b = r.json()
            assert set(b) == {"code", "message", "data"}, b
            assert b["code"] == 501 and isinstance(b["message"], str) and b["message"]
            assert set(b["data"]) == {"reason"} and b["data"]["reason"].endswith("_unsupported")
            shapes.add((tuple(sorted(b)), tuple(sorted(b["data"]))))
            reasons.append(b["data"]["reason"])
        assert len(shapes) == 1, f"形状不一致: {shapes}"
        assert len(set(reasons)) == len(reasons), f"reason 应互异: {reasons}"

    def test_publish_face_no_longer_501(self, dbu):
        """发布面 5 端点已 M1 阶段二实装 → 不得再返回 501。"""
        db, u = dbu
        c = _p_client(db, u)
        r = c.post(f"{self.BASE}/publish", json={"content_id": "x", "platform_ids": [], "account_ids": []})
        assert r.status_code != 501, f"发布面仍为 501（未实装）: {r.text}"

    def test_no_fake_501_as_200(self, dbu):
        """诚实 501 不得被写成 200 假 501。"""
        db, u = dbu
        c = _p_client(db, u)
        for method, path in self.STILL_501:
            r = getattr(c, method)(path, json={})
            assert r.status_code == 501 and r.json().get("code") == 501

    def test_unauthenticated_401_not_501(self):
        """未认证优先 401，不得把鉴权缺失伪装为 501。"""
        db = MagicMock()
        from app.api.v1.routes.platform import router as p_router
        app = FastAPI()
        app.include_router(p_router, prefix="/api/v1")
        app.dependency_overrides[get_db] = lambda: db
        c = TestClient(app)
        for method, path in self.STILL_501:
            r = getattr(c, method)(path, json={})
            assert r.status_code == 401, f"{path} 应为 401，实测 {r.status_code}"


class TestM5SourceGuards:
    """模块5：501 端点源码级守卫（无提前 mutation / 无吞 AttributeError）。"""

    def test_501_handlers_do_not_mutate(self):
        import ast
        import inspect
        from app.api.v1.routes import platform as pf
        src = inspect.getsource(pf)
        tree = ast.parse(src)
        names = {"refresh_account_session", "auto_relogin_account", "keepalive_check"}
        checked = 0
        for fn in [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]:
            if fn.name not in names:
                continue
            checked += 1
            # 函数体内不得出现任何 Commit / db.xxx mutate 调用
            for node in ast.walk(fn):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                    if node.func.attr in ("commit", "flush", "add", "delete", "execute"):
                        raise AssertionError(f"{fn.name} 含提前写操作: .{node.func.attr}")
        assert checked == 3, f"应检出 3 个 501 处理器，实测 {checked}"

    def test_no_broad_except_swallowing_attribute_error(self):
        """整个 platform 路由不得用 except Exception / AttributeError 静默吞错。"""
        import ast
        import inspect
        from app.api.v1.routes import platform as pf
        tree = ast.parse(inspect.getsource(pf))
        bad = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler):
                if node.type is None:
                    bad.append(node.lineno)
                    continue
                t = node.type
                names = []
                if isinstance(t, ast.Name):
                    names = [t.id]
                elif isinstance(t, ast.Tuple):
                    names = [e.id for e in t.elts if isinstance(e, ast.Name)]
                if "Exception" in names or "BaseException" in names or "AttributeError" in names:
                    bad.append(node.lineno)
        assert bad == [], f"发现吞错型 except（行 {bad}）"


# ══════════════════════════════════════════════════════════════════
# ④ 模块4 追加边界（fresh-eye，非作者用例）
# ══════════════════════════════════════════════════════════════════

class TestM4Extra:
    def test_status_whitelist_rejects_derived_only_values(self, db_session):
        """POST /status 仅收 draft/ready/published；派生态（archived/fact_checked/queued）→ 400。"""
        _, _, ma, _ = _seed_m4(db_session)
        c = _m4_client(M4_USER, db_session)
        for bad in ("archived", "verification_failed", "fact_checked", "queued", "approved", ""):
            r = c.post(f"/api/v1/content-assets/{ma}/status", json={"content_status": bad})
            assert r.status_code in (400, 422), f"{bad!r} 应被拒，实测 {r.status_code} {r.text}"

    def test_status_case_and_whitespace_normalized(self, db_session):
        """大小写/空白归一：'  READY  ' 视同 'ready' → 200。"""
        _, _, ma, _ = _seed_m4(db_session)
        c = _m4_client(M4_USER, db_session)
        r = c.post(f"/api/v1/content-assets/{ma}/status", json={"content_status": "  READY  "})
        assert r.status_code == 200, r.text

    def test_status_nonexistent_asset_404(self, db_session):
        _seed_m4(db_session)
        c = _m4_client(M4_USER, db_session)
        assert c.post(f"/api/v1/content-assets/{uuid.uuid4()}/status",
                      json={"content_status": "ready"}).status_code == 404
        assert c.get(f"/api/v1/content-assets/{uuid.uuid4()}").status_code == 404

    def test_nonmember_platform_admin_can_cross_tenant(self, db_session):
        """平台管理员（super_admin）跨租户读放行 200（对照非成员普通用户 403）。"""
        _, _, _, mb = _seed_m4(db_session)
        admin = SimpleNamespace(id=str(uuid.uuid4()), role="super_admin")
        c = _m4_client(admin, db_session)
        assert c.get(f"/api/v1/content-assets/{mb}").status_code == 200


# ══════════════════════════════════════════════════════════════════
# ⑤ 模块10 路由接线：converted→record_ops_win / lost→record_ops_loss
# ══════════════════════════════════════════════════════════════════

class TestM10RouteWinLoss:
    def _client(self, db, user):
        from app.api.v1.routes.inquiries import router as inq_router
        app = FastAPI()
        app.include_router(inq_router, prefix="/api/v1/inquiries")
        app.dependency_overrides[get_db] = lambda: db
        app.dependency_overrides[get_current_user] = lambda: user
        return TestClient(app)

    @pytest.fixture
    def admin(self):
        return SimpleNamespace(id=str(uuid.uuid4()), role="super_admin")

    def test_converted_alias_records_ops_win_and_bills(self, db_session, monkeypatch, admin):
        import app.services.acquisition.experience_feed as exp
        wins, losses = [], []
        monkeypatch.setattr(exp, "record_ops_win", lambda *a, **k: wins.append(k) or {"ok": True})
        monkeypatch.setattr(exp, "record_ops_loss", lambda *a, **k: losses.append(k) or {"ok": True})
        iid = _inquiry(db_session, status="new")
        c = self._client(db_session, admin)
        r = c.put(f"/api/v1/inquiries/{iid}/status", json={"status": "converted"})
        assert r.status_code == 200, r.text
        assert len(wins) == 1 and not losses, (wins, losses)
        assert wins[0]["inquiry_id"] == iid
        # converted 归一为 closed ∈ 计费集合 → 一条计量（直跳漏收已修）
        assert len(_meters(db_session, iid)) == 1

    def test_lost_alias_records_ops_loss_and_not_billed(self, db_session, monkeypatch, admin):
        import app.services.acquisition.experience_feed as exp
        wins, losses = [], []
        monkeypatch.setattr(exp, "record_ops_win", lambda *a, **k: wins.append(k) or {"ok": True})
        monkeypatch.setattr(exp, "record_ops_loss", lambda *a, **k: losses.append(k) or {"ok": True})
        iid = _inquiry(db_session, status="new")
        c = self._client(db_session, admin)
        r = c.put(f"/api/v1/inquiries/{iid}/status", json={"status": "lost"})
        assert r.status_code == 200, r.text
        assert len(losses) == 1 and not wins, (wins, losses)
        assert _meters(db_session, iid) == []   # lost→archived 不计费
