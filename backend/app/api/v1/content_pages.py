"""
Content Pages API Router - 内容页面API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from datetime import datetime

from app.core.database import get_db
from app.core.response import success_response
from app.models.content import ContentPage

router = APIRouter(prefix="/api/v1/content-pages", tags=["content-pages"])


@router.post("/", response_model=dict)
def create_content_page(
    title: str,
    slug: str,
    content: str,
    content_type: str = "blog",  # blog/guide/case_study/news
    author_id: Optional[str] = None,
    status: str = "draft",  # draft/published/archived
    published_at: Optional[str] = None,  # ISO datetime string
    featured_image: Optional[str] = None,
    reading_time: Optional[int] = None,
    language: str = "en",
    hreflang_group: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """创建内容页面"""
    try:
        published = None
        if published_at:
            published = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
        
        page = ContentPage(
            title=title,
            slug=slug,
            content=content,
            content_type=content_type,
            author_id=uuid.UUID(author_id) if author_id else None,
            status=status,
            published_at=published,
            featured_image=featured_image,
            reading_time=reading_time,
            language=language,
            hreflang_group=uuid.UUID(hreflang_group) if hreflang_group else None,
        )
        db.add(page)
        db.commit()
        db.refresh(page)
        return success_response(data={"id": str(page.id), "title": page.title, "status": page.status})
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{page_id}", response_model=dict)
def get_content_page(page_id: str, db: Session = Depends(get_db)):
    """获取内容页面详情"""
    page = db.query(ContentPage).filter(ContentPage.id == uuid.UUID(page_id)).first()
    if not page:
        raise HTTPException(status_code=404, detail="Content page not found")
    
    return success_response(data={
        "id": str(page.id),
        "title": page.title,
        "slug": page.slug,
        "content": page.content,
        "content_type": page.content_type,
        "author_id": str(page.author_id) if page.author_id else None,
        "status": page.status,
        "published_at": page.published_at.isoformat() if page.published_at else None,
        "featured_image": page.featured_image,
        "reading_time": page.reading_time,
        "view_count": page.view_count,
        "language": page.language,
        "created_at": page.created_at.isoformat() if page.created_at else None,
    })


@router.get("/", response_model=List[dict])
def list_content_pages(
    content_type: Optional[str] = None,
    status: Optional[str] = None,
    language: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """列出内容页面（支持过滤）"""
    query = db.query(ContentPage)
    if content_type:
        query = query.filter(ContentPage.content_type == content_type)
    if status:
        query = query.filter(ContentPage.status == status)
    if language:
        query = query.filter(ContentPage.language == language)
    
    pages = query.order_by(ContentPage.published_at.desc().nulls_last(), ContentPage.created_at.desc()).offset(skip).limit(limit).all()
    return success_response(data=[
        {
            "id": str(p.id),
            "title": p.title,
            "slug": p.slug,
            "content_type": p.content_type,
            "status": p.status,
            "language": p.language,
            "view_count": p.view_count,
            "published_at": p.published_at.isoformat() if p.published_at else None,
        }
        for p in pages
    ])


@router.put("/{page_id}", response_model=dict)
def update_content_page(
    page_id: str,
    title: Optional[str] = None,
    slug: Optional[str] = None,
    content: Optional[str] = None,
    content_type: Optional[str] = None,
    status: Optional[str] = None,
    published_at: Optional[str] = None,
    featured_image: Optional[str] = None,
    reading_time: Optional[int] = None,
    language: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """更新内容页面"""
    page = db.query(ContentPage).filter(ContentPage.id == uuid.UUID(page_id)).first()
    if not page:
        raise HTTPException(status_code=404, detail="Content page not found")
    
    if title is not None:
        page.title = title
    if slug is not None:
        page.slug = slug
    if content is not None:
        page.content = content
    if content_type is not None:
        page.content_type = content_type
    if status is not None:
        page.status = status
    if published_at is not None:
        page.published_at = datetime.fromisoformat(published_at.replace("Z", "+00:00")) if published_at else None
    if featured_image is not None:
        page.featured_image = featured_image
    if reading_time is not None:
        page.reading_time = reading_time
    if language is not None:
        page.language = language
    
    db.commit()
    db.refresh(page)
    return success_response(data={"id": str(page.id), "title": page.title, "status": page.status})


@router.delete("/{page_id}")
def delete_content_page(page_id: str, db: Session = Depends(get_db)):
    """删除内容页面"""
    page = db.query(ContentPage).filter(ContentPage.id == uuid.UUID(page_id)).first()
    if not page:
        raise HTTPException(status_code=404, detail="Content page not found")
    
    db.delete(page)
    db.commit()
    return success_response(message="Content page deleted successfully")


@router.post("/{page_id}/view")
def increment_view_count(page_id: str, db: Session = Depends(get_db)):
    """增加页面浏览量"""
    page = db.query(ContentPage).filter(ContentPage.id == uuid.UUID(page_id)).first()
    if not page:
        raise HTTPException(status_code=404, detail="Content page not found")
    
    page.view_count += 1
    db.commit()
    return success_response(data={"view_count": page.view_count})
