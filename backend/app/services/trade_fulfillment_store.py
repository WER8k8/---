# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""P0-1 核心表业务写路径（修复计划 A-2 回归）。

所有写库失败只记日志、不抛穿调用方——业务主链不因审计落库中断；
但写库成功与否会体现在返回 dict 的 `persisted` 字段，禁止假报。
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.trade_fulfillment import (
    BusinessPayment,
    ContactEvent,
    ExperienceRecord,
    Invoice,
    KnowledgeBase,
    LogisticsShipment,
    Pipeline,
    PurchaseOrder,
    WhatsappMessage,
)

logger = logging.getLogger(__name__)


def _now():
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return str(uuid.uuid4())


def persist_whatsapp_message(
    db: Optional[Session],
    *,
    tenant_id: Optional[str],
    phone_e164: str,
    message_body: str,
    direction: str = "outbound",
    status: str = "queued",
    inquiry_id: Optional[str] = None,
    lead_id: Optional[str] = None,
    template_id: Optional[str] = None,
    external_msg_id: Optional[str] = None,
    simulated: bool = False,
    degraded: bool = False,
    error: Optional[str] = None,
    sent_at: Optional[datetime] = None,
) -> dict[str, Any]:
    """WhatsApp 消息落库 whatsapp_messages。"""
    if db is None:
        return {"persisted": False, "reason": "no_db"}
    try:
        row = WhatsappMessage(
            id=_new_id(),
            tenant_id=tenant_id,
            inquiry_id=inquiry_id,
            lead_id=lead_id,
            phone_e164=phone_e164 or "",
            direction=direction or "outbound",
            message_body=message_body or "",
            template_id=template_id,
            status=status or "queued",
            external_msg_id=external_msg_id,
            simulated=bool(simulated),
            degraded=bool(degraded),
            error=error,
            sent_at=sent_at or _now(),
            created_at=_now(),
            updated_at=_now(),
        )
        db.add(row)
        db.commit()
        return {"persisted": True, "id": row.id, "status": row.status}
    except Exception as exc:  # noqa: BLE001
        logger.warning("whatsapp_messages persist failed: %s", exc)
        try:
            db.rollback()
        except Exception:  # noqa: BLE001
            pass
        return {"persisted": False, "error": str(exc)}


def persist_logistics_shipment(
    db: Optional[Session],
    *,
    tenant_id: Optional[str],
    tracking_no: str,
    carrier: Optional[str] = None,
    status: str = "in_transit",
    order_id: Optional[str] = None,
    purchase_order_id: Optional[str] = None,
    origin_port: Optional[str] = None,
    dest_port: Optional[str] = None,
    payload: Optional[dict] = None,
    simulated: bool = False,
) -> dict[str, Any]:
    """发运/物流轨迹落库 logistics_shipments（demo 源如实 status+payload.simulated）。"""
    if db is None:
        return {"persisted": False, "reason": "no_db"}
    try:
        payload = dict(payload or {})
        if simulated:
            payload["simulated"] = True
            if status in ("in_transit", "delivered", "pending"):
                status = "exception" if status == "exception" else status
                payload.setdefault("note", "simulated_source")
        import json

        row = LogisticsShipment(
            id=_new_id(),
            tenant_id=tenant_id,
            order_id=order_id,
            purchase_order_id=purchase_order_id,
            tracking_no=tracking_no,
            carrier=carrier,
            origin_port=origin_port,
            dest_port=dest_port,
            status=status or "pending",
            shipped_at=_now(),
            payload_json=json.dumps(payload, ensure_ascii=False, default=str),
            created_at=_now(),
            updated_at=_now(),
        )
        db.add(row)
        db.commit()
        return {"persisted": True, "id": row.id, "status": row.status, "simulated": bool(simulated)}
    except Exception as exc:  # noqa: BLE001
        logger.warning("logistics_shipments persist failed: %s", exc)
        try:
            db.rollback()
        except Exception:  # noqa: BLE001
            pass
        return {"persisted": False, "error": str(exc)}


def persist_experience_record(
    db: Optional[Session],
    *,
    title: str,
    content: Optional[str] = None,
    tenant_id: Optional[str] = None,
    source_type: str = "biz_outcome",
    source_id: Optional[str] = None,
    experience_type: str = "pattern",
    score: float = 0.0,
    status: str = "raw",
    metadata: Optional[dict] = None,
) -> dict[str, Any]:
    """业务经验落库 experience_records（与 JSON 兜底/evolution 并存，不互相替代）。"""
    if db is None:
        return {"persisted": False, "reason": "no_db"}
    try:
        import json

        row = ExperienceRecord(
            id=_new_id(),
            tenant_id=tenant_id,
            source_type=source_type,
            source_id=source_id,
            experience_type=experience_type,
            title=(title or "untitled")[:200],
            content=content,
            score=float(score or 0),
            status=status or "raw",
            metadata_json=json.dumps(metadata or {}, ensure_ascii=False, default=str),
            created_at=_now(),
            updated_at=_now(),
        )
        db.add(row)
        db.commit()
        return {"persisted": True, "id": row.id, "status": row.status}
    except Exception as exc:  # noqa: BLE001
        logger.warning("experience_records persist failed: %s", exc)
        try:
            db.rollback()
        except Exception:  # noqa: BLE001
            pass
        return {"persisted": False, "error": str(exc)}


def persist_contact_event(
    db: Optional[Session],
    *,
    tenant_id: Optional[str],
    channel: str = "web",
    event_type: str = "inquiry",
    direction: str = "inbound",
    summary: Optional[str] = None,
    inquiry_id: Optional[str] = None,
    lead_id: Optional[str] = None,
    payload: Optional[dict] = None,
) -> dict[str, Any]:
    """触点事件落库 contact_events。"""
    if db is None:
        return {"persisted": False, "reason": "no_db"}
    try:
        import json

        row = ContactEvent(
            id=_new_id(),
            tenant_id=tenant_id,
            inquiry_id=inquiry_id,
            lead_id=lead_id,
            channel=channel or "web",
            event_type=event_type or "view",
            direction=direction or "inbound",
            summary=summary,
            payload_json=json.dumps(payload or {}, ensure_ascii=False, default=str),
            occurred_at=_now(),
            created_at=_now(),
        )
        db.add(row)
        db.commit()
        return {"persisted": True, "id": row.id}
    except Exception as exc:  # noqa: BLE001
        logger.warning("contact_events persist failed: %s", exc)
        try:
            db.rollback()
        except Exception:  # noqa: BLE001
            pass
        return {"persisted": False, "error": str(exc)}


def persist_purchase_order(
    db: Optional[Session],
    *,
    po_number: str,
    tenant_id: Optional[str] = None,
    order_id: Optional[str] = None,
    supplier_name: Optional[str] = None,
    product_desc: Optional[str] = None,
    quantity: float = 0,
    unit: str = "pcs",
    unit_price: float = 0,
    currency: str = "USD",
    status: str = "draft",
    notes: Optional[str] = None,
) -> dict[str, Any]:
    """采购/生产跟单落库 purchase_orders。"""
    if db is None:
        return {"persisted": False, "reason": "no_db"}
    try:
        row = PurchaseOrder(
            id=_new_id(),
            tenant_id=tenant_id,
            order_id=order_id,
            po_number=po_number,
            supplier_name=supplier_name,
            product_desc=product_desc,
            quantity=quantity or 0,
            unit=unit or "pcs",
            unit_price=unit_price or 0,
            currency=currency or "USD",
            status=status or "draft",
            notes=notes,
            created_at=_now(),
            updated_at=_now(),
        )
        db.add(row)
        db.commit()
        return {"persisted": True, "id": row.id, "po_number": row.po_number}
    except Exception as exc:  # noqa: BLE001
        logger.warning("purchase_orders persist failed: %s", exc)
        try:
            db.rollback()
        except Exception:  # noqa: BLE001
            pass
        return {"persisted": False, "error": str(exc)}


def persist_invoice(
    db: Optional[Session],
    *,
    invoice_no: str,
    tenant_id: Optional[str] = None,
    order_id: Optional[str] = None,
    invoice_type: str = "pi",
    buyer_name: Optional[str] = None,
    amount: float = 0,
    currency: str = "USD",
    status: str = "draft",
    notes: Optional[str] = None,
) -> dict[str, Any]:
    """贸易发票/PI 落库 invoices。"""
    if db is None:
        return {"persisted": False, "reason": "no_db"}
    try:
        existing = db.query(Invoice).filter(Invoice.invoice_no == invoice_no).first()
        if existing:
            existing.status = status or existing.status
            existing.amount = amount if amount is not None else existing.amount
            existing.updated_at = _now()
            db.commit()
            return {"persisted": True, "id": existing.id, "invoice_no": existing.invoice_no, "created": False}
        row = Invoice(
            id=_new_id(),
            tenant_id=tenant_id,
            order_id=order_id,
            invoice_no=invoice_no,
            invoice_type=invoice_type or "pi",
            buyer_name=buyer_name,
            amount=amount or 0,
            currency=currency or "USD",
            status=status or "draft",
            notes=notes,
            issued_at=_now() if status in ("issued", "sent", "paid") else None,
            created_at=_now(),
            updated_at=_now(),
        )
        db.add(row)
        db.commit()
        return {"persisted": True, "id": row.id, "invoice_no": row.invoice_no, "created": True}
    except Exception as exc:  # noqa: BLE001
        logger.warning("invoices persist failed: %s", exc)
        try:
            db.rollback()
        except Exception:  # noqa: BLE001
            pass
        return {"persisted": False, "error": str(exc)}


def persist_business_payment(
    db: Optional[Session],
    *,
    amount: float,
    tenant_id: Optional[str] = None,
    order_id: Optional[str] = None,
    invoice_id: Optional[str] = None,
    currency: str = "USD",
    method: str = "tt",
    status: str = "pending",
    reference_no: Optional[str] = None,
    notes: Optional[str] = None,
    paid_at: Optional[datetime] = None,
) -> dict[str, Any]:
    """业务订单收款落库 payments（平台订阅仍写 payment_orders）。"""
    if db is None:
        return {"persisted": False, "reason": "no_db"}
    try:
        row = BusinessPayment(
            id=_new_id(),
            tenant_id=tenant_id,
            order_id=order_id,
            invoice_id=invoice_id,
            amount=amount or 0,
            currency=currency or "USD",
            method=method or "tt",
            status=status or "pending",
            paid_at=paid_at,
            reference_no=reference_no,
            notes=notes,
            created_at=_now(),
            updated_at=_now(),
        )
        db.add(row)
        db.commit()
        return {"persisted": True, "id": row.id, "status": row.status}
    except Exception as exc:  # noqa: BLE001
        logger.warning("payments persist failed: %s", exc)
        try:
            db.rollback()
        except Exception:  # noqa: BLE001
            pass
        return {"persisted": False, "error": str(exc)}


def ensure_default_pipeline(
    db: Optional[Session],
    *,
    tenant_id: Optional[str],
    name: str = "外贸7步履约",
    pipeline_type: str = "fulfillment",
    stages: Optional[list[str]] = None,
) -> dict[str, Any]:
    """确保租户存在默认履约管线 pipelines（幂等：同租户同名不重复建）。"""
    if db is None:
        return {"persisted": False, "reason": "no_db"}
    try:
        stages = stages or [
            "询盘捕获",
            "需求核算",
            "形式发票PI",
            "定金核销",
            "生产跟单",
            "发运单证",
            "尾款与物流",
        ]
        q = db.query(Pipeline).filter(
            Pipeline.tenant_id == tenant_id,
            Pipeline.name == name,
            Pipeline.pipeline_type == pipeline_type,
        )
        existing = q.first()
        if existing:
            return {"persisted": True, "id": existing.id, "created": False}
        import json

        row = Pipeline(
            id=_new_id(),
            tenant_id=tenant_id,
            name=name,
            pipeline_type=pipeline_type,
            stage_count=len(stages),
            is_default=True,
            is_active=True,
            config_json=json.dumps({"stages": stages}, ensure_ascii=False),
            created_at=_now(),
            updated_at=_now(),
        )
        db.add(row)
        db.commit()
        return {"persisted": True, "id": row.id, "created": True}
    except Exception as exc:  # noqa: BLE001
        logger.warning("pipelines ensure failed: %s", exc)
        try:
            db.rollback()
        except Exception:  # noqa: BLE001
            pass
        return {"persisted": False, "error": str(exc)}


def ensure_knowledge_base(
    db: Optional[Session],
    *,
    tenant_id: Optional[str],
    name: str,
    kb_type: str = "product",
    description: Optional[str] = None,
    source: str = "manual",
) -> dict[str, Any]:
    """确保租户知识库目录存在 knowledge_bases（幂等）。"""
    if db is None:
        return {"persisted": False, "reason": "no_db"}
    try:
        existing = (
            db.query(KnowledgeBase)
            .filter(KnowledgeBase.tenant_id == tenant_id, KnowledgeBase.name == name)
            .first()
        )
        if existing:
            return {"persisted": True, "id": existing.id, "created": False}
        row = KnowledgeBase(
            id=_new_id(),
            tenant_id=tenant_id,
            name=name,
            description=description,
            kb_type=kb_type or "product",
            source=source or "manual",
            doc_count=0,
            is_active=True,
            created_at=_now(),
            updated_at=_now(),
        )
        db.add(row)
        db.commit()
        return {"persisted": True, "id": row.id, "created": True}
    except Exception as exc:  # noqa: BLE001
        logger.warning("knowledge_bases ensure failed: %s", exc)
        try:
            db.rollback()
        except Exception:  # noqa: BLE001
            pass
        return {"persisted": False, "error": str(exc)}
