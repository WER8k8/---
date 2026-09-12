"""SEO 收录复检 — 供 API 与 Celery 共用。"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.content import InclusionStatus, PublishTask

logger = logging.getLogger("uj-admin.seo_inclusion")


def _real_probe_enabled() -> bool:
    """实现 real探测enabled 的功能。
    
    :return: 返回 bool 结果
    """
    flag = getattr(settings, "INCLUSION_PROBE_REAL_ENABLED", None)
    if flag is not None:
        return bool(flag)
    return (settings.ENVIRONMENT or "").strip().lower() == "production"


def inclusion_probe_status() -> dict[str, Any]:
    """供 Admin 收录页展示 honest 探测状态。"""
    enabled = _real_probe_enabled()
    env = (settings.ENVIRONMENT or "development").strip().lower()
    return {
        "real_probe_enabled": enabled,
        "environment": env,
        "hint": (
            "生产环境已开启百度 site: 真实探测。"
            if enabled
            else "当前未开启真实收录探测（dev 或 INCLUSION_PROBE_REAL_ENABLED=false）；"
            "上生产或设置 INCLUSION_PROBE_REAL_ENABLED=true 后再信收录结果。"
        ),
    }


def recheck_inclusion_batch(
    db: Session,
    *,
    task_ids: list[str] | None = None,
    limit: int = 200,
    sleep_seconds: float = 1.2,
) -> dict[str, Any]:
    """复检已发布 URL 收录；生产默认 Baidu site: 探测。"""
    ids = _load_pending_publish_ids(db, task_ids=task_ids, limit=limit)
    updated = 0
    skipped = 0
    included_count = 0
    not_included_count = 0
    probe_modes: dict[str, int] = {}
    samples: list[dict[str, Any]] = []
    now = datetime.now(timezone.utc)
    use_real = _real_probe_enabled()
    for task_id in ids:
        task = db.query(PublishTask).filter_by(id=task_id).first()
        if not task or not task.published_url:
            skipped += 1
            continue

        if not use_real:
            skipped += 1
            mode = "stub"
            probe_modes[mode] = probe_modes.get(mode, 0) + 1
            if len(samples) < 8:
                samples.append(
                    {
                        "task_id": task_id,
                        "url": task.published_url[:120],
                        "included": None,
                        "probe_mode": mode,
                        "skipped": True,
                    }
                )
            continue

        probe = _probe_and_record_inclusion(db, task, now, sleep_seconds, task_id)
        mode = probe["mode"]
        probe_modes[mode] = probe_modes.get(mode, 0) + 1
        updated += probe["updated"]
        included_count += probe["included"]
        not_included_count += probe["not_included"]
        if len(samples) < 8:
            samples.append(
                {
                    "task_id": task_id,
                    "url": task.published_url[:120],
                    "included": probe["is_included"],
                    "probe_mode": mode,
                }
            )

    db.commit()
    report = {
        "checked": len(ids),
        "updated_count": updated,
        "skipped": skipped,
        "included_count": included_count,
        "not_included_count": not_included_count,
        "probe_modes": probe_modes,
        "real_probe": use_real,
        "samples": samples,
        "checked_at": now.isoformat(),
    }
    if updated and not_included_count > 0 and not_included_count / max(updated, 1) >= 0.3:
        try:
            from app.services.hermes.alert_dispatcher import notify_inclusion_batch
            notify_inclusion_batch(report)
        except Exception as exc:
            logger.warning("inclusion alert skipped: %s", exc)

    return report


def _load_pending_publish_ids(
    db: Session,
    *,
    task_ids: list[str] | None,
    limit: int,
) -> list[str]:
    """加载待复检任务 id 列表：未指定时取最新已发布 URL 任务。"""
    ids = list(task_ids or [])
    if not ids:
        rows = (
            db.query(PublishTask)
            .filter(
                PublishTask.published_url.isnot(None),
                PublishTask.published_url != "",
            )
            .order_by(PublishTask.updated_at.desc())
            .limit(limit)
            .all()
        )
        ids = [str(t.id) for t in rows]
    return ids


def _probe_and_record_inclusion(
    db: Session,
    task: PublishTask,
    now: datetime,
    sleep_seconds: float,
    task_id: str,
) -> dict[str, Any]:
    """真实探测单条 URL 收录并回写 InclusionStatus，返回统计增量。"""
    from app.services.seo.inclusion_probe import probe_url_inclusion
    probe = probe_url_inclusion(task.published_url, engine="baidu")
    if sleep_seconds > 0:
        time.sleep(sleep_seconds)

    mode = str(probe.get("probe_mode") or "unknown")
    is_included = bool(probe.get("included"))
    status = db.query(InclusionStatus).filter_by(task_id=task_id).first()
    if not status:
        kw = (task.title or task.published_url or "")[:500]
        status = InclusionStatus(
            task_id=task_id,
            url=task.published_url,
            keyword=kw,
        )
        db.add(status)

    status.url = task.published_url
    status.is_included = is_included
    status.search_engine = probe.get("search_engine") or "baidu"
    if probe.get("ranking_hint"):
        status.ranking = int(probe["ranking_hint"])
    status.last_checked_at = now
    try:
        from app.services.seo.inclusion_probe_cache import set_probe_mode
        set_probe_mode(db, task_id, mode)
    except Exception:
        pass

    return {
        "mode": mode,
        "is_included": is_included,
        "updated": 1,
        "included": 1 if is_included else 0,
        "not_included": 0 if is_included else 1,
    }
