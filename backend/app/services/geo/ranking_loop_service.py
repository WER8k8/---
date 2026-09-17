# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""获客排名闭环 — GSC/百度真值回收接入 headless 排名探针。

补齐蓝图 P2：GSC 回收从「只读面板」升级为「判定器」——
- GSC performance 真值 → 谷歌侧命中/曝光证据；
- 百度索引量真值 → 国内侧收录证据；
- 与 headless 探针快照合并为统一 rank-loop 报告，每条证据带 source + 数据真伪标记
  （mock/stub/skipped 一律如实标记，禁止假成功；无凭证时 source=not_configured）。
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.core.no_fake_delivery import is_mock_payload
from app.services.baidu_webmaster_service import BaiduWebmasterService
from app.services.geo.headless_rank_probe_service import (
    load_headless_probe_snapshot,
    probe_single_engine,
)
from app.services.geo.multi_engine_rank_registry import all_traffic_engines
from app.services.google_search_console_service import GSCService

# 站点域名解析：site_url → 纯域（google_aio/gsc 需要不含协议的站点根）
_GSC_TARGET_ENGINES: tuple[str, ...] = ("google", "google_aio")
_BAIDU_TARGET_ENGINES: tuple[str, ...] = ("baidu",)
_UNKNOWN = "unknown"


def _site_root(site_url: str) -> str:
    """site_url（如 https://example.com/path）→ example.com（GSC 需要的纯域）。"""
    root = (site_url or "").strip()
    for prefix in ("https://", "http://"):
        if root.startswith(prefix):
            root = root[len(prefix):]
            break
    return (root or "").split("/", 1)[0].strip() or _UNKNOWN


def _freshness(data: dict[str, Any]) -> str:
    """数据真伪：mock 载荷如实标记，其余视为真值（real 含 stub/skipped，由字段自证）。"""
    if is_mock_payload(data or {}):
        return "mock"
    return "real"


def _evidence(*, source: str, engine_id: str, status: str, data: Any, note: str = "") -> dict[str, Any]:
    """构造一条排名证据。status: real / not_configured / skipped / error。"""
    entry: dict[str, Any] = {
        "source": source,
        "engine_id": engine_id,
        "status": status,
        "freshness": _freshness(data or {}) if isinstance(data, dict) else "unknown",
        "note": note,
        "collected_at": datetime.now(timezone.utc).isoformat(),
    }
    if isinstance(data, dict):
        entry.update({k: v for k, v in data.items() if k != "mode"})
    elif data is not None:
        entry["data"] = data
    return entry


async def collect_gsc_evidence(
    keyword: str,
    target_url: str,
    *,
    site_url: Optional[str] = None,
    days: int = 28,
) -> dict[str, Any]:
    """谷歌侧：GSC performance 真值（含 AI Overviews / Discovery 曝光维度）。

    未配置凭证时返回 source=not_configured 证据（不 fake）；dev mock 时如实标 mock。
    """
    site = site_url or _site_root(target_url)
    result = await GSCService.get_performance(site, days=days, keyword=keyword)
    if not result.get("success"):
        return _evidence(
            source="gsc",
            engine_id="google",
            status="not_configured" if (result.get("error_code") == "GSC_NOT_CONFIGURED") else "error",
            data=None,
            note=result.get("message") or result.get("error_code") or "GSC 回收失败",
        )
    data = result.get("data") or {}
    ai_hits = int(data.get("ai_overviews_impressions") or 0)
    disc_hits = int(data.get("discovery_impressions") or 0)
    status = "real"
    if is_mock_payload(data):
        status = "mock"
    note = (
        f"GSC 回收 window={days}d site={site}；ai_overviews={ai_hits} discovery={disc_hits}；"
        f"总曝光={data.get('total_impressions', 0)} 总点击={data.get('total_clicks', 0)}。"
        "AI Overviews/Discovery 为独立曝光维度，未开放时如实置 0，不冒充普通 impression。"
    )
    return _evidence(
        source="gsc",
        engine_id="google",
        status=status,
        data={
            "site": data.get("site"),
            "total_clicks": data.get("total_clicks", 0),
            "total_impressions": data.get("total_impressions", 0),
            "ai_overviews_impressions": ai_hits,
            "discovery_impressions": disc_hits,
            "keyword_hits": data.get("keyword_hits", 0) or 0,
            "rows_sample": (data.get("rows") or [])[:5],
        },
        note=note,
    )


async def collect_baidu_evidence(
    keyword: str,
    target_url: str,
    *,
    site_url: Optional[str] = None,
) -> dict[str, Any]:
    """国内侧：百度站长索引量真值。未配置 token → not_configured；dev mock 如实标 mock。"""
    site = site_url or _site_root(target_url)
    result = await BaiduWebmasterService.get_index_count(site_url=site)
    if not result.get("success"):
        return _evidence(
            source="baidu_webmaster",
            engine_id="baidu",
            status="not_configured",
            data=None,
            note=result.get("message") or "百度站长 token 未配置",
        )
    data = result.get("data") or {}
    status = "mock" if is_mock_payload(data) else "real"
    return _evidence(
        source="baidu_webmaster",
        engine_id="baidu",
        status=status,
        data={
            "site": site,
            "index_count": data.get("indexCount", data.get("count")),
        },
        note="百度站长索引量真值（mock 载荷如实标记）。",
    )


def probe_google_engines(
    keyword: str,
    target_url: str,
    *,
    engine_ids: Optional[list[str]] = None,
) -> list[dict[str, Any]]:
    """谷歌侧 headless 探针：google / google_aio 逐引擎，unconfigured/skipped 如实标记。"""
    engines = {e.id: e for e in all_traffic_engines() if e.id in _GSC_TARGET_ENGINES}
    if engine_ids:
        engines = {k: v for k, v in engines.items() if k in set(engine_ids)}
    out: list[dict[str, Any]] = []
    for eid, eng in engines.items():
        row = probe_single_engine(engine_id=eid, keyword=keyword, target_url=target_url)
        row["display_name"] = eng.display_name
        if row.get("skipped"):
            row["status"] = "skipped"
        elif row.get("found") is True:
            row["status"] = "hit"
        elif row.get("found") is False:
            row["status"] = "miss"
        else:
            row["status"] = row.get("probe_mode", "unknown")
        out.append(row)
    return out


def summarize_ranks(*, evidence: list[dict[str, Any]], keyword: Optional[str] = None) -> dict[str, Any]:
    """由已收集的各类证据 + headless 快照汇总 per-engine 命中判定。

    判定规则（保守，不编造）：
    - gsc/baidu_webmaster 证据 source 命中且有非零真值指标 → hit；
    - not_configured/skipped/error → 对应状态，不算命中；
    - headless 快照 found=True → hit；
    - 无法判定 → unknown。
    """
    by_engine: dict[str, dict[str, Any]] = {}
    for item in evidence:
        if not isinstance(item, dict):
            continue
        eid = str(item.get("engine_id") or _UNKNOWN)
        status = item.get("status") or _UNKNOWN
        entry = by_engine.setdefault(
            eid,
            {
                "engine_id": eid,
                "found": None,
                "rank_hint": None,
                "sources": [],
                "notes": [],
            },
        )
        entry["sources"].append(item.get("source") or _UNKNOWN)
        if item.get("note"):
            entry["notes"].append(str(item["note"])[:200])

        found_flag = item.get("found")
        if found_flag in (True, False):
            entry["found"] = True if found_flag else False
        elif status == "not_configured" or status == "skipped" or status == "error" or status == "unconfigured":
            # 无证据可判定：保持 None（unknown），显式记录来源
            entry.setdefault("verdict", "no_evidence")
        elif status in ("real", "mock", "hit"):
            # GSC/百度真值回收成功：若有非零指标则判 hit
            numeric = {
                "total_impressions": item.get("total_impressions", 0) or 0,
                "total_clicks": item.get("total_clicks", 0) or 0,
                "ai_overviews_impressions": item.get("ai_overviews_impressions", 0) or 0,
                "discovery_impressions": item.get("discovery_impressions", 0) or 0,
                "index_count": item.get("index_count", 0) or 0,
                "keyword_hits": item.get("keyword_hits", 0) or 0,
            }
            if any(v > 0 for v in numeric.values()):
                entry["found"] = True
            elif status == "hit":
                entry["found"] = True
            # 真值=0 不算命中也不算 miss，保持 None（unknown），避免假阳性
            if entry.get("rank_hint") is None:
                entry["rank_hint"] = item.get("rank_hint")
        # stub / 未知
        if entry.get("found") is None:
            entry.setdefault("verdict", "no_evidence")
    for eng in by_engine.values():
        if eng.get("found") is None and "verdict" not in eng:
            eng["verdict"] = "no_evidence"
        # 清理空 sources/notes
        if not eng.get("notes"):
            eng.pop("notes", None)
        if not eng.get("sources"):
            eng.pop("sources", None)
    return {engine_id: data for engine_id, data in by_engine.items()}


def build_rank_loop_report(
    db: Session | None,
    keyword: str,
    target_url: str,
    *,
    evidence: list[dict[str, Any]] | None = None,
    merge_headless_snapshot: bool = True,
) -> dict[str, Any]:
    """组装统一获客排名闭环报告。

    参数：
    - db: 可选 Session，用于读取 headless 探针快照（无快照则不合并）。
    - evidence: 由 collect_*_evidence + probe_google_engines 产出的证据数组。
    - merge_headless_snapshot: 是否把最近的 headless 快照并进 per-engine 视图。
    """
    ev = list(evidence or [])
    if merge_headless_snapshot and db is not None:
        snap = load_headless_probe_snapshot(db)
        if snap:
            for row in snap.get("results") or []:
                if isinstance(row, dict):
                    ev.append(
                        _evidence(
                            source="headless_snapshot",
                            engine_id=row.get("engine_id") or _UNKNOWN,
                            status=row.get("probe_mode") or "unknown",
                            data={
                                "found": row.get("found"),
                                "rank_hint": row.get("rank_hint"),
                                "evidence_snippet": (row.get("evidence_snippet") or "")[:200],
                                "probe_mode": row.get("probe_mode"),
                            },
                            note=f"headless 快照 saved_at={snap.get('saved_at')}",
                        )
                    )
    ranks = summarize_ranks(evidence=ev, keyword=keyword)
    summary = {
        "engines_tracked": len(ranks),
        "hit": sum(1 for e in ranks.values() if e.get("found") is True),
        "miss": sum(1 for e in ranks.values() if e.get("found") is False),
        "unknown": sum(1 for e in ranks.values() if e.get("found") is None),
    }
    return {
        "keyword": keyword,
        "target_url": target_url,
        "built_at": datetime.now(timezone.utc).isoformat(),
        "per_engine": ranks,
        "summary": summary,
        "note": (
            "排名判定基于 GSC/百度真值 + headless 探针。"
            "未配置凭证或无快照的引擎一律记为 unknown（no_evidence），"
            "不编造命中；生产路径禁用未标记 mock。"
        ),
    }


__all__ = [
    "collect_gsc_evidence",
    "collect_baidu_evidence",
    "probe_google_engines",
    "summarize_ranks",
    "build_rank_loop_report",
]
