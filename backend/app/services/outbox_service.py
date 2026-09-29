# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Outbox 派发服务 —— 统一消息可靠性层的进程内参考实现（修正设计稿 模块17 / Gate G11）。

职责：
- record_outbox_event(db, ...)：业务事务内追加写事件（不 commit —— 与业务同事务提交/回滚）。
- register_consumer(event_type, consumer_name, handler)：注册消费者；
  handler 签名 `handler(db, event) -> None`，**handler 内禁止 commit/rollback**（由派发器统一管理）。
- dispatch_pending(db, ...)：领取到期 pending 事件，逐个投递给已注册消费者；
  PG 上 `FOR UPDATE SKIP LOCKED` 多 worker 安全；消费以 inbox (consumer, event_id) 幂等去重；
  成功 → published；失败按指数退避重投；超过 max_attempts 转入 dead_letter_events。
- requeue_dead_letter(db, ...)：死信运营重放入口（attempts 清零回 pending，DLQ 行留档）。
- stats(db)：状态计数（供运维面 /ops 后续暴露）。

语义红线：
- 无注册消费者的 event_type **保持 pending** —— 不伪造投递成功（NoFakeDelivery 同纪律）；
- 已被消费过的事件（inbox 命中）不再调用 handler，直接判 published；
- 消费者异常只回滚自身 savepoint，不影响同批其它事件。

Celery 接线：`app.tasks.outbox_tasks` 提供 beat 周期 dispatch（本模块保持无 Celery 依赖可单测）。
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Optional

from sqlalchemy import func, or_

from app.models.outbox import DeadLetterEvent, InboxEvent, OutboxEvent

logger = logging.getLogger(__name__)

# handler 类型：handler(db, event) -> None（内部禁止 commit/rollback）
ConsumerHandler = Callable[[Any, OutboxEvent], None]

_CONSUMERS: dict[str, list[tuple[str, ConsumerHandler]]] = {}

DEFAULT_MAX_ATTEMPTS = 5


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _backoff_seconds(attempts: int) -> int:
    """指数退避：1 次=60s，2 次=120s … 上限 30 分钟。"""
    return min(60 * (2 ** max(0, attempts - 1)), 1800)


# ── 生产者侧 ─────────────────────────────────────────────────


def record_outbox_event(
    db,
    *,
    event_type: str,
    tenant_id: Optional[str] = None,
    aggregate_type: Optional[str] = None,
    aggregate_id: Optional[str] = None,
    payload: Optional[dict] = None,
) -> OutboxEvent:
    """业务事务内追加写事件。**不 commit** —— 由业务方与其业务写入同事务提交/回滚。"""
    event = OutboxEvent(
        tenant_id=str(tenant_id) if tenant_id else None,
        event_type=event_type,
        aggregate_type=aggregate_type,
        aggregate_id=str(aggregate_id) if aggregate_id is not None else None,
        payload=payload or {},
        status="pending",
    )
    db.add(event)
    return event


# ── 消费者侧 ─────────────────────────────────────────────────


def register_consumer(event_type: str, consumer_name: str, handler: ConsumerHandler) -> None:
    """注册消费者。同名重复注册以最后一次为准（便于测试/热更）。"""
    consumers = _CONSUMERS.setdefault(event_type, [])
    consumers[:] = [(name, h) for name, h in consumers if name != consumer_name]
    consumers.append((consumer_name, handler))
    logger.info("outbox consumer registered: %s -> %s", event_type, consumer_name)


def get_consumers(event_type: str) -> list[tuple[str, ConsumerHandler]]:
    return list(_CONSUMERS.get(event_type) or [])


def already_processed(db, *, consumer: str, event_id: str) -> bool:
    return (
        db.query(InboxEvent.id)
        .filter(InboxEvent.consumer == consumer, InboxEvent.event_id == str(event_id))
        .first()
        is not None
    )


# ── 派发器 ───────────────────────────────────────────────────


def dispatch_pending(
    db,
    *,
    batch_size: int = 50,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    now: Optional[datetime] = None,
) -> dict[str, int]:
    """领取并投递到期事件。返回计数报告（含 no_consumer —— 不伪造成功）。"""
    now = now or _utcnow()
    claimed = (
        db.query(OutboxEvent)
        .filter(OutboxEvent.status == "pending")
        .filter(or_(OutboxEvent.next_retry_at.is_(None), OutboxEvent.next_retry_at <= now))
        .order_by(OutboxEvent.created_at.asc())
        .limit(batch_size)
        .with_for_update(skip_locked=True)
        .all()
    )

    report: dict[str, int] = {
        "claimed": len(claimed),
        "published": 0,
        "retried": 0,
        "dead": 0,
        "no_consumer": 0,
        "already_consumed": 0,
    }

    for event in claimed:
        consumers = get_consumers(event.event_type)
        if not consumers:
            # 保留 pending：等消费者注册后由下一次 dispatch 处理
            report["no_consumer"] += 1
            continue

        event.status = "processing"
        error: Optional[str] = None
        for consumer_name, handler in consumers:
            if already_processed(db, consumer=consumer_name, event_id=str(event.id)):
                report["already_consumed"] += 1
                continue
            savepoint = db.begin_nested()
            try:
                handler(db, event)
                db.add(
                    InboxEvent(
                        consumer=consumer_name,
                        event_id=str(event.id),
                        event_type=event.event_type,
                        result="ok",
                    )
                )
                savepoint.commit()
            except Exception as exc:  # noqa: BLE001 —— 单消费者失败不拖垮整批
                savepoint.rollback()
                logger.warning(
                    "outbox consumer failed: event=%s consumer=%s err=%s",
                    event.id, consumer_name, exc,
                )
                error = f"{consumer_name}: {exc}"
                break

        if error is None:
            event.status = "published"
            event.published_at = now
            event.attempts = (event.attempts or 0) + 1
            event.last_error = None
            report["published"] += 1
        else:
            event.attempts = (event.attempts or 0) + 1
            event.last_error = error
            if event.attempts >= max_attempts:
                event.status = "dead"
                db.add(
                    DeadLetterEvent(
                        event_id=str(event.id),
                        event_type=event.event_type,
                        tenant_id=event.tenant_id,
                        reason="max_attempts_exceeded",
                        payload=event.payload,
                        last_error=error,
                        retry_count=event.attempts,
                    )
                )
                report["dead"] += 1
            else:
                event.status = "pending"
                event.next_retry_at = now + timedelta(seconds=_backoff_seconds(event.attempts))
                report["retried"] += 1

    db.commit()
    return report


def requeue_dead_letter(db, *, event_id: Optional[str] = None, limit: int = 50) -> int:
    """死信重放：清零 attempts 回 pending（DLQ 行留作审计历史，不删）。"""
    query = db.query(DeadLetterEvent)
    if event_id:
        query = query.filter(DeadLetterEvent.event_id == str(event_id))
    rows = query.order_by(DeadLetterEvent.created_at.asc()).limit(limit).all()
    requeued = 0
    for row in rows:
        event = db.query(OutboxEvent).filter(OutboxEvent.id == row.event_id).first()
        if event and event.status == "dead":
            event.status = "pending"
            event.attempts = 0
            event.next_retry_at = None
            event.last_error = None
            requeued += 1
    db.commit()
    return requeued


def stats(db) -> dict[str, int]:
    """outbox 状态计数 + inbox/死信总量（运维只读）。"""
    rows = (
        db.query(OutboxEvent.status, func.count(OutboxEvent.id))
        .group_by(OutboxEvent.status)
        .all()
    )
    by_status = {status: count for status, count in rows}
    return {
        "pending": by_status.get("pending", 0),
        "processing": by_status.get("processing", 0),
        "published": by_status.get("published", 0),
        "dead": by_status.get("dead", 0),
        "inbox_total": db.query(func.count(InboxEvent.id)).scalar() or 0,
        "dead_letter_total": db.query(func.count(DeadLetterEvent.id)).scalar() or 0,
    }
