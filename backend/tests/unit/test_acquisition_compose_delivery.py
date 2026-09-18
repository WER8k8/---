# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""compose-next 验收：reply-ingest / translate / wallet-status。"""
from __future__ import annotations

import asyncio
from unittest.mock import patch

from app.api.v1.routes import acquisition as acq_api
from app.services.acquisition import buyer_store, ops_card_store
from app.services.hermes import planner_service as ps


REGISTERED = {
    "accio", "lead", "inquiry", "order", "goodjob_crm", "billing",
    "logistics", "deerflow", "trade_ai_agent", "site_builder", "content",
    "publish", "nurture", "egress",
}


def _clear():
    buyer_store._by_id.clear()
    buyer_store._by_email.clear()
    buyer_store.conflict_alerts.clear()
    ops_card_store._by_id.clear()
    ops_card_store._by_inquiry.clear()


def test_reply_ingest_end_to_end():
    _clear()
    body = acq_api.ReplyIngestRequest(
        tenant_id="t1",
        inquiry_id="INQ-E2E-1",
        channel="whatsapp",
        message="Need 5000 sqm rockwool CIF Jeddah",
        country="SA",
        grade=70,
        owner_user_id="sales_01",
        contact_name="Ahmed",
        company_name="Gulf Insulation",
        email="ahmed@gulf.sa",
        buyer_type="project",
    )
    resp = acq_api.reply_ingest(body)
    assert resp["buyer_id"]
    assert resp["summary"]["负责人"] == "sales_01"
    assert "CIF" in resp["summary"]["联系"] or "INQ" in str(resp["card"])
    assert resp["playbook_tips"]  # SA 工程提醒
    card = ops_card_store.get_by_inquiry("INQ-E2E-1")
    assert card is not None
    assert "Ahmed" in (card.buyer_display or "")
    assert buyer_store.get_by_email("t1", "ahmed@gulf.sa") is not None


def test_reply_ingest_requires_inquiry_id():
    try:
        acq_api.reply_ingest(acq_api.ReplyIngestRequest(tenant_id="t1", inquiry_id=""))
        assert False, "should raise"
    except Exception as e:
        assert "inquiry_id" in str(e).lower() or "400" in str(e) or "required" in str(e).lower()


def test_translate_real_engine():
    # P1-1 已接 LLM 真源：配置引擎时真实机翻（degraded=False），非恒等降级
    from unittest.mock import patch
    from app.services.acquisition import translate_service as ts

    with patch.object(
        ts,
        "_try_llm_translate",
        return_value={
            "translated": "买家你好",
            "provider": "llm:Atria-Dawn-Preview",
            "mock": False,
            "machine_translated": True,
            "evidence_url": "",
        },
    ):
        r = acq_api.acquisition_translate(
            acq_api.TranslateRequest(text="Hello buyer", from_lang="en", to_lang="zh")
        )
    assert r["original"] == "Hello buyer"
    assert r["translated"] == "买家你好"
    assert r["degraded"] is False
    assert r["provider"] == "llm:Atria-Dawn-Preview"
    assert r["machine_translated"] is True


def test_translate_same_lang_not_degraded():
    r = acq_api.acquisition_translate(
        acq_api.TranslateRequest(text="你好", from_lang="zh", to_lang="zh")
    )
    assert r["degraded"] is False


def test_wallet_status_honest_unknown():
    r = acq_api.acquisition_wallet_status(tenant_id="t1")
    assert r["status"] in ("unknown", "error")
    assert r["hard_block_enabled"] is False
    assert r["token_balance"] is None
    assert r["message"]


def test_menu_and_spec_files():
    from pathlib import Path
    wt = Path(__file__).resolve().parents[3]
    menu = (wt / "frontend/admin/src/constants/proShellMenus.ts").read_text(encoding="utf-8")
    assert "acquisition-ops" in menu
    assert "获客作战台" in menu
    router = (wt / "frontend/admin/src/router/index.ts").read_text(encoding="utf-8")
    assert "acquisition-ops" in router
    spec = wt / "docs/compose/spec/acquisition-mobius-chain.md"
    assert spec.exists()
    login = wt / "frontend/admin/src/views/login/index.vue"
    assert login.exists()  # 硬锁


def test_route_prefix_not_doubled_and_auth_required():
    """FIX-30：router 已有 prefix=/acquisition 时外挂 ROUTE_PREFIX 必须为空；接口须挂 get_current_user。"""
    import inspect

    assert getattr(acq_api, "ROUTE_PREFIX", None) == ""
    assert acq_api.router.prefix == "/acquisition"
    # 所有路由 handler 必须声明 current_user 依赖（鉴权硬锁）
    for route in acq_api.router.routes:
        endpoint = getattr(route, "endpoint", None)
        if endpoint is None:
            continue
        params = inspect.signature(endpoint).parameters
        assert "current_user" in params, f"{endpoint.__name__} missing auth dependency"
        assert "get_current_user" in str(params["current_user"].default)


def test_intent_preview_still_works():
    caps = set(ps.FALLBACK_CAPABILITIES) | {
        "lead.search", "lead.score", "prospect.enrich", "outreach.letter",
        "billing.meter", "inquiry.capture", "order.create",
        "document.generate_pi", "crm.sync_stage",
        "document.generate_trade_docs", "logistics.track", "default",
    }
    with patch.object(ps, "_registered_executors", lambda: set(REGISTERED)), \
         patch.object(ps, "known_capabilities", lambda: frozenset(caps)), \
         patch.object(ps, "_recall_skills", return_value=[]), \
         patch.object(ps, "_enrich_with_experience", side_effect=lambda e, d: dict(e.payload or {})):
        body = acq_api.IntentPreviewRequest(
            intent="find_leads", tenant_id="t1", payload={"keyword": "rockwool", "country": "IN"}
        )
        resp = asyncio.new_event_loop().run_until_complete(acq_api.intent_preview(body))
    assert resp.nodes
    assert any(n.approval_required for n in resp.nodes)
