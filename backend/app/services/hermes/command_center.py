"""L0 超管司令部 — 聚合 Hermes / DeerFlow / SEO / 视频 Worker 态势（只读）。"""

from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.deerflow_job import DeerflowJob
from app.services.hermes.maintenance_constitution import assert_maintenance_action
from app.services.hermes.ops_autopilot import load_ops_snapshot
from app.services.hermes.site_patrol_service import patrol_status
from app.services.publish_queue_service import queue_stats
from app.services.publish_workers.tier_router import preflight_workers

logger = logging.getLogger(__name__)


def _deerflow_queue_stats(db: Session) -> dict[str, Any]:
    """_deerflow_queue_stats。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    counts: dict[str, int] = {s: 0 for s in ("queued", "running", "success", "failed")}
    rows = (
        db.query(DeerflowJob.status, func.count())
        .filter(DeerflowJob.status.in_(tuple(counts.keys())))
        .group_by(DeerflowJob.status)
        .all()
    )
    for status, total in rows:
        if status in counts:
            counts[str(status)] = int(total or 0)
    return {
        "counts": counts,
        "pending": counts.get("queued", 0) + counts.get("running", 0),
        "failed": counts.get("failed", 0),
    }


def _seo_snapshot(db: Session) -> dict[str, Any]:
    """_seo_snapshot。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    from app.services.seo.rank_scheduler_ops import build_rank_scheduler_ops_snapshot
    from app.services.seo.seo_matrix_db_health import seo_matrix_db_health
    out: dict[str, Any] = {
        "rank_scheduler_enabled": bool(getattr(settings, "RANK_SCHEDULER_ENABLED", False)),
        "rank_scheduler": None,
        "rank_scheduler_ops": None,
        "seo_matrix_db": seo_matrix_db_health(),
        "inclusion": None,
        "rank_guard": None,
    }
    try:
        out["rank_scheduler_ops"] = build_rank_scheduler_ops_snapshot(db)
        out["rank_scheduler"] = out["rank_scheduler_ops"].get("scheduler")
    except Exception as exc:
        out["rank_scheduler"] = {"error": str(exc)[:200]}
    try:
        from app.models.content import InclusionStatus
        total = db.query(InclusionStatus).count()
        included = (
            db.query(InclusionStatus)
            .filter(InclusionStatus.is_included.is_(True))
            .count()
        )
        failed = max(total - included, 0)
        out["inclusion"] = {
            "total": total,
            "included": included,
            "failed": failed,
            "inclusion_rate": round((included / total) * 100, 2) if total else 0,
        }
    except Exception:
        out["inclusion"] = {"available": False}
    try:
        from app.services.geo_rank_guard_probe import load_rank_guard_snapshot
        out["rank_guard"] = load_rank_guard_snapshot()
    except Exception:
        out["rank_guard"] = None
    try:
        from app.services.hermes.daily_rank_ops import load_rank_ops_snapshot
        from app.services.hermes.hermes_rank_first_constitution import rank_first_payload
        out["hermes_rank_ops"] = load_rank_ops_snapshot()
        out["hermes_rank_first"] = rank_first_payload()
    except Exception:
        out["hermes_rank_ops"] = None
    return out


def _ai_hangar_snapshot(db: Session) -> dict[str, Any]:
    """_ai_hangar_snapshot。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    from app.services.ai_key_probe import ai_key_status
    from app.services.scenario_health_store import load_health_snapshot
    keys = ai_key_status(db)
    health = load_health_snapshot(db) or {}
    return {
        "has_real_key": bool(keys.get("has_real_key")),
        "providers": keys.get("providers") or [],
        "environment": keys.get("environment"),
        "scenario_health": {
            "healthy_count": health.get("healthy_count", 0),
            "unhealthy_count": health.get("unhealthy_count", 0),
            "total": health.get("total", 0),
            "saved_at": health.get("saved_at"),
        },
    }


def _ai_lane_snapshot(db: Session) -> dict[str, Any]:
    """_ai_lane_snapshot。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    from app.services.hermes.hermes_ai_lanes_service import build_ai_lane_snapshot
    return build_ai_lane_snapshot(db)


def _integrations_health_snapshot() -> dict[str, Any]:
    """_integrations_health_snapshot。
    :return: 返回处理结果。
    """
    from app.services.ubrain.mem0_batch_sync_service import integrations_health_snapshot
    return integrations_health_snapshot()


def _flywheel_pipeline_snapshot(db: Session) -> dict[str, Any]:
    """_flywheel_pipeline_snapshot。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    from app.models.ubrain_commercial_os import UbrainPipelineRun, UbrainResearchInsight
    pipelines = (
        db.query(UbrainPipelineRun)
        .order_by(UbrainPipelineRun.created_at.desc())
        .limit(8)
        .all()
    )
    items = []
    for row in pipelines:
        items.append(
            {
                "id": row.id,
                "tenant_id": row.tenant_id,
                "status": row.status,
                "insight_id": row.insight_id,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
        )
    insight_total = db.query(UbrainResearchInsight).count()
    pipeline_total = db.query(UbrainPipelineRun).count()
    return {
        "insight_total": insight_total,
        "pipeline_total": pipeline_total,
        "recent": items,
    }


def _tenant_plan_snapshot(db: Session) -> dict[str, Any]:
    """_tenant_plan_snapshot。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    from app.services.ubrain.deerflow_tenant_quota import (
        _plan_codes_allowed,
        monthly_limit,
        resolve_eligible_schedule_tenant_ids,
    )
    eligible, skipped = resolve_eligible_schedule_tenant_ids(db, force=False)
    return {
        "schedule_plan_codes": sorted(_plan_codes_allowed()),
        "monthly_limit_per_tenant": monthly_limit(),
        "eligible_count": len(eligible),
        "skipped_count": len(skipped),
        "skipped_sample": skipped[:5],
        "auto_enqueue": bool(getattr(settings, "DEERFLOW_SCHEDULE_AUTO_ENQUEUE_ENABLED", False)),
    }


def _integrations_snapshot() -> dict[str, Any]:
    """_integrations_snapshot。
    :return: 返回处理结果。
    """
    from app.services.ubrain.flywheel_integrations import flywheel_integrations_status
    from app.services.ubrain.deerflow_sidecar import deerflow_sidecar_status
    base = flywheel_integrations_status()
    base["deerflow_sidecar_detail"] = deerflow_sidecar_status()
    return base


def _deerflow_slo_snapshot(db: Session) -> dict[str, Any]:
    """_deerflow_slo_snapshot。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    from app.services.hermes.deerflow_ops_service import deerflow_slo_snapshot
    return deerflow_slo_snapshot(db)


def _recent_publish_snapshot(db: Session) -> dict[str, Any]:
    """_recent_publish_snapshot。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    from app.services.hermes.publish_history_aggregate import list_unified_publish_history
    return list_unified_publish_history(db, limit=15)


def _rum_snapshot(db: Session) -> dict[str, Any]:
    """_rum_snapshot。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    from app.services.rum_metrics_service import load_rum_snapshot
    return load_rum_snapshot(db) or {"sample_count": 0, "source": "none"}


def _patrol_trend_snapshot(db: Session) -> list[dict[str, Any]]:
    """_patrol_trend_snapshot。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    from app.services.hermes.site_patrol_store import load_patrol_trend
    return load_patrol_trend(db)


def _ecc_hangar_snapshot(db: Session, ops: dict[str, Any] | None = None) -> dict[str, Any]:
    """_ecc_hangar_snapshot。

    参数说明：
    :param db: 参数 db
    :param ops: 参数 ops
    :return: 返回处理结果。
    """
    from app.services.hermes.ecc_expert_panel import panel_meta
    meta = panel_meta()
    ops = ops if ops is not None else (load_ops_snapshot() or {})
    tech = ops.get("tech_radar") or {}
    candidates = tech.get("candidates") or []
    recent_reviews = []
    for c in candidates[:12]:
        reviews = c.get("expert_reviews") or []
        if reviews:
            recent_reviews.append(
                {
                    "title": c.get("title"),
                    "url": c.get("url"),
                    "impact": c.get("impact"),
                    "expert_verdict": c.get("expert_verdict"),
                    "reviews": reviews[:3],
                }
            )
    return {
        **meta,
        "recent_reviews": recent_reviews[:8],
        "tech_radar_saved_at": tech.get("fetched_at") or ops.get("saved_at"),
    }


def _build_command_center_snapshot_uncached(db: Session) -> dict[str, Any]:
    """只读聚合（无缓存层）；供缓存模块与测试直接调用。"""
    assert_maintenance_action("read_probe")
    sections, ops, ecc_hangar, overall, built_ms = _run_command_center_sections(db)
    payload = _assemble_command_center_payload(sections, ops, ecc_hangar, overall, built_ms)
    logger.info("command_center snapshot built in %sms", built_ms)
    return payload

def _run_command_center_sections(db: Session) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], str, int]:
    """_run_command_center_sections。

    参数说明：
    :return: 返回 (sections, ops, ecc_hangar, overall, built_ms)。
    """
    from app.services.ubrain.deerflow_scheduled_service import load_deerflow_schedule_snapshot
    from app.services.ubrain.deerflow_scheduler import deerflow_scheduler
    def _safe(label: str, fn: Callable[[], Any], default: Any) -> Any:
        """_safe。

        参数说明：
        :param label: 参数 label
        :param fn: 参数 fn
        :param default: 参数 default
        :return: 返回处理结果。
        """
        try:
            return fn()
        except Exception as exc:
            logger.warning("command_center section %s failed: %s", label, exc)
            if isinstance(default, dict):
                return {**default, "error": str(exc)[:200]}
            return default

    def _db_task(label: str, fn: Callable[[Session], Any], default: Any) -> Callable[[], Any]:
        """_db_task。

        参数说明：
        :param label: 参数 label
        :param fn: 参数 fn
        :param default: 参数 default
        :return: 返回处理结果。
        """
        def run() -> Any:
            """run。
            :return: 返回处理结果。
            """
            from app.core.database import SessionLocal
            sdb = SessionLocal()
            try:
                return _safe(label, lambda: fn(sdb), default)
            finally:
                sdb.close()

        return run

    started = time.perf_counter()
    tasks: dict[str, Callable[[], Any]] = {
        "ops_autopilot": lambda: _safe("ops_autopilot", load_ops_snapshot, {}) or {},
        "patrol": _db_task("patrol", patrol_status, {"latest": {}}),
        "deerflow_scheduler": lambda: _safe("deerflow_scheduler", deerflow_scheduler.status, {}),
        "deerflow_latest": lambda: _safe("deerflow_latest", load_deerflow_schedule_snapshot, {}) or {},
        "deerflow_queue": _db_task("deerflow_queue", _deerflow_queue_stats, {"counts": {}}),
        "video_workers": lambda: _safe("video_workers", preflight_workers, {"ready": False, "workers": {}}),
        "publish_queue": _db_task("publish_queue", queue_stats, {}),
        "seo": _db_task("seo", _seo_snapshot, {}),
        "ai_hangar": _db_task("ai_hangar", _ai_hangar_snapshot, {}),
        "ai_lane_scenarios": _db_task("ai_lane", _ai_lane_snapshot, {}),
        "integrations_health": lambda: _safe("integrations_health", _integrations_health_snapshot, {}),
        "flywheel_pipeline": _db_task("flywheel", _flywheel_pipeline_snapshot, {}),
        "tenant_plans": _db_task("tenant_plans", _tenant_plan_snapshot, {}),
        "integrations": lambda: _safe("integrations", _integrations_snapshot, {}),
        "deerflow_slo": _db_task("deerflow_slo", _deerflow_slo_snapshot, {}),
        "recent_publish": _db_task("recent_publish", _recent_publish_snapshot, {"items": []}),
        "rum": _db_task("rum", _rum_snapshot, {"sample_count": 0}),
        "patrol_trend": _db_task("patrol_trend", _patrol_trend_snapshot, []),
    }
    sections: dict[str, Any] = {}
    workers = 2 if settings.DB_TYPE == "sqlite" else 8
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(fn): key for key, fn in tasks.items()}
        for fut in as_completed(futures):
            key = futures[fut]
            try:
                sections[key] = fut.result()
            except Exception as exc:
                logger.warning("command_center parallel %s failed: %s", key, exc)
                sections[key] = {"error": str(exc)[:200]}

    ops = sections.get("ops_autopilot") or {}
    ecc_hangar = _safe(
        "ecc_hangar",
        lambda: _ecc_hangar_snapshot(db, ops=ops if isinstance(ops, dict) else None),
        {},
    )
    patrol = sections.get("patrol") or {"latest": {}}
    patrol_latest = patrol.get("latest") or {}
    overall = patrol_latest.get("overall_status") or "unknown"
    return sections, ops, ecc_hangar, overall, built_ms


def _assemble_command_center_payload(
    sections: dict[str, Any],
    ops: dict[str, Any],
    ecc_hangar: dict[str, Any],
    overall: str,
    built_ms: int,
) -> dict[str, Any]:
    """_assemble_command_center_payload。

    参数说明：
    :return: 返回处理结果。
    """
    payload = {
        "positioning": "L0_super_admin_command_core",
        "overall_status": overall,
        "ops_autopilot": ops,
        "patrol": patrol,
        "deerflow": {
            "scheduler": sections.get("deerflow_scheduler") or {},
            "latest": sections.get("deerflow_latest") or {},
            "queue": sections.get("deerflow_queue") or {"counts": {}},
        },
        "seo": sections.get("seo") or {},
        "ai_hangar": sections.get("ai_hangar") or {},
        "ai_lane_scenarios": sections.get("ai_lane_scenarios") or {},
        "integrations_health": sections.get("integrations_health") or {},
        "flywheel_pipeline": sections.get("flywheel_pipeline") or {},
        "tenant_plans": sections.get("tenant_plans") or {},
        "integrations": sections.get("integrations") or {},
        "ecc_hangar": ecc_hangar,
        "deerflow_slo": sections.get("deerflow_slo") or {},
        "recent_publish": sections.get("recent_publish") or {"items": []},
        "rum": sections.get("rum") or {"sample_count": 0},
        "patrol_trend": sections.get("patrol_trend") or [],
        "video_workers": sections.get("video_workers") or {"ready": False, "workers": {}},
        "publish_queue": sections.get("publish_queue") or {},
        "built_ms": built_ms,
        "cache_hit": False,
        "cache_layer": "live",
        "config_flags": {
            "hermes_ops_autopilot_enabled": bool(
                getattr(settings, "HERMES_OPS_AUTOPILOT_ENABLED", False)
            ),
            "hermes_ops_drain_limit": int(getattr(settings, "HERMES_OPS_DRAIN_LIMIT", 3)),
            "deerflow_scheduler_enabled": bool(
                getattr(settings, "DEERFLOW_SCHEDULER_ENABLED", False)
            ),
            "deerflow_schedule_auto_enqueue": bool(
                getattr(settings, "DEERFLOW_SCHEDULE_AUTO_ENQUEUE_ENABLED", False)
            ),
            "rank_scheduler_enabled": bool(getattr(settings, "RANK_SCHEDULER_ENABLED", False)),
        },
        "quick_actions": [
            {"id": "hermes_ops_run", "method": "POST", "path": "/hermes/ops/run", "label": "Hermes 运维循环"},
            {"id": "deerflow_run", "method": "POST", "path": "/hermes/ops/deerflow/run", "label": "DeerFlow 研究+队列"},
            {"id": "patrol", "method": "POST", "path": "/hermes/ops/instruct", "body": {"command": "patrol"}, "label": "仅巡站"},
            {"id": "rank_guard", "method": "POST", "path": "/hermes/ops/rank-guard/check", "label": "Rank Guard 检测"},
            {"id": "inclusion_recheck", "method": "POST", "path": "/hermes/ops/inclusion/recheck", "label": "收录复检"},
            {"id": "tech_radar", "method": "POST", "path": "/hermes/ops/instruct", "body": {"command": "rerun_tech_radar"}, "label": "技术雷达"},
            {"id": "deerflow_jobs", "method": "GET", "path": "/hermes/ops/deerflow/jobs", "label": "DeerFlow 队列明细"},
            {"id": "publish_history", "method": "GET", "path": "/hermes/ops/publish-history", "label": "统一发布历史"},
            {"id": "rank_scheduler", "method": "GET", "path": "/hermes/ops/rank-scheduler", "label": "Rank Scheduler"},
            {"id": "rank_scheduler_sync", "method": "POST", "path": "/hermes/ops/rank-scheduler/sync", "label": "同步关键词"},
            {"id": "brand_audit", "method": "GET", "path": "/hermes/ops/brand-audit", "label": "品牌抽检"},
            {"id": "tech_radar_reports", "method": "GET", "path": "/hermes/ops/tech-radar/reports", "label": "雷达日报"},
            {"id": "write_boundary_audit", "method": "GET", "path": "/hermes/ops/write-boundary-audit", "label": "写库边界审计"},
            {"id": "mem0_sync", "method": "POST", "path": "/hermes/ops/integrations/mem0/sync", "label": "Mem0 双写"},
        ],
    }
    return payload

