#!/usr/bin/env python3
"""B2B 旁路统一冒烟 — 8092–8097 + LibreTranslate 8098 状态探针。"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
VENV_PY = BACKEND / ".venv" / "Scripts" / "python.exe"
if not VENV_PY.is_file():
    VENV_PY = Path(sys.executable)

VERIFY_SCRIPTS = [
    "verify-ai-find-customer-sidecar.py",
    "verify-domain-email-extractor-sidecar.py",
    "verify-media-crawler-sidecar.py",
    "verify-linkedin-decision-maker-sidecar.py",
    "verify-customs-data-spider-sidecar.py",
    "verify-imap-inquiry-sidecar.py",
]


def _load_dev_env() -> None:
    dev_env = BACKEND / "config" / "dev" / ".env"
    if not dev_env.is_file():
        return
    for line in dev_env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = val


def _run_script(name: str, extra_args: list[str]) -> tuple[str, int, str]:
    script = ROOT / "scripts" / name
    if not script.is_file():
        return name, 2, "missing script"
    cmd = [str(VENV_PY), str(script), *extra_args]
    proc = subprocess.run(cmd, cwd=str(BACKEND), capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = (proc.stdout or "") + (proc.stderr or "")
    return name, proc.returncode, out[-2000:]


def _libretranslate_status() -> dict:
    _load_dev_env()
    if str(BACKEND) not in sys.path:
        sys.path.insert(0, str(BACKEND))
    os.environ.setdefault("SECRET_KEY", "verify-sidecar-" + ("x" * 24))
    os.environ.setdefault("JWT_SECRET_KEY", os.environ["SECRET_KEY"])
    os.environ.setdefault("ENVIRONMENT", "development")
    from app.services.cross_border.libretranslate_sidecar import libretranslate_sidecar_status

    return libretranslate_sidecar_status()


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify all B2B sidecars")
    parser.add_argument("--smoke", action="store_true", help="Run smoke_find on AI find customer")
    parser.add_argument("--json", action="store_true", help="Print JSON summary")
    args = parser.parse_args()

    _load_dev_env()
    results: list[dict] = []
    extra = ["--smoke-find"] if args.smoke else []

    for script in VERIFY_SCRIPTS:
        name, code, tail = _run_script(script, extra if script.startswith("verify-ai-find") else [])
        results.append({"script": name, "ok": code == 0, "exit_code": code, "tail": tail})

    lt = _libretranslate_status()
    lt_ok = lt.get("configured") is False or lt.get("healthy") is True
    results.append({"script": "libretranslate_sidecar", "ok": lt_ok, "status": lt})

    failed = [r for r in results if not r.get("ok")]
    summary = {
        "ok": len(failed) == 0,
        "passed": len(results) - len(failed),
        "failed": len(failed),
        "results": results,
    }

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        for row in results:
            mark = "OK" if row.get("ok") else "FAIL"
            print(f"[{mark}] {row.get('script')}")
        print(f"SUMMARY passed={summary['passed']} failed={summary['failed']}")

    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
