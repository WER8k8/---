# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""产品 FAQ API — 中英双语 CRUD"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.product import ProductFaq, Product
from app.core.response import success_response


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = ""

router = APIRouter(prefix="/product-faqs", tags=["产品FAQ"])


class FaqCreate(BaseModel):
    product_id: str
    question_zh: str
    answer_zh: str
    question_en: str | None = None
    answer_en: str | None = None
    sort_order: int = 0


class FaqUpdate(BaseModel):
    question_zh: str | None = None
    answer_zh: str | None = None
    question_en: str | None = None
    answer_en: str | None = None
    sort_order: int | None = None
    is_active: bool | None = None


@router.get("/product/{product_id}")
async def list_faqs(product_id: str, db: Session = Depends(get_db)):
    """获取产品的所有 FAQ"""
    faqs = db.query(ProductFaq).filter(
        ProductFaq.product_id == product_id,
        ProductFaq.is_active == True,
    ).order_by(ProductFaq.sort_order).all()
    return success_response([_faq_to_dict(f) for f in faqs])


@router.post("")
async def create_faq(body: FaqCreate, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    """创建 FAQ"""
    faq = ProductFaq(**body.model_dump())
    db.add(faq)
    db.commit()
    db.refresh(faq)
    return success_response(_faq_to_dict(faq))


@router.put("/{faq_id}")
async def update_faq(faq_id: str, body: FaqUpdate, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    """更新 FAQ"""
    faq = db.get(ProductFaq, faq_id)
    if not faq:
        raise HTTPException(404, "FAQ not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(faq, k, v)
    db.commit()
    db.refresh(faq)
    return success_response(_faq_to_dict(faq))


@router.delete("/{faq_id}")
async def delete_faq(faq_id: str, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    """删除 FAQ"""
    faq = db.get(ProductFaq, faq_id)
    if not faq:
        raise HTTPException(404, "FAQ not found")
    db.delete(faq)
    db.commit()
    return success_response({"deleted": True})


def _faq_to_dict(faq: ProductFaq) -> dict:
    """执行 faq_to_dict 相关逻辑处理。
    
    :param faq: 参数 faq
    :return: 返回处理结果。
    """
    return {
        "id": faq.id,
        "product_id": faq.product_id,
        "question_zh": faq.question_zh,
        "answer_zh": faq.answer_zh,
        "question_en": faq.question_en,
        "answer_en": faq.answer_en,
        "sort_order": faq.sort_order,
        "is_active": faq.is_active,
    }

