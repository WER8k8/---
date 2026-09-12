#!/usr/bin/env python3
"""PAT-02 · 代理机构交接文件清单（可 zip 打包）."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/pat-02-handoff-bundle-latest.json"

FILES = (
    "docs/专利/PAT-02-novelty-search-memo.md",
    "docs/专利/PAT-02-agency-handoff-checklist.md",
    "docs/专利/PAT-01-claims-code-mapping.md",
    "docs/专利/PAT-02-report-number.json",
    "docs/pat-02-handoff-validation-latest.json",
)


def main() -> int:
    manifest = []
    for rel in FILES:
        path = ROOT / rel
        manifest.append({"path": rel, "exists": path.is_file(), "bytes": path.stat().st_size if path.is_file() else 0})
    ok = all(x["exists"] for x in manifest)
    report = {"ok": ok, "task": "PAT-02-bundle", "files": manifest, "human_pending": "PM 发送代理 + 回收检索号"}
    REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
