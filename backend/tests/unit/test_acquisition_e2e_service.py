# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""端到端服务路径：意图预览 + 回复进卡（内存层，傻子都行验收）。"""
from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch

from app.services.acquisition import buyer_store, ops_card_store, playbook_store
from app.services.hermes import planner_service as ps
from app.api.v1.routes import acquisition as acq_api


REGISTERED = {
    "site_builder", "content", "deerflow", "publish", "nurture", "egress",
    "accio", "lead", "trade_ai_agent", "inquiry", "order", "goodjob_crm",
    "billing", "logistics", "trade_ops", "commerce_ops", "platform_ops",
    "module_matrix", "content_deep", "outreach_loop",
}


def _patch_env(monkeypatch):
    monkeypatch.setattr(ps, "_registered_executors", lambda: set(REGISTERED))
    caps = set(ps.FALLBACK_CAPABILITIES)
    caps.update({
        "lead.search", "lead.score", "prospect.enrich", "outreach.letter",
        "inquiry.capture", "order.create", "document.generate_pi",
        "billing.meter", "crm.sync_stage", "document.generate_trade_docs",
        "logistics.track", "site.generate", "content.create", "seo.optimize",
        "publish.multi", "nurture.create", "egress.assign", "research.deep_run",
        "default",
        "trade_ops.pi_precheck", "commerce_ops.crm_pipeline",
        "platform_ops.system_health", "module_matrix.matrix.inspect",
        "content_deep.knowledge", "outreach_loop.gate",
    })
    monkeypatch.setattr(ps, "known_capabilities", lambda: frozenset(caps))


def test_intent_preview_find_leads(monkeypatch):
    _patch_env(monkeypatch)
    body = acq_api.IntentPreviewRequest(
        intent="find_leads",
        tenant_id="t1",
        payload={"keyword": "rockwool", "country": "IN"},
    )

    async def _run():
        with patch.object(ps, "_recall_skills", return_value=[]), \
             patch.object(ps, "_enrich_with_experience", side_effect=lambda e, d: dict(e.payload or {})):
            return await acq_api.intent_preview(body)

    resp = asyncio.new_event_loop().run_until_complete(_run())
    assert resp.source in ("L1_template", "L1_hybrid", "L2_llm", "L3_minimal")
    assert resp.nodes
    assert any(n.capability == "outreach.letter" and n.approval_required for n in resp.nodes)
    # 印度 Playbook 提醒
    assert any("定金" in t or "全款" in t for t in resp.playbook_tips)


def test_reply_ingest_builds_ops_card():
    buyer_store._by_id.clear()
    buyer_store._by_email.clear()
    ops_card_store._by_id.clear()
    ops_card_store._by_inquiry.clear()

    b = acq_api.BuyerUpsertRequest(
        tenant_id="t1",
        email="buyer@gulf.com",
        contact_name="Ahmed",
        contact_gender="male",
        company_name="Gulf Insulation",
        company_country="SA",
        buyer_type="project",
    )
    up = acq_api.buyers_upsert(b)
    assert up["is_new"] is True
    bid = up["buyer"]["buyer_id"]

    card = acq_api.ops_card_materialize(
        acq_api.OpsCardMaterializeRequest(
            tenant_id="t1",
            inquiry_id="INQ-001",
            buyer_id=bid,
            owner_user_id="u1",
            grade=70,
        )
    )
    assert card["summary"]["负责人"] == "u1"
    assert "Ahmed" in card["card"].get("buyer_display", "")

    t = acq_api.ops_card_touch(
        "INQ-001",
        acq_api.OpsCardTouchRequest(channel="inbound", summary="需要 CIF 吉达 5000㎡"),
    )
    assert "CIF" in t["summary"]["联系"]

    n = acq_api.ops_card_note(
        "INQ-001",
        acq_api.OpsCardNoteRequest(body="客户要求 SASO 认证"),
    )
    assert "SASO" in n["summary"]["交代"]

    p = acq_api.playbooks_tips(country="IN", buyer_type="new")
    assert p["tips"]


def test_intent_preview_fulfillment(monkeypatch):
    _patch_env(monkeypatch)
    body = acq_api.IntentPreviewRequest(
        intent="fulfillment",
        tenant_id="t1",
        payload={"message": "出 PI", "incoterms": "CIF"},
    )

    async def _run():
        with patch.object(ps, "_recall_skills", return_value=[]), \
             patch.object(ps, "_enrich_with_experience", side_effect=lambda e, d: dict(e.payload or {})):
            return await acq_api.intent_preview(body)

    resp = asyncio.new_event_loop().run_until_complete(_run())
    caps = [n.capability for n in resp.nodes]
    assert "document.generate_pi" in caps
    assert any(n.approval_required for n in resp.nodes)
