# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""视频成品保留：预览 TTL、下载/发布 handoff、文件清理。"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.media_factory import MediaRenderTask
from app.models.tenant import Tenant

logger = logging.getLogger(__name__)

HANDOFF_DOWNLOADED = "downloaded"
HANDOFF_PUBLISHED = "published"
VALID_HANDOFF_ACTIONS = frozenset({HANDOFF_DOWNLOADED, HANDOFF_PUBLISHED})


def _utcnow() -> datetime:
    """_utcnow。
    :return: 返回处理结果。
    """
    return datetime.now(timezone.utc)


def _safe_tenant_settings(raw: str | None) -> dict[str, Any]:
    """_safe_tenant_settings。

    参数说明：
    :param raw: 参数 raw
    :return: 返回处理结果。
    """
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, TypeError):
        return {}


def retention_hours_for_tenant(db: Session, tenant_id: str | None) -> int:
    """平台默认 MEDIA_RETENTION_HOURS；租户 settings.media_retention_hours 可覆盖。"""
    default = int(getattr(settings, "MEDIA_RETENTION_HOURS", 72) or 72)
    if not tenant_id:
        return default
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        return default
    override = _safe_tenant_settings(tenant.settings).get("media_retention_hours")
    if isinstance(override, (int, float)) and override > 0:
        return int(override)
    return default


def monthly_limit_for_tenant(db: Session, tenant_id: str | None) -> int:
    """0 表示不限制。"""
    default = int(getattr(settings, "MEDIA_FACTORY_MONTHLY_LIMIT_PER_TENANT", 0) or 0)
    if not tenant_id:
        return default
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        return default
    override = _safe_tenant_settings(tenant.settings).get("media_monthly_video_limit")
    if isinstance(override, (int, float)) and override >= 0:
        return int(override)
    return default


def assert_tenant_video_quota(db: Session, tenant_id: str | None) -> None:
    """assert_tenant_video_quota。

    参数说明：
    :param db: 参数 db
    :param tenant_id: 参数 tenant_id
    :return: 返回处理结果。
    """
    limit = monthly_limit_for_tenant(db, tenant_id)
    if limit <= 0 or not tenant_id:
        return
    now = _utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    count = (
        db.query(MediaRenderTask)
        .filter(
            MediaRenderTask.tenant_id == tenant_id,
            MediaRenderTask.created_at >= month_start,
        )
        .count()
    )
    if count >= limit:
        raise ValueError(f"本月视频生成已达上限 {limit} 条，请升级套餐或下月再试")


def apply_render_complete_metadata(
    db: Session,
    task: MediaRenderTask,
    output_path: Path,
) -> None:
    """渲染成功后写入文件大小与过期时间。"""
    size = output_path.stat().st_size if output_path.exists() else 0
    hours = retention_hours_for_tenant(db, task.tenant_id)
    finished = _utcnow()
    task.file_size_bytes = size
    task.finished_at = task.finished_at or finished
    task.expires_at = finished + timedelta(hours=hours)
    task.purge_at = task.expires_at
    task.file_purged = False


def record_handoff(
    db: Session,
    task: MediaRenderTask,
    action: str,
    external_url: str | None = None,
) -> MediaRenderTask:
    """record_handoff。

    参数说明：
    :param db: 参数 db
    :param task: 参数 task
    :param action: 参数 action
    :param external_url: 参数 external_url
    :return: 返回处理结果。
    """
    if action not in VALID_HANDOFF_ACTIONS:
        raise ValueError(f"handoff 动作无效，支持: {', '.join(sorted(VALID_HANDOFF_ACTIONS))}")
    if task.file_purged or not task.result_path:
        raise ValueError("成品文件已过期或不存在，无法登记 handoff")

    handoff_hours = int(getattr(settings, "MEDIA_HANDOFF_DELETE_HOURS", 1) or 1)
    now = _utcnow()
    task.handoff_type = action
    task.handoff_at = now
    task.handoff_external_url = (external_url or "").strip() or None
    task.purge_at = now + timedelta(hours=handoff_hours)
    task.updated_at = now
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def delete_task_file(task: MediaRenderTask) -> bool:
    """删除磁盘文件；返回是否删除了物理文件。"""
    deleted = False
    path_str = (task.result_path or "").strip()
    if path_str:
        path = Path(path_str)
        if path.is_file():
            try:
                path.unlink()
                deleted = True
            except OSError as exc:
                logger.warning("Failed to delete media file %s: %s", path, exc)
    return deleted


def purge_task_media(db: Session, task: MediaRenderTask, *, reason: str = "expired") -> bool:
    """删除成品文件并标记任务；保留脚本与元数据。"""
    if task.file_purged:
        return False

    delete_task_file(task)
    task.result_url = None
    task.result_path = None
    task.file_purged = True
    if task.status == "done":
        task.status = "expired"
    task.updated_at = _utcnow()
    db.add(task)
    db.commit()
    db.refresh(task)
    logger.info("Purged media task %s (%s)", task.id, reason)
    return True


def _backfill_legacy_retention(db: Session) -> int:
    """为历史已完成任务补写 purge_at。"""
    rows = (
        db.query(MediaRenderTask)
        .filter(
            MediaRenderTask.purge_at.is_(None),
            MediaRenderTask.result_path.isnot(None),
            MediaRenderTask.file_purged == 0,
            MediaRenderTask.status == "done",
        )
        .all()
    )
    for task in rows:
        hours = retention_hours_for_tenant(db, task.tenant_id)
        anchor = task.finished_at or task.updated_at or _utcnow()
        if anchor.tzinfo is None:
            anchor = anchor.replace(tzinfo=timezone.utc)
        task.expires_at = anchor + timedelta(hours=hours)
        task.purge_at = task.expires_at
        db.add(task)
    if rows:
        db.commit()
    return len(rows)


def run_media_cleanup(db: Session) -> dict[str, Any]:
    """清理 purge_at 已到期的成品文件。"""
    backfilled = _backfill_legacy_retention(db)
    now = _utcnow()
    rows = (
        db.query(MediaRenderTask)
        .filter(
            MediaRenderTask.file_purged == 0,
            MediaRenderTask.purge_at.isnot(None),
            MediaRenderTask.purge_at <= now,
            MediaRenderTask.result_path.isnot(None),
        )
        .all()
    )
    purged = 0
    bytes_freed = 0
    for task in rows:
        bytes_freed += int(task.file_size_bytes or 0)
        if purge_task_media(db, task, reason="scheduled"):
            purged += 1
    return {
        "purged_count": purged,
        "bytes_freed": bytes_freed,
        "backfilled": backfilled,
        "checked_at": now.isoformat(),
    }


def retention_payload(task: MediaRenderTask, db: Session | None = None) -> dict[str, Any]:
    """序列化用：保留策略与倒计时。"""
    hours = retention_hours_for_tenant(db, task.tenant_id) if db else settings.MEDIA_RETENTION_HOURS
    now = _utcnow()
    purge_at = task.purge_at
    seconds_left: int | None = None
    if purge_at and not task.file_purged:
        if purge_at.tzinfo is None:
            purge_at = purge_at.replace(tzinfo=timezone.utc)
        seconds_left = max(0, int((purge_at - now).total_seconds()))

    return {
        "retention_hours": hours,
        "expires_at": task.expires_at.isoformat() if task.expires_at else None,
        "purge_at": task.purge_at.isoformat() if task.purge_at else None,
        "seconds_until_purge": seconds_left,
        "handoff_type": task.handoff_type,
        "handoff_at": task.handoff_at.isoformat() if task.handoff_at else None,
        "handoff_external_url": task.handoff_external_url,
        "file_purged": bool(task.file_purged),
        "file_size_bytes": int(task.file_size_bytes or 0),
        "tenant_id": task.tenant_id,
        "storage_note": _storage_note(task),
    }


def _storage_note(task: MediaRenderTask) -> str:
    """_storage_note。

    参数说明：
    :param task: 参数 task
    :return: 返回处理结果。
    """
    if task.file_purged or task.status == "expired":
        return "成品已过期删除，脚本仍保留，可重新渲染"
    if task.handoff_type == HANDOFF_PUBLISHED:
        return "已登记发布，成品将在 handoff 窗口后自动删除"
    if task.handoff_type == HANDOFF_DOWNLOADED:
        return "已登记下载，成品将在 shortly 后自动删除"
    return "预览缓存期内可下载；到期自动删除，脚本永久保留"
