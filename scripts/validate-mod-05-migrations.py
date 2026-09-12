#!/usr/bin/env python3
"""MOD-05 · 校验 alembic 025/026 迁移文件存在且 revision 一致."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSIONS = ROOT / "backend/alembic/versions"
REPORT = ROOT / "docs/mod-05-migration-check-latest.json"

REQUIRED: dict[str, str] = {
    "025_ubrain_accio_sales": "025_ubrain_accio_sales.py",
    "026_ubrain_commercial_os": "026_ubrain_commercial_os.py",
}


def revision_id(path: Path) -> str | None:
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        m = re.match(r"""^revision\s*=\s*['"]([^'"]+)['"]""", line.strip())
        if m:
            return m.group(1)
    return None


def main() -> int:
    found: dict[str, str | None] = {k: None for k in REQUIRED}
    for rev, filename in REQUIRED.items():
        path = VERSIONS / filename
        if path.is_file() and revision_id(path) == rev:
            found[rev] = str(path.relative_to(ROOT))

    ok = all(found.values())
    report = {"ok": ok, "task": "MOD-05", "revisions": found, "versions_dir": str(VERSIONS.relative_to(ROOT))}
    REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
