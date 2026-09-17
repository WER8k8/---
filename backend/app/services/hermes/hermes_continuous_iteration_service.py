# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Hermes 持续迭代闭环 — 宪法 + DeerFlow + 研究员 + 营销/各部门 + ECC。

L1 只读采集 → L2 ResearchBrief → L3 ECC 评审 → L4 部门路由 → L5 PM Inbox
禁止：自动改代码、自动入队 DeerFlow（租户日更除外既有调度器）、自动发信/发布。

与「财迷疯」分身：本模块为 SaaS 内 Hermes 主职责；末尾 enrich_iteration_with_a2a 仅为
财迷疯 survival 侧车（真钱脉搏/A2A 挂牌预览），不改变上述闭环行为与租户可见能力。
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.core.cache import redis_client
from app.core.config import settings
from app.services.hermes.maintenance_constitution import CONSTITUTION_VERSION, assert_maintenance_action, constitution_payload
from app.services.hermes.research_brief_service import (
    append_brief_inbox,
    load_brief_inbox,
    load_brief_snapshot,
    run_research_brief_cycle,
)

logger = logging.getLogger("uj-admin.hermes_continuous_iteration")

ITERATION_SNAPSHOT_KEY = "hermes:continuous_iteration:latest"
HOUR_SLOT_PREFIX = "hermes:continuous_iteration:hour:"

# 营销/销售/研究 B2B 专家（b2b_trade_experts.json）+ ECC 八席 + PM
DEPARTMENT_SEATS: tuple[dict[str, Any], ...] = (
    {
        "seat": "marketing",
        "label": "营销与内容",
        "lanes": frozenset({"GW-G", "GW-S", "GW-P"}),
        "expert_ids": ("expert_matrix", "expert_ads"),
        "agent_refs": ("内容创作者", "SEO 专家", "社交媒体策略师", "TikTok 策略师"),
    },
    {
        "seat": "sales",
        "label": "销售与 outbound",
        "lanes": frozenset({"GW-L"}),
        "expert_ids": ("expert_letter", "expert_negotiate", "expert_crm", "expert_diligence"),
        "agent_refs": ("Outbound 策略师", "赢单策略师", "Discovery 教练"),
    },
    {
        "seat": "research",
        "label": "外贸研究员",
        "lanes": frozenset({"GW-R"}),
        "expert_ids": ("expert_research",),
        "agent_refs": ("市场参谋", "DeerFlow market_research"),
    },
    {
        "seat": "product",
        "label": "建站与产品",
        "lanes": frozenset({"GW-G", "GW-PM"}),
        "expert_ids": ("expert_site", "expert_eva"),
        "agent_refs": ("建站助手", "找客专员"),
    },
    {
        "seat": "ecc",
        "label": "ECC 技术八席",
        "lanes": frozenset({"GW-PM"}),
        "expert_ids": (),
        "agent_refs": ("frontend-architect", "insulation-backend-developer", "geo-rank-strategist"),
    },
    {
        "seat": "pm",
        "label": "产品经理编排",
        "lanes": frozenset({"GW-PM", "GW-G", "GW-L", "GW-R", "GW-S", "GW-P"}),
        "expert_ids": (),
        "agent_refs": ("PM-07", "global-overseas-growth-task-register"),
    },
)


def _iteration_enabled() -> bool:
    """_iteration_enabled。
    :return: 返回处理结果。
    """
    flag = getattr(settings, "HERMES_CONTINUOUS_ITERATION_ENABLED", None)
    if flag is not None:
        return bool(flag)
    return (settings.ENVIRONMENT or "").strip().lower() in ("production", "development")


def _hour_slot_key(at: datetime | None = None) -> str:
    """_hour_slot_key。

    参数说明：
    :param at: 参数 at
    :return: 返回处理结果。
    """
    now = at or datetime.now(timezone.utc)
    return f"{HOUR_SLOT_PREFIX}{now.strftime('%Y%m%d%H')}"


def _already_ran_this_hour(*, force: bool) -> bool:
    """_already_ran_this_hour。

    参数说明：
    :param force: 参数 force
    :return: 返回处理结果。
    """
    if force or not redis_client:
        return False
    return bool(redis_client.get(_hour_slot_key()))


def _mark_hour_slot() -> None:
    """_mark_hour_slot。
    :return: 返回处理结果。
    """
    if redis_client:
        redis_client.set(_hour_slot_key(), "1", ex=7200)


def brief_to_ecc_candidate(brief: dict[str, Any]) -> dict[str, Any]:
    """brief_to_ecc_candidate。

    参数说明：
    :param brief: 参数 brief
    :return: 返回处理结果。
    """
    return {
        "title": f"[ResearchBrief] {brief.get('topic_label')}",
        "body_preview": brief.get("finding") or "",
        "category": brief.get("category") or "paper",
        "impact": brief.get("impact") or "low",
        "url": "",
        "source": "hermes_research_brief",
        "validation_status": "pass" if brief.get("evidence") else "skip",
    }


def route_departments(brief: dict[str, Any], *, ecc_reviews: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """按 lane/impact 路由至营销、销售、研究、ECC、PM。"""
    assert_maintenance_action("suggest_remediation")
    lane = brief.get("lane") or "GW-PM"
    impact = brief.get("impact") or "low"
    routing: list[dict[str, Any]] = []
    for seat in DEPARTMENT_SEATS:
        lanes: frozenset[str] = seat["lanes"]
        if lane not in lanes and seat["seat"] != "pm":
            continue
        if impact == "low" and seat["seat"] in ("ecc", "pm") and lane not in ("GW-PM",):
            if seat["seat"] == "ecc":
                continue

        action = "review_in_standup"
        if seat["seat"] == "marketing":
            action = "draft_content_or_campaign_hypothesis"
        elif seat["seat"] == "sales":
            action = "adjust_outreach_playbook"
        elif seat["seat"] == "research":
            action = "extend_deerflow_brief_for_tenants"
        elif seat["seat"] == "pm":
            action = "approve_or_reject_inbox"

        routing.append(
            {
                "seat": seat["seat"],
                "label": seat["label"],
                "action": action,
                "expert_ids": list(seat["expert_ids"]),
                "agent_refs": list(seat["agent_refs"])[:4],
                "note": (brief.get("finding") or "")[:240],
            }
        )

    if impact in ("high", "medium") and not any(r["seat"] == "pm" for r in routing):
        pm = next(s for s in DEPARTMENT_SEATS if s["seat"] == "pm")
        routing.append(
            {
                "seat": "pm",
                "label": pm["label"],
                "action": "approve_or_reject_inbox",
                "expert_ids": [],
                "agent_refs": list(pm["agent_refs"]),
                "note": "impact 升级强制 PM 可见",
            }
        )

    fail_experts = [r for r in ecc_reviews if r.get("verdict") == "fail"]
    if fail_experts:
        routing.append(
            {
                "seat": "ecc",
                "label": "ECC 否决跟进",
                "action": "human_triage_only",
                "expert_ids": [],
                "agent_refs": [r.get("expert_id") for r in fail_experts[:3]],
                "note": "专家 fail — 禁止自动落地",
            }
        )

    return routing


def _run_github_scout_slice(*, force: bool) -> dict[str, Any]:
    """执行 GitHub 生态侦察片，失败降级为错误摘要。"""
    try:
        from app.services.hermes.github_ecosystem_scout_service import run_github_scout_cycle
        return run_github_scout_cycle(force=force)
    except Exception as exc:
        logger.warning("GitHub ecosystem scout skipped: %s", exc)
        return {"error": str(exc)[:200]}


def _run_ecc_review_slice(db: Session, candidate: Any) -> dict[str, Any]:
    """执行 ECC 专家评审片，失败降级为 error verdict。"""
    try:
        from app.services.hermes.ecc_expert_panel import review_candidate
        return review_candidate(db, candidate, allow_llm=False)
    except Exception as exc:
        logger.warning("ECC review for research brief skipped: %s", exc)
        return {"expert_verdict": "error", "error": str(exc)[:200]}


def _run_deerflow_drain_slice(
    db: Session,
    *,
    trigger: str,
    include_deerflow_drain: bool,
) -> dict[str, Any]:
    """按需清空 DeerFlow pending 队列片。"""
    if not include_deerflow_drain:
        return {"processed": 0}
    try:
        from app.services.ubrain.deerflow_scheduled_service import run_deerflow_pending_only
        return run_deerflow_pending_only(
            db,
            trigger=f"{trigger}:deerflow_pending",
            lane="iteration",
        )
    except Exception as exc:
        logger.warning("DeerFlow iteration drain skipped: %s", exc)
        return {"error": str(exc)[:200]}


def _build_iteration_body(
    *,
    trigger: str,
    brief: dict[str, Any],
    ecc_verdict: str,
    reviews: list[Any],
    department_routing: Any,
    deerflow_slice: dict[str, Any],
    github_scout_slice: dict[str, Any],
) -> dict[str, Any]:
    """组装迭代片快照返回体。"""
    return {
        "trigger": trigger,
        "constitution": constitution_payload(),
        "brief": brief,
        "ecc": {
            "verdict": ecc_verdict,
            "review_count": len(reviews),
            "reviews": reviews[:6],
        },
        "department_routing": department_routing,
        "deerflow_pending": deerflow_slice,
        "github_scout": github_scout_slice,
        "rules": [
            "hermes_constitution_whitelist_only",
            "research_brief_json_no_auto_mutate",
            "deerflow_tenant_daily_via_scheduler_not_hourly_enqueue",
            "pm_inbox_pending_approve_before_task_register",
        ],
        "saved_at": datetime.now(timezone.utc).isoformat(),
    }


def _execute_iteration_core(
    db: Session,
    *,
    trigger: str,
    force: bool,
    include_deerflow_drain: bool,
) -> dict[str, Any]:
    """执行研究员 → ECC → 部门路由 → Inbox 主链路，返回快照 body。

    :return: 迭代快照 body；duplicate brief 时返回 skipped 标记。
    """
    github_scout_slice: dict[str, Any] = {"skipped": True, "reason": "not_run"}
    try:
        github_scout_slice = _run_github_scout_slice(force=force)
    except Exception as exc:  # 兜底防抖：与旧实现一致的降级语义
        github_scout_slice = {"error": str(exc)[:200]}

    brief_report = run_research_brief_cycle(db, trigger=f"{trigger}:research", force=force)
    if brief_report.get("skipped") and brief_report.get("reason") == "duplicate_fingerprint":
        _mark_hour_slot()
        return {
            "trigger": trigger,
            "skipped": True,
            "reason": "duplicate_brief",
            "brief_report": brief_report,
        }

    brief = brief_report.get("brief") or {}
    candidate = brief_to_ecc_candidate(brief)
    ecc_result = _run_ecc_review_slice(db, candidate)
    reviews = ecc_result.get("expert_reviews") or []
    department_routing = route_departments(brief, ecc_reviews=reviews)
    ecc_verdict = ecc_result.get("expert_verdict") or "skip"
    if brief.get("brief_id") and ecc_verdict != "fail":
        append_brief_inbox(brief, ecc_verdict=ecc_verdict, department_routing=department_routing)

    deerflow_slice = _run_deerflow_drain_slice(
        db,
        trigger=trigger,
        include_deerflow_drain=include_deerflow_drain,
    )
    return _build_iteration_body(
        trigger=trigger,
        brief=brief,
        ecc_verdict=ecc_verdict,
        reviews=reviews,
        department_routing=department_routing,
        deerflow_slice=deerflow_slice,
        github_scout_slice=github_scout_slice,
    )


def _persist_iteration_snapshot(body: dict[str, Any]) -> None:
    """写入迭代快照缓存并标记本小时槽位。"""
    assert_maintenance_action("write_patrol_snapshot")
    if redis_client:
        redis_client.set(
            ITERATION_SNAPSHOT_KEY,
            json.dumps(body, ensure_ascii=False),
            ex=86400 * 14,
        )
    _mark_hour_slot()


def run_continuous_iteration_cycle(
    db: Session,
    *,
    trigger: str = "scheduler",
    force: bool = False,
    include_deerflow_drain: bool = True,
) -> dict[str, Any]:
    """完整迭代片：研究员 → ECC → 部门 → Inbox；可选 DeerFlow pending drain。"""
    if not _iteration_enabled():
        return {"skipped": True, "reason": "continuous_iteration_disabled", "trigger": trigger}

    if _already_ran_this_hour(force=force):
        return {
            "skipped": True,
            "reason": "already_ran_this_hour",
            "trigger": trigger,
            "latest": load_brief_snapshot(),
        }

    assert_maintenance_action("read_probe")
    body = _execute_iteration_core(
        db,
        trigger=trigger,
        force=force,
        include_deerflow_drain=include_deerflow_drain,
    )
    if body.get("skipped"):
        return body

    body = enrich_iteration_with_a2a(db, iteration_body=body)
    _persist_iteration_snapshot(body)
    logger.info(
        "Continuous iteration [%s] brief=%s ecc=%s depts=%s",
        trigger,
        body.get("brief", {}).get("brief_id"),
        body.get("ecc", {}).get("verdict"),
        len(body.get("department_routing") or {}),
    )
    return body


def load_iteration_snapshot() -> dict[str, Any] | None:
    """load_iteration_snapshot。
    :return: 返回处理结果。
    """
    assert_maintenance_action("read_probe")
    if not redis_client:
        return None
    raw = redis_client.get(ITERATION_SNAPSHOT_KEY)
    if not raw:
        return None
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None


def iteration_status() -> dict[str, Any]:
    """iteration_status。
    :return: 返回处理结果。
    """
    assert_maintenance_action("read_probe")
    a2a_preview: dict[str, Any] = {}
    try:
        from app.services.hermes.a2a_skill_marketplace_service import a2a_status
        a2a_preview = a2a_status()
    except Exception:
        a2a_preview = {}
    return {
        "enabled": _iteration_enabled(),
        "constitution_version": CONSTITUTION_VERSION,
        "latest": load_iteration_snapshot(),
        "latest_brief": load_brief_snapshot(),
        "inbox_preview": load_brief_inbox(limit=5),
        "department_seats": [{"seat": s["seat"], "label": s["label"]} for s in DEPARTMENT_SEATS],
        "a2a": a2a_preview,
    }


def enrich_iteration_with_a2a(db: Session, *, iteration_body: dict[str, Any]) -> dict[str, Any]:
    """enrich_iteration_with_a2a。

    参数说明：
    :param db: 参数 db
    :param iteration_body: 参数 iteration_body
    :return: 返回处理结果。
    """
    from app.services.hermes.a2a_skill_marketplace_service import enrich_iteration_with_a2a as _enrich
    return _enrich(db, iteration_body=iteration_body)
