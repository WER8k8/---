#!/usr/bin/env python3
"""同步人类签字记录 → mod-08-owner-blockers.json（只升不降）."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BLOCKERS = ROOT / "docs/compliance/mod-08-owner-blockers.json"
BJ01 = ROOT / "docs/bj-01-saas-signoff-record.json"
REPORT = ROOT / "docs/mod-08-blockers-sync-latest.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.is_file() else {}


def main() -> int:
    blockers = _load(BLOCKERS)
    items = {i["id"]: i for i in blockers.get("items", [])}
    synced: list[str] = []

    bj = _load(BJ01)
    if bj.get("signed_by") and "saas-bj01-signoff" in items and not items["saas-bj01-signoff"].get("done"):
        items["saas-bj01-signoff"]["done"] = True
        items["saas-bj01-signoff"]["completed_at"] = bj.get("signed_at") or datetime.now(timezone.utc).isoformat()
        synced.append("saas-bj01-signoff")

    blockers["items"] = list(items.values())
    blockers["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    BLOCKERS.write_text(json.dumps(blockers, indent=2, ensure_ascii=False), encoding="utf-8")

    out = {"ok": True, "task": "MOD-08-sync", "synced": synced, "owner_pending": [k for k, v in items.items() if not v.get("done")]}
    REPORT.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
