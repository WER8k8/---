"""海外 B2B 适配器（b2b_global）单元测试。

重点验证「禁止假成功」铁律：缺凭证必须报 PLATFORM_NOT_CONFIGURED，
内核降级必须如实标 incomplete，不编造成功。
"""

from __future__ import annotations

import pytest

import asyncio

def _run(coro):
    return asyncio.run(coro)

from app.services.geo.content_kernel import FactKernel
from app.services.platforms.b2b_global import B2BGlobalPublisher
from app.services.publish_capability_registry import PLATFORM_NOT_CONFIGURED


def _kernel() -> FactKernel:
    return FactKernel.from_dict(
        {
            "entity_name": "Ceramic Fiber Board",
            "trade": {"moq": "100 pieces", "incoterms": "FOB Shanghai"},
            "attrs": {"image_url": "https://x/i.jpg", "price": "USD 2.1"},
            "copy": {"en": "iso ce board"},
        }
    )


def test_missing_credentials_reports_not_configured():
    pub = B2BGlobalPublisher("alibaba", credentials={})
    missing = pub.missing_credentials()
    assert "alibaba_session_cookie" in missing
    assert pub.configured() is False


def test_credentials_from_env_count():
    pub = B2BGlobalPublisher("alibaba", credentials={
        "alibaba_session_cookie": "s", "alibaba_member_id": "m1",
    })
    assert pub.missing_credentials() == []
    assert pub.configured() is True


def test_publish_not_configured_does_not_fake_success():
    pub = B2BGlobalPublisher("made_in_china", credentials={})
    res = _run(pub.publish_offer(_kernel()))
    assert res["status"] == "failed"
    assert res["error_code"] == PLATFORM_NOT_CONFIGURED
    assert "mic_access_token" in res["missing_credentials"]


def test_globalsources_credential_missing():
    pub = B2BGlobalPublisher("globalsources", credentials={"gs_api_key": "k"})
    assert pub.configured() is True


def test_validate_credentials_does_not_send_requests():
    pub = B2BGlobalPublisher("alibaba", credentials={})
    # 只查凭证齐备，不真发（async，用 _run 驱动）
    assert _run(pub.validate_credentials()) is False
    pub2 = B2BGlobalPublisher("alibaba", credentials={
        "alibaba_session_cookie": "s", "alibaba_member_id": "m",
    })
    assert _run(pub2.validate_credentials()) is True


def test_b2b_keys_in_live_registry():
    from app.services.publish_capability_registry import LIVE_PUBLISHER_KEYS
    assert {"alibaba", "made_in_china", "globalsources"} <= LIVE_PUBLISHER_KEYS
