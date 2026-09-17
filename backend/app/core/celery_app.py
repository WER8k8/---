# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Celery 异步任务队列 — FIX-43

提供 Celery 集成配置和多队列支持：
- 高优先级队列（email, lead_verification）
- 默认队列（scoring, enrichment）
- 低优先级队列（cleanup, reporting）

支持 Redis 和 RabbitMQ 两种 broker。
"""

from __future__ import annotations

import logging
import os
from typing import Any, Optional

log = logging.getLogger(__name__)

# Celery 配置
CELERY_CONFIG = {
    "broker_url": os.getenv("CELERY_BROKER_URL", "redis://127.0.0.1:6379/1"),
    "result_backend": os.getenv("CELERY_RESULT_BACKEND", "redis://127.0.0.1:6379/2"),
    "task_serializer": "json",
    "result_serializer": "json",
    "accept_content": ["json"],
    "timezone": "Asia/Shanghai",
    "enable_utc": True,
    "task_track_started": True,
    "task_time_limit": 300,          # 5分钟超时
    "task_soft_time_limit": 240,     # 4分钟软超时
    "worker_max_tasks_per_child": 100,
    "worker_prefetch_multiplier": 1,
    "result_expires": 3600,          # 结果1小时过期
    # 多队列路由
    "task_routes": {
        "app.tasks.email.*": {"queue": "email"},
        "app.tasks.lead_verification.*": {"queue": "lead_verify"},
        "app.tasks.scoring.*": {"queue": "scoring"},
        "app.tasks.enrichment.*": {"queue": "enrichment"},
        "app.tasks.cleanup.*": {"queue": "cleanup"},
        "app.tasks.reporting.*": {"queue": "reporting"},
        "app.tasks.*": {"queue": "default"},
    },
    # 队列定义
    "task_queues": {
        "email": {"exchange": "email", "routing_key": "email"},
        "lead_verify": {"exchange": "lead_verify", "routing_key": "lead_verify"},
        "scoring": {"exchange": "scoring", "routing_key": "scoring"},
        "enrichment": {"exchange": "enrichment", "routing_key": "enrichment"},
        "cleanup": {"exchange": "cleanup", "routing_key": "cleanup"},
        "reporting": {"exchange": "reporting", "routing_key": "reporting"},
        "default": {"exchange": "default", "routing_key": "default"},
    },
    # 定时任务调度 (改造 5: APScheduler 向 Celery Beat 迁移预留点)
    "beat_schedule": {
        # 示例：每天凌晨执行日志清理
        "daily-cleanup": {
            "task": "app.core.celery_app.cleanup_logs",
            "schedule": 86400.0,  # 每天一次
            "options": {"queue": "cleanup"}
        },
    }
}


# 异步任务回退：当 Celery 不可用时，使用 asyncio 执行
class AsyncTaskFallback:
    """异步任务回退机制。

    当 Celery broker 不可用时，自动降级为 asyncio 任务。
    """
    _celery_available: Optional[bool] = None
    @classmethod
    async def is_celery_available(cls) -> bool:
        """检查 Celery 是否可用。"""
        if cls._celery_available is not None:
            return cls._celery_available

        try:
            import redis
            r = redis.Redis.from_url(CELERY_CONFIG["broker_url"])
            r.ping()
            cls._celery_available = True
        except Exception:
            cls._celery_available = False
            log.warning("Celery broker 不可用，将使用 asyncio 回退")

        return cls._celery_available

    @classmethod
    async def run_task(
        cls,
        task_func: callable,
        *args,
        queue: str = "default",
        **kwargs,
    ) -> Any:
        """执行任务（自动选择 Celery 或 asyncio）。"""
        if await cls.is_celery_available():
            return await cls._run_celery(task_func, *args, queue=queue, **kwargs)
        return await cls._run_async(task_func, *args, **kwargs)

    @classmethod
    async def _run_celery(cls, task_func, *args, queue: str = "default", **kwargs):
        """通过 Celery 执行。"""
        try:
            from celery import Celery
            from celery.result import AsyncResult
            app = Celery("uj-admin")
            app.config_from_object(CELERY_CONFIG)
            result = task_func.apply_async(
                args=args,
                kwargs=kwargs,
                queue=queue,
            )
            return result.id
        except Exception as e:
            log.warning("Celery 执行失败，回退到 asyncio: %s", e)
            return await cls._run_async(task_func, *args, **kwargs)

    @classmethod
    async def _run_async(cls, task_func, *args, **kwargs):
        """通过 asyncio 执行。"""
        import asyncio
        if asyncio.iscoroutinefunction(task_func):
            return await task_func(*args, **kwargs)
        else:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, task_func, *args, **kwargs)


# ============================================================
# 任务定义
# ============================================================

async def send_email_task(
    to_email: str,
    subject: str,
    body: str,
    from_name: Optional[str] = None,
) -> dict:
    """邮件发送任务。"""
    from app.services.ubrain.email_send_service import EmailSendService
    service = EmailSendService()
    return await service.send(
        to_email=to_email,
        subject=subject,
        body=body,
        from_name=from_name,
    )


async def verify_email_task(email: str) -> dict:
    """邮箱验证任务。"""
    from app.services.ubrain.email_verification_service import EmailVerificationService
    service = EmailVerificationService()
    return await service.verify(email)


async def score_lead_task(lead_data: dict) -> dict:
    """线索评分任务。"""
    from app.services.ubrain.lead_scoring_engine import score_lead
    return await score_lead(lead_data)


async def process_lead_task(raw_data: dict) -> dict:
    """线索处理 Pipeline 任务。"""
    from app.services.ubrain.lead_processing_pipeline import LeadPipeline
    pipeline = LeadPipeline.create_default()
    ctx = await pipeline.process(raw_data)
    return {
        "lead_id": ctx.id,
        "status": ctx.status.value,
        "score": ctx.score,
        "is_duplicate": ctx.is_duplicate,
    }


async def cleanup_old_logs_task(days: int = 30) -> dict:
    """日志清理任务。"""
    from app.core.config import settings
    import glob
    log_dir = settings.LOG_DIR or "./logs"
    deleted = 0
    try:
        import time
        cutoff = time.time() - days * 86400
        for log_file in glob.glob(f"{log_dir}/*.log*"):
            if os.path.getmtime(log_file) < cutoff:
                os.remove(log_file)
                deleted += 1
    except Exception as e:
        log.error("日志清理失败: %s", e)

    return {"deleted": deleted, "days": days}


# ============================================================
# Celery App 延迟初始化
# ============================================================

def create_celery_app() -> Optional[Any]:
    """创建 Celery 应用实例（延迟初始化）。"""
    try:
        from celery import Celery
        app = Celery("uj-admin")
        app.config_from_object(CELERY_CONFIG)
        # 自动发现任务
        app.autodiscover_tasks(["app.tasks"], force=True)
        log.info("Celery 应用初始化成功")
        return app
    except Exception as e:
        log.warning("Celery 初始化失败: %s", e)
        return None


# 启动 Celery worker 的命令参考
CELERY_START_COMMAND = """
# 启动多队列 worker（生产环境推荐）:
celery -A app.core.celery_app worker \\
  -Q email,lead_verify,scoring,enrichment,default \\
  -c 4 \\
  -l info \\
  --pool=prefork

# 各队列独立 worker（更高并发）:
celery -A app.core.celery_app worker -Q email -c 2 -l info -n email_worker &
celery -A app.core.celery_app worker -Q lead_verify -c 2 -l info -n verify_worker &
celery -A app.core.celery_app worker -Q scoring -c 1 -l info -n scoring_worker &
celery -A app.core.celery_app worker -Q default -c 2 -l info -n default_worker &
"""