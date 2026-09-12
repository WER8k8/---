"""Hermes ops：Rank Scheduler 状态与 keywords 表同步。"""

from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.seo import Keyword, KeywordRanking
from app.services.rank_scheduler import rank_scheduler

logger = logging.getLogger("uj-admin.rank_scheduler_ops")

DEFAULT_DOMAIN = "youding.com"


def _domain_from_url(url: str | None) -> str:
    """实现 domainfromURL 的功能。
    
    :param url: 参数 url（类型: str | None）
    :return: 返回 str 结果
    """
    if not url:
        return DEFAULT_DOMAIN
    try:
        netloc = urlparse(url).netloc
        return netloc or DEFAULT_DOMAIN
    except Exception:
        return DEFAULT_DOMAIN


def sync_keywords_from_db(db: Session, limit: int = 200) -> dict[str, Any]:
    """实现 同步关键词from数据库 的功能。
    
    :param db: 参数 db（类型: Session）
    :param limit: 参数 limit（类型: int）
    :return: 返回 dict[str, Any] 结果
    """
    rows = (
        db.query(Keyword)
        .filter(Keyword.is_active.is_(True))
        .order_by(Keyword.updated_at.desc())
        .limit(limit)
        .all()
    )
    items = [
        {"keyword": r.keyword, "domain": _domain_from_url(r.target_url)}
        for r in rows
        if r.keyword
    ]
    added = rank_scheduler.add_keywords(items)
    return {
        "db_active_keywords": len(rows),
        "synced_items": len(items),
        "scheduler": added,
        "status": rank_scheduler.get_status(),
    }


def recent_rankings(db: Session, limit: int = 50) -> list[dict[str, Any]]:
    """实现 recentrankings 的功能。
    
    :param db: 参数 db（类型: Session）
    :param limit: 参数 limit（类型: int）
    :return: 返回 list[dict[str, Any]] 结果
    """
    rows = (
        db.query(KeywordRanking)
        .filter(KeywordRanking.is_tracking.is_(True))
        .order_by(KeywordRanking.updated_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "keyword": r.keyword,
            "search_engine": r.search_engine,
            "current_position": r.current_position,
            "previous_position": r.previous_position,
            "best_position": r.best_position,
            "last_checked_at": r.last_checked_at.isoformat() if r.last_checked_at else None,
        }
        for r in rows
    ]


def build_rank_scheduler_ops_snapshot(db: Session) -> dict[str, Any]:
    """实现 构建排名scheduleropssnapshot 的功能。
    
    :param db: 参数 db（类型: Session）
    :return: 返回 dict[str, Any] 结果
    """
    enabled = bool(getattr(settings, "RANK_SCHEDULER_ENABLED", False))
    out: dict[str, Any] = {
        "enabled": enabled,
        "scheduler": rank_scheduler.get_status(),
        "tracked_keywords": rank_scheduler.get_tracked_keywords(),
        "recent_rankings": recent_rankings(db, limit=30),
        "db_keyword_count": db.query(Keyword).filter(Keyword.is_active.is_(True)).count(),
    }
    if enabled and not out["tracked_keywords"]:
        out["hint"] = "建议 POST /hermes/ops/rank-scheduler/sync 从 keywords 表同步追踪词"
    return out


def run_rank_check_now(db: Session) -> dict[str, Any]:
    """实现 执行排名检查now 的功能。
    
    :param db: 参数 db（类型: Session）
    :return: 返回 dict[str, Any] 结果
    """
    if not rank_scheduler.get_tracked_keywords():
        sync_keywords_from_db(db)
    results = rank_scheduler.schedule_daily_check()
    return {
        "checked": len(results),
        "results": results[:20],
        "status": rank_scheduler.get_status(),
    }
