# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""中文片出海 Worker：听写 / 出海（Celery 或后台线程调用）。"""

from __future__ import annotations

import asyncio
import concurrent.futures
import json
import logging
from typing import Any

from sqlalchemy.orm import Session

from app.models.media_factory import MediaRenderTask
from app.models.tenant import Tenant
from app.models.user import User
from app.services.cross_border.cross_border_job_service import (
    _parse_job_payload,
    append_job_event,
    save_job_result,
    set_job_progress,
)
from app.services.cross_border.whisper_model_pool import warm_whisper_model
from app.services.cross_border.premium_video_dub_service import run_premium_overseas_job
from app.services.cross_border.video_dub_service import (
    run_video_dub_job,
    transcribe_video_task,
)
from app.services.media_factory_service import get_render_task

logger = logging.getLogger(__name__)


def _job_progress_reporter(job_id: str):
    """跨会话上报进度（Worker 线程安全）。"""
    from app.core.database import SessionLocal

    def report(progress: int, hint: str) -> None:
        db = SessionLocal()
        try:
            task = get_render_task(db, job_id)
            if not task:
                return
            set_job_progress(db, task, progress, status="rendering", hint=hint)
        finally:
            db.close()

    return report


def _safe_asyncio_run(coro):
    """安全执行异步协程。"""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, coro).result()
    return asyncio.run(coro)


def _load_job_context(
    db: Session, job_id: str
) -> tuple[MediaRenderTask, Tenant, User, dict[str, Any]] | None:
    """加载任务上下文。"""
    task = get_render_task(db, job_id)
    if not task:
        return None
    payload = _parse_job_payload(task)
    tenant = db.query(Tenant).filter(Tenant.id == task.tenant_id).first()
    user = None
    user_id = payload.get("user_id")
    if user_id:
        user = db.query(User).filter(User.id == user_id).first()
    if not tenant or not user:
        return None
    return task, tenant, user, payload


def _run_and_persist_job_result(
    db: Session, task: MediaRenderTask, coro, progress_hint: str | None, fail_error: str
) -> dict[str, Any]:
    """执行跨境任务协程并保存结果（成功/失败统一处理）。"""
    result = _safe_asyncio_run(coro)
    if progress_hint:
        set_job_progress(db, task, 95, status="rendering", hint=progress_hint)
    else:
        set_job_progress(db, task, 95, status="rendering")
    if result.get("ok"):
        save_job_result(db, task, result, success=True)
    else:
        save_job_result(
            db,
            task,
            result,
            success=False,
            error_message=result.get("hint") or result.get("error") or fail_error,
        )
    return result


def run_cross_border_job(db: Session, job_id: str) -> dict[str, Any]:
    """执行出海作业流水线。"""
    ctx = _load_job_context(db, job_id)
    if not ctx:
        logger.error("cross_border job context missing: %s", job_id)
        return {"ok": False, "error": "job_not_found"}

    task, tenant, user, payload = ctx
    if task.status in ("done", "failed"):
        cfg_result = {}
        try:
            from app.services.media_video_edit_service import load_edit_config
            cfg_result = load_edit_config(task).get("cross_border_result") or {}
        except Exception:
            pass
        return {"ok": task.status == "done", **cfg_result}

    kind = payload.get("kind") or "transcribe"
    set_job_progress(db, task, 5, status="rendering", hint="任务开始…")
    warm_whisper_model()

    target_lang = str(payload.get("target_lang") or "en")
    voice_clone = bool(payload.get("voice_clone", True))
    lip_sync = bool(payload.get("lip_sync", True))
    distribute_platforms = payload.get("distribute_platforms")

    try:
        if kind == "transcribe":
            return _run_and_persist_job_result(
                db,
                task,
                transcribe_video_task(
                    db,
                    tenant,
                    user,
                    media_task_id=str(payload.get("media_task_id") or ""),
                    on_progress=_job_progress_reporter(job_id),
                ),
                "保存结果…",
                "听写失败",
            )

        if kind == "premium":
            return _run_and_persist_job_result(
                db,
                task,
                run_premium_overseas_job(
                    db,
                    tenant,
                    user,
                    media_task_id=str(payload.get("media_task_id") or ""),
                    track=str(payload.get("track") or "opensource_premium"),
                    localization_provider=payload.get("localization_provider"),
                    transcript_zh=payload.get("transcript_zh"),
                    voice_consent=bool(payload.get("voice_consent")),
                    output_mode=str(payload.get("output_mode") or "dub"),
                    dub_voice_gender=str(payload.get("dub_voice_gender") or "auto"),
                    target_lang=target_lang,
                    voice_clone=voice_clone,
                    lip_sync=lip_sync,
                    distribute_platforms=distribute_platforms,
                    on_progress=_job_progress_reporter(job_id),
                ),
                "保存精品结果…",
                "精品出海失败",
            )

        return _run_and_persist_job_result(
            db,
            task,
            run_video_dub_job(
                db,
                tenant,
                user,
                media_task_id=str(payload.get("media_task_id") or ""),
                transcript_zh=payload.get("transcript_zh"),
                voice_consent=bool(payload.get("voice_consent")),
                output_mode=str(payload.get("output_mode") or "dub"),
                auto_asr=bool(payload.get("auto_asr")),
                tts_voice=payload.get("tts_voice"),
                dub_voice_gender=str(payload.get("dub_voice_gender") or "auto"),
                target_lang=target_lang,
                voice_clone=voice_clone,
                lip_sync=lip_sync,
                distribute_platforms=distribute_platforms,
                on_progress=_job_progress_reporter(job_id),
            ),
            None,
            "出海版生成失败",
        )
    except Exception as exc:
        logger.exception("cross_border job %s failed", job_id)
        err = {"ok": False, "error": str(exc), "hint": "任务执行异常，请重试"}
        save_job_result(db, task, err, success=False, error_message=str(exc))
        return err
