"""渲染完成后异步上云：酷播（国内播放）+ R2（海外发布）。"""

from __future__ import annotations

import logging
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.media_factory import MediaRenderTask
from app.services.media_cuplayer_service import (
    CuplayerUploadError,
    cuplayer_configured,
    upload_video_file as upload_cuplayer,
)
from app.services.media_lenslink_service import (
    MediaLenslinkError,
    lenslink_configured,
    upload_video_backup,
)
from app.services.media_r2_service import (
    MediaR2Error,
    object_key_for_task,
    presigned_get_url,
    r2_configured,
    upload_file_to_r2,
)
logger = logging.getLogger(__name__)


def _get_task(db: Session, task_id: str) -> MediaRenderTask | None:
    """_get_task。

    参数说明：
    :param db: 参数 db
    :param task_id: 参数 task_id
    :return: 返回处理结果。
    """
    return db.query(MediaRenderTask).filter(MediaRenderTask.id == task_id).first()


def cloud_upload_enabled() -> bool:
    """cloud_upload_enabled。
    :return: 返回处理结果。
    """
    return bool(getattr(settings, "MEDIA_CLOUD_UPLOAD_ENABLED", True))


def playback_url_for_task(task: MediaRenderTask) -> str | None:
    """对外播放优先：酷播 CDN > R2 > 本地。"""
    if task.file_purged:
        return None
    primary = (settings.MEDIA_CLOUD_PLAY_PRIMARY or "cuplayer").lower()
    if primary == "cuplayer" and task.cloud_play_url:
        return task.cloud_play_url
    if task.cloud_r2_key:
        try:
            return presigned_get_url(task.cloud_r2_key)
        except MediaR2Error:
            return task.cloud_r2_url
    if task.cloud_play_url:
        return task.cloud_play_url
    if task.cloud_r2_url:
        return task.cloud_r2_url
    return task.edited_result_url or task.result_url or None


def overseas_publish_video_url(task: MediaRenderTask) -> str | None:
    """海外发布（YouTube 等）拉取用 URL。"""
    if task.cloud_r2_key:
        try:
            return presigned_get_url(task.cloud_r2_key)
        except MediaR2Error:
            pass
    return task.cloud_r2_url or task.cloud_play_url or task.cloud_backup_url


def _upload_with_one_retry(
    label: str,
    exc_type: type[Exception],
    upload_fn,
) -> dict[str, str] | None:
    """_upload_with_one_retry。

    参数说明：
    :param label: 参数 label
    :param exc_type: 参数 exc_type
    :param upload_fn: 参数 upload_fn
    :return: 返回处理结果。
    """
    for attempt in range(2):
        try:
            return upload_fn()
        except exc_type as exc:
            if attempt == 0:
                logger.warning("%s upload failed, retrying: %s", label, exc)
                continue
            logger.warning("%s upload failed: %s", label, exc)
            return {"error": str(exc)}
    return None


def _upload_cuplayer_safe(path: Path, title: str) -> dict[str, str] | None:
    """_upload_cuplayer_safe。

    参数说明：
    :param path: 参数 path
    :param title: 参数 title
    :return: 返回处理结果。
    """
    if not cuplayer_configured():
        return None
    return _upload_with_one_retry(
        "Cuplayer",
        CuplayerUploadError,
        lambda: upload_cuplayer(path, title=title),
    )


def _upload_r2_safe(path: Path, task_id: str, tenant_id: str | None) -> dict[str, str] | None:
    """_upload_r2_safe。

    参数说明：
    :param path: 参数 path
    :param task_id: 参数 task_id
    :param tenant_id: 参数 tenant_id
    :return: 返回处理结果。
    """
    if not r2_configured():
        return None
    key = object_key_for_task(task_id, tenant_id)
    def _do() -> dict[str, str]:
        """_do。
        :return: 返回处理结果。
        """
        upload_file_to_r2(path, key)
        return {"key": key, "url": presigned_get_url(key)}

    return _upload_with_one_retry("R2", MediaR2Error, _do)


def _upload_lenslink_safe(path: Path, task_id: str, tenant_id: str | None) -> dict[str, str] | None:
    """_upload_lenslink_safe。

    参数说明：
    :param path: 参数 path
    :param task_id: 参数 task_id
    :param tenant_id: 参数 tenant_id
    :return: 返回处理结果。
    """
    if not lenslink_configured():
        return None
    return _upload_with_one_retry(
        "Lenslink",
        MediaLenslinkError,
        lambda: upload_video_backup(path, task_id, tenant_id),
    )


def _mark_skipped(db: Session, task: MediaRenderTask) -> None:
    """将任务上云状态标记为 skipped 并落库。"""
    task.cloud_upload_status = "skipped"
    db.add(task)
    db.commit()


def _submit_cloud_uploads(pool: ThreadPoolExecutor, path: Path, task: MediaRenderTask) -> dict[Any, str]:
    """按可用通道提交酷播/R2/Lenslink 上传，返回 future→通道名映射。"""
    futures: dict[Any, str] = {}
    if cuplayer_configured():
        futures[pool.submit(_upload_cuplayer_safe, path, task.title)] = "cuplayer"
    if r2_configured():
        futures[pool.submit(_upload_r2_safe, path, task.id, task.tenant_id)] = "r2"
    if lenslink_configured():
        futures[pool.submit(_upload_lenslink_safe, path, task.id, task.tenant_id)] = "lenslink"
    return futures


def _collect_upload_results(futures: dict[Any, str]) -> tuple[dict[str, Any] | None, dict[str, Any] | None, dict[str, Any] | None]:
    """等全部上传完成，按通道分类收集结果 (cu_result, r2_result, lens_result)。"""
    cu_result: dict[str, Any] | None = None
    r2_result: dict[str, Any] | None = None
    lens_result: dict[str, Any] | None = None
    for fut in as_completed(futures):
        kind = futures[fut]
        try:
            res = fut.result()
        except Exception as exc:
            logger.exception("Cloud upload worker error (%s)", kind)
            res = {"error": str(exc)}
        if kind == "cuplayer":
            cu_result = res
        elif kind == "r2":
            r2_result = res
        else:
            lens_result = res
    return (cu_result, r2_result, lens_result)


def _apply_upload_results(
    task: MediaRenderTask,
    cu_result: dict[str, Any] | None,
    r2_result: dict[str, Any] | None,
    lens_result: dict[str, Any] | None,
) -> None:
    """按各通道结果回写任务字段并计算最终云状态。"""
    ok_cu = bool(
        cu_result
        and not cu_result.get("error")
        and (cu_result.get("vid") or cu_result.get("play_url"))
    )
    ok_r2 = bool(r2_result and not r2_result.get("error") and r2_result.get("key"))
    ok_lens = bool(lens_result and not lens_result.get("error") and lens_result.get("url"))
    if ok_lens:
        task.cloud_backup_url = lens_result.get("url")

    if ok_cu:
        task.cloud_vid = cu_result.get("vid") or task.cloud_vid
        task.cloud_play_url = cu_result.get("play_url") or task.cloud_play_url
        if not task.cloud_provider:
            task.cloud_provider = "cuplayer"

    if ok_r2:
        task.cloud_r2_key = r2_result["key"]
        task.cloud_r2_url = r2_result.get("url")
        if not task.cloud_provider:
            task.cloud_provider = "r2"
        elif task.cloud_provider == "cuplayer" and ok_cu:
            task.cloud_provider = "cuplayer"

    if ok_cu and ok_r2:
        task.cloud_upload_status = "done"
    elif ok_cu or ok_r2:
        task.cloud_upload_status = "partial"
    elif ok_lens:
        task.cloud_upload_status = "partial"
        if not task.cloud_provider:
            task.cloud_provider = "lenslink"
    else:
        task.cloud_upload_status = "failed"


def _publish_to_tenant_site(db: Session, task: MediaRenderTask) -> None:
    """任务完成后自动把视频发布到租户站点（异常仅告警不抛出）。"""
    if not task.tenant_id or not getattr(settings, "MEDIA_AUTO_PUBLISH_TENANT_SITE", True):
        return
    if task.cloud_upload_status not in ("done", "partial", "skipped"):
        return
    try:
        from app.services.media_tenant_traffic_service import (
            get_tenant,
            publish_video_to_tenant_site,
        )
        tenant = get_tenant(db, task.tenant_id)
        if tenant:
            publish_video_to_tenant_site(db, task, tenant)
    except Exception as exc:
        logger.warning("Tenant video landing publish failed for %s: %s", task.id, exc)


def sync_cloud_upload(db: Session, task_id: str) -> MediaRenderTask | None:
    """同步执行上云（供后台线程调用）。"""
    task = _get_task(db, task_id)
    if not task or task.status != "done":
        return task

    if not cloud_upload_enabled():
        _mark_skipped(db, task)
        return task

    path_str = task.edited_result_path or task.result_path
    if not path_str:
        return task
    path = Path(path_str)
    if not path.is_file():
        return task

    if not cuplayer_configured() and not r2_configured() and not lenslink_configured():
        _mark_skipped(db, task)
        return task

    task.cloud_upload_status = "uploading"
    db.add(task)
    db.commit()
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = _submit_cloud_uploads(pool, path, task)
        cu_result, r2_result, lens_result = _collect_upload_results(futures)

    _apply_upload_results(task, cu_result, r2_result, lens_result)
    db.add(task)
    db.commit()
    db.refresh(task)
    _publish_to_tenant_site(db, task)
    return task


def run_cloud_upload_background(task_id: str) -> None:
    """非阻塞：渲染 API 立即返回，上云在守护线程完成。"""
    def _worker() -> None:
        """_worker。
        :return: 返回处理结果。
        """
        db = SessionLocal()
        try:
            sync_cloud_upload(db, task_id)
        except Exception as exc:
            logger.exception("Background cloud upload failed for %s: %s", task_id, exc)
        finally:
            db.close()

    threading.Thread(target=_worker, name=f"cloud-upload-{task_id[:8]}", daemon=True).start()