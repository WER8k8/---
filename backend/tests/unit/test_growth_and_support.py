"""获客闭环与海外客服单元测试。"""

from __future__ import annotations

from app.services.growth_loop_service import GrowthLoopEngine
from app.services.omnichannel_support_service import OmnichannelSupportService


def test_growth_loop_campaign():
    engine = GrowthLoopEngine()
    res = engine.run_campaign_pipeline(
        tenant_id="00000000-0000-0000-0000-000000000001",
        campaign_name="Q3 Europe Machinery Push",
        target_industry="Machinery",
        seed_keywords=["extruder", "molding"],
    )
    # 求真契约：无真实线索源数据时如实降级，不伪造线索
    assert res["status"] == "no_data"
    assert res["degraded"] is True
    assert res["pipeline_stages"]["spider_harvest"]["status"] == "not_configured"
    assert res["pipeline_stages"]["ai_intent_scoring"]["high_value_leads"] == []


def test_growth_loop_campaign_with_real_leads(monkeypatch):
    from app.services import growth_loop_service

    monkeypatch.setattr(
        growth_loop_service,
        "_query_real_leads",
        lambda tenant_id, limit=10: [
            {
                "id": "1",
                "company": "Acme Tiles GmbH",
                "country": "DE",
                "email": "buyer@acme.de",
                "score": 0.0,
                "source": "inquiry",
            }
        ],
    )
    res = GrowthLoopEngine().run_campaign_pipeline(
        tenant_id="00000000-0000-0000-0000-000000000002",
        campaign_name="Q3 Europe Machinery Push",
        target_industry="Machinery",
        seed_keywords=["extruder"],
    )
    assert res["status"] == "running"
    assert res["degraded"] is False
    assert res["pipeline_stages"]["spider_harvest"]["status"] == "completed"
    assert res["pipeline_stages"]["ai_intent_scoring"]["high_value_leads"][0]["email"] == "buyer@acme.de"


def test_omnichannel_support():
    svc = OmnichannelSupportService()
    res = svc.handle_visitor_inquiry(
        tenant_id="00000000-0000-0000-0000-000000000001",
        channel="whatsapp",
        sender_id="+14155552671",
        message="What is the price for 100 units?",
    )
    assert res["lead_captured"] is True
    assert "pricing" in res["reply"] or "quote" in res["reply"]
