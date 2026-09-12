#!/usr/bin/env python3
"""COMP-02 严格品牌审查：租户可见面 + API 脱敏 + 内部残留分级。"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.services.hermes.brand_audit_service import FORBIDDEN_PATTERNS, audit_brand_leaks
from app.services.hermes.brand_guard import sanitize_public_data

# 租户可能调用的 API 前缀（响应经 BrandGuard 或应无禁词）
TENANT_API_PREFIXES = (
    "/api/v1/ubrain",
    "/api/v1/wangcai",
    "/api/v1/client",
    "/api/v1/bff/client",
    "/api/v1/app",
    "/api/v1/hermes/flywheel",
    "/api/v1/hermes/plugins",
)

# 仅超管/内部 — 允许出现研发代号，但不应出现在租户路由
INTERNAL_ONLY_MARKERS = (
    "backend/app/api/v1/routes/super_agent.py",
    "backend/app/api/v1/routes/hermes.py",
    "frontend/admin/src/views/admin/system",
)


def _scan_tenant_api_source_leaks(max_findings: int = 30) -> list[dict]:
    """扫描租户 API 路由源文件中可能直达用户的 message 字符串。"""
    routes_dir = ROOT / "backend" / "app" / "api" / "v1" / "routes"
    hits: list[dict] = []
    tenant_files = [
        "ubrain.py",
        "ubrain_commercial_os.py",
        "client.py",
        "app_bff.py",
        "wangcai.py",
    ]
    for name in tenant_files:
        path = routes_dir / name
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for i, line in enumerate(text.splitlines(), 1):
            if "message=" not in line and "error_response" not in line:
                continue
            for pattern, label in FORBIDDEN_PATTERNS:
                if pattern.search(line):
                    hits.append(
                        {
                            "severity": "P1",
                            "file": f"backend/app/api/v1/routes/{name}",
                            "line": i,
                            "term": label,
                            "excerpt": line.strip()[:120],
                        }
                    )
                    break
            if len(hits) >= max_findings:
                return hits
    return hits


def _test_brand_guard_samples() -> list[dict]:
    failures: list[dict] = []
    sample = {
        "version": "v1-accio",
        "accio_core": [{"accio_analog": "AccioWork 找客"}],
        "accio_actions": [{"title": "DeerFlow 研究"}],
        "reply": "由 UBrain 和 AccioWork 驱动",
    }
    out = sanitize_public_data(sample)
    blob = json.dumps(out, ensure_ascii=False)
    if re.search(r'"accio[_"]', blob, re.I):
        failures.append({"check": "no_accio_keys_in_output", "output": out})
    for pattern, label in FORBIDDEN_PATTERNS:
        if pattern.search(blob):
            failures.append({"check": f"forbidden_{label}", "output": out})
    return failures


def main() -> int:
    ui = audit_brand_leaks(ROOT)
    api_hits = _scan_tenant_api_source_leaks()
    guard_fail = _test_brand_guard_samples()

    report = {
        "ok": ui["ok"] and not api_hits and not guard_fail,
        "customer_ui": ui,
        "tenant_api_message_leaks": api_hits,
        "brand_guard_self_test_failures": guard_fail,
        "internal_note": (
            "超管页 / docs / 内部注释中的 Hermes·DeerFlow 不计入 FAIL；"
            "租户可见面零 Accio·AccioWork·阿里对标名。"
        ),
        "production_checklist": [
            "ENVIRONMENT=production 且 DEBUG=false（/docs 不暴露 OpenAPI 标签）",
            "BrandGuardResponseMiddleware 已挂载",
            "FEISHU_WEBHOOK 配告警，不对外宣传 Accio/阿里同款",
            "powershell -File scripts/brand-guard-audit.ps1  exit 0",
        ],
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
