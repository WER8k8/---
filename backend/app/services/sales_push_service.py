# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Lane P · 询盘/社媒互动 → 租户企微推送编排。"""

from __future__ import annotations

import logging
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.inquiry import Inquiry
from app.models.push_event import PushEvent
from app.models.social_interaction import SocialInteraction
from app.services import wecom_push_service as wecom
from app.services.tenant_wecom_config_service import resolve_push_credentials

logger = logging.getLogger(__name__)


def _create_event(
    db: Session,
    *,
    tenant_id: Optional[str],
    event_type: str,
    ref_type: str,
    ref_id: str,
    title: str,
    body: str,
    recipient: Optional[str] = None,
) -> PushEvent:
    """_create_event。

    参数说明：
    :param db: 参数 db
    :param tenant_id: 参数 tenant_id
    :param event_type: 参数 event_type
    :param ref_type: 参数 ref_type
    :param ref_id: 参数 ref_id
    :param title: 参数 title
    :param body: 参数 body
    :param recipient: 参数 recipient
    :return: 返回处理结果。
    """
    row = PushEvent(
        tenant_id=tenant_id,
        event_type=event_type,
        ref_type=ref_type,
        ref_id=ref_id,
        title=title[:200],
        body=body,
        recipient=recipient,
        status="pending",
    )
    db.add(row)
    db.flush()
    return row


def _finalize_event(db: Session, event: PushEvent, result: dict[str, Any]) -> dict[str, Any]:
    """_finalize_event。

    参数说明：
    :param db: 参数 db
    :param event: 参数 event
    :param result: 参数 result
    :return: 返回处理结果。
    """
    if result.get("skipped"):
        db.rollback()
        return result
    if result.get("sent"):
        event.status = "sent"
        event.channel = result.get("channel") or event.channel
        event.upstream_msgid = result.get("upstream_msgid")
        event.upstream_receipt = result.get("upstream_receipt")
        event.recipient = result.get("recipient") or event.recipient
        event.error_code = None
        event.error_message = None
    else:
        event.status = "failed"
        event.error_code = (result.get("error_code") or "PUSH_FAILED")[:64]
        event.error_message = (result.get("error_message") or "推送失败")[:500]
        event.upstream_receipt = result.get("upstream_receipt")
        event.retry_count = (event.retry_count or 0) + 1
    db.commit()
    db.refresh(event)
    return {
        "event_id": event.id,
        "status": event.status,
        "channel": event.channel,
        "upstream_msgid": event.upstream_msgid,
        "error_code": event.error_code,
    }


def dispatch_text_push(
    db: Session,
    *,
    tenant_id: Optional[str],
    event_type: str,
    ref_type: str,
    ref_id: str,
    title: str,
    body: str,
    userids: Optional[list[str]] = None,
) -> dict[str, Any]:
    """使用租户自有企微配置推送；生产禁止用平台 .env 冒充客户接收人。"""
    if not tenant_id:
        return {"sent": False, "skipped": True, "reason": "no_tenant_id"}

    cred, resolved_recipients, cred_source = resolve_push_credentials(db, tenant_id)
    recipients = userids or resolved_recipients
    if not cred or not recipients:
        return {
            "sent": False,
            "skipped": True,
            "reason": "tenant_wecom_not_configured",
            "hint": "请客户在「询盘 IM」页配置本企业企微；开发环境可在 .env 配置 WECOM_* 与 WECOM_PUSH_TO_USERIDS",
            "cred_source": cred_source,
        }

    event = _create_event(
        db,
        tenant_id=tenant_id,
        event_type=event_type,
        ref_type=ref_type,
        ref_id=ref_id,
        title=title,
        body=body,
        recipient="|".join(recipients) if recipients else None,
    )
    result: dict[str, Any] = {"sent": False, "error_code": "NOT_ATTEMPTED"}
    if cred and cred.app_ready:
        result = wecom.send_app_text_message_with_credentials(
            cred,
            userids=recipients,
            content=f"{title}\n{body}",
        )
        event.channel = "wecom_app"

    if not result.get("sent") and cred and cred.webhook_ready:
        result = wecom.send_webhook_markdown_to_url(
            webhook_url=cred.webhook_url,
            title=title,
            body_md=body,
        )
        event.channel = "wecom_webhook"

    if not result.get("sent") and result.get("error_code") == "NOT_ATTEMPTED":
        result = {
            "sent": False,
            "error_code": "TENANT_WECOM_INCOMPLETE",
            "error_message": "租户企微未启用或应用/机器人均未就绪",
        }

    payload = _finalize_event(db, event, result)
    payload["cred_source"] = cred_source
    return payload


def notify_social_interaction(db: Session, interaction: SocialInteraction | dict[str, Any]) -> dict[str, Any]:
    """notify_social_interaction。

    参数说明：
    :param db: 参数 db
    :param interaction: 参数 interaction
    :return: 返回处理结果。
    """
    if isinstance(interaction, dict):
        iid = interaction.get("id")
        tenant_id = interaction.get("tenant_id")
        author = interaction.get("author_name") or "访客"
        content = interaction.get("content") or ""
        intent = interaction.get("intent") or "general"
        status = interaction.get("status") or ""
        inquiry_id = interaction.get("inquiry_id")
    else:
        iid = interaction.id
        tenant_id = interaction.tenant_id
        author = interaction.author_name
        content = interaction.content
        intent = interaction.intent
        status = interaction.status
        inquiry_id = interaction.inquiry_id

    if status == "skipped":
        return {"sent": False, "skipped": True, "reason": "spam_skipped"}

    title = "📣 抖音新评论待谈单"
    body = (
        f"**用户**：{author}\n"
        f"**意向**：{intent}\n"
        f"**内容**：{content[:500]}\n"
        f"**状态**：{status}\n"
        f"**互动ID**：{iid}"
    )
    if inquiry_id:
        body += f"\n**询盘ID**：{inquiry_id}"
    body += f"\n**处理**：/sales/auto-negotiator?interaction={iid}"
    return dispatch_text_push(
        db,
        tenant_id=str(tenant_id) if tenant_id else None,
        event_type="social_comment",
        ref_type="social_interaction",
        ref_id=str(iid),
        title=title,
        body=body,
    )


def notify_inquiry_wecom(db: Session, inquiry: Inquiry) -> dict[str, Any]:
    """notify_inquiry_wecom。

    参数说明：
    :param db: 参数 db
    :param inquiry: 参数 inquiry
    :return: 返回处理结果。
    """
    name = getattr(inquiry, "name", "") or "访客"
    phone = getattr(inquiry, "phone", "") or "—"
    channel = getattr(inquiry, "source_channel", "") or "—"
    message = (getattr(inquiry, "message", "") or "")[:500]
    tenant_id = getattr(inquiry, "tenant_id", None)
    title = "📩 新询盘"
    body = (
        f"**联系人**：{name} · {phone}\n"
        f"**渠道**：{channel}\n"
        f"**需求**：{message}\n"
        f"**询盘ID**：{inquiry.id}"
    )
    return dispatch_text_push(
        db,
        tenant_id=str(tenant_id) if tenant_id else None,
        event_type="inquiry_new",
        ref_type="inquiry",
        ref_id=str(inquiry.id),
        title=title,
        body=body,
    )
