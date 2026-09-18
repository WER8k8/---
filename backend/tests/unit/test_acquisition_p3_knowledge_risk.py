# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""P3-4 制裁重扫 + P3-8 知识队列。"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.api.v1.routes import acquisition as acq_api
from app.services.acquisition import ops_card_store
from app.services.acquisition.knowledge_queue import KnowledgeQueueStore
from app.services.acquisition.risk_rescan import RiskRescanStore, RiskScanRecord


class _User:
    id = "u1"
    username = "tester"


def _user() -> _User:
    return _User()


def setup_function():
    ops_card_store._by_inquiry.clear()
    ops_card_store._by_id.clear()


def test_knowledge_queue_seed_and_mark():
    store = KnowledgeQueueStore()
    rep = store.report(tenant_id="demo")
    assert rep["total"] >= 6
    assert rep["pending_count"] >= 6
    assert "下一题" in rep["plain_summary"] or "待读" in rep["plain_summary"]
    first = rep["next_item"]["id"]
    r = store.mark_done(first, by="sales1")
    assert r["ok"] is True
    rep2 = store.report(tenant_id="demo")
    assert rep2["done_count"] >= 1
    assert rep2["pending_count"] == rep["pending_count"] - 1
    # 重复标记
    r2 = store.mark_done(first)
    assert r2["code"] in ("already_done", "done")
    # API
    api = acq_api.acquisition_knowledge_queue(tenant_id="demo", current_user=_user())
    assert api["total"] >= 6
    mark = acq_api.acquisition_knowledge_mark(
        acq_api.KnowledgeMarkRequest(item_id=api["items"][-1]["id"], action="done"),
        current_user=_user(),
    )
    assert mark["ok"] is True


def test_risk_rescan_never_and_overdue():
    ops_card_store.materialize(tenant_id="demo", inquiry_id="INQ-R1", grade="A", score=85)
    card = ops_card_store.get_by_inquiry("INQ-R1")
    card.buyer_display = "Ahmed @ SA Project"
    card.risk_flags = ["sanctions_watch"]
    ops_card_store.update(card)

    store = RiskRescanStore()
    rep = store.report(ops_store=ops_card_store, tenant_id="demo", rescan_days=90, external_list_configured=False)
    assert rep["total_tracked"] >= 1
    assert rep["never_scanned"] >= 1
    assert "未接入" in rep["source_plain"] or "人工" in rep["source_plain"] or "种子" in rep["source_plain"] or "未配置" in rep["source_plain"]
    assert "不编造" in rep["source_plain"] or "为准" in rep["source_plain"]

    # 标记已扫
    store.mark_scanned("INQ-R1", result="watch", source="manual", note="海关名单无命中但保留观察")
    rep2 = store.report(ops_store=ops_card_store, tenant_id="demo", rescan_days=90)
    assert rep2["never_scanned"] == 0
    item = next(i for i in rep2["items"] if i["inquiry_id"] == "INQ-R1")
    assert item["status"] == "ok"
    assert item["last_scan_result"] == "watch"

    # 人为过期
    rec = store._by_inquiry["INQ-R1"]
    rec.last_scan_at = (datetime.now(timezone.utc) - timedelta(days=200)).isoformat()
    rep3 = store.report(ops_store=None, tenant_id="demo", rescan_days=90)
    item3 = next(i for i in rep3["items"] if i["inquiry_id"] == "INQ-R1")
    assert item3["status"] == "overdue"
    assert item3["due"] is True

    # API
    api = acq_api.acquisition_risk_rescan(tenant_id="demo", current_user=_user())
    assert "plain_summary" in api
    mark = acq_api.acquisition_risk_rescan_mark(
        acq_api.RiskScanRequest(inquiry_id="INQ-R2", result="clear", source="manual"),
        current_user=_user(),
    )
    assert mark["ok"] is True


def test_dealer_playbook_and_dictionary_v1():
    from app.services.acquisition import playbook_store
    from app.services.acquisition.orchestration_dictionary import DICTIONARY, dictionary_plain_summary

    tips = playbook_store.tips_for("GLOBAL", buyer_type="distributor")
    assert any("经销商" in t or "账期" in t or "资质" in t for t in tips)
    tips2 = playbook_store.tips_for("GLOBAL", buyer_type="tender")
    assert any("招投标" in t or "标书" in t or "资质" in t for t in tips2)

    ids = {d["id"] for d in DICTIONARY}
    assert "route-dealer-tender" in ids
    assert len(DICTIONARY) >= 9
    assert "航道" in dictionary_plain_summary()


def test_production_gates_script_reports_honestly():
    import os
    import sys
    from pathlib import Path

    backend = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(backend))
    from scripts.verify_acquisition_production_gates import check_production_gates

    os.environ.pop("PIPELINE_GATES_ENABLED", None)
    os.environ.pop("ACQ_HARD_BLOCK_TOKEN", None)
    os.environ["LIBRETRANSLATE_ALLOW_DEV_STUB"] = "1"
    os.environ["LIBRETRANSLATE_URL"] = "http://127.0.0.1:8098"
    out = check_production_gates()
    assert "plain_summary" in out
    assert out["ready_for_production"] is False  # stub + gates off → 不可宣称上线
    ids = {c["id"] for c in out["checks"]}
    assert "translate" in ids and "human_gate" in ids and "wallet_block" in ids
    stub = next(c for c in out["checks"] if c["id"] == "translate")
    assert "mock" in stub["plain"] or "桩" in stub["plain"]
