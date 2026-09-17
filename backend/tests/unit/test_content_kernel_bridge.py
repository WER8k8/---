"""内核接线层（content_kernel_bridge）单元测试。

验证「母版 + 产品快照 → 事实内核 → 形态投影」的组装逻辑，不碰 DB/网络。
用轻量 stub 替代 ContentMaster，只测 bridge 的纯组装行为。
"""

from __future__ import annotations

from types import SimpleNamespace

from app.services.geo.content_kernel_bridge import (
    build_kernel_from_master,
    project_for_platform,
)
from app.services.geo.platform_content_router import PlatformGroup


def _master_stub() -> SimpleNamespace:
    """最小化的母版替身：bridge 只读这几个字段。"""
    return SimpleNamespace(
        id="m-1",
        title="Ceramic Fiber Board",
        body="High-temp insulation board, ISO/CE, MOQ 100, FOB Shanghai.",
        media_urls=["https://x/img.jpg"],
        tenant_canonical_url="https://t.example/products/cfb",
        tenant_id="t-001",
    )


def _snap() -> dict:
    return {
        "trade": {
            "moq": "100 pieces",
            "lead_time": "15 days",
            "incoterms": "FOB Shanghai",
            "certifications": ["ISO 9001", "CE"],
        },
        "evidence": [{"label": "SGS test report", "level": "strong"}],
        "copy": {"en": "ISO/CE ceramic fiber board"},
    }


def test_bridge_assembles_full_kernel():
    k = build_kernel_from_master(_master_stub(), _snap())
    assert k.entity_name == "Ceramic Fiber Board"
    assert k.trade.moq == "100 pieces"
    assert k.attrs["image_url"] == "https://x/img.jpg"
    assert k.attrs["description"] in ("High-temp insulation board, ISO/CE, MOQ 100, FOB Shanghai.", "High-temp insulation board, ISO/CE, MOQ 100, FOB Shanghai.")
    assert k.schema_ready is True


def test_bridge_degrades_when_no_snapshot():
    k = build_kernel_from_master(_master_stub(), None)
    # 只有文案、无硬事实/证据 → 降级
    assert k.degraded() is True


def test_project_b2b_uses_generic_default():
    out = project_for_platform(_master_stub(), _snap(), "alibaba", PlatformGroup.B2B)
    assert out["platform"] == "alibaba_offer"
    assert out["incomplete"] is False


def test_project_knowledge_cn_de_ai():
    out = project_for_platform(_master_stub(), _snap(), "zhihu", PlatformGroup.KNOWLEDGE, region="cn")
    assert out["de_ai_tuned"] is True
    assert "SGS test report" in out["body"]


def test_project_unknown_group_no_fake_success():
    out = project_for_platform(_master_stub(), _snap(), "weird", "nonsense")
    assert out["incomplete"] is True


def test_bridge_non_ali_platform_gets_generic_feed():
    out = project_for_platform(_master_stub(), _snap(), "made_in_china", PlatformGroup.B2B)
    assert out["platform"] == "generic"
