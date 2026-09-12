"""产品管理路由 - 优化版 - 添加缓存和优化查询"""

import csv
import logging
from io import StringIO
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session, joinedload

from app.core.cache_decorator import cache_response, invalidate_cache
from app.core.response import APIResponse, error_response, success_response
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.product import (CategoryCreate, CategoryResponse,
                                 CategoryTreeResponse, CategoryUpdate,
                                 ProductCreate, ProductDocumentResponse,
                                 ProductListResponse, ProductResponse,
                                 ProductUpdate)
from app.services.product_service import (CategoryService,
                                          ProductDocumentService,
                                          ProductService)


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = "/products"
ROUTE_TAGS = ["产品管理"]

router = APIRouter(tags=["产品管理"])

_EDITOR_ROLES = frozenset({"admin", "super_admin", "tenant_admin", "editor"})
_ADMIN_ROLES = frozenset({"admin", "super_admin", "tenant_admin"})


def _guard_product_user(user: User | None, *, admin_only: bool = False):
    """避免未登录时 current_user 为 None 导致 500。"""
    if user is None:
        return error_response(401, "未登录")
    allowed = _ADMIN_ROLES if admin_only else _EDITOR_ROLES
    if user.role not in allowed:
        return error_response(403, "权限不足")
    return None


class BatchProductIdsBody(BaseModel):
    ids: List[str] = Field(default_factory=list)
    product_ids: List[str] = Field(default_factory=list)
    def combined_ids(self) -> List[str]:
        """执行 combined_ids 相关逻辑处理。
        
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return self.product_ids if self.product_ids else self.ids


class BatchStatusBody(BatchProductIdsBody):
    is_active: bool = True


@router.get("/categories", response_model=APIResponse[List[CategoryResponse]])
@cache_response(expire=600, prefix="product_categories")
async def list_categories(db: Session = Depends(get_db)):
    """获取分类列表 - 缓存优化"""
    service = CategoryService(db)
    categories = service.list_categories()
    return success_response(
        data=[CategoryResponse.model_validate(c) for c in categories])


@router.get("/categories/tree")
@cache_response(expire=600, prefix="category_tree")
async def get_category_tree(db: Session = Depends(get_db)):
    """获取分类树 - 缓存优化"""
    service = CategoryService(db)
    tree = service.get_category_tree()
    import json
    from datetime import datetime
    def json_serial(obj):
        """执行 json_serial 相关逻辑处理。
        
        :param obj: 参数 obj
        :return: 返回处理结果。
        :raises: TypeError 等异常在错误时抛出。
        """
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")
    
    content = {
        "code": 0,
        "message": "success",
        "data": [t.model_dump() for t in tree],
        "total": None,
        "page": None,
        "page_size": None,
    }
    return Response(
        content=json.dumps(content, ensure_ascii=False, default=json_serial),
        media_type="application/json",
    )


@router.get("/categories/{category_id}",
            response_model=APIResponse[CategoryResponse])
async def get_category(category_id: str, db: Session = Depends(get_db)):
    """获取单个分类"""
    service = CategoryService(db)
    category = service.get_category(category_id)
    if not category:
        return error_response(404, "分类不存在")

    return success_response(data=CategoryResponse.model_validate(category))


@router.post("/categories", response_model=APIResponse[CategoryResponse])
@invalidate_cache(pattern="category")
async def create_category(
        category_data: CategoryCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)):
    """创建分类"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin", "editor"]:
        return error_response(403, "权限不足")

    service = CategoryService(db)
    try:
        category = service.create_category(
            category_data, created_by=current_user.id)
        return success_response(
            data=CategoryResponse.model_validate(category),
            message="分类创建成功")
    except ValueError as e:
        return error_response(400, str(e))


@router.put("/categories/{category_id}",
            response_model=APIResponse[CategoryResponse])
@invalidate_cache(pattern="category")
async def update_category(
    category_id: str,
    category_data: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新分类"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin", "editor"]:
        return error_response(403, "权限不足")

    service = CategoryService(db)
    category = service.update_category(
        category_id, category_data, updated_by=current_user.id)

    if not category:
        return error_response(404, "分类不存在")

    return success_response(
        data=CategoryResponse.model_validate(category),
        message="分类更新成功")


@router.delete("/categories/{category_id}", response_model=APIResponse)
@invalidate_cache(pattern="category")
async def delete_category(
        category_id: str,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)):
    """删除分类"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")

    service = CategoryService(db)
    if not service.delete_category(category_id, deleted_by=current_user.id):
        return error_response(404, "分类不存在")

    return success_response(message="分类删除成功")


@router.get("/", response_model=APIResponse[ProductListResponse])
@cache_response(expire=300, prefix="products_list")
async def list_products(
    page: int = 1,
    page_size: int = 20,
    category_id: str = None,
    is_active: str = None,
    search: str = None,
    db: Session = Depends(get_db),
):
    """获取产品列表（分页）- 缓存优化 + 分页验证"""
    # 分页验证
    if page < 1:
        page = 1
    if page_size < 1 or page_size > 100:
        page_size = 20

    service = ProductService(db)
    active_filter = None
    if is_active is not None:
        active_filter = is_active.lower() == "true"

    products, total = service.list_products(
        page=page, page_size=page_size, category_id=category_id, is_active=active_filter, search=search)

    return success_response(
        data=ProductListResponse(
            items=[
                ProductResponse.model_validate(p) for p in products],
            total=total,
            page=page,
            page_size=page_size))


@router.get("/popular", response_model=APIResponse[List[ProductResponse]])
@cache_response(expire=300, prefix="popular_products")
async def get_popular_products(limit: int = 10, db: Session = Depends(get_db)):
    """获取热门产品 - 缓存优化"""
    if limit < 1 or limit > 50:
        limit = 10
    service = ProductService(db)
    products = service.get_popular_products(limit)
    return success_response(
        data=[ProductResponse.model_validate(p) for p in products])


@router.get("/sitemap-feed")
@cache_response(expire=3600, prefix="product_sitemap_feed")
async def get_sitemap_feed(limit: int = 500, db: Session = Depends(get_db)):
    """Sitemap 专用产品数据 — 含图片/视频/alt 文本，供搜索引擎收录。

    返回精简但 SEO 完整的产品数据，不包含重量级字段。
    """
    from app.models.product import Product, ProductImage
    from app.models.media_factory import MediaRenderTask
    products = db.query(Product).filter(
        Product.is_active.is_(True),
    ).order_by(Product.updated_at.desc()).limit(limit).all()
    result = []
    for p in products:
        # 产品图片
        images = []
        try:
            imgs = db.query(ProductImage).filter(
                ProductImage.product_id == str(p.id),
            ).order_by(ProductImage.sort_order.asc()).limit(10).all()
            images = [
                {"image_url": img.image_url, "alt_text": img.alt_text or p.name}
                for img in imgs if img.image_url
            ]
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.warning("查询产品图片失败: %s", e)
            pass

        # 产品关联视频（最近成功的渲染任务）
        video_url = None
        video_title = None
        try:
            vid = db.query(MediaRenderTask).filter(
                MediaRenderTask.tenant_id == str(getattr(p, 'tenant_id', '')),
                MediaRenderTask.status == "success",
            ).order_by(MediaRenderTask.created_at.desc()).first()
            if vid and vid.result_url:
                video_url = vid.result_url
                video_title = vid.title
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.warning("查询产品关联视频失败: %s", e)
            pass
        item = {
            "slug": p.slug,
            "name": p.name,
            "description": (p.description or "")[:300],
            "image_url": p.image_url,
            "updated_at": p.updated_at.isoformat() if p.updated_at else None,
            "images": images,
        }
        if video_url:
            item["video_url"] = video_url
            item["video_title"] = video_title or p.name
            item["video_thumbnail"] = p.image_url
        result.append(item)

    return {"data": result}


@router.get("/export")
@invalidate_cache(pattern="product")
async def export_products(
    request: Request,
    is_active: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """导出产品为 CSV（管理端/测试用）"""
    from app.core.data_export_guard import assert_export_allowed
    if current_user.role not in ["admin", "super_admin", "tenant_admin", "editor"]:
        raise HTTPException(status_code=403, detail="权限不足")

    scope = (
        "platform"
        if current_user.role in ("super_admin", "admin")
        else "tenant"
    )
    service = ProductService(db)
    active_filter = None
    if is_active is not None:
        active_filter = is_active.lower() == "true"

    products, _ = service.list_products(
        page=1,
        page_size=5000,
        category_id=None,
        is_active=active_filter,
        search=None,
    )
    assert_export_allowed(
        db,
        current_user,
        request,
        export_kind="products_csv",
        scope=scope,
        row_count=len(products),
    )
    buf = StringIO()
    writer = csv.writer(buf)
    writer.writerow(["id", "name", "slug", "category_id",
                    "description", "density", "strength", "is_active"])
    for p in products:
        writer.writerow(
            [
                str(p.id),
                p.name,
                p.slug,
                str(p.category_id),
                (p.description or "").replace("\n", " "),
                p.density or "",
                p.strength or "",
                p.is_active,
            ]
        )

    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue().encode("utf-8-sig")]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="products.csv"'},
    )


@router.post("/import", response_model=APIResponse)
@invalidate_cache(pattern="product")
async def import_products_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """从 CSV 批量导入产品（最小实现：满足测试与后台批量录入）"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin", "editor"]:
        return error_response(403, "权限不足")

    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="仅支持 .csv 文件")

    raw = await file.read()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("utf-8", errors="replace")

    reader = csv.DictReader(StringIO(text))
    if not reader.fieldnames:
        raise HTTPException(status_code=400, detail="CSV 无表头")

    service = ProductService(db)
    imported = 0
    for row in reader:
        name = (row.get("name") or "").strip()
        slug = (row.get("slug") or "").strip()
        category_id = (row.get("category_id") or "").strip()
        if not name or not slug or not category_id:
            continue
        try:
            payload = ProductCreate(
                category_id=category_id,
                name=name,
                slug=slug,
                description=(row.get("description") or "").strip() or None,
                density=(row.get("density") or "").strip() or None,
                strength=(row.get("strength") or "").strip() or None,
            )
            service.create_product(payload, created_by=current_user.id)
            imported += 1
        except ValueError:
            continue

    return success_response(
        data={"imported_count": imported, "message": f"导入完成 {imported} 条"},
        message="导入完成",
    )


@router.get("/slug/{slug}", response_model=APIResponse[ProductResponse])
@cache_response(expire=180, prefix="product_by_slug")
async def get_product_by_slug(slug: str, db: Session = Depends(get_db)):
    """根据slug获取产品 - 缓存优化"""
    service = ProductService(db)
    product = service.get_product_by_slug(slug)
    if not product:
        return error_response(404, "产品不存在")

    return success_response(data=ProductResponse.model_validate(product))


@router.post("/{product_id}/increment-view", response_model=APIResponse)
@invalidate_cache(pattern="product")
async def increment_product_view(product_id: str, db: Session = Depends(get_db)):
    """增加产品浏览次数（公开可读统计）"""
    service = ProductService(db)
    new_count = service.increment_view_count(product_id)
    if new_count <= 0:
        return error_response(404, "产品不存在")
    return success_response(data={"view_count": new_count})


@router.get("/{product_id}", response_model=APIResponse[ProductResponse])
@cache_response(expire=180, prefix="product_detail")
async def get_product(product_id: str, db: Session = Depends(get_db)):
    """获取单个产品 - 缓存优化"""
    service = ProductService(db)
    product = service.get_product(product_id)
    if not product:
        return error_response(404, "产品不存在")

    return success_response(data=ProductResponse.model_validate(product))


@router.post("/", response_model=APIResponse[ProductResponse])
@invalidate_cache(pattern="product")
async def create_product(
        product_data: ProductCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)):
    """创建产品"""
    denied = _guard_product_user(current_user)
    if denied is not None:
        return denied

    service = ProductService(db)
    try:
        product = service.create_product(
            product_data, created_by=current_user.id)
        return success_response(
            data=ProductResponse.model_validate(product),
            message="产品创建成功")
    except ValueError as e:
        return error_response(400, str(e))


@router.put("/{product_id}", response_model=APIResponse[ProductResponse])
@invalidate_cache(pattern="product")
async def update_product(
    product_id: str,
    product_data: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新产品"""
    denied = _guard_product_user(current_user)
    if denied is not None:
        return denied

    service = ProductService(db)
    try:
        product = service.update_product(
            product_id, product_data, updated_by=current_user.id)
        if not product:
            return error_response(404, "产品不存在")
        return success_response(
            data=ProductResponse.model_validate(product),
            message="产品更新成功")
    except ValueError as e:
        return error_response(400, str(e))


@router.delete("/{product_id}", response_model=APIResponse)
@invalidate_cache(pattern="product")
async def delete_product(
        product_id: str,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)):
    """删除产品"""
    denied = _guard_product_user(current_user, admin_only=True)
    if denied is not None:
        return denied

    service = ProductService(db)
    if not service.delete_product(product_id, deleted_by=current_user.id):
        return error_response(404, "产品不存在")

    return success_response(message="产品删除成功")


@router.post("/batch-delete", response_model=APIResponse)
@invalidate_cache(pattern="product")
async def batch_delete_products(
    body: BatchProductIdsBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """批量删除产品（请求体 JSON：`ids` 或 `product_ids`）"""
    denied = _guard_product_user(current_user, admin_only=True)
    if denied is not None:
        return denied

    product_ids = body.combined_ids()
    if not product_ids:
        raise HTTPException(status_code=400, detail="ids 不能为空")

    service = ProductService(db)
    deleted = service.batch_delete(product_ids, deleted_by=current_user.id)
    return success_response(
        data={"deleted_count": deleted, "message": f"成功删除 {deleted} 个产品"},
        message=f"成功删除 {deleted} 个产品",
    )


@router.post("/batch-status", response_model=APIResponse)
@router.post("/batch-update-status", response_model=APIResponse)
@invalidate_cache(pattern="product")
async def batch_update_status(
    body: BatchStatusBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """批量更新产品状态（别名：/batch-update-status）"""
    denied = _guard_product_user(current_user)
    if denied is not None:
        return denied

    product_ids = body.combined_ids()
    if not product_ids:
        raise HTTPException(status_code=400, detail="ids 不能为空")

    service = ProductService(db)
    updated = service.batch_update_status(
        product_ids, body.is_active, updated_by=current_user.id)

    return success_response(
        data={"updated_count": updated, "message": f"成功更新 {updated} 个产品状态"},
        message=f"成功更新 {updated} 个产品状态",
    )


@router.get("/{product_id}/documents",
            response_model=APIResponse[List[ProductDocumentResponse]])
@cache_response(expire=300, prefix="product_documents")
async def get_product_documents(
        product_id: str,
        db: Session = Depends(get_db)):
    """获取产品文档列表 - 缓存优化"""
    service = ProductDocumentService(db)
    documents = service.get_documents(product_id)
    return success_response(
        data=[ProductDocumentResponse.model_validate(d) for d in documents])


@router.post("/{product_id}/documents",
             response_model=APIResponse[ProductDocumentResponse])
@invalidate_cache(pattern="product")
async def upload_product_document(
    product_id: str,
    file: UploadFile = File(...),
    doc_type: str = "other",
    description: str = "",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """上传产品文档"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin", "editor"]:
        return error_response(403, "权限不足")

    service = ProductDocumentService(db)
    try:
        content = file.file.read()
        document = service.upload_document(
            product_id=product_id,
            file_content=content,
            file_name=file.filename,
            doc_type=doc_type,
            description=description,
            uploaded_by=current_user.id,
        )
        return success_response(
            data=ProductDocumentResponse.model_validate(document),
            message="文档上传成功")
    except ValueError as e:
        return error_response(400, str(e))


@router.delete("/documents/{doc_id}", response_model=APIResponse)
@invalidate_cache(pattern="product")
async def delete_product_document(
        doc_id: str,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)):
    """删除产品文档"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin", "editor"]:
        return error_response(403, "权限不足")

    service = ProductDocumentService(db)
    if not service.delete_document(doc_id, deleted_by=current_user.id):
        return error_response(404, "文档不存在")

    return success_response(message="文档删除成功")
