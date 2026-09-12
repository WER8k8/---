"""中文片出海异步任务：入队、调度、查询（复用 media_render_tasks）。"""

from __future__ import annotations

import json
import logging
import threading
import uuid
from datetime import datetime, timezone
from typing import Any, Literal

from sqlalchemy.orm import Session

from app.models.media_factory import MediaRenderTask
from app.models.tenant import Tenant
from app.models.user import User
from app.services.media_factory_service import get_render_task_for_user
from app.services.media_video_edit_service import load_edit_config, save_edit_config

logger = logging.getLogger(__name__)

CROSS_BORDER_SCENARIOS = frozenset({
    "cross_border_transcribe",
    "cross_border_dub",
    "cross_border_premium",
})
JobKind = Literal["transcribe", "dub", "premium"]
MAX_TENANT_INFLIGHT = 2
MAX_GLOBAL_QUEUED = 50


def _utcnow() -> datetime:
    """实现 utcnow 的功能。
    
    :return: 返回 datetime 结果
    """
    return datetime.now(timezone.utc)


def _count_tenant_inflight(db: Session, tenant_id: str) -> int:
    """实现 数量租户inflight 的功能。
    
    :param db: 参数 db（类型: Session）
    :param tenant_id: 参数 tenant_id（类型: str）
    :return: 返回 int 结果
    """
    return (
        db.query(MediaRenderTask)
        .filter(
            MediaRenderTask.tenant_id == tenant_id,
            MediaRenderTask.scenario.in_(tuple(CROSS_BORDER_SCENARIOS)),
            MediaRenderTask.status.in_(("queued", "rendering")),
        )
        .count()
    )


def _count_global_queued(db: Session) -> int:
    """实现 数量globalqueued 的功能。
    
    :param db: 参数 db（类型: Session）
    :return: 返回 int 结果
    """
    return (
        db.query(MediaRenderTask)
        .filter(
            MediaRenderTask.scenario.in_(tuple(CROSS_BORDER_SCENARIOS)),
            MediaRenderTask.status == "queued",
        )
        .count()
    )


def _parse_job_payload(task: MediaRenderTask) -> dict[str, Any]:
    """实现 解析任务payload 的功能。
    
    :param task: 参数 task（类型: MediaRenderTask）
    :return: 返回 dict[str, Any] 结果
    """
    try:
        data = json.loads(task.script or "{}")
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}


def _scenario_for_kind(kind: JobKind) -> str:
    """实现 scenariofor种类 的功能。
    
    :param kind: 参数 kind（类型: JobKind）
    :return: 返回 str 结果
    """
    if kind == "transcribe":
        return "cross_border_transcribe"
    if kind == "premium":
        return "cross_border_premium"
    return "cross_border_dub"


def create_cross_border_job(
    db: Session,
    *,
    tenant: Tenant,
    user: User,
    media_task_id: str,
    kind: JobKind,
    payload: dict[str, Any] | None = None,
) -> tuple[MediaRenderTask | None, dict[str, Any] | None]:
    """创建并入队跨境任务。返回 (task, error_dict)。"""
    media = get_render_task_for_user(db, media_task_id, user)
    if not media or str(media.tenant_id or "") != str(tenant.id):
        return None, {"code": 404, "message": "找不到该视频，请先上传"}

    inflight = _count_tenant_inflight(db, str(tenant.id))
    if inflight >= MAX_TENANT_INFLIGHT:
        return None, {
            "code": 429,
            "message": f"该租户已有 {inflight} 个听写/出海任务进行中，请稍后再试",
            "error_code": "TENANT_JOB_LIMIT",
        }

    queued = _count_global_queued(db)
    if queued >= MAX_GLOBAL_QUEUED:
        return None, {
            "code": 503,
            "message": "系统繁忙，队列已满，请 1 分钟后再试",
            "error_code": "QUEUE_FULL",
        }

    body = {
        "kind": kind,
        "media_task_id": media_task_id,
        "user_id": str(user.id),
        **(payload or {}),
    }
    job = MediaRenderTask(
        id=str(uuid.uuid4()),
        title=f"出海{'听写' if kind == 'transcribe' else '精品' if kind == 'premium' else '生成'} · {(media.title or '视频')[:40]}",
        task_type="video",
        script=json.dumps(body, ensure_ascii=False),
        scenario=_scenario_for_kind(kind),
        status="queued",
        progress=0,
        tenant_id=str(tenant.id),
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job, None


def dispatch_cross_border_job(job_id: str) -> str:
    """调度执行；返回 backend: celery|thread。"""
    if _try_celery_dispatch(job_id):
        return "celery"
    thread = threading.Thread(
        target=_run_cross_border_job_background,
        args=(job_id,),
        name=f"cross-border-{job_id[:8]}",
        daemon=True,
    )
    thread.start()
    return "thread"


def _try_celery_dispatch(job_id: str) -> bool:
    """实现 trycelery调度 的功能。
    
    :param job_id: 参数 job_id（类型: str）
    :return: 返回 bool 结果
    """
    try:
        from app.tasks.cross_border_tasks import dispatch_by_job_id
        return dispatch_by_job_id(job_id)
    except Exception as exc:
        logger.warning("celery dispatch unavailable, fallback thread: %s", exc)
        return False


def _run_cross_border_job_background(job_id: str) -> None:
    """实现 执行crossborder任务background 的功能。
    
    :param job_id: 参数 job_id（类型: str）
    :return: 返回 None 结果
    """
    from app.core.database import SessionLocal
    from app.services.cross_border.cross_border_worker import run_cross_border_job
    db = SessionLocal()
    try:
        run_cross_border_job(db, job_id)
    except Exception:
        logger.exception("cross_border background job failed: %s", job_id)
    finally:
        db.close()


def get_cross_border_job(
    db: Session,
    job_id: str,
    user: User,
) -> MediaRenderTask | None:
    """实现 获取crossborder任务 的功能。
    
    :param db: 参数 db（类型: Session）
    :param job_id: 参数 job_id（类型: str）
    :param user: 参数 user（类型: User）
    :return: 返回 MediaRenderTask | None 结果
    """
    task = get_render_task_for_user(db, job_id, user)
    if not task or (task.scenario or "") not in CROSS_BORDER_SCENARIOS:
        return None
    return task


def serialize_cross_border_job(task: MediaRenderTask) -> dict[str, Any]:
    """实现 serializecrossborder任务 的功能。
    
    :param task: 参数 task（类型: MediaRenderTask）
    :return: 返回 dict[str, Any] 结果
    """
    payload = _parse_job_payload(task)
    cfg = load_edit_config(task)
    result = cfg.get("cross_border_result") if isinstance(cfg.get("cross_border_result"), dict) else {}
    kind = payload.get("kind") or (
        "transcribe"
        if task.scenario == "cross_border_transcribe"
        else "premium"
        if task.scenario == "cross_border_premium"
        else "dub"
    )
    status_map = {
        "queued": "queued",
        "rendering": "running",
        "done": "done",
        "failed": "failed",
        "paused": "failed",
    }
    api_status = status_map.get(task.status or "queued", "queued")
    out: dict[str, Any] = {
        "job_id": str(task.id),
        "kind": kind,
        "status": api_status,
        "progress": int(task.progress or 0),
        "media_task_id": payload.get("media_task_id"),
        "error": task.error_message,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "finished_at": task.finished_at.isoformat() if task.finished_at else None,
    }
    if api_status == "done" and result:
        out["result"] = result
        if kind == "transcribe":
            out["text"] = result.get("text")
            out["backend"] = result.get("backend")
            out["hint"] = result.get("hint")
        else:
            out.update({k: result.get(k) for k in (
                "script_en", "transcript_zh", "srt_url", "output_url",
                "audio_url", "output_mode", "hint", "asr", "segments",
                "localization_provider", "localization_mode", "track",
                "lip_sync", "voice_clone", "error_code",
            ) if result.get(k) is not None})
    elif api_status == "failed":
        out["hint"] = task.error_message or result.get("hint") or "任务失败，请重试或手动粘贴解说词"
        if result:
            out["result"] = result
            out.update({k: result.get(k) for k in (
                "script_en", "transcript_zh", "srt_url", "output_url",
                "audio_url", "output_mode", "asr", "segments", "error_code",
            ) if result.get(k) is not None})
    elif api_status == "queued":
        out["hint"] = "已入队，请稍候…"
    else:
        out["hint"] = f"处理中 {task.progress or 0}%"
    events = cfg.get("cross_border_events")
    if isinstance(events, list) and events:
        out["events"] = events[-10:]
    return out


def save_job_result(
    db: Session,
    task: MediaRenderTask,
    result: dict[str, Any],
    *,
    success: bool,
    error_message: str | None = None,
) -> None:
    """实现 保存任务结果 的功能。
    
    :param db: 参数 db（类型: Session）
    :param task: 参数 task（类型: MediaRenderTask）
    :param result: 参数 result（类型: dict[str, Any]）
    :param success: 参数 success（类型: bool）
    :param error_message: 参数 error_message（类型: str | None）
    :return: 返回 None 结果
    """
    cfg = load_edit_config(task)
    cfg["cross_border_result"] = result
    save_edit_config(db, task, cfg)
    task.status = "done" if success else "failed"
    task.progress = 100 if success else int(task.progress or 0)
    task.error_message = error_message
    task.finished_at = _utcnow()
    task.updated_at = _utcnow()
    db.add(task)
    db.commit()


def set_job_progress(
    db: Session,
    task: MediaRenderTask,
    progress: int,
    status: str | None = None,
    *,
    hint: str | None = None,
) -> None:
    """实现 设置任务progress 的功能。
    
    :param db: 参数 db（类型: Session）
    :param task: 参数 task（类型: MediaRenderTask）
    :param progress: 参数 progress（类型: int）
    :param status: 参数 status（类型: str | None）
    :param hint: 参数 hint（类型: str | None）
    :return: 返回 None 结果
    """
    task.progress = max(0, min(100, progress))
    if status:
        task.status = status
    if status == "rendering" and not task.started_at:
        task.started_at = _utcnow()
    task.updated_at = _utcnow()
    if hint:
        append_job_event(db, task, progress, hint, commit=False)
    db.add(task)
    db.commit()


def append_job_event(
    db: Session,
    task: MediaRenderTask,
    progress: int,
    hint: str,
    *,
    commit: bool = True,
) -> None:
    """实现 追加任务事件 的功能。
    
    :param db: 参数 db（类型: Session）
    :param task: 参数 task（类型: MediaRenderTask）
    :param progress: 参数 progress（类型: int）
    :param hint: 参数 hint（类型: str）
    :param commit: 参数 commit（类型: bool）
    :return: 返回 None 结果
    """
    cfg = load_edit_config(task)
    events = cfg.get("cross_border_events")
    if not isinstance(events, list):
        events = []
    events.append(
        {
            "ts": _utcnow().isoformat(),
            "progress": progress,
            "hint": hint,
        }
    )
    cfg["cross_border_events"] = events[-40:]
    task.edit_config = json.dumps(cfg, ensure_ascii=False)
    if commit:
        db.add(task)
        db.commit()
