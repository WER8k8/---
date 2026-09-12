"""海外社交媒体养号周期状态机 — 持久化 + 智能频控 + 平台规则联动。

升级自原内存态版本，新增：
- DB 持久化（NurtureCycle model）
- 各平台养号规则模板（与 platform_sync_service 同源）
- 发布前养号状态检查（can_publish_now）
- 频控窗口检查（rate_limit_check）
- 自动状态升级（auto_advance）
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.logging import get_logger

logger = get_logger(__name__)

# 状态流：draft → warming → active → cooling → paused → archived
VALID_TRANSITIONS: dict[str, set[str]] = {
    "draft": {"warming", "paused", "archived"},
    "warming": {"active", "paused", "archived"},
    "active": {"cooling", "paused", "archived"},
    "cooling": {"active", "paused", "archived"},
    "paused": {"warming", "draft", "archived"},
    "archived": set(),
}

# 各平台养号规则（与 platform_sync_service._CN_OVERRIDES / _INTL_OVERRIDES 同源）
# 增加了发布间隔、每日上限、冷却天数等频控参数
PLATFORM_NURTURE_PROFILES: dict[str, dict[str, Any]] = {
    # —— 国内平台 ——
    "抖音": {
        "warmup_days": 14,
        "daily_posts": 2,
        "daily_likes": 30,
        "daily_comments": 5,
        "daily_follows": 10,
        "post_interval_min_hours": 4,
        "warmup_phase_daily_posts": 1,
        "warmup_phase_daily_likes": 10,
        "warmup_phase_daily_comments": 2,
        "cooldown_days_after_warning": 3,
        "max_posts_per_hour": 1,
        "risk_keywords": ["引流", "加微信", "私聊"],
    },
    "快手": {
        "warmup_days": 14,
        "daily_posts": 2,
        "daily_likes": 25,
        "daily_comments": 4,
        "daily_follows": 8,
        "post_interval_min_hours": 4,
        "warmup_phase_daily_posts": 1,
        "warmup_phase_daily_likes": 8,
        "warmup_phase_daily_comments": 2,
        "cooldown_days_after_warning": 3,
        "max_posts_per_hour": 1,
        "risk_keywords": ["引流", "加微信"],
    },
    "哔哩哔哩": {
        "warmup_days": 21,
        "daily_posts": 1,
        "weekly_videos": 1,
        "daily_likes": 10,
        "daily_comments": 3,
        "daily_follows": 5,
        "post_interval_min_hours": 24,
        "warmup_phase_daily_posts": 0,
        "warmup_phase_daily_likes": 5,
        "warmup_phase_daily_comments": 1,
        "cooldown_days_after_warning": 5,
        "max_posts_per_hour": 1,
    },
    "小红书": {
        "warmup_days": 10,
        "daily_posts": 1,
        "daily_likes": 15,
        "daily_comments": 3,
        "daily_follows": 5,
        "post_interval_min_hours": 8,
        "warmup_phase_daily_posts": 0,
        "warmup_phase_daily_likes": 8,
        "warmup_phase_daily_comments": 2,
        "cooldown_days_after_warning": 3,
        "max_posts_per_hour": 1,
        "risk_keywords": ["微信", "wx", "VX"],
    },
    "微信视频号": {
        "warmup_days": 7,
        "daily_posts": 1,
        "daily_likes": 10,
        "daily_comments": 3,
        "daily_follows": 5,
        "post_interval_min_hours": 8,
        "warmup_phase_daily_posts": 0,
        "warmup_phase_daily_likes": 5,
        "warmup_phase_daily_comments": 1,
        "cooldown_days_after_warning": 2,
        "max_posts_per_hour": 1,
    },
    "微博": {
        "warmup_days": 7,
        "daily_posts": 3,
        "daily_likes": 20,
        "daily_comments": 5,
        "daily_follows": 10,
        "post_interval_min_hours": 2,
        "warmup_phase_daily_posts": 1,
        "warmup_phase_daily_likes": 10,
        "warmup_phase_daily_comments": 3,
        "cooldown_days_after_warning": 2,
        "max_posts_per_hour": 2,
    },
    "知乎": {
        "warmup_days": 14,
        "daily_posts": 1,
        "daily_answers": 2,
        "daily_likes": 8,
        "daily_comments": 3,
        "post_interval_min_hours": 8,
        "warmup_phase_daily_posts": 0,
        "warmup_phase_daily_likes": 4,
        "warmup_phase_daily_comments": 1,
        "cooldown_days_after_warning": 3,
        "max_posts_per_hour": 1,
    },
    "百家号": {
        "warmup_days": 7,
        "daily_posts": 2,
        "daily_likes": 5,
        "daily_comments": 2,
        "post_interval_min_hours": 6,
        "warmup_phase_daily_posts": 1,
        "warmup_phase_daily_likes": 3,
        "cooldown_days_after_warning": 2,
        "max_posts_per_hour": 1,
    },
    "头条号": {
        "warmup_days": 7,
        "daily_posts": 2,
        "daily_likes": 8,
        "daily_comments": 2,
        "post_interval_min_hours": 6,
        "warmup_phase_daily_posts": 1,
        "warmup_phase_daily_likes": 4,
        "cooldown_days_after_warning": 2,
        "max_posts_per_hour": 1,
    },
    # —— 国际平台 ——
    "TikTok": {
        "warmup_days": 14,
        "daily_posts": 2,
        "daily_likes": 20,
        "daily_comments": 5,
        "daily_follows": 10,
        "post_interval_min_hours": 4,
        "warmup_phase_daily_posts": 1,
        "warmup_phase_daily_likes": 10,
        "warmup_phase_daily_comments": 2,
        "cooldown_days_after_warning": 3,
        "max_posts_per_hour": 1,
    },
    "YouTube": {
        "warmup_days": 30,
        "daily_posts": 0,
        "weekly_videos": 1,
        "daily_likes": 5,
        "daily_comments": 2,
        "daily_follows": 3,
        "post_interval_min_hours": 72,
        "warmup_phase_daily_posts": 0,
        "warmup_phase_daily_likes": 3,
        "cooldown_days_after_warning": 7,
        "max_posts_per_hour": 1,
    },
    "Instagram": {
        "warmup_days": 14,
        "daily_posts": 1,
        "daily_stories": 2,
        "daily_likes": 20,
        "daily_comments": 5,
        "daily_follows": 10,
        "post_interval_min_hours": 6,
        "warmup_phase_daily_posts": 0,
        "warmup_phase_daily_likes": 10,
        "warmup_phase_daily_comments": 2,
        "cooldown_days_after_warning": 3,
        "max_posts_per_hour": 1,
    },
    "Facebook": {
        "warmup_days": 14,
        "daily_posts": 1,
        "daily_likes": 8,
        "daily_comments": 3,
        "daily_follows": 5,
        "post_interval_min_hours": 6,
        "warmup_phase_daily_posts": 0,
        "warmup_phase_daily_likes": 5,
        "warmup_phase_daily_comments": 2,
        "cooldown_days_after_warning": 3,
        "max_posts_per_hour": 1,
    },
    "LinkedIn": {
        "warmup_days": 21,
        "daily_posts": 1,
        "daily_connections": 5,
        "daily_likes": 10,
        "daily_comments": 3,
        "post_interval_min_hours": 8,
        "warmup_phase_daily_posts": 0,
        "warmup_phase_daily_likes": 5,
        "warmup_phase_daily_comments": 1,
        "cooldown_days_after_warning": 5,
        "max_posts_per_hour": 1,
    },
    "X": {
        "warmup_days": 10,
        "daily_posts": 3,
        "daily_likes": 15,
        "daily_comments": 5,
        "daily_follows": 10,
        "post_interval_min_hours": 2,
        "warmup_phase_daily_posts": 1,
        "warmup_phase_daily_likes": 8,
        "warmup_phase_daily_comments": 2,
        "cooldown_days_after_warning": 2,
        "max_posts_per_hour": 2,
    },
    "Pinterest": {
        "warmup_days": 14,
        "daily_posts": 3,
        "daily_likes": 10,
        "daily_follows": 5,
        "post_interval_min_hours": 2,
        "warmup_phase_daily_posts": 1,
        "warmup_phase_daily_likes": 5,
        "cooldown_days_after_warning": 3,
        "max_posts_per_hour": 1,
    },
    "Threads": {
        "warmup_days": 10,
        "daily_posts": 2,
        "daily_likes": 15,
        "daily_comments": 3,
        "daily_follows": 5,
        "post_interval_min_hours": 4,
        "warmup_phase_daily_posts": 1,
        "warmup_phase_daily_likes": 8,
        "cooldown_days_after_warning": 3,
        "max_posts_per_hour": 1,
    },
}

# 通用默认规则
_DEFAULT_RULES: dict[str, Any] = {
    "warmup_days": 14,
    "daily_posts": 1,
    "daily_likes": 10,
    "daily_comments": 3,
    "daily_follows": 5,
    "post_interval_min_hours": 6,
    "warmup_phase_daily_posts": 0,
    "warmup_phase_daily_likes": 5,
    "warmup_phase_daily_comments": 1,
    "cooldown_days_after_warning": 3,
    "max_posts_per_hour": 1,
}


def get_nurture_profile(platform: str) -> dict[str, Any]:
    """获取平台养号规则（含频控参数）。"""
    profile = PLATFORM_NURTURE_PROFILES.get(platform, {})
    return {**_DEFAULT_RULES, **profile}


# ---- 持久化 CRUD ----

def create_cycle(
    db: Session,
    *,
    tenant_id: str | None,
    platform: str,
    account_label: str,
    platform_account_id: str | None = None,
    notes: str = "",
    rules: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """创建养号周期（持久化到 DB）。"""
    from app.models.nurture_cycle import NurtureCycle as NurtureCycleModel
    resolved_rules = rules or get_nurture_profile(platform)
    cycle = NurtureCycleModel(
        id=str(uuid4()),
        tenant_id=tenant_id,
        platform=platform,
        account_label=account_label,
        platform_account_id=platform_account_id,
        status="draft",
        rules=resolved_rules,
        notes=notes,
    )
    db.add(cycle)
    db.commit()
    db.refresh(cycle)
    return _serialize_cycle(cycle)


def list_cycles(
    db: Session,
    *,
    tenant_id: str | None = None,
    platform: str | None = None,
    status: str | None = None,
) -> list[dict[str, Any]]:
    """列出养号周期。"""
    from app.models.nurture_cycle import NurtureCycle as NurtureCycleModel
    q = db.query(NurtureCycleModel)
    if tenant_id:
        q = q.filter(NurtureCycleModel.tenant_id == tenant_id)
    if platform:
        q = q.filter(NurtureCycleModel.platform == platform)
    if status:
        q = q.filter(NurtureCycleModel.status == status)

    rows = q.order_by(NurtureCycleModel.updated_at.desc()).all()
    return [_serialize_cycle(r) for r in rows]


def get_cycle(db: Session, cycle_id: str) -> dict[str, Any] | None:
    """获取单个养号周期。"""
    from app.models.nurture_cycle import NurtureCycle as NurtureCycleModel
    row = db.query(NurtureCycleModel).filter(NurtureCycleModel.id == cycle_id).first()
    return _serialize_cycle(row) if row else None


def transition_cycle(
    db: Session,
    *,
    cycle_id: str,
    new_status: str,
    notes: str | None = None,
) -> dict[str, Any]:
    """切换养号状态。"""
    from app.models.nurture_cycle import NurtureCycle as NurtureCycleModel
    row = db.query(NurtureCycleModel).filter(NurtureCycleModel.id == cycle_id).first()
    if not row:
        raise KeyError("cycle_not_found")

    current = row.status
    allowed = VALID_TRANSITIONS.get(current, set())
    if new_status not in allowed:
        raise ValueError(f"invalid_transition:{current}->{new_status}")

    row.status = new_status
    if new_status == "warming" and not row.started_at:
        row.started_at = datetime.now(timezone.utc)
    if notes:
        row.notes = notes
    db.commit()
    db.refresh(row)
    return _serialize_cycle(row)


def auto_advance(db: Session, cycle_id: str) -> dict[str, Any] | None:
    """自动升级养号状态（warmup 天数到期 → active；active 阶段可定期 cooling）。

    调度器每日执行一次，遍历所有 warming 状态的 cycle。
    """
    from app.models.nurture_cycle import NurtureCycle as NurtureCycleModel
    row = db.query(NurtureCycleModel).filter(NurtureCycleModel.id == cycle_id).first()
    if not row:
        return None

    # ORCH-13: 处理 active → cooling 转换（冷却期到期后恢复 active）
    if row.status == "cooling":
        if row.cooldown_until and datetime.now(timezone.utc) < row.cooldown_until:
            # 冷却期未结束，只更新时间戳
            db.commit()
            return _serialize_cycle(row)
        # 冷却期结束，自动恢复为 active
        row.status = "active"
        row.cooldown_until = None
        db.commit()
        db.refresh(row)
        logger.info("nurture_cycle %s cooling → active (cooldown ended)", cycle_id)
        return _serialize_cycle(row)

    if row.status != "warming":
        return None

    rules = row.rules or get_nurture_profile(row.platform)
    warmup_days = int(rules.get("warmup_days", 14))
    if not row.started_at:
        return None

    started = row.started_at
    if started.tzinfo is None:
        started = started.replace(tzinfo=timezone.utc)
    days_elapsed = (datetime.now(timezone.utc) - started).days
    row.current_day = days_elapsed
    if days_elapsed >= warmup_days:
        row.status = "active"
        db.commit()
        db.refresh(row)
        logger.info("nurture_cycle %s auto-advanced: warming → active (day %d/%d)", cycle_id, days_elapsed, warmup_days)
        return _serialize_cycle(row)

    db.commit()
    return _serialize_cycle(row)


# ---- 频控检查 ----

def rate_limit_check(
    db: Session,
    *,
    cycle_id: str,
    action_type: str,
) -> dict[str, Any]:
    """检查是否允许执行指定操作（发布/点赞/评论/关注）。

    返回 {"allowed": bool, "reason": str, "next_available_at": datetime|None}
    """
    from app.models.nurture_cycle import NurtureCycle as NurtureCycleModel
    row = db.query(NurtureCycleModel).filter(NurtureCycleModel.id == cycle_id).first()
    if not row:
        return {"allowed": False, "reason": "cycle_not_found", "next_available_at": None}

    rules = row.rules or get_nurture_profile(row.platform)
    now = datetime.now(timezone.utc)
    # 冷却期检查
    if row.cooldown_until and now < row.cooldown_until:
        return {
            "allowed": False,
            "reason": f"in_cooldown_until_{row.cooldown_until.isoformat()}",
            "next_available_at": row.cooldown_until,
        }

    # warming 阶段使用更保守的限制
    is_warming = row.status == "warming"
    post_key = "warmup_phase_daily_posts" if is_warming else "daily_posts"
    like_key = "warmup_phase_daily_likes" if is_warming else "daily_likes"
    comment_key = "warmup_phase_daily_comments" if is_warming else "daily_comments"
    if action_type == "post":
        max_daily = int(rules.get(post_key, rules.get("daily_posts", 1)))
        interval_hours = int(rules.get("post_interval_min_hours", 6))
        max_per_hour = int(rules.get("max_posts_per_hour", 1))
        # 检查每小时限制
        if row.last_post_at:
            hours_since = (now - row.last_post_at).total_seconds() / 3600
            if hours_since < max_per_hour:
                return {
                    "allowed": False,
                    "reason": f"hourly_limit: {max_per_hour}/hr",
                    "next_available_at": row.last_post_at + timedelta(hours=max_per_hour),
                }

        # 检查间隔限制
        if row.last_post_at:
            hours_since = (now - row.last_post_at).total_seconds() / 3600
            if hours_since < interval_hours:
                return {
                    "allowed": False,
                    "reason": f"interval_limit: min {interval_hours}h between posts",
                    "next_available_at": row.last_post_at + timedelta(hours=interval_hours),
                }

        # 检查每日限制
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        if row.last_post_at and row.last_post_at >= today_start:
            if row.total_posts >= max_daily:
                tomorrow = today_start + timedelta(days=1)
                return {
                    "allowed": False,
                    "reason": f"daily_limit: {max_daily} posts/day (warming)" if is_warming else f"daily_limit: {max_daily} posts/day",
                    "next_available_at": tomorrow,
                }

    elif action_type == "like":
        max_daily = int(rules.get(like_key, rules.get("daily_likes", 10)))
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        # 简化：用总 likes 估算当日（生产应按日统计）
        if row.total_likes > 0 and row.last_like_at and row.last_like_at >= today_start:
            pass  # 详细日计数需 engagement_records 聚合

    elif action_type == "comment":
        max_daily = int(rules.get(comment_key, rules.get("daily_comments", 3)))

    return {"allowed": True, "reason": "within_limits", "next_available_at": None}


def can_publish_now(db: Session, *, cycle_id: str) -> dict[str, Any]:
    """发布前快速检查：养号周期是否允许发布。"""
    from app.models.nurture_cycle import NurtureCycle as NurtureCycleModel
    row = db.query(NurtureCycleModel).filter(NurtureCycleModel.id == cycle_id).first()
    if not row:
        return {"allowed": True, "reason": "no_nurture_cycle"}

    if row.status in ("paused", "archived"):
        return {"allowed": False, "reason": f"cycle_status_{row.status}"}

    if row.cooldown_until and datetime.now(timezone.utc) < row.cooldown_until:
        return {
            "allowed": False,
            "reason": "in_cooldown",
            "next_available_at": row.cooldown_until,
        }

    check = rate_limit_check(db, cycle_id=cycle_id, action_type="post")
    return check


def record_action(
    db: Session,
    *,
    cycle_id: str,
    action_type: str,
) -> None:
    """记录一次操作（更新计数和时间戳）。"""
    from app.models.nurture_cycle import NurtureCycle as NurtureCycleModel
    row = db.query(NurtureCycleModel).filter(NurtureCycleModel.id == cycle_id).first()
    if not row:
        return

    now = datetime.now(timezone.utc)
    if action_type == "post":
        row.total_posts += 1
        row.last_post_at = now
    elif action_type == "like":
        row.total_likes += 1
        row.last_like_at = now
    elif action_type == "comment":
        row.total_comments += 1
        row.last_comment_at = now
    elif action_type == "follow":
        row.total_follows += 1
        row.last_follow_at = now

    db.commit()


def trigger_cooldown(db: Session, *, cycle_id: str, days: int | None = None) -> None:
    """触发冷却期（检测到风控信号时）。"""
    from app.models.nurture_cycle import NurtureCycle as NurtureCycleModel
    row = db.query(NurtureCycleModel).filter(NurtureCycleModel.id == cycle_id).first()
    if not row:
        return

    rules = row.rules or get_nurture_profile(row.platform)
    cooldown_days = days or int(rules.get("cooldown_days_after_warning", 3))
    row.cooldown_until = datetime.now(timezone.utc) + timedelta(days=cooldown_days)
    row.warning_count += 1
    db.commit()
    logger.warning(
        "nurture_cycle %s triggered cooldown for %d days (warning #%d)",
        cycle_id, cooldown_days, row.warning_count,
    )


# ---- 发布调度 ----

def schedule_publish(
    db: Session,
    *,
    tenant_id: str | None,
    platform_name: str,
    title: str,
    body: str = "",
    video_url: str | None = None,
    cover_url: str | None = None,
    tags: list[str] | None = None,
    scheduled_at: datetime | None = None,
    platform_account_id: str | None = None,
    content_master_id: str | None = None,
) -> dict[str, Any]:
    """创建定时发布任务。"""
    from app.models.nurture_cycle import ScheduledPublish as ScheduledPublishModel
    row = ScheduledPublishModel(
        id=str(uuid4()),
        tenant_id=tenant_id,
        platform_account_id=platform_account_id,
        platform_name=platform_name,
        title=title,
        body=body,
        video_url=video_url,
        cover_url=cover_url,
        tags=tags,
        content_master_id=content_master_id,
        scheduled_at=scheduled_at or datetime.now(timezone.utc),
        status="pending",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _serialize_scheduled(row)


def get_pending_scheduled(db: Session, *, limit: int = 50) -> list[dict[str, Any]]:
    """获取待执行的定时发布任务（带行锁，防止多副本并发读到同一批）。"""
    from app.models.nurture_cycle import ScheduledPublish as ScheduledPublishModel
    now = datetime.now(timezone.utc)
    rows = (
        db.query(ScheduledPublishModel)
        .filter(
            ScheduledPublishModel.status == "pending",
            ScheduledPublishModel.scheduled_at <= now,
        )
        .order_by(ScheduledPublishModel.scheduled_at.asc())
        .limit(limit)
        .with_for_update(skip_locked=True)  # 行锁：跳过已被其他事务锁定的行
        .all()
    )
    logger.info("get_pending_scheduled: acquired %d rows with row-level lock (limit=%d)", len(rows), limit)
    return [_serialize_scheduled(r) for r in rows]


def mark_scheduled_dispatched(db: Session, *, scheduled_id: str, publish_task_id: str | None = None) -> bool:
    """原子抢占：将 pending → dispatched，返回 True 表示成功抢占，False 表示已被其他事务处理。

    使用 UPDATE ... WHERE status = 'pending' 实现数据库级幂等键检查，
    防止并发副本重复发布同一任务。
    """
    from app.models.nurture_cycle import ScheduledPublish as ScheduledPublishModel
    updated = (
        db.query(ScheduledPublishModel)
        .filter(
            ScheduledPublishModel.id == scheduled_id,
            ScheduledPublishModel.status == "pending",  # 幂等键：仅 pending 状态可被抢占
        )
        .update(
            {
                "status": "dispatched",
                "dispatched_at": datetime.now(timezone.utc),
                "publish_task_id": publish_task_id,
            },
            synchronize_session=False,
        )
    )
    db.commit()
    success = updated > 0
    logger.info(
        "mark_scheduled_dispatched: id=%s success=%s (rows_updated=%d)",
        scheduled_id, success, updated,
    )
    return success


def mark_scheduled_result(
    db: Session,
    *,
    scheduled_id: str,
    success: bool,
    published_url: str | None = None,
    published_post_id: str | None = None,
    error_message: str | None = None,
    worker_chain: list[str] | None = None,
) -> None:
    """mark_scheduled_result。

    参数说明：
    :param db: 参数 db
    :param scheduled_id: 参数 scheduled_id
    :param success: 参数 success
    :param published_url: 参数 published_url
    :param published_post_id: 参数 published_post_id
    :param error_message: 参数 error_message
    :param worker_chain: 参数 worker_chain
    :return: 返回处理结果。
    """
    from app.models.nurture_cycle import ScheduledPublish as ScheduledPublishModel
    row = db.query(ScheduledPublishModel).filter(ScheduledPublishModel.id == scheduled_id).first()
    if not row:
        return
    row.status = "published" if success else "failed"
    row.published_url = published_url
    row.published_post_id = published_post_id
    row.error_message = error_message
    row.worker_chain = worker_chain
    row.published_at = datetime.now(timezone.utc) if success else None
    row.attempts += 1
    db.commit()


# ---- 互动记录 ----

def record_engagement(
    db: Session,
    *,
    tenant_id: str | None,
    platform: str,
    action_type: str,
    target_post_id: str | None = None,
    target_author: str | None = None,
    content: str | None = None,
    nurture_cycle_id: str | None = None,
    platform_account_id: str | None = None,
) -> dict[str, Any]:
    """记录一次互动操作。"""
    from app.models.nurture_cycle import EngagementRecord as EngagementRecordModel
    row = EngagementRecordModel(
        id=str(uuid4()),
        tenant_id=tenant_id,
        platform=platform,
        platform_account_id=platform_account_id,
        action_type=action_type,
        target_post_id=target_post_id,
        target_author=target_author,
        content=content,
        nurture_cycle_id=nurture_cycle_id,
        status="pending",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return {
        "id": str(row.id),
        "action_type": action_type,
        "platform": platform,
        "status": row.status,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


def list_engagements(
    db: Session,
    *,
    tenant_id: str | None = None,
    platform: str | None = None,
    action_type: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """list_engagements。

    参数说明：
    :param db: 参数 db
    :param tenant_id: 参数 tenant_id
    :param platform: 参数 platform
    :param action_type: 参数 action_type
    :param limit: 参数 limit
    :return: 返回处理结果。
    """
    from app.models.nurture_cycle import EngagementRecord as EngagementRecordModel
    q = db.query(EngagementRecordModel)
    if tenant_id:
        q = q.filter(EngagementRecordModel.tenant_id == tenant_id)
    if platform:
        q = q.filter(EngagementRecordModel.platform == platform)
    if action_type:
        q = q.filter(EngagementRecordModel.action_type == action_type)

    rows = q.order_by(EngagementRecordModel.created_at.desc()).limit(limit).all()
    return [
        {
            "id": str(r.id),
            "platform": r.platform,
            "action_type": r.action_type,
            "target_post_id": r.target_post_id,
            "target_author": r.target_author,
            "content": (r.content or "")[:200],
            "status": r.status,
            "error_message": (r.error_message or "")[:200] or None,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]


def _daily_limit_for_action(rules: dict[str, Any], action_type: str, *, warming: bool) -> int:
    """_daily_limit_for_action。

    参数说明：
    :param rules: 参数 rules
    :param action_type: 参数 action_type
    :param warming: 参数 warming
    :return: 返回处理结果。
    """
    if action_type in ("comment", "reply"):
        key = "warmup_phase_daily_comments" if warming else "daily_comments"
        return int(rules.get(key, rules.get("daily_comments", 3)))
    if action_type == "follow":
        key = "warmup_phase_daily_follows" if warming else "daily_follows"
        return int(rules.get(key, rules.get("daily_follows", 5)))
    key = "warmup_phase_daily_likes" if warming else "daily_likes"
    return int(rules.get(key, rules.get("daily_likes", 10)))


def plan_daily_engagements(db: Session, *, limit: int = 40) -> dict[str, Any]:
    """按养号规则 engagement_targets 生成 pending 任务（调度器周期调用）。"""
    from app.models.nurture_cycle import EngagementRecord as EngagementRecordModel
    from app.models.nurture_cycle import NurtureCycle as NurtureCycleModel
    planned = 0
    skipped_cycles = 0
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    cycles = (
        db.query(NurtureCycleModel)
        .filter(
            NurtureCycleModel.status.in_(("warming", "active")),
            NurtureCycleModel.platform_account_id.isnot(None),
        )
        .all()
    )
    for cycle in cycles:
        if planned >= limit:
            break

        rules = cycle.rules or get_nurture_profile(cycle.platform)
        targets = rules.get("engagement_targets") or []
        if not targets:
            skipped_cycles += 1
            continue

        warming = cycle.status == "warming"
        for spec in targets:
            if planned >= limit:
                break
            if not isinstance(spec, dict):
                continue

            action_type = str(spec.get("action_type") or "like").lower()
            if action_type == "reply":
                action_type = "comment"

            pending_exists = (
                db.query(EngagementRecordModel.id)
                .filter(
                    EngagementRecordModel.nurture_cycle_id == cycle.id,
                    EngagementRecordModel.status == "pending",
                    EngagementRecordModel.action_type == action_type,
                    EngagementRecordModel.target_post_id == spec.get("target_post_id"),
                )
                .first()
            )
            if pending_exists:
                continue

            success_today = (
                db.query(EngagementRecordModel.id)
                .filter(
                    EngagementRecordModel.nurture_cycle_id == cycle.id,
                    EngagementRecordModel.action_type == action_type,
                    EngagementRecordModel.status == "success",
                    EngagementRecordModel.created_at >= today_start,
                )
                .count()
            )
            if success_today >= _daily_limit_for_action(rules, action_type, warming=warming):
                continue

            check = rate_limit_check(db, cycle_id=str(cycle.id), action_type=action_type)
            if not check.get("allowed"):
                continue

            record_engagement(
                db,
                tenant_id=str(cycle.tenant_id) if cycle.tenant_id else None,
                platform=cycle.platform,
                action_type=action_type,
                target_post_id=spec.get("target_post_id"),
                target_author=spec.get("target_author"),
                content=spec.get("content"),
                nurture_cycle_id=str(cycle.id),
                platform_account_id=str(cycle.platform_account_id) if cycle.platform_account_id else None,
            )
            planned += 1

    return {"planned": planned, "skipped_cycles": skipped_cycles, "cycles_checked": len(cycles)}


# ---- 序列化 ----

def _serialize_cycle(row) -> dict[str, Any]:
    """_serialize_cycle。

    参数说明：
    :param row: 参数 row
    :return: 返回处理结果。
    """
    rules = row.rules or {}
    return {
        "id": str(row.id),
        "tenant_id": str(row.tenant_id) if row.tenant_id else None,
        "platform": row.platform,
        "account_label": row.account_label,
        "platform_account_id": str(row.platform_account_id) if row.platform_account_id else None,
        "status": row.status,
        "rules": rules,
        "current_day": row.current_day,
        "warmup_days": int(rules.get("warmup_days", 14)),
        "progress_pct": min(100, round(row.current_day / max(int(rules.get("warmup_days", 14)), 1) * 100)),
        "stats": {
            "total_posts": row.total_posts,
            "total_likes": row.total_likes,
            "total_comments": row.total_comments,
            "total_follows": row.total_follows,
        },
        "last_actions": {
            "last_post_at": row.last_post_at.isoformat() if row.last_post_at else None,
            "last_like_at": row.last_like_at.isoformat() if row.last_like_at else None,
            "last_comment_at": row.last_comment_at.isoformat() if row.last_comment_at else None,
            "last_follow_at": row.last_follow_at.isoformat() if row.last_follow_at else None,
        },
        "warning_count": row.warning_count,
        "cooldown_until": row.cooldown_until.isoformat() if row.cooldown_until else None,
        "notes": row.notes or "",
        "started_at": row.started_at.isoformat() if row.started_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "allowed_next": sorted(VALID_TRANSITIONS.get(row.status, set())),
    }


def _serialize_scheduled(row) -> dict[str, Any]:
    """_serialize_scheduled。

    参数说明：
    :param row: 参数 row
    :return: 返回处理结果。
    """
    return {
        "id": str(row.id),
        "tenant_id": str(row.tenant_id) if row.tenant_id else None,
        "platform_name": row.platform_name,
        "title": row.title,
        "video_url": row.video_url,
        "scheduled_at": row.scheduled_at.isoformat() if row.scheduled_at else None,
        "status": row.status,
        "attempts": row.attempts,
        "published_url": row.published_url,
        "error_message": (row.error_message or "")[:200] or None,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }
