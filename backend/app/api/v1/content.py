import os
import uuid
import re
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Body, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_
from pydantic import BaseModel, Field
from typing import List, Optional
from app.core.database import get_db
from app.core.security import require_admin
from app.models.content import ContentPage, SeoMetadata, ContentVersion
from app.schemas.content import ContentPageCreate, ContentPageUpdate, ContentPageResponse, SeoMetadataCreate, SeoMetadataUpdate, SeoMetadataResponse, ContentVersionCreate, ContentVersionResponse, ContentRollbackRequest

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

router = APIRouter()

@router.post("/upload")
async def upload_image(file: UploadFile = File(...), admin = Depends(require_admin)):
    ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp"}
    ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
    
    if not file.filename or "." not in file.filename:
        raise HTTPException(status_code=400, detail="无效的文件名")
    
    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"不支持的图片格式: .{ext}，仅支持 {', '.join(ALLOWED_EXTENSIONS)}")
    
    if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail=f"不允许的文件类型: {file.content_type}")
    
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    content = await file.read()
    
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件大小不能超过 5MB")
    
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="文件内容为空")
    
    with open(filepath, "wb") as f:
        f.write(content)
    
    return {"url": f"/uploads/{filename}", "filename": filename}

@router.get("/pages")
def list_pages(
    page_type: str = None, 
    page: int = 1, 
    page_size: int = 20,
    search: str = None,
    is_published: str = None,
    db: Session = Depends(get_db)
):
    q = db.query(ContentPage).filter(ContentPage.is_active == True)
    if page_type:
        q = q.filter(ContentPage.page_type == page_type)
    if search:
        q = q.filter(ContentPage.title.contains(search) | ContentPage.summary.contains(search))
    if is_published is not None:
        q = q.filter(ContentPage.status == ("published" if is_published == "true" else "draft"))
    
    total = q.count()
    items = q.order_by(ContentPage.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    return {"items": [ContentPageResponse.model_validate(page.__dict__) for page in items], "total": total}

@router.get("/pages/{page_id}", response_model=ContentPageResponse)
def get_page(page_id: str, db: Session = Depends(get_db)):
    page = db.query(ContentPage).filter(ContentPage.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="页面不存在")
    return page

@router.get("/pages/slug/{slug}", response_model=ContentPageResponse)
def get_page_by_slug(slug: str, db: Session = Depends(get_db)):
    page = db.query(ContentPage).filter(ContentPage.slug == slug, ContentPage.is_active == True).first()
    if not page:
        raise HTTPException(status_code=404, detail="页面不存在")
    page.view_count += 1
    db.commit()
    return page

@router.post("/pages", response_model=ContentPageResponse)
def create_page(req: ContentPageCreate, db: Session = Depends(get_db), admin = Depends(require_admin)):
    page = ContentPage(**req.model_dump())
    db.add(page)
    db.commit()
    db.refresh(page)
    return page

@router.put("/pages/{page_id}", response_model=ContentPageResponse)
def update_page(page_id: str, req: ContentPageUpdate, db: Session = Depends(get_db), admin = Depends(require_admin)):
    page = db.query(ContentPage).filter(ContentPage.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="页面不存在")
    for k, v in req.model_dump(exclude_unset=True).items():
        setattr(page, k, v)
    db.commit()
    db.refresh(page)
    return page

@router.delete("/pages/{page_id}")
def delete_page(page_id: str, db: Session = Depends(get_db), admin = Depends(require_admin)):
    page = db.query(ContentPage).filter(ContentPage.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="页面不存在")
    db.delete(page)
    db.commit()
    return {"message": "删除成功"}

@router.get("/seo/{resource_type}/{resource_id}", response_model=SeoMetadataResponse)
def get_seo_meta(resource_type: str, resource_id: str, db: Session = Depends(get_db)):
    meta = db.query(SeoMetadata).filter(
        SeoMetadata.resource_type == resource_type,
        SeoMetadata.resource_id == resource_id
    ).first()
    if not meta:
        raise HTTPException(status_code=404, detail="SEO元数据不存在")
    return meta

@router.get("/seo/page/{resource_id}", response_model=SeoMetadataResponse)
def get_page_seo_meta(resource_id: str, db: Session = Depends(get_db)):
    meta = db.query(SeoMetadata).filter(
        SeoMetadata.resource_type == "page",
        SeoMetadata.resource_id == resource_id
    ).first()
    if not meta:
        raise HTTPException(status_code=404, detail="SEO元数据不存在")
    return meta

@router.put("/seo/page/{resource_id}", response_model=SeoMetadataResponse)
def update_page_seo_meta(resource_id: str, req: SeoMetadataUpdate, db: Session = Depends(get_db), admin = Depends(require_admin)):
    meta = db.query(SeoMetadata).filter(
        SeoMetadata.resource_type == "page",
        SeoMetadata.resource_id == resource_id
    ).first()
    if not meta:
        from app.schemas.content import SeoMetadataCreate as SeoCreate
        create_req = SeoCreate(
            resource_type="page",
            resource_id=resource_id,
            meta_title=req.meta_title,
            meta_description=req.meta_description,
            meta_keywords=req.meta_keywords,
            canonical_url=req.canonical_url,
            og_title=req.og_title,
            og_description=req.og_description,
            og_image=req.og_image,
            schema_markup=req.schema_markup,
            noindex=req.noindex,
            h1_tag=req.h1_tag
        )
        meta = SeoMetadata(**create_req.model_dump())
        db.add(meta)
        db.commit()
        db.refresh(meta)
        return meta
    for k, v in req.model_dump(exclude_unset=True).items():
        setattr(meta, k, v)
    db.commit()
    db.refresh(meta)
    return meta

@router.post("/seo", response_model=SeoMetadataResponse)
def create_seo_meta(req: SeoMetadataCreate, db: Session = Depends(get_db), admin = Depends(require_admin)):
    meta = SeoMetadata(**req.model_dump())
    db.add(meta)
    db.commit()
    db.refresh(meta)
    return meta

@router.put("/seo/{resource_type}/{resource_id}", response_model=SeoMetadataResponse)
def update_seo_meta(resource_type: str, resource_id: str, req: SeoMetadataUpdate, db: Session = Depends(get_db), admin = Depends(require_admin)):
    meta = db.query(SeoMetadata).filter(
        SeoMetadata.resource_type == resource_type,
        SeoMetadata.resource_id == resource_id
    ).first()
    if not meta:
        raise HTTPException(status_code=404, detail="SEO元数据不存在")
    for k, v in req.model_dump(exclude_unset=True).items():
        setattr(meta, k, v)
    db.commit()
    db.refresh(meta)
    return meta

@router.post("/ai/generate")
async def ai_generate_content(
    request: dict = Body(...),
    db: Session = Depends(get_db),
    admin = Depends(require_admin)
):
    """AI生成内容接口"""
    from app.services.ai_engine import get_ai_engine
    
    ai_engine = get_ai_engine()
    
    content_type: str = request.get("content_type", "product")
    keywords: list = request.get("keywords", [])
    product_name: str = request.get("product_name", "")
    category_name: str = request.get("category_name", "")
    density: float = request.get("density", 0)
    strength_grade: str = request.get("strength_grade", "")
    thermal_conductivity: float = request.get("thermal_conductivity", 0)
    fire_rating: str = request.get("fire_rating", "")
    existing_description: str = request.get("existing_description", "")
    
    # 构建产品信息字符串
    product_info = []
    if product_name:
        product_info.append(f"产品名称：{product_name}")
    if category_name:
        product_info.append(f"产品分类：{category_name}")
    if density:
        product_info.append(f"干密度：{density} kg/m³")
    if strength_grade:
        product_info.append(f"强度等级：{strength_grade}")
    if thermal_conductivity:
        product_info.append(f"导热系数：{thermal_conductivity} W/m·K")
    if fire_rating:
        product_info.append(f"防火等级：{fire_rating}")
    
    product_info_str = "\n".join(product_info)
    
    if content_type == "product":
        # 生成产品描述
        prompt = f"""请为以下轻集料混凝土产品生成专业、详细的产品描述：

产品信息：
{product_info_str}

关键词：{', '.join(keywords)}

要求：
1. 内容必须与产品名称严格相关，不偏离主题
2. 突出产品特点和核心优势
3. 包含技术参数（密度、强度等级、导热系数等）
4. 语言专业且易于理解
5. 符合SEO优化要求，包含关键词
6. 引用行业标准（如JGJ/T 12-2019）
7. 结构清晰，段落分明
"""
        result = await ai_engine._generate_response(
            ai_engine._get_llm("chinese"),
            prompt,
            "product_description",
            None,
            task_type="product_gen"
        )
    elif content_type == "seo_title":
        # 生成SEO标题（专业中英文SEO引擎）
        prompt = f"""请根据以下产品信息生成专业的SEO标题（建议长度30-60字符）：

产品名称：{product_name}
产品分类：{category_name}
强度等级：{strength_grade}
防火等级：{fire_rating}

要求：
1. 包含核心关键词：{product_name}、{category_name}
2. 突出产品核心卖点
3. 中英文关键词结合（如保温材料/insulation material）
4. 符合搜索引擎优化标准
5. 吸引用户点击，提升CTR
"""
        result = await ai_engine._generate_response(
            ai_engine._get_llm("chinese"),
            prompt,
            "seo_title",
            None,
            task_type="product_gen"
        )
    elif content_type == "seo_description":
        # 生成SEO描述（基于产品信息）
        prompt = f"""请根据以下产品信息生成专业的SEO描述（建议长度80-160字符）：

产品名称：{product_name}
产品分类：{category_name}
干密度：{density} kg/m³
强度等级：{strength_grade}
防火等级：{fire_rating}
导热系数：{thermal_conductivity} W/m·K
产品描述：{existing_description[:300] if existing_description else ''}

要求：
1. 包含核心关键词：{product_name}、{category_name}
2. 突出产品卖点（如节能、防火、高强度等）
3. 吸引用户点击，提升CTR
4. 符合搜索引擎优化要求
5. 语句通顺自然，不堆砌关键词
"""
        result = await ai_engine._generate_response(
            ai_engine._get_llm("chinese"),
            prompt,
            "seo_description",
            None,
            task_type="product_gen"
        )
    else:
        # 默认生成产品描述
        prompt = f"""请生成{content_type}相关内容，关键词：{', '.join(keywords)}"""
        result = await ai_engine._generate_response(
            ai_engine._get_llm("chinese"),
            prompt,
            content_type,
            None,
            task_type="product_gen"
        )
    
    return {
        "content": result.get("optimized_content", result.get("content", "生成失败")),
        "mock": result.get("mock", False),
        "token_usage": result.get("token_usage", 0),
        "cost": result.get("cost", 0)
    }

@router.post("/ai/polish")
async def ai_polish_content(
    request: dict = Body(...),
    db: Session = Depends(get_db),
    admin = Depends(require_admin)
):
    content: str = request.get("content", "")
    polish_type: str = request.get("polish_type", "general")
    """AI润色内容接口"""
    from app.services.ai_engine import get_ai_engine
    
    ai_engine = get_ai_engine()
    
    # 根据润色类型构建提示词
    if polish_type == "professional":
        prompt = f"""请将以下内容润色得更加专业正式：

{content}

要求：
1. 使用专业术语
2. 语气正式商务
3. 保持原意不变
4. 优化句子结构
"""
    elif polish_type == "concise":
        prompt = f"""请将以下内容精简优化：

{content}

要求：
1. 保持核心信息完整
2. 删除冗余内容
3. 提高信息密度
4. 保持原意不变
"""
    elif polish_type == "seo":
        prompt = f"""请优化以下内容使其更符合SEO要求：

{content}

要求：
1. 自然融入相关关键词
2. 优化标题和描述结构
3. 提高内容可读性
4. 保持原意不变
"""
    elif polish_type == "emotional":
        prompt = f"""请将以下内容润色得更有感染力和吸引力：

{content}

要求：
1. 使用更生动的语言
2. 增强情感表达
3. 吸引读者注意力
4. 保持原意不变
"""
    else:
        prompt = f"""请润色以下内容：

{content}

要求：
1. 语法正确
2. 表达流畅自然
3. 保持原意不变
4. 提高可读性
"""
    
    result = await ai_engine._generate_response(
        ai_engine._get_llm("chinese"),
        prompt,
        polish_type,
        None,
        task_type="polish"
    )
    
    return {
        "content": result.get("optimized_content", result.get("content", "润色失败")),
        "mock": result.get("mock", False),
        "token_usage": result.get("token_usage", 0),
        "cost": result.get("cost", 0)
    }


# ============= 版本控制API =============

@router.post("/pages/{page_id}/versions", response_model=ContentVersionResponse)
def create_page_version(page_id: str, req: ContentVersionCreate = None, db: Session = Depends(get_db), admin = Depends(require_admin)):
    page = db.query(ContentPage).filter(ContentPage.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="页面不存在")
    
    max_version = db.query(ContentVersion).filter(ContentVersion.page_id == page_id).count()
    new_version_number = max_version + 1
    
    version = ContentVersion(
        page_id=page_id,
        version_number=new_version_number,
        title=page.title,
        content=page.content,
        summary=page.summary,
        change_log=req.change_log if req else f"版本 {new_version_number}",
        author_id=page.author_id
    )
    db.add(version)
    db.commit()
    db.refresh(version)
    return version


@router.get("/pages/{page_id}/versions", response_model=list[ContentVersionResponse])
def list_page_versions(page_id: str, db: Session = Depends(get_db), admin = Depends(require_admin)):
    page = db.query(ContentPage).filter(ContentPage.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="页面不存在")
    
    return db.query(ContentVersion).filter(
        ContentVersion.page_id == page_id
    ).order_by(ContentVersion.version_number.desc()).all()


@router.get("/pages/{page_id}/versions/{version_id}", response_model=ContentVersionResponse)
def get_page_version(page_id: str, version_id: str, db: Session = Depends(get_db), admin = Depends(require_admin)):
    version = db.query(ContentVersion).filter(
        ContentVersion.id == version_id,
        ContentVersion.page_id == page_id
    ).first()
    if not version:
        raise HTTPException(status_code=404, detail="版本不存在")
    return version


@router.post("/pages/{page_id}/rollback")
def rollback_to_version(page_id: str, req: ContentRollbackRequest, db: Session = Depends(get_db), admin = Depends(require_admin)):
    page = db.query(ContentPage).filter(ContentPage.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="页面不存在")
    
    version = db.query(ContentVersion).filter(
        ContentVersion.id == req.version_id,
        ContentVersion.page_id == page_id
    ).first()
    if not version:
        raise HTTPException(status_code=404, detail="版本不存在")
    
    page.title = version.title
    page.content = version.content
    page.summary = version.summary
    db.commit()
    db.refresh(page)
    
    return {"message": f"已回滚到版本 {version.version_number}", "page": ContentPageResponse.model_validate(page.__dict__)}


# ============= 批量操作API =============

class BatchDeleteRequest(BaseModel):
    ids: List[str] = Field(..., min_items=1, max_items=100)

class BatchUpdateStatusRequest(BaseModel):
    ids: List[str] = Field(..., min_items=1, max_items=100)
    status: str = Field(..., pattern="^(published|draft)$")

class BatchPublishRequest(BaseModel):
    ids: List[str] = Field(..., min_items=1, max_items=100)

def sanitize_html(content: str) -> str:
    """清理HTML内容，防止XSS攻击"""
    dangerous_patterns = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'on\w+\s*=',
        r'<iframe[^>]*>.*?</iframe>',
        r'<object[^>]*>.*?</object>',
        r'<embed[^>]*>.*?</embed>',
        r'<form[^>]*>.*?</form>',
    ]
    for pattern in dangerous_patterns:
        content = re.sub(pattern, '', content, flags=re.IGNORECASE | re.DOTALL)
    return content

@router.post("/pages/batch-delete")
def batch_delete_pages(req: BatchDeleteRequest, db: Session = Depends(get_db), admin = Depends(require_admin)):
    pages = db.query(ContentPage).filter(ContentPage.id.in_(req.ids)).all()
    if not pages:
        raise HTTPException(status_code=404, detail="未找到指定页面")
    
    for page in pages:
        db.delete(page)
    
    db.commit()
    return {"message": f"成功删除 {len(pages)} 个页面", "deleted_count": len(pages)}

@router.post("/pages/batch-update-status")
def batch_update_status(req: BatchUpdateStatusRequest, db: Session = Depends(get_db), admin = Depends(require_admin)):
    pages = db.query(ContentPage).filter(ContentPage.id.in_(req.ids)).all()
    if not pages:
        raise HTTPException(status_code=404, detail="未找到指定页面")
    
    for page in pages:
        page.status = req.status
    
    db.commit()
    return {"message": f"成功更新 {len(pages)} 个页面状态", "updated_count": len(pages)}

@router.post("/pages/batch-publish")
def batch_publish_pages(req: BatchPublishRequest, db: Session = Depends(get_db), admin = Depends(require_admin)):
    from datetime import datetime, timezone
    
    pages = db.query(ContentPage).filter(ContentPage.id.in_(req.ids)).all()
    if not pages:
        raise HTTPException(status_code=404, detail="未找到指定页面")
    
    now = datetime.now(timezone.utc)
    for page in pages:
        page.status = "published"
        page.published_at = now
    
    db.commit()
    return {"message": f"成功发布 {len(pages)} 个页面", "published_count": len(pages)}

@router.get("/pages/export")
def export_pages(
    page_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    admin = Depends(require_admin)
):
    q = db.query(ContentPage).filter(ContentPage.is_active == True)
    if page_type:
        q = q.filter(ContentPage.page_type == page_type)
    if status:
        q = q.filter(ContentPage.status == status)
    
    pages = q.order_by(ContentPage.created_at.desc()).all()
    
    export_data = []
    for page in pages:
        export_data.append({
            "id": page.id,
            "title": page.title,
            "slug": page.slug,
            "content": page.content,
            "summary": page.summary,
            "page_type": page.page_type,
            "status": page.status,
            "view_count": page.view_count,
            "created_at": page.created_at.isoformat() if page.created_at else None,
            "published_at": page.published_at.isoformat() if page.published_at else None,
        })
    
    return {"total": len(export_data), "data": export_data}

@router.get("/stats")
def get_content_stats(db: Session = Depends(get_db)):
    total_pages = db.query(ContentPage).filter(ContentPage.is_active == True).count()
    published_pages = db.query(ContentPage).filter(ContentPage.status == "published", ContentPage.is_active == True).count()
    draft_pages = db.query(ContentPage).filter(ContentPage.status == "draft", ContentPage.is_active == True).count()
    total_versions = db.query(ContentVersion).count()
    
    page_type_stats = db.query(
        ContentPage.page_type,
        db.func.count(ContentPage.id).label('count')
    ).filter(ContentPage.is_active == True).group_by(ContentPage.page_type).all()
    
    page_type_dict = {pt: count for pt, count in page_type_stats}
    
    return {
        "total_pages": total_pages,
        "published_pages": published_pages,
        "draft_pages": draft_pages,
        "total_versions": total_versions,
        "page_type_stats": page_type_dict
    }