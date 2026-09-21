# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""
获客全链路极智升维单元测试集 (Unit Tests for Acquisition Pipeline Upgrade)。
"""
from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.services.acquisition.buyer_360_enrichment import Buyer360EnrichmentEngine
from app.services.acquisition.ai_pitch_studio import AIPitchStudio
from app.services.acquisition.cadence_engine import OutboundCadenceEngine
from app.services.acquisition.objection_copilot import ObjectionCopilot
from app.api.v1.routes.acquisition_pipeline import router as acq_router


def test_buyer_360_enrichment_tier1_contractor():
    res = Buyer360EnrichmentEngine.enrich_buyer(
        company_name="Al Fozan Industrial Group",
        country="SA",
        industry_hint="stone",
    )
    assert res["tier_code"] == "T1"
    assert "Jeddah" in res["port_intelligence"]["primary_ports"][0]
    assert len(res["buying_committee"]) >= 3
    assert res["sanctions_compliance"]["passed"] is True
    assert res["product_intelligence"]["hs_code"] == "6802.91.00"


def test_buyer_360_enrichment_sanction_detection():
    res = Buyer360EnrichmentEngine.enrich_buyer(
        company_name="Denied Sanctioned Entity Ltd",
        country="SA",
    )
    assert res["sanctions_compliance"]["passed"] is False
    assert res["sanctions_compliance"]["flagged_entity"] is True


def test_ai_pitch_studio_multilingual():
    # 测试英语
    en_res = AIPitchStudio.generate_pitch(
        company_name="Turner Construction",
        country="United States",
        product_category="Porcelain Tiles",
        language="en",
        research_level="basic",
    )
    assert "Turner Construction" in en_res["channel_artifacts"]["cold_email"]["body"]
    assert "Hi " in en_res["channel_artifacts"]["whatsapp_hook"]["text"]

    # 测试阿拉伯语
    ar_res = AIPitchStudio.generate_pitch(
        company_name="Al Fozan",
        country="Saudi Arabia",
        product_category="الرخام والجرانيت",
        language="ar",
        research_level="osint",
    )
    assert ar_res["language"] == "ar"
    assert "SABER" in ar_res["channel_artifacts"]["cold_email"]["subject"]
    assert "مرحباً" in ar_res["channel_artifacts"]["whatsapp_hook"]["text"]


def test_ai_pitch_studio_research_gate_none():
    res = AIPitchStudio.generate_pitch(
        company_name="Cold Lead Corp",
        research_level="none",
        language="en",
    )
    assert res["research_gate"]["personalized_allowed"] is False


def test_cadence_engine_7_touches():
    plan = OutboundCadenceEngine.generate_cadence_plan(
        company_name="Emaar Properties",
        country="AE",
        product_category="Marble Slabs",
    )
    assert plan["total_touches"] == 7
    assert plan["cadence_cycle_days"] == 30
    assert len(plan["touches"]) == 7
    assert plan["touches"][0]["day_offset"] == 1
    assert plan["touches"][-1]["day_offset"] == 30
    assert "Dubai" in plan["timezone_intelligence"]["tz_name"]


def test_objection_copilot_scenarios():
    all_objs = ObjectionCopilot.list_all_objections()
    assert len(all_objs) == 8

    # 测试价格高抗拒
    price_sol = ObjectionCopilot.get_objection_solution("price_high")
    assert "Target Price" in price_sol["name_cn"] or "价格偏高" in price_sol["name_cn"]
    assert "Value Engineering" in price_sol["response_en"]
    assert len(price_sol["bottom_line_rules"]) >= 2

    # 测试索要账期抗拒
    oa_sol = ObjectionCopilot.get_objection_solution("long_oa")
    assert "Sinosure" in oa_sol["response_en"] or "L/C" in oa_sol["response_en"]


def test_acquisition_pipeline_api_routes():
    app = FastAPI()
    app.include_router(acq_router, prefix="/api/v1")
    client = TestClient(app)

    # 1. 360 画像
    r1 = client.post(
        "/api/v1/acquisition-pipeline/enrich-buyer",
        json={"company_name": "Al Rajhi Building Corp", "country": "SA", "industry_hint": "stone"},
    )
    assert r1.status_code == 200
    assert r1.json()["data"]["tier_code"] in ["T1", "T2"]

    # 2. 破冰话术
    r2 = client.post(
        "/api/v1/acquisition-pipeline/generate-pitch",
        json={"company_name": "Al Rajhi", "country": "Saudi Arabia", "language": "ar"},
    )
    assert r2.status_code == 200
    assert r2.json()["data"]["language"] == "ar"

    # 3. 7 步节奏
    r3 = client.post(
        "/api/v1/acquisition-pipeline/cadence-plan",
        json={"company_name": "Al Rajhi", "country": "SA"},
    )
    assert r3.status_code == 200
    assert r3.json()["data"]["total_touches"] == 7

    # 4. 抗拒列表
    r4 = client.get("/api/v1/acquisition-pipeline/objections")
    assert r4.status_code == 200
    assert len(r4.json()["data"]["objections"]) == 8

    # 5. 抗拒助攻
    r5 = client.post(
        "/api/v1/acquisition-pipeline/objection-assist",
        json={"objection_key": "quality_cert"},
    )
    assert r5.status_code == 200
    assert "ASTM" in r5.json()["data"]["response_en"] or "SGS" in r5.json()["data"]["response_en"]

    # 6. 一键 BOQ 核价
    r6 = client.post(
        "/api/v1/acquisition-pipeline/handoff-to-quote",
        json={"buyer_name": "Al Rajhi", "country": "SA", "product_category": "granite"},
    )
    assert r6.status_code == 200
    assert r6.json()["data"]["material_type"] == "granite"
    assert "/client/export-quote" in r6.json()["data"]["recommended_route"]
