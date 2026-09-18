# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""B2B 订单支付状态联动。"""

from __future__ import annotations

import json
import uuid
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.order import Order

_VALID = frozenset({"unpaid", "partial", "paid", "refunded"})


def update_order_payment_status(
    db: Session,
    order_id: str,
    payment_status: str,
    *,
    auto_confirm: bool = True,
) -> dict[str, Any]:
    """update_order_payment_status。

    参数说明：
    :param db: 参数 db
    :param order_id: 参数 order_id
    :param payment_status: 参数 payment_status
    :param auto_confirm: 参数 auto_confirm
    :return: 返回处理结果。
    """
    status = (payment_status or "").strip().lower()
    if status not in _VALID:
        raise ValueError(f"payment_status 须为 {sorted(_VALID)}")

    oid_str = str(uuid.UUID(str(order_id)))  # 验证格式后使用字符串，兼容SQLite
    order = db.query(Order).filter(Order.id == oid_str).first()
    if not order:
        raise ValueError("订单不存在")

    order.payment_status = status
    if auto_confirm:
        if status == "partial":
            if order.status in ("pending", "confirmed"):
                order.status = "deposit_received"
        elif status == "paid":
            if order.status == "pending":
                order.status = "confirmed"
            elif order.status == "deposit_received":
                order.status = "in_production"
            elif order.status == "shipped":
                order.status = "final_payment_received"
    db.commit()
    db.refresh(order)
    # P0-1 写路径：业务收款落库 payments（与平台 payment_orders 分账）
    payment_persist = {"persisted": False, "reason": "skipped"}
    try:
        from app.services.trade_fulfillment_store import persist_business_payment

        pay_status = {
            "unpaid": "pending",
            "partial": "received",
            "paid": "confirmed",
            "refunded": "refunded",
        }.get(status, "pending")
        amount = 0.0
        try:
            amount = float(getattr(order, "deposit_amount", 0) or 0) if status == "partial" else float(
                getattr(order, "total_amount", 0) or 0
            )
        except (TypeError, ValueError):
            amount = 0.0
        payment_persist = persist_business_payment(
            db,
            amount=amount,
            tenant_id=str(getattr(order, "tenant_id", "") or "") or None,
            order_id=str(order.id),
            currency=str(getattr(order, "currency", "USD") or "USD"),
            method="platform",
            status=pay_status,
            reference_no=order.order_number,
            notes=f"order_payment_status={status}",
        )
    except Exception as exc:  # noqa: BLE001
        payment_persist = {"persisted": False, "error": str(exc)}
    return {
        "id": str(order.id),
        "order_number": order.order_number,
        "status": order.status,
        "payment_status": order.payment_status,
        "payment_persisted": payment_persist,
    }


def sync_b2b_from_payment_notify(db: Session, data: dict) -> Optional[dict[str, Any]]:
    """支付网关回调 data 中含 business_order_id 或 attach JSON 时联动 B2B 订单。"""
    b2b_id = data.get("business_order_id") or data.get("order_id")
    attach = data.get("attach")
    if not b2b_id and attach:
        try:
            parsed = json.loads(attach) if isinstance(attach, str) and attach.startswith("{") else (
                attach if isinstance(attach, dict) else {}
            )
            b2b_id = parsed.get("business_order_id") or parsed.get("order_id")
        except (json.JSONDecodeError, TypeError):
            b2b_id = None
    if not b2b_id:
        return None
    try:
        return update_order_payment_status(db, str(b2b_id), "paid")
    except ValueError:
        return None
