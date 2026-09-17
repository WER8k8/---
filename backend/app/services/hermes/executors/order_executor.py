# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Order Executor Plugin for Hermes Orchestration.

把既有 order services（order_addon_service / order_payment_sync_service）
包成 ExecutorRegistry 插件，使业务链订单履约环节可被任务图调度。

契约：
    node.executor   = "order"
    node.capability = "order.create" | "order.sync" | "default"
    node.input      = { order_id?, product_id?, quantity?, status? }
"""
from __future__ import annotations

import logging
import secrets
import uuid
from typing import Any, Dict

from app.schemas.hermes_orchestration import ExecutorResult, TaskNode

from .base import BaseExecutor, ExecutorContext, ExecutorRegistry

logger = logging.getLogger(__name__)

_SUPPORTED_CAPABILITIES = frozenset({"order.create", "order.sync", "default"})


class OrderExecutor(BaseExecutor):
    """订单执行器：创建/同步订单状态。"""

    @classmethod
    def get_executor_name(cls) -> str:
        return "order"

    async def run(self, node: TaskNode, context: ExecutorContext) -> ExecutorResult:
        capability = (node.capability or "default").strip()
        if capability not in _SUPPORTED_CAPABILITIES:
            return ExecutorResult(
                node_id=node.id,
                status="skipped",
                output={},
                error=f"order 不支持 capability={capability!r}",
            )

        params: dict[str, Any] = dict(node.input or {})

        try:
            if capability == "order.sync":
                from app.services.order_payment_sync_service import update_order_payment_status

                order_id = str(params.get("order_id") or "").strip()
                if not order_id:
                    return ExecutorResult(node_id=node.id, status="failed", output={}, error="missing_order_id")
                result = update_order_payment_status(
                    context.db,
                    order_id,
                    str(params.get("payment_status") or "paid").lower(),
                )
            else:
                from app.models.enums import OrderStatus, PaymentStatus
                from app.models.order import Order, OrderItem
                from app.models.product import Product

                buyer_id = str(params.get("buyer_id") or "").strip()
                merchant_id = str(params.get("merchant_id") or "").strip()
                product_id = str(params.get("product_id") or params.get("item_id") or "").strip()
                if not (buyer_id and merchant_id and product_id):
                    return ExecutorResult(
                        node_id=node.id,
                        status="failed",
                        output={},
                        error="missing_buyer_id_or_merchant_id_or_product_id",
                    )
                product = context.db.query(Product).filter(Product.id == str(uuid.UUID(product_id))).first()
                if not product:
                    return ExecutorResult(node_id=node.id, status="failed", output={}, error="product_not_found")
                price = float(params.get("price") or 0)
                quantity = int(params.get("quantity") or 1)
                order = Order(
                    tenant_id=context.tenant_id,
                    buyer_id=str(uuid.UUID(buyer_id)),
                    merchant_id=str(uuid.UUID(merchant_id)),
                    order_number=f"ORD{uuid.uuid4().hex[:12].upper()}",
                    total_amount=price * quantity,
                    currency=str(params.get("currency") or "USD"),
                    status=OrderStatus.PENDING,
                    payment_status=PaymentStatus.PENDING,
                    access_token=secrets.token_hex(32),
                )
                context.db.add(order)
                context.db.flush()
                context.db.add(
                    OrderItem(
                        order_id=order.id,
                        product_id=str(uuid.UUID(product_id)),
                        quantity=quantity,
                        unit_price=price,
                        total_price=price * quantity,
                    )
                )
                context.db.commit()
                result = {"order_id": str(order.id), "order_number": order.order_number, "status": "pending", "access_token": order.access_token}
        except (ImportError, AttributeError) as exc:
            return ExecutorResult(
                node_id=node.id,
                status="failed",
                output={},
                error=f"order service 未落地: {type(exc).__name__}: {exc}",
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("OrderExecutor 执行失败 node=%s", node.id)
            return ExecutorResult(node_id=node.id, status="failed", output={}, error=f"{type(exc).__name__}: {exc}")

        output = dict(result or {})
        output["executor"] = "order"
        output["capability"] = capability
        return ExecutorResult(node_id=node.id, status="succeeded", output=output)

    @classmethod
    def get_capabilities(cls) -> Dict[str, Dict[str, Any]]:
        return {
            "order.create": {
                "desc": "创建订单/加购（product_id + quantity）",
                "input": ["product_id", "quantity", "tenant_id"],
                "output": ["order_id", "status"],
                "cost": {"tokens": 0, "seconds": 3},
                "needs_approval": False,
            },
            "order.sync": {
                "desc": "订单支付状态同步",
                "input": ["order_id"],
                "output": ["payment_status", "synced_at"],
                "cost": {"tokens": 0, "seconds": 5},
                "needs_approval": False,
            },
        }


ExecutorRegistry.register(OrderExecutor())
