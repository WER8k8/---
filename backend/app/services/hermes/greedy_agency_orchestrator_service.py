"""Hermes 财迷疯 × agency-agents-zh — 专家库编排（SaaS 内嵌 220+ 角色）。"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.core.cache import redis_client
from app.services.hermes.agency.orchestrator_bridge import agency_catalog
from app.services.hermes.agency.role_loader import list_roles, load_role, roles_meta
from app.services.hermes.agency.workflow_runner import list_workflows, run_workflow_async
from app.services.hermes.greedy_avatar_constitution import assert_greedy_action

logger = logging.getLogger("uj-admin.hermes_greedy_agency")

_CONFIG_PATH = Path(__file__).resolve().parents[2] / "data" / "hermes_greedy_agency_orchestration.json"
_SNAPSHOT_KEY = "hermes:greedy_agency:latest_plan"


@lru_cache(maxsize=1)
def load_greedy_agency_config() -> dict[str, Any]:
    """load_greedy_agency_config。
    :return: 返回处理结果。
    """
    with open(_CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def _resolve_playbook(
    *,
    intent: str | None = None,
    survival_mood: str | None = None,
    progress_pct: float | None = None,
) -> dict[str, Any] | None:
    """_resolve_playbook。

    参数说明：
    :param intent: 参数 intent
    :param survival_mood: 参数 survival_mood
    :param progress_pct: 参数 progress_pct
    :return: 返回处理结果。
    """
    cfg = load_greedy_agency_config()
    playbooks = list(cfg.get("playbooks") or [])
    playbooks.sort(key=lambda p: int(p.get("priority") or 99))
    intent_key = (intent or "").strip()
    for pb in playbooks:
        when = pb.get("when") or {}
        if intent_key and when.get("intent") == intent_key:
            return pb
        moods = when.get("survival_mood_in") or []
        below = when.get("progress_pct_below")
        if moods and survival_mood in moods:
            if below is None or progress_pct is None or progress_pct < float(below):
                return pb
    return playbooks[0] if playbooks else None


def greedy_agency_status(db: Session | None = None) -> dict[str, Any]:
    """财迷疯视角：内嵌专家库规模 + survival 脉搏 + 推荐 playbook。"""
    assert_greedy_action("read_probe")
    meta = roles_meta()
    cfg = load_greedy_agency_config()
    wfs = list_workflows()
    survival: dict[str, Any] = {}
    mood = "unknown"
    progress_pct: float | None = None
    if db is not None:
        try:
            from app.services.hermes.platform_survival_service import greedy_survival_pulse
            survival = greedy_survival_pulse(db)
            mood = str(survival.get("mood") or "unknown")
            progress_pct = survival.get("progress_pct")
            if progress_pct is not None:
                progress_pct = float(progress_pct)
        except Exception as exc:
            logger.info("survival pulse skipped: %s", exc)

    playbook = _resolve_playbook(survival_mood=mood, progress_pct=progress_pct)
    snap = _load_plan_snapshot()
    from app.services.hermes.role_economics_service import economics_coverage_report
    from app.services.hermes.greedy_contest_memory_service import contest_status_summary
    return {
        "orchestrator": cfg.get("orchestrator_agent"),
        "source_repo": cfg.get("source_repo"),
        "persona_note": cfg.get("persona_note"),
        "agency_embedded": {
            "role_count": meta.get("role_count"),
            "categories": meta.get("categories"),
            "workflow_count": len(wfs),
            "roles_dir": meta.get("roles_dir"),
        },
        "survival_pulse": survival,
        "recommended_playbook": playbook,
        "playbooks": cfg.get("playbooks"),
        "intent_workflow_map": cfg.get("intent_workflow_map"),
        "lane_role_pools": cfg.get("lane_role_pools"),
        "latest_plan": snap,
        "legal_gate": cfg.get("legal_gate"),
        "economics_coverage": economics_coverage_report(),
        "money_contest": contest_status_summary(),
    }


def _collect_survival_pulse(db: Session | None) -> tuple[str, float | None]:
    """读取平台生存脉搏，返回 (mood, progress_pct)；失败时回退 unknown。"""
    if db is None:
        return "unknown", None
    try:
        from app.services.hermes.platform_survival_service import greedy_survival_pulse
        pulse = greedy_survival_pulse(db)
        mood = str(pulse.get("mood") or "unknown")
        progress_pct: float | None = None
        if pulse.get("progress_pct") is not None:
            progress_pct = float(pulse["progress_pct"])
        return mood, progress_pct
    except Exception:
        return "unknown", None


def _resolve_candidate_pool(
    *,
    cfg: dict[str, Any],
    intent: str | None,
    lane: str | None,
    playbook: dict[str, Any] | None,
) -> tuple[str | None, list[str], list[Any]]:
    """解析 workflow_id 与候选专家池，返回 (workflow_id, candidate_ids, ranked)。"""
    intent_map = cfg.get("intent_workflow_map") or {}
    workflow_id = (playbook or {}).get("workflow_id")
    roles_hint: list[str] = []
    if intent and intent in intent_map:
        entry = intent_map[intent]
        workflow_id = entry.get("workflow_id") or workflow_id
        roles_hint = list(entry.get("roles_hint") or [])

    lane_pool: list[str] = []
    if lane:
        lane_pool = list((cfg.get("lane_role_pools") or {}).get(lane) or [])

    from app.services.hermes.role_economics_service import rank_roles_for_survival
    ranked = rank_roles_for_survival(intent=intent, lane=lane, limit=8)
    candidate_ids: list[str] = []
    for rid in roles_hint[:6] + lane_pool[:4] + [r["role_id"] for r in ranked]:
        if rid and rid not in candidate_ids:
            candidate_ids.append(rid)
    return workflow_id, candidate_ids, ranked


def _build_expert_rows(candidate_ids: list[str], ranked: list[Any]) -> list[dict[str, Any]]:
    """组装可上场专家的经济数据行（callable 过滤）。"""
    from app.services.hermes.role_economics_service import resolve_role_economics
    role_rows: list[dict[str, Any]] = []
    for rid in candidate_ids[:10]:
        role = load_role(rid)
        if not role:
            continue
        eco = resolve_role_economics(rid)
        if not eco.get("callable"):
            continue
        role_rows.append(
            {
                "role_id": rid,
                "name": role.get("name"),
                "emoji": role.get("emoji"),
                "economic_tier": eco.get("economic_tier"),
                "monetize_type": eco.get("monetize_type"),
                "deliverable_skus": eco.get("deliverable_skus"),
                "survival_score": next((r.get("survival_score") for r in ranked if r["role_id"] == rid), None),
            }
        )
    return role_rows


def _build_plan_inputs(
    *,
    playbook: dict[str, Any] | None,
    locale: str,
    survival_goal_cny: int,
    message: str,
) -> dict[str, Any]:
    """组装工作流输入默认值与用户覆盖字段。"""
    inputs = dict((playbook or {}).get("input_defaults") or {})
    inputs.update(
        {
            "locale": locale,
            "survival_goal_cny": survival_goal_cny,
            "product_context": (message or inputs.get("product_context") or "")[:500],
        }
    )
    if playbook and playbook.get("id") == "greedy_allhands" and message:
        inputs["idea"] = message[:500]
    return inputs


def _inject_expert_memory(inputs: dict[str, Any], role_rows: list[dict[str, Any]]) -> None:
    """注入历史专家记忆到 inputs（失败时静默降级）。"""
    try:
        from app.services.hermes.greedy_contest_memory_service import format_expert_memory_prompt
        mem_block = format_expert_memory_prompt([r["role_id"] for r in role_rows])
        if mem_block:
            inputs["prior_expert_memory"] = mem_block
            inputs["product_context"] = (
                (inputs.get("product_context") or "") + "\n\n" + mem_block
            )[:3500]
    except Exception as exc:
        logger.debug("expert memory inject skipped: %s", exc)


def _assemble_plan(
    *,
    cfg: dict[str, Any],
    intent: str | None,
    lane: str | None,
    mood: str,
    progress_pct: float | None,
    playbook: dict[str, Any] | None,
    workflow_id: str | None,
    inputs: dict[str, Any],
    role_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    """组装编排计划返回体。"""
    return {
        "planned_at": datetime.now(timezone.utc).isoformat(),
        "orchestrator": cfg.get("orchestrator_agent"),
        "survival_mood": mood,
        "progress_pct": progress_pct,
        "playbook_id": (playbook or {}).get("id"),
        "playbook_label": (playbook or {}).get("label"),
        "workflow_id": workflow_id,
        "inputs": inputs,
        "experts_selected": role_rows,
        "lane": lane,
        "intent": intent,
        "human_review_required": True,
        "constitution": cfg.get("greedy_system_directive"),
        "does_not_mutate": "saas_hermes_tenant_flows_unchanged",
        "economics_mandate": "每位上场专家须携带 monetize_type + deliverable_skus；dormant 角色不得编排",
    }


def plan_greedy_orchestration(
    *,
    intent: str | None = None,
    lane: str | None = None,
    message: str = "",
    locale: str = "global",
    survival_goal_cny: int = 1000,
    db: Session | None = None,
) -> dict[str, Any]:
    """只读编排计划：选 playbook + workflow + 专家池，不调用 LLM。"""
    assert_greedy_action("suggest_remediation")
    cfg = load_greedy_agency_config()
    mood, progress_pct = _collect_survival_pulse(db)

    playbook = _resolve_playbook(intent=intent, survival_mood=mood, progress_pct=progress_pct)
    workflow_id, candidate_ids, ranked = _resolve_candidate_pool(
        cfg=cfg,
        intent=intent,
        lane=lane,
        playbook=playbook,
    )
    role_rows = _build_expert_rows(candidate_ids, ranked)
    inputs = _build_plan_inputs(
        playbook=playbook,
        locale=locale,
        survival_goal_cny=survival_goal_cny,
        message=message,
    )
    _inject_expert_memory(inputs, role_rows)

    plan = _assemble_plan(
        cfg=cfg,
        intent=intent,
        lane=lane,
        mood=mood,
        progress_pct=progress_pct,
        playbook=playbook,
        workflow_id=workflow_id,
        inputs=inputs,
        role_rows=role_rows,
    )
    assert_greedy_action("write_greedy_snapshot")
    if redis_client:
        redis_client.set(_SNAPSHOT_KEY, json.dumps(plan, ensure_ascii=False), ex=86400 * 3)
    return plan


async def run_greedy_orchestration_async(
    db: Session,
    *,
    workflow_id: str | None = None,
    playbook_id: str | None = None,
    intent: str | None = None,
    inputs: dict[str, Any] | None = None,
    tenant_id: str | None = None,
    max_steps: int | None = None,
) -> dict[str, Any]:
    """财迷疯驱动 agency YAML DAG 执行（超管；产出须人审）。"""
    assert_greedy_action("orchestrate_agency")
    plan = plan_greedy_orchestration(
        intent=intent,
        message=str((inputs or {}).get("product_context") or ""),
        locale=str((inputs or {}).get("locale") or "global"),
        survival_goal_cny=int((inputs or {}).get("survival_goal_cny") or 1000),
        db=db,
    )
    if playbook_id:
        cfg = load_greedy_agency_config()
        for pb in cfg.get("playbooks") or []:
            if pb.get("id") == playbook_id:
                plan["playbook_id"] = playbook_id
                plan["workflow_id"] = pb.get("workflow_id")
                break

    wid = workflow_id or plan.get("workflow_id")
    if not wid:
        raise ValueError("greedy_workflow_not_resolved")

    merged_inputs = dict(plan.get("inputs") or {})
    merged_inputs.update(inputs or {})
    result = await run_workflow_async(
        db,
        workflow_id=wid,
        inputs=merged_inputs,
        tenant_id=tenant_id,
        max_steps=max_steps,
    )
    out = {
        **result,
        "greedy_plan": plan,
        "orchestrator": load_greedy_agency_config().get("orchestrator_agent"),
        "human_review_required": True,
        "persona_split": "财迷疯编排 agency 专家；SaaS Hermes 租户主流程不变",
        "source_repo": load_greedy_agency_config().get("source_repo"),
    }
    return out


def run_greedy_orchestration(
    db: Session,
    **kwargs: Any,
) -> dict[str, Any]:
    """run_greedy_orchestration。

    参数说明：
    :param db: 参数 db
    :param **kwargs: 参数 **kwargs
    :return: 返回处理结果。
    """
    import asyncio
    return asyncio.run(run_greedy_orchestration_async(db, **kwargs))


def greedy_agency_catalog_summary(*, category: str | None = None, limit: int = 50) -> dict[str, Any]:
    """轻量目录：财迷疯选人用。"""
    roles = list_roles(category=category)[: max(1, min(limit, 200))]
    cfg = load_greedy_agency_config()
    return {
        "source_repo": cfg.get("source_repo"),
        "role_count": len(list_roles()),
        "roles_preview": roles,
        "workflows_count": len(list_workflows()),
        "full_catalog_api": "/api/v1/hermes/agency/catalog",
    }


def _load_plan_snapshot() -> dict[str, Any] | None:
    """_load_plan_snapshot。
    :return: 返回处理结果。
    """
    if not redis_client:
        return None
    raw = redis_client.get(_SNAPSHOT_KEY)
    if not raw:
        return None
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None


def enrich_greedy_with_agency_catalog() -> dict[str, Any]:
    """供 A2A / survival 侧车挂载 agency 规模元数据。"""
    return {
        "agency_roles_embedded": roles_meta().get("role_count"),
        "agency_workflows": len(list_workflows()),
        "source": load_greedy_agency_config().get("source_repo"),
        "orchestrator": "hermes_greedy_core",
    }
