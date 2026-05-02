from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.database import get_db
from app.core.security import require_admin
from app.models.product import Product
from app.models.content import ContentPage, SeoMetadata
from app.models.case_study import CaseStudy

router = APIRouter()


def _fetch_seo_items(db: Session, search: str = ""):
    items = []
    products = db.query(Product).filter(Product.is_active == True).all()
    for p in products:
        if search and search.lower() not in (p.name or "").lower() and search.lower() not in (p.slug or "").lower():
            continue
        meta = db.query(SeoMetadata).filter(
            SeoMetadata.resource_type == "product",
            SeoMetadata.resource_id == str(p.id),
        ).first()
        items.append({
            "resource_type": "product",
            "resource_id": str(p.id),
            "title": p.name,
            "current_meta_title": meta.meta_title if meta else "",
            "current_meta_description": meta.meta_description if meta else "",
            "current_meta_keywords": meta.meta_keywords if meta else "",
        })

    cases = db.query(CaseStudy).filter(CaseStudy.is_active == True).all()
    for c in cases:
        if search and search.lower() not in (c.project_name or "").lower() and search.lower() not in (c.slug or "").lower():
            continue
        meta = db.query(SeoMetadata).filter(
            SeoMetadata.resource_type == "case_study",
            SeoMetadata.resource_id == str(c.id),
        ).first()
        items.append({
            "resource_type": "case",
            "resource_id": str(c.id),
            "title": c.project_name,
            "current_meta_title": meta.meta_title if meta else "",
            "current_meta_description": meta.meta_description if meta else "",
            "current_meta_keywords": meta.meta_keywords if meta else "",
        })

    pages = db.query(ContentPage).filter(ContentPage.is_active == True).all()
    for pg in pages:
        if search and search.lower() not in (pg.title or "").lower() and search.lower() not in (pg.slug or "").lower():
            continue
        meta = db.query(SeoMetadata).filter(
            SeoMetadata.resource_type == "page",
            SeoMetadata.resource_id == str(pg.id),
        ).first()
        items.append({
            "resource_type": "page",
            "resource_id": str(pg.id),
            "title": pg.title,
            "current_meta_title": meta.meta_title if meta else "",
            "current_meta_description": meta.meta_description if meta else "",
            "current_meta_keywords": meta.meta_keywords if meta else "",
        })
    return items


@router.get("/seo-batch-list")
def get_seo_batch_list(search: str = "", db: Session = Depends(get_db), admin = Depends(require_admin)):
    return _fetch_seo_items(db, search)


@router.get("/pages")
def get_seo_pages(
    search: str = "",
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
):
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
    admin = Depends(require_admin)
):
    RESOURCE_TYPE_MAP = {
        "product": "product",
        "case": "case_study",
        "page": "page",
    }
    rtype = RESOURCE_TYPE_MAP.get(resource_type, resource_type)
    
    meta = db.query(SeoMetadata).filter(
        SeoMetadata.resource_type == rtype,
        SeoMetadata.resource_id == resource_id,
    ).first()
    
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


class BatchApplyRuleRequest(BaseModel):
    resource_type: str = ""
    rule_type: str
    value: str


@router.post("/seo-batch-apply-rule")
def apply_batch_rule(req: BatchApplyRuleRequest, db: Session = Depends(get_db), admin = Depends(require_admin)):
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
        rtype = RESOURCE_TYPE_MAP.get(item["resource_type"], item["resource_type"])
        meta = db.query(SeoMetadata).filter(
            SeoMetadata.resource_type == rtype,
            SeoMetadata.resource_id == item["resource_id"],
        ).first()
        if not meta:
            meta = SeoMetadata(resource_type=rtype, resource_id=item["resource_id"])
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
