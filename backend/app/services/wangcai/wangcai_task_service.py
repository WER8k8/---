# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Wangcai ask -> unified ai_task entry (H.5: 旺财接入 Hermes 任务面).

公开旺财端点保持响应契约不变，但执行改走与 UBrain（H.3）相同的
ai_task 任务面：create_task → Celery/Hermes 桥派发 → 读回终态。
除 Hermes 外不再保留第二个旺财路由入口。
"""

from __future__ import annotations

import json
import logging
from typing import Any

from sqlalchemy.orm import Session

from app.models.ai_task import AiTask
from app.services.tasks.task_control import TaskControlService

logger = logging.getLogger(__name__)


class WangcaiChatTaskError(RuntimeError):
    """Raised when a Wangcai chat cannot be executed through the task plane."""

    def __init__(self, message: str, task: AiTask | None = None):
        super().__init__(message)
        self.task = task


def run_wangcai_task(
    db: Session,
    *,
    tenant_id: str,
    message: str,
    source: str = "public_site",
    product_hint: str | None = None,
    language: str | None = None,
    user_id: str | None = None,
    timeout: int = 30,
) -> tuple[AiTask, dict[str, Any]]:
    """Create one ai_task, dispatch it through Celery/Hermes, and read it back.

    The public Wangcai endpoint keeps its response contract, but execution now
    has the same task plane and traceability as the other Hermes entry points.
    """
    ctl = TaskControlService(db)
    task = ctl.create_task(
        tenant_id=str(tenant_id),
        task_type="wangcai_intent",
        input_data={
            "message": message,
            "source": source,
            "product_hint": product_hint,
            "language": language,
        },
        source="wangcai_chat",
        created_by=str(user_id) if user_id else None,
    )
    task_id = str(task.id)

    try:
        from app.tasks.orchestration_tasks import process_ai_task

        process_ai_task.delay(task_id).get(timeout=timeout)
    except Exception as exc:  # noqa: BLE001 - keep the chat API usable
        logger.warning("Wangcai Celery dispatch unavailable, using Hermes bridge directly: %s", exc)
        from app.services.tasks.hermes_task_bridge import dispatch_ai_task

        dispatch_ai_task(db, task_id)

    db.expire_all()
    refreshed = ctl.get_task(task_id, tenant_id=str(tenant_id))
    if refreshed is None:
        raise WangcaiChatTaskError(f"wangcai_task_not_found: {task_id}", task=task)
    if refreshed.status != "done":
        raise WangcaiChatTaskError(
            refreshed.error_message or f"wangcai_task_status={refreshed.status}",
            task=refreshed,
        )
    try:
        output = json.loads(refreshed.output_json or "{}")
    except json.JSONDecodeError as exc:
        raise WangcaiChatTaskError(f"wangcai_task_output_invalid: {exc}", task=refreshed) from exc
    if not isinstance(output, dict):
        raise WangcaiChatTaskError(
            f"wangcai_task_output_type={type(output).__name__}", task=refreshed
        )
    return refreshed, output
