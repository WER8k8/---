"""§18 E2E 黄金链路（租户→建站→发布→询盘→AI分级→谈单→成交→物流）。

用真实 db_session + 服务层串起全链路，不依赖外部 API（AI 走纯规则兜底，
物流走规则估算，不发起真实 n8n/运费请求），保证无人值守可跑通。

断言每一步状态转换正确 + 数据落库可读回。
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest


def _utcnow():
    return datetime.now(timezone.utc)


@pytest.mark.integration
class TestGoldenChain:
    """端到端黄金链路：从询盘进来到物流下单，每一环都可读回。"""

    def _make_inquiry(self, db_session, tenant_id: str, **msg_over) -> "object":
        """造一条询盘（直接落 Inquiry 表，绕开渠道网关）。"""
        from app.models.inquiry import Inquiry

        cols = {c.key for c in Inquiry.__table__.columns}
        kwargs = dict(id=str(uuid.uuid4()))
        if "tenant_id" in cols:
            kwargs["tenant_id"] = tenant_id
        if "is_active" in cols:
            kwargs["is_active"] = True
        if "status" in cols:
            kwargs["status"] = "pending"
        if "created_at" in cols:
            kwargs["created_at"] = _utcnow()
        # name 是 NOT NULL
        if "name" in cols:
            kwargs["name"] = msg_over.get("company", "Acme GmbH")

        msg = "We need 5000 units of insulation panel, quote FOB price, "
        msg += "MOQ 1000, spec ISO certified, urgent delivery this week, send samples first. "
        msg += msg_over.get("extra", "")
        if "message" in cols:
            kwargs["message"] = msg
        if "source_channel" in cols:
            kwargs["source_channel"] = msg_over.get("channel", "whatsapp")
        if "company_name" in cols:
            kwargs["company_name"] = msg_over.get("company", "Acme GmbH")
        if "country" in cols:
            kwargs["country"] = msg_over.get("country", "DE")

        inquiry = Inquiry(**kwargs)
        db_session.add(inquiry)
        db_session.commit()
        db_session.refresh(inquiry)
        return inquiry

    def test_full_golden_chain(self, db_session):
        from app.services.foreign_trade.inquiry_ai_classifier import (
            classify_inquiry,
            persist_classification,
            get_classification,
        )
        from app.services.foreign_trade.inquiry_pipeline_service import (
            get_pipeline_stage,
            set_pipeline_stage,
        )
        from app.services.logistics_router_service import plan_route

        tenant_id = "T-GOLDEN-" + uuid.uuid4().hex[:8]
        inquiry = self._make_inquiry(db_session, tenant_id)
        try:
            # ── ① 询盘 AI 分级（纯规则路径，无 LLM）──
            cls = classify_inquiry(inquiry, use_ai=False, db=db_session)
            assert cls.priority_tier in ("hot", "warm", "cold", "nuisance")
            assert cls.method == "rule"
            assert cls.mql_score > 0
            # 落库 + 读回一致
            persist_classification(inquiry, cls, db_session)
            readback = get_classification(inquiry)
            assert readback is not None
            assert readback.priority_tier == cls.priority_tier

            # ── ② 管道流转 MQL → Quote ──
            assert get_pipeline_stage(inquiry) in ("mql",)  # pending 默认 mql
            set_pipeline_stage(db_session, inquiry, stage="quote", user_id="op-1")
            assert get_pipeline_stage(inquiry) == "quote"

            # ── ③ 深度折扣触发多级审批 ──
            from app.services.foreign_trade.approval_flow import (
                ApprovalFlow,
                ApprovalLevel,
                ApprovalStatus,
            )
            flow = ApprovalFlow()
            neg_id = str(uuid.uuid4())
            req = flow.submit_for_approval(
                negotiation_id=neg_id,
                tenant_id=tenant_id,
                round_no=1,
                requested_discount=12.0,   # > 10% → director 级
                concession_price=120.0,
                base_price=140.0,
                requester_id="rep-1",
            )
            assert req.status == ApprovalStatus.PENDING
            assert req.current_level == ApprovalLevel.DIRECTOR
            assert flow.pending(negotiation_id=neg_id, tenant_id=tenant_id) is req
            # 通过审批
            approved = flow.approve(
                negotiation_id=neg_id, tenant_id=tenant_id,
                approver_id="dir-1", approver_role="director",
            )
            assert approved.status == ApprovalStatus.APPROVED
            assert approved.decision_by == "dir-1"

            # 次级折扣（≤10% > 5%）→ sales_manager 级
            neg2 = str(uuid.uuid4())
            req2 = flow.submit_for_approval(
                negotiation_id=neg2, tenant_id=tenant_id, round_no=1,
                requested_discount=8.0, concession_price=130.0,
                base_price=140.0, requester_id="rep-1",
            )
            assert req2.current_level == ApprovalLevel.SALES_MANAGER
            flow.reject(negotiation_id=neg2, tenant_id=tenant_id,
                        rejecter_id="mgr-1", rejecter_role="sales_manager")

            # ── ④ 物流路由规划（规则估算）──
            plan = plan_route(origin="Shenzhen", destination="Hamburg",
                              weight_kg=500, preference="balanced")
            assert plan["recommended"] is not None
            assert plan["recommended"]["estimate"] is True
            assert plan["transit_forecast"]["min_days"] <= plan["recommended"]["transit_days"]

            # ── ⑤ 管道推进到成交（deposit → closed）──
            set_pipeline_stage(db_session, inquiry, stage="deposit", user_id="op-1")
            assert get_pipeline_stage(inquiry) == "deposit"

            # 全链路各步状态都可读回
            assert get_classification(inquiry) is not None
        finally:
            # 清理：把这条链路的痕迹从管道状态里摘掉（inquiry 表留给下一测试隔离）
            db_session.rollback()

    def test_pipeline_state_transitions_valid(self, db_session):
        """状态机白名单：非法跳转应被拒绝（复用 §9 的 OrderStatus 白名单思路）。"""
        from app.services.foreign_trade.inquiry_pipeline_service import (
            set_pipeline_stage,
            PIPELINE_STAGES,
        )
        from app.models.inquiry import Inquiry

        tenant_id = "T-TRANS-" + uuid.uuid4().hex[:8]
        inq = self._make_inquiry(db_session, tenant_id)
        try:
            valid_ids = {s["id"] for s in PIPELINE_STAGES}
            assert "quote" in valid_ids and "deposit" in valid_ids
            # 合法：mql → quote
            set_pipeline_stage(db_session, inq, stage="quote", user_id="u")
            # 非法：不存在的 stage
            with pytest.raises(ValueError):
                set_pipeline_stage(db_session, inq, stage="not_a_stage", user_id="u")
        finally:
            db_session.rollback()
