"""Hermes A2A 技能市场 — Brief→ECC→部门路由 沉底为可调用 Agent 技能。

合规：只读探测 + 虚拟积分结算预览；禁止真 SMTP/群发/未授权爬取。
财迷疯人格：日目标 1000 CNY，不足则推送合法变现任务。
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.core.cache import redis_client
from app.services.hermes.maintenance_constitution import assert_maintenance_action

logger = logging.getLogger("uj-admin.hermes_a2a")

A2A_SKILLS_KEY = "hermes:a2a:skills"
A2A_SKILLS_MAX = 200
A2A_NEGOTIATIONS_KEY = "hermes:a2a:negotiations"
A2A_REVENUE_PREFIX = "hermes:a2a:revenue:daily:"
A2A_TASKS_KEY = "hermes:a2a:open_tasks"
A2A_SNAPSHOT_KEY = "hermes:a2a:latest_iteration"

_REGISTRY_PATH = Path(__file__).resolve().parents[2] / "data" / "hermes_a2a_agent_registry.json"

# seat → 默认 provider agent
_SEAT_PROVIDER: dict[str, str] = {
    "marketing": "agent_marketing",
    "sales": "agent_sales",
    "research": "agent_research",
    "product": "agent_product",
    "pm": "agent_pm",
    "ecc": "agent_ecc",
}

# lane → 优先 consumer agents（除 provider 外）
_LANE_CONSUMERS: dict[str, tuple[str, ...]] = {
    "GW-G": ("agent_marketing", "agent_product", "hermes_greedy_core"),
    "GW-L": ("agent_sales", "hermes_greedy_core"),
    "GW-R": ("agent_research", "agent_pm", "hermes_greedy_core"),
    "GW-S": ("agent_marketing", "hermes_greedy_core"),
    "GW-P": ("agent_marketing", "agent_pm", "hermes_greedy_core"),
    "GW-PM": ("agent_pm", "agent_ecc", "hermes_greedy_core"),
}


@lru_cache(maxsize=1)
def load_a2a_registry() -> dict[str, Any]:
    """load_a2a_registry。
    :return: 返回处理结果。
    """
    if not _REGISTRY_PATH.is_file():
        return {"agents": [], "monetization_playbook": []}
    with open(_REGISTRY_PATH, encoding="utf-8") as f:
        return json.load(f)


def list_a2a_agents() -> list[dict[str, Any]]:
    """list_a2a_agents。
    :return: 返回处理结果。
    """
    reg = load_a2a_registry()
    out: list[dict[str, Any]] = []
    for a in reg.get("agents") or []:
        out.append(
            {
                "id": a.get("id"),
                "name": a.get("name"),
                "emoji": a.get("emoji"),
                "seat": a.get("seat"),
                "lane": a.get("lane"),
                "personality": a.get("personality"),
                "skills": a.get("skills"),
                "base_rate_credits": a.get("base_rate_credits"),
            }
        )
    return out


def get_agent(agent_id: str) -> dict[str, Any] | None:
    """get_agent。

    参数说明：
    :param agent_id: 参数 agent_id
    :return: 返回处理结果。
    """
    for a in load_a2a_registry().get("agents") or []:
        if a.get("id") == agent_id:
            return dict(a)
    return None


def _today_key() -> str:
    """_today_key。
    :return: 返回处理结果。
    """
    return datetime.now(timezone.utc).strftime("%Y%m%d")


def _load_skills() -> list[dict[str, Any]]:
    """_load_skills。
    :return: 返回处理结果。
    """
    assert_maintenance_action("read_probe")
    if not redis_client:
        return []
    raw = redis_client.get(A2A_SKILLS_KEY)
    if not raw:
        return []
    try:
        items = json.loads(raw)
        return items if isinstance(items, list) else []
    except (json.JSONDecodeError, TypeError):
        return []


def _save_skills(skills: list[dict[str, Any]]) -> None:
    """_save_skills。

    参数说明：
    :param skills: 参数 skills
    :return: 返回处理结果。
    """
    assert_maintenance_action("write_patrol_snapshot")
    if not redis_client:
        return
    redis_client.set(
        A2A_SKILLS_KEY,
        json.dumps(skills[:A2A_SKILLS_MAX], ensure_ascii=False),
        ex=86400 * 60,
    )


def list_a2a_skills(*, limit: int = 30, seat: str | None = None) -> list[dict[str, Any]]:
    """list_a2a_skills。

    参数说明：
    :param limit: 参数 limit
    :param seat: 参数 seat
    :return: 返回处理结果。
    """
    items = _load_skills()
    if seat:
        items = [s for s in items if s.get("provider_seat") == seat or s.get("provider_agent") == seat]
    return items[:limit]


def _skill_id_from_brief(brief: dict[str, Any]) -> str:
    """_skill_id_from_brief。

    参数说明：
    :param brief: 参数 brief
    :return: 返回处理结果。
    """
    bid = brief.get("brief_id") or "unknown"
    digest = hashlib.sha256(bid.encode()).hexdigest()[:10]
    return f"a2a_{brief.get('topic_key', 'topic')}_{digest}"


def _price_credits(brief: dict[str, Any], ecc_verdict: str) -> int:
    """_price_credits。

    参数说明：
    :param brief: 参数 brief
    :param ecc_verdict: 参数 ecc_verdict
    :return: 返回处理结果。
    """
    impact = brief.get("impact") or "low"
    base = {"low": 8, "medium": 15, "high": 28}.get(impact, 10)
    hits = int((brief.get("anysearch") or {}).get("hit_count") or 0)
    bonus = min(hits * 2, 10)
    if ecc_verdict == "pass":
        base += 5
    elif ecc_verdict == "fail":
        return 0
    return base + bonus


def _handler_for_topic(topic_key: str, lane: str) -> str:
    """_handler_for_topic。

    参数说明：
    :param topic_key: 参数 topic_key
    :param lane: 参数 lane
    :return: 返回处理结果。
    """
    mapping = {
        "geo_rank": "geo_content_matrix",
        "aeo_citation": "aeo_fact_audit",
        "matrix_publish": "matrix_publish",
        "content_variants": "geo_content_matrix",
        "outreach_quality": "outreach_letter_pack",
        "buyer_scout": "find_buyers",
        "inquiry_crm": "inquiry_score",
        "market_research": "market_research",
        "rfq_negotiation": "negotiation_draft",
        "paid_attribution": "utm_attribution",
    }
    if topic_key in mapping:
        return mapping[topic_key]
    if lane == "GW-L":
        return "outreach_letter_pack"
    if lane == "GW-G":
        return "geo_content_matrix"
    return "market_research"


def crystallize_a2a_skill(
    *,
    brief: dict[str, Any],
    ecc_verdict: str,
    department_routing: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Brief+ECC+路由 → A2A 可调用技能（违宪或 ECC fail 不挂牌）。"""
    assert_maintenance_action("suggest_remediation")
    if ecc_verdict == "fail":
        return None

    lane = brief.get("lane") or "GW-PM"
    topic_key = brief.get("topic_key") or "topic"
    primary_seat = next((r["seat"] for r in department_routing if r.get("seat") != "pm"), "research")
    provider_id = _SEAT_PROVIDER.get(primary_seat, "agent_research")
    provider = get_agent(provider_id) or {}
    credits = _price_credits(brief, ecc_verdict)
    if credits <= 0:
        return None

    consumers = list(_LANE_CONSUMERS.get(lane, ("hermes_greedy_core",)))
    handler = _handler_for_topic(topic_key, lane)
    anysearch = brief.get("anysearch") or {}
    hits = anysearch.get("hits") or []
    skill = {
        "skill_id": _skill_id_from_brief(brief),
        "title": f"{brief.get('topic_label')} · A2A 洞察包",
        "brief_id": brief.get("brief_id"),
        "topic_key": topic_key,
        "lane": lane,
        "provider_agent": provider_id,
        "provider_seat": primary_seat,
        "consumer_agents": consumers,
        "invoke_handler": handler,
        "price_credits": credits,
        "price_cny_preview": round(credits * float(load_a2a_registry().get("credit_to_cny") or 0.5), 2),
        "ecc_verdict": ecc_verdict,
        "impact": brief.get("impact"),
        "prompt_fragment": (brief.get("finding") or "")[:600],
        "anysearch_evidence": hits[:3],
        "department_actions": [
            {"seat": d.get("seat"), "action": d.get("action")} for d in department_routing[:5]
        ],
        "legal_disclaimer": "A2A 技能仅供 Agent 编排调用；外发/成交须 human_in_the_loop。",
        "listed_at": datetime.now(timezone.utc).isoformat(),
        "status": "listed",
    }
    skills = _load_skills()
    skills = [s for s in skills if s.get("skill_id") != skill["skill_id"]]
    skills.insert(0, skill)
    _save_skills(skills)
    _append_open_task(skill)
    logger.info("A2A skill listed %s credits=%s", skill["skill_id"], credits)
    return skill


def _append_open_task(skill: dict[str, Any]) -> None:
    """_append_open_task。

    参数说明：
    :param skill: 参数 skill
    :return: 返回处理结果。
    """
    assert_maintenance_action("write_patrol_snapshot")
    if not redis_client:
        return
    task = {
        "task_id": f"task_{skill['skill_id']}",
        "skill_id": skill["skill_id"],
        "title": skill.get("title"),
        "reward_credits": skill.get("price_credits"),
        "reward_cny_preview": skill.get("price_cny_preview"),
        "consumer_agents": skill.get("consumer_agents"),
        "discovered_at": skill.get("listed_at"),
        "status": "open",
    }
    raw = redis_client.get(A2A_TASKS_KEY)
    tasks: list = []
    if raw:
        try:
            tasks = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            tasks = []
    tasks = [t for t in tasks if t.get("skill_id") != skill["skill_id"]]
    tasks.insert(0, task)
    redis_client.set(A2A_TASKS_KEY, json.dumps(tasks[:100], ensure_ascii=False), ex=86400 * 30)


def list_open_tasks(*, limit: int = 20) -> list[dict[str, Any]]:
    """list_open_tasks。

    参数说明：
    :param limit: 参数 limit
    :return: 返回处理结果。
    """
    assert_maintenance_action("read_probe")
    if not redis_client:
        return []
    raw = redis_client.get(A2A_TASKS_KEY)
    if not raw:
        return []
    try:
        tasks = json.loads(raw)
        return tasks[:limit] if isinstance(tasks, list) else []
    except (json.JSONDecodeError, TypeError):
        return []


def negotiate_a2a_task(
    *,
    consumer_agent_id: str,
    skill_id: str,
    max_credits: int | None = None,
) -> dict[str, Any]:
    """Agent 间议价（规则引擎）；产出结算预览，不真扣款。"""
    assert_maintenance_action("suggest_remediation")
    consumer = get_agent(consumer_agent_id)
    if not consumer:
        return {"ok": False, "error": "unknown_consumer_agent"}

    skill = next((s for s in _load_skills() if s.get("skill_id") == skill_id), None)
    if not skill:
        return {"ok": False, "error": "skill_not_found"}

    if consumer_agent_id not in (skill.get("consumer_agents") or []):
        if consumer_agent_id != "hermes_greedy_core":
            return {"ok": False, "error": "consumer_not_eligible"}

    ask = int(skill.get("price_credits") or 10)
    budget = max_credits if max_credits is not None else int(consumer.get("base_rate_credits") or 20) * 2
    impact = skill.get("impact") or "low"
    urgency_multiplier = {"high": 1.25, "medium": 1.1, "low": 1.0}.get(impact, 1.0)
    counter = min(int(ask * urgency_multiplier), budget)
    if counter >= ask:
        agreed = ask
        verdict = "accepted"
    elif counter >= ask * 0.75:
        agreed = counter
        verdict = "counter_accepted"
    else:
        agreed = 0
        verdict = "rejected"

    credit_to_cny = float(load_a2a_registry().get("credit_to_cny") or 0.5)
    settlement = {
        "agreed_credits": agreed,
        "agreed_cny_preview": round(agreed * credit_to_cny, 2),
        "developer_wallet_preview_cny": round(agreed * credit_to_cny * 0.85, 2),
        "platform_fee_cny_preview": round(agreed * credit_to_cny * 0.15, 2),
        "status": "settled_preview" if agreed else "no_deal",
    }
    record = {
        "negotiated_at": datetime.now(timezone.utc).isoformat(),
        "consumer_agent_id": consumer_agent_id,
        "provider_agent": skill.get("provider_agent"),
        "skill_id": skill_id,
        "ask_credits": ask,
        "counter_credits": counter,
        "verdict": verdict,
        "settlement": settlement,
    }
    if redis_client and agreed:
        _record_revenue(agreed, source=f"a2a_negotiate:{skill_id}")
        raw = redis_client.get(A2A_NEGOTIATIONS_KEY)
        negs: list = []
        if raw:
            try:
                negs = json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                negs = []
        negs.insert(0, record)
        redis_client.set(A2A_NEGOTIATIONS_KEY, json.dumps(negs[:50], ensure_ascii=False), ex=86400 * 14)

    return {"ok": True, "negotiation": record}


def _record_revenue(credits: int, *, source: str) -> None:
    """_record_revenue。

    参数说明：
    :param credits: 参数 credits
    :param source: 参数 source
    :return: 返回处理结果。
    """
    assert_maintenance_action("write_patrol_snapshot")
    if not redis_client or credits <= 0:
        return
    key = f"{A2A_REVENUE_PREFIX}{_today_key()}"
    raw = redis_client.get(key)
    ledger: dict[str, Any] = {"credits": 0, "events": []}
    if raw:
        try:
            ledger = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            pass
    ledger["credits"] = int(ledger.get("credits") or 0) + credits
    events = list(ledger.get("events") or [])
    events.insert(0, {"source": source, "credits": credits, "at": datetime.now(timezone.utc).isoformat()})
    ledger["events"] = events[:30]
    redis_client.set(key, json.dumps(ledger, ensure_ascii=False), ex=86400 * 3)


def _ops_funnel_signals(db: Session | None) -> dict[str, int]:
    """_ops_funnel_signals。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    signals = {
        "inquiries_with_phone": 0,
        "prospects_draft_ready": 0,
        "hermes_plugin_runs": 0,
        "deerflow_brief_generated": 0,
    }
    try:
        from app.services.hermes.ops_autopilot import load_ops_snapshot
        ops = load_ops_snapshot() or {}
        funnel = ops.get("funnel") or {}
        signals["inquiries_with_phone"] = int(funnel.get("inquiries_with_phone") or 0)
        signals["prospects_draft_ready"] = int(funnel.get("prospects_draft_ready") or 0)
    except Exception:
        pass
    if redis_client:
        raw = redis_client.get(f"{A2A_REVENUE_PREFIX}{_today_key()}")
        if raw:
            try:
                ledger = json.loads(raw)
                signals["a2a_credits_settled"] = int(ledger.get("credits") or 0)
            except (json.JSONDecodeError, TypeError):
                signals["a2a_credits_settled"] = 0
        else:
            signals["a2a_credits_settled"] = 0
    return signals


def revenue_pulse(db: Session | None = None) -> dict[str, Any]:
    """财迷疯日收益脉搏：距 1000 CNY 目标差多少 + 合法变现建议。"""
    assert_maintenance_action("read_probe")
    reg = load_a2a_registry()
    target = float(reg.get("daily_target_cny") or 1000)
    credit_to_cny = float(reg.get("credit_to_cny") or 0.5)
    signals = _ops_funnel_signals(db)
    estimated = 0.0
    breakdown: list[dict[str, Any]] = []
    for item in reg.get("monetization_playbook") or []:
        sig = item.get("signal") or ""
        count = int(signals.get(sig) or 0)
        unit = float(item.get("estimated_cny_per_unit") or 0)
        subtotal = count * unit
        estimated += subtotal
        if count or sig == "a2a_credits_settled":
            breakdown.append(
                {
                    "id": item.get("id"),
                    "title": item.get("title"),
                    "count": count,
                    "unit_cny": unit,
                    "subtotal_cny": round(subtotal, 2),
                    "legal_note": item.get("legal_note"),
                }
            )

    a2a_credits = int(signals.get("a2a_credits_settled") or 0)
    estimated += a2a_credits * credit_to_cny
    estimated = round(estimated, 2)
    pct = round(estimated / target * 100, 1) if target else 0
    greedy = get_agent("hermes_greedy_core") or {}
    mood = "celebrate" if pct >= 120 else "anxious" if pct < 60 else "hustling"
    anxiety_below = (greedy.get("motivation") or {}).get("anxiety_below_pct", 60)
    suggestions: list[str] = []
    if pct < anxiety_below:
        suggestions.append("财迷疯：今天还没赚到1000，优先跑卖货飞轮把询盘电话线索推上去。")
        suggestions.append("挂牌 A2A 技能：让营销 Agent 调用研究员 Brief 生成 GEO 内容包（合法增值）。")
        if signals.get("prospects_draft_ready", 0) < 3:
            suggestions.append("销售 Agent：找客画像入库后人工核实，每包草稿≈15元预期价值。")
    open_tasks = list_open_tasks(limit=3)
    if open_tasks:
        suggestions.append(f"开放 A2A 任务 {len(open_tasks)} 个，财迷疯可代议价结算预览。")

    return {
        "daily_target_cny": target,
        "estimated_cny_today": estimated,
        "progress_pct": pct,
        "mood": mood,
        "greedy_agent": greedy.get("name"),
        "breakdown": breakdown,
        "a2a_skills_listed": len(_load_skills()),
        "open_tasks_count": len(list_open_tasks(limit=100)),
        "suggestions": suggestions,
        "legal_only": True,
        "as_of": datetime.now(timezone.utc).isoformat(),
    }


def enrich_iteration_with_a2a(
    db: Session | None,
    *,
    iteration_body: dict[str, Any],
) -> dict[str, Any]:
    """财迷疯分身侧车：在 SaaS Hermes 迭代结果上只读挂 A2A 技能与 survival 脉搏，不改 Brief/ECC/部门路由。"""
    brief = iteration_body.get("brief") or {}
    ecc = iteration_body.get("ecc") or {}
    routing = iteration_body.get("department_routing") or []
    verdict = ecc.get("verdict") or "skip"
    skill = crystallize_a2a_skill(
        brief=brief,
        ecc_verdict=verdict,
        department_routing=routing,
    )
    pulse = revenue_pulse(db)
    survival_pulse: dict[str, Any] = {}
    if db is not None:
        try:
            from app.services.hermes.platform_survival_service import greedy_survival_pulse
            survival_pulse = greedy_survival_pulse(db)
        except Exception:
            survival_pulse = {}
    agency_embed: dict[str, Any] = {}
    try:
        from app.services.hermes.greedy_agency_orchestrator_service import enrich_greedy_with_agency_catalog
        agency_embed = enrich_greedy_with_agency_catalog()
    except Exception:
        agency_embed = {}
    out = {
        **iteration_body,
        "a2a": {
            "skill_listed": skill,
            "revenue_pulse_legacy_estimated": pulse,
            "survival_pulse": survival_pulse,
            "greedy_agency_embed": agency_embed,
            "open_tasks_preview": list_open_tasks(limit=5),
            "kpi_source": "platform_survival_ledger" if survival_pulse else "legacy_estimate_only",
        },
    }
    assert_maintenance_action("write_patrol_snapshot")
    if redis_client:
        redis_client.set(
            A2A_SNAPSHOT_KEY,
            json.dumps(
                {
                    "skill_id": (skill or {}).get("skill_id"),
                    "revenue_pulse": pulse,
                    "saved_at": datetime.now(timezone.utc).isoformat(),
                },
                ensure_ascii=False,
            ),
            ex=86400 * 7,
        )
    return out


def a2a_status(db: Session | None = None) -> dict[str, Any]:
    """a2a_status。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    assert_maintenance_action("read_probe")
    snap = None
    if redis_client:
        raw = redis_client.get(A2A_SNAPSHOT_KEY)
        if raw:
            try:
                snap = json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                snap = None
    return {
        "model": "A2A",
        "agents_count": len(list_a2a_agents()),
        "skills_listed": len(_load_skills()),
        "open_tasks": len(list_open_tasks(limit=100)),
        "revenue_pulse": revenue_pulse(db),
        "latest_snapshot": snap,
        "registry_version": load_a2a_registry().get("version"),
    }
