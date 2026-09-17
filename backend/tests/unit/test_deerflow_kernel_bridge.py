"""DeerFlow 内核桥接（kernel_bridge）单元测试。

验证内容类意图抽事实层、非内容类跳过、绝不编造。
"""

from __future__ import annotations

from app.services.deerflow.kernel_bridge import (
    extract_kernel_from_subtask,
    project_deerflow_output,
)
from app.services.geo.platform_content_router import PlatformGroup


def test_content_intent_extracts_kernel():
    out = {
        "title": "Ceramic Fiber Board",
        "attrs": {"image_url": "https://x/i.jpg"},
        "trade": {"moq": "100", "incoterms": "FOB"},
        "copy": {"en": "iso board"},
    }
    k = extract_kernel_from_subtask("content_creation", out)
    assert k is not None
    assert k.entity_name == "Ceramic Fiber Board"
    assert k.trade.moq == "100"


def test_non_content_intent_returns_none():
    assert extract_kernel_from_subtask("some_other_intent", {"title": "x"}) is None


def test_explicit_fact_kernel_wins():
    out = {"fact_kernel": {"entity_name": "A", "trade": {"moq": "5"}}}
    k = extract_kernel_from_subtask("seo_publish", out)
    assert k.entity_name == "A"
    assert k.trade.moq == "5"


def test_product_snapshot_used_when_no_kernel():
    out = {"title": "T", "product": {"entity_name": "Prod", "attrs": {"moq": "8"}}}
    k = extract_kernel_from_subtask("page_creation", out)
    assert k.entity_name == "Prod"
    assert k.attrs.get("moq") == "8"


def test_degraded_not_fabricated():
    # 只有 title，无硬事实/证据 → 内核降级，不编造
    k = extract_kernel_from_subtask("content_creation", {"title": "X"})
    assert k is not None
    assert k.degraded() is True


def test_project_deerflow_output_b2b():
    out = {
        "entity_name": "Board",
        "trade": {"moq": "100", "incoterms": "FOB Shanghai"},
        "attrs": {"image_url": "https://x/i.jpg", "price": "USD 2"},
        "copy": {"en": "iso ce"},
    }
    res = project_deerflow_output("content_creation", out, PlatformGroup.B2B)
    assert res["platform"] == "generic"
    assert res["incomplete"] is False


def test_project_deerflow_output_skips_non_content():
    res = project_deerflow_output("not_a_content_intent", {"x": 1}, PlatformGroup.B2B)
    assert res["skipped"] is True
