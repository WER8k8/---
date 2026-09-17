# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""国际支付路由模块。"""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Header, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.stripe_pay_service import StripePayService
from app.services.paypal_pay_service import PayPalPayService

router = APIRouter(prefix="/payments/international", tags=["International Payments"])

ROUTE_PREFIX = ""
ROUTE_TAGS = ["International Payments"]


class StripeCheckoutRequest(BaseModel):
    tenant_id: str = Field(..., description="租户 ID")
    amount_cents: int = Field(..., ge=100, description="支付金额（分）")
    currency: str = Field(default="usd", description="币种代码")
    product_name: str = Field(default="AI SaaS Plan", description="商品描述")


class PayPalCreateRequest(BaseModel):
    tenant_id: str = Field(..., description="租户 ID")
    amount_cents: int = Field(..., ge=100, description="支付金额（分）")
    currency: str = Field(default="USD", description="币种代码")
    description: str = Field(default="SaaS Token Subscription", description="商品描述")


class PayPalCaptureRequest(BaseModel):
    order_no: str = Field(..., description="本地商户订单号")
    paypal_order_id: str = Field(..., description="PayPal 返回的 Order ID")


@router.post("/stripe/checkout", summary="创建 Stripe Checkout 会话")
def create_stripe_checkout(req: StripeCheckoutRequest, db: Session = Depends(get_db)) -> dict[str, Any]:
    svc = StripePayService(db)
    res = svc.create_checkout_session(
        tenant_id=req.tenant_id,
        amount_cents=req.amount_cents,
        currency=req.currency,
        product_name=req.product_name,
    )
    return {"code": 0, "msg": "ok", "data": res}


@router.post("/stripe/webhook", summary="接收 Stripe Webhook 回调通知")
async def stripe_webhook(
    request: Request,
    stripe_signature: str | None = Header(None, alias="Stripe-Signature"),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    body = await request.body()
    svc = StripePayService(db)
    if stripe_signature and not svc.verify_webhook_signature(body, stripe_signature):
        raise HTTPException(status_code=400, detail="Stripe 签名校验失败")
    try:
        data = await request.json()
    except Exception:
        data = {}
    svc.handle_checkout_completed(data)
    return {"status": "success"}


@router.post("/paypal/create", summary="创建 PayPal 订单")
def create_paypal_order(req: PayPalCreateRequest, db: Session = Depends(get_db)) -> dict[str, Any]:
    svc = PayPalPayService(db)
    res = svc.create_order(
        tenant_id=req.tenant_id,
        amount_cents=req.amount_cents,
        currency=req.currency,
        description=req.description,
    )
    return {"code": 0, "msg": "ok", "data": res}


@router.post("/paypal/capture", summary="捕获并确认 PayPal 订单结算")
def capture_paypal_order(req: PayPalCaptureRequest, db: Session = Depends(get_db)) -> dict[str, Any]:
    svc = PayPalPayService(db)
    ok = svc.capture_order(req.order_no, req.paypal_order_id)
    if not ok:
        raise HTTPException(status_code=400, detail="PayPal 结算确认失败")
    return {"code": 0, "msg": "PayPal 结算成功", "data": {"order_no": req.order_no, "status": "paid"}}
