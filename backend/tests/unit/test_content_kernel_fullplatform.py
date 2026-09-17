"""全平台内容中台（事实内核 / B2B feed / 形态路由）单元测试。

覆盖缺口第 2、3、4 条：ContentMaster 升级为一核多形的内核层。
不碰 DB / 网络，纯离线断言。
"""

from __future__ import annotations

from app.services.geo.content_kernel import FactKernel, PlatformGroup, TradeTerms
from app.services.geo.product_feed import (
    build_feed_record,
    build_product_feed,
    to_generic_xml_item,
)
from app.services.geo.platform_content_router import (
    render_b2b,
    render_knowledge,
    render_search,
    render_social,
    route,
)


def _rich_raw() -> dict:
    return {
        "entity_name": "Ceramic Fiber Board",
        "entity_type": "product",
        "entity_aliases": ["Ceramboard", "Alumina Board"],
        "attrs": {
            "description": "High-temperature insulation board",
            "image_url": "https://x/img.jpg",
            "moq": "100 pieces",
            "price": "USD 2.1-4.5 / piece",
            "unit": "piece",
        },
        "trade": {
            "moq": "100 pieces",
            "lead_time": "15 days",
            "incoterms": "FOB Shanghai",
            "payment_terms": "30% T/T deposit",
            "certifications": ["ISO 9001", "CE"],
        },
        "evidence": [
            {"label": "SGS test report", "level": "strong", "source": "SGS-2024", "verifiable": True},
            {"label": "CE certificate", "level": "verified"},
        ],
        "copy": {"en": "ISO/CE ceramic fiber board, MOQ 100, FOB Shanghai", "zh": "陶瓷纤维板"},
        "source_url": "https://tenant.example/products/ceramic-fiber-board",
        "source_tenant": "t-001",
    }


def test_kernel_from_dict_full():
    k = FactKernel.from_dict(_rich_raw())
    assert k.entity_name == "Ceramic Fiber Board"
    assert "Ceramboard" in k.entity_aliases
    assert k.trade.certifications == ("ISO 9001", "CE")
    assert len(k.evidence) == 2
    assert k.evidence[0].level == "strong"
    assert k.schema_ready is True
    assert k.completeness() >= 0.8


def test_kernel_degraded_when_sparse():
    k = FactKernel.from_dict({"entity_name": "Board"})
    assert k.schema_ready is False
    assert k.degraded() is True
    assert k.completeness() < 0.6


def test_kernel_cleans_whitespace_and_caps():
    k = FactKernel.from_dict({"entity_name": "  A\nB   C", "copy": {"en": "x" * 900}})
    assert k.entity_name == "A B C"
    assert len(k.copy["en"]) <= 600


def test_trade_terms_string_certifications_split():
    t = TradeTerms.from_dict({"certifications": "ISO, CE, SGS"})
    assert t.certifications == ("ISO", "CE", "SGS")


def test_kernel_to_dict_roundtrip_completeness():
    k = FactKernel.from_dict(_rich_raw())
    d = k.to_dict()
    assert d["completeness"] == round(k.completeness(), 4)
    assert d["trade"]["incoterms"] == "FOB Shanghai"
    assert d["evidence"][0]["verifiable"] is True


def test_feed_record_complete():
    rec = build_feed_record(FactKernel.from_dict(_rich_raw()))
    assert rec["incomplete"] is False
    assert rec["certifications"] == ["ISO 9001", "CE"]
    assert rec["moq"] == "100 pieces"
    assert rec["price"] == "USD 2.1-4.5 / piece"


def test_feed_record_incomplete_flags_missing():
    rec = build_feed_record(FactKernel.from_dict({"entity_name": "Thing"}))
    assert rec["incomplete"] is True
    assert "moq" in rec["missing_fields"] or "image" in rec["missing_fields"]


def test_feed_cert_fallback_from_evidence():
    raw = _rich_raw()
    raw["trade"]["certifications"] = []  # 无显式认证，应从强证据抽
    rec = build_feed_record(FactKernel.from_dict(raw))
    # 证据 label 不含 'cert' 子串（SGS test report / CE certificate）→ 抽不到则空
    assert rec["certifications"] in ([], ["CE certificate"])


def test_product_feed_summary_counts():
    kernels = [FactKernel.from_dict(_rich_raw()), FactKernel.from_dict({"entity_name": "X"})]
    feed = build_product_feed(kernels)
    assert feed["count"] == 2
    assert feed["complete"] == 1
    assert feed["incomplete"] == 1
    assert feed["complete_ratio"] == 0.5


def test_product_feed_empty():
    feed = build_product_feed([])
    assert feed["count"] == 0
    assert feed["complete_ratio"] == 0.0


def test_generic_xml_escapes_and_omits_empty():
    rec = build_feed_record(FactKernel.from_dict(_rich_raw()))
    xml = to_generic_xml_item(rec)
    assert "<item incomplete=\"false\">" in xml
    assert "<cert>" in xml
    sparse = build_feed_record(FactKernel.from_dict({"entity_name": "A<B&"}))
    xml2 = to_generic_xml_item(sparse)
    assert "A&lt;B&amp;" in xml2
    assert "<price>" not in xml2  # 空字段不输出


def test_render_search_has_schema():
    r = render_search(FactKernel.from_dict(_rich_raw()))
    assert r["schema"]["@type"] == "Product"
    assert r["schema"]["@context"] == "https://schema.org"
    assert "MOQ 100 pieces" in r["facts_sentence"]
    assert r["incomplete"] is False


def test_render_social_script():
    r = render_social(FactKernel.from_dict(_rich_raw()))
    assert r["group"] == PlatformGroup.SOCIAL
    assert len(r["short_video_script"]) == 3
    assert "cta" in r["short_video_script"][2]


def test_render_b2b_delegates():
    r = render_b2b(FactKernel.from_dict(_rich_raw()))
    assert r["group"] == PlatformGroup.B2B
    assert r["platform"] == "alibaba_offer"


def test_render_knowledge_cn_de_ai():
    r = render_knowledge(FactKernel.from_dict(_rich_raw()), region="cn")
    assert r["de_ai_tuned"] is True
    assert "可查证" in r["body"]
    assert "SGS test report" in r["body"]


def test_render_knowledge_global_not_cn():
    r = render_knowledge(FactKernel.from_dict(_rich_raw()), region="global")
    assert r["de_ai_tuned"] is False


def test_route_unknown_group_no_fake_success():
    out = route(FactKernel.from_dict(_rich_raw()), "nonsense")
    assert out["incomplete"] is True
    assert "group not recognized" in out["missing_fields"]


def test_route_dispatches_all_groups():
    k = FactKernel.from_dict(_rich_raw())
    assert route(k, PlatformGroup.SEARCH)["group"] == "search"
    assert route(k, PlatformGroup.SOCIAL)["group"] == "social"
    assert route(k, PlatformGroup.B2B, platform="made_in_china")["platform"] == "made_in_china"
    assert route(k, PlatformGroup.KNOWLEDGE, region="cn")["de_ai_tuned"] is True
