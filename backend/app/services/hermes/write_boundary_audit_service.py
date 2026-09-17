# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""ARCH-03：Hermes 写库边界静态审计（只读扫描）。"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


def _repo_root() -> Path:
    """_repo_root。
    :return: 返回处理结果。
    """
    return Path(__file__).resolve().parents[4]


def _read(rel: str) -> str:
    """_read。

    参数说明：
    :param rel: 参数 rel
    :return: 返回处理结果。
    """
    path = _repo_root() / rel.replace("/", "\\")
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def _scan_tenant_routes_import_ops() -> list[dict[str, Any]]:
    """_scan_tenant_routes_import_ops。
    :return: 返回处理结果。
    """
    violations: list[dict[str, Any]] = []
    api_dir = _repo_root() / "backend" / "app" / "api"
    forbidden = ("run_full_ops_cycle", "run_tech_radar_cycle")
    for py in api_dir.rglob("*.py"):
        rel = str(py.relative_to(_repo_root())).replace("\\", "/")
        if "/hermes" in rel or "/ops_jobs" in rel or "/super_admin" in rel:
            continue
        text = py.read_text(encoding="utf-8", errors="ignore")
        for token in forbidden:
            if token in text:
                violations.append(
                    {
                        "rule": "tenant_api_no_ops_autopilot",
                        "file": rel,
                        "detail": f"含 {token}",
                    }
                )
                break
    return violations


def _scan_hermes_ops_gated() -> list[dict[str, Any]]:
    """_scan_hermes_ops_gated。
    :return: 返回处理结果。
    """
    text = _read("backend/app/api/v1/routes/hermes.py")
    if not text:
        return [{"rule": "hermes_routes_missing", "file": "hermes.py", "detail": "文件不存在"}]
    # 外部系统回调：独立 webhook 密钥/HMAC，不走 JWT _ops_gate
    webhook_exempt = frozenset({"hermes_worldfirst_survival_webhook"})
    violations: list[dict[str, Any]] = []
    blocks = re.split(r"(?=@router\.(get|post|put|delete|patch))", text)
    for block in blocks:
        if not block.strip().startswith("@router"):
            continue
        if '"/ops/' not in block and "'/ops/" not in block:
            continue
        name_m = re.search(r"def (hermes_\w+)", block)
        if not name_m:
            continue
        if name_m.group(1) in webhook_exempt:
            continue
        if "_ops_gate(current_user)" not in block:
            violations.append(
                {
                    "rule": "hermes_ops_requires_gate",
                    "file": "backend/app/api/v1/routes/hermes.py",
                    "detail": f"{name_m.group(1)} 缺少 _ops_gate",
                }
            )
    return violations


def _scan_brand_guard_coverage() -> list[dict[str, Any]]:
    """_scan_brand_guard_coverage。
    :return: 返回处理结果。
    """
    text = _read("backend/app/core/brand_guard_middleware.py")
    required = ("/api/v1/ubrain", "/api/v1/client", "/api/v1/bff/client")
    missing = [p for p in required if p not in text]
    if missing:
        return [
            {
                "rule": "brand_guard_prefixes",
                "file": "backend/app/core/brand_guard_middleware.py",
                "detail": f"缺少前缀: {', '.join(missing)}",
            }
        ]
    return []


def audit_write_boundaries() -> dict[str, Any]:
    """audit_write_boundaries。
    :return: 返回处理结果。
    """
    checks: list[dict[str, Any]] = []
    all_violations: list[dict[str, Any]] = []
    for rule_id, fn in (
        ("tenant_api_no_ops_autopilot", _scan_tenant_routes_import_ops),
        ("hermes_ops_requires_gate", _scan_hermes_ops_gated),
        ("brand_guard_prefixes", _scan_brand_guard_coverage),
    ):
        found = fn()
        checks.append({"id": rule_id, "violations": len(found), "ok": len(found) == 0})
        all_violations.extend(found)

    return {
        "ok": len(all_violations) == 0,
        "violations_count": len(all_violations),
        "violations": all_violations[:40],
        "checks": checks,
        "constitution": "docs/HERMES-FLYWHEEL-WRITE-CONSTITUTION.md",
    }
