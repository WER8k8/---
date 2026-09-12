"""财迷疯 · 摸金校尉 — 搞钱商业闭环（调研→编排→生产→发出→卖出跟踪→收款 KPI）。

仅 platform_survival scope；不触 SaaS 租户主流程。宪法：greedy_avatar_constitution.py
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import json
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.core.cache import redis_client
from app.core.config import settings
from app.services.hermes.greedy_avatar_constitution import (
    REVENUE_LOOP_STAGES,
    assert_greedy_action,
    greedy_constitution_payload,
    legal_gate_check,
)

logger = logging.getLogger("uj-admin.hermes_greedy_revenue_loop")


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

_LOOP_SNAPSHOT_KEY = "hermes:greedy:revenue_loop:latest"
_PUBLISH_QUEUE_KEY = "hermes:greedy:publish_queue"


def _greedy_auto_publish_enabled() -> bool:
    """_greedy_auto_publish_enabled。
    :return: 返回处理结果。
    """
    flag = getattr(settings, "HERMES_GREEDY_AUTO_PUBLISH_ENABLED", None)
    if flag is not None:
        return bool(flag)
    return False


async def _stage_research(db: Session | None, *, locale: str, message: str) -> dict[str, Any]:
    """_stage_research。

    参数说明：
    :param db: 参数 db
    :param locale: 参数 locale
    :param message: 参数 message
    :return: 返回处理结果。
    """
    assert_greedy_action("read_probe")
    probe: dict[str, Any] = {"ok": False, "hits": []}
    try:
        from app.services.hermes.anysearch_probe_service import run_anysearch
        q = f"digital product B2B monetization agent workflow {locale} 2026"
        if message:
            q = f"{message[:120]} {q}"
        probe = run_anysearch(query=q, max_results=3)
    except Exception as exc:
        probe = {"ok": False, "error": str(exc)[:120]}
    brief: dict[str, Any] = {}
    if db is not None:
        try:
            from app.services.hermes.research_brief_service import collect_signals, compose_research_brief
            topic = {
                "key": "greedy_revenue_loop",
                "lane": "GW-G",
                "label": "摸金校尉日循环调研",
                "category": "paper",
            }
            brief = compose_research_brief(db, topic=topic, signals=collect_signals(db))
        except Exception as exc:
            brief = {"error": str(exc)[:120]}
    return {"stage": "L1_research", "anysearch": probe, "brief_id": brief.get("brief_id"), "finding": brief.get("finding")}


async def _stage_orchestrate(
    db: Session,
    *,
    locale: str,
    message: str,
    survival_goal_cny: int,
    max_steps: int | None,
) -> dict[str, Any]:
    """_stage_orchestrate。

    参数说明：
    :param db: 参数 db
    :param locale: 参数 locale
    :param message: 参数 message
    :param survival_goal_cny: 参数 survival_goal_cny
    :param max_steps: 参数 max_steps
    :return: 返回处理结果。
    """
    assert_greedy_action("orchestrate_agency")
    from app.services.hermes.greedy_agency_orchestrator_service import run_greedy_orchestration_async
    result = await run_greedy_orchestration_async(
        db,
        playbook_id="greedy_survival_critical",
        inputs={
            "locale": locale,
            "survival_goal_cny": survival_goal_cny,
            "product_context": message or "B2B 外贸 SaaS platform survival monetization",
        },
        tenant_id=None,
        max_steps=max_steps,
    )
    return {"stage": "L2_orchestrate", "workflow_id": result.get("workflow_id"), "steps": len(result.get("steps") or []), "result": result}


def _stage_compose(orchestrate: dict[str, Any]) -> dict[str, Any]:
    """_stage_compose。

    参数说明：
    :param orchestrate: 参数 orchestrate
    :return: 返回处理结果。
    """
    assert_greedy_action("compose_monetize_asset")
    inner = orchestrate.get("result") or {}
    outputs = inner.get("outputs") or {}
    plan = inner.get("greedy_plan") or {}
    deliverable_skus: list[str] = []
    for ex in plan.get("experts_selected") or []:
        if isinstance(ex, dict):
            deliverable_skus.extend(ex.get("deliverable_skus") or [])
    deliverable_skus = list(dict.fromkeys(deliverable_skus))
    asset = {
        "greedy_summary": outputs.get("greedy_summary") or outputs.get("battle_plan") or "",
        "marketing_plan": outputs.get("marketing_plan") or "",
        "sales_plan": outputs.get("sales_plan") or "",
        "finance_plan": outputs.get("finance_plan") or "",
        "demo_concept": outputs.get("demo_concept") or "",
        "xr_variant": outputs.get("xr_variant") or "",
        "deliverable_skus": deliverable_skus,
        "composed_at": datetime.now(timezone.utc).isoformat(),
    }
    gate = legal_gate_check(action="compose_monetize_asset", meta=asset)
    return {"stage": "L3_compose", "asset": asset, "legal_gate": gate}


def _stage_publish(db: Session | None, compose: dict[str, Any], *, locale: str) -> dict[str, Any]:
    """_stage_publish。

    参数说明：
    :param db: 参数 db
    :param compose: 参数 compose
    :param locale: 参数 locale
    :return: 返回处理结果。
    """
    assert_greedy_action("stage_publish")
    asset = compose.get("asset") or {}
    if not (compose.get("legal_gate") or {}).get("ok"):
        return {"stage": "L4_publish", "skipped": True, "reason": "legal_gate_blocked"}

    from app.services.hermes.role_economics_service import build_l4_publish_items
    queue_items = build_l4_publish_items(
        asset=asset,
        locale=locale,
        deliverable_skus=list(asset.get("deliverable_skus") or []),
    )
    published = False
    publish_detail: dict[str, Any] = {"mode": "staged_only", "items": len(queue_items)}
    if _greedy_auto_publish_enabled() and db is not None:
        try:
            assert_greedy_action("publish_survival_marketing")
            from app.services.ubrain.matrix_publish_service import build_matrix_publish_plan
            plan = build_matrix_publish_plan(
                {
                    "locale": locale,
                    "content_source": "greedy_compose",
                    "cta": queue_items[0].get("cta") or "B2B inquiry / digital product",
                    "skus": [i.get("sku") for i in queue_items],
                }
            )
            publish_detail = {"mode": "auto_publish_enabled", "plan": plan, "items": len(queue_items)}
            published = True
        except Exception as exc:
            publish_detail = {"mode": "auto_publish_failed", "error": str(exc)[:160], "items": len(queue_items)}

    if redis_client:
        for payload in queue_items:
            redis_client.lpush(_PUBLISH_QUEUE_KEY, json.dumps(payload, ensure_ascii=False))
        redis_client.ltrim(_PUBLISH_QUEUE_KEY, 0, 49)

    return {
        "stage": "L4_publish",
        "staged": True,
        "auto_published": published,
        "detail": publish_detail,
        "queue_key": _PUBLISH_QUEUE_KEY,
        "publish_items": [{"sku": p.get("sku"), "channels": p.get("publish_channels")} for p in queue_items],
    }


def _stage_sell_track(compose: dict[str, Any], *, survival_goal_cny: int) -> dict[str, Any]:
    """_stage_sell_track。

    参数说明：
    :param compose: 参数 compose
    :param survival_goal_cny: 参数 survival_goal_cny
    :return: 返回处理结果。
    """
    assert_greedy_action("run_revenue_loop")
    asset = compose.get("asset") or {}
    opportunities = []
    if asset.get("sales_plan"):
        opportunities.append({"type": "b2b_inquiry_pipeline", "status": "tracking"})
    if asset.get("finance_plan"):
        opportunities.append({"type": "digital_goods_or_affiliate", "status": "tracking"})
    return {
        "stage": "L5_sell_track",
        "daily_target_cny": survival_goal_cny,
        "opportunities": opportunities,
        "note": "卖出由外链/询盘/数字品平台完成；分身只跟踪 opportunity 信号",
    }


def _stage_collect(db: Session) -> dict[str, Any]:
    """_stage_collect。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    assert_greedy_action("read_probe")
    from app.services.hermes.platform_survival_service import greedy_survival_pulse
    pulse = greedy_survival_pulse(db)
    return {
        "stage": "L6_collect",
        "survival_pulse": pulse,
        "kpi_met": (pulse.get("progress_pct") or 0) >= 100,
        "collect_mode": "webhook_or_manual_worldfirst_record",
        "record_action": "record_survival_settlement",
    }


async def run_greedy_revenue_loop_async(
    db: Session,
    *,
    message: str = "",
    locale: str = "global",
    survival_goal_cny: int = 1000,
    max_agency_steps: int | None = 8,
    trigger: str = "api",
) -> dict[str, Any]:
    """摸金校尉一整轮：六段闭环。"""
    assert_greedy_action("run_revenue_loop")
    s1 = await _stage_research(db, locale=locale, message=message)
    s2 = await _stage_orchestrate(
        db,
        locale=locale,
        message=message,
        survival_goal_cny=survival_goal_cny,
        max_steps=max_agency_steps,
    )
    s3 = _stage_compose(s2)
    s4 = _stage_publish(db, s3, locale=locale)
    s5 = _stage_sell_track(s3, survival_goal_cny=survival_goal_cny)
    s6 = _stage_collect(db)
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "trigger": trigger,
        "codename": greedy_constitution_payload().get("codename"),
        "agent_id": "hermes_greedy_core",
        "saas_hermes_untouched": True,
        "stages": [s1, s2, s3, s4, s5, s6],
        "loop_complete": True,
        "constitution": greedy_constitution_payload(),
        "auto_publish_enabled": _greedy_auto_publish_enabled(),
    }
    assert_greedy_action("write_greedy_snapshot")
    if redis_client:
        redis_client.set(_LOOP_SNAPSHOT_KEY, json.dumps(report, ensure_ascii=False), ex=86400 * 7)

    logger.info("Greedy revenue loop [%s] kpi_met=%s", trigger, (s6.get("survival_pulse") or {}).get("progress_pct"))
    try:
        from app.services.hermes.greedy_contest_memory_service import settle_revenue_loop_contest
        report["contest"] = settle_revenue_loop_contest(report)
    except Exception as exc:
        logger.warning("Greedy contest settle skipped: %s", exc)
        report["contest"] = {"error": str(exc)[:120]}

    return report


def run_greedy_revenue_loop(db: Session, **kwargs: Any) -> dict[str, Any]:
    """run_greedy_revenue_loop。

    参数说明：
    :param db: 参数 db
    :param **kwargs: 参数 **kwargs
    :return: 返回处理结果。
    """
    return _safe_asyncio_run(run_greedy_revenue_loop_async(db, **kwargs))


def get_greedy_publish_queue(*, limit: int = 50) -> dict[str, Any]:
    """L4 Redis 发布队列（人工审核 / 自动发布关闭时 staging）。"""
    assert_greedy_action("read_probe")
    cap = max(1, min(int(limit), 100))
    items: list[dict[str, Any]] = []
    if redis_client:
        try:
            raw_list = redis_client.lrange(_PUBLISH_QUEUE_KEY, 0, cap - 1) or []
            for idx, raw in enumerate(raw_list):
                try:
                    payload = json.loads(raw)
                except (json.JSONDecodeError, TypeError):
                    payload = {"raw": str(raw)[:200]}
                if isinstance(payload, dict):
                    payload.setdefault("queue_index", idx)
                    items.append(payload)
        except Exception as exc:
            logger.debug("publish queue read failed: %s", exc)
    return {
        "queue_key": _PUBLISH_QUEUE_KEY,
        "depth": len(items) if items else (int(redis_client.llen(_PUBLISH_QUEUE_KEY) or 0) if redis_client else 0),
        "auto_publish_enabled": _greedy_auto_publish_enabled(),
        "items": items,
    }


def greedy_revenue_loop_status() -> dict[str, Any]:
    """greedy_revenue_loop_status。
    :return: 返回处理结果。
    """
    assert_greedy_action("read_probe")
    snap = None
    if redis_client:
        raw = redis_client.get(_LOOP_SNAPSHOT_KEY)
        if raw:
            try:
                snap = json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                snap = None
    queue_len = 0
    if redis_client:
        queue_len = int(redis_client.llen(_PUBLISH_QUEUE_KEY) or 0)
    return {
        "stages": list(REVENUE_LOOP_STAGES),
        "constitution": greedy_constitution_payload(),
        "latest_loop": snap,
        "publish_queue_depth": queue_len,
        "auto_publish_enabled": _greedy_auto_publish_enabled(),
    }
