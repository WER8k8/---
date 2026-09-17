# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""
Product Images API Router - 产品图片API
"""
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
import os

from app.core.database import get_db
from app.core.response import success_response
from app.models.product_image import ProductImage


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = "/product-images"
ROUTE_TAGS = ["产品图片"]

router = APIRouter(tags=["product-images"])

# 图片上传目录
UPLOAD_DIR = "uploads/products"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/", response_model=dict)
def upload_product_image(
    product_id: str,
    image: UploadFile = File(...),
    alt_text: Optional[str] = None,
    sort_order: int = 0,
    is_primary: bool = False,
    db: Session = Depends(get_db)
):
    """上传产品图片"""
    try:
        # 保存图片到本地
        file_ext = os.path.splitext(image.filename)[1]
        file_name = f"{uuid.uuid4()}{file_ext}"
        file_path = os.path.join(UPLOAD_DIR, file_name)
        with open(file_path, "wb") as f:
            f.write(image.file.read())
        
        image_url = f"/{UPLOAD_DIR}/{file_name}"
        # 如果设置为主图，取消其他主图
        if is_primary:
            db.query(ProductImage).filter(
                ProductImage.product_id == uuid.UUID(product_id),
                ProductImage.is_primary == True
            ).update({"is_primary": False})
        
        # 创建图片记录
        product_image = ProductImage(
            product_id=uuid.UUID(product_id),
            image_url=image_url,
            alt_text=alt_text,
            sort_order=sort_order,
            is_primary=is_primary,
        )
        db.add(product_image)
        db.commit()
        db.refresh(product_image)
        return success_response(data={
            "id": str(product_image.id),
            "image_url": product_image.image_url,
            "is_primary": product_image.is_primary,
        })
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{image_id}", response_model=dict)
def get_product_image(image_id: str, db: Session = Depends(get_db)):
    """获取产品图片详情"""
    image = db.query(ProductImage).filter(ProductImage.id == uuid.UUID(image_id)).first()
    if not image:
        raise HTTPException(status_code=404, detail="Product image not found")
    
    return success_response(data={
        "id": str(image.id),
        "product_id": str(image.product_id),
        "image_url": image.image_url,
        "alt_text": image.alt_text,
        "sort_order": image.sort_order,
        "is_primary": image.is_primary,
    })


@router.get("/by-product/{product_id}", response_model=List[dict])
def list_product_images(product_id: str, db: Session = Depends(get_db)):
    """列出产品的所有图片"""
    images = db.query(ProductImage).filter(
        ProductImage.product_id == uuid.UUID(product_id)
    ).order_by(ProductImage.sort_order).all()
    return success_response(data=[
        {
            "id": str(img.id),
            "image_url": img.image_url,
            "alt_text": img.alt_text,
            "sort_order": img.sort_order,
            "is_primary": img.is_primary,
        }
        for img in images
    ])


@router.put("/{image_id}", response_model=dict)
def update_product_image(
    image_id: str,
    alt_text: Optional[str] = None,
    sort_order: Optional[int] = None,
    is_primary: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """更新产品图片"""
    image = db.query(ProductImage).filter(ProductImage.id == uuid.UUID(image_id)).first()
    if not image:
        raise HTTPException(status_code=404, detail="Product image not found")
    
    if alt_text is not None:
        image.alt_text = alt_text
    if sort_order is not None:
        image.sort_order = sort_order
    if is_primary is not None:
        if is_primary:
            # 取消其他主图
            db.query(ProductImage).filter(
                ProductImage.product_id == image.product_id,
                ProductImage.is_primary == True
            ).update({"is_primary": False})
        image.is_primary = is_primary
    
    db.commit()
    db.refresh(image)
    return success_response(data={
        "id": str(image.id),
        "image_url": image.image_url,
        "is_primary": image.is_primary,
    })


@router.delete("/{image_id}")
def delete_product_image(image_id: str, db: Session = Depends(get_db)):
    """删除产品图片"""
    image = db.query(ProductImage).filter(ProductImage.id == uuid.UUID(image_id)).first()
    if not image:
        raise HTTPException(status_code=404, detail="Product image not found")
    
    # 删除本地文件
    file_path = image.image_url.lstrip("/")
    if os.path.exists(file_path):
        os.remove(file_path)
    
    db.delete(image)
    db.commit()
    return success_response(message="Product image deleted successfully")
