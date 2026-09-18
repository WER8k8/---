# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""P3-4/7/8 + E-2 深接收口测试。"""
from __future__ import annotations

import asyncio
import os

from app.schemas.hermes_orchestration import TaskNode
from app.services.acquisition import ops_card_store
from app.services.acquisition.knowledge_queue import knowledge_queue_store
from app.services.acquisition.risk_rescan import risk_rescan_store
from app.services.acquisition.sanctions_source import list_source_status, screen_subject
from app.services.acquisition.tender_engine import tender_engine
from app.services.hermes.executors import ExecutorRegistry
from app.services.hermes.executors.base import ExecutorContext
from app.services.hermes.executors.trade_ops_executor import TradeOpsExecutor
from app.api.v1.routes import acquisition as acq_api


class _U:
    id = "u"
    username = "t"


def _ctx():
    return ExecutorContext(db=None, tenant_id="demo", plan_id="p")


def setup_function():
    ops_card_store._by_inquiry.clear()
    ops_card_store._by_id.clear()
    risk_rescan_store._by_inquiry.clear()
    tender_engine._by_id.clear()
    os.environ.pop("SANCTIONS_LIST_PATH", None)
    os.environ.pop("SANCTIONS_LIST_URL", None)
    os.environ.pop("SANCTIONS_LIST_INLINE", None)


def test_p34_sanctions_seed_and_blocked():
    st = list_source_status()
    assert st["source"] in ("seed_demo",) or st["configured"] is True
    # 种子名单应能命中
    hit = screen_subject(name="Sanctioned Demo Trading LLC", company="Sanctioned Demo Trading LLC")
    assert hit["result"] == "blocked"
    clear = screen_subject(name="Clean Buyer GmbH", company="Clean Buyer GmbH")
    assert clear["result"] in ("clear", "not_configured")
    # inline 真源配置
    os.environ["SANCTIONS_LIST_INLINE"] = '[{"name":"BadCorp Ltd","level":"blocked","reason":"test"}]'
    st2 = list_source_status()
    assert st2["configured"] is True
    hit2 = screen_subject(company="BadCorp Ltd")
    assert hit2["result"] == "blocked"
    assert hit2["source"].startswith("env:inline") or "inline" in hit2["source"]


def test_p34_risk_rescan_uses_sanctions():
    ops_card_store.materialize(tenant_id="demo", inquiry_id="INQ-SAN-1")
    card = ops_card_store.get_by_inquiry("INQ-SAN-1")
    card.buyer_display = "Sanctioned Demo Trading LLC"
    ops_card_store.update(card)
    os.environ["SANCTIONS_LIST_INLINE"] = '[{"name":"Sanctioned Demo Trading LLC","level":"blocked","reason":"demo"}]'
    rep = risk_rescan_store.report(ops_store=ops_card_store, tenant_id="demo", auto_screen=True)
    assert rep["blocked_count"] >= 1
    assert rep["external_list_configured"] is True
    api = acq_api.acquisition_risk_rescan(tenant_id="demo", current_user=_U())
    assert api["source_status"]["configured"] is True


def test_p37_tender_engine_gate():
    t = tender_engine.upsert(tender_id="TDR-1", inquiry_id="INQ-T1", buyer_name="Distributor Co", amount=50000)
    # 提交投标前资质不齐必须拒
    bad = tender_engine.advance("TDR-1", "tender_submit")
    assert bad["ok"] is False
    assert bad["code"] == "docs_incomplete"
    for doc in ("business_license", "iso_cert", "product_test_report", "project_cases", "bank_account", "factory_video"):
        tender_engine.mark_doc("TDR-1", doc, True)
    ok = tender_engine.advance("TDR-1", "tender_submit")
    assert ok["ok"] is True
    assert ok["stage"] == "tender_submit"
    pay = tender_engine.set_payment("TDR-1", "OA 90 days credit", credit_ok=False)
    assert pay["auto_pi_allowed"] is False
    # API
    api = acq_api.acquisition_tender_view("TDR-1", current_user=_U())
    assert api["qualify_ready"] is True
    adv = acq_api.acquisition_tender_advance(
        acq_api.TenderAdvanceRequest(tender_id="TDR-1", to_stage="evaluation", note="评标中"),
        current_user=_U(),
    )
    assert adv["ok"] is True


def test_p37_trade_ops_tender_and_sanctions_caps():
    caps = TradeOpsExecutor.get_capabilities()
    assert "trade_ops.sanctions_screen" in caps
    assert "trade_ops.tender_advance" in caps
    ex = ExecutorRegistry.get("trade_ops")
    node = TaskNode(
        id="t1",
        executor="trade_ops",
        capability="trade_ops.sanctions_screen",
        input={"company": "Clean Buyer GmbH", "name": "Ahmed"},
    )
    res = asyncio.run(ex.run(node, _ctx()))
    assert res.status == "succeeded"
    assert res.output.get("result") in ("clear", "not_configured", "watch", "blocked")


def test_p38_knowledge_queue_expanded():
    rep = knowledge_queue_store.report(tenant_id="demo")
    assert rep["total"] >= 16
    ids = {i["id"] for i in rep["items"]}
    for extra in ("know-india-playbook", "know-tender-docs", "know-sanctions-screen", "know-scam-fake-watermark"):
        assert extra in ids
    api = acq_api.acquisition_knowledge_queue(tenant_id="demo", current_user=_U())
    assert api["total"] >= 16


def test_e2_read_session_and_topology():
    from app.core.db_sessions import get_read_session, db_topology, read_engine_configured

    topo = db_topology()
    assert topo["primary_configured"] is True
    # 未配读库时诚实回落
    if not read_engine_configured():
        assert topo["read_falls_back_to_primary"] is True
    api = acq_api.acquisition_db_topology(current_user=_U())
    assert "plain_summary" in api
    api2 = acq_api.acquisition_billing_reconcile(tenant_id="demo", current_user=_U(), db=None)
    assert "plain_summary" in api2


def test_e4_sharding_doc_exists():
    from pathlib import Path
    p = Path(__file__).resolve().parents[3] / "docs" / "ops" / "database-sharding-design-E4.md"
    assert p.exists(), p
    text = p.read_text(encoding="utf-8")
    assert "DATABASE_READ_URL" in text
    assert "分片" in text


def test_ops_card_tender_bind_api():
    ops_card_store.materialize(tenant_id="demo", inquiry_id="INQ-TB-1")
    resp = acq_api.ops_card_tender_bind(
        "INQ-TB-1",
        acq_api.TenderUpsertRequest(inquiry_id="INQ-TB-1", buyer_name="Agent Co", project_name="Villa"),
        current_user=_U(),
    )
    assert resp["tender"]["inquiry_id"] == "INQ-TB-1"
    assert resp["card"]["notes"]
