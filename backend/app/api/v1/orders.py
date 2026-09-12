"""
Orders API Router - 订单API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from app.core.database import get_db
from app.core.response import success_response
from app.models.order import Order
from app.models.enums import OrderStatus, VALID_ORDER_STATUSES, validate_status
from app.services.logistics_tracking_service import sync_order_from_tracking


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = "/orders"
ROUTE_TAGS = ["订单管理"]

router = APIRouter(tags=["orders"])


# ── ORCH-08/09 状态白名单校验 ──────────────────────────────────────────────
_VALID_ORDER_STATUSES: frozenset = VALID_ORDER_STATUSES


def _validate_order_status(status: str) -> str:
    """校验订单状态是否合法（ORCH-08/09）"""
    ok, msg = validate_status(status, _VALID_ORDER_STATUSES, "订单状态")
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return status


class TrackingNumberUpdate(BaseModel):
    tracking_number: str = Field(..., min_length=3, max_length=100)
    carrier: Optional[str] = None


class PaymentStatusUpdate(BaseModel):
    payment_status: str = Field(..., pattern="^(unpaid|partial|paid|refunded)$")
    auto_confirm: bool = True


@router.post("/", response_model=dict)
def create_order(
    buyer_id: str,
    merchant_id: str,
    total_amount: float,
    currency: str = "USD",
    quote_id: Optional[str] = None,
    shipping_address: Optional[str] = None,
    shipping_method: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """创建订单"""
    try:
        import random
        import string
        order_number = "ORD-" + "".join(random.choices(string.digits, k=10))
        order = Order(
            buyer_id=uuid.UUID(buyer_id),
            merchant_id=uuid.UUID(merchant_id),
            quote_id=uuid.UUID(quote_id) if quote_id else None,
            order_number=order_number,
            total_amount=total_amount,
            currency=currency,
            shipping_address=shipping_address,
            shipping_method=shipping_method,
        )
        db.add(order)
        db.commit()
        db.refresh(order)
        return success_response(data={"id": str(order.id), "order_number": order.order_number, "status": order.status})
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{order_id}", response_model=dict)
def get_order(order_id: str, db: Session = Depends(get_db)):
    """获取订单详情"""
    order = db.query(Order).filter(Order.id == uuid.UUID(order_id)).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return success_response(data={
        "id": str(order.id),
        "order_number": order.order_number,
        "buyer_id": str(order.buyer_id),
        "merchant_id": str(order.merchant_id),
        "total_amount": float(order.total_amount),
        "currency": order.currency,
        "status": order.status,
        "payment_status": order.payment_status,
        "shipping_address": order.shipping_address,
        "tracking_number": order.tracking_number,
        "created_at": order.created_at.isoformat() if order.created_at else None,
    })


@router.patch("/{order_id}/payment-status")
def update_order_payment_status(
    order_id: str,
    body: PaymentStatusUpdate,
    db: Session = Depends(get_db),
):
    """七步⑥：订单支付状态联动（支付回调或后台可写）。"""
    from app.services.order_payment_sync_service import update_order_payment_status as sync_pay
    try:
        data = sync_pay(
            db,
            order_id,
            body.payment_status,
            auto_confirm=body.auto_confirm,
        )
        return data
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.put("/{order_id}/status", response_model=dict)
def update_order_status(
    order_id: str,
    status: str,  # pending/confirmed/shipped/completed/cancelled
    db: Session = Depends(get_db)
):
    """更新订单状态（ORCH-08/09: 白名单校验）"""
    order = db.query(Order).filter(Order.id == uuid.UUID(order_id)).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # ORCH-08: 白名单校验，拒绝非法状态
    validated_status = _validate_order_status(status)
    order.status = validated_status
    db.commit()
    db.refresh(order)
    return success_response(data={"id": str(order.id), "status": order.status})


@router.get("/", response_model=List[dict])
def list_orders(
    buyer_id: Optional[str] = None,
    merchant_id: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """列出订单（支持过滤）"""
    query = db.query(Order)
    if buyer_id:
        query = query.filter(Order.buyer_id == uuid.UUID(buyer_id))
    if merchant_id:
        query = query.filter(Order.merchant_id == uuid.UUID(merchant_id))
    if status:
        query = query.filter(Order.status == status)
    
    orders = query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()
    return [
        {
            "id": str(o.id),
            "order_number": o.order_number,
            "status": o.status,
            "payment_status": o.payment_status,
            "total_amount": float(o.total_amount),
            "currency": o.currency,
            "tracking_number": o.tracking_number,
            "created_at": o.created_at.isoformat() if o.created_at else None,
        }
        for o in orders
    ]


@router.patch("/{order_id}/tracking")
def update_order_tracking(
    order_id: str,
    body: TrackingNumberUpdate,
    db: Session = Depends(get_db),
):
    """填写/更新运单号，可选立即同步物流轨迹。"""
    order = db.query(Order).filter(Order.id == uuid.UUID(order_id)).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    order.tracking_number = body.tracking_number.strip()
    db.commit()
    db.refresh(order)
    result = {"id": str(order.id), "tracking_number": order.tracking_number}
    if body.carrier is not None:
        try:
            synced = sync_order_from_tracking(db, order, carrier=body.carrier or None)
            result["sync"] = synced
        except ValueError as exc:
            result["sync_error"] = str(exc)
    return success_response(data=result)
