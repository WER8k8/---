# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""多媒体工厂业务逻辑。"""



from __future__ import annotations



import uuid
from datetime import datetime, timezone
from typing import Any



from sqlalchemy.orm import Session



from app.core.config import settings

from app.models.media_factory import MediaRenderTask

from app.services.cosmos_infer_service import script_to_video_prompt
from app.services.media_retention_service import (
    assert_tenant_video_quota,
    delete_task_file,
    purge_task_media,
    retention_payload,
)
from app.services.media_cloud_upload_service import overseas_publish_video_url
from app.models.user import User
from app.services.media_video_edit_service import effective_preview_url, load_edit_config
from app.services.product_image_storage_service import (
    resolve_tenant_scope,
    store_uploaded_bytes,
    validate_platform_tenant_id,
)
from app.services.tenant_scenario_service import resolve_tenant_id_for_user


def _publish_video_url(task: MediaRenderTask) -> str | None:
    """_publish_video_url。

    参数说明：
    :param task: 参数 task
    :return: 返回处理结果。
    """
    return overseas_publish_video_url(task)

from app.services.nvidia_scenario_service import get_scenario_mappings





CONTENT_TYPE_SCENARIO = {

    "video-script": "article_to_video_script",

    "article": "article",

    "marketing": "article",

}





def scenario_for_content_type(content_type: str) -> str:
    """scenario_for_content_type。

    参数说明：
    :param content_type: 参数 content_type
    :return: 返回处理结果。
    """
    return CONTENT_TYPE_SCENARIO.get((content_type or "").strip(), "article_to_video_script")





def build_ai_write_prompt(prompt: str, content_type: str) -> str:
    """build_ai_write_prompt。

    参数说明：
    :param prompt: 参数 prompt
    :param content_type: 参数 content_type
    :return: 返回处理结果。
    """
    if content_type == "video-script":

        return (

            "请将以下需求写成短视频分镜脚本，包含镜头序号、画面描述、旁白文案，"
            "总时长约 60 秒：\n\n"
            f"{prompt.strip()}"

        )

    return prompt.strip()





def build_dev_video_script_fallback(prompt: str) -> str:

    """开发/MVP 下 LLM 不可用时的分镜脚本模板。"""
    topic = (prompt or "施工场景").strip()
    return (

        f"镜头1 | 航拍全景，展示项目规模 | 走进{topic}，见证现代工程的力量与效率。\n"
        f"镜头2 | 材料进场与配比作业特写 | 原材料严格检验，每一批{topic}都符合标准。\n"
        "镜头3 | 施工班组协同作业 | 工序衔接流畅，安全与质量同步把控。\n"
        "镜头4 | 关键节点检测与验收 | 数据实时记录，确保施工过程可追溯。\n"
        f"镜头5 | 成品效果与团队合影 | {topic}顺利推进，为项目交付打下坚实基础。"

    )





def build_article_to_video_script_prompt(article: str) -> str:
    """build_article_to_video_script_prompt。

    参数说明：
    :param article: 参数 article
    :return: 返回处理结果。
    """
    return (

        "请将以下文章改写成 60 秒短视频分镜脚本。"
        "输出格式：按「镜头N | 画面描述 | 旁白文案」分行，语言简洁、适合配音。\n\n"
        f"{article.strip()}"

    )





def create_render_task(db: Session, payload: dict[str, Any]) -> MediaRenderTask:
    """create_render_task。

    参数说明：
    :param db: 参数 db
    :param payload: 参数 payload
    :return: 返回处理结果。
    """
    script = (payload.get("script") or "").strip()
    if not script:

        raise ValueError("script 不能为空")

    tenant_id = (payload.get("tenant_id") or "").strip() or None
    guest_token = (payload.get("guest_token") or "").strip() or None
    assert_tenant_video_quota(db, tenant_id)
    mappings = get_scenario_mappings(db)
    scenario = (payload.get("scenario") or "article_to_video_render").strip()
    video_model = (
        payload.get("video_model")
        or mappings.get(scenario)
        or mappings.get("article_to_video_render")
        or (
            "wanx2.1-t2v-plus"
            if getattr(settings, "VIDEO_GENERATION_ENGINE", "wan") == "wan"
            else mappings.get("text_to_video", "nvidia/cosmos-predict1-5b")
        )
    )
    title = (payload.get("title") or script[:40] or "视频任务").strip()
    prompt_text = (payload.get("prompt_text") or script_to_video_prompt(script)).strip()
    task = MediaRenderTask(

        id=str(uuid.uuid4()),
        title=title,
        task_type="video",
        script=script,
        scenario=scenario,
        prompt_text=prompt_text,
        status="queued",
        progress=0,
        priority=str(payload.get("priority") or "中"),
        video_model=video_model,
        voice=str(payload.get("voice") or ""),
        resolution=str(payload.get("resolution") or "1080p"),
        aspect=str(payload.get("aspect") or "16:9"),
        image_url=str(payload.get("image_url") or "") or None,
        tenant_id=tenant_id,
        guest_token=guest_token if not tenant_id else None,

    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task





def get_render_task(db: Session, task_id: str) -> MediaRenderTask | None:
    """get_render_task。

    参数说明：
    :param db: 参数 db
    :param task_id: 参数 task_id
    :return: 返回处理结果。
    """
    return db.query(MediaRenderTask).filter(MediaRenderTask.id == task_id).first()





def update_task_status(

    db: Session,

    task: MediaRenderTask,

    *,

    status: str | None = None,

    progress: int | None = None,

    error_message: str | None = None,

) -> MediaRenderTask:
    """update_task_status。

    参数说明：
    :param db: 参数 db
    :param task: 参数 task
    :param status: 参数 status
    :param progress: 参数 progress
    :param error_message: 参数 error_message
    :return: 返回处理结果。
    """
    if status is not None:

        task.status = status

    if progress is not None:

        task.progress = max(0, min(100, progress))

    if error_message is not None:

        task.error_message = error_message

    db.add(task)
    db.commit()
    db.refresh(task)
    return task





def serialize_task(task: MediaRenderTask, db: Session | None = None) -> dict[str, Any]:
    """serialize_task。

    参数说明：
    :param task: 参数 task
    :param db: 参数 db
    :return: 返回处理结果。
    """
    status_label = {

        "queued": "排队中",
        "rendering": "处理中",
        "done": "已完成",
        "failed": "失败",
        "paused": "已暂停",
        "cancelled": "已取消",
        "expired": "已过期",

    }.get(task.status, task.status)
    eta = "-"
    if task.status == "queued":

        eta = "待调度"

    elif task.status == "rendering":

        eta = "渲染中"

    elif task.status == "done":

        eta = "0s"



    return {

        "id": task.id,
        "name": task.title,
        "title": task.title,
        "task_type": task.task_type,
        "tenant_id": task.tenant_id,
        "type": "视频",
        "progress": task.progress,
        "priority": task.priority,
        "eta": eta,
        "status": status_label,
        "raw_status": task.status,
        "scenario": task.scenario,
        "script": task.script,
        "video_model": task.video_model,
        "prompt_text": task.prompt_text,
        "result_url": None if task.file_purged else task.result_url,
        "preview_url": effective_preview_url(task),
        "edited_result_url": None if task.file_purged else task.edited_result_url,
        "cloud_play_url": task.cloud_play_url,
        "cloud_r2_url": task.cloud_r2_url,
        "cloud_vid": task.cloud_vid,
        "cloud_upload_status": task.cloud_upload_status or "pending",
        "cloud_backup_url": task.cloud_backup_url,
        "publish_video_url": _publish_video_url(task),
        "seo_ready": task.status == "done" and not task.file_purged,
        "tenant_landing_url": (load_edit_config(task).get("tenant_traffic") or {}).get(
            "landing_url"
        ),
        "edit_config": load_edit_config(task),
        "error_message": task.error_message,
        "mock_render": bool(settings.MEDIA_FACTORY_MOCK_RENDER),
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "started_at": task.started_at.isoformat() if task.started_at else None,
        "finished_at": task.finished_at.isoformat() if task.finished_at else None,
        **retention_payload(task, db),

    }





def list_render_tasks(
    db: Session,
    limit: int = 50,
    *,
    user: User | None = None,
    tenant_id: str | None = None,
) -> list[dict[str, Any]]:
    """list_render_tasks。

    参数说明：
    :param db: 参数 db
    :param limit: 参数 limit
    :param user: 参数 user
    :param tenant_id: 参数 tenant_id
    :return: 返回处理结果。
    """
    query = db.query(MediaRenderTask).order_by(MediaRenderTask.created_at.desc())
    if user is not None:
        if user.role in ("super_admin", "admin"):
            if tenant_id:
                query = query.filter(MediaRenderTask.tenant_id == tenant_id.strip())
        else:
            scope = resolve_tenant_id_for_user(db, user)
            if not scope:
                return []
            query = query.filter(MediaRenderTask.tenant_id == scope)
    elif tenant_id:
        query = query.filter(MediaRenderTask.tenant_id == tenant_id)
    rows = query.limit(limit).all()
    return [serialize_task(row, db) for row in rows]


def tenant_scope_groups_for_tasks(db: Session) -> list[dict[str, Any]]:
    """tenant_scope_groups_for_tasks。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    counts: dict[str, int] = {}
    for (tid,) in db.query(MediaRenderTask.tenant_id).all():
        key = str(tid or "").strip() or "unknown"
        counts[key] = counts.get(key, 0) + 1
    return [
        {"tenant_id": tid, "file_count": count}
        for tid, count in sorted(counts.items(), key=lambda x: (-x[1], x[0]))
    ]


def _dashboard_item_from_task(row: dict[str, Any]) -> dict[str, Any]:
    """_dashboard_item_from_task。

    参数说明：
    :param row: 参数 row
    :return: 返回处理结果。
    """
    src = (
        row.get("preview_url")
        or row.get("publish_video_url")
        or row.get("cloud_play_url")
        or row.get("result_url")
        or ""
    )
    created = row.get("created_at") or ""
    task_type = (row.get("task_type") or "video").strip().lower()
    return {
        "id": row.get("id"),
        "title": row.get("title") or "未命名视频",
        "type": "audio" if task_type == "audio" else "video",
        "src": src,
        "durationLabel": "—",
        "durationSeconds": 0,
        "createdAt": created[:10] if created else "",
        "size": "",
        "tenant_id": row.get("tenant_id"),
        "raw_status": row.get("raw_status"),
        "cloud_upload_status": row.get("cloud_upload_status"),
        "tenant_landing_url": row.get("tenant_landing_url"),
    }


def ingest_uploaded_media_file(
    db: Session,
    user: User,
    *,
    content: bytes,
    original_filename: str,
    content_type: str | None,
    explicit_tenant_id: str | None = None,
    prefer_local_storage: bool = False,
) -> dict[str, Any]:
    """用户直传视频/音频：写入租户隔离云路径并登记渲染任务（已完成）。"""
    ext = original_filename.rsplit(".", 1)[-1].lower() if "." in original_filename else ""
    is_audio = ext in {"mp3", "wav", "m4a", "aac", "ogg"}
    is_video = ext in {"mp4", "webm", "avi", "mov", "mkv", "flv", "wmv"}
    if not is_audio and not is_video:
        raise ValueError(f"不支持的媒体类型 .{ext or '?'}")

    tenant_scope = resolve_tenant_scope(db, user, explicit_tenant_id=explicit_tenant_id)
    meta = store_uploaded_bytes(
        db,
        user,
        content=content,
        original_filename=original_filename,
        content_type=content_type,
        explicit_tenant_id=explicit_tenant_id,
        prefer_local_storage=prefer_local_storage,
    )
    task = MediaRenderTask(
        id=str(uuid.uuid4()),
        title=(original_filename or "上传媒体")[:200],
        task_type="audio" if is_audio else "video",
        script="用户上传",
        status="done",
        progress=100,
        tenant_id=tenant_scope,
        result_url=meta.get("url"),
        file_size_bytes=int(meta.get("size") or len(content)),
        cloud_upload_status="done" if meta.get("storage_backend") not in (None, "local") else "skipped",
        finished_at=datetime.now(timezone.utc),
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return _dashboard_item_from_task(serialize_task(task, db))


def get_render_task_for_user(db: Session, task_id: str, user: User) -> MediaRenderTask | None:
    """get_render_task_for_user。

    参数说明：
    :param db: 参数 db
    :param task_id: 参数 task_id
    :param user: 参数 user
    :return: 返回处理结果。
    """
    task = get_render_task(db, task_id)
    if not task:
        return None
    if user.role in ("super_admin", "admin"):
        return task
    scope = resolve_tenant_id_for_user(db, user)
    if not scope:
        return None
    if str(task.tenant_id or "") != scope:
        return None
    return task


def list_videos_for_dashboard(
    db: Session,
    user: User,
    limit: int = 100,
    *,
    tenant_id: str | None = None,
) -> list[dict[str, Any]]:
    """视频管理中心列表（与 dashboard.vue MediaItem 对齐）。"""
    rows = list_render_tasks(db, limit=limit, user=user, tenant_id=tenant_id)
    return [_dashboard_item_from_task(row) for row in rows]


def media_overview_stats(
    db: Session,
    user: User,
    *,
    tenant_id: str | None = None,
) -> dict[str, Any]:
    """media_overview_stats。

    参数说明：
    :param db: 参数 db
    :param user: 参数 user
    :param tenant_id: 参数 tenant_id
    :return: 返回处理结果。
    """
    tasks = list_render_tasks(db, limit=500, user=user, tenant_id=tenant_id)
    queued = sum(1 for t in tasks if t.get("raw_status") == "queued")
    rendering = sum(1 for t in tasks if t.get("raw_status") == "rendering")
    done = sum(1 for t in tasks if t.get("raw_status") == "done")
    from datetime import date
    today = date.today().isoformat()
    today_done = sum(
        1
        for t in tasks
        if t.get("raw_status") == "done"
        and (t.get("finished_at") or t.get("created_at") or "").startswith(today)
    )
    payload: dict[str, Any] = {
        "rendered_videos": done,
        "queued_videos": queued + rendering,
        "total": done,
        "rendering": rendering,
        "today": today_done,
        "duration": 0,
        "storage": 0,
        "tts_audio_generated": 0,
        "charts_generated": 0,
        "mock_render": settings.MEDIA_FACTORY_MOCK_RENDER,
        "cosmos_base_url": settings.AI_NVIDIA_COSMOS_BASE_URL or "",
        "media_retention_hours": settings.MEDIA_RETENTION_HOURS,
        "media_handoff_delete_hours": settings.MEDIA_HANDOFF_DELETE_HOURS,
    }
    if user.role in ("super_admin", "admin"):
        payload["tenant_scopes"] = tenant_scope_groups_for_tasks(db)
    return payload





def delete_render_task(db: Session, task_id: str) -> bool:
    """delete_render_task。

    参数说明：
    :param db: 参数 db
    :param task_id: 参数 task_id
    :return: 返回处理结果。
    """
    task = get_render_task(db, task_id)
    if not task:

        return False

    if task.status == "rendering":

        raise ValueError("任务正在渲染，无法取消")

    delete_task_file(task)
    if task.edited_result_path and task.edited_result_path != task.result_path:
        extra = MediaRenderTask()
        extra.result_path = task.edited_result_path
        delete_task_file(extra)

    db.delete(task)
    db.commit()
    return True





def clear_done_tasks(db: Session) -> int:
    """clear_done_tasks。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    rows = db.query(MediaRenderTask).filter(MediaRenderTask.status.in_(["done", "expired"])).all()
    count = len(rows)
    for row in rows:

        delete_task_file(row)
        if row.edited_result_path and row.edited_result_path != row.result_path:
            extra = MediaRenderTask()
            extra.result_path = row.edited_result_path
            delete_task_file(extra)

        db.delete(row)

    db.commit()
    return count


