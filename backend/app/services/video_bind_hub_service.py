# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""视频发布绑定中枢 — 登录优丁后一次入口绑号（含 AiToEarn 同步）。"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models.content import Platform
from app.models.tenant import Tenant
from app.services.tenant_aitoearn_slot_service import (
    get_tenant_aitoearn_account_ids,
    sync_tenant_aitoearn_slot_accounts,
    tenant_aitoearn_slot_summary,
)
from app.services.aitoearn_publish_adapter import (
    PLATFORM_TO_AITO_ACCOUNT_TYPE,
    aitoearn_enabled,
    normalize_account_type,
    preflight_aitoearn,
)
from app.services.platform_account_service import list_active_accounts
from app.services.publish_capability_registry import video_publish_capability
from app.services.publish_dispatch_service import publisher_key_for_platform
from app.services.publish_workers.sau_worker import SAU_SUPPORTED, sau_bind_hint, sau_enabled
from app.services.publish_workers.tier_router import preflight_workers

AITO_BIND_URL = "https://aitoearn.cn"
AITO_ACCOUNT_BIND_HINT = "平台为每个租户分配独立 AiToEarn 矩阵号，代发更安全；无需客户自行登录 AiToEarn"

# canonical accountType → 优丁平台显示名
AITO_CANONICAL_TO_PLATFORM: dict[str, str] = {
    "douyin": "抖音",
    "kuaishou": "快手",
    "bilibili": "哔哩哔哩",
    "wxchannels": "微信视频号",
    "tiktok": "TikTok",
    "youtube": "YouTube",
    "xiaohongshu": "小红书",
    "facebook": "Facebook",
    "instagram": "Instagram",
    "threads": "Threads",
    "pinterest": "Pinterest",
}

VIDEO_PLATFORM_NAMES: frozenset[str] = frozenset(
    {
        "抖音",
        "快手",
        "哔哩哔哩",
        "微信视频号",
        "小红书",
        "YouTube",
        "TikTok",
        "LinkedIn",
        "Facebook",
        "Instagram",
        "X",
        "Pinterest",
        "Reddit",
        "Snapchat",
        "Threads",
    }
)


def _is_video_platform(p: Platform) -> bool:
    """_is_video_platform。

    参数说明：
    :param p: 参数 p
    :return: 返回处理结果。
    """
    ctype = (p.content_type or "").lower()
    if "video" in ctype:
        return True
    return p.name in VIDEO_PLATFORM_NAMES


def _account_by_platform_id(accounts, platform_id: str) -> dict[str, Any] | None:
    """_account_by_platform_id。

    参数说明：
    :param accounts: 参数 accounts
    :param platform_id: 参数 platform_id
    :return: 返回处理结果。
    """
    for acc in accounts:
        if str(acc.platform_id) == str(platform_id):
            return {
                "id": str(acc.id),
                "login_status": acc.login_status,
                "username": acc.username,
                "account_name": acc.account_name,
                "bound": acc.login_status in ("logged_in", "bound"),
            }
    return None


async def build_video_bind_hub(db: Session, *, tenant_id: str | None) -> dict[str, Any]:
    """租户视频绑号总览（发布前入口）。"""
    platforms = (
        db.query(Platform)
        .filter(Platform.is_active.is_(True))
        .order_by(Platform.region.desc(), Platform.name)
        .all()
    )
    video_rows = [p for p in platforms if _is_video_platform(p)]
    tenant_accounts = list_active_accounts(db, tenant_id=tenant_id) if tenant_id else []
    items: list[dict[str, Any]] = []
    bound_count = 0
    for p in video_rows:
        pub_key = publisher_key_for_platform(p)
        cap = video_publish_capability(platform_name=p.name, publisher_key=pub_key)
        acc = _account_by_platform_id(tenant_accounts, str(p.id))
        if acc and acc.get("bound"):
            bound_count += 1
        aito_type = PLATFORM_TO_AITO_ACCOUNT_TYPE.get(p.name)
        bind_via = (
            "aitoearn"
            if aito_type
            else ("oauth_token" if (p.region or "") == "global" else "cookie_or_password")
        )
        row: dict[str, Any] = {
            "platform_id": str(p.id),
            "platform_name": p.name,
            "region": p.region or "cn",
            "content_type": p.content_type,
            "base_url": p.base_url,
            "video_publish": cap,
            "account": acc,
            "bind_via": bind_via,
            "aitoearn_account_type": aito_type,
        }
        if p.name in SAU_SUPPORTED and sau_enabled():
            hint = sau_bind_hint(platform_name=p.name, tenant_id=tenant_id)
            if hint:
                row["sau_bind"] = hint
                if bind_via == "cookie_or_password":
                    row["bind_via"] = "sau_cookie"
        items.append(row)

    workers = preflight_workers()
    aito = await preflight_aitoearn()
    aito_accounts = aito.get("accounts") or []
    tenant_row = db.query(Tenant).filter(Tenant.id == tenant_id).first() if tenant_id else None
    slot_summary = tenant_aitoearn_slot_summary(db, tenant_row)
    tenant_aids = set(get_tenant_aitoearn_account_ids(tenant_row))
    tenant_aito_types = {
        str(a.get("canonical_type") or "")
        for a in aito_accounts
        if str(a.get("account_id") or "") in tenant_aids
    }
    for row in items:
        at = row.get("aitoearn_account_type")
        if tenant_aids and at and normalize_account_type(at) in tenant_aito_types:
            row["aitoearn_synced"] = True
            row["bind_via"] = "aitoearn_dedicated"
        else:
            row["aitoearn_synced"] = False

    return {
        "entry": "video_bind_hub",
        "tenant_id": tenant_id,
        "tenant_aitoearn_slot": slot_summary,
        "summary": {
            "video_platforms": len(items),
            "bound_local": bound_count,
            "unbound_local": max(len(items) - bound_count, 0),
            "aitoearn_enabled": aitoearn_enabled(),
            "aitoearn_account_count": len(tenant_aids) if tenant_aids else 0,
            "worker_ready": bool(workers.get("ready")),
        },
        "aitoearn": {
            "enabled": aitoearn_enabled(),
            "ready": bool(tenant_aids) and bool(aito.get("ready")),
            "bind_url": AITO_BIND_URL,
            "hint": slot_summary.get("customer_hint") or AITO_ACCOUNT_BIND_HINT,
            "mode": "dedicated_per_tenant",
            "tenant_account_ids": list(tenant_aids),
            "setup": aito.get("setup"),
            "reason": aito.get("reason") if not tenant_aids else None,
        },
        "workers": workers,
        "platforms": items,
        "quick_links": {
            "article_to_video": "/client/article-to-video",
            "publish_queue": "/client/queues/publish",
        },
    }


async def sync_aitoearn_accounts_to_tenant(db: Session, *, tenant_id: str) -> dict[str, Any]:
    """同步本租户独占 AiToEarn 槽位到 PlatformAccount（不拉整池）。"""
    return await sync_tenant_aitoearn_slot_accounts(db, tenant_id=tenant_id)
