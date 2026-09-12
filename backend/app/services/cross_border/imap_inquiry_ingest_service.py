"""只读 IMAP 询盘入库 — 去重 + 诚实门禁（禁止假询盘、禁止自动回复）。"""

from __future__ import annotations

import re
from typing import Any

from sqlalchemy.orm import Session

from app.models.tenant import Tenant
from app.services.inquiries_unified_service import InquiriesUnifiedService
from app.services.ubrain.imap_inquiry_sidecar import poll_imap_inbox

_IMAP_TAG = re.compile(r"\[imap-msg:([^\]]+)\]")


def _message_tag(message_id: str) -> str:
    """实现 消息标签 的功能。
    
    :param message_id: 参数 message_id（类型: str）
    :return: 返回 str 结果
    """
    return f"[imap-msg:{message_id}]"


def _already_ingested(db: Session, tenant_id: str, message_id: str) -> bool:
    """实现 alreadyingested 的功能。
    
    :param db: 参数 db（类型: Session）
    :param tenant_id: 参数 tenant_id（类型: str）
    :param message_id: 参数 message_id（类型: str）
    :return: 返回 bool 结果
    """
    tag = _message_tag(message_id)
    from app.models.inquiry import Inquiry
    hit = (
        db.query(Inquiry.id)
        .filter(
            Inquiry.tenant_id == tenant_id,
            Inquiry.is_active.is_(True),
            Inquiry.message.contains(tag),
        )
        .first()
    )
    return hit is not None


def _build_stored_message(msg: dict[str, Any]) -> str:
    """实现 构建stored消息 的功能。
    
    :param msg: 参数 msg（类型: dict[str, Any]）
    :return: 返回 str 结果
    """
    tag = _message_tag(str(msg["message_id"]))
    subject = str(msg.get("subject") or "").strip()
    body = str(msg.get("body") or "").strip()
    lines = [tag]
    if subject:
        lines.append(f"Subject: {subject}")
    if msg.get("evidence_url"):
        lines.append(f"evidence={msg['evidence_url']}")
    lines.append("")
    lines.append(body)
    return "\n".join(lines)[:12000]


def poll_and_ingest_imap_inquiries(
    db: Session,
    *,
    tenant: Tenant,
    max_messages: int = 10,
    mailbox: str | None = None,
) -> dict[str, Any]:
    """拉取 IMAP 新邮件并写入询盘表；跳过已入库 message_id。"""
    pack = poll_imap_inbox(
        tenant_id=str(tenant.id),
        mailbox=mailbox,
        max_messages=max_messages,
    )
    if not pack:
        return {
            "ok": False,
            "error_code": "IMAP_INQUIRY_NOT_CONFIGURED",
            "ingested": 0,
            "skipped": 0,
            "note": "请部署 IMAP_INQUIRY_URL Sidecar（只读收取，禁止 SMTP 群发）",
        }

    svc = InquiriesUnifiedService(db)
    ingested = 0
    skipped = 0
    errors: list[str] = []
    items: list[dict[str, Any]] = []
    for msg in pack.get("messages") or []:
        mid = str(msg.get("message_id") or "")
        if not mid:
            skipped += 1
            continue
        if _already_ingested(db, str(tenant.id), mid):
            skipped += 1
            continue
        from_email = str(msg.get("from_email") or "").strip()
        body = str(msg.get("body") or "").strip()
        if not from_email or len(body) < 4:
            skipped += 1
            errors.append(f"skip {mid}: missing email or body")
            continue
        name = str(msg.get("from_name") or from_email.split("@")[0] or "Email Lead")[:120]
        phone = f"email:{from_email}"[:50]
        subject = str(msg.get("subject") or "").strip()
        try:
            row = svc.create_public_lead(
                name=name,
                message=_build_stored_message(msg),
                email=from_email,
                phone=phone,
                product=subject[:100] if subject else None,
                source_channel="imap_readonly",
                tenant_id=str(tenant.id),
            )
            ingested += 1
            items.append({"inquiry_id": row.get("id"), "message_id": mid, "from_email": from_email})
        except Exception as exc:
            skipped += 1
            errors.append(f"{mid}: {exc}")

    return {
        "ok": True,
        "ingested": ingested,
        "skipped": skipped,
        "polled": pack.get("count", 0),
        "probe_mode": pack.get("probe_mode"),
        "mailbox": pack.get("mailbox"),
        "items": items,
        "errors": errors[:5] if errors else [],
        "human_verify_required": True,
        "disclaimer": "只读收取；不自动回复、不标记已发送。回复须人工确认。",
        "smtp_disabled": True,
    }
