"""内容管理路由 - 优化版 - 添加缓存和分页验证"""

from typing import List

from fastapi import APIRouter, Depends, File, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.cache_decorator import cache_response, invalidate_cache
from app.core.response import APIResponse, error_response, success_response
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.content import (ContentPageCreate, ContentPageListResponse,
                                 ContentPageResponse, ContentPageUpdate,
                                 ContentVersionResponse, SeoMetadataCreate,
                                 SeoMetadataResponse, SeoMetadataUpdate)
from app.services.content_service import (ContentPageService,
                                          ContentVersionService,
                                          SeoMetadataService)


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = "/content"
ROUTE_TAGS = ["内容管理"]

router = APIRouter(tags=["内容管理"])


@router.get("", summary="内容管理根路径")
@router.get("/", summary="内容管理根路径(尾斜杠)")
async def content_index():
    """内容管理模块概览 — 解决 /api/v1/content 404 链路断点
    Returns:
        模块说明与可用的子路由清单
    """
    return success_response(
        data={
            "module": "content",
            "description": "内容管理(CMS):页面、版本、SEO 元数据、批量操作",
            "endpoints": {
                "GET    /api/v1/content/pages": "分页获取页面列表",
                "GET    /api/v1/content/pages/search?keyword=...": "关键词搜索",
                "GET    /api/v1/content/pages/{page_id}": "获取单个页面",
                "POST   /api/v1/content/pages": "创建页面",
                "PUT    /api/v1/content/pages/{page_id}": "更新页面",
                "DELETE /api/v1/content/pages/{page_id}": "删除页面",
                "POST   /api/v1/content/pages/batch-delete": "批量删除",
                "POST   /api/v1/content/pages/batch-publish": "批量发布",
                "POST   /api/v1/content/pages/upload-image": "上传页面图片",
                "GET    /api/v1/content/pages/stats/summary": "页面统计",
                "GET    /api/v1/content/versions/{page_id}": "版本历史",
            },
            "auth_required": True,
        }
    )


@router.get("/pages", response_model=APIResponse[ContentPageListResponse])
@cache_response(expire=300, prefix="content_pages")
async def list_pages(
    page: int = 1,
    page_size: int = 20,
    page_type: str = None,
    is_published: str = None,
    search: str = None,
    db: Session = Depends(get_db),
):
    """获取页面列表（分页）- 缓存优化 + 分页验证"""
    # 分页验证
    if page < 1:
        page = 1
    if page_size < 1 or page_size > 100:
        page_size = 20

    service = ContentPageService(db)
    pages, total = service.list_pages(
        page_type=page_type, page=page, page_size=page_size, search=search, is_published=is_published)

    return success_response(
        data=ContentPageListResponse(
            items=[
                ContentPageResponse.model_validate(p) for p in pages],
            total=total,
            page=page,
            page_size=page_size))


@router.get("/pages/search",
            response_model=APIResponse[ContentPageListResponse])
@cache_response(expire=300, prefix="content_search")
async def search_pages(
        keyword: str,
        page: int = 1,
        page_size: int = 20,
        db: Session = Depends(get_db)):
    """搜索页面 - 缓存优化 + 分页验证"""
    if page < 1:
        page = 1
    if page_size < 1 or page_size > 100:
        page_size = 20

    service = ContentPageService(db)
    pages, total = service.search_pages(keyword, page, page_size)
    return success_response(
        data=ContentPageListResponse(
            items=[
                ContentPageResponse.model_validate(p) for p in pages],
            total=total,
            page=page,
            page_size=page_size))


@router.get("/pages/slug/{slug}",
            response_model=APIResponse[ContentPageResponse])
@cache_response(expire=180, prefix="content_page_by_slug")
async def get_page_by_slug(slug: str, db: Session = Depends(get_db)):
    """根据slug获取页面（前台展示用）- 缓存优化"""
    service = ContentPageService(db)
    page = service.get_page_by_slug(slug)
    if not page:
        return error_response(404, "页面不存在")

    if page.status != "published":
        return error_response(403, "页面未发布")

    return success_response(data=ContentPageResponse.model_validate(page))


@router.get("/pages/stats", response_model=APIResponse)
async def get_page_stats(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)):
    """获取页面统计信息"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")

    service = ContentPageService(db)
    stats = service.get_stats()
    return success_response(data=stats)


@router.post("/pages/batch-delete", response_model=APIResponse)
@invalidate_cache(pattern="content")
async def batch_delete_pages(
        page_ids: List[str],
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)):
    """批量删除页面"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")

    service = ContentPageService(db)
    deleted = service.batch_delete(page_ids, deleted_by=current_user.id)
    return success_response(message=f"成功删除 {deleted} 个页面")


@router.post("/pages/batch-publish", response_model=APIResponse)
@invalidate_cache(pattern="content")
async def batch_publish_pages(
        page_ids: List[str],
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)):
    """批量发布页面"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin", "editor"]:
        return error_response(403, "权限不足")

    service = ContentPageService(db)
    published = service.batch_publish(page_ids, published_by=current_user.id)
    return success_response(message=f"成功发布 {published} 个页面")


@router.post("/pages/upload-image", response_model=APIResponse)
async def upload_image(
        db: Session = Depends(get_db),
        file: UploadFile = File(...),
        current_user: User = Depends(get_current_user)):
    """上传图片"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin", "editor"]:
        return error_response(403, "权限不足")

    service = ContentPageService(db)
    try:
        content = file.file.read()
        result = service.upload_image(content, file.filename)
        return success_response(data=result, message="图片上传成功")
    except ValueError as e:
        return error_response(400, str(e))


@router.get("/pages/{page_id}",
            response_model=APIResponse[ContentPageResponse])
@cache_response(expire=180, prefix="content_page_detail")
async def get_page(page_id: str, db: Session = Depends(get_db)):
    """获取单个页面 - 缓存优化"""
    service = ContentPageService(db)
    page = service.get_page(page_id)
    if not page:
        return error_response(404, "页面不存在")

    return success_response(data=ContentPageResponse.model_validate(page))


@router.post("/pages", response_model=APIResponse[ContentPageResponse])
@invalidate_cache(pattern="content")
async def create_page(
        page_data: ContentPageCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)):
    """创建页面"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin", "editor"]:
        return error_response(403, "权限不足")

    service = ContentPageService(db)
    try:
        page = service.create_page(page_data, created_by=current_user.id)
        return success_response(
            data=ContentPageResponse.model_validate(page),
            message="页面创建成功")
    except ValueError as e:
        return error_response(400, str(e))


@router.put("/pages/{page_id}",
            response_model=APIResponse[ContentPageResponse])
@invalidate_cache(pattern="content")
async def update_page(
    page_id: str,
    page_data: ContentPageUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新页面"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin", "editor"]:
        return error_response(403, "权限不足")

    service = ContentPageService(db)
    try:
        page = service.update_page(
            page_id, page_data, updated_by=current_user.id)
        if not page:
            return error_response(404, "页面不存在")
        return success_response(
            data=ContentPageResponse.model_validate(page),
            message="页面更新成功")
    except ValueError as e:
        return error_response(400, str(e))


@router.delete("/pages/{page_id}", response_model=APIResponse)
@invalidate_cache(pattern="content")
async def delete_page(
        page_id: str,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)):
    """删除页面"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")

    service = ContentPageService(db)
    if not service.delete_page(page_id, deleted_by=current_user.id):
        return error_response(404, "页面不存在")

    return success_response(message="页面删除成功")


@router.get("/pages/{page_id}/seo",
            response_model=APIResponse[SeoMetadataResponse])
async def get_page_seo_meta(page_id: str, db: Session = Depends(get_db)):
    """获取页面SEO元数据"""
    service = SeoMetadataService(db)
    seo_meta = service.get_page_seo_meta(page_id)
    if not seo_meta:
        return error_response(404, "SEO元数据不存在")

    return success_response(data=SeoMetadataResponse.model_validate(seo_meta))


@router.post("/pages/{page_id}/seo",
             response_model=APIResponse[SeoMetadataResponse])
@invalidate_cache(pattern="content")
async def create_page_seo_meta(
    page_id: str,
    seo_data: SeoMetadataCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建页面SEO元数据"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin", "editor"]:
        return error_response(403, "权限不足")

    seo_data.resource_type = "page"
    seo_data.resource_id = page_id
    service = SeoMetadataService(db)
    seo_meta = service.create_seo_meta(seo_data, created_by=current_user.id)
    return success_response(
        data=SeoMetadataResponse.model_validate(seo_meta),
        message="SEO元数据创建成功")


@router.put("/pages/{page_id}/seo",
            response_model=APIResponse[SeoMetadataResponse])
@invalidate_cache(pattern="content")
async def update_page_seo_meta(
    page_id: str,
    seo_data: SeoMetadataUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新页面SEO元数据"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin", "editor"]:
        return error_response(403, "权限不足")

    service = SeoMetadataService(db)
    seo_meta = service.update_page_seo_meta(
        page_id, seo_data, updated_by=current_user.id)

    return success_response(
        data=SeoMetadataResponse.model_validate(seo_meta),
        message="SEO元数据更新成功")


@router.get("/pages/{page_id}/versions",
            response_model=APIResponse[List[ContentVersionResponse]])
async def list_page_versions(
        page_id: str,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)):
    """获取页面版本列表"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin", "editor"]:
        return error_response(403, "权限不足")

    service = ContentVersionService(db)
    try:
        versions = service.list_versions(page_id)
        return success_response(
            data=[ContentVersionResponse.model_validate(v) for v in versions])
    except ValueError as e:
        return error_response(404, str(e))


@router.post("/pages/{page_id}/versions",
             response_model=APIResponse[ContentVersionResponse])
@invalidate_cache(pattern="content")
async def create_page_version(
        page_id: str,
        change_note: str = None,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)):
    """创建页面版本"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin", "editor"]:
        return error_response(403, "权限不足")

    service = ContentVersionService(db)
    try:
        version = service.create_version(
            page_id, change_note, author_id=current_user.id)
        return success_response(
            data=ContentVersionResponse.model_validate(version),
            message="版本创建成功")
    except ValueError as e:
        return error_response(400, str(e))


@router.get("/pages/{page_id}/versions/{version_id}",
            response_model=APIResponse[ContentVersionResponse])
async def get_page_version(
        page_id: str,
        version_id: str,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)):
    """获取指定版本"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin", "editor"]:
        return error_response(403, "权限不足")

    service = ContentVersionService(db)
    version = service.get_version(page_id, version_id)
    if not version:
        return error_response(404, "版本不存在")

    return success_response(data=ContentVersionResponse.model_validate(version))


@router.post("/pages/{page_id}/versions/{version_id}/rollback",
             response_model=APIResponse[ContentPageResponse])
@invalidate_cache(pattern="content")
async def rollback_to_version(
        page_id: str,
        version_id: str,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)):
    """回滚到指定版本"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin", "editor"]:
        return error_response(403, "权限不足")

    service = ContentVersionService(db)
    try:
        page = service.rollback_to_version(
            page_id, version_id, rolled_by=current_user.id)
        return success_response(
            data=ContentPageResponse.model_validate(page),
            message="页面已回滚到指定版本")
    except ValueError as e:
        return error_response(400, str(e))


_SEO_RESOURCE_TYPES = frozenset({"product", "case_study", "page"})


@router.get("/seo/{resource_type}/{resource_id}",
            response_model=APIResponse[SeoMetadataResponse])
@cache_response(expire=180, prefix="seo_meta_resource")
async def get_seo_by_resource(
    resource_type: str,
    resource_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """按资源类型获取 SEO 元数据（产品 / 案例 / 页面）"""
    if resource_type not in _SEO_RESOURCE_TYPES:
        return error_response(400, "不支持的资源类型")
    if current_user.role not in ["admin", "super_admin", "tenant_admin", "editor"]:
        return error_response(403, "权限不足")
    service = SeoMetadataService(db)
    meta = service.get_seo_meta(resource_type, resource_id)
    if not meta:
        return error_response(404, "SEO元数据不存在")
    return success_response(data=SeoMetadataResponse.model_validate(meta))


@router.put("/seo/{resource_type}/{resource_id}",
            response_model=APIResponse[SeoMetadataResponse])
@invalidate_cache(pattern="content")
async def upsert_seo_by_resource(
    resource_type: str,
    resource_id: str,
    seo_data: SeoMetadataUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新指定资源的 SEO 元数据"""
    if resource_type not in _SEO_RESOURCE_TYPES:
        return error_response(400, "不支持的资源类型")
    if current_user.role not in ["admin", "super_admin", "tenant_admin", "editor"]:
        return error_response(403, "权限不足")
    service = SeoMetadataService(db)
    meta = service.update_seo_meta(
        resource_type,
        resource_id,
        seo_data,
        updated_by=current_user.id)
    return success_response(
        data=SeoMetadataResponse.model_validate(meta),
        message="SEO已更新")


@router.post("/seo", response_model=APIResponse[SeoMetadataResponse])
@invalidate_cache(pattern="content")
async def create_seo_resource(
    seo_data: SeoMetadataCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建 SEO 元数据（需指定 resource_type / resource_id）"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin", "editor"]:
        return error_response(403, "权限不足")
    if seo_data.resource_type not in _SEO_RESOURCE_TYPES:
        return error_response(400, "不支持的资源类型")
    service = SeoMetadataService(db)
    meta = service.create_seo_meta(seo_data, created_by=current_user.id)
    return success_response(
        data=SeoMetadataResponse.model_validate(meta),
        message="SEO创建成功")


class ProductAIGenerateBody(BaseModel):
    content_type: str = "product"
    keywords: list[str] = []
    product_name: str = ""
    category_name: str = ""
    density: float | None = None
    strength_grade: str = ""
    thermal_conductivity: float | None = None
    fire_rating: str = ""
    existing_description: str = ""


class ProductAIPolishBody(BaseModel):
    content: str = ""
    polish_type: str = "general"


@router.post("/ai/generate")
async def ai_generate_product_content(
    body: ProductAIGenerateBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """产品编辑页 — AI 生成描述/SEO 标题/SEO 描述（NVIDIA NIM 等场景模型）。"""
    if current_user.role not in ("admin", "super_admin", "tenant_admin", "editor", "operator", "user"):
        return error_response(403, "权限不足")
    from app.services.product_content_ai_service import generate_product_content
    from app.services.tenant_scenario_service import resolve_tenant_id_for_user
    tenant_id = resolve_tenant_id_for_user(db, current_user)
    try:
        data = await generate_product_content(
            db,
            payload=body.model_dump(),
            tenant_id=tenant_id,
        )
    except RuntimeError as exc:
        return error_response(503, str(exc))
    return success_response(data=data, message="生成成功")


@router.post("/ai/polish")
async def ai_polish_product_content(
    body: ProductAIPolishBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """产品编辑页 — AI 润色描述/SEO 描述。"""
    if current_user.role not in ("admin", "super_admin", "tenant_admin", "editor", "operator", "user"):
        return error_response(403, "权限不足")
    from app.services.product_content_ai_service import polish_product_content
    from app.services.tenant_scenario_service import resolve_tenant_id_for_user
    tenant_id = resolve_tenant_id_for_user(db, current_user)
    try:
        data = await polish_product_content(
            db,
            content=body.content,
            polish_type=body.polish_type,
            tenant_id=tenant_id,
        )
    except ValueError as exc:
        return error_response(400, str(exc))
    except RuntimeError as exc:
        return error_response(503, str(exc))
    return success_response(data=data, message="润色成功")
