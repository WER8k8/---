"""AI 独立站与多模态营销单元测试。"""

from __future__ import annotations

import pytest
from app.services.ai_site_engine import AISiteEngine
from app.services.ai_multimodal_studio import AIMultimodalStudio


@pytest.mark.asyncio
async def test_ai_landing_page_generation():
    engine = AISiteEngine()
    schema = await engine.generate_landing_page(
        product_name="CNC Laser Cutting Machine",
        product_description="High precision optical fiber laser metal sheet cutting equipment",
        target_industry="Sheet Metal Fabrication",
    )
    assert schema["locale"] == "en"
    assert "hero" in schema["sections"]
    assert "Laser" in schema["meta"]["title"]
    assert len(schema["sections"]["features"]) >= 2
    assert "offers" in schema["seo_json_ld"]


def test_ai_site_multilingual_translation():
    engine = AISiteEngine()
    base_schema = {
        "site_id": "site_123",
        "locale": "en",
        "meta": {"title": "Industrial Valve"},
        "sections": {"hero": {"headline": "Heavy Duty Valve"}},
    }
    es_schema = engine.translate_site_schema(base_schema, "es")
    assert es_schema["locale"] == "es"
    assert "Spanish" in es_schema["meta"]["title"]

    ar_schema = engine.translate_site_schema(base_schema, "ar")
    assert ar_schema["locale"] == "ar"
    assert ar_schema["dir"] == "rtl"


@pytest.mark.asyncio
async def test_multimodal_prompts_and_social():
    studio = AIMultimodalStudio()
    prompt = await studio.generate_image_prompts("Solar Inverter", scene="industrial")
    assert "Solar Inverter" in prompt["positive_prompt"]
    assert "low quality" in prompt["negative_prompt"]

    social = await studio.generate_social_post("Solar Inverter", platform="linkedin")
    assert any("#B2B" in h for h in social["hashtags"])
    assert "Solar Inverter" in social["copywriting"]
