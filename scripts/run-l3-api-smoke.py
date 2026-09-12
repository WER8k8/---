#!/usr/bin/env python3
"""T-QA-06：L3 API 六项冒烟（无需浏览器）。"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

os.environ.setdefault("JWT_SECRET_KEY", "l3-smoke-" + ("x" * 24))
os.environ.setdefault("MVP_LAUNCH", "1")


def main() -> int:
    from fastapi.testclient import TestClient
    from app.main import app
    from app.core.security import create_access_token, get_password_hash
    from app.core.database import rebind_engine
    from app.db.session import SessionLocal, init_db
    from app.models.user import User
    import uuid

    rebind_engine(os.environ.get("DATABASE_URL"))
    init_db()

    client = TestClient(app, raise_server_exceptions=False)
    checks: list[dict] = []

    def record(name: str, ok: bool, detail: str = "") -> None:
        checks.append({"name": name, "ok": ok, "detail": detail})

    r = client.get("/api/v1/health")
    record("health", r.status_code == 200, str(r.status_code))

    db = SessionLocal()
    try:
        user = User(
            id=str(uuid.uuid4()),
            username=f"l3-{uuid.uuid4().hex[:8]}",
            email=f"l3-{uuid.uuid4().hex[:8]}@t.com",
            hashed_password=get_password_hash("TestPass123!"),
            role="super_admin",
            is_active=True,
        )
        db.add(user)
        db.commit()
        token = create_access_token({"sub": user.id})
    finally:
        db.close()
    h = {"Authorization": f"Bearer {token}"}

    for path in (
        "/api/v1/bff/client/bootstrap",
        "/api/v1/platforms/catalog",
        "/api/v1/inquiries/unified",
        "/api/v1/analytics/traffic-board",
        "/api/v1/ubrain/commercial-os/status",
        "/api/v1/seo/report/export?format=json",
    ):
        r = client.get(path, headers=h)
        ok = r.status_code == 200 and (
            r.headers.get("content-type", "").startswith("text/html")
            or (r.json().get("code") == 0 if "json" in r.headers.get("content-type", "") else True)
        )
        if path.endswith("json"):
            ok = r.status_code == 200
        record(path, ok, str(r.status_code))

    r_exp = client.get("/api/v1/inquiries/export?scope=tenant", headers=h)
    record("inquiries_export", r_exp.status_code == 200, str(r_exp.status_code))

    all_ok = all(c["ok"] for c in checks)
    out = {
        "all_ok": all_ok,
        "checks": checks,
        "engineering_l3_ready": all_ok,
    }
    sign_dir = ROOT / "docs" / "pm-signoffs"
    sign_dir.mkdir(parents=True, exist_ok=True)
    sign_path = sign_dir / "l3-signoff.json"
    sign = {}
    if sign_path.is_file():
        sign = json.loads(sign_path.read_text(encoding="utf-8"))
    sign.update(
        {
            "engineering_automated_l3": all_ok,
            "automated_checks": checks,
            "pm_signed": sign.get("pm_signed", False),
        }
    )
    sign_path.write_text(
        json.dumps(sign, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    report = ROOT / "docs" / "l3-api-smoke-latest.json"
    report.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
