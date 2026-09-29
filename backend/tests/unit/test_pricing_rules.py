# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""定价规则版本化 + 预占快照测试（修正设计稿 模块14.2 / 第二层缺口 A / Gate G9）。

锁定语义：
- effective_rule：active + 生效窗口 + 版本号最大；plan 专属优先于通用；
- 无生效规则 → 诚实默认快照（no_active_pricing_rule），不伪造定价依据；
- amount_for：单价×数量，扣免费额度，clamp [min, max]；
- 快照冻结：创建预占时取当时规则，规则后续修改不影响已生成快照。
"""
from __future__ import annotations

from datetime import timedelta

import pytest

from app.models.billing_reservation import BillingReservation
from app.models.pricing_rule import PricingRule
from app.services.billing import reservation_service as rs
from app.services.billing import pricing_service as ps

TENANT = "4a111111-1111-4111-8111-111111111111"


def _rule(db, *, version=1, effective_from=None, effective_to=None, unit=800,
          status="active", meter="usage.qualified_inquiry", plan_id=None, free=0,
          minimum=None, maximum=None):
    row = PricingRule(
        rule_code="qualified-inquiry-default",
        version=version,
        meter_code=meter,
        plan_id=plan_id,
        unit_price_cents=unit,
        free_quota=free,
        minimum_charge_cents=minimum,
        maximum_charge_cents=maximum,
        status=status,
        is_active=(status == "active"),
        effective_from=effective_from,
        effective_to=effective_to,
    )
    db.add(row)
    db.commit()
    return row


class TestEffectiveRule:
    def test_latest_active_version_wins(self, db_session):
        now = ps._utcnow()
        _rule(db_session, version=1, effective_from=now - timedelta(days=10), unit=500)
        _rule(db_session, version=2, effective_from=now - timedelta(days=1), unit=900)
        rule = ps.effective_rule(db_session, meter_code="usage.qualified_inquiry", at=now)
        assert rule.version == 2
        assert rule.unit_price_cents == 900

    def test_future_version_not_effective(self, db_session):
        now = ps._utcnow()
        _rule(db_session, version=1, effective_from=now - timedelta(days=10), unit=500)
        _rule(db_session, version=2, effective_from=now + timedelta(days=1), unit=900)
        rule = ps.effective_rule(db_session, meter_code="usage.qualified_inquiry", at=now)
        assert rule.version == 1

    def test_expired_window_excluded(self, db_session):
        now = ps._utcnow()
        _rule(db_session, version=1, effective_from=now - timedelta(days=10),
              effective_to=now - timedelta(days=1), unit=500)
        assert ps.effective_rule(db_session, meter_code="usage.qualified_inquiry", at=now) is None


class TestSnapshot:
    def test_no_rule_honest_default(self, db_session):
        snap = ps.snapshot_for(db_session, meter_code="usage.qualified_inquiry")
        assert snap["rule_code"] is None
        assert snap["version"] == "v0"
        assert snap["note"] == "no_active_pricing_rule"

    def test_snapshot_frozen_against_later_rule_change(self, db_session):
        """模块14.2：结算快照取创建时点规则；后续改价不影响已生成快照。"""
        now = ps._utcnow()
        _rule(db_session, version=1, effective_from=now - timedelta(days=5), unit=700)
        r1, _ = rs.create_reservation(
            db_session, tenant_id=TENANT, meter_code="usage.qualified_inquiry",
            subject_type="inquiry", subject_id="snap-1", amount_cents=700,
        )
        assert r1.pricing_snapshot["unit_price_cents"] == 700
        # 改价：新版本 v2（立即生效，版本号最大者优先）
        _rule(db_session, version=2, effective_from=now - timedelta(seconds=1), unit=1500)
        r2, _ = rs.create_reservation(
            db_session, tenant_id=TENANT, meter_code="usage.qualified_inquiry",
            subject_type="inquiry", subject_id="snap-2", amount_cents=700,
        )
        assert r2.pricing_snapshot["unit_price_cents"] == 1500
        assert r1.pricing_snapshot["unit_price_cents"] == 700  # 旧快照不被重新解释


class TestAmountFor:
    def test_free_quota_and_clamp(self):
        snap = {"unit_price_cents": 100, "free_quota": 2,
                "minimum_charge_cents": 100, "maximum_charge_cents": 900}
        assert ps.amount_for(snap, quantity=1) == 100   # 免费额度内 → clamp 到最小
        assert ps.amount_for(snap, quantity=5) == 300   # (5-2)*100
        assert ps.amount_for(snap, quantity=20) == 900  # 上限


class TestAutoSnapshotInReservation:
    def test_create_reservation_autofills_snapshot(self, db_session):
        now = ps._utcnow()
        _rule(db_session, version=1, effective_from=now - timedelta(days=1), unit=650)
        r, created = rs.create_reservation(
            db_session, tenant_id=TENANT, meter_code="usage.qualified_inquiry",
            subject_type="inquiry", subject_id="auto-1",
        )
        assert created is True
        assert r.pricing_snapshot["rule_code"] == "qualified-inquiry-default"
        assert r.pricing_rule_version == "v1"
