"""PayPal 国际支付服务模块。"""

from __future__ import annotations

import logging
import os
import uuid
from typing import Any
from datetime import datetime, timezone

from sqlalchemy.orm import Session
from app.models.payment import PaymentOrder
from app.services.token_service import TokenService

logger = logging.getLogger(__name__)


class PayPalPayService:
    def __init__(self, db: Session, client_id: str | None = None, client_secret: str | None = None):
        self.db = db
        self.client_id = client_id or os.getenv("PAYPAL_CLIENT_ID", "")
        self.client_secret = client_secret or os.getenv("PAYPAL_CLIENT_SECRET", "")

    def create_order(
        self,
        tenant_id: str,
        amount_cents: int,
        currency: str = "USD",
        description: str = "AI Subscription",
    ) -> dict[str, Any]:
        now_str = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        rand_id = uuid.uuid4().hex[:8]
        order_no = f"PPL_{now_str}_{rand_id}"
        amount_float = round(amount_cents / 100.0, 2)
        curr = currency.upper()

        order = PaymentOrder(
            tenant_id=tenant_id,
            order_no=order_no,
            amount=amount_cents,
            currency=curr,
            channel="paypal",
            subject=description,
            status="pending",
        )
        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)

        paypal_order_id = f"PAYPAL_{uuid.uuid4().hex[:12]}"
        approve_url = f"https://www.sandbox.paypal.com/checkoutnow?token={paypal_order_id}&order={order_no}"
        return {
            "order_no": order_no,
            "paypal_order_id": paypal_order_id,
            "approve_url": approve_url,
            "amount": amount_float,
            "currency": curr,
        }

    def capture_order(self, order_no: str, paypal_order_id: str) -> bool:
        order = self.db.query(PaymentOrder).filter(PaymentOrder.order_no == order_no).first()
        if not order:
            return False

        if order.status == "paid":
            return True

        order.status = "paid"
        order.paid_at = datetime.now(timezone.utc)
        self.db.commit()

        try:
            tokens_to_add = max(100, int((order.amount / 100) * 100))
            token_svc = TokenService(self.db)
            token_svc.credit(
                tenant_id=str(order.tenant_id),
                amount=tokens_to_add,
                reason="paypal_payment_topup",
                reference_id=order.order_no,
            )
        except Exception:
            pass
        return True
