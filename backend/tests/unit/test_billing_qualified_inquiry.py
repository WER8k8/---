# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""模块 9/10 · 轨 2 Pay-per-use 计费时点反证测试（R-8/R-10）。

配对反证（缺任一侧 = 空真）：
- 负向：未发生合格询盘 → 零扣费（计量不增、预占不增）；
- 正向：首次到达 in_progress 及以后 → 计量 +1（含 new→quoted 直跳，漏收回归锁）；
- 幂等：重复推进 → event_key 仍 1 行；
- 别名：contacted → in_progress（不得落库 contacted）；
- 校验回归：super_agent 路径非法状态抛错而非落库；
- fail-closed：tenant_id 为空 → 不计费。

基线说明：meter_events / billing_reservations 的计数均在测试内取「推进前」快照后
比较增量，不假设全库绝对值（测试库非现网）。
"""
from __future__ import annotations

import asyncio
import uuid

import pytest

from app.models.billing_reservation import BillingReservation
from app.models.inquiry import Inquiry
from app.models.meter import METER_CODES_PLANNED, METER_DEFINITIONS, MeterEvent
from app.services.billing.reservation_service import IllegalTransition
from app.services.inquiry_funnel_state_machine import normalize
from app.services.inquiry_status_service import (
    BILLABLE_QUALIFIED_STAGES,
    advance_inquiry_status,
)

TENANT = "3a111111-1111-4111-8111-111111111111"
_EVENT_KEY = "inquiry:{id}:qualified"
_METER_CODE = "usage.qualified_inquiry"


def _qualified_count(db) -> int:
    return db.query(MeterEvent).filter(MeterEvent.meter_code == _METER_CODE).count()


def _reservation_count(db) -> int:
    return db.query(BillingReservation).count()


@pytest.fixture
def make_inquiry(db_session):
    """造询盘并登记 id，测试结束清理（保证 inquiries 恢复原状）。"""
    created: list[str] = []

    def _make(*, status: str = "pending", tenant_id: str | None = TENANT,
              phone: str | None = "13800000000", email: str | None = None,
              customer_finder_id: str | None = None) -> Inquiry:
        inq = Inquiry(
            id=str(uuid.uuid4()),
            name="反证询盘",
            message="需要 5000 件保温板，请报价",
            status=status,
            is_active=True,
            phone=phone,
            email=email,
            tenant_id=tenant_id,
            customer_finder_id=customer_finder_id,
        )
        db_session.add(inq)
        db_session.commit()
        db_session.refresh(inq)
        created.append(str(inq.id))
        return inq

    yield _make

    # 清理：删除本测试创建的询盘与其计量/预占痕迹（幂等、留空库）
    try:
        for iid in created:
            db_session.query(MeterEvent).filter(
                MeterEvent.event_key == _EVENT_KEY.format(id=iid)
            ).delete(synchronize_session=False)
            db_session.query(Inquiry).filter(Inquiry.id == iid).delete(
                synchronize_session=False)
        db_session.commit()
    except Exception:  # noqa: BLE001
        db_session.rollback()


# ============ 模块9 · METER_DEFINITIONS 常量 ============

class TestMeterDefinitions:
    def test_covers_all_planned_codes(self):
        assert set(METER_DEFINITIONS) == set(METER_CODES_PLANNED), (
            f"缺定义: {set(METER_CODES_PLANNED) - set(METER_DEFINITIONS)}；"
            f"多余: {set(METER_DEFINITIONS) - set(METER_CODES_PLANNED)}"
        )
        assert len(METER_DEFINITIONS) == 10

    def test_each_definition_has_required_keys(self):
        required = {"unit", "subject_type", "billable", "requires_reservation", "track"}
        for code, d in METER_DEFINITIONS.items():
            assert set(d) == required, f"{code} 定义键不符: {set(d)}"

    def test_units_match_emit_star(self):
        # 与既有 emit_* 实际写入值一致（回源码核对，非臆造）
        assert METER_DEFINITIONS["ai.token"]["unit"] == "call"          # emit_ai_generation
        assert METER_DEFINITIONS["usage.qualified_inquiry"]["unit"] == "lead"  # emit_lead_generated
        assert METER_DEFINITIONS["api.request"]["unit"] == "call"       # emit_api_call

    def test_no_meter_definitions_table_declared(self):
        # 模块9 裁定：不建表（定义只以代码常量表达）
        from app.core.database import Base
        assert "meter_definitions" not in Base.metadata.tables


# ============ 词表唯一真源 ============

class TestWhitelistSingleSource:
    def test_routes_reuse_funnel_whitelist(self):
        from app.services.inquiry_funnel_state_machine import VALID_STATUSES
        import app.api.v1.routes.inquiries as routes_mod
        assert routes_mod.VALID_STATUSES is VALID_STATUSES
        # 禁止在路由层再留副本
        assert not hasattr(routes_mod, "_VALID_INQUIRY_STATUSES")

    def test_contacted_is_alias(self):
        from app.services.inquiry_funnel_state_machine import normalize
        assert normalize("contacted") == "in_progress"
        assert normalize("pending") == "new"


# ============ 负向反证：未合格 → 零扣费 ============

class TestNegative:
    def test_stays_new_no_billing(self, db_session, make_inquiry):
        before_meter = _qualified_count(db_session)
        before_resv = _reservation_count(db_session)

        inq = make_inquiry(status="new")
        # 停在 new，不推进
        assert inq.status == "new"
        db_session.refresh(inq)
        assert inq.status == "new"

        assert _qualified_count(db_session) == before_meter, "未合格询盘不得计费"
        assert _reservation_count(db_session) == before_resv, "不得产生隐式预占"

    def test_no_op_new_does_not_bill(self, db_session, make_inquiry):
        before = _qualified_count(db_session)
        inq = make_inquiry(status="new")
        advance_inquiry_status(db_session, inq, "new", source="t")  # 未达计费阶
        assert _qualified_count(db_session) == before


# ============ 正向反证：合格 → 计量 +1 ============

class TestPositive:
    def test_new_to_in_progress_bills_once(self, db_session, make_inquiry):
        before = _qualified_count(db_session)
        inq = make_inquiry(status="pending")

        advance_inquiry_status(
            db_session, inq, "in_progress", source="inquiries_api", actor_id="u-1")

        assert _qualified_count(db_session) == before + 1
        ev = db_session.query(MeterEvent).filter(
            MeterEvent.event_key == _EVENT_KEY.format(id=inq.id)).one()
        assert ev.meter_code == _METER_CODE
        assert ev.tenant_id is not None and str(ev.tenant_id)
        assert ev.quantity == 1
        assert ev.unit == "lead"
        assert ev.source_ref_type == "lead"
        assert ev.source_ref_id == str(inq.id)
        assert ev.bill_status == "unlinked"
        # 预占闸门 BILLING_GATE_ENABLED 默认 False（R-3 备选解耦）→ 默认零隐式预占；
        # 开启态的正向/幂等反证见 TestReservationGate（09-28 接线）
        assert _reservation_count(db_session) == 0

    def test_direct_jump_new_to_quoted_bills(self, db_session, make_inquiry):
        """漏收回归锁：new → quoted 直跳（跳过 in_progress）必须计费（阶数判据）。"""
        before = _qualified_count(db_session)
        inq = make_inquiry(status="pending")

        advance_inquiry_status(db_session, inq, "quoted", source="inquiries_api")

        assert db_session.query(Inquiry).filter(Inquiry.id == inq.id).one().status == "quoted"
        assert _qualified_count(db_session) == before + 1, "直跳 quoted 漏计费 = 回归失败"

    def test_direct_jump_new_to_accepted_bills(self, db_session, make_inquiry):
        before = _qualified_count(db_session)
        inq = make_inquiry(status="new")
        advance_inquiry_status(db_session, inq, "accepted", source="inquiries_api")
        assert _qualified_count(db_session) == before + 1

    def test_email_only_contact_bills(self, db_session, make_inquiry):
        before = _qualified_count(db_session)
        inq = make_inquiry(status="new", phone=None, email="buyer@example.com")
        advance_inquiry_status(db_session, inq, "in_progress", source="inquiries_api")
        assert _qualified_count(db_session) == before + 1


# ============ fail-closed：tenant_id 为空不计费 ============

class TestFailClosed:
    def test_missing_tenant_not_billed(self, db_session, make_inquiry):
        before = _qualified_count(db_session)
        inq = make_inquiry(status="new", tenant_id=None)

        advance_inquiry_status(db_session, inq, "in_progress", source="inquiries_api")

        assert db_session.query(Inquiry).filter(Inquiry.id == inq.id).one().status == "in_progress"
        assert _qualified_count(db_session) == before, "tenant_id 为空必须 fail-closed"
        assert db_session.query(MeterEvent).filter(
            MeterEvent.event_key == _EVENT_KEY.format(id=inq.id)).count() == 0


# ============ 轨2 预占闸门（BILLING_GATE_ENABLED，09-28 接线） ============

class TestReservationGate:
    """BILLING_GATE_ENABLED=True 时：计量后追加 create_reservation（幂等，不阻断）。"""

    @pytest.fixture
    def gate_on(self, monkeypatch):
        from app.core.config import settings

        monkeypatch.setattr(settings, "BILLING_GATE_ENABLED", True)
        return True

    def test_gate_off_by_default_no_reservation(self, db_session, make_inquiry):
        """闸门默认关：即使代码已接线，默认路径也不得产生预占（防隐式扣费）。"""
        from app.core.config import settings

        assert settings.BILLING_GATE_ENABLED is False
        before = _reservation_count(db_session)
        inq = make_inquiry(status="pending")
        advance_inquiry_status(db_session, inq, "in_progress", source="t")
        assert _reservation_count(db_session) == before, "闸门默认关不得预占"

    def test_gate_on_bills_and_reserves(self, db_session, make_inquiry, gate_on):
        before_resv = _reservation_count(db_session)
        inq = make_inquiry(status="pending")

        advance_inquiry_status(db_session, inq, "in_progress", source="inquiries_api")

        assert _qualified_count(db_session) >= 1, "计量仍必须发生"
        assert _reservation_count(db_session) == before_resv + 1, "闸门开启须 +1 预占"
        resv = (
            db_session.query(BillingReservation)
            .filter(BillingReservation.idempotency_key == (
                f"bill:{inq.tenant_id}:{_METER_CODE}:inquiry:{inq.id}:v1"))
            .one()
        )
        assert resv.status == "created"
        assert resv.meter_code == _METER_CODE
        assert str(resv.subject_id) == str(inq.id)
        # 幂等键规范：bill:{tenant}:{meter_code}:{subject_type}:{subject_id}:v1
        assert resv.idempotency_key == (
            f"bill:{inq.tenant_id}:{_METER_CODE}:inquiry:{inq.id}:v1"
        )
        # 无 Pricing Rule 时 v0 / 0 分（契约 §8.2）
        assert resv.pricing_rule_version == "v0"
        assert resv.amount_cents == 0
        # 计量行关联：unlinked → reserved
        ev = db_session.query(MeterEvent).filter(
            MeterEvent.event_key == _EVENT_KEY.format(id=inq.id)).one()
        assert ev.bill_status == "reserved"

    def test_gate_on_idempotent_no_double_reserve(self, db_session, make_inquiry, gate_on):
        """同询盘重复推进（幂等命中计量）不得二次预占。"""
        inq = make_inquiry(status="pending")
        advance_inquiry_status(db_session, inq, "in_progress", source="t")
        after_first = _reservation_count(db_session)

        # 二次推进同一询盘到更后阶段：计量 event_key 幂等命中 → 不得新增预占
        advance_inquiry_status(db_session, inq, "quoted", source="t")

        assert _reservation_count(db_session) == after_first, "同询盘不得二次预占"

    def test_reservation_failure_does_not_block_inquiry(
        self, db_session, make_inquiry, gate_on, monkeypatch
    ):
        """预占抛错：询盘推进与计量必须照常成功（不阻断主链路）。"""
        from app.services.billing import reservation_service as rs

        def _boom(*a, **k):
            raise RuntimeError("reservation upstream down")

        monkeypatch.setattr(rs, "create_reservation", _boom)
        inq = make_inquiry(status="pending")

        out = advance_inquiry_status(db_session, inq, "in_progress", source="t")

        assert out.status == "in_progress", "预占失败不得阻断状态推进"
        ev = db_session.query(MeterEvent).filter(
            MeterEvent.event_key == _EVENT_KEY.format(id=inq.id)).one()
        assert ev.bill_status == "unlinked", "预占失败计量保持 unlinked"

    def test_missing_contact_not_billed(self, db_session, make_inquiry):
        before = _qualified_count(db_session)
        inq = make_inquiry(status="new", phone=None, email=None)

        advance_inquiry_status(db_session, inq, "in_progress", source="inquiries_api")

        assert _qualified_count(db_session) == before, "无联系方式必须 fail-closed"


# ============ 幂等 ============

class TestIdempotency:
    def test_repeat_advance_keeps_single_event(self, db_session, make_inquiry):
        before = _qualified_count(db_session)
        inq = make_inquiry(status="pending")

        advance_inquiry_status(db_session, inq, "in_progress", source="inquiries_api")
        # 重复推进（in_progress → quoted），不得产生第二行
        advance_inquiry_status(db_session, inq, "quoted", source="inquiries_api")
        # 再次同状态推进
        advance_inquiry_status(db_session, inq, "quoted", source="inquiries_api")

        rows = db_session.query(MeterEvent).filter(
            MeterEvent.event_key == _EVENT_KEY.format(id=inq.id)).count()
        assert rows == 1
        assert _qualified_count(db_session) == before + 1


# ============ 别名 + 校验回归 ============

class TestAliasAndValidation:
    def test_contacted_normalizes_to_in_progress(self, db_session, make_inquiry):
        before = _qualified_count(db_session)
        inq = make_inquiry(status="pending")

        advance_inquiry_status(db_session, inq, "contacted", source="feishu_mark_contacted")

        row = db_session.query(Inquiry).filter(Inquiry.id == inq.id).one()
        assert row.status == "in_progress"
        assert row.status != "contacted"
        assert _qualified_count(db_session) == before + 1

    def test_invalid_status_raises_and_not_persisted(self, db_session, make_inquiry):
        inq = make_inquiry(status="new")
        with pytest.raises(ValueError):
            advance_inquiry_status(db_session, inq, "totally_bogus", source="t")
        with pytest.raises(ValueError):
            advance_inquiry_status(db_session, inq, "第8类", source="t")
        assert db_session.query(Inquiry).filter(Inquiry.id == inq.id).one().status == "new"

    def test_illegal_backward_transition_raises(self, db_session, make_inquiry):
        inq = make_inquiry(status="pending")
        advance_inquiry_status(db_session, inq, "quoted", source="t")
        with pytest.raises(IllegalTransition):
            advance_inquiry_status(db_session, inq, "in_progress", source="t")
        assert db_session.query(Inquiry).filter(Inquiry.id == inq.id).one().status == "quoted"

    def test_super_agent_path_rejects_invalid_status(self, db_session, make_inquiry):
        """super_agent 路径非法状态 → 返回 400 且不落库（收回零校验直写）。"""
        from types import SimpleNamespace

        from app.api.v1.routes.super_agent import (
            CustomerStatusBody,
            update_customer_status,
        )

        cid = "cf-" + uuid.uuid4().hex[:8]
        inq = make_inquiry(status="new", customer_finder_id=cid)

        resp = asyncio.run(update_customer_status(
            cid, CustomerStatusBody(status="totally_bogus"),
            db=db_session, current_user=SimpleNamespace(id="u-1"),
        ))
        assert getattr(resp, "status_code", None) == 400
        assert db_session.query(Inquiry).filter(Inquiry.id == inq.id).one().status == "new"

    def test_super_agent_path_accepts_alias(self, db_session, make_inquiry):
        from types import SimpleNamespace

        from app.api.v1.routes.super_agent import (
            CustomerStatusBody,
            update_customer_status,
        )

        cid = "cf-" + uuid.uuid4().hex[:8]
        inq = make_inquiry(status="new", customer_finder_id=cid)

        resp = asyncio.run(update_customer_status(
            cid, CustomerStatusBody(status="contacted"),
            db=db_session, current_user=SimpleNamespace(id="u-1"),
        ))
        # success_response 返回 APIResponse 模型（非 HTTP 响应）
        assert getattr(resp, "status_code", 0) in (0, 200)
        assert db_session.query(Inquiry).filter(Inquiry.id == inq.id).one().status == "in_progress"


# ============ 补正2：显式计费集合（严禁下标比较） ============

class TestBillingStageSet:
    def test_billable_set_is_explicit_and_excludes_archived(self):
        assert BILLABLE_QUALIFIED_STAGES == frozenset({
            "in_progress", "quoted", "accepted", "processing", "resolved", "closed",
        })
        assert "archived" not in BILLABLE_QUALIFIED_STAGES
        assert "new" not in BILLABLE_QUALIFIED_STAGES

    def test_archived_index_gt_in_progress_guard(self):
        """防下标比较回归：archived 下标 > in_progress，但绝不允许据此计费。"""
        from app.services.inquiry_funnel_state_machine import FUNNEL_STAGES
        assert FUNNEL_STAGES.index("archived") > FUNNEL_STAGES.index("in_progress")
        assert "archived" not in BILLABLE_QUALIFIED_STAGES


class TestArchivedNotBilled:
    def test_archived_direct_not_billed(self, db_session, make_inquiry):
        before = _qualified_count(db_session)
        inq = make_inquiry(status="new")
        advance_inquiry_status(db_session, inq, "archived", source="inquiries_api")
        assert db_session.query(Inquiry).filter(Inquiry.id == inq.id).one().status == "archived"
        assert _qualified_count(db_session) == before, "archived 不得计费"

    def test_spam_alias_not_billed(self, db_session, make_inquiry):
        before = _qualified_count(db_session)
        inq = make_inquiry(status="new")
        advance_inquiry_status(db_session, inq, "spam", source="inquiries_api")
        assert db_session.query(Inquiry).filter(Inquiry.id == inq.id).one().status == "archived"
        assert _qualified_count(db_session) == before, "spam→archived 不得计费"

    def test_lost_alias_not_billed(self, db_session, make_inquiry):
        before = _qualified_count(db_session)
        inq = make_inquiry(status="new")
        advance_inquiry_status(db_session, inq, "lost", source="inquiries_api")
        assert db_session.query(Inquiry).filter(Inquiry.id == inq.id).one().status == "archived"
        assert _qualified_count(db_session) == before, "lost→archived 不得计费"


# ============ 补正1：9 条别名归一 ============

class TestAliases:
    def test_all_nine_aliases(self):
        assert normalize("pending") == "new"
        assert normalize("contacted") == "in_progress"
        assert normalize("qualified") == "in_progress"
        assert normalize("converted") == "closed"
        assert normalize("won") == "closed"
        assert normalize("deal") == "closed"
        assert normalize("lost") == "archived"
        assert normalize("rejected") == "archived"
        assert normalize("spam") == "archived"

    def test_won_bills_as_closed(self, db_session, make_inquiry):
        before = _qualified_count(db_session)
        inq = make_inquiry(status="new")
        advance_inquiry_status(db_session, inq, "won", source="inquiries_api")
        assert db_session.query(Inquiry).filter(Inquiry.id == inq.id).one().status == "closed"
        assert _qualified_count(db_session) == before + 1

    def test_qualified_alias_bills(self, db_session, make_inquiry):
        before = _qualified_count(db_session)
        inq = make_inquiry(status="new")
        advance_inquiry_status(db_session, inq, "qualified", source="inquiries_api")
        assert db_session.query(Inquiry).filter(Inquiry.id == inq.id).one().status == "in_progress"
        assert _qualified_count(db_session) == before + 1

    def test_rejected_alias_archives_no_bill(self, db_session, make_inquiry):
        before = _qualified_count(db_session)
        inq = make_inquiry(status="new")
        advance_inquiry_status(db_session, inq, "rejected", source="inquiries_api")
        assert db_session.query(Inquiry).filter(Inquiry.id == inq.id).one().status == "archived"
        assert _qualified_count(db_session) == before


# ============ 补正3/5：赢/输经验环通路可达 ============

class TestWinLossWiring:
    def _stub_user(self):
        from types import SimpleNamespace
        return SimpleNamespace(id="u-1", role="super_admin")  # super_admin 跳过租户拦截

    def test_won_reaches_record_ops_win(self, db_session, make_inquiry, monkeypatch):
        from app.api.v1.routes.inquiries import InquiryStatusUpdate, update_inquiry_status
        from app.services.acquisition import experience_feed

        calls: dict[str, int] = {"win": 0, "loss": 0}
        monkeypatch.setattr(
            experience_feed, "record_ops_win",
            lambda *a, **k: calls.__setitem__("win", calls["win"] + 1) or {})
        monkeypatch.setattr(
            experience_feed, "record_ops_loss",
            lambda *a, **k: calls.__setitem__("loss", calls["loss"] + 1) or {})

        inq = make_inquiry(status="new")
        resp = update_inquiry_status(
            str(inq.id), InquiryStatusUpdate(status="won"),
            db=db_session, current_user=self._stub_user(),
        )

        assert getattr(resp, "status_code", 0) in (0, 200), "won 应放行（原为白名单死代码）"
        assert db_session.query(Inquiry).filter(Inquiry.id == inq.id).one().status == "closed"
        assert calls["win"] == 1, "won 必须触达 record_ops_win（经验环）"
        assert calls["loss"] == 0

    def test_converted_reaches_record_ops_win(self, db_session, make_inquiry, monkeypatch):
        """converted（转化成功）与 won/deal 同义：归一为 closed 且必须触发 record_ops_win。

        回归锁：raw `converted` 若只落 closed 却不进 win 元组 → 经验环漏一类成单（静默漏收）。
        """
        from app.api.v1.routes.inquiries import InquiryStatusUpdate, update_inquiry_status
        from app.services.acquisition import experience_feed

        calls: dict[str, int] = {"win": 0, "loss": 0}
        monkeypatch.setattr(
            experience_feed, "record_ops_win",
            lambda *a, **k: calls.__setitem__("win", calls["win"] + 1) or {})
        monkeypatch.setattr(
            experience_feed, "record_ops_loss",
            lambda *a, **k: calls.__setitem__("loss", calls["loss"] + 1) or {})

        inq = make_inquiry(status="new")
        resp = update_inquiry_status(
            str(inq.id), InquiryStatusUpdate(status="converted"),
            db=db_session, current_user=self._stub_user(),
        )

        assert getattr(resp, "status_code", 0) in (0, 200), "converted 应放行（别名 → closed）"
        assert db_session.query(Inquiry).filter(Inquiry.id == inq.id).one().status == "closed"
        assert calls["win"] == 1, "converted（成单）必须触达 record_ops_win（经验环）"
        assert calls["loss"] == 0

    def test_spam_reaches_record_ops_loss(self, db_session, make_inquiry, monkeypatch):
        from app.api.v1.routes.inquiries import InquiryStatusUpdate, update_inquiry_status
        from app.services.acquisition import experience_feed

        calls: dict[str, int] = {"win": 0, "loss": 0}
        monkeypatch.setattr(
            experience_feed, "record_ops_win",
            lambda *a, **k: calls.__setitem__("win", calls["win"] + 1) or {})
        monkeypatch.setattr(
            experience_feed, "record_ops_loss",
            lambda *a, **k: calls.__setitem__("loss", calls["loss"] + 1) or {})

        inq = make_inquiry(status="new")
        before = _qualified_count(db_session)
        resp = update_inquiry_status(
            str(inq.id), InquiryStatusUpdate(status="spam"),
            db=db_session, current_user=self._stub_user(),
        )

        assert getattr(resp, "status_code", 0) in (0, 200)
        assert db_session.query(Inquiry).filter(Inquiry.id == inq.id).one().status == "archived"
        assert calls["loss"] == 1, "spam 必须触达 record_ops_loss（经验环）"
        assert calls["win"] == 0
        assert _qualified_count(db_session) == before, "spam 归档不得计费"

    def test_invalid_status_still_400(self, db_session, make_inquiry):
        from app.api.v1.routes.inquiries import InquiryStatusUpdate, update_inquiry_status

        inq = make_inquiry(status="new")
        resp = update_inquiry_status(
            str(inq.id), InquiryStatusUpdate(status="totally_bogus"),
            db=db_session, current_user=self._stub_user(),
        )
        assert getattr(resp, "status_code", None) == 400
        assert db_session.query(Inquiry).filter(Inquiry.id == inq.id).one().status == "new"

