# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Industry Profile 解析链 / 零漂移真反证 / 管理面 测试（模块2 契约 §7 矩阵）。

覆盖：
- 解析优先级（未配 → 默认；配 → 覆盖；code 缺失/坏 JSON → 安全回落）；
- 管理面（激活互斥；绑定 draft/retired → 400；跨租户 → 404；超管门禁 → 403）；
- 管道层零漂移**真反证**（负向逐字段相等 + 阳性对照必须变化，两条配对）；
- 非建材端到端（machinery）可复算断言；
- 管理面 6 端点挂载。
"""
from __future__ import annotations

import json
import uuid
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.boq_import import BoqLineItem
from app.models.industry_profile import IndustryProfile
from app.models.tenant import Tenant, UserTenant
from app.services import boq_pipeline_service as bps
from app.services import industry_profile_service as ips
from app.services.boq_calculator import (
    _DEFAULT_MOQ_TIERS,
    _EDGE_FEES,
    _GRADE_MULTIPLIER,
    _MATERIAL_BASE_PRICES,
    _MATERIAL_DENSITY,
    _SURFACE_FEES,
    BOQCalculator,
)

TENANT = "6a222222-2222-4222-8222-222222222222"
TENANT_OTHER = "6a333333-3333-4333-8333-333333333333"

# §6.1 machinery 最小必备键（与 scripts/seeds/seed_machinery_profile.py 一致）
MACHINERY_RULES = {
    "material_base_prices": {"steel_plate": 420.0, "aluminum": 560.0, "cast_iron": 300.0},
    "material_densities": {"steel_plate": 7850, "aluminum": 2700, "cast_iron": 7200},
    "surface_fees": {"raw": 0.0, "painted": 8.0, "galvanized": 12.0},
    "edge_fees": {"none": 0.0, "machined": 15.0},
    "grade_multipliers": {"standard": 1.0, "precision": 1.25},
    "moq_tiers": [{"min_quantity_sqm": 100, "discount_rate": 0.03}],
    "material_tokens": {
        "steel_plate": ["steel plate", "钢板", "q235", "carbon steel"],
        "aluminum": ["aluminum", "铝", "6061"],
        "cast_iron": ["cast iron", "铸铁"],
    },
    "default_material": "steel_plate",
}


def _building_rules() -> dict:
    """建材默认 boq_rules（逐键等于引擎内置 → 零漂移）。"""
    return {
        "material_base_prices": dict(_MATERIAL_BASE_PRICES),
        "material_densities": dict(_MATERIAL_DENSITY),
        "surface_fees": dict(_SURFACE_FEES),
        "edge_fees": dict(_EDGE_FEES),
        "grade_multipliers": dict(_GRADE_MULTIPLIER),
        "moq_tiers": [dict(t) for t in _DEFAULT_MOQ_TIERS],
    }


def _mk_profile(db, code, version=1, status="active", rules=None):
    profile = IndustryProfile(
        id=str(uuid.uuid4()),
        code=code,
        name=f"{code}-{version}",
        version=version,
        status=status,
        unit_system="metric",
        boq_rules=rules if rules is not None else {},
    )
    db.add(profile)
    db.commit()
    return profile


def _mk_tenant(db, tid, settings=None):
    tenant = Tenant(
        id=str(tid),
        name=f"tenant-{str(tid)[:8]}",
        domain=f"t-{str(tid)[:8]}.example.com",
        plan_id=str(uuid.uuid4()),
        settings=settings,
    )
    db.add(tenant)
    db.commit()
    return tenant


def _bind_user(db, user_id, tenant_id):
    db.add(
        UserTenant(
            id=str(uuid.uuid4()),
            user_id=str(user_id),
            tenant_id=str(tenant_id),
            is_active=True,
        )
    )
    db.commit()


def _run_calc(db, tenant_id, defaults, desc, qty, unit="sqm"):
    """经真实管道跑一行核价（normalize → 人工置 confirmed → calculate）。

    incoterms 是引擎必填参数：默认注入 FOB，但允许 defaults 覆盖（如 CIF）。
    """
    defaults = {"incoterms": "FOB", **(defaults or {})}
    job = bps.create_job(db, tenant_id=tenant_id, source_name="t", defaults=defaults)
    bps.add_manual_lines(
        db, job, [{"description": desc, "quantity": qty, "unit": unit}], extractor="manual"
    )
    bps.run_normalization(db, job)
    line = db.query(BoqLineItem).filter_by(boq_job_id=job.id).first()
    line.review_status = "confirmed"
    db.add(line)
    db.commit()
    return bps.run_calculation(db, job)


def _mini_app(router, user, db, prefix):
    app = FastAPI()
    app.include_router(router, prefix=prefix)
    app.dependency_overrides[get_db] = lambda: db
    if user is not None:
        app.dependency_overrides[get_current_user] = lambda: user
    return TestClient(app)


# ================= 解析链 =================


class TestResolveChain:
    def test_resolve_returns_default_when_unconfigured(self, db_session):
        _mk_profile(db_session, "building_materials", 1, "active", _building_rules())
        _mk_tenant(db_session, TENANT)  # settings=None
        prof = ips.resolve_profile_for_tenant(db_session, TENANT)
        assert prof is not None
        assert prof.code == "building_materials"

    def test_resolve_tenant_overrides_default(self, db_session):
        _mk_profile(db_session, "building_materials", 1, "active", _building_rules())
        _mk_profile(db_session, "machinery", 1, "active", MACHINERY_RULES)
        _mk_tenant(db_session, TENANT, json.dumps({"industry_profile_code": "machinery"}))
        prof = ips.resolve_profile_for_tenant(db_session, TENANT)
        assert prof is not None and prof.code == "machinery"

    def test_resolve_falls_back_when_code_missing(self, db_session):
        _mk_profile(db_session, "building_materials", 1, "active", _building_rules())
        _mk_tenant(db_session, TENANT, json.dumps({"industry_profile_code": "nonexistent"}))
        prof = ips.resolve_profile_for_tenant(db_session, TENANT)
        assert prof is not None and prof.code == "building_materials"

    def test_resolve_broken_settings_json_is_safe(self, db_session):
        _mk_profile(db_session, "building_materials", 1, "active", _building_rules())
        _mk_tenant(db_session, TENANT, "{bad json")
        prof = ips.resolve_profile_for_tenant(db_session, TENANT)  # 不得抛异常
        assert prof is not None and prof.code == "building_materials"

    def test_resolve_overrides_for_tenant_unconfigured_is_zero_drift(self, db_session):
        """未配租户 → 覆盖包 == 默认建材包（与引擎内置逐键相等 → 空转即零漂移）。"""
        _mk_profile(db_session, "building_materials", 1, "active", _building_rules())
        _mk_tenant(db_session, TENANT)
        ov = ips.resolve_boq_overrides_for_tenant(db_session, TENANT)
        assert ov["material_base_prices"] == _MATERIAL_BASE_PRICES


# ================= 管理面（服务层） =================


class TestManagementService:
    def test_activate_is_exclusive(self, db_session):
        _mk_profile(db_session, "machinery", 1, "active", MACHINERY_RULES)
        _mk_profile(db_session, "machinery", 2, "draft", MACHINERY_RULES)
        ips.activate_profile(db_session, "machinery", 2, actor="tester")
        actives = (
            db_session.query(IndustryProfile)
            .filter(IndustryProfile.code == "machinery", IndustryProfile.status == "active")
            .all()
        )
        assert len(actives) == 1
        assert actives[0].version == 2

    def test_set_tenant_profile_rejects_draft(self, db_session):
        _mk_profile(db_session, "machinery", 1, "draft", MACHINERY_RULES)
        _mk_tenant(db_session, TENANT)
        with pytest.raises(ValueError):
            ips.set_tenant_profile_code(db_session, TENANT, "machinery", actor="tester")

    def test_set_tenant_profile_preserves_other_settings_keys(self, db_session):
        """只改 industry_profile_code 一个键，不整体替换（churn / ai_traffic 共用此列）。"""
        _mk_profile(db_session, "machinery", 1, "active", MACHINERY_RULES)
        _mk_tenant(
            db_session,
            TENANT,
            json.dumps({"ai_traffic_enabled": True, "keep_me": {"a": 1}}),
        )
        ips.set_tenant_profile_code(db_session, TENANT, "machinery", actor="tester")
        tenant = db_session.query(Tenant).filter(Tenant.id == TENANT).first()
        data = json.loads(tenant.settings)
        assert data["industry_profile_code"] == "machinery"
        assert data["ai_traffic_enabled"] is True
        assert data["keep_me"] == {"a": 1}

    def test_activate_retired_version_conflicts(self, db_session):
        _mk_profile(db_session, "machinery", 1, "retired", MACHINERY_RULES)
        with pytest.raises(ips.ProfileConflictError):
            ips.activate_profile(db_session, "machinery", 1, actor="tester")


# ================= 零漂移【真反证】 =================


class TestZeroDrift:
    def test_zero_drift_service_layer(self, db_session):
        """boq_overrides(建材) 的 6 键与 boq_calculator 内置逐键相等。"""
        _mk_profile(db_session, "building_materials", 1, "active", _building_rules())
        ov = ips.boq_overrides(ips.get_active_profile(db_session, "building_materials"))
        assert set(ov.keys()) == {
            "material_base_prices",
            "material_densities",
            "surface_fees",
            "edge_fees",
            "grade_multipliers",
            "moq_tiers",
        }
        assert ov["material_base_prices"] == _MATERIAL_BASE_PRICES
        assert ov["material_densities"] == _MATERIAL_DENSITY
        assert ov["surface_fees"] == _SURFACE_FEES
        assert ov["edge_fees"] == _EDGE_FEES
        assert ov["grade_multipliers"] == _GRADE_MULTIPLIER
        assert ov["moq_tiers"] == _DEFAULT_MOQ_TIERS

    @pytest.mark.parametrize(
        "defaults,desc,qty",
        [
            ({}, "全抛釉瓷砖 800x800", "1000"),
            (
                {
                    "thickness_mm": 30,
                    "material_grade": "premium",
                    "surface_finish": "honed",
                    "edge_profile": "beveled",
                },
                "大理石大板 意大利白",
                "300",
            ),
            (
                {
                    "customization": True,
                    "logo_printing": True,
                    "inspection_required": True,
                    "certification": "ce",
                },
                "花岗岩 台面",
                "120",
            ),
            ({"insurance_required": True, "incoterms": "CIF"}, "木质 地板", "500"),
            (
                {
                    "material_grade": "commercial",
                    "surface_finish": "sandblasted",
                    "edge_profile": "ogee",
                },
                "瓷质砖",
                "6000",
            ),
            ({"small_batch_surcharge": True}, "瓷砖", "30"),
            ({"thickness_mm": 12, "material_grade": "b"}, "金属 板", "2500"),
            (
                {
                    "surface_finish": "brushed",
                    "edge_profile": "half_bullnose",
                    "certification": "sgs",
                    "incoterms": "CIF",
                },
                "大理石 门槛石",
                "1500",
            ),
        ],
    )
    def test_zero_drift_pipeline_end_to_end(self, db_session, defaults, desc, qty):
        """租户未配 Profile：管道每行 calc dict 逐字段 == 直接 BOQCalculator().calculate。"""
        _mk_profile(db_session, "building_materials", 1, "active", _building_rules())
        _mk_tenant(db_session, TENANT)
        result = _run_calc(db_session, TENANT, defaults, desc, qty)
        line_results = [l for l in result["lines"] if "calc" in l]
        assert line_results
        calc = BOQCalculator()
        for lr in line_results:
            assert lr["calc"] == calc.calculate(dict(lr["params"]))

    def test_zero_drift_positive_control(self, db_session):
        """同参数下租户切成 machinery → base_price 必须变化（420≠120），否则注入是空转。"""
        _mk_profile(db_session, "building_materials", 1, "active", _building_rules())
        _mk_profile(db_session, "machinery", 1, "active", MACHINERY_RULES)
        _mk_tenant(db_session, TENANT, json.dumps({"industry_profile_code": "machinery"}))
        _mk_tenant(db_session, TENANT_OTHER)  # 未配 → 默认建材

        machinery_calc = _run_calc(db_session, TENANT, {"incoterms": "FOB"}, "Q235 钢板 3mm", "500")
        default_calc = _run_calc(db_session, TENANT_OTHER, {"incoterms": "FOB"}, "Q235 钢板 3mm", "500")

        m = machinery_calc["lines"][0]["calc"]
        d = default_calc["lines"][0]["calc"]
        assert m["base_price"] == 420.0
        assert d["base_price"] == 120.0
        assert m["base_price"] != d["base_price"]


# ================= 材料词表随 Profile 变 =================


class TestMaterialVocabulary:
    def test_material_tokens_profile_driven(self):
        tokens_m, default_m = bps._material_vocabulary(MACHINERY_RULES)
        assert default_m == "steel_plate"
        assert bps._material_of("Q235 钢板", tokens_m) == "steel_plate"
        assert bps._material_of("Q235 钢板") == "metal"  # 默认建材词表：钢 → metal

    def test_material_conflict_uses_profile_tokens(self):
        tokens_m, _ = bps._material_vocabulary(MACHINERY_RULES)
        # machinery：钢板(steel_plate) vs 铝(aluminum) → 冲突
        assert bps.material_conflict("钢板", "铝型材", tokens_m) is not None
        # 默认建材：两者皆 metal → 不冲突
        assert bps.material_conflict("钢板", "铝型材") is None


# ================= 非建材端到端验收（machinery） =================


class TestMachineryEndToEnd:
    def test_machinery_end_to_end_quote(self, db_session):
        """§6.2 可复算断言：base 420 / subtotal 210000 / total 203700 / grand_total 203700。"""
        _mk_profile(db_session, "machinery", 1, "active", MACHINERY_RULES)
        _mk_tenant(db_session, TENANT, json.dumps({"industry_profile_code": "machinery"}))
        result = _run_calc(db_session, TENANT, {"incoterms": "FOB"}, "Q235 钢板 3mm", "500")
        lr = result["lines"][0]
        assert lr["params"]["material_type"] == "steel_plate"
        calc = lr["calc"]
        assert calc["base_price"] == 420.0
        assert calc["adjusted_unit_price"] == 420.0
        assert calc["subtotal"] == 210000.0
        assert calc["total"] == 203700.0
        assert result["grand_total_usd"] == 203700.0


# ================= 管理面路由 =================


class TestRoutes:
    def test_admin_route_mounted(self):
        from app.main import app

        paths = app.openapi()["paths"]
        combos = [
            ("get", "/api/v1/industry-profiles"),
            ("get", "/api/v1/industry-profiles/{code}"),
            ("post", "/api/v1/industry-profiles/{code}/versions"),
            ("post", "/api/v1/industry-profiles/{code}/activate"),
            ("get", "/api/v1/industry-profiles/tenants/{tenant_id}"),
            ("put", "/api/v1/industry-profiles/tenants/{tenant_id}"),
        ]
        for method, path in combos:
            assert path in paths, f"缺少路径 {path}"
            assert method in paths[path], f"{path} 缺少方法 {method}"

    def test_tenants_segment_not_swallowed_by_code_route(self, db_session):
        """路由歧义守卫：`/industry-profiles/tenants` 单段访问不得命中 `{code}` 返回 200。"""
        from app.api.v1.routes.industry_profiles import router

        _mk_profile(db_session, "building_materials", 1, "active", _building_rules())
        client = _mini_app(
            router,
            SimpleNamespace(id=str(uuid.uuid4()), role="admin"),
            db_session,
            "/api/v1/industry-profiles",
        )
        resp = client.get("/api/v1/industry-profiles/tenants")
        assert resp.status_code != 200
        assert resp.status_code == 404

    def test_list_industry_profiles_200(self, db_session):
        from app.api.v1.routes.industry_profiles import router

        _mk_profile(db_session, "building_materials", 1, "active", _building_rules())
        client = _mini_app(
            router,
            SimpleNamespace(id=str(uuid.uuid4()), role="admin"),
            db_session,
            "/api/v1/industry-profiles",
        )
        resp = client.get("/api/v1/industry-profiles")
        assert resp.status_code == 200
        codes = [i["code"] for i in resp.json()["data"]["items"]]
        assert "building_materials" in codes

    def test_binding_requires_tenant_admin_403(self, db_session):
        """本租户内非管理员成员改绑定 → 403。"""
        from app.api.v1.routes.industry_profiles import router

        _mk_profile(db_session, "building_materials", 1, "active", _building_rules())
        _mk_tenant(db_session, TENANT)
        uid = str(uuid.uuid4())
        db_session.add(
            UserTenant(id=str(uuid.uuid4()), user_id=uid, tenant_id=TENANT, role="viewer", is_active=True)
        )
        db_session.commit()
        client = _mini_app(
            router,
            SimpleNamespace(id=uid, role="viewer"),
            db_session,
            "/api/v1/industry-profiles",
        )
        resp = client.put(
            f"/api/v1/industry-profiles/tenants/{TENANT}", json={"code": "building_materials"}
        )
        assert resp.status_code == 403

    def test_activate_requires_super_admin(self, db_session):
        from app.api.v1.routes.industry_profiles import router

        _mk_profile(db_session, "machinery", 1, "active", MACHINERY_RULES)
        _mk_profile(db_session, "machinery", 2, "draft", MACHINERY_RULES)
        client = _mini_app(
            router,
            SimpleNamespace(id=str(uuid.uuid4()), role="tenant_admin"),
            db_session,
            "/api/v1/industry-profiles",
        )
        resp = client.post("/api/v1/industry-profiles/machinery/activate", json={"version": 2})
        assert resp.status_code == 403

    def test_create_version_rejects_bool_base_version(self, db_session):
        """P3-1 守卫：base_version=True（bool ⊂ int）必须 400，不得被当作 1 通过。"""
        from app.api.v1.routes.industry_profiles import router

        client = _mini_app(
            router,
            SimpleNamespace(id=str(uuid.uuid4()), role="super_admin"),
            db_session,
            "/api/v1/industry-profiles",
        )
        resp = client.post(
            "/api/v1/industry-profiles/newcode/versions",
            json={"name": "ok", "base_version": True},
        )
        assert resp.status_code == 400

    def test_platform_admin_uses_canonical_ssot(self):
        """P3-a：平台管理员判据须走 app.core.tenant_access SSOT（本地不得自造判定）。"""
        from app.api.v1.routes import industry_profiles as mod
        from app.core import tenant_access

        assert mod.is_platform_admin is tenant_access.is_platform_admin
        assert not hasattr(mod, "_is_platform_admin")
        assert not hasattr(mod, "_PLATFORM_ADMIN_ROLES")

    def test_tenant_binding_requires_active(self, db_session):
        from app.api.v1.routes.industry_profiles import router

        _mk_profile(db_session, "machinery", 1, "retired", MACHINERY_RULES)
        _mk_tenant(db_session, TENANT)
        client = _mini_app(
            router,
            SimpleNamespace(id=str(uuid.uuid4()), role="admin"),
            db_session,
            "/api/v1/industry-profiles",
        )
        resp = client.put(
            f"/api/v1/industry-profiles/tenants/{TENANT}", json={"code": "machinery"}
        )
        assert resp.status_code == 400

    def test_cross_tenant_404(self, db_session):
        from app.api.v1.routes.industry_profiles import router

        _mk_profile(db_session, "building_materials", 1, "active", _building_rules())
        _mk_tenant(db_session, TENANT)
        _mk_tenant(db_session, TENANT_OTHER)
        uid = str(uuid.uuid4())
        _bind_user(db_session, uid, TENANT)
        client = _mini_app(
            router,
            SimpleNamespace(id=uid, role="tenant_admin"),
            db_session,
            "/api/v1/industry-profiles",
        )
        resp = client.get(f"/api/v1/industry-profiles/tenants/{TENANT_OTHER}")
        assert resp.status_code == 404

    def test_tenant_binding_ok_and_reports_tenant_source(self, db_session):
        from app.api.v1.routes.industry_profiles import router

        _mk_profile(db_session, "building_materials", 1, "active", _building_rules())
        _mk_profile(db_session, "machinery", 1, "active", MACHINERY_RULES)
        _mk_tenant(db_session, TENANT)
        uid = str(uuid.uuid4())
        _bind_user(db_session, uid, TENANT)
        client = _mini_app(
            router,
            SimpleNamespace(id=uid, role="tenant_admin"),
            db_session,
            "/api/v1/industry-profiles",
        )
        put = client.put(
            f"/api/v1/industry-profiles/tenants/{TENANT}", json={"code": "machinery"}
        )
        assert put.status_code == 200
        assert put.json()["data"]["industry_profile_code"] == "machinery"
        got = client.get(f"/api/v1/industry-profiles/tenants/{TENANT}")
        assert got.status_code == 200
        assert got.json()["data"]["effective_code"] == "machinery"
        assert got.json()["data"]["source"] == "tenant"


# ================= 第二注入点：quotes /calculate-boq =================


class TestQuotesInjection:
    def test_requires_auth(self, db_session):
        from app.api.v1.quotes import router

        client = _mini_app(router, None, db_session, "/api/v1/quotes")
        resp = client.post(
            "/api/v1/quotes/calculate-boq",
            json={"material_type": "ceramic", "quantity_sqm": 500, "incoterms": "FOB"},
        )
        assert resp.status_code == 401

    def test_quotes_calculate_boq_injects_profile(self, db_session):
        from app.api.v1.quotes import router

        _mk_profile(db_session, "machinery", 1, "active", MACHINERY_RULES)
        _mk_tenant(db_session, TENANT, json.dumps({"industry_profile_code": "machinery"}))
        uid = str(uuid.uuid4())
        _bind_user(db_session, uid, TENANT)
        client = _mini_app(
            router, SimpleNamespace(id=uid, role="tenant_admin"), db_session, "/api/v1/quotes"
        )
        resp = client.post(
            "/api/v1/quotes/calculate-boq",
            json={"material_type": "steel_plate", "quantity_sqm": 500, "incoterms": "FOB"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["base_price"] == 420.0

    def test_quotes_calculate_boq_default_zero_drift(self, db_session):
        """老调用方（不传 profile、默认建材租户）数值不变：ceramic → 25。"""
        from app.api.v1.quotes import router

        _mk_profile(db_session, "building_materials", 1, "active", _building_rules())
        _mk_tenant(db_session, TENANT)
        uid = str(uuid.uuid4())
        _bind_user(db_session, uid, TENANT)
        client = _mini_app(
            router, SimpleNamespace(id=uid, role="tenant_admin"), db_session, "/api/v1/quotes"
        )
        resp = client.post(
            "/api/v1/quotes/calculate-boq",
            json={"material_type": "ceramic", "quantity_sqm": 500, "incoterms": "FOB"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["base_price"] == 25.0


# ================= 邻近旁路：trade_fulfillment_ops 最小诚实化 =================


class TestLegacyQuotePathHonesty:
    def test_legacy_path_rejects_non_building_profile(self, db_session):
        from app.api.v1.routes.trade_fulfillment_ops import router

        _mk_profile(db_session, "machinery", 1, "active", MACHINERY_RULES)
        _mk_tenant(db_session, TENANT, json.dumps({"industry_profile_code": "machinery"}))
        uid = str(uuid.uuid4())
        _bind_user(db_session, uid, TENANT)
        client = _mini_app(
            router, SimpleNamespace(id=uid, role="tenant_admin"), db_session, "/api/v1"
        )
        resp = client.post(
            "/api/v1/orders/fulfillment/quote",
            json={"quantity_sqm": 100, "spec_key": "x"},
        )
        assert resp.status_code == 422
        assert "industry_profile_unsupported_by_legacy_quote_path" in resp.json()["message"]

    def test_legacy_path_unchanged_for_building_profile(self, db_session):
        from app.api.v1.routes.trade_fulfillment_ops import router

        _mk_profile(db_session, "building_materials", 1, "active", _building_rules())
        _mk_tenant(db_session, TENANT)
        uid = str(uuid.uuid4())
        _bind_user(db_session, uid, TENANT)
        client = _mini_app(
            router, SimpleNamespace(id=uid, role="tenant_admin"), db_session, "/api/v1"
        )
        resp = client.post(
            "/api/v1/orders/fulfillment/quote",
            json={"quantity_sqm": 100, "spec_key": "rockwool_sandwich_50mm"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["cost_components_usd"]["exw_total"] > 0
