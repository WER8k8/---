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
from app.models.quote import Quote, QuoteItem
from app.models.rfq import RFQ
from app.models.user import User

logger = logging.getLogger(__name__)


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = "/quotes"
ROUTE_TAGS = ["报价管理"]

router = APIRouter(tags=["quotes"])

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
    from app.core.tenant_scope import tenant_can_access
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
def list_versions(quote_id: str, db: Session = Depends(get_db)):
    """list_versions。

    参数说明：
    :param quote_id: 参数 quote_id
    :param db: 参数 db
    :return: 返回处理结果。
    """
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
    if merchant_id: query = query.filter(Quote.merchant_id == uuid.UUID(merchant_id))
    if status: query = query.filter(Quote.status == status)
    if rfq_id: query = query.filter(Quote.rfq_id == uuid.UUID(rfq_id))
    quotes = query.order_by(Quote.created_at.desc()).offset(skip).limit(limit).all()
    return [_serialize(q) for q in quotes]

@router.put("/{quote_id}/status", response_model=dict)
def update_quote_status(quote_id: str, status: str, db: Session = Depends(get_db)):
    """update_quote_status。

    参数说明：
    :param quote_id: 参数 quote_id
    :param status: 参数 status
    :param db: 参数 db
    :return: 返回处理结果。
    """
    quote = db.query(Quote).filter(Quote.id == uuid.UUID(quote_id)).first()
    if not quote: raise HTTPException(404, "Quote not found")
    quote.status = status
    db.commit()
    db.refresh(quote)
    return success_response(data={"id": str(quote.id), "status": quote.status})