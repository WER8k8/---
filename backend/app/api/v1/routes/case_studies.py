"""案例管理路由 - 优化版 - 解决N+1查询和添加缓存"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session, joinedload

from app.core.cache_decorator import cache_response, invalidate_cache
from app.core.response import APIResponse, error_response, success_response
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.case_study import CaseImage, CaseStudy
from app.models.user import User
from app.schemas import CaseStudyCreate, CaseStudyUpdate


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = "/case-studies"
ROUTE_TAGS = ["案例管理"]

router = APIRouter()


def _safe_case_image_dict(img) -> dict:
    """
    处理 _safe_case_image_dict 相关业务逻辑。

    :param img: 入参。

    :return: 返回 dict 类型的结果。
    """
    return {
        "id": str(img.id),
        "case_id": str(img.case_id),
        "image_url": img.image_url,
        "image_alt": img.image_alt,
        "sort_order": img.sort_order,
        "is_active": img.is_active,
        "created_at": img.created_at.isoformat() if img.created_at else None,
    }


def _safe_case_study_dict(case) -> dict:
    """
    处理 _safe_case_study_dict 相关业务逻辑。

    :param case: 入参。

    :return: 返回 dict 类型的结果。
    """
    return {
        "id": str(case.id),
        "product_id": str(case.product_id) if case.product_id else None,
        "project_name": case.project_name,
        "slug": case.slug,
        "client_name": case.client_name,
        "materials_used": case.materials_used,
        "construction_area": case.construction_area,
        "project_date": case.project_date,
        "location": case.location,
        "project_address": case.project_address,
        "description": case.description,
        "cover_image": case.cover_image,
        "status": case.status,
        "sort_order": case.sort_order,
        "view_count": case.view_count,
        "is_active": case.is_active,
        "created_at": case.created_at.isoformat() if case.created_at else None,
        "updated_at": case.updated_at.isoformat() if case.updated_at else None,
        "images": [_safe_case_image_dict(img) for img in case.images] if case.images else [],
    }


class CaseImageCreate(BaseModel):
    image_url: str = Field(..., min_length=1, max_length=500)
    image_alt: str = Field(default="", max_length=255)
    sort_order: int = 0


@router.get("/")
@cache_response(expire=300, prefix="case_studies")
async def list_case_studies(
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """获取案例列表（分页）- 公开API - 优化：使用joinedload解决N+1查询"""
    q = db.query(CaseStudy).filter(CaseStudy.is_active).options(
        joinedload(CaseStudy.images)
    )
    if status:
        q = q.filter(CaseStudy.status == status)
    if search:
        q = q.filter(CaseStudy.project_name.ilike(f"%{search}%"))

    total = q.count()
    # 分页验证
    if page < 1:
        page = 1
    if page_size < 1 or page_size > 100:
        page_size = 20

    items = (
        q.order_by(CaseStudy.sort_order, CaseStudy.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    # 构建响应数据
    result_items = [_safe_case_study_dict(item) for item in items]
    return success_response(
        data={
            "items": result_items,
            "total": total,
            "page": page,
            "page_size": page_size})


@router.get("/{case_id}")
@cache_response(expire=180, prefix="case_study_detail")
async def get_case_study(
    case_id: str,
    db: Session = Depends(get_db),
):
    """获取单个案例详情（公开）- 优化：使用joinedload预加载图片"""
    case = (
        db.query(CaseStudy)
        .options(joinedload(CaseStudy.images), joinedload(CaseStudy.product))
        .filter(CaseStudy.id == case_id, CaseStudy.is_active)
        .first()
    )
    if not case:
        return error_response(404, "案例不存在")

    # 更新访问计数
    case.view_count += 1
    db.commit()
    # 构建响应数据
    case_dict = _safe_case_study_dict(case)
    return success_response(data=case_dict)


@router.post("/{case_id}/images", response_model=APIResponse)
@invalidate_cache(pattern="case_studies")
async def add_case_study_image(
    case_id: str,
    payload: CaseImageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """为案例添加一张图片"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin", "editor"]:
        return error_response(403, "权限不足")
    case = db.query(CaseStudy).filter(CaseStudy.id == case_id).first()
    if not case:
        return error_response(404, "案例不存在")
    img = CaseImage(
        id=str(uuid.uuid4()),
        case_id=case_id,
        image_url=payload.image_url,
        image_alt=payload.image_alt,
        sort_order=payload.sort_order,
    )
    db.add(img)
    db.commit()
    db.refresh(img)
    return success_response(
        data={"id": str(img.id), "image_url": img.image_url},
        message="图片已添加",
    )


@router.post("/")
@invalidate_cache(pattern="case_studies")
async def create_case_study(
        req: CaseStudyCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)):
    """创建案例"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")

    slug = req.get("slug")
    if db.query(CaseStudy).filter(CaseStudy.slug == slug).first():
        return error_response(400, "slug已存在")

    case = CaseStudy(**req)
    db.add(case)
    db.commit()
    db.refresh(case)
    return success_response(data=_safe_case_study_dict(case), message="案例创建成功")


@router.put("/{case_id}")
@invalidate_cache(pattern="case_studies")
async def update_case_study(
        case_id: str,
        req: CaseStudyUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)):
    """更新案例"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")

    case = db.query(CaseStudy).filter(CaseStudy.id == case_id).first()
    if not case:
        return error_response(404, "案例不存在")

    slug = req.get("slug")
    if slug:
        existing = db.query(CaseStudy).filter(
            CaseStudy.slug == slug, CaseStudy.id != case_id).first()
        if existing:
            return error_response(400, "slug已存在")

    for k, v in req.items():
        if hasattr(case, k):
            setattr(case, k, v)
    db.commit()
    db.refresh(case)
    return success_response(data=_safe_case_study_dict(case), message="案例更新成功")


@router.delete("/{case_id}")
@invalidate_cache(pattern="case_studies")
async def delete_case_study(
        case_id: str,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)):
    """删除案例"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")

    case = db.query(CaseStudy).filter(CaseStudy.id == case_id).first()
    if not case:
        return error_response(404, "案例不存在")

    db.delete(case)
    db.commit()
    return success_response(message="案例删除成功")
