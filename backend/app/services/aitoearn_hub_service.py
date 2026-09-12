"""AiToEarn 能力 Hub — Publish / Engage / Create 对齐（Phase 4 复刻优化）。"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models.tenant import Tenant
from app.services.aitoearn_publish_adapter import (
    PLATFORM_TO_AITO_ACCOUNT_TYPE,
    aitoearn_enabled,
    fetch_accounts,
    fetch_post_comments,
    preflight_aitoearn,
    reply_comment,
    _safe_asyncio_run,
)
from app.services.publish_workers.tier_router import preflight_workers
from app.services.tenant_aitoearn_slot_service import get_tenant_aitoearn_account_ids


AITOEARN_PLATFORM_LABELS = sorted(PLATFORM_TO_AITO_ACCOUNT_TYPE.keys())


def build_aitoearn_capabilities(*, tenant: Tenant | None = None) -> dict[str, Any]:
    """对齐 AiToEarn 四大模块的就绪态（无 Key 时明确未配置，不假装可用）。"""
    workers = preflight_workers()
    aito = workers.get("workers", {}).get("aitoearn") or {}
    preflight = _safe_asyncio_run(preflight_aitoearn()) if aitoearn_enabled() else {
        "ready": False,
        "reason": "未配置 AITOEARN_API_KEY",
        "account_count": 0,
    }
    slot_ids = get_tenant_aitoearn_account_ids(tenant) if tenant else []
    return {
        "aitoearn_enabled": aitoearn_enabled(),
        "platform_count": len(AITOEARN_PLATFORM_LABELS),
        "platforms": AITOEARN_PLATFORM_LABELS,
        "modules": {
            "create": {
                "available": aitoearn_enabled(),
                "hint": "内容分发中心 AI 生成 + 多媒体工厂；素材库走 AiToEarn material API",
                "endpoint": "/api/v1/seo-matrix/generate",
            },
            "publish": {
                "available": bool(preflight.get("ready")) and bool(slot_ids or preflight.get("account_count")),
                "scheduled_publish": True,
                "hint": "视频分发 / Hermes 编排；支持 publishTime 定时",
                "endpoint": "/api/v1/publish/video/distribute",
            },
            "engage": {
                "available": aitoearn_enabled() and bool(slot_ids),
                "hint": "评论拉取 + AI 草稿 + AiToEarn 真回复（须平台回执）",
                "endpoint": "/api/v1/aitoearn/hub/engage/reply",
            },
            "analytics": {
                "available": aitoearn_enabled(),
                "hint": "跨平台数据看板",
                "endpoint": "/api/v1/cross-platform-dashboard/overview",
            },
        },
        "tenant_slot": {
            "assigned": bool(slot_ids),
            "account_count": len(slot_ids),
        },
        "workers": workers,
        "aitoearn_preflight": preflight,
    }


async def _pick_tenant_account(
    tenant: Tenant,
    *,
    platform: str = "douyin",
) -> str:
    """_pick_tenant_account。

    参数说明：
    :param tenant: 参数 tenant
    :param platform: 参数 platform
    :return: 返回处理结果。
    """
    from app.services.aitoearn_publish_adapter import account_type_for_platform_name, normalize_account_type
    allowed = set(get_tenant_aitoearn_account_ids(tenant))
    if not allowed:
        raise ValueError("租户未分配 AiToEarn 矩阵号")
    want = normalize_account_type(account_type_for_platform_name(platform) or platform)
    accounts = await fetch_accounts()
    for acc in accounts:
        aid = str(acc.get("accountId") or acc.get("id") or "")
        if aid not in allowed:
            continue
        atype = normalize_account_type(str(acc.get("accountType") or ""))
        if not want or atype == want:
            return aid
    if len(allowed) == 1:
        return next(iter(allowed))
    raise ValueError(f"本租户槽位无 {platform} 可用账号")


async def engage_reply_via_aitoearn(
    *,
    tenant: Tenant,
    account_id: str | None,
    comment_id: str,
    content: str,
    post_id: str = "",
) -> dict[str, Any]:
    """engage_reply_via_aitoearn。

    参数说明：
    :param tenant: 参数 tenant
    :param account_id: 参数 account_id
    :param comment_id: 参数 comment_id
    :param content: 参数 content
    :param post_id: 参数 post_id
    :return: 返回处理结果。
    """
    if not aitoearn_enabled():
        return {"ok": False, "error_code": "AITOEARN_NOT_CONFIGURED", "message": "未配置 AITOEARN_API_KEY"}
    aid = account_id
    if not aid:
        aid = await _pick_tenant_account(tenant, platform="douyin")
    body = await reply_comment(
        account_id=aid,
        comment_id=comment_id,
        content=content,
        post_id=post_id,
    )
    code = body.get("code")
    data = body.get("data") or {}
    msg_id = str(data.get("messageId") or data.get("commentId") or data.get("id") or "")
    if code not in (0, None, "0") and not body.get("success"):
        return {
            "ok": False,
            "error_code": "AITOEARN_REPLY_FAILED",
            "message": body.get("message") or "AiToEarn 回复失败",
            "raw": body,
        }
    return {
        "ok": True,
        "account_id": aid,
        "platform_message_id": msg_id or comment_id,
        "platform_receipt_id": msg_id or f"aitoearn-reply-{comment_id}",
        "raw": body,
    }


async def engage_list_comments(
    *,
    tenant: Tenant,
    post_id: str,
    platform: str = "douyin",
    account_id: str | None = None,
) -> list[dict[str, Any]]:
    """engage_list_comments。

    参数说明：
    :param tenant: 参数 tenant
    :param post_id: 参数 post_id
    :param platform: 参数 platform
    :param account_id: 参数 account_id
    :return: 返回处理结果。
    """
    if not aitoearn_enabled():
        return []
    aid = account_id or await _pick_tenant_account(tenant, platform=platform)
    return await fetch_post_comments(account_id=aid, post_id=post_id, platform=platform)
