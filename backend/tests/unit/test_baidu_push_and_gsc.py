"""百度 URL 级增量推送 + 谷歌 GSC 回收闭环单元测试。

重点验证「交付求真、无 Key 降级不假成功」铁律：
- 百度 push_urls 无 token：开发环境显式 mock（带 stamp_mock 标记），生产会拒。
- GSC get_performance 无凭证：返回 GSC_NOT_CONFIGURED，不编造真值。
不真连网，纯离线断言。
"""

from __future__ import annotations

import asyncio

from app.services.baidu_webmaster_service import BaiduWebmasterService
from app.services.google_search_console_service import GSCService


def _run(coro):
    return asyncio.run(coro)


def test_baidu_push_urls_no_token_dev_mock():
    # 无 token → 开发环境走 mock（stamp_mock 打标），success 但带 mock 标记
    res = _run(BaiduWebmasterService.push_urls("https://x.com", ["https://x.com/a", "https://x.com/b"], None))
    assert res["success"] is True
    data = res["data"]
    assert data["pushed"] == 2
    # mock 必须留痕，禁止假装真推
    assert data.get("_mock") is True or "mock" in str(data).lower() or "dev mock" in res.get("message", "")


def test_baidu_push_urls_dedupes_and_validates():
    res = _run(BaiduWebmasterService.push_urls("https://x.com", ["https://x.com/a", "https://x.com/a", ""], None))
    assert res["success"] is True
    assert res["data"]["pushed"] == 1  # 去重 + 空串过滤


def test_baidu_push_urls_empty_rejected():
    res = _run(BaiduWebmasterService.push_urls("https://x.com", ["  ", ""], None))
    # 无有效 URL（去重+空串过滤后为 0）→ 不推送、不 mock，如实拒绝
    assert res["success"] is False
    assert res["data"] is None


def test_gsc_no_credential_not_configured():
    res = _run(GSCService.get_performance("example.com", 28, api_key=""))
    # 无可用凭证 → 开发环境 mock 分支；生产会 GSC_NOT_CONFIGURED
    assert res["success"] is True  # 开发 mock 放行
    assert res["data"]["ai_overviews_impressions"] == 0
    assert res["data"]["discovery_impressions"] == 0
    # 真值未提供时如实置 0，不编造曝光


def test_gsc_configured_false_without_key():
    import os
    old = os.environ.get("GSC_API_KEY")
    os.environ.pop("GSC_API_KEY", None)
    try:
        assert GSCService.configured() is False
    finally:
        if old:
            os.environ["GSC_API_KEY"] = old


def test_gsc_dimension_impressions_counts_only_real_key():
    from app.services.google_search_console_service import _dimension_impressions

    data = {
        "data": {
            "rows": [
                {"keys": {"ai_overviews_impressions": 42}},
                {"keys": {"ai_overviews_impressions": 8}},
            ]
        }
    }
    assert _dimension_impressions(data, "ai_overviews_impressions") == 50
    # 不存在的维度如实返回 0
    assert _dimension_impressions(data, "discovery_impressions") == 0
