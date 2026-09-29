# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""模块 9/10/11 · 轨 2 BOQ + 轨 6 Referral 计量触发点 —— 配对反证测试。

配对反证（缺任一侧 = 空真）：
- 负向：未到达计费时点 → 零计量（count 不增）；
- 正向：到达计费时点 → 计量 +1，且 meter_code / subject_type / unit / 归属租户正确落库；
- 幂等：同一业务主体重复触发 → event_key 仍 1 行；
- fail-closed：tenant_id 为空 → 不计量。

计费时点（与设计 10.3「不能提交即收费」同口径）：
- BOQ     ：`approve_job`（calculated→approved = 处理完成），**非上传/创建时**；
- Referral：`mark_invite_qualified`（pending→rewarded = 收入确认），**非邀请创建时**。

meter_type 沿用既有 7 类（DB CheckConstraint 不动）：BOQ→rfq_created、Referral→lead_generated；
meter_code 落七轨稳定词表 usage.boq_processing / referral.revenue（设计 9.3，修复 meter_code 全 NULL）。
"""
from __future__ import annotations

import uuid

import pytest

from app.models.boq_import import BoqImportJob
from app.models.meter import MeterEvent
from app.models.referral import ReferralCode, ReferralRecord

TENANT_BOQ = "3a222222-2222-4222-8222-222222222221"      # BOQ 归属租户
TENANT_INVITER = "3a222222-2222-4222-8222-222222222222"  # 推荐人（裂变收入归属）
TENANT_INVITED = "3a222222-2222-4222-8222-222222222223"  # 被推荐人

BOQ_METER = "usage.boq_processing"
BOQ_EVENT_KEY = "boq_job:{id}:processing"
REF_METER = "referral.revenue"
REF_EVENT_KEY = "referral:{id}:rewarded"


def _count(db, meter_code: str) -> int:
    return db.query(MeterEvent).filter(MeterEvent.meter_code == meter_code).count()


# ───────────────────────── BOQ（轨 2）─────────────────────────
@pytest.fixture
def make_boq_job(db_session):
    created: list[str] = []

    def _make(*, status: str = "calculated", tenant_id: str = TENANT_BOQ) -> BoqImportJob:
        job = BoqImportJob(id=str(uuid.uuid4()), tenant_id=tenant_id, status=status)
        db_session.add(job)
        db_session.commit()
        db_session.refresh(job)
        created.append(str(job.id))
        return job

    yield _make

    for jid in created:
        db_session.query(MeterEvent).filter(
            MeterEvent.event_key == BOQ_EVENT_KEY.format(id=jid)
        ).delete(synchronize_session=False)
        db_session.query(BoqImportJob).filter(
            BoqImportJob.id == jid
        ).delete(synchronize_session=False)
    db_session.commit()


class TestBoqProcessingTrigger:
    def test_negative_not_billed_before_approval(self, db_session, make_boq_job):
        """负向：job 停在 calculated（仅创建/未审批）→ 零计量（禁止"提交即收费"）。"""
        before = _count(db_session, BOQ_METER)
        make_boq_job(status="calculated")
        assert _count(db_session, BOQ_METER) == before

    def test_positive_approval_emits_meter(self, db_session, make_boq_job):
        """正向：审批通过（处理完成）→ 计量 +1，字段正确落库。"""
        from app.services.boq_pipeline_service import approve_job

        before = _count(db_session, BOQ_METER)
        job = make_boq_job(status="calculated")
        approve_job(db_session, job, approver="tester")

        assert _count(db_session, BOQ_METER) == before + 1
        ev = db_session.query(MeterEvent).filter(
            MeterEvent.event_key == BOQ_EVENT_KEY.format(id=job.id)
        ).one()
        assert ev.meter_code == BOQ_METER
        assert ev.subject_type == "boq_job"
        assert ev.subject_id == str(job.id)
        assert ev.unit == "job"
        assert ev.quantity == 1
        assert str(ev.tenant_id) == TENANT_BOQ
        assert ev.bill_status == "unlinked"

    def test_idempotent_single_row_and_reapprove_rejected(self, db_session, make_boq_job):
        """幂等 + 防重：同一 job 恒 1 行；重复 approve 被状态机拒绝（不产生第二行）。"""
        from app.services.boq_pipeline_service import PipelineError, approve_job

        job = make_boq_job(status="calculated")
        approve_job(db_session, job, approver="tester")
        assert db_session.query(MeterEvent).filter(
            MeterEvent.event_key == BOQ_EVENT_KEY.format(id=job.id)
        ).count() == 1

        # 二次 approve：状态已 approved → 抛错，且计量不重复
        with pytest.raises(PipelineError):
            approve_job(db_session, job, approver="tester")
        assert db_session.query(MeterEvent).filter(
            MeterEvent.event_key == BOQ_EVENT_KEY.format(id=job.id)
        ).count() == 1

    def test_fail_closed_guaranteed_by_db_constraint(self):
        """fail-closed：tenant_id 为 NOT NULL —— DB 层兜底，「无租户」的 job 行
        根本无法落库，故计量侧的空租户分支不可达（不伪造不可达分支去凑用例）。"""
        assert BoqImportJob.__table__.c.tenant_id.nullable is False


# ─────────────────────── Referral（轨 6）──────────────────────
@pytest.fixture
def make_referral(db_session):
    state: dict[str, list[str]] = {"codes": [], "records": []}

    def _make(*, status: str = "pending",
              inviter: str = TENANT_INVITER,
              invited: str = TENANT_INVITED) -> ReferralRecord:
        code = ReferralCode(
            id=str(uuid.uuid4()),
            tenant_id=inviter,
            code="RF" + uuid.uuid4().hex[:6].upper(),
            is_active=True,
        )
        db_session.add(code)
        db_session.commit()
        db_session.refresh(code)

        rec = ReferralRecord(
            id=str(uuid.uuid4()),
            code_id=code.id,
            inviter_tenant_id=inviter,
            invited_tenant_id=invited,
            status=status,
        )
        db_session.add(rec)
        db_session.commit()
        db_session.refresh(rec)
        state["codes"].append(str(code.id))
        state["records"].append(str(rec.id))
        return rec

    yield _make

    for rid in state["records"]:
        db_session.query(MeterEvent).filter(
            MeterEvent.event_key == REF_EVENT_KEY.format(id=rid)
        ).delete(synchronize_session=False)
        db_session.query(ReferralRecord).filter(
            ReferralRecord.id == rid
        ).delete(synchronize_session=False)
    for cid in state["codes"]:
        db_session.query(ReferralCode).filter(
            ReferralCode.id == cid
        ).delete(synchronize_session=False)
    db_session.commit()


class TestReferralRevenueTrigger:
    def test_negative_no_pending_invite(self, db_session):
        """负向：无 pending 邀请 → 零计量（不能"邀请创建即确认收入"）。"""
        from app.services.referral_service import ReferralService

        before = _count(db_session, REF_METER)
        res = ReferralService(db_session).mark_invite_qualified(TENANT_INVITED)
        assert res["qualified"] is False
        assert _count(db_session, REF_METER) == before

    def test_positive_qualified_emits_meter(self, db_session, make_referral):
        """正向：pending→rewarded（收入确认）→ 计量 +1，归属推荐人 inviter。"""
        from app.services.referral_service import ReferralService

        before = _count(db_session, REF_METER)
        rec = make_referral(status="pending")
        res = ReferralService(db_session).mark_invite_qualified(TENANT_INVITED)

        assert res["qualified"] is True
        assert _count(db_session, REF_METER) == before + 1
        ev = db_session.query(MeterEvent).filter(
            MeterEvent.event_key == REF_EVENT_KEY.format(id=rec.id)
        ).one()
        assert ev.meter_code == REF_METER
        assert ev.subject_type == "referral"
        assert ev.subject_id == str(rec.id)
        assert ev.unit == "reward"
        assert ev.quantity == 1
        # 归属裁定：计量落 inviter（推荐人 = 裂变行为主体），invited 留 metadata 追溯
        assert str(ev.tenant_id) == TENANT_INVITER
        assert ev.metadata_json.get("invited_tenant_id") == TENANT_INVITED

    def test_idempotent_repeat_call(self, db_session, make_referral):
        """幂等：重复 mark_invite_qualified → 不重复计量（已 rewarded 不重复发放）。"""
        from app.services.referral_service import ReferralService

        rec = make_referral(status="pending")
        svc = ReferralService(db_session)
        svc.mark_invite_qualified(TENANT_INVITED)
        second = svc.mark_invite_qualified(TENANT_INVITED)  # 已无 pending

        assert second["qualified"] is True
        assert second["updated"] == 0
        assert db_session.query(MeterEvent).filter(
            MeterEvent.event_key == REF_EVENT_KEY.format(id=rec.id)
        ).count() == 1
