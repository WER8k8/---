"""ECommerceCrawlers smart layer tests."""

from app.services.crawlers.ecommerce_crawlers_smart import (
    build_panel,
    quick_run,
    resolve_spider_id,
)


def test_resolve_preset_aliases():
    assert resolve_spider_id("baidu") == "baidu_keyword"
    assert resolve_spider_id("seo") == "baidu_keyword"
    assert resolve_spider_id("qichacha") == "qichacha"


def test_build_panel_has_modules():
    panel = build_panel()
    assert panel["headline"] == "数据采集旁路"
    assert len(panel["modules"]) >= 3
    assert panel["usage_tips"]


def test_quick_run_not_configured(monkeypatch):
    monkeypatch.delenv("ECOMMERCE_CRAWLERS_URL", raising=False)
    out = quick_run("baidu", keyword="测试词", operator_role="admin")
    assert out["ok"] is False
    assert out.get("message_zh")


def test_quick_run_admin_auto_consent_for_restricted(monkeypatch):
    monkeypatch.setenv("ECOMMERCE_CRAWLERS_URL", "http://127.0.0.1:9999")
    monkeypatch.setenv("ECOMMERCE_SPIDER_ENABLE_TAOBAO", "1")
    out = quick_run(
        "taobao",
        keyword="建材",
        operator_role="admin",
        purpose="竞品价盘监测测试",
    )
    assert out["ok"] is False
    assert out["error_code"] in (
        "ECOMMERCE_CRAWLERS_SIDECAR_ERROR",
        "ECOMMERCE_CRAWLERS_NOT_CONFIGURED",
        "SPIDER_NO_EVIDENCE",
    )
