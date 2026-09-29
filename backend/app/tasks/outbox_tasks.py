# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Outbox 周期派发任务 + 首批生产消费者（修正设计稿 模块17 收尾 / Gate G11）。

- dispatch_outbox_events：Celery beat 每 2 分钟调用，领取 pending 事件投递给已注册
  消费者（PG SKIP LOCKED 多实例安全）。
- 首个生产消费者 ops_trail：inquiry.created → contact_events 触点轨迹。
  **消费者契约**：只 `db.add(...)`，绝不 commit/rollback —— 事务由派发器的
  savepoint + 末次 commit 统一管理；消费幂等由派发器的 inbox (consumer, event_id)
  唯一约束保证：重放不会写第二条轨迹。
"""

from __future__ import annotations

import json
import logging

from app.tasks.celery_app import celery_app as task_app

logger = logging.getLogger(__name__)


def _ops_trail_consumer(db, event) -> None:
    """inquiry.created → contact_events 轨迹（派发事务内 add，不 commit）。"""
    from app.models.trade_fulfillment import ContactEvent

    db.add(
        ContactEvent(
            tenant_id=event.tenant_id or None,
            inquiry_id=event.aggregate_id or None,
            channel="outbox",
            event_type="inquiry_created",
            direction="inbound",
            summary=f"outbox 投递：{event.event_type}",
            payload_json=json.dumps(event.payload or {}, ensure_ascii=False, default=str),
        )
    )


def register_production_consumers() -> None:
    """注册生产消费者（幂等：register_consumer 同名覆盖）。"""
    from app.services.outbox_service import register_consumer

    register_consumer("inquiry.created", "ops_trail", _ops_trail_consumer)


@task_app.task(name="app.tasks.outbox_tasks.dispatch_outbox_events", bind=True)
def dispatch_outbox_events(self, batch_size: int = 100) -> dict:  # noqa: ARG001
    """周期派发入口（beat：每 2 分钟；max_instances=1 防堆积）。"""
    import json

    register_production_consumers()
    from app.core.database import SessionLocal
    from app.services.outbox_service import dispatch_pending

    db = SessionLocal()
    try:
        report = dispatch_pending(db, batch_size=batch_size)
        logger.info("outbox dispatch: %s", report)
        return report
    finally:
        db.close()
