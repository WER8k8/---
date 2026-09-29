# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""模块7 · TradeAI 序列停机条件（T7-b）配对反证测试。

判据（设计稿）：positive reply → stop；unsubscribe → suppression + 停序；
bounce → 可联性降级；manual stop → 不可自动重启。
suppression_store 用进程内桩（隔离开发库，wiring 正确性为本测试目标）。
"""
from __future__ import annotations

import uuid
from typing import Any

import pytest

from app.models.email_outreach import BounceType, EmailOutreach, EmailStatus
from app.services import acquisition_outreach_service as aos
from app.services.tradeai.native_acquisition import classify_inbox
from app.services.ubrain.email_outreach_service import record_bounce

TENANT = "6d555555-5555-4555-8555-555555555555"


class _StubSuppression:
    """进程内 suppression 桩：记录 add 调用；可编程 check_outreach 结果。"""

    def __init__(self, *, allow: bool = True):
        self.allow = allow
        self.added: list[dict[str, Any]] = []

    def add(self, *, email, tenant_id="demo", reason="unsubscribe", source=None, created_by=None):
        self.added.append({"email": email, "reason": reason, "source": source})
        return {"ok": True}

    def is_suppressed(self, email, tenant_id="demo"):
        return any(a["email"] == email for a in self.added) or not self.allow

    def check_outreach(self, *, email, tenant_id="demo", channel="email", mode="send"):
        allowed = self.allow and not self.added
        return {"allowed": allowed, "reason": None if allowed else "stub_suppressed"}


@pytest.fixture
def make_sequence(db_session):
    def _make(*, to_email: str | None = None, steps: int = 2):
        return aos.create_sequence(
            db_session,
            tenant_id=TENANT,
            user_id=None,
            to_email=to_email or f"buyer-{uuid.uuid4().hex[:8]}@example.com",
            steps=[
                {"subject": f"step{i}", "html_body": f"<p>hi {i}</p>", "delay_days": 0}
                for i in range(steps)
            ],
        )

    return _make


@pytest.fixture
def send_spy(monkeypatch):
    calls: list[dict[str, Any]] = []

    async def _fake_send(**kwargs):
        calls.append(kwargs)
        return {"success": True, "mode": "test", "message_id": f"m-{len(calls)}", "method": "stub"}

    monkeypatch.setattr("app.services.email_service.send_email", _fake_send)
    return calls


def _rows(db, sequence_id: str) -> list[EmailOutreach]:
    return (
        db.query(EmailOutreach)
        .filter(EmailOutreach.sequence_id == sequence_id)
        .order_by(EmailOutreach.sequence_step.asc())
        .all()
    )


def _status(row: EmailOutreach) -> str:
    return row.status.value if hasattr(row.status, "value") else str(row.status)


# ── 1. stop_sequence 本体 ──

class TestStopSequence:
    def test_idempotent_marks_all_and_cancels_active(self, db_session, make_sequence):
        seq = make_sequence(steps=3)
        rows = _rows(db_session, seq["sequence_id"])
        rows[0].status = EmailStatus.SENT  # 已发步不取消，仅标记
        db_session.commit()

        first = aos.stop_sequence(db_session, seq["sequence_id"], reason="manual", stopped_by="u1")
        assert first["exists"] is True
        assert first["cancelled_steps"] == 2  # step1/step2（draft→cancelled）
        assert first["marked_steps"] == 3  # 全部标记

        second = aos.stop_sequence(db_session, seq["sequence_id"], reason="manual")
        assert second["marked_steps"] == 0, "幂等：不覆盖/不重复标记"
        for r in _rows(db_session, seq["sequence_id"]):
            assert r.outreach_metadata["sequence_stopped"]["reason"] == "manual"

    def test_nonexistent_sequence_is_noop(self, db_session):
        out = aos.stop_sequence(db_session, "no-such-seq", reason="manual")
        assert out["exists"] is False


# ── 2. 发送咽喉 ──

class TestSendThroat:
    def test_suppressed_email_blocks_send(self, db_session, make_sequence, send_spy, monkeypatch):
        seq = make_sequence()
        row = _rows(db_session, seq["sequence_id"])[0]
        monkeypatch.setattr(
            "app.services.acquisition.suppression_list.suppression_store",
            _StubSuppression(allow=False),
        )
        out = aos.send_outreach_step(db_session, outreach_id=str(row.id))
        assert out["ok"] is False and out["error_code"] == "SEQUENCE_STOPPED"
        assert out["stop_reason"] == "suppressed"
        assert send_spy == [], "suppressed 必须零发送"
        assert _status(db_session.query(EmailOutreach).filter(EmailOutreach.id == row.id).one()) == "cancelled"

    def test_manual_stop_blocks_send(self, db_session, make_sequence, send_spy):
        seq = make_sequence()
        row = _rows(db_session, seq["sequence_id"])[1]
        row.status = EmailStatus.SENDING  # SENDING 不可跃迁 cancelled → 只有 metadata 拦截面
        db_session.commit()
        aos.stop_sequence(db_session, seq["sequence_id"], reason="manual")
        out = aos.send_outreach_step(db_session, outreach_id=str(row.id))
        assert out["error_code"] == "SEQUENCE_STOPPED"
        assert send_spy == []

    def test_manual_stop_cancels_draft_so_send_refuses(self, db_session, make_sequence, send_spy):
        """draft 步被 stop 直接取消 → send 走 cancelled 拒发（殊途同归，零发送）。"""
        seq = make_sequence()
        row = _rows(db_session, seq["sequence_id"])[0]
        aos.stop_sequence(db_session, seq["sequence_id"], reason="manual")
        out = aos.send_outreach_step(db_session, outreach_id=str(row.id))
        assert out["error_code"] == "OUTREACH_CANCELLED"
        assert send_spy == []

    def test_hard_bounce_in_sequence_blocks_send(self, db_session, make_sequence, send_spy):
        seq = make_sequence()
        rows = _rows(db_session, seq["sequence_id"])
        rows[0].status = EmailStatus.SENT
        rows[0].bounce_type = BounceType.HARD
        db_session.commit()
        out = aos.send_outreach_step(db_session, outreach_id=str(rows[1].id))
        assert out["stop_reason"] == "bounced_hard"
        assert send_spy == []

    def test_clean_sequence_sends_normally(self, db_session, make_sequence, send_spy, monkeypatch):
        """正向对照（防空真）：无任何停止判据时照常发送。"""
        monkeypatch.setattr(
            "app.services.acquisition.suppression_list.suppression_store",
            _StubSuppression(allow=True),
        )
        seq = make_sequence()
        row = _rows(db_session, seq["sequence_id"])[0]
        out = aos.send_outreach_step(db_session, outreach_id=str(row.id))
        assert out["ok"] is True
        assert len(send_spy) == 1
        fresh = db_session.query(EmailOutreach).filter(EmailOutreach.id == row.id).one()
        assert _status(fresh) == "sent"


# ── 3. bounce 联动 ──

class TestBounceLinkage:
    def test_hard_bounce_adds_suppression_and_stops(self, db_session, make_sequence, monkeypatch):
        stub = _StubSuppression(allow=True)
        monkeypatch.setattr(
            "app.services.acquisition.suppression_list.suppression_store", stub
        )
        seq = make_sequence()
        rows = _rows(db_session, seq["sequence_id"])
        rows[0].status = EmailStatus.SENT
        db_session.commit()

        assert record_bounce(db_session, str(rows[0].id), BounceType.HARD, "mailbox not found")

        assert any(a["reason"] == "bounce_hard" for a in stub.added)
        fresh = _rows(db_session, seq["sequence_id"])
        assert all("sequence_stopped" in (r.outreach_metadata or {}) for r in fresh)

    def test_soft_bounce_twice_downgrades_and_stops(self, db_session, make_sequence):
        seq = make_sequence()
        rows = _rows(db_session, seq["sequence_id"])
        rows[0].status = EmailStatus.SENT
        db_session.commit()
        target = str(rows[0].id)

        assert record_bounce(db_session, target, BounceType.SOFT, "temp fail")  # 1st
        assert record_bounce(db_session, target, BounceType.SOFT, "temp fail")  # 2nd

        fresh = _rows(db_session, seq["sequence_id"])
        bounced = next(r for r in fresh if str(r.id) == target)
        assert bounced.outreach_metadata["soft_bounce_count"] == 2
        assert bounced.outreach_metadata["contactability"] == "downgraded"
        assert all("sequence_stopped" in (r.outreach_metadata or {}) for r in fresh)


# ── 4. enqueue 红线（不可自动重启）──

class TestEnqueueRedLine:
    def test_suppressed_sequence_not_enqueued(self, db_session, make_sequence, monkeypatch):
        """suppression 命中（行仍是 DRAFT）→ 扫描不入队并整序列标记（不可自动重启）。"""
        monkeypatch.setattr(
            "app.services.acquisition.suppression_list.suppression_store",
            _StubSuppression(allow=False),
        )
        seq = make_sequence()

        out = aos.enqueue_due_steps(db_session, limit=50)

        assert out["queued"] == 0
        assert len(out["skipped_stopped"]) >= 1, "到期步必须被拦下"
        assert seq["sequence_id"] in out["stopped_sequences"]
        for r in _rows(db_session, seq["sequence_id"]):
            assert _status(r) == "cancelled"

    def test_manual_stop_leaves_nothing_to_enqueue(self, db_session, make_sequence):
        """manual stop 后步子已全 cancelled → 扫描空转、零入队（红线）。"""
        seq = make_sequence()
        aos.stop_sequence(db_session, seq["sequence_id"], reason="manual")

        out = aos.enqueue_due_steps(db_session, limit=50)

        assert out["queued"] == 0 and out["job_ids"] == []
        for r in _rows(db_session, seq["sequence_id"]):
            assert _status(r) == "cancelled"

    def test_confirm_rejects_stopped_sequence(self, db_session, make_sequence):
        seq = make_sequence()
        aos.stop_sequence(db_session, seq["sequence_id"], reason="manual")
        # 步子已被 stop 全量取消 → confirm 无 draft 可确认（红线：确认通道不可重启）
        with pytest.raises(ValueError) as ei:
            aos.confirm_and_enqueue(
                db_session, sequence_id=seq["sequence_id"], tenant_id=TENANT
            )
        assert str(ei.value) in ("sequence_stopped", "no_draft_steps")


# ── 5. classify_inbox 联动 ──

class TestClassifyInboxLinkage:
    def test_unsubscribe_adds_suppression(self, db_session, monkeypatch, make_sequence):
        stub = _StubSuppression(allow=True)
        monkeypatch.setattr(
            "app.services.acquisition.suppression_list.suppression_store", stub
        )
        seq = make_sequence()

        out = classify_inbox(
            tenant_id=TENANT,
            message="Please unsubscribe me from your list",
            db=db_session,
            params={"from_email": "buyer@example.com", "sequence_id": seq["sequence_id"]},
        )

        assert out["detected_intent"] == "nuisance"
        assert out["stop_triggers"]["suppressed"] is True
        assert any(a["reason"] == "unsubscribe" and a["email"] == "buyer@example.com" for a in stub.added)
        stopped = out["stop_triggers"]["sequence_stopped"]
        assert stopped["exists"] is True

    def test_positive_reply_stops_sequence(self, db_session, make_sequence):
        seq = make_sequence()

        out = classify_inbox(
            tenant_id=TENANT,
            message="Please send me your best price quotation for 5000 sqm",
            db=db_session,
            params={"sequence_id": seq["sequence_id"]},
        )

        assert out["detected_intent"] == "pricing"
        assert out["stop_triggers"]["human_handoff"] is True
        assert out["stop_triggers"]["sequence_stopped"]["exists"] is True
        for r in _rows(db_session, seq["sequence_id"]):
            assert r.outreach_metadata["sequence_stopped"]["reason"] == "replied_positive"

    def test_no_linkage_keeps_legacy_behavior(self, db_session, monkeypatch):
        """无 from_email/sequence_id：不臆造关联，仅分类+留痕。"""
        stub = _StubSuppression(allow=True)
        monkeypatch.setattr(
            "app.services.acquisition.suppression_list.suppression_store", stub
        )
        out = classify_inbox(
            tenant_id=TENANT,
            message="unsubscribe me",
            db=db_session,
        )
        assert out["detected_intent"] == "nuisance"
        assert "stop_triggers" not in out
        assert stub.added == []
