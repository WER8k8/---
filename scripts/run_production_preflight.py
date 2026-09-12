#!/usr/bin/env python3
"""生产上线预检（Sprint I）：路由 + 就绪检查 + 备份状态。"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
OUT = ROOT / "docs" / "production-preflight-latest.json"


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="生产上线预检")
    parser.add_argument(
        "--production",
        action="store_true",
        help="模拟生产检查（SQLite/缺平台数据会 fail）；默认本地 development",
    )
    args = parser.parse_args()

    env = os.environ.copy()
    env.setdefault("JWT_SECRET_KEY", "preflight-" + "x" * 32)
    # 默认本地 development；仅 --production 或显式 PREFLIGHT_ENVIRONMENT=production 时按生产
    preflight_env = "production" if args.production else "development"
    env["ENVIRONMENT"] = preflight_env
    os.environ["ENVIRONMENT"] = preflight_env
    if preflight_env == "development":
        env.setdefault("DATABASE_URL", "sqlite:///./youding_dev.db")
        env["DB_TYPE"] = "sqlite"
        env.setdefault("FRONTEND_URL", "http://127.0.0.1:5173")
        os.environ.setdefault("DATABASE_URL", env["DATABASE_URL"])
        os.environ["DB_TYPE"] = "sqlite"
        os.environ.setdefault("FRONTEND_URL", env["FRONTEND_URL"])
    # 主站商用 MVP 预检：PREFLIGHT_MVP_LAUNCH=1 或 MVP_LAUNCH=1
    if env.get("PREFLIGHT_MVP_LAUNCH", "").lower() in ("1", "true", "yes"):
        env.setdefault("MVP_LAUNCH", "1")
    env.setdefault("MVP_LAUNCH", env.get("MVP_LAUNCH", ""))
    os.environ.setdefault("MVP_LAUNCH", env.get("MVP_LAUNCH", ""))

    report: dict = {"generated_at": datetime.now(timezone.utc).isoformat(), "steps": []}

    p1 = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_mounted_routes.py")],
        cwd=str(ROOT),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    report["steps"].append(
        {
            "name": "check_mounted_routes",
            "ok": p1.returncode == 0,
            "detail": (p1.stdout or "") + (p1.stderr or ""),
        }
    )

    seed_ok = True
    seed_detail = ""
    if env.get("PREFLIGHT_SEED_PLATFORMS", "1").lower() in ("1", "true", "yes"):
        p_seed = subprocess.run(
            [sys.executable, str(BACKEND / "scripts" / "seed_platforms_full.py")],
            cwd=str(BACKEND),
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        seed_ok = p_seed.returncode == 0
        seed_detail = (p_seed.stdout or "") + (p_seed.stderr or "")
        report["steps"].append(
            {
                "name": "seed_platforms_full",
                "ok": seed_ok,
                "detail": seed_detail.strip() or "(no output)",
            }
        )

    sys.path.insert(0, str(BACKEND))
    os.environ.setdefault("JWT_SECRET_KEY", env["JWT_SECRET_KEY"])

    import app.models  # noqa: F401
    from app.core.config import settings

    settings.ENVIRONMENT = preflight_env
    if preflight_env == "development":
        settings.DATABASE_URL = env.get("DATABASE_URL", "sqlite:///./youding_dev.db")
    from app.core.sqlite_paths import resolve_sqlite_database_url

    if settings.DATABASE_URL.startswith("sqlite"):
        settings.DATABASE_URL = resolve_sqlite_database_url(settings.DATABASE_URL)
        env["DATABASE_URL"] = settings.DATABASE_URL
    from app.core.database import SessionLocal, rebind_engine

    rebind_engine(settings.DATABASE_URL)
    from app.services.production_readiness_service import (
        check_mounted_routes,
        run_readiness_checks,
    )
    from app.services.ops_backup_service import backup_status

    db = SessionLocal()
    try:
        readiness = run_readiness_checks(db)
        readiness.add(check_mounted_routes())
        report["readiness"] = readiness.to_dict()
    finally:
        db.close()

    report["backup"] = backup_status()
    report["preflight_environment"] = preflight_env
    report["ok"] = report["readiness"]["ready"] and all(s["ok"] for s in report["steps"])

    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    payload = json.dumps(report, ensure_ascii=False, indent=2)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    print(payload)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
