#!/usr/bin/env python3
"""本地验证流量看板链路（默认 SQLite 文件库，无需 Postgres）。

用法（仓库根目录）:
  python scripts/verify_traffic_pipeline.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault(
    "DATABASE_URL",
    f"sqlite:///{(BACKEND / 'youding_traffic_verify.db').as_posix()}",
)
os.environ.setdefault("SECRET_KEY", "dev-verify-traffic-pipeline-secret-32b")
os.environ.setdefault("JWT_SECRET_KEY", "dev-verify-traffic-jwt-secret-key-32b")
os.environ.setdefault("REDIS_ENABLED", "false")

from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.core.security import get_password_hash  # noqa: E402
from app.db.session import init_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models.tenant import Tenant, TenantPlan, UserTenant  # noqa: E402
from app.models.user import User  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402


def main() -> int:
    print("==> init_db (含 site_analytics_events)")
    init_db()
    db = SessionLocal()
    plan = TenantPlan(
        id=str(uuid4()),
        name="验证套餐",
        code=f"v-{uuid4().hex[:6]}",
        price_monthly=0,
        price_yearly=0,
    )
    tid = str(uuid4())
    domain = f"verify-{uuid4().hex[:6]}"
    tenant = Tenant(
        id=tid,
        name="验证租户",
        domain=domain,
        plan_id=plan.id,
        status="active",
        settings="{}",
        is_active=True,
    )
    uid = str(uuid4())
    uname = f"verify_ta_{uuid4().hex[:8]}"
    user = User(
        id=uid,
        username=uname,
        email=f"{uname}@local.test",
        hashed_password=get_password_hash("VerifyPass123!"),
        role="tenant_admin",
        is_active=True,
    )
    db.add_all([plan, tenant, user, UserTenant(user_id=uid, tenant_id=tid, role="owner", is_active=True)])
    db.commit()
    db.close()

    from app.core.database import get_db
    from app.db.session import get_db as session_get_db

    def _db():
        s = SessionLocal()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_db] = _db
    app.dependency_overrides[session_get_db] = _db

    host = f"{domain}.youding-saas.com"
    sid = "verify-session-1"
    failures: list[str] = []

    with TestClient(app, base_url="http://test") as c:
        steps = [
            ("site-context", lambda: c.get(f"/api/v1/analytics/site-context?host={host}")),
            (
                "event page_view",
                lambda: c.post(
                    "/api/v1/analytics/event",
                    json={
                        "event_type": "page_view",
                        "session_id": sid,
                        "tenant_id": tid,
                        "page_path": "/",
                    },
                ),
            ),
            (
                "public inquiry",
                lambda: c.post(
                    "/api/v1/inquiries/public",
                    json={
                        "name": "测试",
                        "phone": "13800138000",
                        "message": "验证询盘",
                        "session_id": sid,
                        "tenant_id": tid,
                        "landing_path": "/",
                        "last_click_label": "CTA",
                    },
                ),
            ),
        ]
        for name, fn in steps:
            r = fn()
            ok = r.status_code == 200 and r.json().get("code", -1) == 0
            print(f"  {'OK' if ok else 'FAIL'} {name} -> {r.status_code}")
            if not ok:
                failures.append(f"{name}: {r.text[:200]}")

        from app.core.security import get_current_user

        auth_user = SimpleNamespace(
            id=uid,
            username=uname,
            email=f"{uname}@local.test",
            role="tenant_admin",
            is_active=True,
        )
        app.dependency_overrides[get_current_user] = lambda: auth_user
        r = c.get("/api/v1/analytics/traffic-board?period=7d")
        body = r.json()
        summary = (body.get("data") or {}).get("summary") or {}
        ok = r.status_code == 200 and summary.get("page_views", 0) >= 1
        print(
            f"  {'OK' if ok else 'FAIL'} traffic-board "
            f"pv={summary.get('page_views')} inq={summary.get('inquiries')}"
        )
        if not ok:
            failures.append(f"traffic-board: {r.text[:300]}")
        app.dependency_overrides.pop(get_current_user, None)

    app.dependency_overrides.clear()

    if failures:
        print("\nFAILED:")
        for f in failures:
            print(" -", f)
        return 1
    print("\nAll traffic pipeline checks passed.")
    print(f"SQLite DB: {os.environ['DATABASE_URL']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
