#!/usr/bin/env python3
"""SITE-DESIGN-01e/f · dev.local 租户种子 + L-Pro 发布门禁 E2E。"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
REPORT = ROOT / "docs" / "site-l-pro-publish-e2e-latest.json"
VENV_PY = BACKEND / ".venv" / "Scripts" / "python.exe"


def _ensure_seed() -> tuple[bool, str]:
    ensure = BACKEND / "scripts" / "ensure_dev_sqlite.py"
    proc = subprocess.run(
        [str(VENV_PY), str(ensure)],
        cwd=str(BACKEND),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    out = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode == 0, out[-1500:]


def _extract_site_content() -> dict | None:
    if str(BACKEND) not in sys.path:
        sys.path.insert(0, str(BACKEND))
    os.environ.setdefault("DB_TYPE", "sqlite")
    os.environ.setdefault("DATABASE_URL", f"sqlite:///{(BACKEND / 'youding_dev.db').as_posix()}")
    os.environ.setdefault("SECRET_KEY", "e2e-" + ("x" * 28))
    os.environ.setdefault("JWT_SECRET_KEY", os.environ["SECRET_KEY"])
    os.environ.setdefault("ENVIRONMENT", "development")

    from app.db.session import SessionLocal, init_db
    from app.models.tenant import Tenant

    init_db()
    db = SessionLocal()
    try:
        tenant = db.query(Tenant).filter(Tenant.domain == "dev.local").first()
        if not tenant:
            return None
        settings = json.loads(tenant.settings or "{}")
        brand = settings.get("brand") if isinstance(settings.get("brand"), dict) else {}
        site = brand.get("site_content")
        return site if isinstance(site, dict) else None
    finally:
        db.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="L-Pro publish gate E2E for dev.local")
    parser.add_argument("--skip-seed", action="store_true")
    args = parser.parse_args()

    issues: list[dict[str, str]] = []
    seed_ok, seed_log = True, "skipped"
    if not args.skip_seed:
        seed_ok, seed_log = _ensure_seed()
        if not seed_ok:
            issues.append({"severity": "P0", "check": "ensure_dev_sqlite", "detail": seed_log[:300]})

    site_content = _extract_site_content()
    if not site_content:
        issues.append({"severity": "P0", "check": "dev_local_site", "detail": "dev.local site_content missing"})
        gate = None
    else:
        from app.services.site_l_pro_service import validate_l_pro_publish_gate

        gate = validate_l_pro_publish_gate(site_content, environment="development")
        for item in gate.get("issues") or []:
            if isinstance(item, dict):
                issues.append(item)

    p0 = [i for i in issues if i.get("severity") == "P0"]
    ok = seed_ok and len(p0) == 0
    payload = {
        "ok": ok,
        "seed_ok": seed_ok,
        "p0": len(p0),
        "issues": issues,
        "gate_ready": bool(gate and gate.get("ready")),
        "site_content_gate": gate,
        "seed_log_tail": seed_log,
    }
    REPORT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    for item in issues:
        print(f"[{item['severity']}] {item['check']}: {item['detail']}")
    if ok:
        print(f"PASS E2E — see {REPORT}")
        return 0
    print(f"FAIL P0={len(p0)} — see {REPORT}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
