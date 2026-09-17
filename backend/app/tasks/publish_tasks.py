# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Publish task definitions and enqueue functions."""
import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from arq import create_pool
from arq.connections import RedisSettings
from arq.typing import WorkerSettings

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def get_redis_settings() -> RedisSettings:
    """Get Redis settings for ARQ."""
    return RedisSettings(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        password=settings.REDIS_PASSWORD,
        database=settings.REDIS_DB_ARQ,
    )


async def enqueue_publish_task(
    redis, task_id: str, platform_id: str, content: Dict[str, Any]
) -> str:
    """Enqueue a publish task to ARQ.

    Args:
        redis: Redis connection from ARQ ctx.
        task_id: Publish task ID.
        platform_id: Platform ID (e.g., 'facebook').
        content: Content data dict.

    Returns:
        str: ARQ job ID.
    """
    from arq.utils import timestamp_ms
    job = await redis.enqueue_job(
        "publish_to_platform",
        task_id,
        platform_id,
        content,
        _job_id=f"publish_{task_id}_{timestamp_ms()}",
        _defer_by=0,  # Execute immediately
    )
    logger.info(f"Enqueued publish task {task_id} for platform {platform_id}, job_id={job.job_id}")
    return job.job_id


async def enqueue_retry_publish(redis, task_id: str) -> str:
    """Enqueue a retry for a failed publish task.

    Args:
        redis: Redis connection.
        task_id: Failed publish task ID.

    Returns:
        str: ARQ job ID.
    """
    from arq.utils import timestamp_ms
    job = await redis.enqueue_job(
        "retry_failed_publish",
        task_id,
        _job_id=f"retry_{task_id}_{timestamp_ms()}",
        _defer_by=60,  # Retry after 60 seconds
    )
    logger.info(f"Enqueued retry for task {task_id}, job_id={job.job_id}")
    return job.job_id


async def get_task_result(redis, job_id: str) -> Optional[Dict]:
    """Get the result of an ARQ job.

    Args:
        redis: Redis connection.
        job_id: ARQ job ID.

    Returns:
        dict or None: Job result if available.
    """
    result = await redis.get(f"arq:result:{job_id}")
    if result:
        import json
        return json.loads(result)
    return None


async def cancel_task(redis, job_id: str) -> bool:
    """Cancel a pending ARQ job.

    Args:
        redis: Redis connection.
        job_id: ARQ job ID.

    Returns:
        bool: True if job was cancelled.
    """
    return await redis.cancel_job(job_id)


async def get_queue_stats(redis) -> Dict[str, int]:
    """Get ARQ queue statistics.

    Returns:
        dict: Queue stats (queued, in_progress, complete, failed).
    """
    queued = await redis.zcard("arq:queue")
    in_progress = await redis.zcard("arq:in_progress")
    complete = await redis.zcard("arq:complete")
    failed = await redis.zcard("arq:failed")
    return {
        "queued": queued,
        "in_progress": in_progress,
        "complete": complete,
        "failed": failed,
    }
