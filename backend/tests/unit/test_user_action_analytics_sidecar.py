"""UserActionAnalyzePlatform sidecar tests."""

from app.services.analytics.user_action_analytics_smart import (
    build_panel_slice,
    quick_run,
    resolve_module_id,
)


def test_resolve_conversion_preset():
    assert resolve_module_id("conversion") == "page_conversion"
    assert resolve_module_id("funnel") == "page_conversion"


def test_panel_slice():
    slice_ = build_panel_slice()
    assert slice_["id"] == "user_action_analytics"
    assert slice_["featured_modules"]


def test_quick_run_not_configured(monkeypatch):
    monkeypatch.delenv("USER_ACTION_ANALYTICS_URL", raising=False)
    out = quick_run("conversion", operator_role="admin")
    assert out["ok"] is False
    assert out.get("message_zh")
