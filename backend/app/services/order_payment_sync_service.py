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
    if auto_confirm and status == "paid" and order.status == "pending":
        order.status = "confirmed"
    db.commit()
    db.refresh(order)
    return {
        "id": str(order.id),
        "order_number": order.order_number,
        "status": order.status,
        "payment_status": order.payment_status,
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
