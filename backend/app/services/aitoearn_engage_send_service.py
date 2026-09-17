# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""社媒互动 — 批准后经 AiToEarn 真发回复（禁止无回执假成功）。"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models.tenant import Tenant
from app.services import social_interaction_service as svc
from app.services.aitoearn_hub_service import engage_reply_via_aitoearn
from app.services.aitoearn_publish_adapter import _safe_asyncio_run


async def approve_and_send_via_aitoearn(
    db: Session,
    *,
    interaction_id: str,
    tenant: Tenant,
    final_reply: str | None = None,
) -> dict[str, Any]:
    """approve_and_send_via_aitoearn。

    参数说明：
    :param db: 参数 db
    :param interaction_id: 参数 interaction_id
    :param tenant: 参数 tenant
    :param final_reply: 参数 final_reply
    :return: 返回处理结果。
    """
    row = svc.approve_draft(db, interaction_id, final_reply=final_reply)
    comment_id = str(row.get("platform_comment_id") or "")
    post_id = str(row.get("platform_post_id") or "")
    text = str(row.get("final_reply") or "")
    if not comment_id or not text:
        raise ValueError("缺少评论 ID 或回复正文")

    send = await engage_reply_via_aitoearn(
        tenant=tenant,
        account_id=None,
        comment_id=comment_id,
        content=text,
        post_id=post_id,
    )
    if not send.get("ok"):
        svc.mark_failed(
            db,
            interaction_id,
            error_code=str(send.get("error_code") or "AITOEARN_SEND_FAILED"),
            error_message=str(send.get("message") or "AiToEarn 发送失败")[:500],
        )
        raise ValueError(send.get("message") or "AiToEarn 发送失败")

    return svc.mark_sent(
        db,
        interaction_id,
        platform_receipt_id=str(send["platform_receipt_id"]),
        platform_message_id=str(send.get("platform_message_id") or ""),
        extra={"via": "aitoearn", "account_id": send.get("account_id")},
    )


def approve_and_send_via_aitoearn_sync(
    db: Session,
    *,
    interaction_id: str,
    tenant: Tenant,
    final_reply: str | None = None,
) -> dict[str, Any]:
    """approve_and_send_via_aitoearn_sync。

    参数说明：
    :param db: 参数 db
    :param interaction_id: 参数 interaction_id
    :param tenant: 参数 tenant
    :param final_reply: 参数 final_reply
    :return: 返回处理结果。
    """
    return _safe_asyncio_run(
        approve_and_send_via_aitoearn(
            db,
            interaction_id=interaction_id,
            tenant=tenant,
            final_reply=final_reply,
        )
    )
