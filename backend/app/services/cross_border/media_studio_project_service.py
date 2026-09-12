"""全媒体工作室项目持久化 — SRT/segments 存于 media_task edit_config。"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.user import User
from app.services.media_factory_service import get_render_task_for_user
from app.services.media_video_edit_service import load_edit_config, save_edit_config


def get_studio_project(
    db: Session,
    media_task_id: str,
    user: User,
) -> dict[str, Any] | None:
    """实现 获取studioproject 的功能。
    
    :param db: 参数 db（类型: Session）
    :param media_task_id: 参数 media_task_id（类型: str）
    :param user: 参数 user（类型: User）
    :return: 返回 dict[str, Any] | None 结果
    """
    task = get_render_task_for_user(db, media_task_id, user)
    if not task:
        return None
    cfg = load_edit_config(task)
    project = cfg.get("media_studio_project")
    if not isinstance(project, dict):
        project = {}
    dub = cfg.get("cross_border_dub") if isinstance(cfg.get("cross_border_dub"), dict) else {}
    premium = cfg.get("cross_border_premium") if isinstance(cfg.get("cross_border_premium"), dict) else {}
    return {
        "media_task_id": str(task.id),
        "title": task.title,
        "result_url": task.result_url,
        "project": project,
        "latest_dub": dub or None,
        "latest_premium": premium or None,
        "updated_at": project.get("updated_at"),
    }


def save_studio_project(
    db: Session,
    media_task_id: str,
    user: User,
    *,
    transcript_zh: str | None = None,
    script_en: str | None = None,
    srt_url: str | None = None,
    segments: list[dict[str, Any]] | None = None,
    asr_backend: str | None = None,
    localization_provider: str | None = None,
    output_url: str | None = None,
) -> dict[str, Any] | None:
    """实现 保存studioproject 的功能。
    
    :param db: 参数 db（类型: Session）
    :param media_task_id: 参数 media_task_id（类型: str）
    :param user: 参数 user（类型: User）
    :param transcript_zh: 参数 transcript_zh（类型: str | None）
    :param script_en: 参数 script_en（类型: str | None）
    :param srt_url: 参数 srt_url（类型: str | None）
    :param segments: 参数 segments（类型: list[dict[str, Any]] | None）
    :param asr_backend: 参数 asr_backend（类型: str | None）
    :param localization_provider: 参数 localization_provider（类型: str | None）
    :param output_url: 参数 output_url（类型: str | None）
    :return: 返回 dict[str, Any] | None 结果
    """
    task = get_render_task_for_user(db, media_task_id, user)
    if not task:
        return None

    cfg = load_edit_config(task)
    prev = cfg.get("media_studio_project")
    if not isinstance(prev, dict):
        prev = {}

    body: dict[str, Any] = {**prev}
    if transcript_zh is not None:
        body["transcript_zh"] = transcript_zh
    if script_en is not None:
        body["script_en"] = script_en
    if srt_url is not None:
        body["srt_url"] = srt_url
    if segments is not None:
        body["segments"] = segments
    if asr_backend is not None:
        body["asr_backend"] = asr_backend
    if localization_provider is not None:
        body["localization_provider"] = localization_provider
    if output_url is not None:
        body["output_url"] = output_url
    body["updated_at"] = datetime.now(timezone.utc).isoformat()
    cfg["media_studio_project"] = body
    save_edit_config(db, task, cfg)
    return get_studio_project(db, media_task_id, user)
