# -*- coding: utf-8 -*-
"""谷歌商机大数据与 AI 拓客引擎自动化测试。"""

import pytest
from app.services.google_intelligence import (
    GoogleB2BDorkingEngine,
    GoogleEmailValidator,
    GlobalTradeRadarEngine,
    GoogleEEATSchemaEngine,
)


def test_google_dorking_matrix():
    res = GoogleB2BDorkingEngine.generate_dork_matrix("marble slab", "United Arab Emirates")
    assert res["keyword"] == "marble slab"
    assert res["target_country"] == "United Arab Emirates"
    assert len(res["dorks"]) == 4
    for dork in res["dorks"]:
        assert "google.com/search?q=" in dork["google_search_url"]
        assert "marble slab" in dork["query"]


def test_google_email_validator():
    # 1. 正常企业邮箱
    res_corp = GoogleEmailValidator.validate_email("buyer@saint-gobain.com")
    assert res_corp["is_valid_format"] is True
    assert res_corp["domain_type"] == "corporate_buyer"
    assert res_corp["score"] >= 90
    assert res_corp["recommendation"] == "safe_to_send"

    # 2. 一次性垃圾邮箱拦截
    res_disp = GoogleEmailValidator.validate_email("fake_user@mailinator.com")
    assert res_disp["deliverable"] is False
    assert res_disp["domain_type"] == "disposable"
    assert res_disp["recommendation"] == "blocked"

    # 3. 语法畸形拦截
    res_bad = GoogleEmailValidator.validate_email("invalid@@domain..com")
    assert res_bad["is_valid_format"] is False
    assert res_bad["deliverable"] is False


def test_google_customs_trade_flow_radar():
    # 陶瓷砖 HS 6907
    radar_tile = GlobalTradeRadarEngine.get_market_intelligence("porcelain floor tiles")
    assert radar_tile["matched_hs_chapter"] == "6907"
    assert len(radar_tile["intelligence"]["top_importing_regions"]) >= 3
    assert "20GP" in radar_tile["intelligence"]["container_rules"]

    # 钢结构 HS 7308
    radar_steel = GlobalTradeRadarEngine.get_market_intelligence("structural steel beam")
    assert radar_steel["matched_hs_chapter"] == "7308"


def test_google_eeat_schema_engine():
    schema = GoogleEEATSchemaEngine.generate_product_schema(
        brand_name="YouDing",
        product_name="Pure White Calacatta Marble",
        description="Luxury architectural project marble tiles",
        image_url="https://www.youding.com/calacatta.jpg",
        price_usd=75.0,
        moq=200,
        hs_code="6802.91.00",
    )
    assert schema["@context"] == "https://schema.org"
    assert schema["@type"] == "Product"
    assert schema["name"] == "Pure White Calacatta Marble"
    assert schema["offers"]["priceCurrency"] == "USD"
    assert schema["offers"]["eligibleQuantity"]["minValue"] == 200

    faq = GoogleEEATSchemaEngine.generate_faq_schema("Calacatta Marble")
    assert faq["@type"] == "FAQPage"
    assert len(faq["mainEntity"]) == 3
