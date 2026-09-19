# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""
Orders API Router - 订单API
鉴权模型（order-token + 登录态双因子）：
  - 买家（匿名）：凭订单访问令牌（X-Order-Token 头 / order_token 参数）查询、取消、确认收货自己的订单
  - 卖家/管理员：登录态（Bearer）放行，买家不可改支付/运单
  - 无任何凭据 → 读 404（防枚举）、列表 400、写 403
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import hmac
import secrets
import uuid

from app.core.database import get_db
from app.core.response import error_response, success_response
from app.core.security import get_current_user, get_current_user_optional
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.user import User
from app.models.enums import OrderStatus, PaymentStatus, VALID_ORDER_STATUSES, validate_status
from app.services.logistics_tracking_service import sync_order_from_tracking
from app.services.foreign_trade.trade_document_service import (
    build_proforma_invoice,
    build_commercial_invoice,
    build_packing_list,
    build_certificate_of_origin,
    build_split_shipment_documents,
    build_credit_note,
)
from app.services.foreign_trade.trade_document_export_service import (
    build_trade_document_html,
    build_trade_document_docx,
)


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = "/orders"
ROUTE_TAGS = ["订单管理"]

router = APIRouter(tags=["orders"])

_ADMIN_ROLES = frozenset({"admin", "super_admin"})


# ── ORCH-08/09 状态白名单校验 ──────────────────────────────────────────────
_VALID_ORDER_STATUSES: frozenset = VALID_ORDER_STATUSES


def _validate_order_status(status: str) -> str:
    """校验订单状态是否合法（ORCH-08/09）"""
    ok, msg = validate_status(status, _VALID_ORDER_STATUSES, "订单状态")
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return status


def _order_token_of(request: Request) -> str:
    """从 X-Order-Token 头或 order_token query 参数取订单访问令牌。"""
    if request is None:
        return ""
    return (request.headers.get("X-Order-Token") or "").strip() or str(request.query_params.get("order_token") or "").strip()


def _sync_order_stage_to_goodjob(order: Order, stage: str, step_number: int, details: dict = None) -> None:
    """订单履约阶段写入**本项目 CRM**（优丁原生 PG；失败安全）。

    goodjob_crm = 优丁 CRM，默认不走外桥。
    """
    try:
        from app.core.database import SessionLocal
        from app.services.goodjob.native_fulfillment import sync_fulfillment_stage

        db = SessionLocal()
        try:
            sync_fulfillment_stage(
                tenant_id=str(getattr(order, "tenant_id", None) or "") or None,
                order_id=str(order.id),
                stage=stage,
                step_number=step_number,
                params={
                    "order_number": getattr(order, "order_number", ""),
                    "total_amount": float(getattr(order, "total_amount", 0.0) or 0.0),
                    "currency": getattr(order, "currency", "USD"),
                    "details": details or {},
                },
                db=db,
            )
        finally:
            db.close()
    except Exception:
        pass


def _num(value):
    return float(value) if value is not None else None


def _status_val(status) -> str:
    """提取状态字符串值，兼容 Enum 实例与原生字符串。"""
    if status is None:
        return ""
    return str(getattr(status, "value", status)).strip().lower()


def _can_access(order, user, token: str) -> bool:
    """放行：超管/平台管理员 / 订单买卖双方 / 持有该订单访问令牌（恒定时间比较）；跨租户严格阻断。"""
    if user is not None:
        uid = str(getattr(user, "id", ""))
        role = str(getattr(user, "role", "") or "")
        user_tid = str(getattr(user, "tenant_id", "") or "")
        order_tid = str(getattr(order, "tenant_id", "") or "")
        if role in _ADMIN_ROLES:
            return True
        if uid in {str(order.buyer_id), str(order.merchant_id)}:
            return True
        # 租户隔离强约束：非买卖双方且非平台管理员时，若订单与用户均有 tenant_id 且不一致，强阻断
        if order_tid and user_tid and order_tid != user_tid:
            return False
        if role in {"tenant_admin", "agent_admin"}:
            return True
        return False
    return bool(token) and bool(getattr(order, "access_token", None)) and hmac.compare_digest(token, order.access_token)


def _is_buyer_scope(order, user, token: str) -> bool:
    """请求者处于买家身份：持订单令牌（令牌仅随创建响应下发买家）或登录用户是订单 buyer 且不是卖家或管理员。"""
    if user is not None:
        role = str(getattr(user, "role", "") or "")
        uid = str(getattr(user, "id", ""))
        # 若是超管、平台管理员、租户管理员或订单的卖家，拥有卖家/履约方管理权限，非买家受限范围
        if role in _ADMIN_ROLES or role in {"tenant_admin", "agent_admin"} or uid == str(order.merchant_id):
            return False
        if uid == str(order.buyer_id):
            return True
        return False
    return bool(token) and bool(getattr(order, "access_token", None)) and hmac.compare_digest(token, order.access_token)



def _load_order(db: Session, order_id: str, user, token: str) -> Order:
    """按 id 取订单；不存在 → 404；已认证跨租户越权 → 403；未认证无令牌 → 404（防枚举）。"""
    try:
        oid = uuid.UUID(order_id)
    except (ValueError, TypeError, AttributeError):
        raise HTTPException(status_code=404, detail="Order not found")
    order = db.query(Order).filter(Order.id == oid).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if not _can_access(order, user, token):
        if user is not None:
            raise HTTPException(status_code=403, detail="Cross tenant order access denied")
        raise HTTPException(status_code=404, detail="Order not found")
    return order


class TrackingNumberUpdate(BaseModel):
    tracking_number: str = Field(..., min_length=3, max_length=100)
    carrier: Optional[str] = None


class PaymentStatusUpdate(BaseModel):
    payment_status: str = Field(..., pattern="^(unpaid|partial|paid|refunded)$")
    auto_confirm: bool = True


class TradeDetailsUpdate(BaseModel):
    """④定金核销 + ⑥发运单证数据：贸易条款 / 定金 / CI·箱单（卖家/管理员填）。"""
    incoterms: Optional[str] = None
    payment_terms: Optional[str] = None
    deposit_ratio: Optional[float] = None
    deposit_amount: Optional[float] = None
    port_of_loading: Optional[str] = None
    port_of_discharge: Optional[str] = None
    gross_weight: Optional[float] = None
    net_weight: Optional[float] = None
    volume: Optional[float] = None
    shipping_marks: Optional[str] = None
    container_no: Optional[str] = None
    bl_number: Optional[str] = None


class VerifyDepositRequest(BaseModel):
    """定金核销请求"""
    deposit_amount: Optional[float] = Field(None, description="实收定金金额")
    deposit_ratio: Optional[float] = Field(None, description="定金比例(%)")
    payment_reference: Optional[str] = Field(None, description="银行流水号/参考号")


class ProductionFollowupRequest(BaseModel):
    """生产跟单请求"""
    production_notes: Optional[str] = Field(None, description="生产排期/进度说明")
    estimated_delivery: Optional[str] = Field(None, description="预计交期 YYYY-MM-DD")


class DispatchShipmentRequest(BaseModel):
    """发货与提单绑定请求"""
    tracking_number: Optional[str] = Field(None, description="快递/货运单号")
    bl_number: Optional[str] = Field(None, description="海运提单号")
    container_no: Optional[str] = Field(None, description="集装箱号")
    carrier: Optional[str] = Field(None, description="承运商/船公司")
    gross_weight: Optional[float] = Field(None, description="总毛重(kg)")
    volume: Optional[float] = Field(None, description="总体积(CBM)")


class SettleBalanceRequest(BaseModel):
    """尾款核销请求"""
    balance_amount: Optional[float] = Field(None, description="实收尾款金额")
    payment_reference: Optional[str] = Field(None, description="银行电汇水单号")


class SplitShipmentRequest(BaseModel):
    """分批装运请求"""
    batch_index: int = Field(1, ge=1, description="批次序号")
    batch_lines: List[Dict[str, Any]] = Field(..., description="本批出运明细 [{description, quantity, unit_price}]")


class CreditNoteRequest(BaseModel):
    """单据冲红请求"""
    original_ci_no: str = Field(..., description="原商业发票号")
    credited_items: List[Dict[str, Any]] = Field(..., description="冲红明细 [{description, quantity, unit_price, reason}]")
    reason: str = Field("Defective goods compensation / Return adjustment", description="冲红原因")



@router.post("/", response_model=dict)
def create_order(
    buyer_id: str,
    merchant_id: str,
    total_amount: float,
    currency: str = "USD",
    quote_id: Optional[str] = None,
    shipping_address: Optional[str] = None,
    shipping_method: Optional[str] = None,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建订单（需登录；返回 access_token 供买家查询/操作）"""
    if getattr(user, "role", None) not in _ADMIN_ROLES:
        buyer_id = str(user.id)  # 非管理员禁止伪造买家（防订单冒名/数据污染）
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
            access_token=secrets.token_hex(32),
            tenant_id=str(getattr(user, "tenant_id", None) or ""),
        )
        db.add(order)
        db.commit()
        db.refresh(order)
        return success_response(data={
            "id": str(order.id),
            "order_number": order.order_number,
            "status": _status_val(order.status),
            "access_token": order.access_token,
        })
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{order_id}")
def get_order(
    order_id: str,
    request: Request = None,
    user=Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """获取订单详情（买家凭令牌 / 卖家与管理员凭登录态）"""
    order = _load_order(db, order_id, user, _order_token_of(request))
    return success_response(data={
        "id": str(order.id),
        "order_number": order.order_number,
        "buyer_id": str(order.buyer_id),
        "merchant_id": str(order.merchant_id),
        "total_amount": float(order.total_amount),
        "currency": order.currency,
        "status": _status_val(order.status),
        "payment_status": _status_val(order.payment_status),
        "shipping_address": order.shipping_address,
        "tracking_number": order.tracking_number,
        "created_at": order.created_at.isoformat() if order.created_at else None,
        "incoterms": order.incoterms,
        "payment_terms": order.payment_terms,
        "deposit_ratio": _num(order.deposit_ratio),
        "deposit_amount": _num(order.deposit_amount),
        "port_of_loading": order.port_of_loading,
        "port_of_discharge": order.port_of_discharge,
        "gross_weight": _num(order.gross_weight),
        "net_weight": _num(order.net_weight),
        "volume": _num(order.volume),
        "shipping_marks": order.shipping_marks,
        "container_no": order.container_no,
        "bl_number": order.bl_number,
    })


@router.patch("/{order_id}/payment-status")
def update_order_payment_status(
    order_id: str,
    body: PaymentStatusUpdate,
    request: Request = None,
    user=Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """七步⑥：订单支付状态联动（支付回调或卖家后台可写；买家无权）。"""
    order = _load_order(db, order_id, user, _order_token_of(request))
    if _is_buyer_scope(order, user, _order_token_of(request)):
        raise HTTPException(status_code=403, detail="买家无权修改支付状态")
    from app.services.order_payment_sync_service import update_order_payment_status as sync_pay
    try:
        return sync_pay(db, order_id, body.payment_status, auto_confirm=body.auto_confirm)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.put("/{order_id}/status", response_model=dict)
def update_order_status(
    order_id: str,
    status: str,  # pending/confirmed/shipped/completed/cancelled
    request: Request = None,
    user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """更新订单状态（ORCH-08/09: 白名单校验；买家仅可取消待处理订单）"""
    token = _order_token_of(request)
    order = _load_order(db, order_id, user, token)
    validated_status = _validate_order_status(status)
    if _is_buyer_scope(order, user, token) and not (
        _status_val(order.status) == "pending" and validated_status == "cancelled"
    ):
        raise HTTPException(status_code=403, detail="买家仅可取消待处理订单")
    order.status = validated_status
    db.commit()
    db.refresh(order)
    return success_response(data={"id": str(order.id), "status": order.status})


@router.get("", include_in_schema=False)
@router.get("/", response_model=List[dict])
def list_orders(
    request: Request = None,
    buyer_id: Optional[str] = None,
    merchant_id: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """列出订单：持令牌查自己订单；登录态查本人（管理员可全量+过滤）；无凭据拒绝。"""
    from sqlalchemy import or_
    token = _order_token_of(request)
    if user is None and not token:
        raise HTTPException(status_code=400, detail="查询订单需登录或提供订单访问令牌")
    query = db.query(Order)
    if token:
        query = query.filter(Order.access_token == token)
    else:
        role = str(getattr(user, "role", "") or "")
        if role in _ADMIN_ROLES:
            if buyer_id:
                query = query.filter(Order.buyer_id == uuid.UUID(buyer_id))
            if merchant_id:
                query = query.filter(Order.merchant_id == uuid.UUID(merchant_id))
        else:
            uid = str(user.id)
            query = query.filter(or_(Order.buyer_id == uuid.UUID(uid), Order.merchant_id == uuid.UUID(uid)))
    if status:
        query = query.filter(Order.status == status)

    orders = query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()
    return [
        {
            "id": str(o.id),
            "order_number": o.order_number,
            "status": _status_val(o.status),
            "payment_status": _status_val(o.payment_status),
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
    request: Request = None,
    user=Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """填写/更新运单号（卖家/管理员；买家无权），可选立即同步物流轨迹。"""
    token = _order_token_of(request)
    order = _load_order(db, order_id, user, token)
    if _is_buyer_scope(order, user, token):
        raise HTTPException(status_code=403, detail="买家无权填写运单号")
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


@router.put("/{order_id}/trade", response_model=dict)
def update_order_trade(
    order_id: str,
    body: TradeDetailsUpdate,
    request: Request = None,
    user=Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """④定金核销 + ⑥发运单证数据：卖家/管理员填贸易条款、定金、CI/箱单字段（买家无权）。

    未显式给 deposit_amount 但给了 deposit_ratio 时，按 total_amount × ratio 自动折算定金。
    """
    token = _order_token_of(request)
    order = _load_order(db, order_id, user, token)
    if _is_buyer_scope(order, user, token):
        raise HTTPException(status_code=403, detail="买家无权修改贸易履约数据")
    data = body.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(order, field, value)
    if data.get("deposit_ratio") is not None and "deposit_amount" not in data and order.total_amount:
        order.deposit_amount = round(float(order.total_amount) * float(data["deposit_ratio"]) / 100, 2)
    db.commit()
    db.refresh(order)
    return success_response(data={"id": str(order.id), "incoterms": order.incoterms, "deposit_amount": order.deposit_amount})


@router.post("/{order_id}/cancel")
def cancel_order(
    order_id: str,
    request: Request = None,
    user=Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """买家/卖家取消待处理订单（官网 [id].vue 在用端点）"""
    order = _load_order(db, order_id, user, _order_token_of(request))
    if _status_val(order.status) != "pending":
        raise HTTPException(status_code=400, detail="仅待处理订单可取消")
    order.status = OrderStatus.CANCELLED.value
    db.commit()
    db.refresh(order)
    return success_response(data={"id": str(order.id), "status": _status_val(order.status)})


@router.post("/{order_id}/confirm-receipt")
def confirm_receipt(
    order_id: str,
    request: Request = None,
    user=Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """买家确认收货（shipped → completed；官网 [id].vue 在用端点）"""
    order = _load_order(db, order_id, user, _order_token_of(request))
    if _status_val(order.status) != "shipped":
        raise HTTPException(status_code=400, detail="仅已发货订单可确认收货")
    order.status = OrderStatus.COMPLETED.value
    db.commit()
    db.refresh(order)
    return success_response(data={"id": str(order.id), "status": _status_val(order.status)})


# ── 外贸 7 步履约与单证自动化中枢 ──────────────────────────────────────────

def _extract_seller_buyer_lines(order: Order, db: Session):
    """从订单与其关联主体中提取卖方、买方与明细行结构。"""
    seller_user = db.query(User).filter(User.id == order.merchant_id).first() if order.merchant_id else None
    buyer_user = db.query(User).filter(User.id == order.buyer_id).first() if order.buyer_id else None

    seller = {
        "name": (seller_user.username if seller_user else None) or "YouDing Building Materials Tech Co., Ltd.",
        "address": "No. 88 Export Industrial Zone, Guangdong, China",
        "email": (seller_user.email if seller_user else None) or "export@youding.com",
    }
    buyer = {
        "name": (buyer_user.username if buyer_user else None) or "Global Trade Buyer",
        "company": (buyer_user.username if buyer_user else None) or "Global Trade Buyer Inc.",
        "address": order.shipping_address or "Overseas Delivery Terminal",
        "email": (buyer_user.email if buyer_user else None) or "buyer@trade.com",
    }

    # 读取订单明细行
    lines = []
    items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
    if items:
        for it in items:
            p_name = "Product"
            if it.product:
                p_name = it.product.name
            lines.append({
                "description": p_name,
                "quantity": float(it.quantity or 1),
                "unit": "pcs",
                "unit_price": float(it.unit_price or 0),
                "hs_code": "6802.91.00",
            })
    elif getattr(order, "quote", None) and getattr(order.quote, "items", None):
        for qi in order.quote.items:
            lines.append({
                "description": qi.product_name or "Product",
                "quantity": float(qi.quantity or 1),
                "unit": qi.unit or "pcs",
                "unit_price": float(qi.unit_price or 0),
                "hs_code": "6802.91.00",
            })
    else:
        lines.append({
            "description": "Standard Industrial Building Materials Pack",
            "quantity": 1.0,
            "unit": "lot",
            "unit_price": float(order.total_amount or 0.0),
            "hs_code": "6802.91.00",
        })
    return seller, buyer, lines


@router.post("/{order_id}/verify-deposit")
def verify_order_deposit(
    order_id: str,
    body: VerifyDepositRequest,
    request: Request = None,
    user=Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """外贸七步④：定金核销（待支付/已确认 → deposit_received，卖家/管理员操作）。"""
    token = _order_token_of(request)
    order = _load_order(db, order_id, user, token)
    if _is_buyer_scope(order, user, token):
        raise HTTPException(status_code=403, detail="买家无权核销定金")

    cur_status = _status_val(order.status)
    if cur_status not in ("pending", "confirmed", "paid"):
        raise HTTPException(status_code=400, detail=f"当前订单状态 '{cur_status}' 不支持定金核销")

    total = float(order.total_amount or 0.0)
    if body.deposit_ratio is not None:
        order.deposit_ratio = body.deposit_ratio
        order.deposit_amount = round(total * (body.deposit_ratio / 100.0), 2)
    elif body.deposit_amount is not None:
        order.deposit_amount = body.deposit_amount
        if total > 0:
            order.deposit_ratio = round((body.deposit_amount / total) * 100.0, 2)
    elif not order.deposit_amount and total > 0:
        # 默认 30% 定金核销
        order.deposit_ratio = 30.0
        order.deposit_amount = round(total * 0.3, 2)

    order.status = OrderStatus.DEPOSIT_RECEIVED.value
    order.payment_status = PaymentStatus.PROCESSING.value
    db.commit()
    db.refresh(order)
    _sync_order_stage_to_goodjob(
        order,
        stage="deposit_received",
        step_number=4,
        details={
            "deposit_amount": _num(order.deposit_amount),
            "deposit_ratio": _num(order.deposit_ratio),
            "payment_reference": body.payment_reference if body else None,
        },
    )
    return success_response(data={
        "id": str(order.id),
        "status": _status_val(order.status),
        "payment_status": _status_val(order.payment_status),
        "deposit_amount": _num(order.deposit_amount),
        "deposit_ratio": _num(order.deposit_ratio),
    }, message="定金已成功核销，订单进入生产备料阶段")


@router.post("/{order_id}/start-production")
def start_order_production(
    order_id: str,
    body: ProductionFollowupRequest = None,
    request: Request = None,
    user=Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """外贸七步⑤：生产跟单（deposit_received/confirmed → in_production，卖家/管理员操作）。"""
    token = _order_token_of(request)
    order = _load_order(db, order_id, user, token)
    if _is_buyer_scope(order, user, token):
        raise HTTPException(status_code=403, detail="买家无权变更生产状态")

    cur_status = _status_val(order.status)
    if cur_status not in ("deposit_received", "confirmed", "paid"):
        raise HTTPException(status_code=400, detail=f"当前订单状态 '{cur_status}' 不满足排产条件（需先核销定金）")

    order.status = OrderStatus.IN_PRODUCTION.value
    if body and body.estimated_delivery:
        try:
            from datetime import datetime
            order.estimated_delivery = datetime.fromisoformat(body.estimated_delivery)
        except Exception:
            pass
    db.commit()
    db.refresh(order)
    _sync_order_stage_to_goodjob(
        order,
        stage="in_production",
        step_number=5,
        details={
            "estimated_delivery": order.estimated_delivery.isoformat() if order.estimated_delivery else None,
            "production_notes": body.production_notes if body else None,
        },
    )
    return success_response(data={
        "id": str(order.id),
        "status": _status_val(order.status),
        "estimated_delivery": order.estimated_delivery.isoformat() if order.estimated_delivery else None,
    }, message="生产计划已启动，工厂排产跟单中")


@router.post("/{order_id}/dispatch")
def dispatch_order_shipment(
    order_id: str,
    body: DispatchShipmentRequest,
    request: Request = None,
    user=Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """外贸七步⑥：发运装船与提单绑定（in_production/confirmed → shipped，卖家/管理员操作）。"""
    token = _order_token_of(request)
    order = _load_order(db, order_id, user, token)
    if _is_buyer_scope(order, user, token):
        raise HTTPException(status_code=403, detail="买家无权进行出运调度")

    if body.tracking_number:
        order.tracking_number = body.tracking_number.strip()
    if body.bl_number:
        order.bl_number = body.bl_number.strip()
    if body.container_no:
        order.container_no = body.container_no.strip()
    if body.carrier:
        order.shipping_method = body.carrier.strip()
    if body.gross_weight is not None:
        order.gross_weight = body.gross_weight
    if body.volume is not None:
        order.volume = body.volume

    order.status = OrderStatus.SHIPPED.value
    db.commit()
    db.refresh(order)

    # 自动同步一次物流轨迹（若提供 carrier）
    sync_res = None
    if body.carrier and order.tracking_number:
        try:
            sync_res = sync_order_from_tracking(db, order, carrier=body.carrier)
        except Exception:
            pass

    _sync_order_stage_to_goodjob(
        order,
        stage="shipped",
        step_number=6,
        details={
            "bl_number": order.bl_number,
            "container_no": order.container_no,
            "tracking_number": order.tracking_number,
            "carrier": body.carrier,
        },
    )
    return success_response(data={
        "id": str(order.id),
        "status": _status_val(order.status),
        "bl_number": order.bl_number,
        "container_no": order.container_no,
        "tracking_number": order.tracking_number,
        "sync": sync_res,
    }, message="货物已出运装船，提单与箱号已绑定")


@router.post("/{order_id}/settle-balance")
def settle_order_balance(
    order_id: str,
    body: SettleBalanceRequest = None,
    request: Request = None,
    user=Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """外贸七步⑦：尾款核销与全单交割（shipped/final_payment_received → completed，卖家/管理员操作）。"""
    token = _order_token_of(request)
    order = _load_order(db, order_id, user, token)
    if _is_buyer_scope(order, user, token):
        raise HTTPException(status_code=403, detail="买家无权核销尾款")

    order.status = OrderStatus.COMPLETED.value
    order.payment_status = PaymentStatus.PAID.value
    db.commit()
    db.refresh(order)
    _sync_order_stage_to_goodjob(
        order,
        stage="completed",
        step_number=7,
        details={
            "balance_amount": body.balance_amount if body else None,
            "payment_reference": body.payment_reference if body else None,
        },
    )
    return success_response(data={
        "id": str(order.id),
        "status": _status_val(order.status),
        "payment_status": _status_val(order.payment_status),
    }, message="尾款已核销结清，订单7步全链路履约完成")


@router.post("/{order_id}/documents/pi")
def get_or_create_order_pi(
    order_id: str,
    request: Request = None,

    user=Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """生成形式发票 Proforma Invoice (PI)。"""
    order = _load_order(db, order_id, user, _order_token_of(request))
    seller, buyer, lines = _extract_seller_buyer_lines(order, db)
    pi_no = f"PI-{order.order_number}"
    pi_doc = build_proforma_invoice(
        seller=seller,
        buyer=buyer,
        lines=lines,
        currency=order.currency or "USD",
        payment_terms=order.payment_terms or "30% deposit, 70% before shipment",
        delivery_terms=order.incoterms or "FOB Shenzhen",
        validity_days=30,
        notes="Official Proforma Invoice generated by YouDing Trade Engine",
        pi_no=pi_no,
        db=db,
        tenant_id=str(getattr(order, "tenant_id", "") or "") or None,
        order_id=str(order.id),
    )
    return success_response(data=pi_doc, message="形式发票 PI 已成功生成")


@router.post("/{order_id}/documents/ci")
def get_or_create_order_ci(
    order_id: str,
    request: Request = None,
    user=Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """生成商业发票 Commercial Invoice (CI)，自动扣除已付定金。"""
    order = _load_order(db, order_id, user, _order_token_of(request))
    seller, buyer, lines = _extract_seller_buyer_lines(order, db)
    ci_no = f"CI-{order.order_number}"
    ci_doc = build_commercial_invoice(
        seller=seller,
        buyer=buyer,
        lines=lines,
        ci_no=ci_no,
        pi_ref=f"PI-{order.order_number}",
        order_ref=order.order_number,
        currency=order.currency or "USD",
        incoterms=order.incoterms or "FOB Shenzhen",
        port_of_loading=order.port_of_loading or "Shenzhen, China",
        port_of_discharge=order.port_of_discharge or "Destination Port",
        bl_number=order.bl_number or "Pending B/L",
        deposit_paid=float(order.deposit_amount or 0.0),
        payment_terms=order.payment_terms or "30% deposit, 70% against B/L copy",
    )
    return success_response(data=ci_doc, message="商业发票 CI 已成功生成")


@router.post("/{order_id}/documents/packing-list")
def get_or_create_order_packing_list(
    order_id: str,
    request: Request = None,
    user=Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """生成装箱单 Packing List (PL)，自动计算箱数、毛重、净重与配载测算。"""
    order = _load_order(db, order_id, user, _order_token_of(request))
    seller, buyer, lines = _extract_seller_buyer_lines(order, db)
    pl_no = f"PL-{order.order_number}"

    # 基于明细自动折算箱规
    packages = []
    for row in lines:
        qty = float(row.get("quantity") or 1)
        pkg_count = max(1, int(qty // 10) or 1)
        packages.append({
            "package_count": pkg_count,
            "qty_per_package": round(qty / pkg_count, 1),
            "description": row.get("description"),
            "net_weight_kg": float(order.net_weight or 15.0) / len(lines),
            "gross_weight_kg": float(order.gross_weight or 17.5) / len(lines),
            "length_cm": 60.0,
            "width_cm": 40.0,
            "height_cm": 35.0,
        })

    pl_doc = build_packing_list(
        seller=seller,
        buyer=buyer,
        packages=packages,
        pl_no=pl_no,
        ci_ref=f"CI-{order.order_number}",
        order_ref=order.order_number,
        shipping_marks=order.shipping_marks or f"S/M {order.order_number}",
        port_of_loading=order.port_of_loading or "Shenzhen, China",
        port_of_discharge=order.port_of_discharge or "Destination Port",
    )
    return success_response(data=pl_doc, message="装箱单 Packing List 已成功生成")


@router.post("/{order_id}/documents/certificate-of-origin")
def get_or_create_order_co(
    order_id: str,
    request: Request = None,
    user=Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """生成符合 CCPIT/海关规范的原产地证 (Certificate of Origin)。"""
    order = _load_order(db, order_id, user, _order_token_of(request))
    seller, buyer, lines = _extract_seller_buyer_lines(order, db)
    co_no = f"CO-{order.order_number}-CCPIT"
    items = []
    for row in lines:
        items.append({
            "shipping_marks": order.shipping_marks or "N/M",
            "description": row.get("description"),
            "hs_code": row.get("hs_code") or "6802.91.00",
            "origin_criterion": "WO",
            "gross_weight_kg": float(order.gross_weight or 100.0),
        })
    co_doc = build_certificate_of_origin(
        exporter=seller,
        consignee=buyer,
        items=items,
        co_no=co_no,
        invoice_no=f"CI-{order.order_number}",
        transport_details=f"By Sea from {order.port_of_loading or 'Shenzhen'} to {order.port_of_discharge or 'Destination'}",
    )
    return success_response(data=co_doc, message="原产地证 CO 已成功生成")


@router.post("/{order_id}/documents/split-shipment")
def split_order_shipment(
    order_id: str,
    body: SplitShipmentRequest,
    request: Request = None,
    user=Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """分批装运拆单制单：自动核算批次 CI、装箱单与未发余量。"""
    order = _load_order(db, order_id, user, _order_token_of(request))
    seller, buyer, lines = _extract_seller_buyer_lines(order, db)
    split_doc = build_split_shipment_documents(
        parent_order_id=order.order_number,
        seller=seller,
        buyer=buyer,
        total_order_lines=lines,
        batch_lines=body.batch_lines,
        batch_index=body.batch_index,
        currency=order.currency or "USD",
        incoterms=order.incoterms or "FOB Shenzhen",
    )
    return success_response(data=split_doc, message=f"第 {body.batch_index} 批次分批出运单据已生成")


@router.post("/{order_id}/documents/credit-note")
def create_order_credit_note(
    order_id: str,
    body: CreditNoteRequest,
    request: Request = None,
    user=Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """单据冲红与贷项凭单：生成 Credit Note 用于退货、货损与退款扣减。"""
    order = _load_order(db, order_id, user, _order_token_of(request))
    seller, buyer, _ = _extract_seller_buyer_lines(order, db)
    cn_doc = build_credit_note(
        original_ci_no=body.original_ci_no,
        seller=seller,
        buyer=buyer,
        credited_items=body.credited_items,
        currency=order.currency or "USD",
        reason=body.reason,
    )
    return success_response(data=cn_doc, message="单据冲红 Credit Note 已成功生成")



@router.get("/{order_id}/documents/{doc_type}/export")
def export_order_document(
    order_id: str,
    doc_type: str,  # pi, ci, pl, co, credit_note
    format: str = Query("html", pattern="^(html|docx)$"),
    request: Request = None,
    user=Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """外贸单证专业级导出：支持可打印 HTML (含公章印签) 与 DOCX 格式。"""
    order = _load_order(db, order_id, user, _order_token_of(request))
    seller, buyer, lines = _extract_seller_buyer_lines(order, db)
    norm_type = doc_type.strip().lower()

    if norm_type == "pi":
        doc_data = build_proforma_invoice(
            seller=seller,
            buyer=buyer,
            lines=lines,
            currency=order.currency or "USD",
            payment_terms=order.payment_terms or "30% deposit, 70% before shipment",
            delivery_terms=order.incoterms or "FOB Shenzhen",
            pi_no=f"PI-{order.order_number}",
            db=db,
            tenant_id=str(getattr(order, "tenant_id", "") or "") or None,
            order_id=str(order.id),
        )
    elif norm_type == "ci":
        doc_data = build_commercial_invoice(
            seller=seller,
            buyer=buyer,
            lines=lines,
            ci_no=f"CI-{order.order_number}",
            pi_ref=f"PI-{order.order_number}",
            order_ref=order.order_number,
            currency=order.currency or "USD",
            incoterms=order.incoterms or "FOB Shenzhen",
            port_of_loading=order.port_of_loading or "Shenzhen, China",
            port_of_discharge=order.port_of_discharge or "Destination Port",
            bl_number=order.bl_number or "Pending",
            deposit_paid=float(order.deposit_amount or 0.0),
        )
    elif norm_type in ("pl", "packing_list", "packing-list"):
        packages = [{
            "package_count": 10,
            "qty_per_package": 10,
            "description": lines[0]["description"] if lines else "Building Components",
            "net_weight_kg": float(order.net_weight or 150.0),
            "gross_weight_kg": float(order.gross_weight or 175.0),
        }]
        doc_data = build_packing_list(
            seller=seller,
            buyer=buyer,
            packages=packages,
            pl_no=f"PL-{order.order_number}",
            ci_ref=f"CI-{order.order_number}",
            order_ref=order.order_number,
        )
    elif norm_type in ("co", "origin"):
        items = [{
            "shipping_marks": order.shipping_marks or "N/M",
            "description": lines[0]["description"] if lines else "Building Components",
            "hs_code": "6802.91.00",
            "origin_criterion": "WO",
            "gross_weight_kg": float(order.gross_weight or 100.0),
        }]
        doc_data = build_certificate_of_origin(
            exporter=seller,
            consignee=buyer,
            items=items,
            co_no=f"CO-{order.order_number}-CCPIT",
            invoice_no=f"CI-{order.order_number}",
        )
    else:
        raise HTTPException(status_code=400, detail=f"不支持的单证类型: {doc_type}")

    if format == "docx":
        content_bytes = build_trade_document_docx(doc_data)
        filename = f"{norm_type.upper()}-{order.order_number}.docx"
        return Response(
            content=content_bytes,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    html_str = build_trade_document_html(doc_data)
    return Response(content=html_str, media_type="text/html; charset=utf-8")

