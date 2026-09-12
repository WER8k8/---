"""Hermes 安全自愈 — 仅白名单动作，违宪即拒绝。"""

from __future__ import annotations

import logging
from typing import Any

from app.core.config import settings
from app.services.hermes.maintenance_constitution import assert_maintenance_action

logger = logging.getLogger("uj-admin.hermes_safe_remediation")

# 允许自动执行的动作（硬编码，不可配置扩展为删库/发版）
SAFE_ACTIONS: frozenset[str] = frozenset(
    {
        "invalidate_ai_model_cache",
        "rerun_scenario_health_probe",
        "bootstrap_agency_ollama",
    }
)


def _auto_enabled() -> bool:
    """_auto_enabled。
    :return: 返回处理结果。
    """
    flag = getattr(settings, "HERMES_AUTO_REMEDIATION_ENABLED", None)
    if flag is not None:
        return bool(flag)
    return (settings.ENVIRONMENT or "").strip().lower() == "production"


def run_safe_remediation(db, failed_probes: list[dict[str, Any]]) -> dict[str, Any]:
    """根据失败探测项尝试安全自愈；无法自愈则留给告警+人工。"""
    if not _auto_enabled():
        return {"attempted": False, "reason": "auto_remediation_disabled", "actions": []}

    actions: list[dict[str, Any]] = []
    ids = {p.get("id") for p in failed_probes}
    if "scenario_health" in ids:
        try:
            assert_maintenance_action("read_probe")
            from app.services.scenario_health_scheduler import run_scenario_health_check
            report = run_scenario_health_check()
            actions.append(
                {
                    "action": "rerun_scenario_health_probe",
                    "ok": True,
                    "detail": {
                        "healthy_count": report.get("healthy_count"),
                        "unhealthy_count": report.get("unhealthy_count"),
                    },
                }
            )
        except Exception as exc:
            actions.append({"action": "rerun_scenario_health_probe", "ok": False, "error": str(exc)})

    if "ai_connect" in ids or "readiness" in ids:
        try:
            assert_maintenance_action("read_probe")
            from app.core.cache import invalidate_ai_model_cache
            invalidate_ai_model_cache()
            actions.append({"action": "invalidate_ai_model_cache", "ok": True})
        except Exception as exc:
            actions.append({"action": "invalidate_ai_model_cache", "ok": False, "error": str(exc)})

    if "agency_llm" in ids:
        try:
            assert_maintenance_action("read_probe")
            from app.services.hermes.agency.provider_setup import run_automated_bootstrap
            boot = run_automated_bootstrap(pull_ollama_model=True)
            ok_after = int(boot.get("available_after") or 0)
            actions.append(
                {
                    "action": "bootstrap_agency_ollama",
                    "ok": ok_after > 0,
                    "detail": {
                        "available_after": ok_after,
                        "bootstrap_results": boot.get("bootstrap_results"),
                    },
                }
            )
        except Exception as exc:
            actions.append({"action": "bootstrap_agency_ollama", "ok": False, "error": str(exc)})

    ok_count = sum(1 for a in actions if a.get("ok"))
    return {
        "attempted": bool(actions),
        "actions": actions,
        "summary": f"已执行 {ok_count}/{len(actions)} 项安全自愈" if actions else "无可自动处理项",
    }


def execute_human_instruction(db, command: str) -> dict[str, Any]:
    """超管/飞书跟进指令 — 仍受宪法约束。"""
    cmd = (command or "").strip().lower()
    if cmd in ("rerun_patrol", "patrol", "巡站"):
        from app.services.hermes.site_patrol_service import run_site_patrol
        return {"command": cmd, "result": run_site_patrol(db, trigger="human_instruction")}

    if cmd in ("rerun_tech_radar", "tech_radar", "技术雷达"):
        from app.services.hermes.ops_autopilot import run_tech_radar_cycle
        report = run_tech_radar_cycle(db, trigger="human_instruction")
        from app.services.hermes.tech_radar_markdown_export import export_tech_radar_markdown
        md = export_tech_radar_markdown(report)
        return {"command": cmd, "result": report, "markdown_export": md}

    if cmd in ("export_tech_radar_md", "radar_md"):
        from app.services.hermes.ops_autopilot import load_ops_snapshot
        from app.services.hermes.tech_radar_markdown_export import export_tech_radar_markdown
        snap = load_ops_snapshot() or {}
        md = export_tech_radar_markdown(snap.get("tech_radar"))
        return {"command": cmd, "markdown_export": md}

    if cmd in ("ack", "ack_alert", "ack_tech_radar", "已读"):
        assert_maintenance_action("emit_alert")
        return {"command": cmd, "result": "ack_recorded", "note": "告警已确认，冷却不变"}

    if cmd in ("rerun_deerflow", "deerflow", "市场研究"):
        from app.services.ubrain.deerflow_scheduled_service import run_scheduled_deerflow_update
        return {
            "command": cmd,
            "result": run_scheduled_deerflow_update(db, trigger="human_instruction", force=True),
        }

    if cmd in ("deerflow_pending", "消费队列"):
        from app.services.ubrain.deerflow_scheduled_service import run_deerflow_pending_only
        return {"command": cmd, "result": run_deerflow_pending_only(db, trigger="human_instruction")}

    if cmd in ("full_cycle", "full", "全套"):
        from app.services.hermes.ops_autopilot import run_full_ops_cycle
        return {"command": cmd, "result": run_full_ops_cycle(db, trigger="human_instruction")}

    return {
        "command": cmd,
        "error": "未知指令",
        "allowed": [
            "rerun_patrol",
            "rerun_tech_radar",
            "export_tech_radar_md",
            "rerun_deerflow",
            "deerflow_pending",
            "full_cycle",
            "ack",
        ],
    }
