# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""本项目 CRM 履约域 · 优丁原生实现。

主理人裁定：**goodjob_crm 就是本项目的 CRM**；TradeAI 同理是本项目拓客能力域。
真相与写路径落在优丁 PG，**不以 GOODJOB_BASE_URL 外桥为前置条件**。

- document.generate_*  → trade_document_service + invoices 落库
- crm.sync_stage       → orders 状态机（可达路径跃迁）+ pipelines/contact_events
- crm.sync_lead        → inquiries / opportunities
- crm.update_opportunity → opportunities.stage

求真：账户未配置不编造银行号；状态跃迁走白名单可达路径；**无外桥**。
"""
from __future__ import annotations

import logging
import os
import uuid
from collections import deque
from typing import Any, Optional

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

_DEFAULT_SELLER = {
    "name": "YouDing Building Materials Tech Co., Ltd.",
    "address": "No. 88 Export Industrial Zone, Guangdong, China",
    "email": "export@youding.com",
}

_STAGE_TO_ORDER_STATUS = {
    "draft": "draft",
    "pending": "pending",
    "quoted": "pending",
    "pi_issued": "pending",
    "deposit": "deposit_received",
    "deposit_received": "deposit_received",
    "confirmed": "confirmed",
    "production": "in_production",
    "in_production": "in_production",
    "producing": "in_production",
    "shipped": "shipped",
    "shipping": "shipped",
    "dispatched": "shipped",
    "final_payment": "final_payment_received",
    "final_payment_received": "final_payment_received",
    "completed": "completed",
    "done": "completed",
    "won": "completed",
    "cancelled": "cancelled",
}

_OPP_STAGE_MAP = {
    "new": "prospecting",
    "prospecting": "prospecting",
    "contacted": "qualification",
    "qualified": "qualification",
    "needs_analysis": "needs_analysis",
    "proposal": "proposal",
    "quoted": "proposal",
    "negotiation": "negotiation",
    "negotiated": "negotiation",
    "won": "won",
    "lost": "lost",
}


def _bank_from_settings() -> Optional[dict[str, Any]]:
    try:
        from app.core.config import settings
    except Exception:  # noqa: BLE001
        settings = None  # type: ignore
    beneficiary = (getattr(settings, "TRADE_BANK_BENEFICIARY", None) or os.getenv("TRADE_BANK_BENEFICIARY") or "").strip()
    bank_name = (getattr(settings, "TRADE_BANK_NAME", None) or os.getenv("TRADE_BANK_NAME") or "").strip()
    account_no = (getattr(settings, "TRADE_BANK_ACCOUNT", None) or os.getenv("TRADE_BANK_ACCOUNT") or "").strip()
    swift = (getattr(settings, "TRADE_BANK_SWIFT", None) or os.getenv("TRADE_BANK_SWIFT") or "").strip()
    if not (beneficiary or bank_name or account_no):
        return None
    return {
        "beneficiary": beneficiary or _DEFAULT_SELLER["name"],
        "bank_name": bank_name or "PENDING_CONFIGURATION",
        "account_no": account_no or "PENDING_CONFIGURATION",
        "swift_code": swift or "PENDING_CONFIGURATION",
        "configured": bool(account_no and bank_name),
    }


def _norm_items(items: Any) -> list[dict[str, Any]]:
    if isinstance(items, dict):
        items = [items]
    if not isinstance(items, list):
        return []
    out: list[dict[str, Any]] = []
    for row in items:
        if not isinstance(row, dict):
            continue
        out.append(
            {
                "description": row.get("description") or row.get("product_name") or row.get("name") or "",
                "product_name": row.get("product_name") or row.get("description") or "",
                "quantity": float(row.get("quantity") or row.get("qty") or 0),
                "unit": row.get("unit") or "pcs",
                "unit_price": float(row.get("unit_price") or row.get("price") or 0),
                "hs_code": row.get("hs_code") or "6802.91.00",
            }
        )
    return out


def _default_items_from_params(params: dict[str, Any]) -> list[dict[str, Any]]:
    name = str(params.get("product_name") or params.get("product") or "Building Materials Solution")
    qty = float(params.get("quantity") or params.get("qty") or 1)
    price = float(params.get("unit_price") or params.get("price") or 0)
    return [
        {
            "description": name,
            "product_name": name,
            "quantity": qty,
            "unit": str(params.get("unit") or "pcs"),
            "unit_price": price,
            "hs_code": str(params.get("hs_code") or "6802.91.00"),
        }
    ]


def _buyer_from_params(params: dict[str, Any]) -> dict[str, Any]:
    name = str(params.get("buyer_name") or params.get("company_name") or params.get("buyer") or "Global Trade Buyer")
    return {
        "name": name,
        "company": str(params.get("company") or name),
        "country": str(params.get("country") or ""),
        "email": str(params.get("email") or params.get("buyer_email") or ""),
        "code": str(params.get("buyer_code") or "")[:24],
    }


def _status_val(v: Any) -> str:
    return getattr(v, "value", v) or ""


def _status_path(current: str, target: str) -> Optional[list[str]]:
    from app.models.enums import _ORDER_TRANSITIONS

    if current == target:
        return [current]
    adj: dict[str, list[str]] = {}
    for fr, to in _ORDER_TRANSITIONS:
        adj.setdefault(fr, []).append(to)
    q = deque([(current, [current])])
    seen = {current}
    while q:
        node, path = q.popleft()
        for nxt in adj.get(node, []):
            if nxt in seen:
                continue
            np = path + [nxt]
            if nxt == target:
                return np
            seen.add(nxt)
            q.append((nxt, np))
    return None


def generate_trade_document(
    *,
    doc_type: str,
    tenant_id: Optional[str],
    params: dict[str, Any],
    db: Optional[Session] = None,
    order_id: Optional[str] = None,
    inquiry_id: Optional[str] = None,
) -> dict[str, Any]:
    """优丁原生生成 PI/CI/PL；账户未配置不编造银行号。"""
    doc_type = (doc_type or "PI").upper()
    if doc_type in ("PACKING_LIST", "PACKING-LIST"):
        doc_type = "PL"
    if doc_type not in ("PI", "CI", "PL"):
        return {"success": False, "error": f"unsupported_doc_type:{doc_type}", "native": True}

    items = _norm_items(params.get("items")) or _default_items_from_params(params)
    if not items:
        return {"success": False, "error": "items_required", "native": True}

    seller = dict(_DEFAULT_SELLER)
    if isinstance(params.get("seller"), dict):
        seller.update({k: v for k, v in params["seller"].items() if v})
    buyer = _buyer_from_params(params)
    currency = str(params.get("currency") or "USD")
    bank = params.get("bank_details") if isinstance(params.get("bank_details"), dict) else _bank_from_settings()
    if bank is None:
        bank = {
            "beneficiary": seller.get("name"),
            "bank_name": "PENDING_CONFIGURATION",
            "account_no": "PENDING_CONFIGURATION",
            "swift_code": "PENDING_CONFIGURATION",
            "configured": False,
            "note": "收款账户未在优丁配置，单证不编造银行账号",
        }

    from app.services.foreign_trade.trade_document_service import (
        build_commercial_invoice,
        build_packing_list,
        build_proforma_invoice,
    )

    pi_no = str(params.get("pi_no") or params.get("invoice_no") or "") or None
    ci_no = str(params.get("ci_no") or "") or None
    order_ref = order_id or str(params.get("order_ref") or params.get("order_number") or "")

    try:
        if doc_type == "PI":
            doc = build_proforma_invoice(
                seller=seller,
                buyer=buyer,
                lines=items,
                currency=currency,
                payment_terms=str(params.get("payment_terms") or "30% deposit, 70% before shipment"),
                delivery_terms=str(params.get("incoterms") or params.get("delivery_terms") or "FOB Shenzhen"),
                notes=str(params.get("notes") or "Generated by YouDing CRM (goodjob_crm native)"),
                pi_no=pi_no,
                bank_details=bank,
                db=db,
                tenant_id=tenant_id,
                order_id=order_id,
            )
            doc_no = doc.get("pi_no")
            amount = float(doc.get("subtotal") or 0)
        elif doc_type == "CI":
            doc = build_commercial_invoice(
                seller=seller,
                buyer=buyer,
                lines=items,
                ci_no=ci_no or (f"CI-{order_ref}" if order_ref else None),
                pi_ref=pi_no or str(params.get("pi_ref") or ""),
                order_ref=order_ref,
                currency=currency,
                incoterms=str(params.get("incoterms") or "FOB Shenzhen"),
                port_of_loading=str(params.get("port_of_loading") or "Shenzhen, China"),
                port_of_discharge=str(params.get("port_of_discharge") or "Destination Port"),
                bl_number=str(params.get("bl_number") or "Pending"),
                deposit_paid=float(params.get("deposit_paid") or 0),
                payment_terms=str(params.get("payment_terms") or "30% deposit received, 70% against B/L copy"),
                bank_details=bank,
            )
            doc_no = doc.get("ci_no") or ci_no
            amount = float(doc.get("subtotal") or doc.get("total_amount") or 0)
            if db is not None and doc_no:
                from app.services.trade_fulfillment_store import persist_invoice

                doc["invoice_persisted"] = persist_invoice(
                    db,
                    invoice_no=str(doc_no),
                    tenant_id=tenant_id,
                    order_id=order_id,
                    invoice_type="commercial",
                    buyer_name=buyer.get("name"),
                    amount=amount,
                    currency=currency,
                    status="draft",
                )
        else:
            packing_ci_no = ci_no or (f"CI-{order_ref}" if order_ref else None)
            packages = params.get("packages")
            if not isinstance(packages, list) or not packages:
                packages = [
                    {
                        "description": it.get("description") or it.get("product_name"),
                        "quantity": it.get("quantity"),
                        "package_count": 1,
                        "qty_per_package": it.get("quantity") or 1,
                    }
                    for it in items
                ]
            doc = build_packing_list(
                seller=seller,
                buyer=buyer,
                packages=packages,
                pl_no=str(params.get("pl_no") or "") or None,
                ci_ref=packing_ci_no,
                order_ref=order_ref or None,
                shipping_marks=str(params.get("shipping_marks") or "N/M (No Marks) or As Addressed"),
                port_of_loading=str(params.get("port_of_loading") or "Shenzhen, China"),
                port_of_discharge=str(params.get("port_of_discharge") or "Destination Port"),
            )
            doc_no = doc.get("pl_no") or f"PL-{uuid.uuid4().hex[:8].upper()}"
            amount = 0.0
            if db is not None:
                from app.services.trade_fulfillment_store import persist_invoice

                doc["invoice_persisted"] = persist_invoice(
                    db,
                    invoice_no=str(doc_no),
                    tenant_id=tenant_id,
                    order_id=order_id,
                    invoice_type="packing_list",
                    buyer_name=buyer.get("name"),
                    amount=0,
                    currency=currency,
                    status="draft",
                )
    except Exception as exc:  # noqa: BLE001
        logger.exception("native generate_trade_document failed type=%s", doc_type)
        return {"success": False, "error": f"{type(exc).__name__}: {exc}", "native": True, "doc_type": doc_type}

    return {
        "success": True,
        "native": True,
        "source": "youding_crm_native",
        "doc_type": doc_type,
        "doc_no": doc_no,
        "pi_number": doc.get("pi_no") if doc_type == "PI" else pi_no,
        "ci_number": doc.get("ci_no") if doc_type == "CI" else ci_no,
        "amount": amount,
        "currency": currency,
        "tenant_id": tenant_id,
        "order_id": order_id,
        "inquiry_id": inquiry_id,
        "bank_configured": bool((bank or {}).get("configured")),
        "document": doc,
        "markdown": doc.get("markdown"),
        "invoice_persisted": doc.get("invoice_persisted"),
        "note": "优丁 CRM 原生单证；银行账户未配置时不编造账号",
    }


def sync_fulfillment_stage(
    *,
    tenant_id: Optional[str],
    order_id: Optional[str],
    stage: str,
    step_number: int = 1,
    params: Optional[dict[str, Any]] = None,
    db: Optional[Session] = None,
) -> dict[str, Any]:
    params = dict(params or {})
    stage_key = (stage or "").strip().lower()
    target = _STAGE_TO_ORDER_STATUS.get(stage_key)
    result: dict[str, Any] = {
        "success": False,
        "native": True,
        "stage": stage_key,
        "step_number": step_number,
        "order_id": order_id,
        "tenant_id": tenant_id,
    }
    if not order_id:
        return {**result, "error": "order_id_required"}
    if db is None:
        return {**result, "error": "db_required"}

    from app.models.order import Order
    from app.services.trade_fulfillment_store import (
        ensure_default_pipeline,
        persist_contact_event,
    )

    order = db.query(Order).filter(Order.id == str(order_id)).first()
    if not order:
        order = db.query(Order).filter(Order.order_number == str(order_id)).first()
    if not order:
        return {**result, "error": f"order_not_found:{order_id}"}

    oid = str(order.id)
    result["order_number"] = order.order_number
    result["current_status"] = _status_val(order.status)

    if target:
        current = _status_val(order.status)
        if current != target:
            path = _status_path(current, target)
            if path is None:
                result["transition_skipped"] = f"{current}->{target} 不在订单状态机可达路径"
            else:
                try:
                    order.status = target
                    db.commit()
                    db.refresh(order)
                    result["transition_path"] = path

                    # 挂接经验环 (Evolution Engine)：履约里程碑沉淀
                    if target in ("completed", "confirmed", "final_payment_received"):
                        try:
                            from app.services.acquisition.experience_feed import record_ops_win
                            record_ops_win(
                                db,
                                tenant_id=str(getattr(order, "tenant_id", "") or tenant_id or ""),
                                inquiry_id=str(getattr(order, "inquiry_id", "") or order.order_number or ""),
                                amount=float(getattr(order, "total_amount", 0.0) or 0.0),
                                currency=str(getattr(order, "currency", "USD") or "USD"),
                                note=f"GoodJob 履约状态推进至 {target}",
                            )
                        except Exception:
                            pass
                except Exception as exc:  # noqa: BLE001
                    db.rollback()
                    return {**result, "error": f"order_update_failed:{exc}"}
        result["status"] = _status_val(order.status)
    else:
        result["status"] = result["current_status"]
        result["note"] = f"stage={stage_key!r} 无订单状态映射，仅记触点/管线"

    persist_contact_event(
        db,
        tenant_id=str(getattr(order, "tenant_id", "") or tenant_id or "") or None,
        channel="internal",
        event_type="fulfillment_stage",
        direction="internal",
        summary=f"step={step_number} stage={stage_key} status={result.get('status')}",
        payload={"order_id": oid, "stage": stage_key},
    )
    result["pipeline"] = ensure_default_pipeline(
        db, tenant_id=str(getattr(order, "tenant_id", "") or tenant_id or "") or None
    )
    result["success"] = True
    result["note"] = f"外贸7步履约第 {step_number} 步 [{stage_key}] 已写入优丁 PG（本项目 CRM）"
    return result


def sync_lead(
    *,
    tenant_id: Optional[str],
    lead_data: dict[str, Any],
    db: Optional[Session] = None,
) -> dict[str, Any]:
    required = ("company_name", "contact_name", "email")
    missing = [f for f in required if not (lead_data or {}).get(f)]
    if missing:
        return {"success": False, "lead_id": None, "error": f"缺少必填字段: {missing}", "native": True}
    if db is None:
        return {"success": False, "lead_id": None, "error": "db_required", "native": True}

    from app.models.inquiry import Inquiry
    from app.models.opportunity import Opportunity
    from app.services.trade_fulfillment_store import persist_contact_event

    company = str(lead_data["company_name"])
    contact = str(lead_data["contact_name"])
    email = str(lead_data["email"])
    phone = str(lead_data.get("phone") or "")
    country = str(lead_data.get("country") or "")
    source = str(lead_data.get("source") or "youding_crm")
    inquiry_id = str(lead_data.get("inquiry_id") or "")

    try:
        inquiry_uuid = str(uuid.UUID(inquiry_id)) if inquiry_id else None
    except ValueError:
        inquiry_uuid = None

    if not inquiry_uuid:
        cols = {c.key for c in Inquiry.__table__.columns}
        kwargs = {
            "id": str(uuid.uuid4()),
            "name": contact or company,
            "email": email,
            "phone": phone or None,
            "product": str(lead_data.get("product") or ""),
            "message": str(lead_data.get("message") or f"CRM lead sync: {company}"),
            "status": "pending",
            "is_active": True,
            "source_channel": source,
            "tenant_id": str(tenant_id or "") or None,
        }
        if "company_name" in cols:
            kwargs["company_name"] = company
        if "country" in cols:
            kwargs["country"] = country
        inquiry = Inquiry(**{k: v for k, v in kwargs.items() if k in cols})
        db.add(inquiry)
        db.commit()
        db.refresh(inquiry)
        inquiry_uuid = str(inquiry.id)

    opp = Opportunity(
        id=str(uuid.uuid4()),
        name=f"{company} · {contact}",
        company=company,
        contact_name=contact,
        contact_email=email,
        country=country or None,
        stage="prospecting",
        probability=10,
        tenant_id=str(tenant_id or "") or None,
        source=source,
        notes=str(lead_data.get("extra") or ""),
    )
    db.add(opp)
    db.commit()
    db.refresh(opp)

    persist_contact_event(
        db,
        tenant_id=str(tenant_id or "") or None,
        channel="crm",
        event_type="lead_sync",
        direction="internal",
        summary=f"{company}/{contact} <{email}>",
        inquiry_id=inquiry_uuid,
        lead_id=str(opp.id),
        payload={"source": source, "country": country},
    )

    return {
        "success": True,
        "native": True,
        "lead_id": str(opp.id),
        "inquiry_id": inquiry_uuid,
        "opportunity_id": str(opp.id),
        "error": None,
        "note": "线索已写入优丁 PG（本项目 CRM）",
    }


def update_opportunity(
    *,
    opportunity_id: str,
    status: str,
    tenant_id: Optional[str] = None,
    db: Optional[Session] = None,
) -> dict[str, Any]:
    status_key = (status or "").strip().lower()
    stage = _OPP_STAGE_MAP.get(status_key, status_key)
    if stage not in set(_OPP_STAGE_MAP.values()):
        return {
            "success": False,
            "error": f"非法状态 {status_key!r}，合法值: {sorted(set(_OPP_STAGE_MAP))}",
            "native": True,
        }
    if not opportunity_id:
        return {"success": False, "error": "opportunity_id 不能为空", "native": True}
    if db is None:
        return {"success": False, "error": "db_required", "native": True}

    from app.models.opportunity import Opportunity, OpportunityStage as OppStageRow

    try:
        oid = str(uuid.UUID(str(opportunity_id)))
    except ValueError:
        oid = str(opportunity_id)

    opp = db.query(Opportunity).filter(Opportunity.id == oid).first()
    if not opp:
        return {"success": False, "error": f"opportunity_not_found:{opportunity_id}", "native": True}
    if tenant_id and getattr(opp, "tenant_id", None) and str(opp.tenant_id) != str(tenant_id):
        return {"success": False, "error": "tenant_mismatch", "native": True}

    old = opp.stage
    opp.stage = stage
    try:
        db.add(
            OppStageRow(
                id=str(uuid.uuid4()),
                opportunity_id=str(opp.id),
                stage=stage,
                notes=f"native sync {old}->{stage}",
            )
        )
        db.commit()
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        return {"success": False, "error": f"{type(exc).__name__}: {exc}", "native": True}

    return {
        "success": True,
        "native": True,
        "opportunity_id": str(opp.id),
        "stage": stage,
        "previous_stage": old,
        "error": None,
    }
