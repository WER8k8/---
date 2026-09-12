#!/usr/bin/env python3
"""演示验收一键脚本（Sprint G）：路由检查 → 5+5 seed → B-07 母版发布冒烟。"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
OUT = ROOT / "docs" / "demo-acceptance-latest.json"


def _run(cmd: list[str], cwd: Path, env: dict | None = None) -> tuple[int, str]:
    p = subprocess.run(
        cmd,
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    out = (p.stdout or "") + (p.stderr or "")
    return p.returncode, out.strip()


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    env = os.environ.copy()
    env.setdefault("JWT_SECRET_KEY", "demo-accept-" + "x" * 32)
    env["DEMO_USE_PRODUCTION_DB"] = "0"
    env["DATABASE_URL"] = "sqlite:///./youding_dev.db"
    env["DB_TYPE"] = "sqlite"
    env.setdefault("ENVIRONMENT", "development")
    env.setdefault("REDIS_ENABLED", "false")

    report: dict = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "steps": [],
        "ok": False,
    }

    code, out = _run(
        [sys.executable, str(ROOT / "scripts" / "check_mounted_routes.py")],
        ROOT,
        env,
    )
    report["steps"].append({"name": "check_mounted_routes", "ok": code == 0, "detail": out[-500:]})

    b7_env = env.copy()
    b7_env.pop("DATABASE_URL", None)
    b7_env.pop("DB_TYPE", None)
    b7_env["DEMO_USE_PRODUCTION_DB"] = "0"
    demo_db = BACKEND / "data" / "demo_acceptance.db"
    if demo_db.is_file():
        demo_db.unlink()
    code, out = _run(
        [sys.executable, str(BACKEND / "scripts" / "b7_pilot_acceptance.py")],
        BACKEND,
        b7_env,
    )
    report["steps"].append({"name": "b7_pilot_acceptance", "ok": code == 0, "detail": out[-800:]})

    b7_path = ROOT / "docs" / "b7-pilot-acceptance-result.json"
    if b7_path.is_file():
        report["b7"] = json.loads(b7_path.read_text(encoding="utf-8"))

    report["ok"] = all(s["ok"] for s in report["steps"])
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
