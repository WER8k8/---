# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""租户 AiToEarn 槽位 — 一客户一组矩阵号，与池内其他租户隔离。"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.system_config import SystemConfig
from app.models.tenant import Tenant

BUNDLES_CONFIG_KEY = "aitoearn_tenant_bundles"
SLOT_SETTINGS_KEY = "aitoearn_slot"


def _utcnow() -> datetime:
    """_utcnow。
    :return: 返回处理结果。
    """
    return datetime.now(timezone.utc)


def _safe_settings(raw: str | None) -> dict[str, Any]:
    """_safe_settings。

    参数说明：
    :param raw: 参数 raw
    :return: 返回处理结果。
    """
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}


def _load_bundles_config(db: Session) -> list[dict[str, Any]]:
    """_load_bundles_config。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    row = db.query(SystemConfig).filter(SystemConfig.key == BUNDLES_CONFIG_KEY).first()
    if not row or not row.value:
        return []
    try:
        data = json.loads(row.value)
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def iter_all_assigned_account_ids(db: Session) -> set[str]:
    """全库已分配给租户的 AiToEarn account_id（独占）。"""
    assigned: set[str] = set()
    for tenant in db.query(Tenant).filter(Tenant.is_active.is_(True)).all():
        slot = get_tenant_aitoearn_slot(tenant)
        if not slot:
            continue
        for aid in slot.get("account_ids") or []:
            if aid:
                assigned.add(str(aid))
    return assigned


def get_tenant_aitoearn_slot(tenant: Tenant | None) -> dict[str, Any] | None:
    """get_tenant_aitoearn_slot。

    参数说明：
    :param tenant: 参数 tenant
    :return: 返回处理结果。
    """
    if not tenant:
        return None
    slot = _safe_settings(tenant.settings).get(SLOT_SETTINGS_KEY)
    return slot if isinstance(slot, dict) else None


def get_tenant_aitoearn_account_ids(tenant: Tenant | None) -> list[str]:
    """get_tenant_aitoearn_account_ids。

    参数说明：
    :param tenant: 参数 tenant
    :return: 返回处理结果。
    """
    slot = get_tenant_aitoearn_slot(tenant)
    if not slot:
        return []
    return [str(x) for x in (slot.get("account_ids") or []) if x]


def _persist_tenant_slot(db: Session, tenant: Tenant, slot: dict[str, Any]) -> None:
    """_persist_tenant_slot。

    参数说明：
    :param db: 参数 db
    :param tenant: 参数 tenant
    :param slot: 参数 slot
    :return: 返回处理结果。
    """
    settings = _safe_settings(tenant.settings)
    settings[SLOT_SETTINGS_KEY] = slot
    tenant.settings = json.dumps(settings, ensure_ascii=False)
    db.add(tenant)
    db.flush()


def assign_aitoearn_accounts_to_tenant(
    db: Session,
    *,
    tenant_id: str,
    account_ids: list[str],
    bundle_id: str | None = None,
    label: str | None = None,
) -> dict[str, Any]:
    """超管/运维：将一组 AiToEarn 创作者账号独占分配给租户（通常对应一个 AiToEarn 登录）。"""
    ids = [str(x).strip() for x in account_ids if str(x).strip()]
    if not ids:
        return {"ok": False, "error": "account_ids 不能为空"}

    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        return {"ok": False, "error": "tenant_not_found"}

    assigned_global = iter_all_assigned_account_ids(db)
    current = set(get_tenant_aitoearn_account_ids(tenant))
    conflict = [aid for aid in ids if aid in assigned_global and aid not in current]
    if conflict:
        return {
            "ok": False,
            "error": f"以下账号已分配给其他租户: {', '.join(conflict[:5])}",
        }

    slot = {
        "slot_id": str(uuid.uuid4()),
        "bundle_id": bundle_id or f"manual-{ids[0][:8]}",
        "label": label or f"{tenant.name[:20]} · 专属矩阵",
        "account_ids": ids,
        "assigned_at": _utcnow().isoformat(),
        "status": "active",
        "isolation": "one_tenant_one_aitoearn_login",
    }
    _persist_tenant_slot(db, tenant, slot)
    db.commit()
    return {"ok": True, "slot": slot}


async def list_unassigned_aitoearn_pool(db: Session) -> dict[str, Any]:
    """列出 AiToEarn 池中尚未分配给任何租户的账号。"""
    from app.services.aitoearn_publish_adapter import aitoearn_enabled, preflight_aitoearn
    if not aitoearn_enabled():
        return {"ok": False, "error": "AITOEARN_API_KEY 未配置", "accounts": []}

    assigned = iter_all_assigned_account_ids(db)
    preflight = await preflight_aitoearn()
    pool: list[dict[str, Any]] = []
    for row in preflight.get("accounts") or []:
        aid = str(row.get("account_id") or "")
        if not aid or aid in assigned:
            continue
        pool.append(
            {
                "account_id": aid,
                "platform": row.get("canonical_type") or row.get("account_type") or "",
                "nickname": row.get("nickname") or row.get("name") or aid[:12],
            }
        )
    return {"ok": True, "accounts": pool, "total": len(pool)}


def auto_assign_aitoearn_slot_for_tenant(db: Session, tenant: Tenant) -> dict[str, Any]:
    """
    开户时自动分配：优先系统配置中的未占用 bundle；否则分配单个未占用 account_id。
    一租户一组号，避免多客户共用一个 AiToEarn 登录导致频控/封号。
    """
    if get_tenant_aitoearn_account_ids(tenant):
        return {"ok": True, "skipped": True, "reason": "已有槽位"}

    assigned = iter_all_assigned_account_ids(db)
    for bundle in _load_bundles_config(db):
        bundle_ids = [str(x) for x in (bundle.get("account_ids") or []) if x]
        if not bundle_ids:
            continue
        if any(aid in assigned for aid in bundle_ids):
            continue
        return assign_aitoearn_accounts_to_tenant(
            db,
            tenant_id=str(tenant.id),
            account_ids=bundle_ids,
            bundle_id=str(bundle.get("bundle_id") or bundle.get("id") or ""),
            label=str(bundle.get("label") or ""),
        )

    try:
        from app.services.aitoearn_publish_adapter import preflight_aitoearn_sync
        preflight = preflight_aitoearn_sync()
        pool = preflight.get("accounts") or []
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:200], "deferred": True}

    for row in pool:
        aid = str(row.get("account_id") or "")
        if aid and aid not in assigned:
            return assign_aitoearn_accounts_to_tenant(
                db,
                tenant_id=str(tenant.id),
                account_ids=[aid],
                bundle_id=f"auto-{aid[:8]}",
                label=f"{tenant.name[:20]} · 单号矩阵",
            )

    return {
        "ok": False,
        "error": "AiToEarn 池无可用未分配账号，请联系运营分配",
        "deferred": True,
    }


def tenant_aitoearn_slot_summary(db: Session, tenant: Tenant | None) -> dict[str, Any]:
    """tenant_aitoearn_slot_summary。

    参数说明：
    :param db: 参数 db
    :param tenant: 参数 tenant
    :return: 返回处理结果。
    """
    slot = get_tenant_aitoearn_slot(tenant)
    ids = get_tenant_aitoearn_account_ids(tenant)
    return {
        "assigned": bool(ids),
        "account_count": len(ids),
        "account_ids": ids,
        "slot": slot,
        "mode": "dedicated_per_tenant",
        "customer_hint": (
            "平台已为您的租户分配专属 AiToEarn 代发矩阵号，无需自行登录 AiToEarn。"
            if ids
            else "代发矩阵号待运营分配，分配完成后即可视频外发。"
        ),
    }


async def sync_tenant_aitoearn_slot_accounts(db: Session, *, tenant_id: str) -> dict[str, Any]:
    """将本租户独占槽位内的 AiToEarn 账号同步为 PlatformAccount（不拉整池）。"""
    from app.services.aitoearn_publish_adapter import aitoearn_enabled, preflight_aitoearn
    from app.services.platform_account_service import upsert_bound_account
    from app.services.platform_catalog import resolve_or_create_platform_by_name
    from app.services.video_bind_hub_service import (
        AITO_BIND_URL,
        AITO_CANONICAL_TO_PLATFORM,
    )
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        return {"ok": False, "error": "tenant_not_found"}

    ids = set(get_tenant_aitoearn_account_ids(tenant))
    if not ids:
        return {
            "ok": False,
            "error": "本租户尚未分配 AiToEarn 矩阵号，请联系运营",
            "bind_url": AITO_BIND_URL,
        }
    if not aitoearn_enabled():
        return {"ok": False, "error": "未配置 AITOEARN_API_KEY"}

    preflight = await preflight_aitoearn()
    accounts = [a for a in (preflight.get("accounts") or []) if str(a.get("account_id") or "") in ids]
    if not accounts:
        return {
            "ok": False,
            "error": "槽位账号在 AiToEarn 侧不可用，请运维核对",
            "bind_url": AITO_BIND_URL,
        }

    synced: list[str] = []
    for acc in accounts:
        canonical = str(acc.get("canonical_type") or "")
        account_id = str(acc.get("account_id") or "")
        platform_name = AITO_CANONICAL_TO_PLATFORM.get(canonical)
        if not platform_name or not account_id:
            continue
        region = "global" if platform_name in {"YouTube", "TikTok", "Facebook", "Instagram"} else "cn"
        ctype = "long_video" if platform_name == "YouTube" else "short_video"
        platform = resolve_or_create_platform_by_name(
            db, platform_name, region=region, content_type=ctype
        )
        payload = {
            "username": f"aitoearn:{account_id[:12]}",
            "account_name": f"{platform_name} · 专属矩阵",
            "token_data": {
                "source": "aitoearn",
                "account_id": account_id,
                "account_type": canonical,
                "tenant_dedicated": True,
            },
            "configs": {
                "aitoearn_account_id": account_id,
                "aitoearn_account_type": canonical,
            },
        }
        upsert_bound_account(db, tenant_id=tenant_id, platform=platform, payload=payload)
        synced.append(platform_name)

    db.commit()
    return {
        "ok": bool(synced),
        "synced": synced,
        "message": f"已同步专属矩阵 {len(synced)} 个平台" if synced else "无可同步平台",
    }
