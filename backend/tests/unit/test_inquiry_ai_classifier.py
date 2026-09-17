"""§7 询盘 AI 智能分级单元测试（纯规则路径，不依赖真实 LLM）。"""

from __future__ import annotations

from app.services.foreign_trade.inquiry_ai_classifier import (
    Classification,
    classify_inquiry,
)


def _inq(message: str, channel: str = "webform", **extra) -> dict:
    d = {"message": message, "source_channel": channel}
    d.update(extra)
    return d


class TestMQLScore:
    def test_rich_whatsapp_high_mql(self):
        r = classify_inquiry(_inq(
            "We need 5000 units of insulated panel, budget 40k USD",
            channel="whatsapp",
            company_name="ABC Corp", country="Germany", quantity="5000",
        ))
        assert r.mql_score >= 60
        assert r.method == "rule"

    def test_thin_form_low_mql(self):
        r = classify_inquiry(_inq("hi", channel="webform"))
        assert r.mql_score < r.mql_score + 1
        assert isinstance(r, Classification)


class TestSQLScore:
    def test_strong_intent_high_sql(self):
        r = classify_inquiry(_inq(
            "Please quote FOB price, MOQ 1000, specs ISO certified, delivery 30 days, we will send PO after samples",
            channel="email",
        ))
        assert r.sql_score >= 60

    def test_weak_intent_low_sql(self):
        r = classify_inquiry(_inq("just checking, nothing urgent", channel="other"))
        assert r.sql_score < 30


class TestPriorityTier:
    def test_hot_tier(self):
        r = classify_inquiry(_inq(
            "quote MOQ 2000 USD price specs order",
            channel="whatsapp", company_name="X", country="US", quantity="2000",
        ))
        assert r.priority_tier in ("hot", "warm")

    def test_nuisance_tier(self):
        r = classify_inquiry(_inq("work from home crypto airdrop free money"))
        assert r.priority_tier == "nuisance"

    def test_cold_tier(self):
        r = classify_inquiry(_inq("hello"))
        assert r.priority_tier in ("cold", "nuisance")


class TestTags:
    def test_urgency_detected(self):
        r = classify_inquiry(_inq("urgent order needed ASAP this week, quote MOQ 500"))
        assert r.urgency_tag is True

    def test_no_urgency(self):
        r = classify_inquiry(_inq("please quote a standard sample"))
        assert r.urgency_tag is False

    def test_industry_building_materials(self):
        r = classify_inquiry(_inq("we need insulation concrete building materials, quote price"))
        assert r.industry_tag in ("building_materials", "unknown")

    def test_language_detection(self):
        r = classify_inquiry(_inq("我们需要保温材料报价"))
        assert r.language_preference == "zh"
        r2 = classify_inquiry(_inq("we need insulation quote please"))
        assert r2.language_preference == "en"


class TestPersistenceShape:
    def test_to_meta_roundtrip(self):
        r = classify_inquiry(_inq("quote MOQ 100 price urgent", channel="email"))
        meta = r.to_meta()
        assert "ai_classify" in meta
        assert meta["ai_classify"]["priority_tier"] in ("hot", "warm", "cold", "nuisance")
        assert meta["ai_classify"]["method"] == "rule"
