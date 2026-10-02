# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Outbox / Inbox / DLQ 单元测试（修正设计稿 模块17 / Gate G11）。

锁定语义：
- record → dispatch 成功链路（published + inbox 登记）；
- 消费幂等：inbox 命中不再调用 handler（重试/重放不产生重复副作用）；
- 失败退避（指数 next_retry_at）+ 超限转死信（dead_letter_events 留档）；
- 无消费者的 event_type 保持 pending —— 不伪造投递成功；
- 死信重放：attempts 清零回 pending；
- 生产者接线：POST /system/contact 事务内写入 inquiry.created 事件。
"""
from __future__ import annotations

import uuid
from datetime import timedelta

import pytest

from app.models.outbox import DeadLetterEvent, InboxEvent, OutboxEvent
from app.services import outbox_service


@pytest.fixture(autouse=True)
def _restore_consumers():
    """每个用例前后恢复消费者注册表，避免测试互相污染。"""
    snapshot = {k: list(v) for k, v in outbox_service._CONSUMERS.items()}
    yield
    outbox_service._CONSUMERS.clear()
    outbox_service._CONSUMERS.update(snapshot)


def _record(db, event_type="test.event", payload=None):
    return outbox_service.record_outbox_event(
        db,
        event_type=event_type,
        # ⚠ 测试库为 sqlite：UUID 列按 NUMERIC 亲和性建表，纯数字 hex 会被转成 REAL，
        # 必须用含字母的 uuid 形态（uuid4 天然含字母，生产 PG 为原生 UUID 不受影响）。
        tenant_id="1a111111-1111-4111-8111-111111111111",
        aggregate_type="demo",
        aggregate_id="agg-1",
        payload=payload or {"k": "v"},
    )


class TestDispatchPublished:
    def test_record_and_dispatch_published(self, db_session):
        seen = []

        def handler(db, event):
            seen.append(event.payload["k"])

        outbox_service.register_consumer("test.event", "unit_consumer", handler)
        _record(db_session)  # 有消费者
        outbox_service.record_outbox_event(  # 无消费者 → 保持 pending
            db_session, event_type="unknown.event", payload={}
        )
        db_session.commit()

        report = outbox_service.dispatch_pending(db_session)

        assert report["claimed"] == 2
        assert report["published"] == 1
        assert report["no_consumer"] == 1
        assert seen == ["v"]

        event = db_session.query(OutboxEvent).filter_by(event_type="test.event").one()
        assert event.status == "published"
        assert event.published_at is not None
        assert event.attempts == 1
        inbox = (
            db_session.query(InboxEvent)
            .filter_by(consumer="unit_consumer", event_id=str(event.id))
            .one()
        )
        assert inbox.result == "ok"

    def test_no_consumer_stays_pending(self, db_session):
        _record(db_session, event_type="never.consumed")
        db_session.commit()

        report = outbox_service.dispatch_pending(db_session)

        assert report["no_consumer"] == 1
        event = db_session.query(OutboxEvent).one()
        assert event.status == "pending"
        # 语义红线：无消费者不伪造投递成功
        assert event.published_at is None


class TestInboxIdempotency:
    def test_inbox_hit_skips_handler(self, db_session):
        calls = []

        def handler(db, event):
            calls.append(event.id)

        outbox_service.register_consumer("test.event", "unit_consumer", handler)
        event = _record(db_session)
        db_session.flush()
        # 预登记：该消费者已处理过此事件（模拟重放场景）
        db_session.add(
            InboxEvent(consumer="unit_consumer", event_id=str(event.id), event_type="test.event")
        )
        db_session.commit()

        report = outbox_service.dispatch_pending(db_session)

        assert report["already_consumed"] == 1
        assert report["published"] == 1
        assert calls == []  # handler 不再被调用 → 无重复副作用


class TestRetryAndDeadLetter:
    def test_failure_backoff_then_dead(self, db_session):
        def always_fail(db, event):
            raise RuntimeError("downstream_down")

        outbox_service.register_consumer("test.event", "bad_consumer", always_fail)
        _record(db_session)
        db_session.commit()

        # sqlite 读回 naive datetime → 测试内统一用 naive 比较
        now = outbox_service._utcnow().replace(tzinfo=None)
        report1 = outbox_service.dispatch_pending(db_session, now=now)
        assert report1["retried"] == 1

        event = db_session.query(OutboxEvent).one()
        assert event.status == "pending"
        assert event.attempts == 1
        assert event.next_retry_at is not None
        assert event.next_retry_at > now
        assert "downstream_down" in (event.last_error or "")

        # 快进到退避点之后，连续重投直至超限
        attempts = 1
        while event.status == "pending" and attempts < 20:
            now = event.next_retry_at + timedelta(seconds=1)
            outbox_service.dispatch_pending(db_session, now=now)
            db_session.refresh(event)
            attempts += 1

        assert event.status == "dead"
        assert event.attempts == outbox_service.DEFAULT_MAX_ATTEMPTS
        dlq = db_session.query(DeadLetterEvent).filter_by(event_id=str(event.id)).one()
        assert dlq.retry_count == outbox_service.DEFAULT_MAX_ATTEMPTS
        assert dlq.reason == "max_attempts_exceeded"
        assert dlq.payload == {"k": "v"}

    def test_requeue_dead_letter_then_succeed(self, db_session):
        state = {"fail": True}

        def flaky(db, event):
            if state["fail"]:
                raise RuntimeError("flaky")

        outbox_service.register_consumer("test.event", "flaky_consumer", flaky)
        event = _record(db_session)
        db_session.commit()

        now = outbox_service._utcnow().replace(tzinfo=None)
        for _ in range(outbox_service.DEFAULT_MAX_ATTEMPTS):
            now = (event.next_retry_at or now) + timedelta(seconds=1) if event.status == "pending" else now
            outbox_service.dispatch_pending(db_session, now=now)
            db_session.refresh(event)

        assert event.status == "dead"

        # 运营修复后重放
        state["fail"] = False
        requeued = outbox_service.requeue_dead_letter(db_session)
        assert requeued == 1
        db_session.refresh(event)
        assert event.status == "pending"
        assert event.attempts == 0

        report = outbox_service.dispatch_pending(db_session)
        assert report["published"] == 1
        assert outbox_service.stats(db_session)["dead_letter_total"] == 1  # DLQ 留档不删


class TestStats:
    def test_stats_counts(self, db_session):
        outbox_service.register_consumer("test.event", "c1", lambda db, e: None)
        _record(db_session)
        _record(db_session, event_type="other.event")
        db_session.commit()
        outbox_service.dispatch_pending(db_session)

        s = outbox_service.stats(db_session)
        assert s["published"] == 1
        assert s["pending"] == 1
        assert s["inbox_total"] == 1
        assert s["dead"] == 0


class TestContactProducerWiring:
    def test_contact_writes_outbox_event_transactional(self, client, db_session):
        """公开联系表单 → 同事务写入 inquiry.created Outbox 事件（模块17 首批接入 Inquiry）。"""
        resp = client.post(
            "/api/v1/system/contact",
            json={
                "name": "Outbox Tester",
                "phone": "+10000000000",
                "email": "ob@test.io",
                "message": "need quote",
            },
            headers={"Authorization": "Bearer test"},  # Bearer 请求豁免 CSRF（仅测 CSRF 层）
        )
        assert resp.status_code == 201
        events = db_session.query(OutboxEvent).filter_by(event_type="inquiry.created").all()
        assert len(events) == 1
        assert events[0].aggregate_type == "inquiry"
        assert events[0].payload["email"] == "ob@test.io"


class TestProductionConsumer:
    def test_beat_task_dispatches_with_ops_trail_consumer(self, monkeypatch, request):
        """T17-b2：beat 任务接线——生产消费者 ops_trail 注册后，派发把事件落到 contact_events。

        beat 任务经独立连接访问测试库，故播种/断言也用落盘会话。
        """
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        from app.models.trade_fulfillment import ContactEvent
        from app.tasks import outbox_tasks

        # P0-3 修订（2026-09-28）：不再复用 conftest 共享文件库——实测存在
        # 「共享临时 .db 运行中途被清理 → 新连接拿到空文件 → no such table」的
        # 组合敏感偶发（长跑触发、短组合不复现，且 create_all 也救不回中途删除）。
        # 本用例改用**私有临时库** + 显式 create_all 所需四表，与其它测试彻底解耦。
        import os as _os
        import tempfile as _tempfile
        from pathlib import Path as _Path

        from app.models import Base as _Base
        from app.models.outbox import (
            DeadLetterEvent as _DLE,
            InboxEvent as _IE,
            OutboxEvent as _OE,
        )

        _fd, _db_path = _tempfile.mkstemp(prefix="uj_outbox_beat_", suffix=".db")
        _os.close(_fd)
        _test_engine = create_engine(
            f"sqlite:///{_Path(_db_path).as_posix()}",
            connect_args={"check_same_thread": False},
        )
        _Base.metadata.create_all(
            _test_engine,
            tables=[_OE.__table__, _IE.__table__, _DLE.__table__, ContactEvent.__table__],
        )
        _TestSession = sessionmaker(bind=_test_engine)
        monkeypatch.setattr("app.core.database.SessionLocal", _TestSession)

        def _cleanup_private_db():
            try:
                _test_engine.dispose()
            except Exception:  # noqa: BLE001
                pass
            try:
                _os.remove(_db_path)
            except OSError:
                pass

        request.addfinalizer(_cleanup_private_db)


        # 播种：落盘会话写入 inquiry.created 事件
        seeded = _TestSession()
        outbox_service.record_outbox_event(
            seeded,
            event_type="inquiry.created",
            tenant_id="5a111111-1111-4111-8111-111111111111",
            aggregate_type="inquiry",
            # ⚠ sqlite UUID 列 NUMERIC 亲和性：纯数字 hex 会被转 REAL（见坑位记录），用含字母 uuid
            aggregate_id="1a111111-2b22-4c33-8d44-e55555555555",
            payload={"email": "trail@test.io"},
        )
        seeded.commit()

        outbox_tasks.register_production_consumers()
        report = outbox_tasks.dispatch_outbox_events.run(batch_size=10)
        assert report["published"] >= 1

        def _trail_count():
            s = _TestSession()
            try:
                return (
                    s.query(ContactEvent)
                    .filter_by(channel="outbox", event_type="inquiry_created")
                    .count()
                )
            finally:
                s.close()

        assert _trail_count() >= 1, "ops_trail 消费者应写 contact_events 轨迹"

        # 幂等：同一事件重放不再产生第二条轨迹（inbox 去重）
        outbox_tasks.dispatch_outbox_events.run(batch_size=10)
        assert _trail_count() >= 1
        s2 = _TestSession()
        try:
            events = (
                s2.query(OutboxEvent)
                .filter_by(event_type="inquiry.created")
                .filter(OutboxEvent.aggregate_id == "1a111111-2b22-4c33-8d44-e55555555555")
                .all()
            )
            assert all(e.status == "published" for e in events)
        finally:
            s2.close()
