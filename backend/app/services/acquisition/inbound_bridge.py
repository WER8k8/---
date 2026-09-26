# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199304817). All rights reserved.
"""入站消息 → 可跟进询盘 总线桥（W3 · 团队任务 #4）。

设计目标：**「收到消息」必然形成「可跟进询盘」**，且可重放、可观测、不静默。

链路：入站（WhatsApp / 邮件回复 / 表单 / 社媒）
      → ``handle_inbound_message``
      → ``repo.persist_inquiry``（唯一询盘收口，status=pending）
      → ``contact_events``（触点留痕，含方向/证据）
      → ``OpsCardStore.materialize``（跟单卡，落 CRM 唯一初始阶段 Lead）
      → 既有线索 ``prospect_leads.status = engaged``（命中邮箱/电话时，best-effort）

幂等：以 ``inquiries.session_id = "<channel>:<external_msg_id>"`` 为键，
同一条外部消息重放不产生第二张询盘（P0-7 要求「重发幂等」）。

红线：不新建平行业务账本；DB 不可用/单步失败 → 如实返回 ``created=false`` 与原因，
不假装成功（禁止静默）。
"""
from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

_MAX_SUMMARY = 4000


def _dedupe_key(
    channel: str,
    external_msg_id: str,
    *,
    phone: str = "",
    email: str = "",
    body: str = "",
) -> str:
    """构造 ``inquiries.session_id`` 幂等键（列长 64，稳定哈希）。

    - 有外部消息 id：``channel:msg_id``；
    - 无外部消息 id（如社媒/表单）：退化为 ``channel:发信人:正文前 200 字``，
      保证同一条入站重放仍幂等，不会被判为两条询盘；
    - 既无 id 又无发信人/正文：返回 ``""``（无法幂等，调用方按新建处理）。
    """
    ch = (channel or "").strip()
    mid = (external_msg_id or "").strip()
    if mid:
        raw = f"{ch}:{mid}"
    else:
        ident = (phone or email or "").strip()
        text = (body or "").strip()
        if not ident or not text:
            return ""
        raw = f"{ch}:{ident}:{text[:200]}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:64]


def record_contact_event(
    db: Any,
    *,
    tenant_id: str = "",
    channel: str,
    event_type: str = "message",
    direction: str = "inbound",
    inquiry_id: str = "",
    lead_id: str = "",
    summary: str = "",
    payload: Optional[dict] = None,
    provenance_metadata: Optional[dict] = None,
) -> dict[str, Any]:
    """写一条 ``contact_events`` 触点（外发/入站统一留痕）。

    Returns: ``{"persisted": bool, "id": str|None, "reason": str}``
    """
    if db is None:
        return {"persisted": False, "id": None, "reason": "db_unavailable"}
    try:
        from app.models.trade_fulfillment import ContactEvent
        from app.services.acquisition.repo import resolve_tenant_uuid

        tid = resolve_tenant_uuid(db, tenant_id) if tenant_id else None
        row = ContactEvent(
            tenant_id=tid,
            inquiry_id=inquiry_id or None,
            lead_id=(lead_id or None),
            channel=(channel or "web")[:30],
            event_type=(event_type or "message")[:40],
            direction=(direction or "inbound")[:12],
            summary=(summary or "")[:_MAX_SUMMARY] or None,
            payload_json=json.dumps(payload or {}, ensure_ascii=False, default=str)[:20000],
            provenance_metadata=provenance_metadata,
        )
        db.add(row)
        db.commit()
        return {"persisted": True, "id": str(getattr(row, "id", "") or ""), "reason": ""}
    except Exception as exc:  # noqa: BLE001
        logger.warning("record_contact_event 失败: %s", exc)
        try:
            db.rollback()
        except Exception:  # noqa: BLE001
            pass
        return {"persisted": False, "id": None, "reason": str(exc)[:200]}


def _find_existing_inquiry(db: Any, session_id: str) -> Optional[str]:
    if not session_id:
        return None
    try:
        from app.models.inquiry import Inquiry
        row = db.query(Inquiry).filter(Inquiry.session_id == session_id).first()
        return str(getattr(row, "id", "") or "") or None
    except Exception:  # noqa: BLE001
        return None


def _mark_lead_engaged(db: Any, *, email: str, phone: str, tenant_id: str) -> Optional[str]:
    """命中既有线索则置 ``engaged``（best-effort，失败不影响询盘主链）。"""
    if not email and not phone:
        return None
    try:
        from app.models.prospect_lead import LeadStatus, ProspectLead
        from app.services.acquisition.repo import resolve_tenant_uuid

        tid = resolve_tenant_uuid(db, tenant_id) if tenant_id else None
        q = db.query(ProspectLead)
        if email:
            q = q.filter(ProspectLead.email == email)
        elif phone:
            q = q.filter(ProspectLead.phone == phone)
        if tid:
            q = q.filter(ProspectLead.tenant_id == tid)
        lead = q.first()
        if lead is None:
            return None
        lead.status = LeadStatus.ENGAGED
        db.commit()
        return str(getattr(lead, "id", "") or "") or None
    except Exception as exc:  # noqa: BLE001
        logger.debug("mark_lead_engaged 跳过: %s", exc)
        try:
            db.rollback()
        except Exception:  # noqa: BLE001
            pass
        return None


def handle_inbound_message(
    db: Any,
    *,
    tenant_id: str = "",
    channel: str = "web",
    phone: str = "",
    email: str = "",
    body: str = "",
    subject: str = "",
    sender_name: str = "",
    external_msg_id: str = "",
    source: str = "",
    country: str = "",
    payload: Optional[dict] = None,
    create_ops_card: bool = True,
) -> dict[str, Any]:
    """入站消息统一收口 → 询盘 + 触点 + 跟单卡（幂等）。

    Returns:
        ``{created, duplicate, inquiry_id, contact_event_id, ops_card, lead_id, reason, errors}``
    """
    from app.services.acquisition.repo import persist_inquiry

    result: dict[str, Any] = {
        "created": False,
        "duplicate": False,
        "inquiry_id": None,
        "contact_event_id": None,
        "ops_card": None,
        "lead_id": None,
        "reason": "",
        "errors": [],
        "channel": channel,
    }
    if db is None:
        result["reason"] = "db_unavailable"
        return result
    if not (phone or email or body):
        result["reason"] = "empty_inbound_payload"
        return result

    session_id = _dedupe_key(
        channel, external_msg_id, phone=phone, email=email, body=body
    )

    # 1. 幂等：同一条外部消息重放 → 只返回既有询盘
    existing = _find_existing_inquiry(db, session_id)
    if existing:
        result.update({"duplicate": True, "inquiry_id": existing, "reason": "duplicate_message"})
        logger.info("[inbound] 重复入站消息跳过 channel=%s msg=%s inquiry=%s",
                    channel, external_msg_id, existing)
        return result

    # 2. 询盘（唯一收口）
    message = body or (f"[{channel} 入站消息]")
    prov = {
        "source": source or f"{channel}_inbound",
        "external_msg_id": external_msg_id or "",
        "bus": "inbound_bridge",
        "has_subject": bool(subject),
    }
    ires = persist_inquiry(
        db,
        tenant_id=tenant_id,
        inquiry_id="",
        message=message,
        email=email,
        contact_name=sender_name,
        phone=phone,
        product=(subject or "")[:100],
        country=country,
        channel=f"{channel}_inbound",
        status="pending",
        session_id=session_id,
        source_channel=f"{channel}_inbound",
        provenance_metadata=prov,
    )
    if not ires.get("persisted"):
        result["reason"] = f"inquiry_persist_failed: {ires.get('reason')}"
        result["errors"].append(result["reason"])
        logger.warning("[inbound] 询盘落库失败 channel=%s reason=%s", channel, ires.get("reason"))
        return result

    inquiry_id = ires.get("id")
    result["created"] = True
    result["inquiry_id"] = inquiry_id

    # 3. 触点留痕
    ce = record_contact_event(
        db,
        tenant_id=tenant_id,
        channel=channel,
        event_type="message",
        direction="inbound",
        inquiry_id=inquiry_id or "",
        summary=message[:500],
        payload=payload or {},
        provenance_metadata=prov,
    )
    if ce.get("persisted"):
        result["contact_event_id"] = ce.get("id")
    else:
        result["errors"].append(f"contact_event_failed: {ce.get('reason')}")

    # 4. 跟单卡（CRM 唯一初始阶段）
    if create_ops_card and inquiry_id:
        try:
            from app.services.acquisition import ops_card_store
            card = ops_card_store.materialize(tenant_id=str(tenant_id or ""), inquiry_id=inquiry_id)
            ops_card_store.record_touch(
                inquiry_id,
                channel=channel,
                summary=message[:200],
                direction="inbound",
            )
            result["ops_card"] = {"inquiry_id": inquiry_id, "stage": getattr(card, "stage", None)}
        except Exception as exc:  # noqa: BLE001
            result["errors"].append(f"ops_card_failed: {str(exc)[:120]}")
            logger.warning("[inbound] 跟单卡生成失败: %s", exc)

    # 5. 既有线索置 engaged（best-effort）
    lead_id = _mark_lead_engaged(db, email=email, phone=phone, tenant_id=tenant_id)
    if lead_id:
        result["lead_id"] = lead_id

    logger.info("[inbound] 入站 → 询盘: channel=%s inquiry=%s", channel, inquiry_id)
    return result
