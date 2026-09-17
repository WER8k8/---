# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Hermes 每日排名攻坚 — 多引擎 probe + 战术雷达 + ECC 评审 + 回归告警。"""

from __future__ import annotations

import asyncio
import concurrent.futures
import json
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.core.cache import redis_client
from app.services.geo.multi_engine_rank_registry import (
    default_probe_keywords,
    exploration_engines,
    probe_ready_engines,
)
from app.services.geo.platform_discovery_service import discovery_snapshot
from app.services.geo.geo_writing_policy import TACTICS_VERSION
from app.services.hermes.hermes_rank_first_constitution import (
    RANK_FIRST_PRINCIPLE,
    rank_first_payload,
)
from app.services.hermes.maintenance_constitution import assert_maintenance_action

logger = logging.getLogger("uj-admin.hermes_daily_rank_ops")


def _safe_asyncio_run(coro):
    """安全执行异步协程：兼容已有事件循环（FastAPI）和无事件循环（Celery）。"""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, coro).result()
    return asyncio.run(coro)

RANK_OPS_SNAPSHOT_KEY = "hermes:rank_ops:latest"
RANK_OPS_HISTORY_PREFIX = "hermes:rank_ops:day:"


def _save_snapshot(payload: dict[str, Any]) -> dict[str, Any]:
    """_save_snapshot。

    参数说明：
    :param payload: 参数 payload
    :return: 返回处理结果。
    """
    assert_maintenance_action("write_patrol_snapshot")
    body = {**payload, "saved_at": datetime.now(timezone.utc).isoformat()}
    if redis_client:
        redis_client.set(
            RANK_OPS_SNAPSHOT_KEY,
            json.dumps(body, ensure_ascii=False),
            ex=86400 * 14,
        )
        day = datetime.now(timezone.utc).strftime("%Y%m%d")
        redis_client.set(
            f"{RANK_OPS_HISTORY_PREFIX}{day}",
            json.dumps(body, ensure_ascii=False),
            ex=86400 * 90,
        )
    return body


def _load_yesterday_pass_rate() -> float | None:
    """_load_yesterday_pass_rate。
    :return: 返回处理结果。
    """
    if not redis_client:
        return None
    from datetime import timedelta
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y%m%d")
    raw = redis_client.get(f"{RANK_OPS_HISTORY_PREFIX}{yesterday}")
    if not raw:
        return None
    try:
        data = json.loads(raw)
        return float(data.get("summary", {}).get("recommend_pass_rate") or 0)
    except (TypeError, ValueError, json.JSONDecodeError):
        return None


async def _run_multi_engine_probes() -> dict[str, Any]:
    """_run_multi_engine_probes。
    :return: 返回处理结果。
    """
    from app.services.geo_engine_service import GEOEngine
    engines = probe_ready_engines()
    keywords = default_probe_keywords()
    probes: list[dict[str, Any]] = []
    recommended = 0
    total = 0
    for kw in keywords:
        brand = kw["brand"]
        category = kw["product_category"]
        region = kw.get("region", "")
        model_ids = [e.geo_model_id for e in engines if e.geo_model_id]
        try:
            result = await GEOEngine.check_keyword(
                keyword=brand,
                models=model_ids,
                probe_mode="recommend",
                brand_name=brand,
                product_category=category,
                region=region,
            )
            for m in result.get("models") or []:
                total += 1
                in_top3 = m.get("status") == "indexed" and (
                    m.get("rank_position") in (1, 2, 3) or m.get("mentions_brand")
                )
                if in_top3:
                    recommended += 1
                probes.append(
                    {
                        "keyword": brand,
                        "category": category,
                        "engine_id": m.get("id"),
                        "engine_name": m.get("name"),
                        "status": m.get("status"),
                        "rank_position": m.get("rank_position"),
                        "mentions_brand": m.get("mentions_brand"),
                        "confidence": m.get("confidence"),
                        "probe_mode": "recommend",
                    }
                )
        except Exception as exc:
            logger.warning("multi-engine probe failed brand=%s: %s", brand, exc)
            probes.append({"keyword": brand, "error": str(exc)[:200]})

    pass_rate = round(recommended / total, 4) if total else 0.0
    return {
        "probes": probes,
        "engines_probed": len(engines),
        "exploration_engines": [e.id for e in exploration_engines()],
        "recommend_pass_rate": pass_rate,
        "recommended_count": recommended,
        "probe_total": total,
    }


def _fetch_geo_tactics_radar() -> dict[str, Any]:
    """外网 GEO 战术更新（Tavily + 公开源摘要）。"""
    assert_maintenance_action("read_probe")
    items: list[dict[str, Any]] = []
    errors: list[str] = []
    try:
        from app.services.geo.tavily_search import fetch_tavily_radar_items
        tavily = fetch_tavily_radar_items(limit_per_query=3)
        if tavily.get("configured"):
            items.extend(tavily.get("items") or [])
            errors.extend(f"tavily:{e}" for e in (tavily.get("errors") or []))
        else:
            errors.append("tavily:not_configured")
    except Exception as exc:
        errors.append(f"tavily:{exc}")

    return {
        "tactics_version": TACTICS_VERSION,
        "items": items[:20],
        "item_count": len(items),
        "errors": errors,
    }


def _ecc_rank_review_summary(
    probe_report: dict[str, Any],
    *,
    regression: bool,
) -> dict[str, Any]:
    """ECC 专家只读评审摘要（规则层；LLM 评审由 tech_validation 承担）。"""
    assert_maintenance_action("read_probe")
    verdict = "pass"
    actions: list[str] = []
    if regression:
        verdict = "warn"
        actions.append("suggest_remediation: 对比昨日 probe 通过率，优先补强 FAQ/参数/platform 矩阵")

    if probe_report.get("recommend_pass_rate", 0) < 0.25:
        verdict = "fail"
        actions.append("suggest_remediation: recommend 通过率过低，触发 geo_content_matrix 人审发稿")

    exploration = probe_report.get("exploration_engines") or []
    if exploration:
        actions.append(
            f"suggest_remediation: 待攻坚入口 {', '.join(exploration[:5])} — 需 headless/API 探针"
        )

    experts = [
        "insulation-material-product-manager",
        "testing-reality-checker",
        "fullstack-developer",
    ]
    if verdict == "fail":
        experts.insert(0, "insulation-backend-security-expert")

    return {
        "verdict": verdict,
        "experts": experts,
        "actions": actions,
        "readonly": True,
        "principle": RANK_FIRST_PRINCIPLE[:120],
    }


async def run_hermes_daily_rank_cycle_async(
    db: Session,
    *,
    trigger: str = "scheduler",
) -> dict[str, Any]:
    """Hermes 排名第一准则 — 每日主循环。"""
    assert_maintenance_action("read_probe")
    probe_report = await _run_multi_engine_probes()
    tactics = _fetch_geo_tactics_radar()
    platform_gap = discovery_snapshot(db)
    rank_guard: dict[str, Any] = {}
    try:
        from app.services.geo_rank_guard_probe import run_rank_guard_probe
        rank_guard = run_rank_guard_probe(db, trigger=f"{trigger}:rank_guard")
    except Exception as exc:
        rank_guard = {"error": str(exc)[:200]}

    yesterday_rate = _load_yesterday_pass_rate()
    today_rate = float(probe_report.get("recommend_pass_rate") or 0)
    regression = (
        yesterday_rate is not None and today_rate < yesterday_rate - 0.05
    )
    ecc = _ecc_rank_review_summary(probe_report, regression=regression)
    summary = {
        "recommend_pass_rate": today_rate,
        "yesterday_pass_rate": yesterday_rate,
        "regression_detected": regression,
        "tactics_version": TACTICS_VERSION,
        "live_platform_coverage": platform_gap.get("coverage_rate"),
        "exploration_queue_len": len(platform_gap.get("next_build_queue") or []),
        "rank_guard_passed": rank_guard.get("passed"),
    }
    body: dict[str, Any] = {
        "trigger": trigger,
        "charter": rank_first_payload(),
        "summary": summary,
        "multi_engine_probe": probe_report,
        "geo_tactics_radar": tactics,
        "platform_discovery": {
            "coverage_rate": platform_gap.get("coverage_rate"),
            "next_build_queue": (platform_gap.get("next_build_queue") or [])[:5],
            "recommended_publish_order_cn": platform_gap.get("recommended_publish_order_cn"),
        },
        "rank_guard": rank_guard,
        "ecc_review": ecc,
    }
    alert = {"sent": False}
    if regression or ecc.get("verdict") == "fail" or not rank_guard.get("passed", True):
        assert_maintenance_action("emit_alert")
        try:
            from app.services.hermes.alert_dispatcher import notify_rank_guard
            alert = notify_rank_guard(
                {
                    "trigger": trigger,
                    "message": "Hermes 每日排名攻坚：检测到回归或 probe 失败",
                    "summary": summary,
                    "ecc_verdict": ecc.get("verdict"),
                }
            )
        except Exception as exc:
            logger.warning("rank ops alert skipped: %s", exc)
            alert = {"sent": False, "error": str(exc)[:200]}

    body["alert"] = alert
    return _save_snapshot(body)


def run_hermes_daily_rank_cycle(db: Session, *, trigger: str = "scheduler") -> dict[str, Any]:
    """run_hermes_daily_rank_cycle。

    参数说明：
    :param db: 参数 db
    :param trigger: 参数 trigger
    :return: 返回处理结果。
    """
    return _safe_asyncio_run(run_hermes_daily_rank_cycle_async(db, trigger=trigger))


def load_rank_ops_snapshot() -> dict[str, Any] | None:
    """load_rank_ops_snapshot。
    :return: 返回处理结果。
    """
    assert_maintenance_action("read_probe")
    from app.core.cache import redis_available
    if not redis_available():
        return None
    try:
        raw = redis_client.get(RANK_OPS_SNAPSHOT_KEY)
    except Exception as exc:
        logger.warning("load_rank_ops_snapshot redis get failed: %s", exc)
        return None
    if not raw:
        return None
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        return None
