import pytest


"""ECommerceCrawlers registry, compliance & sidecar tests."""

import os

from app.services.crawlers.ecommerce_crawlers_compliance import assert_spider_compliance
from app.services.crawlers.ecommerce_crawlers_registry import recipe_by_id, registry_payload
from app.services.crawlers.ecommerce_crawlers_sidecar import (
    ecommerce_crawlers_sidecar_status,
    run_spider,
)


def test_registry_expanded_and_social_restricted():
    payload = registry_payload()
    ids = {x["id"] for x in payload["items"]}
    assert "baidu_keyword" in ids
    assert "wechat" in ids
    assert "zhihu" in ids
    assert "spider_flood_dir" in ids
    assert recipe_by_id("wechat").compliance == "social_restricted"
    assert recipe_by_id("spider_flood_dir").compliance == "platform_blocked"
    blocked = [i for i in payload["items"] if not i["callable"]]
    assert any(i["id"] == "spider_flood_dir" for i in blocked)


def test_platform_blocked_spider():
    out = run_spider("spider_flood_dir", params={})
    assert out["ok"] is False
    assert out["error_code"] == "SPIDER_PLATFORM_BLOCKED"


def test_social_spider_requires_gates(monkeypatch):
    monkeypatch.setenv("ECOMMERCE_CRAWLERS_URL", "http://127.0.0.1:9999")
    monkeypatch.delenv("ECOMMERCE_SOCIAL_SPIDERS_ENABLED", raising=False)
    out = run_spider("wechat", params={}, operator_role="admin")
    assert out["ok"] is False
    assert out["error_code"] == "SOCIAL_SPIDERS_NOT_ENABLED"


def test_social_spider_with_gates_but_no_sidecar(monkeypatch):
    monkeypatch.setenv("ECOMMERCE_SOCIAL_SPIDERS_ENABLED", "1")
    monkeypatch.setenv("ECOMMERCE_SPIDER_ENABLE_WECHAT", "1")
    monkeypatch.delenv("ECOMMERCE_CRAWLERS_URL", raising=False)
    out = run_spider(
        "wechat",
        params={},
        operator_role="tenant_admin",
        tenant_consent=True,
        compliance_acknowledged=True,
        purpose="公开文章行业监测用途说明",
    )
    assert out["ok"] is False
    assert out["error_code"] == "ECOMMERCE_CRAWLERS_NOT_CONFIGURED"


def test_restricted_taobao_requires_consent(monkeypatch):
    monkeypatch.setenv("ECOMMERCE_CRAWLERS_URL", "http://127.0.0.1:9999")
    monkeypatch.setenv("ECOMMERCE_SPIDER_ENABLE_TAOBAO", "1")
    recipe = recipe_by_id("taobao")
    decision = assert_spider_compliance(
        recipe,
        params={},
        tenant_id="t1",
        operator_role="tenant_admin",
        tenant_consent=False,
        compliance_acknowledged=True,
        purpose="绔炲搧浠风洏鐩戞祴",
    )
    assert decision.verdict == "deny"
    assert decision.error_code == "SPIDER_TENANT_CONSENT_REQUIRED"


def test_run_spider_not_configured(monkeypatch):
    monkeypatch.delenv("ECOMMERCE_CRAWLERS_URL", raising=False)
    out = run_spider(
        "baidu_keyword",
        params={"keyword": "x"},
        purpose="seo_probe",
        operator_role="admin",
    )
    assert out["ok"] is False
    assert out["error_code"] == "ECOMMERCE_CRAWLERS_NOT_CONFIGURED"


def test_sidecar_status_not_configured(monkeypatch):
    monkeypatch.delenv("ECOMMERCE_CRAWLERS_URL", raising=False)
    st = ecommerce_crawlers_sidecar_status()
    assert st["configured"] is False


def test_baidu_requires_purpose():
    recipe = recipe_by_id("baidu_keyword")
    decision = assert_spider_compliance(
        recipe,
        params={},
        tenant_id=None,
        operator_role="admin",
        purpose=None,
    )
    assert decision.verdict == "deny"
    assert decision.error_code == "SPIDER_PURPOSE_REQUIRED"
