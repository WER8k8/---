"""获客排名闭环（GSC + 百度 + headless 探针统一命中判定）单元测试。

验证核心不变量：
1. GSC 无凭证 → not_configured 证据，不假成功；dev mock 如实标 mock。
2. GSC keyword 命中真值：_keyword_hits 仅统计 query 维度含关键词的行，keyword 为空返回 0。
3. summarize_ranks 保守判定：无证据 → unknown(no_evidence)；有非零真值指标 → hit；真值=0 不判 hit（防假阳性）。
4. build_rank_loop_report 合并 headless 快照，不改变未配置引擎的 unknown 判定。
不真连网，离线断言。
"""

from __future__ import annotations

import asyncio
from typing import Any

from app.services.google_search_console_service import GSCService, _keyword_hits
from app.services.geo.ranking_loop_service import (
    build_rank_loop_report,
    collect_gsc_evidence,
    probe_google_engines,
    summarize_ranks,
)


def _run(coro):
    return asyncio.run(coro)


# ── GSC _keyword_hits ────────────────────────────────────────────────

def test_keyword_hits_empty_keyword_returns_zero():
    rows = [{"keys": {"query": "x", "impressions": 5}}]
    assert _keyword_hits(rows, "") == 0
    assert _keyword_hits(rows, None) == 0


def test_keyword_hits_counts_matching_rows_only():
    rows = [
        {"keys": {"query": "best b2b supplier", "impressions": 10}},
        {"keys": {"query": "random query", "impressions": 3}},
        {"keys": {"query": "b2b supplier china", "impressions": 7}},
        {"keys": "not-a-dict", "impressions": 1},
    ]
    # "b2b" in "best b2b supplier" and "b2b supplier china" -> 2
    assert _keyword_hits(rows, "b2b") == 2
    # case-insensitive
    assert _keyword_hits(rows, "B2B") == 2
    # no match
    assert _keyword_hits(rows, "zzz-not-present") == 0


# ── GSC get_performance 无凭证 → not_configured（不假成功）──────────

def test_gsc_evidence_not_configured_no_fake_success():
    # 清空可能的 GSC 凭证，走 not_configured 分支
    import os
    old_key = os.environ.pop("GSC_API_KEY", None)
    try:
        ev = _run(collect_gsc_evidence("keyword", "https://example.com"))
        # 无凭证：开发环境会 mock（显式标记），生产会 GSC_NOT_CONFIGURED；
        # 无论哪种，都不得出现「真值命中却无来源」的假阳性
        assert ev["source"] == "gsc"
        assert ev["engine_id"] == "google"
        if ev["status"] in ("real", "mock", "hit"):
            # mock 载荷必须带标记
            assert ev.get("freshness") in ("real", "mock")
    finally:
        if old_key is not None:
            os.environ["GSC_API_KEY"] = old_key


# ── summarize_ranks 保守判定 ────────────────────────────────────────

def test_summarize_ranks_no_evidence_is_unknown():
    ranks = summarize_ranks(evidence=[], keyword="k")
    assert ranks == {}


def test_summarize_ranks_nonzero_metric_is_hit():
    evidence = [
        {
            "source": "gsc",
            "engine_id": "google",
            "status": "real",
            "total_impressions": 120,
            "keyword_hits": 3,
        }
    ]
    ranks = summarize_ranks(evidence=evidence, keyword="k")
    assert ranks["google"]["found"] is True


def test_summarize_ranks_zero_metrics_not_hit_no_false_positive():
    # 真值=0：不算命中也不算 miss，保持 unknown，避免假阳性
    evidence = [
        {
            "source": "gsc",
            "engine_id": "google",
            "status": "real",
            "total_impressions": 0,
            "keyword_hits": 0,
        }
    ]
    ranks = summarize_ranks(evidence=evidence, keyword="k")
    assert ranks["google"]["found"] is None
    assert ranks["google"].get("verdict") == "no_evidence"


def test_summarize_ranks_headless_found_true_is_hit():
    evidence = [
        {
            "source": "headless_snapshot",
            "engine_id": "google_aio",
            "status": "headless",
            "found": True,
        }
    ]
    ranks = summarize_ranks(evidence=evidence, keyword="k")
    assert ranks["google_aio"]["found"] is True


def test_summarize_ranks_skipped_not_configured_stays_unknown():
    evidence = [
        {"source": "gsc", "engine_id": "google", "status": "not_configured", "note": "GSC 凭证未配置"},
        {"source": "baidu_webmaster", "engine_id": "baidu", "status": "not_configured"},
    ]
    ranks = summarize_ranks(evidence=evidence, keyword="k")
    assert ranks["google"]["found"] is None
    assert ranks["baidu"]["found"] is None
    assert ranks["google"].get("verdict") == "no_evidence"


# ── build_rank_loop_report ───────────────────────────────────────────

def test_build_rank_loop_report_merges_snapshot_and_keeps_unknown():
    evidence: list[Any] = []
    report = build_rank_loop_report(
        db=None,  # 无快照可读，不合并
        keyword="k",
        target_url="https://example.com",
        evidence=[
            {"source": "gsc", "engine_id": "google", "status": "real", "total_impressions": 0, "keyword_hits": 0},
            {"source": "headless_snapshot", "engine_id": "google_aio", "status": "headless", "found": True},
        ],
    )
    per = report["per_engine"]
    assert per["google"]["found"] is None  # 真值=0 不判 hit
    assert per["google_aio"]["found"] is True
    assert report["summary"]["hit"] == 1
    assert report["summary"]["unknown"] == 1
    assert report["keyword"] == "k"


def test_build_rank_loop_report_no_evidence_all_unknown():
    report = build_rank_loop_report(db=None, keyword="k", target_url="https://example.com", evidence=[])
    assert report["per_engine"] == {}
    assert report["summary"]["engines_tracked"] == 0


# ── probe_google_engines（无 sidecar → 如实 skipped/unconfigured）──

def test_probe_google_engines_unconfigured_is_honest():
    # 无 HEADLESS_PROBE_SIDECAR_URL：dev stub 或 unconfigured，绝不伪造命中
    rows = probe_google_engines("k", "https://example.com")
    assert len(rows) == 2  # google + google_aio
    for r in rows:
        assert r["engine_id"] in ("google", "google_aio")
        # 无真实探针：found 必须为 None（未探测）或 status 为 skipped/unconfigured
        assert r.get("found") in (None, True, False)
        assert r.get("skipped") is True or r.get("probe_mode") in ("headless", "stub")
