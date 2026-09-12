#!/usr/bin/env python3
"""COMP-07 · 软著 60 页导出 vs 专利边界 — 自动化扫描（签字仍人类）"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPORT = ROOT / "docs/compliance/soft-copyright-file-export.json"
OUT = ROOT / "docs/compliance/comp-07-scope-scan-latest.json"

FORBIDDEN_PATTERNS = [
    (r"(^|/)_ref/", "第三方 _ref 目录"),
    (r"frontend/admin-vben/", "Vben fork 整库"),
    (r"node_modules/", "node_modules"),
    (r"\.min\.(js|css)$", "压缩产物"),
]

PATENT_CORE_HINTS = [
    "ai_invocation_service",
    "ai_traffic_provider_service",
]

WARN_IF_IN_SOFT_ONLY = [
    "plan_gate_service",
]


def main() -> int:
    if not EXPORT.is_file():
        print(f"Missing {EXPORT}", file=sys.stderr)
        return 1
    data = json.loads(EXPORT.read_text(encoding="utf-8"))
    files = data.get("backend_files", []) + data.get("frontend_files", [])
    violations: list[dict] = []
    warnings: list[dict] = []

    for rel in files:
        for pat, reason in FORBIDDEN_PATTERNS:
            if re.search(pat, rel.replace("\\", "/")):
                violations.append({"file": rel, "reason": reason, "pattern": pat})
        for hint in PATENT_CORE_HINTS:
            if hint in rel:
                warnings.append({"file": rel, "note": f"专利核心模块也在软著清单: {hint}"})

    report = {
        "total_files": len(files),
        "violations": violations,
        "warnings": warnings,
        "pass": len(violations) == 0,
        "recommendation": "PASS" if not violations else "FAIL — 从 soft-copyright-file-export.json 移除违规路径",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"pass": report["pass"], "violations": len(violations), "out": str(OUT)}, ensure_ascii=False))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
