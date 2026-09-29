# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""模块2 行业参数包管理面 —— 独立越权/边界探针（QA 自研，不复用被测方测试）。

用真实 FastAPI 路由 + 临时 sqlite 库，按角色矩阵实际发请求，逐条打印
(用例 / 期望 / 实际 / 判定)。只读生产代码；临时库随进程销毁。

用法::

    cd backend
    ./.venv/Scripts/python.exe scripts/qa/probe_industry_profile_security.py

退出码 0 = 全部符合期望；1 = 存在不符（列出）。
"""
from __future__ import annotations

import json
import sys
import tempfile
import uuid
from pathlib import Path
from types import SimpleNamespace

BACKEND_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BACKEND_ROOT))

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.core.database import get_db  # noqa: E402
from app.core.security import get_current_user  # noqa: E402
from app.models import Base  # noqa: E402
from app.models.industry_profile import IndustryProfile  # noqa: E402
from app.models.tenant import Tenant, UserTenant  # noqa: E402

TENANT_A = "6a100000-0000-4000-8000-00000000000a"
TENANT_B = "6a100000-0000-4000-8000-00000000000b"

RULES = {
    "material_base_prices": {"ceramic": 25.0},
    "material_densities": {"ceramic": 2200},
    "surface_fees": {"polished": 0.0},
    "edge_fees": {"eased": 0.0},
    "grade_multipliers": {"standard": 1.0},
    "moq_tiers": [{"min_quantity_sqm": 1000, "discount_rate": 0.05}],
}

_results: list[tuple[str, str, str, bool]] = []


def record(name: str, expect: str, actual: str, ok: bool) -> None:
    _results.append((name, expect, actual, ok))


def build_engine():
    tmp = Path(tempfile.mkdtemp(prefix="qa_ip_probe_")) / "probe.db"
    eng = create_engine(f"sqlite:///{tmp.as_posix()}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=eng)
    return eng


def mini_app(router, user, db, prefix="/api/v1/industry-profiles"):
    app = FastAPI()
    app.include_router(router, prefix=prefix)
    app.dependency_overrides[get_db] = lambda: db
    if user is not None:
        app.dependency_overrides[get_current_user] = lambda: user
    return TestClient(app)


def seed(db):
    for code, ver, status in [("building_materials", 1, "active"), ("machinery", 1, "active"),
                              ("machinery", 2, "draft"), ("machinery", 3, "retired")]:
        db.add(IndustryProfile(id=str(uuid.uuid4()), code=code, name=f"{code}-{ver}",
                               version=ver, status=status, unit_system="metric", boq_rules=RULES))
    db.add(Tenant(id=TENANT_A, name="A", domain="a.example.com", plan_id=str(uuid.uuid4())))
    db.add(Tenant(id=TENANT_B, name="B", domain="b.example.com", plan_id=str(uuid.uuid4())))
    db.commit()
    return db


def bind(db, uid, tid, role):
    db.add(UserTenant(id=str(uuid.uuid4()), user_id=uid, tenant_id=tid, role=role, is_active=True))
    db.commit()


def main() -> int:
    from app.api.v1.routes.industry_profiles import router

    eng = build_engine()
    Session = sessionmaker(bind=eng)
    db = Session()
    seed(db)

    uid_viewer = str(uuid.uuid4())
    bind(db, uid_viewer, TENANT_A, "viewer")
    uid_tadmin = str(uuid.uuid4())
    bind(db, uid_tadmin, TENANT_A, "tenant_admin")
    uid_owner = str(uuid.uuid4())
    bind(db, uid_owner, TENANT_A, "owner")
    uid_stranger = str(uuid.uuid4())  # 与任何租户无关联

    P = "/api/v1/industry-profiles"

    # ── 认证 ──
    c = mini_app(router, None, db)
    r = c.get(P)
    record("无 token GET 列表", "401", str(r.status_code), r.status_code == 401)

    # ── 平台管理员门禁（create / activate） ──
    c = mini_app(router, SimpleNamespace(id=uid_viewer, role="viewer"), db)
    r = c.post(f"{P}/machinery/versions", json={"name": "x"})
    record("viewer 建版本", "403", str(r.status_code), r.status_code == 403)
    r = c.post(f"{P}/machinery/activate", json={"version": 2})
    record("viewer 激活", "403", str(r.status_code), r.status_code == 403)

    c = mini_app(router, SimpleNamespace(id=uid_tadmin, role="tenant_admin"), db)
    r = c.post(f"{P}/machinery/activate", json={"version": 2})
    record("tenant_admin 激活（非平台管理员）", "403", str(r.status_code), r.status_code == 403)

    c = mini_app(router, SimpleNamespace(id=str(uuid.uuid4()), role="super_admin"), db)
    r = c.post(f"{P}/machinery/activate", json={"version": 2})
    record("super_admin 激活 draft v2", "200", str(r.status_code), r.status_code == 200)

    # ── 租户绑定越权（IDOR / 跨租户） ──
    c = mini_app(router, SimpleNamespace(id=uid_viewer, role="viewer"), db)
    r = c.put(f"{P}/tenants/{TENANT_A}", json={"code": "machinery"})
    record("本租户 viewer 改绑定", "403", str(r.status_code), r.status_code == 403)

    c = mini_app(router, SimpleNamespace(id=uid_owner, role="owner"), db)
    r = c.put(f"{P}/tenants/{TENANT_A}", json={"code": "building_materials"})
    record("本租户 owner 改绑定", "200", str(r.status_code), r.status_code == 200)

    c = mini_app(router, SimpleNamespace(id=uid_stranger, role="viewer"), db)
    r = c.get(f"{P}/tenants/{TENANT_A}")
    record("无关联用户读他人租户", "404", str(r.status_code), r.status_code == 404)
    r = c.put(f"{P}/tenants/{TENANT_A}", json={"code": "machinery"})
    record("无关联用户写他人租户", "404", str(r.status_code), r.status_code == 404)

    c = mini_app(router, SimpleNamespace(id=uid_viewer, role="viewer"), db)
    r = c.get(f"{P}/tenants/{TENANT_B}")
    record("A 成员读 B 租户", "404", str(r.status_code), r.status_code == 404)

    # ── 绑定目标状态门控 ──
    c = mini_app(router, SimpleNamespace(id=uid_tadmin, role="tenant_admin"), db)
    r = c.put(f"{P}/tenants/{TENANT_A}", json={"code": "machinery"})
    record("绑 active 版本（v2 已激活？machinery active 仍 v1）", "200", str(r.status_code), r.status_code == 200)
    db.rollback()
    r = c.put(f"{P}/tenants/{TENANT_A}", json={"code": "does_not_exist"})
    record("绑不存在的 code", "400", str(r.status_code), r.status_code == 400)
    r = c.put(f"{P}/tenants/{TENANT_A}", json={"code": None})
    record("清除绑定 code=null", "200", str(r.status_code), r.status_code == 200)

    # 绑 retired-only code
    db.add(IndustryProfile(id=str(uuid.uuid4()), code="only_retired", name="r", version=1,
                           status="retired", unit_system="metric", boq_rules=RULES))
    db.commit()
    r = c.put(f"{P}/tenants/{TENANT_A}", json={"code": "only_retired"})
    record("绑 retired-only code", "400", str(r.status_code), r.status_code == 400)
    db.add(IndustryProfile(id=str(uuid.uuid4()), code="only_draft", name="d", version=1,
                           status="draft", unit_system="metric", boq_rules=RULES))
    db.commit()
    r = c.put(f"{P}/tenants/{TENANT_A}", json={"code": "only_draft"})
    record("绑 draft-only code", "400", str(r.status_code), r.status_code == 400)

    # ── 边界：version query / body ──
    c = mini_app(router, SimpleNamespace(id=str(uuid.uuid4()), role="admin"), db)
    for v, exp in [("0", 422), ("-1", 422), ("abc", 422), ("999999", 404), ("1", 200)]:
        r = c.get(f"{P}/machinery?version={v}")
        record(f"详情 version={v}", str(exp), str(r.status_code), r.status_code == exp)

    c = mini_app(router, SimpleNamespace(id=str(uuid.uuid4()), role="super_admin"), db)
    for body, exp, tag in [
        ({"version": 0}, 400, "0"),
        ({"version": -1}, 400, "-1"),
        ({"version": "2"}, 400, "字符串2"),
        ({"version": True}, 400, "bool"),
        ({"version": 999999}, 404, "不存在"),
        ({}, 400, "缺 version"),
    ]:
        r = c.post(f"{P}/machinery/activate", json=body)
        record(f"激活 version={tag}", str(exp), str(r.status_code), r.status_code == exp)

    for body, exp, tag in [
        ({}, 400, "缺 name"),
        ({"name": "x" * 121}, 400, "name超长"),
        ({"name": "ok", "boq_rules": "not-dict"}, 400, "boq_rules非dict"),
        ({"name": "ok", "base_version": 0}, 400, "base_version=0"),
        ({"name": "ok"}, 201, "正常"),
    ]:
        r = c.post(f"{P}/newcode/versions", json=body)
        record(f"建版本 {tag}", str(exp), str(r.status_code), r.status_code == exp)

    # ── 路由歧义守卫 ──
    r = c.get(f"{P}/tenants")
    record("单段 /tenants 不被 {code} 吞掉", "非200", str(r.status_code), r.status_code != 200)

    # ── 详情不存在 ──
    r = c.get(f"{P}/no_such_code")
    record("详情不存在 code", "404", str(r.status_code), r.status_code == 404)

    # ── 输出矩阵 ──
    print("=" * 90)
    print(f"{'用例':<42}{'期望':<8}{'实际':<8}判定")
    print("-" * 90)
    fails = 0
    for name, exp, act, ok in _results:
        if not ok:
            fails += 1
        print(f"{name:<42}{exp:<8}{act:<8}{'PASS' if ok else 'FAIL'}")
    print("=" * 90)
    print(f"合计 {len(_results)} 例，PASS {len(_results) - fails}，FAIL {fails}")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
