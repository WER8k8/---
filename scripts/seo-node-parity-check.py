#!/usr/bin/env python3
"""T-NODE-1：seo-backend 与 FastAPI 矩阵能力对照（只读）。"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEO_NODE = ROOT / "seo-backend" / "src"
FASTAPI_MATRIX = ROOT / "backend" / "app" / "api" / "v1" / "routes" / "seo_matrix.py"

CAPABILITIES = [
    ("regions", "省市区", "districts"),
    ("keywords", "关键词", "keywords"),
    ("content", "内容生成", "content"),
    ("publish", "发布任务", "publish"),
    ("platforms", "平台账号", "platform"),
    ("inclusion", "收录监控", "inclusion"),
    ("risk", "风控", "risk"),
]


def _fastapi_hits() -> dict[str, bool]:
    text = FASTAPI_MATRIX.read_text(encoding="utf-8", errors="ignore").lower()
    return {key: token in text for key, _label, token in CAPABILITIES}


def _node_hits() -> dict[str, bool]:
    hits = {key: False for key, _, _ in CAPABILITIES}
    if not SEO_NODE.exists():
        return hits
    for py in SEO_NODE.rglob("*.js"):
        try:
            body = py.read_text(encoding="utf-8", errors="ignore").lower()
        except OSError:
            continue
        for key, _label, token in CAPABILITIES:
            if token in body or key in body:
                hits[key] = True
    return hits


def main() -> None:
    fa = _fastapi_hits()
    node = _node_hits()
    rows = []
    for key, label, _token in CAPABILITIES:
        rows.append(
            {
                "capability": key,
                "label": label,
                "fastapi_seo_matrix": fa.get(key, False),
                "seo_backend_legacy": node.get(key, False),
                "parity": fa.get(key, False) and node.get(key, False),
            }
        )
    covered = sum(1 for r in rows if r["fastapi_seo_matrix"])
    report = {
        "fastapi_primary": True,
        "node_readonly_policy": "docs/adr/seo-backend-vs-fastapi.md",
        "capabilities_covered_in_fastapi": f"{covered}/{len(rows)}",
        "rows": rows,
    }
    out = ROOT / "docs" / "seo-node-parity-latest.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
