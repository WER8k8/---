"""ARQ Worker for publishing tasks."""
import asyncio
import concurrent.futures
from datetime import datetime, timezone
from pathlib import Path
try:
    from arq import create_pool
    from arq.connections import RedisSettings
    from arq.typing import WorkerSettings as ArqWorkerSettings
    ARQ_AVAILABLE = True
except ImportError:
    # arq not available
    create_pool = None
    RedisSettings = None
    ArqWorkerSettings = None
    ARQ_AVAILABLE = False

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def _safe_asyncio_run(coro):
    """安全执行异步协程：兼容已有事件循环（FastAPI）和无事件循环（Celery）。"""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, coro).result()
    return asyncio.run(coro)


def redis_settings():
    """Get Redis settings for ARQ."""
    if not ARQ_AVAILABLE:
        return None
    return RedisSettings(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        password=settings.REDIS_PASSWORD,
        database=settings.REDIS_DB_ARQ,
    )


async def publish_to_platform(ctx: dict, task_id: str, platform_id: str, content: dict) -> dict:
    """Publish content to a platform."""
    from app.services.publish_capability_registry import normalize_publish_result
    from app.services.publish_service import PublishService
    logger.info(f"Starting publish task {task_id} to platform {platform_id}")
    try:
        service = PublishService()
        result = normalize_publish_result(await service.publish(platform_id, content))
        logger.info(f"Publish task {task_id} completed: {result}")
        from app.core.database import SessionLocal
        from app.models.content import PublishTask
        from sqlalchemy import update
        db = SessionLocal()
        try:
            db.execute(
                update(PublishTask)
                .where(PublishTask.id == task_id)
                .values(
                    status=result["status"],
                    published_url=result.get("platform_post_url"),
                    error_message=result.get("error_message"),
                    finished_at=datetime.now(timezone.utc),
                )
            )
            db.commit()
        finally:
            db.close()

        return result

    except Exception as e:
        logger.error(f"Publish task {task_id} failed: {e}", exc_info=True)
        from app.core.database import SessionLocal
        from app.models.content import PublishTask
        from sqlalchemy import update
        db = SessionLocal()
        try:
            db.execute(
                update(PublishTask)
                .where(PublishTask.id == task_id)
                .values(
                    status="failed",
                    error_message=str(e),
                    finished_at=datetime.now(timezone.utc),
                )
            )
            db.commit()
        finally:
            db.close()

        raise


async def retry_failed_publish(ctx: dict, task_id: str) -> dict:
    """Retry a failed publish task."""
    from app.core.database import SessionLocal
    from app.models.content import PublishTask
    from sqlalchemy import select, update
    db = SessionLocal()
    try:
        result = db.execute(select(PublishTask).where(PublishTask.id == task_id))
        task = result.scalar_one_or_none()
        if not task:
            raise ValueError(f"Task {task_id} not found")

        if task.status != "failed":
            raise ValueError(f"Task {task_id} is not in failed status")

        db.execute(
            update(PublishTask)
            .where(PublishTask.id == task_id)
            .values(
                status="pending",
                retry_count=task.retry_count + 1,
                error_message=None,
            )
        )
        db.commit()
        # Re-enqueue via the sync cron consumer (next cycle will pick it up)
        return {"task_id": task_id, "status": "requeued"}
    finally:
        db.close()


if ARQ_AVAILABLE:
    class WorkerSettings:
        """ARQ Worker settings."""
        functions = [publish_to_platform, retry_failed_publish]
        redis_settings = redis_settings
        max_jobs = 10
        job_timeout = 300  # 5 minutes
        keep_result = 3600  # Keep result for 1 hour
        poll_delay = 1  # Poll every 1 second


async def startup(ctx: dict):
    """Worker startup hook."""
    logger.info("Publish worker starting up...")
    ctx["redis"] = await create_pool(redis_settings())


async def shutdown(ctx: dict):
    """Worker shutdown hook."""
    logger.info("Publish worker shutting down...")
    if "redis" in ctx:
        await ctx["redis"].close()


def run_process_pending_tasks(db: "Session", limit: int = 100) -> dict:
    """Sync entry for cron / FastAPI routes."""
    return _safe_asyncio_run(process_pending_tasks(db, limit=limit))


async def process_pending_tasks(db: "Session", limit: int = 100) -> dict:
    """Consume pending publish tasks — 无 MVP 假成功，无失败回退为成功。"""
    from datetime import datetime, timezone
    from app.models.content import GeneratedContent, Platform, PlatformAccount, PublishTask
    from app.models.content_master import ContentMaster
    from app.services.publish_capability_registry import (
        is_publish_result_success,
        publish_block_reason,
    )
    from app.services.publish_dispatch_service import SeoPublishService, _publisher_key
    from app.services.publish_queue_service import recover_stale_processing
    recovered_stale = recover_stale_processing(db)
    now = datetime.now(timezone.utc)
    rows = (
        db.query(PublishTask)
        .filter(PublishTask.status == "pending")
        .filter(
            (PublishTask.scheduled_time.is_(None))
            | (PublishTask.scheduled_time <= now)
        )
        .order_by(PublishTask.created_at.asc())
        .limit(limit)
        .all()
    )
    processed = success = failed = 0
    svc = SeoPublishService(db)
    for task in rows:
        processed += 1
        task.status = "processing"
        task.updated_at = now
        db.flush()
        try:
            outcome = _process_single_publish_task(db, task, svc, now)
            if outcome == "success":
                success += 1
            else:
                failed += 1
        except Exception as exc:
            logger.exception("publish task %s failed", task.id)
            task.status = "failed"
            task.error_message = str(exc)[:500]
            failed += 1

    if processed:
        db.commit()

    return {
        "processed": processed,
        "success": success,
        "failed": failed,
        "recovered_stale": recovered_stale,
        "recovered_errors": 0,
    }


def _process_single_publish_task(db, task, svc, now: datetime) -> str:
    """处理单个 pending 发布任务，直接修改 task 状态，返回 "success" 或 "failed"。"""
    from datetime import datetime
    from app.models.content import GeneratedContent, Platform, PlatformAccount, PublishTask
    from app.models.content_master import ContentMaster
    from app.services.publish_capability_registry import (
        is_publish_result_success,
        publish_block_reason,
    )
    from app.services.publish_dispatch_service import SeoPublishService, _publisher_key
    from app.services.seo.seo_utm_service import append_publish_utm
    plat = db.query(Platform).filter(Platform.id == task.platform_id).first()
    account = db.query(PlatformAccount).filter(PlatformAccount.id == task.account_id).first()
    if not plat or not account:
        task.status = "failed"
        task.error_message = "平台或账号不存在"
        return "failed"

    gc: GeneratedContent | None = None
    if task.content_id:
        gc = db.query(GeneratedContent).filter(GeneratedContent.id == task.content_id).first()
    elif task.content_master_id:
        master = db.query(ContentMaster).filter(ContentMaster.id == task.content_master_id).first()
        if master:
            gc = GeneratedContent(
                title=master.title or "发布内容",
                content=master.body or "",
                word_count=len(master.body or ""),
                status="draft",
            )

    if gc is None:
        task.status = "failed"
        task.error_message = (
            "发布任务缺少正文内容；禁止用 primary_url 冒充平台作品链接"
        )
        return "failed"

    blocked = publish_block_reason(
        platform_name=plat.name,
        publisher_key=_publisher_key(plat),
        content={
            "title": gc.title or "",
            "body": gc.content or "",
            "content": gc.content or "",
        },
    )
    if blocked:
        task.status = "failed"
        task.error_message = blocked[:500]
        return "failed"

    post_url = svc._dispatch_to_platform(plat, account, gc)
    if not is_publish_result_success({"platform_post_url": post_url}):
        task.status = "failed"
        task.error_message = "发布未返回可验证作品链接（禁止假成功）"
        return "failed"

    task.status = "success"
    task.published_at = now
    plat_code = getattr(plat, "code", None) or getattr(plat, "name", None)
    task.published_url = append_publish_utm(
        post_url,
        platform_code=str(plat_code) if plat_code else None,
        task_id=str(task.id),
        tenant_id=str(getattr(account, "tenant_id", "") or "") or None,
    )
    task.error_message = None
    return "success"
