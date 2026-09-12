"""摸金校尉总控 Hub — 一次拉取累计/大赛/耐力/闭环/队列/生存脉搏。"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.services.hermes.greedy_avatar_constitution import assert_greedy_action


def greedy_hub_snapshot(db: Session) -> dict[str, Any]:
    """greedy_hub_snapshot。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    assert_greedy_action("read_probe")
    out: dict[str, Any] = {"ok": True}
    try:
        from app.services.hermes.greedy_cumulative_personality_service import get_cumulative_stats
        out["cumulative"] = get_cumulative_stats()
        out["personality_mood"] = (out["cumulative"].get("personality") or {}).get("mood")
    except Exception as exc:
        out["cumulative"] = {"error": str(exc)[:120]}

    try:
        from app.services.hermes.greedy_contest_memory_service import contest_status_summary
        out["contest"] = contest_status_summary()
    except Exception as exc:
        out["contest"] = {"error": str(exc)[:120]}

    try:
        from app.services.hermes.greedy_contest_memory_service import get_endurance_status
        from app.services.hermes.greedy_endurance_scheduler import greedy_endurance_scheduler
        endurance = get_endurance_status()
        endurance["scheduler_7x24"] = greedy_endurance_scheduler.status()
        out["endurance"] = endurance
    except Exception as exc:
        out["endurance"] = {"error": str(exc)[:120]}

    try:
        from app.services.hermes.greedy_revenue_loop_service import greedy_revenue_loop_status
        from app.services.hermes.greedy_revenue_loop_scheduler import greedy_revenue_loop_scheduler
        loop = greedy_revenue_loop_status()
        loop["scheduler"] = greedy_revenue_loop_scheduler.status()
        out["revenue_loop"] = loop
    except Exception as exc:
        out["revenue_loop"] = {"error": str(exc)[:120]}

    try:
        from app.services.hermes.greedy_revenue_loop_service import get_greedy_publish_queue
        from app.services.hermes.greedy_publish_queue_service import get_publish_review_history
        out["publish_queue"] = get_greedy_publish_queue(limit=5)
        out["publish_review_history"] = get_publish_review_history(limit=5)
    except Exception as exc:
        out["publish_queue"] = {"error": str(exc)[:120]}

    try:
        from app.services.hermes.greedy_survival_publish_service import list_survival_publish_tasks
        out["survival_publish_tasks"] = list_survival_publish_tasks(db, limit=8)
    except Exception as exc:
        out["survival_publish_tasks"] = {"error": str(exc)[:120]}

    try:
        from app.services.hermes.platform_survival_service import survival_status
        surv = survival_status(db, recent_limit=5)
        out["survival"] = {
            "pulse": surv.get("pulse"),
            "recent_entries": surv.get("recent_entries"),
            "primary_rail": surv.get("primary_rail"),
        }
    except Exception as exc:
        out["survival"] = {"error": str(exc)[:120]}

    try:
        from app.services.hermes.greedy_survival_digest_scheduler import greedy_survival_digest_scheduler
        out["digest_scheduler"] = greedy_survival_digest_scheduler.status()
    except Exception as exc:
        out["digest_scheduler"] = {"error": str(exc)[:120]}

    try:
        from app.services.hermes.greedy_production_readiness_service import greedy_production_readiness
        out["production_readiness"] = greedy_production_readiness(db)
    except Exception as exc:
        out["production_readiness"] = {"error": str(exc)[:120]}

    return out
