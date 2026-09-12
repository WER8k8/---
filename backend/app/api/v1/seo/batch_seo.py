from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_admin
from app.models.case_study import CaseStudy
from app.models.content import ContentPage
from app.models.seo_metadata import SeoMetadata
from app.models.product import Product

router = APIRouter()


def _fetch_seo_items(db: Session, search: str = ""):
    """_fetch_seo_items。

    参数说明：
    :param db: 参数 db
    :param search: 参数 search
    :return: 返回处理结果。
    """
    items = []
    products = db.query(Product).filter(Product.is_active).all()
    for p in products:
        if search and search.lower() not in (
                p.name or "").lower() and search.lower() not in (
                p.slug or "").lower():
            continue
        meta = (
            db.query(SeoMetadata)
            .filter(
                SeoMetadata.resource_type == "product",
                SeoMetadata.resource_id == str(p.id),
            )
            .first()
        )
        items.append({"resource_type": "product",
                      "resource_id": str(p.id),
                      "title": p.name,
                      "current_meta_title": meta.meta_title if meta else "",
                      "current_meta_description": meta.meta_description if meta else "",
                      "current_meta_keywords": meta.meta_keywords if meta else "",
                      })

    cases = db.query(CaseStudy).filter(CaseStudy.is_active).all()
    for c in cases:
        if (
            search
            and search.lower() not in (c.project_name or "").lower()
            and search.lower() not in (c.slug or "").lower()
        ):
            continue
        meta = (
            db.query(SeoMetadata)
            .filter(
                SeoMetadata.resource_type == "case_study",
                SeoMetadata.resource_id == str(c.id),
            )
            .first()
        )
        items.append({"resource_type": "case",
                      "resource_id": str(c.id),
                      "title": c.project_name,
                      "current_meta_title": meta.meta_title if meta else "",
                      "current_meta_description": meta.meta_description if meta else "",
                      "current_meta_keywords": meta.meta_keywords if meta else "",
                      })

    pages = db.query(ContentPage).filter(ContentPage.is_active).all()
    for pg in pages:
        if search and search.lower() not in (
                pg.title or "").lower() and search.lower() not in (
                pg.slug or "").lower():
            continue
        meta = (
            db.query(SeoMetadata)
            .filter(
                SeoMetadata.resource_type == "page",
                SeoMetadata.resource_id == str(pg.id),
            )
            .first()
        )
        items.append({"resource_type": "page",
                      "resource_id": str(pg.id),
                      "title": pg.title,
                      "current_meta_title": meta.meta_title if meta else "",
                      "current_meta_description": meta.meta_description if meta else "",
                      "current_meta_keywords": meta.meta_keywords if meta else "",
                      })
    return items


@router.get("/seo-batch-list")
def get_seo_batch_list(
        search: str = "",
        db: Session = Depends(get_db),
        admin=Depends(require_admin)):
    """get_seo_batch_list。

    参数说明：
    :param search: 参数 search
    :param db: 参数 db
    :param admin: 参数 admin
    :return: 返回处理结果。
    """
    return _fetch_seo_items(db, search)


@router.get("/pages")
def get_seo_pages(
    search: str = "",
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
):
    """get_seo_pages。

    参数说明：
    :param search: 参数 search
    :param page: 参数 page
    :param page_size: 参数 page_size
    :param db: 参数 db
    :return: 返回处理结果。
    """
    items = _fetch_seo_items(db, search)
    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "items": items[start:end],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.put("/pages/{resource_id}")
def update_seo_page(
    resource_id: str,
    resource_type: str = "page",
    meta_title: str = "",
    meta_description: str = "",
    meta_keywords: str = "",
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """update_seo_page。

    参数说明：
    :param resource_id: 参数 resource_id
    :param resource_type: 参数 resource_type
    :param meta_title: 参数 meta_title
    :param meta_description: 参数 meta_description
    :param meta_keywords: 参数 meta_keywords
    :param db: 参数 db
    :param admin: 参数 admin
    :return: 返回处理结果。
    """
    RESOURCE_TYPE_MAP = {
        "product": "product",
        "case": "case_study",
        "page": "page",
    }
    rtype = RESOURCE_TYPE_MAP.get(resource_type, resource_type)
    meta = (
        db.query(SeoMetadata)
        .filter(
            SeoMetadata.resource_type == rtype,
            SeoMetadata.resource_id == resource_id,
        )
        .first()
    )
    if not meta:
        meta = SeoMetadata(resource_type=rtype, resource_id=resource_id)
        db.add(meta)

    if meta_title:
        meta.meta_title = meta_title
    if meta_description:
        meta.meta_description = meta_description
    if meta_keywords:
        meta.meta_keywords = meta_keywords

    db.commit()
    db.refresh(meta)
    return {
        "message": "更新成功",
        "meta_title": meta.meta_title,
        "meta_description": meta.meta_description,
        "meta_keywords": meta.meta_keywords,
    }


@router.post("/pages/{resource_id}/optimize")
def optimize_seo_page(
    resource_id: str,
    resource_type: str = "page",
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """AI优化单条SEO页面（前端 seoAPI.optimizePage 对应接口）"""
    RESOURCE_TYPE_MAP = {
        "product": "product",
        "case": "case_study",
        "page": "page",
    }
    rtype = RESOURCE_TYPE_MAP.get(resource_type, resource_type)
    meta = (
        db.query(SeoMetadata)
        .filter(
            SeoMetadata.resource_type == rtype,
            SeoMetadata.resource_id == resource_id,
        )
        .first()
    )
    if not meta:
        meta = SeoMetadata(resource_type=rtype, resource_id=resource_id)
        db.add(meta)
        db.commit()
        db.refresh(meta)

    # 尝试调用AI引擎优化
    try:
        from app.services.ai_engine import get_ai_engine
        ai_engine = get_ai_engine()
        title = meta.meta_title or ""
        desc = meta.meta_description or ""
        prompt = f"优化以下SEO元数据，生成更专业的SEO标题和描述：\n原标题：{title}\n原描述：{desc}"
        result = ai_engine._generate_response(
            ai_engine._get_llm("chinese"),
            prompt,
            "seo_optimization",
            None,
            task_type="seo_opt")
        optimized = result.get("optimized_content", result.get("content", ""))
        if optimized:
            meta.ai_suggestions = optimized
            db.commit()
            return {"message": "AI优化完成", "suggestion": optimized}
    except Exception as e:
        pass

    return {
        "message": "优化完成（默认规则）",
        "meta_title": meta.meta_title,
        "meta_description": meta.meta_description}


class BatchApplyRuleRequest(BaseModel):
    resource_type: str = ""
    rule_type: str
    value: str


@router.post("/seo-batch-apply-rule")
def apply_batch_rule(
        req: BatchApplyRuleRequest,
        db: Session = Depends(get_db),
        admin=Depends(require_admin)):
    """apply_batch_rule。

    参数说明：
    :param req: 参数 req
    :param db: 参数 db
    :param admin: 参数 admin
    :return: 返回处理结果。
    """
    items = _fetch_seo_items(db)
    updated = 0
    RESOURCE_TYPE_MAP = {
        "product": "product",
        "case": "case_study",
        "page": "page",
    }
    for item in items:
        if req.resource_type and item["resource_type"] != req.resource_type:
            continue
        rtype = RESOURCE_TYPE_MAP.get(
            item["resource_type"], item["resource_type"])
        meta = (
            db.query(SeoMetadata)
            .filter(
                SeoMetadata.resource_type == rtype,
                SeoMetadata.resource_id == item["resource_id"],
            )
            .first()
        )
        if not meta:
            meta = SeoMetadata(
                resource_type=rtype,
                resource_id=item["resource_id"])
            db.add(meta)

        if req.rule_type == "prefix_title":
            prefix = req.value.rstrip()
            meta.meta_title = f"{prefix}{meta.meta_title or item['title']}"
        elif req.rule_type == "suffix_title":
            suffix = req.value.rstrip()
            meta.meta_title = f"{meta.meta_title or item['title']}{suffix}"
        elif req.rule_type == "set_description":
            meta.meta_description = req.value
        elif req.rule_type == "set_keywords":
            meta.meta_keywords = req.value

        updated += 1

    db.commit()
    return {"updated": updated, "message": f"成功更新 {updated} 条记录的SEO信息"}
