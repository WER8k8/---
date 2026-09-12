import os
import re
import uuid
from typing import List, Optional

from fastapi import (APIRouter, Body, Depends, File, HTTPException, Query,
                     UploadFile)
from pydantic import BaseModel, Field
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.response import success_response
from app.core.security import require_admin
from app.models.content import ContentPage, ContentVersion
from app.models.seo_metadata import SeoMetadata
from app.schemas.content import (ContentPageCreate, ContentPageResponse,
                                 ContentPageUpdate, ContentRollbackRequest,
                                 ContentVersionCreate, ContentVersionResponse,
                                 SeoMetadataCreate, SeoMetadataResponse,
                                 SeoMetadataUpdate)

UPLOAD_DIR = os.path.join(
    os.path.dirname(
        os.path.dirname(
            os.path.dirname(
                os.path.dirname(__file__)))),
    "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

router = APIRouter()


@router.post("/upload")
async def upload_image(
        file: UploadFile = File(...),
        admin=Depends(require_admin)):
    """upload_image。

    参数说明：
    :param file: 参数 file
    :param admin: 参数 admin
    :return: 返回处理结果。
    """
    ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp"}
    ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
    if not file.filename or "." not in file.filename:
        raise HTTPException(status_code=400, detail="无效的文件名")

    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的图片格式: .{ext}，仅支持 {', '.join(ALLOWED_EXTENSIONS)}")

    if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400,
                            detail=f"不允许的文件类型: {file.content_type}")

    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件大小不能超过 5MB")

    if len(content) == 0:
        raise HTTPException(status_code=400, detail="文件内容为空")

    with open(filepath, "wb") as f:
        f.write(content)

    return success_response(data={"url": f"/uploads/{filename}", "filename": filename})


@router.get("/pages")
def list_pages(
    page_type: str = None,
    page: int = 1,
    page_size: int = 20,
    search: str = None,
    is_published: str = None,
    db: Session = Depends(get_db),
):
    """list_pages。

    参数说明：
    :param page_type: 参数 page_type
    :param page: 参数 page
    :param page_size: 参数 page_size
    :param search: 参数 search
    :param is_published: 参数 is_published
    :param db: 参数 db
    :return: 返回处理结果。
    """
    q = db.query(ContentPage).filter(ContentPage.is_active)
    if page_type:
        q = q.filter(ContentPage.page_type == page_type)
    if search:
        q = q.filter(ContentPage.title.contains(search) |
                     ContentPage.summary.contains(search))
    if is_published is not None:
        q = q.filter(
            ContentPage.status == (
                "published" if is_published == "true" else "draft"))

    total = q.count()
    items = q.order_by(
        ContentPage.created_at.desc()).offset(
        (page - 1) * page_size).limit(page_size).all()

    return success_response(data={
        "items": [
            ContentPageResponse.model_validate(
                page.__dict__) for page in items],
        "total": total})


@router.get("/pages/search")
def search_pages(
        q: str = None,
        page: int = 1,
        page_size: int = 20,
        db: Session = Depends(get_db)):
    """搜索页面内容"""
    query = db.query(ContentPage).filter(ContentPage.is_active)
    if q:
        query = query.filter(ContentPage.title.contains(
            q) | ContentPage.summary.contains(q) | ContentPage.content.contains(q))

    total = query.count()
    items = query.order_by(
        ContentPage.created_at.desc()).offset(
        (page - 1) * page_size).limit(page_size).all()

    return success_response(data={
        "items": [
            ContentPageResponse.model_validate(
                page.__dict__) for page in items],
        "total": total})


@router.get("/pages/{page_id}", response_model=ContentPageResponse)
def get_page(page_id: str, db: Session = Depends(get_db)):
    """get_page。

    参数说明：
    :param page_id: 参数 page_id
    :param db: 参数 db
    :return: 返回处理结果。
    """
    page = db.query(ContentPage).filter(ContentPage.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="页面不存在")
    return page


@router.get("/pages/slug/{slug}", response_model=ContentPageResponse)
def get_page_by_slug(slug: str, db: Session = Depends(get_db)):
    """get_page_by_slug。

    参数说明：
    :param slug: 参数 slug
    :param db: 参数 db
    :return: 返回处理结果。
    """
    page = db.query(ContentPage).filter(
        ContentPage.slug == slug,
        ContentPage.is_active).first()
    if not page:
        raise HTTPException(status_code=404, detail="页面不存在")
    page.view_count += 1
    db.commit()
    return page


@router.post("/pages", response_model=ContentPageResponse)
def create_page(
        req: ContentPageCreate,
        db: Session = Depends(get_db),
        admin=Depends(require_admin)):
    """create_page。

    参数说明：
    :param req: 参数 req
    :param db: 参数 db
    :param admin: 参数 admin
    :return: 返回处理结果。
    """
    page = ContentPage(**req.model_dump())
    db.add(page)
    db.commit()
    db.refresh(page)
    return page


@router.put("/pages/{page_id}", response_model=ContentPageResponse)
def update_page(
        page_id: str,
        req: ContentPageUpdate,
        db: Session = Depends(get_db),
        admin=Depends(require_admin)):
    """update_page。

    参数说明：
    :param page_id: 参数 page_id
    :param req: 参数 req
    :param db: 参数 db
    :param admin: 参数 admin
    :return: 返回处理结果。
    """
    page = db.query(ContentPage).filter(ContentPage.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="页面不存在")
    for k, v in req.model_dump(exclude_unset=True).items():
        setattr(page, k, v)
    db.commit()
    db.refresh(page)
    return page


@router.delete("/pages/{page_id}")
def delete_page(
        page_id: str,
        db: Session = Depends(get_db),
        admin=Depends(require_admin)):
    """delete_page。

    参数说明：
    :param page_id: 参数 page_id
    :param db: 参数 db
    :param admin: 参数 admin
    :return: 返回处理结果。
    """
    page = db.query(ContentPage).filter(ContentPage.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="页面不存在")
    db.delete(page)
    db.commit()
    return success_response(message="删除成功")


@router.get("/seo/{resource_type}/{resource_id}",
            response_model=SeoMetadataResponse)
def get_seo_meta(
        resource_type: str,
        resource_id: str,
        db: Session = Depends(get_db)):
    """get_seo_meta。

    参数说明：
    :param resource_type: 参数 resource_type
    :param resource_id: 参数 resource_id
    :param db: 参数 db
    :return: 返回处理结果。
    """
    meta = (
        db.query(SeoMetadata) .filter(
            SeoMetadata.resource_type == resource_type,
            SeoMetadata.resource_id == resource_id) .first())
    if not meta:
        raise HTTPException(status_code=404, detail="SEO元数据不存在")
    return meta


@router.get("/seo/page/{resource_id}", response_model=SeoMetadataResponse)
def get_page_seo_meta(resource_id: str, db: Session = Depends(get_db)):
    """get_page_seo_meta。

    参数说明：
    :param resource_id: 参数 resource_id
    :param db: 参数 db
    :return: 返回处理结果。
    """
    meta = (
        db.query(SeoMetadata) .filter(
            SeoMetadata.resource_type == "page",
            SeoMetadata.resource_id == resource_id) .first())
    if not meta:
        raise HTTPException(status_code=404, detail="SEO元数据不存在")
    return meta


@router.put("/seo/page/{resource_id}", response_model=SeoMetadataResponse)
def update_page_seo_meta(
        resource_id: str,
        req: SeoMetadataUpdate,
        db: Session = Depends(get_db),
        admin=Depends(require_admin)):
    """update_page_seo_meta。

    参数说明：
    :param resource_id: 参数 resource_id
    :param req: 参数 req
    :param db: 参数 db
    :param admin: 参数 admin
    :return: 返回处理结果。
    """
    meta = (
        db.query(SeoMetadata) .filter(
            SeoMetadata.resource_type == "page",
            SeoMetadata.resource_id == resource_id) .first())
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
            h1_tag=req.h1_tag,
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
def create_seo_meta(
        req: SeoMetadataCreate,
        db: Session = Depends(get_db),
        admin=Depends(require_admin)):
    """create_seo_meta。

    参数说明：
    :param req: 参数 req
    :param db: 参数 db
    :param admin: 参数 admin
    :return: 返回处理结果。
    """
    meta = SeoMetadata(**req.model_dump())
    db.add(meta)
    db.commit()
    db.refresh(meta)
    return meta


@router.put("/seo/{resource_type}/{resource_id}",
            response_model=SeoMetadataResponse)
def update_seo_meta(
    resource_type: str,
    resource_id: str,
    req: SeoMetadataUpdate,
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """update_seo_meta。

    参数说明：
    :param resource_type: 参数 resource_type
    :param resource_id: 参数 resource_id
    :param req: 参数 req
    :param db: 参数 db
    :param admin: 参数 admin
    :return: 返回处理结果。
    """
    meta = (
        db.query(SeoMetadata) .filter(
            SeoMetadata.resource_type == resource_type,
            SeoMetadata.resource_id == resource_id) .first())
    if not meta:
        raise HTTPException(status_code=404, detail="SEO元数据不存在")
    for k, v in req.model_dump(exclude_unset=True).items():
        setattr(meta, k, v)
    db.commit()
    db.refresh(meta)
    return meta


def _build_ai_generate_prompt(content_type, product_name, category_name, keywords, density, strength_grade, thermal_conductivity, fire_rating, existing_description):
    """根据内容类型拼装 AI 生成提示词。"""
    # 构建产品信息字符串
    product_info = []
    if product_name:
        product_info.append(f"\\u4ea7\\u54c1\\u540d\\u79f0\\uff1a{product_name}")
    if category_name:
        product_info.append(f"\\u4ea7\\u54c1\\u5206\\u7c7b\\uff1a{category_name}")
    if density:
        product_info.append(f"\\u5e72\\u5bc6\\u5ea6\\uff1a{density} kg/m\\u00b3")
    if strength_grade:
        product_info.append(f"\\u5f3a\\u5ea6\\u7b49\\u7ea7\\uff1a{strength_grade}")
    if thermal_conductivity:
        product_info.append(f"\\u5bfc\\u70ed\\u7cfb\\u6570\\uff1a{thermal_conductivity} W/m\\u00b7K")
    if fire_rating:
        product_info.append(f"\\u9632\\u706b\\u7b49\\u7ea7\\uff1a{fire_rating}")

    product_info_str = "\\n".join(product_info)
    if content_type == "product":
        prompt = f"""\\u8bf7\\u4e3a\\u4ee5\\u4e0b\\u8f7b\\u96c6\\u6599\\u6df7\\u51dd\\u571f\\u4ea7\\u54c1\\u751f\\u6210\\u4e13\\u4e1a\\u3001\\u8be6\\u7ec6\\u7684\\u4ea7\\u54c1\\u63cf\\u8ff0\\uff1a

\\u4ea7\\u54c1\\u4fe1\\u606f\\uff1a
{product_info_str}

\\u5173\\u952e\\u8bcd\\uff1a{', '.join(keywords)}

\\u8981\\u6c42\\uff1a
1. \\u5185\\u5bb9\\u5fc5\\u987b\\u4e0e\\u4ea7\\u54c1\\u540d\\u79f0\\u4e25\\u683c\\u76f8\\u5173\\uff0c\\u4e0d\\u504f\\u79bb\\u4e3b\\u9898
2. \\u7a81\\u51fa\\u4ea7\\u54c1\\u7279\\u70b9\\u548c\\u6838\\u5fc3\\u4f18\\u52bf
3. \\u5305\\u542b\\u6280\\u672f\\u53c2\\u6570\\uff08\\u5bc6\\u5ea6\\u3001\\u5f3a\\u5ea6\\u7b49\\u7ea7\\u3001\\u5bfc\\u70ed\\u7cfb\\u6570\\u7b49\\uff09
4. \\u8bed\\u8a00\\u4e13\\u4e1a\\u4e14\\u6613\\u4e8e\\u7406\\u89e3
5. \\u7b26\\u5408SEO\\u4f18\\u5316\\u8981\\u6c42\\uff0c\\u5305\\u542b\\u5173\\u952e\\u8bcd
6. \\u5f15\\u7528\\u884c\\u4e1a\\u6807\\u51c6\\uff08\\u5982JGJ/T 12-2019\\uff09
7. \\u7ed3\\u6784\\u6e05\\u6670\\uff0c\\u6bb5\\u843d\\u5206\\u660e
"""
    elif content_type == "seo_title":
        prompt = f"""\\u8bf7\\u6839\\u636e\\u4ee5\\u4e0b\\u4ea7\\u54c1\\u4fe1\\u606f\\u751f\\u6210\\u4e13\\u4e1a\\u7684SEO\\u6807\\u9898\\uff08\\u5efa\\u8bae\\u957f\\u5ea630-60\\u5b57\\u7b26\\uff09\\uff1a

\\u4ea7\\u54c1\\u540d\\u79f0\\uff1a{product_name}
\\u4ea7\\u54c1\\u5206\\u7c7b\\uff1a{category_name}
\\u5f3a\\u5ea6\\u7b49\\u7ea7\\uff1a{strength_grade}
\\u9632\\u706b\\u7b49\\u7ea7\\uff1a{fire_rating}

\\u8981\\u6c42\\uff1a
1. \\u5305\\u542b\\u6838\\u5fc3\\u5173\\u952e\\u8bcd\\uff1a{product_name}\\u3001{category_name}
2. \\u7a81\\u51fa\\u4ea7\\u54c1\\u6838\\u5fc3\\u5356\\u70b9
3. \\u4e2d\\u82f1\\u6587\\u5173\\u952e\\u8bcd\\u7ed3\\u5408\\uff08\\u5982\\u4fdd\\u6e29\\u6750\\u6599/insulation material\\uff09
4. \\u7b26\\u5408\\u641c\\u7d22\\u5f15\\u64ce\\u4f18\\u5316\\u6807\\u51c6
5. \\u5438\\u5f15\\u7528\\u6237\\u70b9\\u51fb\\uff0c\\u63d0\\u5347CTR
"""
    elif content_type == "seo_description":
        prompt = f"""\\u8bf7\\u6839\\u636e\\u4ee5\\u4e0b\\u4ea7\\u54c1\\u4fe1\\u606f\\u751f\\u6210\\u4e13\\u4e1a\\u7684SEO\\u63cf\\u8ff0\\uff08\\u5efa\\u8bae\\u957f\\u5ea680-160\\u5b57\\u7b26\\uff09\\uff1a

\\u4ea7\\u54c1\\u540d\\u79f0\\uff1a{product_name}
\\u4ea7\\u54c1\\u5206\\u7c7b\\uff1a{category_name}
\\u5e72\\u5bc6\\u5ea6\\uff1a{density} kg/m\\u00b3
\\u5f3a\\u5ea6\\u7b49\\u7ea7\\uff1a{strength_grade}
\\u9632\\u706b\\u7b49\\u7ea7\\uff1a{fire_rating}
\\u5bfc\\u70ed\\u7cfb\\u6570\\uff1a{thermal_conductivity} W/m\\u00b7K
\\u4ea7\\u54c1\\u63cf\\u8ff0\\uff1a{existing_description[:300] if existing_description else ''}

\\u8981\\u6c42\\uff1a
1. \\u5305\\u542b\\u6838\\u5fc3\\u5173\\u952e\\u8bcd\\uff1a{product_name}\\u3001{category_name}
2. \\u7a81\\u51fa\\u4ea7\\u54c1\\u5356\\u70b9\\uff08\\u5982\\u8282\\u80fd\\u3001\\u9632\\u706b\\u3001\\u9ad8\\u5f3a\\u5ea6\\u7b49\\uff09
3. \\u5438\\u5f15\\u7528\\u6237\\u70b9\\u51fb\\uff0c\\u63d0\\u5347CTR
4. \\u7b26\\u5408\\u641c\\u7d22\\u5f15\\u64ce\\u4f18\\u5316\\u8981\\u6c42
5. \\u8bed\\u53e5\\u901a\\u987a\\u81ea\\u7136\\uff0c\\u4e0d\\u5806\\u7838\\u5173\\u952e\\u8bcd
"""
    else:
        prompt = f"""\\u8bf7\\u751f\\u6210{content_type}\\u76f8\\u5173\\u5185\\u5bb9\\uff0c\\u5173\\u952e\\u8bcd\\uff1a{', '.join(keywords)}"""
    return prompt


@router.post("/ai/generate")
async def ai_generate_content(
        request: dict = Body(...),
        db: Session = Depends(get_db),
        admin=Depends(require_admin)):
    """AI\\u751f\\u6210\\u5185\\u5bb9\\u63a5\\u53e3"""
    from app.services.ai_engine import get_ai_engine
    ai_engine = get_ai_engine()
    content_type = request.get("content_type", "product")
    keywords = request.get("keywords", [])
    product_name = request.get("product_name", "")
    category_name = request.get("category_name", "")
    density = request.get("density", 0)
    strength_grade = request.get("strength_grade", "")
    thermal_conductivity = request.get("thermal_conductivity", 0)
    fire_rating = request.get("fire_rating", "")
    existing_description = request.get("existing_description", "")
    prompt = _build_ai_generate_prompt(content_type, product_name, category_name, keywords, density, strength_grade, thermal_conductivity, fire_rating, existing_description)
    result = await ai_engine._generate_response(
        ai_engine._get_llm("chinese"), prompt, content_type, None, task_type="product_gen"
    )
    return success_response(data={
        "content": result.get(
            "optimized_content", result.get(
                "content", "\\u751f\\u6210\\u5931\\u8d25")), "mock": result.get(
            "mock", False), "token_usage": result.get(
            "token_usage", 0), "cost": result.get(
                "cost", 0), })


@router.post("/ai/polish")
async def ai_polish_content(
        request: dict = Body(...),
        db: Session = Depends(get_db),
        admin=Depends(require_admin)):
    """ai_polish_content。

    参数说明：
    :param request: 参数 request
    :param db: 参数 db
    :param admin: 参数 admin
    :return: 返回处理结果。
    """
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
        ai_engine._get_llm("chinese"), prompt, polish_type, None, task_type="polish"
    )
    return success_response(data={
        "content": result.get(
            "optimized_content", result.get(
                "content", "润色失败")), "mock": result.get(
            "mock", False), "token_usage": result.get(
                    "token_usage", 0), "cost": result.get(
                        "cost", 0), })


# ============= 版本控制API =============


@router.post("/pages/{page_id}/versions",
             response_model=ContentVersionResponse)
def create_page_version(
        page_id: str,
        req: ContentVersionCreate = None,
        db: Session = Depends(get_db),
        admin=Depends(require_admin)):
    """create_page_version。

    参数说明：
    :param page_id: 参数 page_id
    :param req: 参数 req
    :param db: 参数 db
    :param admin: 参数 admin
    :return: 返回处理结果。
    """
    page = db.query(ContentPage).filter(ContentPage.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="页面不存在")

    max_version = db.query(ContentVersion).filter(
        ContentVersion.page_id == page_id).count()
    new_version_number = max_version + 1
    version = ContentVersion(
        page_id=page_id,
        version_number=new_version_number,
        title=page.title,
        content=page.content,
        summary=page.summary,
        change_note=req.change_note if req else f"版本 {new_version_number}",
        author_id=page.author_id,
    )
    db.add(version)
    db.commit()
    db.refresh(version)
    return version


@router.get("/pages/{page_id}/versions",
            response_model=list[ContentVersionResponse])
def list_page_versions(
        page_id: str,
        db: Session = Depends(get_db),
        admin=Depends(require_admin)):
    """list_page_versions。

    参数说明：
    :param page_id: 参数 page_id
    :param db: 参数 db
    :param admin: 参数 admin
    :return: 返回处理结果。
    """
    page = db.query(ContentPage).filter(ContentPage.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="页面不存在")

    return (
        db.query(ContentVersion)
        .filter(ContentVersion.page_id == page_id)
        .order_by(ContentVersion.version_number.desc())
        .all()
    )


@router.get("/pages/{page_id}/versions/{version_id}",
            response_model=ContentVersionResponse)
def get_page_version(
        page_id: str,
        version_id: str,
        db: Session = Depends(get_db),
        admin=Depends(require_admin)):
    """get_page_version。

    参数说明：
    :param page_id: 参数 page_id
    :param version_id: 参数 version_id
    :param db: 参数 db
    :param admin: 参数 admin
    :return: 返回处理结果。
    """
    version = (
        db.query(ContentVersion).filter(
            ContentVersion.id == version_id,
            ContentVersion.page_id == page_id).first())
    if not version:
        raise HTTPException(status_code=404, detail="版本不存在")
    return version


@router.post("/pages/{page_id}/rollback")
def rollback_to_version(
        page_id: str,
        req: ContentRollbackRequest,
        db: Session = Depends(get_db),
        admin=Depends(require_admin)):
    """rollback_to_version。

    参数说明：
    :param page_id: 参数 page_id
    :param req: 参数 req
    :param db: 参数 db
    :param admin: 参数 admin
    :return: 返回处理结果。
    """
    page = db.query(ContentPage).filter(ContentPage.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="页面不存在")

    version = (
        db.query(ContentVersion).filter(
            ContentVersion.id == req.version_id,
            ContentVersion.page_id == page_id).first())
    if not version:
        raise HTTPException(status_code=404, detail="版本不存在")

    page.title = version.title
    page.content = version.content
    page.summary = version.summary
    db.commit()
    db.refresh(page)
    return success_response(data={
        "message": f"已回滚到版本 {version.version_number}",
        "page": ContentPageResponse.model_validate(page.__dict__),
    })


# ============= 批量操作API =============


class BatchDeleteRequest(BaseModel):
    ids: List[str] = Field(..., min_length=1, max_length=100)


class BatchUpdateStatusRequest(BaseModel):
    ids: List[str] = Field(..., min_length=1, max_length=100)
    status: str = Field(..., pattern="^(published|draft)$")


class BatchPublishRequest(BaseModel):
    ids: List[str] = Field(..., min_length=1, max_length=100)


def sanitize_html(content: str) -> str:
    """清理HTML内容，防止XSS攻击"""
    dangerous_patterns = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>.*?</iframe>",
        r"<object[^>]*>.*?</object>",
        r"<embed[^>]*>.*?</embed>",
        r"<form[^>]*>.*?</form>",
    ]
    for pattern in dangerous_patterns:
        content = re.sub(pattern, "", content, flags=re.IGNORECASE | re.DOTALL)
    return content


@router.post("/pages/batch-delete")
def batch_delete_pages(
        req: BatchDeleteRequest,
        db: Session = Depends(get_db),
        admin=Depends(require_admin)):
    """batch_delete_pages。

    参数说明：
    :param req: 参数 req
    :param db: 参数 db
    :param admin: 参数 admin
    :return: 返回处理结果。
    """
    pages = db.query(ContentPage).filter(ContentPage.id.in_(req.ids)).all()
    if not pages:
        raise HTTPException(status_code=404, detail="未找到指定页面")

    for page in pages:
        db.delete(page)

    db.commit()
    return success_response(data={"message": f"成功删除 {len(pages)} 个页面", "deleted_count": len(pages)})


@router.post("/pages/batch-update-status")
def batch_update_status(
        req: BatchUpdateStatusRequest,
        db: Session = Depends(get_db),
        admin=Depends(require_admin)):
    """batch_update_status。

    参数说明：
    :param req: 参数 req
    :param db: 参数 db
    :param admin: 参数 admin
    :return: 返回处理结果。
    """
    pages = db.query(ContentPage).filter(ContentPage.id.in_(req.ids)).all()
    if not pages:
        raise HTTPException(status_code=404, detail="未找到指定页面")

    for page in pages:
        page.status = req.status

    db.commit()
    return success_response(data={"message": f"成功更新 {len(pages)} 个页面状态", "updated_count": len(pages)})


@router.post("/pages/batch-publish")
def batch_publish_pages(
        req: BatchPublishRequest,
        db: Session = Depends(get_db),
        admin=Depends(require_admin)):
    """batch_publish_pages。

    参数说明：
    :param req: 参数 req
    :param db: 参数 db
    :param admin: 参数 admin
    :return: 返回处理结果。
    """
    from datetime import datetime, timezone
    pages = db.query(ContentPage).filter(ContentPage.id.in_(req.ids)).all()
    if not pages:
        raise HTTPException(status_code=404, detail="未找到指定页面")

    now = datetime.now(timezone.utc)
    for page in pages:
        page.status = "published"
        page.published_at = now

    db.commit()
    return success_response(data={"message": f"成功发布 {len(pages)} 个页面", "published_count": len(pages)})


@router.get("/pages/export")
def export_pages(
    page_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """export_pages。

    参数说明：
    :param page_type: 参数 page_type
    :param status: 参数 status
    :param db: 参数 db
    :param admin: 参数 admin
    :return: 返回处理结果。
    """
    q = db.query(ContentPage).filter(ContentPage.is_active)
    if page_type:
        q = q.filter(ContentPage.page_type == page_type)
    if status:
        q = q.filter(ContentPage.status == status)

    pages = q.order_by(ContentPage.created_at.desc()).all()
    export_data = []
    for page in pages:
        export_data.append(
            {
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

    return success_response(data={"total": len(export_data), "data": export_data})


@router.get("/stats")
def get_content_stats(db: Session = Depends(get_db)):
    """get_content_stats。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    from sqlalchemy import func
    total_pages = db.query(ContentPage).filter(ContentPage.is_active).count()
    published_pages = (
        db.query(ContentPage).filter(
            ContentPage.status == "published",
            ContentPage.is_active).count())
    draft_pages = db.query(ContentPage).filter(
        ContentPage.status == "draft",
        ContentPage.is_active).count()
    total_versions = db.query(ContentVersion).count()
    page_type_stats = (
        db.query(
            ContentPage.page_type,
            func.count(
                ContentPage.id).label("count")) .filter(
            ContentPage.is_active) .group_by(
                    ContentPage.page_type) .all())

    page_type_dict = {pt: count for pt, count in page_type_stats}
    return success_response(data={
        "total_pages": total_pages,
        "published_pages": published_pages,
        "draft_pages": draft_pages,
        "total_versions": total_versions,
        "page_type_stats": page_type_dict,
    })
