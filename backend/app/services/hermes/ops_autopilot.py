"""Hermes 运维自动驾驶 — 巡站 + 技术雷达 + 自愈 + 飞书通知。"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.core.cache import redis_client
from app.core.config import settings
from app.services.geo.tech_radar_fetch import fetch_tech_radar
from app.services.hermes.alert_dispatcher import notify_patrol_report, notify_tech_radar
from app.services.hermes.maintenance_constitution import assert_maintenance_action
from app.services.hermes.safe_remediation import run_safe_remediation
from app.services.hermes.site_patrol_service import run_site_patrol
from app.services.hermes.tech_validation import validate_all

logger = logging.getLogger("uj-admin.hermes_ops_autopilot")

OPS_SNAPSHOT_KEY = "hermes_ops_autopilot_latest"


def _save_ops_snapshot(db: Session, payload: dict[str, Any]) -> dict[str, Any]:
    """_save_ops_snapshot。

    参数说明：
    :param db: 参数 db
    :param payload: 参数 payload
    :return: 返回处理结果。
    """
    assert_maintenance_action("write_patrol_snapshot")
    body = {**payload, "saved_at": datetime.now(timezone.utc).isoformat()}
    if redis_client:
        redis_client.set(OPS_SNAPSHOT_KEY, json.dumps(body, ensure_ascii=False), ex=86400 * 14)
    return body


def run_tech_radar_cycle(db: Session, *, trigger: str = "scheduler") -> dict[str, Any]:
    """抓取 → Hermes 验证 → 快照；高影响项通知人工。"""
    assert_maintenance_action("read_probe")
    fetched = fetch_tech_radar(limit_per_source=5)
    validated = validate_all(fetched.get("candidates") or [], db, expert_review=True)
    high_impact = [c for c in validated if c.get("impact") == "high"]
    expert_fail = [c for c in validated if c.get("expert_verdict") == "fail"]
    failed_validation = [c for c in validated if c.get("validation_status") == "fail"]
    notify_worthy = bool(expert_fail or high_impact or fetched.get("fetch_errors"))
    report: dict[str, Any] = {
        "trigger": trigger,
        "mode": "fetch_validate_ecc_expert",
        "fetched_at": fetched.get("fetched_at"),
        "fetch_errors": fetched.get("fetch_errors") or [],
        "candidates": validated,
        "high_impact_count": len(high_impact),
        "expert_fail_count": len(expert_fail),
        "validation_fail_count": len(failed_validation),
        "rules": [
            "only_public_sources",
            "no_direct_production_hot_update",
            "ecc_expert_readonly_review",
            "hermes_validates_then_notify",
        ],
    }
    # 同步更新 geo tech radar redis 键（兼容旧 MVP）
    if redis_client:
        day = datetime.now(timezone.utc).strftime("%Y%m%d")
        redis_client.set(
            f"geo:tech_radar:{day}",
            json.dumps({"status": "completed", "report": report}, ensure_ascii=False),
            ex=86400 * 7,
        )

    alert = {"sent": False}
    if notify_worthy:
        report["saved_at"] = datetime.now(timezone.utc).isoformat()
        alert = notify_tech_radar(report)

    report["alert"] = alert
    try:
        from app.services.hermes.tech_radar_markdown_export import export_tech_radar_markdown
        md = export_tech_radar_markdown(report)
        report["markdown_export"] = md
    except Exception as exc:
        logger.warning("Tech radar markdown export skipped: %s", exc)
        report["markdown_export"] = {"ok": False, "reason": str(exc)[:200]}

    logger.info(
        "Tech radar cycle [%s] candidates=%s high=%s alert=%s",
        trigger,
        len(validated),
        len(high_impact),
        alert.get("sent"),
    )
    return report


def run_full_ops_cycle(db: Session, *, trigger: str = "scheduler", notify: bool = True) -> dict[str, Any]:
    """完整运维循环：排名攻坚 → 技术雷达 → 巡站 → 安全自愈 → 飞书。"""
    rank_ops: dict[str, Any] = {}
    try:
        from app.services.hermes.daily_rank_ops import run_hermes_daily_rank_cycle
        rank_ops = run_hermes_daily_rank_cycle(db, trigger=f"{trigger}:rank_first")
    except Exception as exc:
        logger.warning("Hermes daily rank cycle skipped: %s", exc)
        rank_ops = {"error": str(exc)[:200]}

    tech = run_tech_radar_cycle(db, trigger=f"{trigger}:tech_radar")
    patrol = run_site_patrol(db, trigger=f"{trigger}:patrol")
    failed = [p for p in patrol.get("probes") or [] if p.get("status") == "fail"]
    remediation = run_safe_remediation(db, failed)
    deerflow_pending = {"processed": 0}
    try:
        from app.services.ubrain.deerflow_scheduled_service import run_deerflow_pending_only
        deerflow_pending = run_deerflow_pending_only(
            db,
            trigger=f"{trigger}:deerflow_pending",
            lane="ops",
        )
    except Exception as exc:
        logger.warning("DeerFlow ops drain skipped: %s", exc)

    continuous_iteration: dict[str, Any] = {}
    try:
        from app.services.hermes.hermes_continuous_iteration_service import run_continuous_iteration_cycle
        continuous_iteration = run_continuous_iteration_cycle(
            db,
            trigger=f"{trigger}:continuous_iteration",
            include_deerflow_drain=False,
        )
    except Exception as exc:
        logger.warning("Hermes continuous iteration skipped: %s", exc)
        continuous_iteration = {"error": str(exc)[:200]}

    gw_ops: dict[str, Any] = {}
    try:
        from app.services.foreign_trade.aeo_fact_audit_service import run_aeo_fact_audit
        from app.services.foreign_trade.platform_health_alert_service import (
            run_platform_health_alert_cycle,
        )
        gw_ops = {
            "aeo_fact_audit": run_aeo_fact_audit(db),
            "platform_health": run_platform_health_alert_cycle(db, hours=24, notify=True),
        }
    except Exception as exc:
        logger.warning("GW P0 ops cycle skipped: %s", exc)
        gw_ops = {"error": str(exc)[:200]}

    # 自愈后可选再探一轮（只读）
    if remediation.get("attempted") and remediation.get("actions"):
        patrol = run_site_patrol(db, trigger=f"{trigger}:patrol_after_remediation")

    alert = {"sent": False}
    if notify and patrol.get("overall_status") in ("critical", "degraded"):
        alert = notify_patrol_report(patrol, remediation=remediation)

    body = _save_ops_snapshot(
        db,
        {
            "trigger": trigger,
            "rank_ops": rank_ops,
            "tech_radar": tech,
            "patrol": patrol,
            "remediation": remediation,
            "deerflow_pending": deerflow_pending,
            "continuous_iteration": continuous_iteration,
            "gw_ops": gw_ops,
            "alert": alert,
        },
    )
    return body


def load_ops_snapshot() -> dict[str, Any] | None:
    """load_ops_snapshot。
    :return: 返回处理结果。
    """
    assert_maintenance_action("read_probe")
    from app.core.cache import redis_available
    if not redis_available():
        return None
    try:
        raw = redis_client.get(OPS_SNAPSHOT_KEY)
    except Exception as exc:
        logger.warning("load_ops_snapshot redis get failed: %s", exc)
        return None
    if not raw:
        return None
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None
