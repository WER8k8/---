# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""GW-S-MAT-01 — 矩阵真发 OAuth 绑定 SLA 门禁。"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models.content import Platform, PlatformAccount
from app.services.publish_capability_registry import LIVE_PUBLISHER_KEYS, publish_block_reason
from app.services.ubrain.matrix_publish_service import _match_platform

OAUTH_READY_STATUSES = frozenset({"logged_in", "active", "connected", "authorized"})


def _account_oauth_ready(account: PlatformAccount | None) -> bool:
    """实现 账户oauthready 的功能。
    
    :param account: 参数 account（类型: PlatformAccount | None）
    :return: 返回 bool 结果
    """
    if account is None or not account.is_active:
        return False
    status = str(account.login_status or "").strip().lower()
    if status in OAUTH_READY_STATUSES:
        return True
    if account.token_data or account.cookie_data:
        return True
    return False


def check_platform_oauth_gate(
    db: Session,
    *,
    tenant_id: str,
    platform_name: str,
    content: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """单平台 OAuth + Worker 双门禁。"""
    content = content or {}
    plat = _match_platform(db, platform_name)
    worker_block = publish_block_reason(platform_name=platform_name, content=content)
    if plat is None:
        return {
            "platform_name": platform_name,
            "matched": False,
            "oauth_ready": False,
            "selectable": False,
            "blocked": True,
            "reason": "platform_not_in_catalog",
            "gw_task": "GW-S-MAT-01",
        }

    account = (
        db.query(PlatformAccount)
        .filter(
            PlatformAccount.tenant_id == tenant_id,
            PlatformAccount.platform_id == plat.id,
            PlatformAccount.is_active.is_(True),
        )
        .first()
    )
    oauth_ready = _account_oauth_ready(account)
    key = plat.name.strip().lower()
    requires_oauth = key in LIVE_PUBLISHER_KEYS or plat.platform_type in ("social", "video", "blog")
    blocked_reason = worker_block
    if requires_oauth and not oauth_ready:
        blocked_reason = blocked_reason or f"{plat.name} 未绑定 OAuth（login_status 须为 logged_in 或已存 token）"

    return {
        "platform_id": str(plat.id),
        "platform_name": plat.name,
        "matched": True,
        "requires_oauth": requires_oauth,
        "oauth_ready": oauth_ready,
        "login_status": account.login_status if account else None,
        "account_id": str(account.id) if account else None,
        "selectable": blocked_reason is None,
        "blocked": blocked_reason is not None,
        "reason": blocked_reason,
        "gw_task": "GW-S-MAT-01",
    }


def matrix_oauth_gate_report(
    db: Session,
    *,
    tenant_id: str,
    platform_names: list[str] | None = None,
) -> dict[str, Any]:
    """实现 matrixoauthgate报告 的功能。
    
    :param db: 参数 db（类型: Session）
    :param tenant_id: 参数 tenant_id（类型: str）
    :param platform_names: 参数 platform_names（类型: list[str] | None）
    :return: 返回 dict[str, Any] 结果
    """
    from app.services.ubrain.matrix_publish_service import default_platform_names
    names = platform_names or default_platform_names()
    checks = [
        check_platform_oauth_gate(db, tenant_id=tenant_id, platform_name=name) for name in names
    ]
    ready = sum(1 for c in checks if c.get("selectable"))
    return {
        "tenant_id": tenant_id,
        "platforms_checked": len(checks),
        "platforms_ready": ready,
        "all_ready": ready == len(checks) and len(checks) > 0,
        "checks": checks,
        "gw_task": "GW-S-MAT-01",
        "sla_note": "真发前须 OAuth 绑定 + Worker 预检双绿；禁止无账号占位假成功",
    }


def assert_matrix_oauth_before_publish(
    db: Session,
    *,
    tenant_id: str,
    platform_names: list[str],
) -> dict[str, Any] | None:
    """返回 blocked dict 或 None 表示通过。"""
    blocked: list[dict[str, Any]] = []
    for name in platform_names:
        gate = check_platform_oauth_gate(db, tenant_id=tenant_id, platform_name=name)
        if gate.get("blocked"):
            blocked.append(gate)
    if not blocked:
        return None
    return {
        "status": "blocked",
        "error_code": "MATRIX_OAUTH_GATE",
        "blocked": True,
        "reason": "部分平台未通过 OAuth/Worker 门禁",
        "platform_gates": blocked,
        "gw_task": "GW-S-MAT-01",
        "next_step": "在 SEO 矩阵绑定平台 OAuth 后重试；Stub 平台不得宣称已发布",
    }
