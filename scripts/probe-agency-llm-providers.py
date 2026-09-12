#!/usr/bin/env python3
"""探测 Hermes agency-orchestrator LLM providers（本地/服务器通用）。"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.services.hermes.agency.llm_router import list_providers, provider_catalog_meta


def main() -> int:
    meta = provider_catalog_meta()
    rows = list_providers(probe=True)
    print("=== Hermes Agency LLM Providers ===")
    print(json.dumps(meta, ensure_ascii=False, indent=2))
    print()
    ok = 0
    for p in rows:
        avail = bool(p.get("available"))
        if avail:
            ok += 1
        mark = "OK  " if avail else "MISS"
        reason = p.get("reason") or ""
        extra = ""
        if p.get("command"):
            extra = f" cmd={p['command']}"
        if p.get("base_url"):
            extra = f" url={p['base_url']}"
        print(f"{mark}  {p['id']:16}  {reason}{extra}")
    print()
    print(f"available: {ok}/{len(rows)}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
