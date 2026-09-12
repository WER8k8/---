#!/usr/bin/env python3
"""导出 FastAPI OpenAPI 快照供 BJ-03 gen-crud 使用。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from app.main import app  # noqa: E402

OUT = BACKEND / "openapi.json"


def main() -> None:
    spec = app.openapi()
    OUT.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
    paths = len(spec.get("paths", {}))
    print(json.dumps({"ok": True, "out": str(OUT.relative_to(ROOT)), "paths": paths}, indent=2))


if __name__ == "__main__":
    main()
