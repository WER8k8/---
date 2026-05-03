from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime
import uuid
import re

from app.core.database import get_db
from app.core.security import require_admin
from app.models.news import NewsArticle, NewsCategory

router = APIRouter()


def sanitize_input(value: str) -> str:
    if not value:
        return value
    dangerous_patterns = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'on\w+\s*=',
        r'<iframe[^>]*>.*?</iframe>',
        r'<object[^>]*>.*?</object>',
        r'<embed[^>]*>.*?</embed>',
    ]
    for pattern in dangerous_patterns:
        value = re.sub(pattern, '', value, flags=re.IGNORECASE | re.DOTALL)
    return value.strip()


def generate_slug(title: str) -> str:
    from pypinyin import pinyin, Style
    py_list = pinyin(title, style=Style.NORMAL)
    slug = '-'.join([item[0] for item in py_list])
    slug = re.sub(r'[^a-z0-9\-]', '', slug.lower())
    slug = re.sub(r'-+', '-', slug).strip('-')
    return slug or str(uuid.uuid4())[:8]


@router.get("/")
def list_articles(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    category: Optional[str] = None,
    is_published: Optional[bool] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(NewsArticle).filter(NewsArticle.is_active == True)
    
    if is_published is not None:
        query = query.filter(NewsArticle.is_published == is_published)
    else:
        query = query.filter(NewsArticle.is_published == True)
    
    if category:
        query = query.filter(NewsArticle.category == category)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (NewsArticle.title.ilike(search_term)) |
            (NewsArticle.summary.ilike(search_term)) |
            (NewsArticle.content.ilike(search_term))
        )
    
    total = query.count()
    items = query.order_by(
        NewsArticle.published_at.desc(),
        NewsArticle.sort_order.asc()
    ).offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "items": [
            {
                "id": item.id,
                "title": item.title,
                "slug": item.slug,
                "subtitle": item.subtitle,
                "summary": item.summary,
                "cover_image": item.cover_image,
                "category": item.category,
                "author": item.author,
                "view_count": item.view_count,
                "published_at": item.published_at.isoformat() if item.published_at else None,
                "created_at": item.created_at.isoformat() if item.created_at else None,
            }
            for item in items
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


@router.get("/categories")
def list_categories(db: Session = Depends(get_db)):
    categories = db.query(NewsCategory).filter(
        NewsCategory.is_active == True
    ).order_by(NewsCategory.sort_order.asc()).all()
    
    return [
        {
            "id": cat.id,
            "name": cat.name,
            "slug": cat.slug,
            "description": cat.description,
        }
        for cat in categories
    ]


@router.get("/{article_id}")
def get_article(
    article_id: str,
    db: Session = Depends(get_db),
):
    article = db.query(NewsArticle).filter(
        NewsArticle.id == article_id,
        NewsArticle.is_active == True,
    ).first()
    
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")
    
    article.view_count = (article.view_count or 0) + 1
    db.commit()
    
    return {
        "id": article.id,
        "title": article.title,
        "slug": article.slug,
        "subtitle": article.subtitle,
        "summary": article.summary,
        "content": article.content,
        "cover_image": article.cover_image,
        "category": article.category,
        "tags": article.tags,
        "author": article.author,
        "source": article.source,
        "view_count": article.view_count,
        "published_at": article.published_at.isoformat() if article.published_at else None,
        "created_at": article.created_at.isoformat() if article.created_at else None,
        "updated_at": article.updated_at.isoformat() if article.updated_at else None,
    }


@router.get("/slug/{slug}")
def get_article_by_slug(
    slug: str,
    db: Session = Depends(get_db),
):
    article = db.query(NewsArticle).filter(
        NewsArticle.slug == slug,
        NewsArticle.is_active == True,
        NewsArticle.is_published == True,
    ).first()
    
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")
    
    article.view_count = (article.view_count or 0) + 1
    db.commit()
    
    return {
        "id": article.id,
        "title": article.title,
        "slug": article.slug,
        "subtitle": article.subtitle,
        "summary": article.summary,
        "content": article.content,
        "cover_image": article.cover_image,
        "category": article.category,
        "tags": article.tags,
        "author": article.author,
        "source": article.source,
        "view_count": article.view_count,
        "published_at": article.published_at.isoformat() if article.published_at else None,
        "created_at": article.created_at.isoformat() if article.created_at else None,
        "updated_at": article.updated_at.isoformat() if article.updated_at else None,
    }


@router.get("/related/{article_id}")
def get_related_articles(
    article_id: str,
    limit: int = Query(3, ge=1, le=10),
    db: Session = Depends(get_db),
):
    article = db.query(NewsArticle).filter(NewsArticle.id == article_id).first()
    if not article:
        return {"items": []}
    
    related = db.query(NewsArticle).filter(
        NewsArticle.is_active == True,
        NewsArticle.is_published == True,
        NewsArticle.id != article_id,
        NewsArticle.category == article.category,
    ).order_by(
        NewsArticle.published_at.desc()
    ).limit(limit).all()
    
    return {
        "items": [
            {
                "id": item.id,
                "title": item.title,
                "slug": item.slug,
                "summary": item.summary,
                "cover_image": item.cover_image,
                "category": item.category,
                "published_at": item.published_at.isoformat() if item.published_at else None,
            }
            for item in related
        ]
    }


@router.post("/")
def create_article(
    req: dict,
    db: Session = Depends(get_db),
    admin = Depends(require_admin),
):
    title = sanitize_input(req.get("title", ""))
    if not title:
        raise HTTPException(status_code=400, detail="标题不能为空")
    
    slug = req.get("slug") or generate_slug(title)
    existing = db.query(NewsArticle).filter(NewsArticle.slug == slug).first()
    if existing:
        slug = f"{slug}-{uuid.uuid4().hex[:6]}"
    
    now = datetime.now()
    article = NewsArticle(
        id=str(uuid.uuid4()),
        title=title,
        slug=slug,
        subtitle=sanitize_input(req.get("subtitle", "")),
        summary=sanitize_input(req.get("summary", "")),
        content=req.get("content", ""),
        cover_image=req.get("cover_image"),
        category=req.get("category", "company"),
        tags=req.get("tags"),
        author=sanitize_input(req.get("author", "")),
        source=sanitize_input(req.get("source", "")),
        is_published=req.get("is_published", False),
        published_at=now if req.get("is_published") else None,
        sort_order=req.get("sort_order", 0),
        meta_title=sanitize_input(req.get("meta_title", "")),
        meta_description=sanitize_input(req.get("meta_description", "")),
    )
    
    db.add(article)
    db.commit()
    db.refresh(article)
    
    return {
        "id": article.id,
        "title": article.title,
        "slug": article.slug,
        "message": "文章创建成功",
    }


@router.put("/{article_id}")
def update_article(
    article_id: str,
    req: dict,
    db: Session = Depends(get_db),
    admin = Depends(require_admin),
):
    article = db.query(NewsArticle).filter(NewsArticle.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")
    
    if "title" in req:
        article.title = sanitize_input(req["title"])
    if "subtitle" in req:
        article.subtitle = sanitize_input(req["subtitle"])
    if "summary" in req:
        article.summary = sanitize_input(req["summary"])
    if "content" in req:
        article.content = req["content"]
    if "cover_image" in req:
        article.cover_image = req["cover_image"]
    if "category" in req:
        article.category = req["category"]
    if "tags" in req:
        article.tags = req["tags"]
    if "author" in req:
        article.author = sanitize_input(req["author"])
    if "source" in req:
        article.source = sanitize_input(req["source"])
    if "sort_order" in req:
        article.sort_order = req["sort_order"]
    if "meta_title" in req:
        article.meta_title = sanitize_input(req["meta_title"])
    if "meta_description" in req:
        article.meta_description = sanitize_input(req["meta_description"])
    if "is_published" in req:
        article.is_published = req["is_published"]
        if req["is_published"] and not article.published_at:
            article.published_at = datetime.now()
    
    db.commit()
    db.refresh(article)
    
    return {
        "id": article.id,
        "title": article.title,
        "message": "文章更新成功",
    }


@router.delete("/{article_id}")
def delete_article(
    article_id: str,
    db: Session = Depends(get_db),
    admin = Depends(require_admin),
):
    article = db.query(NewsArticle).filter(NewsArticle.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")
    
    article.is_active = False
    db.commit()
    
    return {"message": "文章删除成功"}


@router.post("/batch-delete")
def batch_delete_articles(
    req: dict,
    db: Session = Depends(get_db),
    admin = Depends(require_admin),
):
    ids = req.get("ids", [])
    if not ids:
        raise HTTPException(status_code=400, detail="请提供要删除的文章ID")
    
    articles = db.query(NewsArticle).filter(
        NewsArticle.id.in_(ids),
        NewsArticle.is_active == True
    ).all()
    
    if not articles:
        raise HTTPException(status_code=404, detail="未找到指定文章")
    
    for article in articles:
        article.is_active = False
    
    db.commit()
    return {"message": f"成功删除 {len(articles)} 篇文章", "deleted_count": len(articles)}


@router.post("/batch-update-status")
def batch_update_status(
    req: dict,
    db: Session = Depends(get_db),
    admin = Depends(require_admin),
):
    ids = req.get("ids", [])
    is_published = req.get("is_published", False)
    
    if not ids:
        raise HTTPException(status_code=400, detail="请提供要更新的文章ID")
    
    articles = db.query(NewsArticle).filter(
        NewsArticle.id.in_(ids),
        NewsArticle.is_active == True
    ).all()
    
    now = datetime.now()
    for article in articles:
        article.is_published = is_published
        if is_published and not article.published_at:
            article.published_at = now
    
    db.commit()
    return {"message": f"成功更新 {len(articles)} 篇文章状态", "updated_count": len(articles)}


@router.get("/stats")
def get_article_stats(
    db: Session = Depends(get_db),
    admin = Depends(require_admin),
):
    total = db.query(func.count(NewsArticle.id)).filter(NewsArticle.is_active == True).scalar() or 0
    published = db.query(func.count(NewsArticle.id)).filter(
        NewsArticle.is_active == True,
        NewsArticle.is_published == True
    ).scalar() or 0
    draft = db.query(func.count(NewsArticle.id)).filter(
        NewsArticle.is_active == True,
        NewsArticle.is_published == False
    ).scalar() or 0
    
    category_stats = db.query(
        NewsArticle.category,
        func.count(NewsArticle.id).label('count')
    ).filter(NewsArticle.is_active == True).group_by(NewsArticle.category).all()
    
    category_dict = {cat: count for cat, count in category_stats}
    
    return {
        "total": total,
        "published": published,
        "draft": draft,
        "category_stats": category_dict,
    }
