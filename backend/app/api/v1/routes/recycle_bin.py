"""回收站 API — 软删除内容的查询、恢复、永久删除"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, desc, func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.product import Product
from app.models.inquiry import Inquiry
from app.models.content import ContentPage


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = ""

router = APIRouter(prefix="/recycle-bin", tags=["回收站"])

MODEL_MAP = {
    "product": Product,
    "inquiry": Inquiry,
    "content": ContentPage,
}


@router.get("")
async def list_trashed(
    type: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    """获取已软删除的内容列表"""
    items = []
    total = 0
    models = {type: MODEL_MAP[type]} if type and type in MODEL_MAP else MODEL_MAP
    for model_type, model in models.items():
        if not hasattr(model, "deleted_at"):
            continue
        query = select(model).where(model.deleted_at.is_not(None))
        count_query = select(func.count()).select_from(
            select(model.id).where(model.deleted_at.is_not(None)).subquery()
        )
        if q:
            name_col = getattr(model, "name", None) or getattr(model, "title", None)
            if name_col:
                query = query.where(name_col.ilike(f"%{q}%"))
                count_query = select(func.count()).select_from(
                    select(model.id).where(
                        model.deleted_at.is_not(None),
                        name_col.ilike(f"%{q}%"),
                    ).subquery()
                )

        model_total = db.scalar(count_query) or 0
        total += model_total
        query = query.order_by(desc(model.deleted_at))
        query = query.offset((page - 1) * page_size).limit(page_size)
        rows = db.execute(query).scalars().all()
        for row in rows:
            name = getattr(row, "name", None) or getattr(row, "title", None) or str(row.id)
            items.append({
                "id": row.id,
                "name": name,
                "type": model_type,
                "deletedAt": row.deleted_at.isoformat() if row.deleted_at else None,
            })

    # 按删除时间排序
    items.sort(key=lambda x: x["deletedAt"] or "", reverse=True)
    return {"items": items[:page_size], "total": total, "page": page, "pageSize": page_size}


@router.post("/{item_type}/{item_id}/restore")
async def restore_item(
    item_type: str,
    item_id: str,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    """恢复软删除的内容"""
    model = MODEL_MAP.get(item_type)
    if not model:
        return {"error": "未知类型"}

    row = db.execute(
        select(model).where(model.id == item_id, model.deleted_at.is_not(None))
    ).scalar_one_or_none()
    if not row:
        return {"error": "未找到"}

    row.deleted_at = None
    db.commit()
    return {"success": True, "message": "已恢复"}


@router.delete("/{item_type}/{item_id}")
async def permanent_delete(
    item_type: str,
    item_id: str,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    """永久删除"""
    model = MODEL_MAP.get(item_type)
    if not model:
        return {"error": "未知类型"}

    row = db.execute(
        select(model).where(model.id == item_id, model.deleted_at.is_not(None))
    ).scalar_one_or_none()
    if not row:
        return {"error": "未找到"}

    db.delete(row)
    db.commit()
    return {"success": True, "message": "已永久删除"}


@router.post("/batch-delete")
async def batch_permanent_delete(
    body: dict,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    """批量永久删除"""
    ids = body.get("ids", [])
    if not ids:
        return {"error": "未选择"}

    count = 0
    for model in MODEL_MAP.values():
        rows = db.execute(
            select(model).where(model.id.in_(ids), model.deleted_at.is_not(None))
        ).scalars().all()
        for row in rows:
            db.delete(row)
            count += 1

    db.commit()
    return {"success": True, "deleted": count}

