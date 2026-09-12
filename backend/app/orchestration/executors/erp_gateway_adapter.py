"""ERP_BACKEND 插槽适配器：复用订单真相，不虚构库存。"""

from __future__ import annotations

from typing import Any, Mapping

from sqlalchemy.orm import Session

from app.models.order import Order
from app.orchestration.interfaces import ErpConnector, SlotArchetype


class OrderNotFoundError(LookupError):
    """指定订单不存在。"""


class ErpGatewayAdapter(ErpConnector):
    """当前无真实 ERP 供应商；仅提供订单真相与履约投影查询。"""

    archetype = SlotArchetype.ERP_BACKEND

    def __init__(self, db: Session) -> None:
        self._db = db

    def push_order(self, tenant_id: str, order_payload: Mapping[str, Any]) -> str:
        order_number = str(order_payload.get("order_number") or "").strip()
        if not tenant_id.strip():
            raise ValueError("tenant_id 不能为空")
        if not order_number:
            raise ValueError("order_payload 缺 order_number")

        order = (
            self._db.query(Order)
            .filter(Order.order_number == order_number, Order.tenant_id == tenant_id)
            .first()
        )
        if order is None:
            raise OrderNotFoundError(f"租户 {tenant_id} 不存在订单: {order_number}")
        return str(order.order_number)

    def pull_inventory(self, tenant_id: str, skus: tuple[str, ...]) -> Mapping[str, Any]:
        if not tenant_id.strip():
            raise ValueError("tenant_id 不能为空")
        return {
            "status": "not_configured",
            "reason": "当前系统无真实 ERP 库存模型，不返回虚构库存",
            "skus": list(skus),
        }

    def pull_fulfillment_status(
        self, tenant_id: str, external_refs: tuple[str, ...]
    ) -> Mapping[str, Any]:
        if not tenant_id.strip():
            raise ValueError("tenant_id 不能为空")

        items: list[dict[str, Any]] = []
        for external_ref in external_refs:
            order = (
                self._db.query(Order)
                .filter(Order.order_number == external_ref, Order.tenant_id == tenant_id)
                .first()
            )
            items.append(
                {
                    "external_ref": external_ref,
                    "status": order.status if order else "not_found",
                    "tracking_number": order.tracking_number if order else None,
                }
            )
        return {"items": items}


__all__ = ["ErpGatewayAdapter", "OrderNotFoundError"]
