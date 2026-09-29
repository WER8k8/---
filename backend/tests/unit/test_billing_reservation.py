# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""计费预占状态机测试（修正设计稿 模块18 / Gate G9）。

锁定语义：
- 幂等键规范拼装稳定；同身份重复 create 只有一条（重试/回调重放防线）；
- 未知 meter_code 拒绝（禁止序号语义回潮）；
- settle 恰好落一条 finance_ledger 营收分录；重复 settle 被状态机拒绝；
- reserved → released 不落账（未收费）；settled → reversed 写负向冲正分录；
- 非法跃迁（created→settled 直接跳闸）一律拒绝 —— 禁止绕过预占直接落账。
"""
from __future__ import annotations

import pytest

from app.models.billing_reservation import BillingReservation
from app.models.finance_ledger import FinanceLedgerEntry
from app.services.billing import reservation_service as rs

TENANT = "3a111111-1111-4111-8111-111111111111"


def _key(**over):
    return rs.build_idempotency_key(
        over.get("tenant", TENANT),
        over.get("meter_code", "usage.qualified_inquiry"),
        over.get("subject_type", "inquiry"),
        over.get("subject_id", "inq-1"),
        over.get("event_version", 1),
    )


class TestIdempotencyKey:
    def test_composition_is_stable(self):
        assert _key() == f"bill:{TENANT}:usage.qualified_inquiry:inquiry:inq-1:v1"

    def test_version_changes_identity(self):
        assert _key(event_version=2) != _key(event_version=1)


class TestCreateReservation:
    def test_duplicate_identity_returns_same_row(self, db_session):
        r1, created1 = rs.create_reservation(
            db_session,
            tenant_id=TENANT,
            meter_code="usage.qualified_inquiry",
            subject_type="inquiry",
            subject_id="inq-1",
            amount_cents=500,
        )
        assert created1 is True
        # 模拟重试 / 回调重放：同身份再来一次
        r2, created2 = rs.create_reservation(
            db_session,
            tenant_id=TENANT,
            meter_code="usage.qualified_inquiry",
            subject_type="inquiry",
            subject_id="inq-1",
            amount_cents=500,
        )
        assert created2 is False
        assert str(r1.id) == str(r2.id)
        assert db_session.query(BillingReservation).count() == 1

    def test_unknown_meter_code_rejected(self, db_session):
        with pytest.raises(rs.UnknownMeterCode):
            rs.create_reservation(
                db_session,
                tenant_id=TENANT,
                meter_code="第8类",  # 序号语义必须被拒绝
                subject_type="inquiry",
                subject_id="x",
            )


class TestStateMachine:
    def test_settle_writes_exactly_one_revenue_entry(self, db_session):
        r, _ = rs.create_reservation(
            db_session,
            tenant_id=TENANT,
            meter_code="usage.boq_processing",
            subject_type="boq_job",
            subject_id="boq-9",
            amount_cents=1200,
            pricing_rule_version="v1",
        )
        rs.reserve(db_session, r, reason="execute")
        rs.settle(db_session, r, ledger_note="BOQ 处理完成")

        entries = (
            db_session.query(FinanceLedgerEntry)
            .filter(FinanceLedgerEntry.reference_id == str(r.id))
            .all()
        )
        assert len(entries) == 1
        assert entries[0].entry_type == "revenue"
        assert entries[0].amount_cents == 1200
        assert entries[0].category == "usage.boq_processing"
        assert r.finance_entry_id == entries[0].id

        # 重复 settle（重复扣费）→ 状态机拒绝
        with pytest.raises(rs.IllegalTransition):
            rs.settle(db_session, r)
        # 分录仍然只有一条
        assert (
            db_session.query(FinanceLedgerEntry)
            .filter(FinanceLedgerEntry.reference_id == str(r.id))
            .count()
            == 1
        )

    def test_release_does_not_write_ledger(self, db_session):
        r, _ = rs.create_reservation(
            db_session,
            tenant_id=TENANT,
            meter_code="usage.premium_research",
            subject_type="research",
            subject_id="res-1",
            amount_cents=800,
        )
        rs.reserve(db_session, r)
        rs.release(db_session, r, reason="执行失败")
        assert r.status == "released"
        assert (
            db_session.query(FinanceLedgerEntry)
            .filter(FinanceLedgerEntry.reference_id == str(r.id))
            .count()
            == 0
        )

    def test_reverse_writes_negative_entry(self, db_session):
        r, _ = rs.create_reservation(
            db_session,
            tenant_id=TENANT,
            meter_code="commission.deal",
            subject_type="order",
            subject_id="ord-7",
            amount_cents=3000,
        )
        rs.reserve(db_session, r)
        rs.settle(db_session, r)
        rs.reverse(db_session, r, reason="订单退款")

        amounts = [
            e.amount_cents
            for e in db_session.query(FinanceLedgerEntry)
            .filter(FinanceLedgerEntry.reference_id == str(r.id))
            .all()
        ]
        assert amounts == [3000, -3000]  # 原分录 + 冲正
        assert r.reversal_entry_id is not None
        assert r.status == "reversed"

    def test_cannot_skip_reservation_to_settle(self, db_session):
        """设计红线：禁止 created 直接 → settled（绕过预占落账）。"""
        r, _ = rs.create_reservation(
            db_session,
            tenant_id=TENANT,
            meter_code="api.request",
            subject_type="api_call",
            subject_id="call-1",
            amount_cents=10,
        )
        with pytest.raises(rs.IllegalTransition):
            rs.settle(db_session, r)
        assert r.status == "created"
        assert (
            db_session.query(FinanceLedgerEntry)
            .filter(FinanceLedgerEntry.reference_id == str(r.id))
            .count()
            == 0
        )


class TestOutboxWiring:
    def test_transitions_emit_outbox_events(self, db_session):
        from app.models.outbox import OutboxEvent

        r, _ = rs.create_reservation(
            db_session,
            tenant_id=TENANT,
            meter_code="usage.qualified_inquiry",
            subject_type="inquiry",
            subject_id="inq-2",
            amount_cents=500,
        )
        rs.reserve(db_session, r)
        rs.settle(db_session, r)
        types = {
            e.event_type for e in db_session.query(OutboxEvent).filter_by(aggregate_id=str(r.id))
        }
        assert "billing.reserved" in types
        assert "billing.settled" in types
