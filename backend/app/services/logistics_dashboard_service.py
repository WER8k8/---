# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""物流看板 — 基于真实订单聚合（P1-09 / P2-06）。"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.order import Order
from app.models.user import User
from app.services.logistics_access import tenant_member_user_ids

_UI_STATUS = {
    "pending": "pending",
    "confirmed": "pending",
    "shipped": "intransit",
    "completed": "delivered",
    "cancelled": "cancelled",
}


def _orders_query(db: Session, user: User):
    """_orders_query。

    参数说明：
    :param db: 参数 db
    :param user: 参数 user
    :return: 返回处理结果。
    """
    q = db.query(Order)
    member_ids = tenant_member_user_ids(db, user)
    if member_ids is None:
        return q
    return q.filter(
        (Order.buyer_id.in_(member_ids)) | (Order.merchant_id.in_(member_ids))
    )


def build_logistics_overview(db: Session, user: User) -> dict[str, Any]:
    """build_logistics_overview。

    参数说明：
    :param db: 参数 db
    :param user: 参数 user
    :return: 返回处理结果。
    """
    base = _orders_query(db, user)
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    with_tracking = base.filter(Order.tracking_number.isnot(None))
    in_transit = with_tracking.filter(Order.status.in_(("shipped", "confirmed"))).count()
    delivered = with_tracking.filter(Order.status == "completed").count()
    pending_ship = with_tracking.filter(Order.status == "pending").count()
    total_with_tracking = with_tracking.count()
    no_tracking = base.filter(
        (Order.tracking_number.is_(None)) | (Order.tracking_number == "")
    ).count()
    today_orders = base.filter(Order.created_at >= today_start).count()
    amount_rows = (
        base.with_entities(Order.total_amount)
        .all()
    )
    amounts = [float(a[0] or 0) for a in amount_rows if a[0] is not None]
    avg_amount = round(sum(amounts) / len(amounts), 2) if amounts else 0.0
    sum_amount = round(sum(amounts), 2) if amounts else 0.0
    recent = base.order_by(Order.updated_at.desc()).limit(30).all()
    orders_payload = []
    for o in recent:
        ui_status = _UI_STATUS.get(o.status or "pending", "pending")
        if not o.tracking_number and ui_status == "pending":
            ui_status = "pending"
        orders_payload.append(
            {
                "id": str(o.id),
                "no": o.tracking_number or o.order_number,
                "order_number": o.order_number,
                "from": (o.shipping_address or "—")[:40],
                "to": o.shipping_method or "—",
                "cargo": o.shipping_method or "建材",
                "price": float(o.total_amount or 0),
                "status": ui_status,
                "raw_status": o.status,
                "has_tracking": bool(o.tracking_number),
                "eta": (
                    o.estimated_delivery.strftime("%Y-%m-%d")
                    if o.estimated_delivery
                    else "—"
                ),
                "payment_status": o.payment_status,
            }
        )

    return {
        "active_shipments": in_transit,
        "today_quotations": today_orders,
        "total_routes": len({o.shipping_method for o in recent if o.shipping_method}),
        "avg_freight_cost": avg_amount,
        "freight_total": sum_amount,
        "orders_without_tracking": no_tracking,
        "stats": [
            {"l": "在途运单", "v": in_transit, "c": "#1890ff"},
            {"l": "有单号订单", "v": total_with_tracking, "c": "#52c41a"},
            {"l": "今日新单", "v": today_orders, "c": "#722ed1"},
            {"l": "待填运单", "v": no_tracking, "c": "#fa8c16"},
        ],
        "freight_stats": [
            {
                "title": "在途运单",
                "value": str(in_transit),
                "sub": "shipped/confirmed",
                "color": "#1890ff",
            },
            {
                "title": "待发运单",
                "value": str(pending_ship),
                "sub": "已填单号待发货",
                "color": "#faad14",
            },
            {
                "title": "平均订单额",
                "value": f"¥{avg_amount:,.0f}",
                "sub": f"合计 ¥{sum_amount:,.0f}",
                "color": "#52c41a",
            },
        ],
        "orders": orders_payload,
        "data_source": "orders_table",
    }
