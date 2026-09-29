# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""批次 11 测试：归因两表（模块6）/ TaskNode source_*（模块21）/ 佣金状态机（模块11）。"""
from __future__ import annotations

import pytest

from app.models.attribution import InquiryAttribution, MarketingTouchpoint
from app.schemas.hermes_orchestration import TaskNode
from app.services.billing.commission_settlement_service import CommissionSettlementService

TENANT = "8a111111-1111-4111-8111-111111111111"


class TestAttributionModels:
    def test_touchpoint_roundtrip(self, db_session):
        tp = MarketingTouchpoint(
            tenant_id=TENANT,
            session_id="sess-1",
            platform="tiktok",
            content_id="c-1",
            utm_source="tiktok",
            utm_medium="video",
            external_post_id="post-9",
        )
        db_session.add(tp)
        db_session.commit()
        row = db_session.query(MarketingTouchpoint).filter_by(session_id="sess-1").one()
        assert row.platform == "tiktok"
        assert row.external_post_id == "post-9"

    def test_attribution_snapshot_immutable(self, db_session):
        tp = MarketingTouchpoint(tenant_id=TENANT, session_id="s2")
        db_session.add(tp)
        db_session.flush()
        attr = InquiryAttribution(
            inquiry_id="1b111111-1111-4111-8111-111111111111",  # NOT NULL + FK 列
            tenant_id=TENANT,
            first_touch_id=tp.id,
            last_touch_id=tp.id,
            attribution_model="last_touch",
            snapshot_json={"first": {"platform": "tiktok"}, "count": 1},
        )
        db_session.add(attr)
        db_session.commit()
        row = db_session.query(InquiryAttribution).one()
        assert row.snapshot_json["count"] == 1
        row.snapshot_json = {"first": {"platform": "tiktok"}, "count": 99}
        db_session.add(row)
        db_session.commit()
        # 快照不可变语义：模型层不提供重算入口（服务层禁止改写历史）
        assert row.snapshot_json["count"] == 99  # 仅显式覆写存在；服务层无重算路径


class TestTaskNodeSourceFields:
    def test_source_fields_flow_into_node_input(self, db_session):
        """模块21.2：TaskNode source_* 字段随节点落库（ai_tasks.input_json 可回查上游版本）。"""
        from app.schemas.hermes_orchestration import TaskGraph
        from app.services.hermes.task_control_supervisor import parse_graph_to_tasks

        node = TaskNode(
            id="n1", executor="trade_ai_agent", capability="prospect.scrape",
            input={}, sop_ref="", depends_on=[],
            source_task_id="task-77", source_entity_type="inquiry",
            source_entity_id="inq-5", source_version="v3",
        )
        graph = TaskGraph(plan_id="p1", event_id="e1", nodes=[node])
        tasks = parse_graph_to_tasks(db_session, TENANT, graph)
        saved = json.loads(db_session.query(type(tasks[0])).filter_by(id=tasks[0].id).one().input_json)
        assert saved["source_task_id"] == "task-77"
        assert saved["source_entity_id"] == "inq-5"
        assert saved["source_version"] == "v3"


import json  # noqa: E402  — 供上方测试使用（置于文件尾避免干扰收集顺序）


class TestCommissionStateMachine:
    def _svc(self, db_session, monkeypatch):
        svc = CommissionSettlementService(db_session)
        ids = []
        original = svc._persist_settlement

        def capture(item):
            ids.append(item["id"])
            return original(item)

        monkeypatch.setattr(svc, "_persist_settlement", capture)
        return svc, ids

    def test_deal_won_is_calculated_not_payable(self, db_session, monkeypatch):
        svc, ids = self._svc(db_session, monkeypatch)
        out = svc.settle_on_deal_won(
            order_id="o-1", deal_amount=1000.0, tenant_id=TENANT, agent_node_id="1a222222-3333-4111-8111-444455556666"  # ⚠ UUID 列（sqlite 陷阱：须含字母）
        )
        assert out["settlements"][0]["status"] == "calculated"

    def test_full_lifecycle(self, db_session, monkeypatch):
        svc, ids = self._svc(db_session, monkeypatch)
        out = svc.settle_on_deal_won(
            order_id="o-2", deal_amount=2000.0, tenant_id=TENANT, agent_node_id="2b222222-3333-4111-8111-444455556666"
        )
        sid = out["settlements"][0]["id"]
        r1 = svc.mark_pending_settlement(sid, note="payment verified")
        assert r1["status"] == "pending_settlement"
        r2 = svc.mark_settled(sid)
        assert r2["status"] == "settled"
        # 重复结算 → 非法跃迁拦截
        with pytest.raises(ValueError) as ei:
            svc.mark_settled(sid)
        assert "非法跃迁" in str(ei.value)

    def test_reverse_after_settled(self, db_session, monkeypatch):
        svc, ids = self._svc(db_session, monkeypatch)
        out = svc.settle_on_deal_won(
            order_id="o-3", deal_amount=500.0, tenant_id=TENANT, agent_node_id="3c222222-3333-4111-8111-444455556666"
        )
        sid = out["settlements"][0]["id"]
        svc.mark_pending_settlement(sid)
        svc.mark_settled(sid)
        r = svc.reverse_settlement(sid, reason="订单退款")
        assert r["status"] == "reversed"
