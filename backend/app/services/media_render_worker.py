# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""多媒体工厂渲染 worker：queued → rendering → done/failed。"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.media_factory import MediaRenderTask
from app.services.ai_invocation_service import get_scenario_runtime, log_ai_invocation
from app.services.cosmos_infer_service import (
    CosmosInferError,
    infer_text_to_video,
    script_to_video_prompt,
    write_mock_video,
)
from app.services.wan_video_service import (
    is_wan_video_configured,
    render_video_with_wan,
)
from app.services.media_cloud_upload_service import run_cloud_upload_background
from app.services.media_retention_service import apply_render_complete_metadata
from app.services.media_video_edit_service import load_edit_config, probe_video_duration, save_edit_config

logger = logging.getLogger(__name__)


def _media_output_dir() -> Path:
    """_media_output_dir。
    :return: 返回处理结果。
    """
    backend_root = Path(__file__).resolve().parents[2]
    rel = getattr(settings, "MEDIA_OUTPUT_DIR", "uploads/media_factory") or "uploads/media_factory"
    path = Path(rel)
    if not path.is_absolute():
        path = backend_root / rel
    path.mkdir(parents=True, exist_ok=True)
    return path


def _now() -> datetime:
    """_now。
    :return: 返回处理结果。
    """
    return datetime.now(timezone.utc)


def get_task(db: Session, task_id: str) -> MediaRenderTask | None:
    """get_task。

    参数说明：
    :param db: 参数 db
    :param task_id: 参数 task_id
    :return: 返回处理结果。
    """
    return db.query(MediaRenderTask).filter(MediaRenderTask.id == task_id).first()


def _set_progress(db: Session, task: MediaRenderTask, progress: int, status: str | None = None) -> None:
    """_set_progress。

    参数说明：
    :param db: 参数 db
    :param task: 参数 task
    :param progress: 参数 progress
    :param status: 参数 status
    :return: 返回处理结果。
    """
    task.progress = max(0, min(100, progress))
    if status:
        task.status = status
    task.updated_at = _now()
    db.add(task)
    db.commit()
    db.refresh(task)


def _attach_edit_metadata(db: Session, task: MediaRenderTask, output_path: Path, *, mock: bool) -> None:
    """_attach_edit_metadata。

    参数说明：
    :param db: 参数 db
    :param task: 参数 task
    :param output_path: 参数 output_path
    :param mock: 参数 mock
    :return: 返回处理结果。
    """
    apply_render_complete_metadata(db, task, output_path)
    cfg = load_edit_config(task)
    dur = probe_video_duration(output_path)
    if dur is not None:
        cfg["source_duration_sec"] = round(dur, 3)
        cfg.setdefault("clip_start_sec", 0)
        cfg.setdefault("clip_end_sec", round(dur, 3))
    cfg["mock_render"] = mock
    save_edit_config(db, task, cfg)


def run_render_task(db: Session, task_id: str) -> MediaRenderTask:
    """同步执行单个渲染任务。"""
    task = get_task(db, task_id)
    if not task:
        raise ValueError(f"任务不存在: {task_id}")

    if task.status in {"rendering", "done"}:
        return task

    if task.status == "paused":
        raise RuntimeError("任务已暂停，请先恢复后再执行")

    runtime = get_scenario_runtime(db, task.scenario or "article_to_video_render", task.tenant_id)
    model = task.video_model or runtime["model_name"]
    prompt = task.prompt_text or script_to_video_prompt(task.script)
    task.status = "rendering"
    task.progress = 5
    task.started_at = _now()
    task.error_message = None
    task.updated_at = _now()
    if not task.prompt_text:
        task.prompt_text = prompt
    if not task.video_model:
        task.video_model = model
    db.add(task)
    db.commit()
    db.refresh(task)
    started = _now()
    success = False
    error_message: str | None = None
    try:
        _set_progress(db, task, 20)
        output_dir = _media_output_dir()
        output_path = output_dir / f"{task.id}.mp4"
        engine = getattr(settings, "VIDEO_GENERATION_ENGINE", "wan").lower().strip()
        is_wan_preferred = (
            engine == "wan"
            or str(model or "").lower().startswith(("wan", "wanx"))
            or not getattr(settings, "AI_NVIDIA_COSMOS_BASE_URL", None)
        )

        if settings.MEDIA_FACTORY_MOCK_RENDER:
            write_mock_video(
                output_path,
                resolution=task.resolution or "720p",
                aspect=task.aspect or "16:9",
            )
            task.result_path = str(output_path)
            task.result_url = f"/uploads/media_factory/{task.id}.mp4"
            _attach_edit_metadata(db, task, output_path, mock=True)
            task.status = "done"
            task.progress = 100
            task.finished_at = _now()
            success = True
        elif is_wan_preferred:
            # 采用阿里 Wan-Video (Wan2.1) 最优解引擎
            _set_progress(db, task, 30)

            def progress_cb(pct: int, hint: str):
                _set_progress(db, task, pct)

            wan_res = asyncio.run(
                render_video_with_wan(
                    prompt=prompt,
                    output_path=output_path,
                    image_url=task.image_url,
                    model=model if str(model or "").startswith("wan") else "wanx2.1-t2v-plus",
                    resolution=task.resolution or "720p",
                    aspect=task.aspect or "16:9",
                    on_progress=progress_cb,
                )
            )
            if wan_res.get("ok") and output_path.is_file():
                task.result_path = str(output_path)
                task.result_url = f"/uploads/media_factory/{task.id}.mp4"
                _attach_edit_metadata(db, task, output_path, mock=bool(wan_res.get("degraded")))
                task.status = "done"
                task.progress = 100
                task.finished_at = _now()
                success = True
            else:
                raise RuntimeError(wan_res.get("error") or "Wan-Video 渲染未产出有效视频")
        else:
            _set_progress(db, task, 40)
            video_bytes = infer_text_to_video(
                model=model,
                prompt=prompt,
                resolution=task.resolution or "1080p",
                aspect=task.aspect or "16:9",
                image_url=task.image_url,
            )
            _set_progress(db, task, 80)
            output_path.write_bytes(video_bytes)
            task.result_path = str(output_path)
            task.result_url = f"/uploads/media_factory/{task.id}.mp4"
            _attach_edit_metadata(db, task, output_path, mock=False)
            task.status = "done"
            task.progress = 100
            task.finished_at = _now()
            success = True

    except (CosmosInferError, Exception) as exc:
        error_message = str(exc)
        task.status = "failed"
        task.progress = 0
        task.error_message = error_message
        task.finished_at = _now()
        logger.exception("Render task %s failed", task_id)

    task.updated_at = _now()
    db.add(task)
    db.commit()
    db.refresh(task)
    elapsed_ms = int((_now() - started).total_seconds() * 1000)
    log_ai_invocation(
        db,
        runtime=runtime,
        task_type=task.scenario or "article_to_video_render",
        token_usage=0,
        duration_ms=elapsed_ms,
        success=success,
        error_message=error_message,
    )
    if success:
        run_cloud_upload_background(task_id)
    return task


def run_render_task_background(task_id: str) -> None:
    """后台线程/BackgroundTasks 入口（独立 DB 会话）。"""
    db = SessionLocal()
    try:
        run_render_task(db, task_id)
    except Exception as exc:
        logger.exception("Background render failed for %s: %s", task_id, exc)
    finally:
        db.close()
