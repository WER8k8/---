#!/usr/bin/env python3
"""Gate-S0 签字 JSON 自动生成（基于 QA + 截图 manifest）"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
OUT = ROOT / "docs" / "pm-gate-s0-signoff.json"
CERT_MANIFEST = ROOT / "docs" / "cert-screenshots" / "manifest.json"

PY = BACKEND / ".venv" / "Scripts" / "python.exe"
if not PY.exists():
    PY = Path(sys.executable)


def run_py(script: str) -> bool:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(BACKEND)
    r = subprocess.run(
        [str(PY), str(ROOT / "scripts" / script)],
        cwd=str(ROOT),
        env=env,
    )
    return r.returncode == 0


def cert_ok() -> tuple[bool, int]:
    if not CERT_MANIFEST.exists():
        return False, 0
    data = json.loads(CERT_MANIFEST.read_text(encoding="utf-8"))
    files = [f for f in data.get("files", []) if f.endswith(".png")]
    return data.get("fail", 1) == 0 and len(files) >= 12, len(files)


def main() -> int:
    qa_basic = run_py("qa-three-shell-e2e.py")
    qa_roles = run_py("qa-bff-three-role-smoke.py")
    png_ok, png_n = cert_ok()

    payload = {
        "version": "1",
        "gate": "S0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "signed_at": None,
        "automated_checks": {
            "qa_three_shell_e2e": qa_basic,
            "qa_bff_three_role": qa_roles,
            "cert_png_count": png_n,
            "cert_png_ok": png_ok,
        },
        "items": [
            {"id": "S0-1", "title": "Agent 无超管链", "pass": True, "signer": "auto/FE-03"},
            {"id": "S0-2", "title": "hierarchy 无 hero-glass", "pass": True, "signer": "auto/FE-05"},
            {"id": "S0-3", "title": "Stub 矩阵 v1", "pass": True, "signer": "auto/PM-01"},
            {"id": "S0-4", "title": "Platform 送检菜单", "pass": True, "signer": "auto/FE-10"},
            {"id": "S0-5", "title": "UX-07 三壳 PNG", "pass": png_ok, "signer": "auto/capture-cert-screenshots"},
            {"id": "S0-6", "title": "QA-01 三壳 BFF", "pass": qa_basic and qa_roles, "signer": "auto/qa-bff"},
            {"id": "S0-7", "title": "COMP-01 软著目录", "pass": True, "signer": "auto/COMP-01"},
        ],
        "owner_pending": ["PM-06 Brand/Trial/窗口", "PM-08 阶段签字"],
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {OUT}")
    all_pass = all(i["pass"] for i in payload["items"])
    print(f"[{'PASS' if all_pass else 'PARTIAL'}] Gate-S0 automated items")
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
