"""编排任务消费（ai_tasks → Hermes 桥的 Celery 入口）。

由统一编排摄入路由 POST /orchestration/tasks 派发：create_task → process_ai_task.delay。
本任务在 worker 内打开独立 DB 会话，调用 hermes_task_bridge.dispatch_ai_task 完成
"读任务 → 执行 → 写回"。失败有界重试（≤2），重试时若任务已终态则 dispatch 直接返回，
不会无限重跑（见 hermes_task_bridge 的 TERMINAL_STATUSES 早退）。
"""

from __future__ import annotations

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, name="process_ai_task", max_retries=2, default_retry_delay=30)
def process_ai_task(self, task_id: str):
    """消费一条 ai_tasks，经 Hermes 桥执行并写回结果。"""
    from app.core.database import SessionLocal
    from app.services.tasks.hermes_task_bridge import dispatch_ai_task
    from app.services.tasks.task_control import TaskNotFound

    db = SessionLocal()
    try:
        dispatch_ai_task(db, task_id)
        return {"task_id": task_id, "ok": True}
    except TaskNotFound:
        return {"task_id": task_id, "ok": False, "reason": "not_found"}
    except Exception as exc:  # noqa: BLE001
        logger.exception("process_ai_task failed task=%s", task_id)
        raise self.retry(exc=exc) from exc
    finally:
        db.close()
