"""
Product Categories API Router - 产品分类API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from app.core.database import get_db
from app.core.response import success_response
from app.models.product_category import ProductCategory


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = "/product-categories"
ROUTE_TAGS = ["产品分类"]

router = APIRouter(tags=["product-categories"])


@router.post("/", response_model=dict)
def create_product_category(
    name: str,
    slug: str,
    name_i18n: Optional[str] = None,  # JSON string
    parent_id: Optional[str] = None,
    level: int = 0,
    icon_url: Optional[str] = None,
    sort_order: int = 0,
    meta_title: Optional[str] = None,
    meta_description: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """创建产品分类"""
    try:
        category = ProductCategory(
            name=name,
            slug=slug,
            name_i18n=name_i18n,
            parent_id=uuid.UUID(parent_id) if parent_id else None,
            level=level,
            icon_url=icon_url,
            sort_order=sort_order,
            meta_title=meta_title,
            meta_description=meta_description,
        )
        db.add(category)
        db.commit()
        db.refresh(category)
        return success_response(data={"id": str(category.id), "name": category.name, "slug": category.slug})
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{category_id}", response_model=dict)
def get_product_category(category_id: str, db: Session = Depends(get_db)):
    """获取产品分类详情"""
    category = db.query(ProductCategory).filter(ProductCategory.id == uuid.UUID(category_id)).first()
    if not category:
        raise HTTPException(status_code=404, detail="Product category not found")
    
    return success_response(data={
        "id": str(category.id),
        "name": category.name,
        "slug": category.slug,
        "parent_id": str(category.parent_id) if category.parent_id else None,
        "level": category.level,
        "icon_url": category.icon_url,
        "sort_order": category.sort_order,
        "meta_title": category.meta_title,
        "meta_description": category.meta_description,
    })


@router.get("/", response_model=List[dict])
def list_product_categories(
    parent_id: Optional[str] = None,
    level: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """列出产品分类（支持按父分类/层级过滤）"""
    query = db.query(ProductCategory)
    if parent_id:
        query = query.filter(ProductCategory.parent_id == uuid.UUID(parent_id))
    if level is not None:
        query = query.filter(ProductCategory.level == level)
    
    categories = query.order_by(ProductCategory.sort_order).offset(skip).limit(limit).all()
    return success_response(data=[
        {
            "id": str(c.id),
            "name": c.name,
            "slug": c.slug,
            "level": c.level,
            "icon_url": c.icon_url,
        }
        for c in categories
    ])


@router.put("/{category_id}", response_model=dict)
def update_product_category(
    category_id: str,
    name: Optional[str] = None,
    slug: Optional[str] = None,
    name_i18n: Optional[str] = None,
    parent_id: Optional[str] = None,
    level: Optional[int] = None,
    icon_url: Optional[str] = None,
    sort_order: Optional[int] = None,
    meta_title: Optional[str] = None,
    meta_description: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """更新产品分类"""
    category = db.query(ProductCategory).filter(ProductCategory.id == uuid.UUID(category_id)).first()
    if not category:
        raise HTTPException(status_code=404, detail="Product category not found")
    
    if name is not None:
        category.name = name
    if slug is not None:
        category.slug = slug
    if name_i18n is not None:
        category.name_i18n = name_i18n
    if parent_id is not None:
        category.parent_id = uuid.UUID(parent_id) if parent_id else None
    if level is not None:
        category.level = level
    if icon_url is not None:
        category.icon_url = icon_url
    if sort_order is not None:
        category.sort_order = sort_order
    if meta_title is not None:
        category.meta_title = meta_title
    if meta_description is not None:
        category.meta_description = meta_description
    
    db.commit()
    db.refresh(category)
    return success_response(data={"id": str(category.id), "name": category.name, "slug": category.slug})


@router.delete("/{category_id}")
def delete_product_category(category_id: str, db: Session = Depends(get_db)):
    """删除产品分类"""
    category = db.query(ProductCategory).filter(ProductCategory.id == uuid.UUID(category_id)).first()
    if not category:
        raise HTTPException(status_code=404, detail="Product category not found")
    
    # 检查是否有子分类
    children = db.query(ProductCategory).filter(ProductCategory.parent_id == uuid.UUID(category_id)).first()
    if children:
        raise HTTPException(status_code=400, detail="Cannot delete category with children")
    
    db.delete(category)
    db.commit()
    return success_response(message="Product category deleted successfully")
