"""新闻管理路由 - 模块化架构"""

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.response import error_response, success_response
from app.core.security import get_current_user, get_current_user_optional
from app.db.session import get_db
from app.models.news import NewsArticle as News
from app.models.user import User


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = "/news"
ROUTE_TAGS = ["新闻管理"]

router = APIRouter()

_NEWS_COLUMNS = {c.name for c in News.__table__.columns}


def _news_to_dict(n: News) -> dict:
    """执行 news_to_dict 相关逻辑处理。
    
    :param n: 参数 n
    :return: 返回处理结果。
    """
    return {
        "id": n.id,
        "title": n.title,
        "slug": n.slug,
        "subtitle": n.subtitle,
        "summary": n.summary,
        "content": n.content,
        "cover_image": n.cover_image,
        "category": n.category,
        "tags": n.tags,
        "author": n.author,
        "source": n.source,
        "view_count": n.view_count,
        "is_published": n.is_published,
        "published_at": n.published_at.isoformat() if n.published_at else None,
        "sort_order": n.sort_order,
        "is_active": n.is_active,
        "meta_title": n.meta_title,
        "meta_description": n.meta_description,
        "created_at": n.created_at.isoformat() if n.created_at else None,
        "updated_at": n.updated_at.isoformat() if n.updated_at else None,
    }


def _filter_news_payload(req: dict) -> dict:
    """执行 filter_news_payload 相关逻辑处理。

    :param req: 请求对象
    :return: 返回处理结果。
    """
    payload = {k: v for k, v in req.items() if k in _NEWS_COLUMNS}
    # JSON 里的 DateTime 字段是 ISO 字符串，SQLite DateTime 列只接受 datetime 对象
    if isinstance(payload.get("published_at"), str):
        try:
            payload["published_at"] = datetime.fromisoformat(payload["published_at"])
        except ValueError:
            payload.pop("published_at", None)
    return payload


@router.get("", include_in_schema=False)
@router.get("/")
def list_news(
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    search: Optional[str] = None,
    public: bool = Query(False, description="公开访问：只返回已发布新闻，门户匿名用"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_optional),
):
    """获取新闻列表（分页）"""
    q = db.query(News).filter(News.is_active)
    if public or not current_user:
        q = q.filter(News.is_published)
    elif status == "published":
        q = q.filter(News.is_published)
    elif status == "draft":
        q = q.filter(News.is_published == False)
    if search:
        q = q.filter(News.title.ilike(f"%{search}%"))

    total = q.count()
    rows = q.order_by(
        News.sort_order,
        News.created_at.desc()).offset(
        (page - 1) * page_size).limit(page_size).all()
    items = [
        {
            "id": r.id,
            "title": r.title,
            "slug": r.slug,
            "category": r.category,
            "is_published": r.is_published,
            "view_count": r.view_count,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "updated_at": r.updated_at.isoformat() if r.updated_at else None,
        }
        for r in rows
    ]
    return success_response(
        data={
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size})


@router.get("/{news_id_or_slug}")
def get_news(
    news_id_or_slug: str,
    slug: Optional[str] = Query(None, description="按 slug 查公开已发布新闻（门户匿名用）"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_optional),
):
    """获取单个新闻详情。

    - 登录用户：可按 id 查任何启用新闻（含未发布）
    - 匿名门户访客：用 ?slug=xxx 仅查已发布新闻
    """
    q = db.query(News).filter(News.is_active)
    if slug or not current_user:
        q = q.filter(News.is_published)
    if slug:
        news = q.filter(News.slug == slug).first()
    else:
        news = q.filter(News.id == news_id_or_slug).first()
    if not news:
        return error_response(404, "新闻不存在")
    return success_response(data=_news_to_dict(news))


@router.post("", include_in_schema=False)
@router.post("/")
def create_news(req: dict, db: Session = Depends(get_db),
                current_user: User = Depends(get_current_user)):
    """创建新闻"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")

    payload = _filter_news_payload(req)
    if not payload.get("id"):
        # String 主键无服务端默认值，必须由应用侧生成
        payload["id"] = str(uuid.uuid4())
    news = News(**payload)
    db.add(news)
    db.commit()
    db.refresh(news)
    return success_response(data=_news_to_dict(news), message="新闻创建成功")


@router.put("/{news_id}")
def update_news(news_id: str, req: dict, db: Session = Depends(
        get_db), current_user: User = Depends(get_current_user)):
    """更新新闻"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")

    news = db.query(News).filter(News.id == news_id).first()
    if not news:
        return error_response(404, "新闻不存在")

    for k, v in _filter_news_payload(req).items():
        setattr(news, k, v)
    db.commit()
    db.refresh(news)
    return success_response(data=_news_to_dict(news), message="新闻更新成功")


@router.delete("/{news_id}")
def delete_news(news_id: str, db: Session = Depends(get_db),
                current_user: User = Depends(get_current_user)):
    """删除新闻"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")

    news = db.query(News).filter(News.id == news_id).first()
    if not news:
        return error_response(404, "新闻不存在")

    db.delete(news)
    db.commit()
    return success_response(message="新闻删除成功")
