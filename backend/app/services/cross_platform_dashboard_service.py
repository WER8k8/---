# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""跨平台数据聚合服务 — 从 AiToEarn 拉取各平台数据并聚合。

提供：
- 账号数据概览（粉丝/作品/互动统计）
- 发布效果追踪（播放/点赞/评论/分享）
- 养号效果看板（养号周期进度 + 互动完成率）
- 数据缓存（避免频繁调用 AiToEarn API）
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import json
import time
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.logging import get_logger

logger = get_logger(__name__)

# 缓存配置
CACHE_TTL_SECONDS = 300  # 5 分钟缓存
_cache: dict[str, dict[str, Any]] = {}


def _safe_asyncio_run(coro):
    """_safe_asyncio_run。

    参数说明：
    :param coro: 参数 coro
    :return: 返回处理结果。
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, coro).result()
    return asyncio.run(coro)


def _get_cached(key: str) -> dict[str, Any] | None:
    """获取缓存数据。"""
    if key not in _cache:
        return None
    entry = _cache[key]
    if time.time() - entry.get("ts", 0) > CACHE_TTL_SECONDS:
        del _cache[key]
        return None
    return entry.get("data")


def _set_cached(key: str, data: dict[str, Any]) -> None:
    """设置缓存数据。"""
    _cache[key] = {"ts": time.time(), "data": data}


async def _fetch_account_stats(tenant_id: str | None = None) -> list[dict[str, Any]]:
    """从 AiToEarn 获取所有账号的统计数据。"""
    from app.services.aitoearn_publish_adapter import fetch_accounts, aitoearn_enabled
    if not aitoearn_enabled():
        return []

    accounts = await fetch_accounts()
    # 租户数据隔离：过滤出属于该租户的账号
    if tenant_id:
        from app.services.platform_account_service import list_platform_accounts
        db = SessionLocal()
        try:
            tenant_accounts = list_platform_accounts(db, tenant_id=tenant_id)
            tenant_account_ids = {str(acc.bound_external_id) for acc in tenant_accounts if acc.bound_external_id}
            accounts = [acc for acc in accounts if str(acc.get("accountId") or acc.get("id") or "") in tenant_account_ids]
        finally:
            db.close()
    
    stats = []
    for acc in accounts:
        account_id = str(acc.get("accountId") or acc.get("id") or "")
        account_type = str(acc.get("accountType") or "")
        stats.append({
            "account_id": account_id,
            "platform": account_type,
            "nickname": acc.get("nickname") or acc.get("name") or "",
            "avatar": acc.get("avatar") or acc.get("headImg") or "",
            "followers": acc.get("followerCount") or acc.get("fans") or 0,
            "followings": acc.get("followingCount") or acc.get("follows") or 0,
            "total_posts": acc.get("postCount") or acc.get("works") or 0,
            "total_likes": acc.get("likeCount") or acc.get("likes") or 0,
            "status": acc.get("status") or "active",
            "bound_at": acc.get("bindTime") or acc.get("createdAt") or None,
        })
    return stats


async def _fetch_publish_stats(flow_id: str | None = None) -> list[dict[str, Any]]:
    """从 AiToEarn 获取发布任务统计。"""
    from app.services.aitoearn_publish_adapter import fetch_publish_tasks, aitoearn_enabled
    if not aitoearn_enabled():
        return []

    if not flow_id:
        # 无 flow_id 时返回空（需要具体 flow_id 才能查询）
        return []

    tasks = await fetch_publish_tasks(flow_id)
    stats = []
    for task in tasks:
        stats.append({
            "task_id": str(task.get("id") or ""),
            "account_id": str(task.get("accountId") or ""),
            "platform": task.get("accountType") or "",
            "status": task.get("status") or "pending",
            "title": task.get("title") or "",
            "video_url": task.get("videoUrl") or "",
            "post_url": task.get("postUrl") or task.get("publishUrl") or "",
            "views": task.get("viewCount") or task.get("playCount") or 0,
            "likes": task.get("likeCount") or task.get("likes") or 0,
            "comments": task.get("commentCount") or task.get("comments") or 0,
            "shares": task.get("shareCount") or task.get("shares") or 0,
            "created_at": task.get("createTime") or task.get("createdAt") or None,
            "published_at": task.get("publishTime") or task.get("publishedAt") or None,
        })
    return stats


async def get_platform_overview(tenant_id: str | None = None) -> dict[str, Any]:
    """获取跨平台数据概览（带缓存）。"""
    cache_key = f"platform_overview_{tenant_id or 'all'}"
    cached = _get_cached(cache_key)
    if cached:
        return cached

    try:
        account_stats = await _fetch_account_stats(tenant_id=tenant_id)
    except Exception as exc:
        logger.warning("fetch account stats failed: %s", exc)
        account_stats = []

    # 按平台聚合
    by_platform: dict[str, list[dict[str, Any]]] = {}
    for acc in account_stats:
        platform = acc.get("platform") or "unknown"
        if platform not in by_platform:
            by_platform[platform] = []
        by_platform[platform].append(acc)

    platform_summary = []
    for platform, accounts in by_platform.items():
        total_followers = sum(a.get("followers", 0) for a in accounts)
        total_posts = sum(a.get("total_posts", 0) for a in accounts)
        total_likes = sum(a.get("total_likes", 0) for a in accounts)
        platform_summary.append({
            "platform": platform,
            "account_count": len(accounts),
            "total_followers": total_followers,
            "total_posts": total_posts,
            "total_likes": total_likes,
            "accounts": accounts,
        })

    result = {
        "total_accounts": len(account_stats),
        "total_platforms": len(by_platform),
        "total_followers": sum(a.get("followers", 0) for a in account_stats),
        "total_posts": sum(a.get("total_posts", 0) for a in account_stats),
        "total_likes": sum(a.get("total_likes", 0) for a in account_stats),
        "platforms": platform_summary,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    _set_cached(cache_key, result)
    return result


async def get_nurture_dashboard(tenant_id: str | None = None) -> dict[str, Any]:
    """获取养号效果看板数据。"""
    db: Session = SessionLocal()
    try:
        from app.services.social_nurture_service import list_cycles
        cycles = list_cycles(db, tenant_id=tenant_id)
        # 统计各状态数量
        status_counts: dict[str, int] = {}
        for cycle in cycles:
            status = cycle.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1

        # 计算平均进度
        progress_list = [c.get("progress_pct", 0) for c in cycles]
        avg_progress = sum(progress_list) / len(progress_list) if progress_list else 0
        # 统计总互动次数
        total_likes = sum(c.get("stats", {}).get("total_likes", 0) for c in cycles)
        total_comments = sum(c.get("stats", {}).get("total_comments", 0) for c in cycles)
        total_follows = sum(c.get("stats", {}).get("total_follows", 0) for c in cycles)
        return {
            "total_cycles": len(cycles),
            "status_counts": status_counts,
            "avg_progress_pct": round(avg_progress, 1),
            "total_engagements": {
                "likes": total_likes,
                "comments": total_comments,
                "follows": total_follows,
            },
            "cycles": cycles[:20],  # 最多返回 20 条
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
    finally:
        db.close()


async def get_publish_dashboard(
    tenant_id: str | None = None,
    days: int = 7,
) -> dict[str, Any]:
    """获取发布效果看板数据。"""
    db: Session = SessionLocal()
    try:
        from app.models.nurture_cycle import ScheduledPublish
        since = datetime.now(timezone.utc) - timedelta(days=days)
        query = db.query(ScheduledPublish).filter(ScheduledPublish.created_at >= since)
        if tenant_id:
            query = query.filter(ScheduledPublish.tenant_id == tenant_id)

        rows = query.order_by(ScheduledPublish.created_at.desc()).limit(100).all()
        # 统计
        total = len(rows)
        succeeded = sum(1 for r in rows if r.status == "published")
        failed = sum(1 for r in rows if r.status == "failed")
        pending = sum(1 for r in rows if r.status == "pending")
        # 按平台统计
        by_platform: dict[str, int] = {}
        for r in rows:
            platform = r.platform_name or "unknown"
            by_platform[platform] = by_platform.get(platform, 0) + 1

        return {
            "period_days": days,
            "total_tasks": total,
            "succeeded": succeeded,
            "failed": failed,
            "pending": pending,
            "success_rate": round(succeeded / total * 100, 1) if total > 0 else 0,
            "by_platform": by_platform,
            "recent_tasks": [
                {
                    "id": str(r.id),
                    "platform": r.platform_name,
                    "title": r.title,
                    "status": r.status,
                    "scheduled_at": r.scheduled_at.isoformat() if r.scheduled_at else None,
                    "published_at": r.published_at.isoformat() if r.published_at else None,
                    "published_url": r.published_url,
                    "error_message": (r.error_message or "")[:200] or None,
                }
                for r in rows[:20]
            ],
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
    finally:
        db.close()


def get_platform_overview_sync() -> dict[str, Any]:
    """get_platform_overview_sync。
    :return: 返回处理结果。
    """
    return _safe_asyncio_run(get_platform_overview())


def get_nurture_dashboard_sync(tenant_id: str | None = None) -> dict[str, Any]:
    """get_nurture_dashboard_sync。

    参数说明：
    :param tenant_id: 参数 tenant_id
    :return: 返回处理结果。
    """
    return _safe_asyncio_run(get_nurture_dashboard(tenant_id=tenant_id))


def get_publish_dashboard_sync(
    tenant_id: str | None = None,
    days: int = 7,
) -> dict[str, Any]:
    """get_publish_dashboard_sync。

    参数说明：
    :param tenant_id: 参数 tenant_id
    :param days: 参数 days
    :return: 返回处理结果。
    """
    return _safe_asyncio_run(get_publish_dashboard(tenant_id=tenant_id, days=days))
