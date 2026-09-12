#!/usr/bin/env python3
"""Print AI key status (no secrets). Used by run-g4-real-ai-verify.ps1."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

os.environ.setdefault("JWT_SECRET_KEY", "ai-key-check-" + ("x" * 20))
os.environ.setdefault("SECRET_KEY", os.environ["JWT_SECRET_KEY"])


def main() -> int:
    from app.db.session import SessionLocal
    from app.services.ai_key_probe import probe_ubrain_non_mock

    db = SessionLocal()
    try:
        st = probe_ubrain_non_mock(db)
    finally:
        db.close()
    print(json.dumps(st, ensure_ascii=False, indent=2, default=str))
    return 0 if st.get("g4_pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
