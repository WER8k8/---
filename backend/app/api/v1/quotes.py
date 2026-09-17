# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Quotes API Router - 报价管理（RFQ 关联 + 审批 + 版本）"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import uuid
import logging
from datetime import datetime, timezone

from app.core.database import get_db
from app.core.response import success_response, error_response
from app.core.security import get_current_user
from pydantic import BaseModel, Field
import secrets
from app.models.quote import Quote, QuoteItem
from app.models.rfq import RFQ
from app.models.user import User

logger = logging.getLogger(__name__)


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = "/quotes"
ROUTE_TAGS = ["报价管理"]

router = APIRouter(tags=["quotes"])

def _is_valid_uuid(s: str) -> bool:
    """非法 UUID 字符串直接查 PG UUID 列会抛 DataError→500，先挡成 404。"""
    try:
        uuid.UUID(s)
        return True
    except ValueError:
        return False

def _serialize(q: Quote) -> dict:
    """_serialize。

    参数说明：
    :param q: 参数 q
    :return: 返回处理结果。
    """
    return {
        "id": str(q.id), "inquiry_id": str(q.inquiry_id) if q.inquiry_id else None,
        "rfq_id": str(q.rfq_id) if q.rfq_id else None, "merchant_id": str(q.merchant_id),
        "total_amount": float(q.total_amount), "currency": q.currency, "status": q.status,
        "version": q.version, "approved_by": q.approved_by,
        "valid_until": q.valid_until.isoformat() if q.valid_until else None,
        "payment_terms": q.payment_terms, "delivery_terms": q.delivery_terms,
        "items": [{"product_name": i.product_name, "quantity": i.quantity, "unit": i.unit, "unit_price": float(i.unit_price) if i.unit_price else None, "total_price": float(i.total_price) if i.total_price else None} for i in (q.items or [])],
        "created_at": q.created_at.isoformat() if q.created_at else None,
        "updated_at": q.updated_at.isoformat() if q.updated_at else None,
    }

@router.post("/from-rfq", summary="从 RFQ 创建报价")
def create_from_rfq(rfq_id: str, merchant_id: str, valid_until: Optional[str] = None, payment_terms: Optional[str] = None, delivery_terms: Optional[str] = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """create_from_rfq。

    参数说明：
    :param rfq_id: 参数 rfq_id
    :param merchant_id: 参数 merchant_id
    :param valid_until: 参数 valid_until
    :param payment_terms: 参数 payment_terms
    :param delivery_terms: 参数 delivery_terms
    :param db: 参数 db
    :param current_user: 参数 current_user
    :return: 返回处理结果。
    """
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")
    if not _is_valid_uuid(merchant_id): return error_response(404, "商家不存在")
    from app.core.tenant_scope import tenant_can_access
    if not _is_valid_uuid(rfq_id): return error_response(404, "RFQ 不存在")
    rfq = db.query(RFQ).filter(RFQ.id == rfq_id, RFQ.deleted_at.is_(None)).first()
    if not rfq:
        return error_response(404, "RFQ 不存在")
    # T07 跨租户引用校验：报价的源 RFQ 必须属于当前用户租户（平台级放行）
    if not tenant_can_access(db, current_user, rfq.tenant_id):
        return error_response(403, "无权引用该 RFQ（跨租户）")
    valid = None
    if valid_until:
        try:
            valid = datetime.strptime(valid_until, "%Y-%m-%d").date()
        except ValueError as exc:
            logger.warning("Invalid valid_until format: %s", valid_until)
            return error_response(400, f"valid_until 格式错误: {exc}")
    quote = Quote(inquiry_id=None, tenant_id=rfq.tenant_id, merchant_id=uuid.UUID(merchant_id), rfq_id=rfq.id, total_amount=0, currency=rfq.currency or "USD", valid_until=valid, payment_terms=payment_terms, delivery_terms=delivery_terms, status="draft")
    db.add(quote)
    db.flush()
    # Copy RFQ items as QuoteItems
    for item in (rfq.items or []):
        if getattr(item, "deleted_at", None) is None:
            db.add(QuoteItem(quote_id=quote.id, product_id=item.product_id, product_name=item.product_name, quantity=item.quantity, unit=item.unit))
    db.commit()
    db.refresh(quote)
    return success_response(data=_serialize(quote), message="已从 RFQ 创建报价")

@router.post("/{quote_id}/approve", summary="审批报价")
def approve_quote(quote_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """approve_quote。

    参数说明：
    :param quote_id: 参数 quote_id
    :param db: 参数 db
    :param current_user: 参数 current_user
    :return: 返回处理结果。
    """
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")
    if not _is_valid_uuid(quote_id): return error_response(404, "报价不存在")
    q = db.query(Quote).filter(Quote.id == uuid.UUID(quote_id)).first()
    if not q: return error_response(404, "报价不存在")
    q.status = "sent"
    q.approved_by = str(current_user.id)
    q.approved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(q)
    return success_response(data=_serialize(q), message="报价已审批")

@router.post("/{quote_id}/version", summary="创建新版本")
def new_version(quote_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """new_version。

    参数说明：
    :param quote_id: 参数 quote_id
    :param db: 参数 db
    :param current_user: 参数 current_user
    :return: 返回处理结果。
    """
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")
    if not _is_valid_uuid(quote_id): return error_response(404, "报价不存在")
    orig = db.query(Quote).filter(Quote.id == uuid.UUID(quote_id)).first()
    if not orig: return error_response(404, "报价不存在")
    # Create new version as a new Quote row
    new_q = Quote(inquiry_id=orig.inquiry_id, merchant_id=orig.merchant_id, rfq_id=orig.rfq_id, total_amount=orig.total_amount, currency=orig.currency, status="draft", version=orig.version + 1)
    db.add(new_q)
    db.flush()
    for item in (orig.items or []):
        db.add(QuoteItem(quote_id=new_q.id, product_id=item.product_id, product_name=item.product_name, quantity=item.quantity, unit=item.unit, unit_price=item.unit_price, total_price=item.total_price))
    db.commit()
    db.refresh(new_q)
    return success_response(data=_serialize(new_q), message=f"版本 v{new_q.version} 已创建")

@router.get("/{quote_id}/versions", summary="版本历史")
def list_versions(quote_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """list_versions。

    参数说明：
    :param quote_id: 参数 quote_id
    :param db: 参数 db
    :param current_user: 参数 current_user
    :return: 返回处理结果。
    """
    if not _is_valid_uuid(quote_id): return error_response(404, "报价不存在")
    quote = db.query(Quote).filter(Quote.id == uuid.UUID(quote_id)).first()
    if not quote:
        return error_response(404, "报价不存在")
    quotes = db.query(Quote).filter(Quote.rfq_id == quote.rfq_id).order_by(Quote.version.desc()).all()
    return success_response(data=[{"id": str(q.id), "version": q.version, "status": q.status, "total_amount": float(q.total_amount), "created_at": q.created_at.isoformat() if q.created_at else None} for q in quotes])

@router.get("/{quote_id}", response_model=dict)
def get_quote(quote_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """get_quote。

    参数说明：
    :param quote_id: 参数 quote_id
    :param db: 参数 db
    :return: 返回处理结果。
    """
    if not _is_valid_uuid(quote_id): raise HTTPException(404, "Quote not found")
    quote = db.query(Quote).filter(Quote.id == uuid.UUID(quote_id)).first()
    if not quote: raise HTTPException(404, "Quote not found")
    from app.core.tenant_scope import tenant_can_access
    if not tenant_can_access(db, current_user, quote.tenant_id):
        raise HTTPException(404, "Quote not found")  # 跨租户按不存在处理
    return success_response(data=_serialize(quote))

@router.get("/", response_model=List[dict])
def list_quotes(merchant_id: Optional[str] = None, status: Optional[str] = None, rfq_id: Optional[str] = None, skip: int = Query(0, ge=0), limit: int = Query(10, ge=1, le=100), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """list_quotes。

    参数说明：
    :param merchant_id: 参数 merchant_id
    :param status: 参数 status
    :param rfq_id: 参数 rfq_id
    :param skip: 参数 skip
    :param limit: 参数 limit
    :param db: 参数 db
    :return: 返回处理结果。
    """
    from app.core.tenant_scope import scope_tenant_query
    query = scope_tenant_query(db.query(Quote), Quote, db, current_user)
    if (merchant_id and not _is_valid_uuid(merchant_id)) or (rfq_id and not _is_valid_uuid(rfq_id)):
        return error_response(404, "报价不存在")
    if merchant_id: query = query.filter(Quote.merchant_id == uuid.UUID(merchant_id))
    if status: query = query.filter(Quote.status == status)
    if rfq_id: query = query.filter(Quote.rfq_id == uuid.UUID(rfq_id))
    quotes = query.order_by(Quote.created_at.desc()).offset(skip).limit(limit).all()
    return [_serialize(q) for q in quotes]

@router.put("/{quote_id}/status", response_model=dict)
def update_quote_status(quote_id: str, status: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """update_quote_status。

    参数说明：
    :param quote_id: 参数 quote_id
    :param status: 参数 status
    :param db: 参数 db
    :param current_user: 参数 current_user
    :return: 返回处理结果。
    """
    if not _is_valid_uuid(quote_id): return error_response(404, "报价不存在")
    quote = db.query(Quote).filter(Quote.id == uuid.UUID(quote_id)).first()
    if not quote: raise HTTPException(404, "Quote not found")
    quote.status = status
    db.commit()
    db.refresh(quote)
    return success_response(data={"id": str(quote.id), "status": quote.status})


class BOQCalculationRequest(BaseModel):
    material_type: str = Field(..., description="材料类型: marble, granite, ceramic, wood, metal 等")
    quantity_sqm: float = Field(..., gt=0, description="数量(平方米)")
    incoterms: str = Field("FOB", description="贸易术语: FOB, CIF, EXW 等")
    thickness_mm: Optional[float] = None
    customization: Optional[bool] = False
    logo_printing: Optional[bool] = False
    inspection_required: Optional[bool] = False
    insurance_required: Optional[bool] = False
    params: Optional[dict] = None


@router.post("/calculate-boq", summary="BOQ 22 参数工业核价")
def calculate_boq(req: BOQCalculationRequest):
    """根据材料规格与外贸参数计算工业级报价。"""
    from app.services.boq_calculator import BOQCalculator
    calc_params = dict(req.params or {})
    calc_params.update(req.model_dump(exclude={"params"}))
    calculator = BOQCalculator()
    result = calculator.calculate(calc_params)
    if "error" in result:
        return error_response(400, result["error"])
    return success_response(data=result, message="BOQ 核价完成")


class QuoteFromInquiryRequest(BaseModel):
    inquiry_id: str
    merchant_id: Optional[str] = None
    valid_until: Optional[str] = None
    payment_terms: Optional[str] = "T/T 30/70"
    delivery_terms: Optional[str] = "FOB"
    product_name: Optional[str] = None
    quantity: Optional[float] = 1.0
    unit_price: Optional[float] = 0.0


@router.post("/from-inquiry", summary="从询盘一键创建报价单")
def create_from_inquiry(
    req: QuoteFromInquiryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """外贸商业闭环：客户询盘入库后直接生成关联的报价单草稿。"""
    if not _is_valid_uuid(req.inquiry_id):
        return error_response(404, "询盘不存在")
    from app.models.inquiry import Inquiry
    from app.core.tenant_scope import tenant_can_access
    inquiry = db.query(Inquiry).filter(Inquiry.id == uuid.UUID(req.inquiry_id)).first()
    if not inquiry:
        return error_response(404, "询盘不存在")
    if not tenant_can_access(db, current_user, inquiry.tenant_id):
        return error_response(403, "无权引用该询盘（跨租户）")

    mid = None
    if req.merchant_id and _is_valid_uuid(req.merchant_id):
        mid = uuid.UUID(req.merchant_id)
    else:
        mid = current_user.id

    valid = None
    if req.valid_until:
        try:
            valid = datetime.strptime(req.valid_until, "%Y-%m-%d").date()
        except ValueError as exc:
            return error_response(400, f"valid_until 格式错误: {exc}")

    p_name = req.product_name or getattr(inquiry, "product_name", None) or "Standard Industrial Supplies"
    qty = req.quantity if req.quantity and req.quantity > 0 else 1.0
    u_price = req.unit_price if req.unit_price and req.unit_price >= 0 else 0.0
    total = round(qty * u_price, 2)

    quote = Quote(
        inquiry_id=inquiry.id,
        tenant_id=inquiry.tenant_id,
        merchant_id=mid,
        rfq_id=None,
        total_amount=total,
        currency="USD",
        valid_until=valid,
        payment_terms=req.payment_terms,
        delivery_terms=req.delivery_terms,
        status="draft",
        version=1,
    )
    db.add(quote)
    db.flush()

    item = QuoteItem(
        quote_id=quote.id,
        product_name=p_name,
        quantity=qty,
        unit="sqm",
        unit_price=u_price,
        total_price=total,
    )
    db.add(item)
    db.commit()
    db.refresh(quote)
    return success_response(data=_serialize(quote), message="已从询盘创建报价单")


class ConvertQuoteToOrderRequest(BaseModel):
    buyer_id: Optional[str] = None
    shipping_address: Optional[str] = "Standard Port Delivery"
    deposit_ratio: Optional[float] = 30.0


@router.post("/{quote_id}/convert-to-order", summary="报价单一键转换为正式订单")
def convert_to_order(
    quote_id: str,
    req: Optional[ConvertQuoteToOrderRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """外贸商业闭环：买卖双方确认报价后，一键生成正式订单与 256 位安全 Access Token。"""
    if not _is_valid_uuid(quote_id):
        return error_response(404, "报价单不存在")
    from app.core.tenant_scope import tenant_can_access
    from app.models.order import Order
    quote = db.query(Quote).filter(Quote.id == uuid.UUID(quote_id)).first()
    if not quote:
        return error_response(404, "报价单不存在")
    if not tenant_can_access(db, current_user, quote.tenant_id):
        return error_response(403, "无权操作该报价单（跨租户）")

    buyer_id = None
    if req and req.buyer_id and _is_valid_uuid(req.buyer_id):
        buyer_id = uuid.UUID(req.buyer_id)
    else:
        buyer_id = current_user.id

    shipping_addr = (req.shipping_address if req and req.shipping_address else None) or "Standard Delivery"
    dep_ratio = req.deposit_ratio if req and req.deposit_ratio is not None else 30.0
    dep_amount = round(float(quote.total_amount) * dep_ratio / 100.0, 2) if quote.total_amount else 0.0

    order_number = f"ORD-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(2).upper()}"
    access_token = secrets.token_hex(32)

    new_order = Order(
        order_number=order_number,
        buyer_id=buyer_id,
        merchant_id=quote.merchant_id,
        tenant_id=quote.tenant_id,
        quote_id=quote.id,
        total_amount=float(quote.total_amount),
        currency=quote.currency or "USD",
        status="pending",
        payment_status="unpaid",
        shipping_address=shipping_addr,
        access_token=access_token,
        incoterms=quote.delivery_terms or "FOB",
        payment_terms=quote.payment_terms or "T/T 30/70",
        deposit_ratio=dep_ratio,
        deposit_amount=dep_amount,
    )
    db.add(new_order)
    quote.status = "converted"
    db.commit()
    db.refresh(new_order)
    return success_response(
        data={
            "order_id": str(new_order.id),
            "order_number": new_order.order_number,
            "status": new_order.status,
            "total_amount": float(new_order.total_amount),
            "currency": new_order.currency,
            "access_token": new_order.access_token,
            "incoterms": new_order.incoterms,
            "deposit_amount": new_order.deposit_amount,
        },
        message="报价单已成功转换为正式订单",
    )