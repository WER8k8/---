# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""物流轨迹查询与订单回填。"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.order import Order
from app.models.user import User
from app.services.logistics_access import tenant_member_user_ids
from app.services.logistics_provider import fetch_tracking

_STATUS_MAP = {
    "picked_up": "confirmed",
    "in_transit": "shipped",
    "delivered": "completed",
    "exception": "shipped",
}


def fetch_tracking_payload(
    tracking_number: str,
    carrier: str | None = None,
) -> dict[str, Any]:
    """fetch_tracking_payload。

    参数说明：
    :param tracking_number: 参数 tracking_number
    :param carrier: 参数 carrier
    :return: 返回处理结果。
    """
    return fetch_tracking(tracking_number, carrier)


def _parse_estimated_delivery(iso_str: str | None) -> datetime | None:
    """_parse_estimated_delivery。

    参数说明：
    :param iso_str: 参数 iso_str
    :return: 返回处理结果。
    """
    if not iso_str:
        return None
    try:
        return datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    except ValueError:
        return None


def sync_order_from_tracking(
    db: Session,
    order: Order,
    *,
    carrier: str | None = None,
) -> dict[str, Any]:
    """按订单运单号拉轨迹并写回订单状态。"""
    if not order.tracking_number:
        raise ValueError("订单未填写运单号")
    payload = fetch_tracking_payload(order.tracking_number, carrier)
    ship_status = payload.get("status") or "in_transit"
    order.status = _STATUS_MAP.get(ship_status, order.status or "shipped")
    eta = _parse_estimated_delivery(payload.get("estimated_delivery"))
    if eta:
        order.estimated_delivery = eta
    db.add(order)
    db.commit()
    db.refresh(order)
    return {
        "order_id": str(order.id),
        "order_number": order.order_number,
        "order_status": order.status,
        "tracking": payload,
    }


def get_order_for_user(db: Session, order_id: UUID, user: User) -> Order | None:
    """get_order_for_user。

    参数说明：
    :param db: 参数 db
    :param order_id: 参数 order_id
    :param user: 参数 user
    :return: 返回处理结果。
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        return None
    member_ids = tenant_member_user_ids(db, user)
    if member_ids is None:
        return order
    if str(order.buyer_id) in member_ids or str(order.merchant_id) in member_ids:
        return order
    return None
