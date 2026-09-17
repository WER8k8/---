# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""摸金校尉 · 挣钱大赛 + 专家记忆 — 持续盈利者不下线，越赛越有 experience。"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.core.cache import redis_client
from app.services.hermes.greedy_avatar_constitution import assert_greedy_action

logger = logging.getLogger("uj-admin.greedy_contest_memory")

_CONFIG_PATH = Path(__file__).resolve().parents[2] / "data" / "hermes_greedy_money_contest.json"
_MEM_PREFIX = "hermes:greedy:mem:role:"
_MOJIN_KEY = "hermes:greedy:mem:mojin"
_SCORE_PREFIX = "hermes:greedy:contest:score:"
_LEADERBOARD_KEY = "hermes:greedy:contest:leaderboard"
_LAST_PARTICIPANTS_KEY = "hermes:greedy:contest:last_participants"
_ROUNDS_KEY = "hermes:greedy:contest:rounds"
_ARENA_STATE_KEY = "hermes:greedy:contest:arena_state"
_ARENA_HISTORY_KEY = "hermes:greedy:contest:arena_history"

# 单测 / 无 Redis 时的进程内 fallback
_fallback: dict[str, Any] = {}


def _format_contest_season(raw: Any) -> str | None:
    """contest_season 配置可能是 { id, label } 对象，API 统一返回可读字符串。"""
    if raw is None:
        return None
    if isinstance(raw, str):
        s = raw.strip()
        return s or None
    if isinstance(raw, dict):
        for key in ("label", "id", "name", "title"):
            val = raw.get(key)
            if isinstance(val, str) and val.strip():
                return val.strip()
    return None


@lru_cache(maxsize=1)
def load_contest_config() -> dict[str, Any]:
    """load_contest_config。
    :return: 返回处理结果。
    """
    if not _CONFIG_PATH.is_file():
        return {}
    with open(_CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def _ttl_seconds() -> int:
    """_ttl_seconds。
    :return: 返回处理结果。
    """
    days = int((load_contest_config().get("memory") or {}).get("redis_ttl_days") or 365)
    return max(days, 30) * 86400


def _store_get(key: str) -> dict[str, Any] | None:
    """_store_get。

    参数说明：
    :param key: 参数 key
    :return: 返回处理结果。
    """
    if redis_client:
        try:
            raw = redis_client.get(key)
            if raw:
                return json.loads(raw)
        except Exception as exc:
            logger.debug("contest memory get failed %s: %s", key, exc)
            return None
    val = _fallback.get(key)
    return dict(val) if isinstance(val, dict) else None


def _store_set(key: str, payload: dict[str, Any]) -> None:
    """_store_set。

    参数说明：
    :param key: 参数 key
    :param payload: 参数 payload
    :return: 返回处理结果。
    """
    if redis_client:
        try:
            redis_client.set(key, json.dumps(payload, ensure_ascii=False), ex=_ttl_seconds())
            return
        except Exception as exc:
            logger.debug("contest memory set failed %s: %s", key, exc)
    _fallback[key] = dict(payload)


def _default_role_memory(role_id: str) -> dict[str, Any]:
    """_default_role_memory。

    参数说明：
    :param role_id: 参数 role_id
    :return: 返回处理结果。
    """
    arena = get_arena_state()
    return {
        "role_id": role_id,
        "experience_points": 0,
        "total_score": 0,
        "score_30d": 0,
        "score_arena": 0,
        "score_year": 0,
        "deployments": 0,
        "publish_credits": 0,
        "revenue_attributed_cny_minor": 0,
        "win_streak_weeks": 0,
        "contest_tier": "rookie",
        "protected": False,
        "lessons": [],
        "arenas_won": [],
        "last_active_at": None,
        "current_arena_id": None,
        "year_cycle": None,
        "season_id": (load_contest_config().get("contest_season") or {}).get("id"),
    }


def _default_mojin_memory() -> dict[str, Any]:
    """_default_mojin_memory。
    :return: 返回处理结果。
    """
    return {
        "agent_id": "hermes_greedy_core",
        "codename": "摸金校尉",
        "experience_points": 0,
        "loops_completed": 0,
        "total_settlements_minor": 0,
        "lessons": [],
        "season_id": (load_contest_config().get("contest_season") or {}).get("id"),
    }


def _score_key(role_id: str) -> str:
    """_score_key。

    参数说明：
    :param role_id: 参数 role_id
    :return: 返回处理结果。
    """
    return f"{_SCORE_PREFIX}{role_id}"


def _mem_key(role_id: str) -> str:
    """_mem_key。

    参数说明：
    :param role_id: 参数 role_id
    :return: 返回处理结果。
    """
    return f"{_MEM_PREFIX}{role_id}"


def _endurance_cfg() -> dict[str, Any]:
    """_endurance_cfg。
    :return: 返回处理结果。
    """
    return load_contest_config().get("endurance_cycle") or {}


def _parse_dt(iso: str | None) -> datetime | None:
    """_parse_dt。

    参数说明：
    :param iso: 参数 iso
    :return: 返回处理结果。
    """
    if not iso:
        return None
    try:
        return datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except ValueError:
        return None


def _bootstrap_arena_state() -> dict[str, Any]:
    """_bootstrap_arena_state。
    :return: 返回处理结果。
    """
    now = datetime.now(timezone.utc)
    ec = _endurance_cfg()
    days = int(ec.get("days_per_arena") or 30)
    year = int(now.year)
    state = _store_get(_ARENA_STATE_KEY) or {}
    year_cycle = int(state.get("year_cycle") or year)
    arena_index = int(state.get("arena_index") or 1)
    if state.get("arena_id"):
        arena_index = int(state.get("arena_index") or 1)
    else:
        arena_index = 1
    ends = now + timedelta(days=days)
    arena_id = f"{year_cycle}-arena-{arena_index:02d}"
    return {
        "mode": ec.get("mode") or "7x24x30x12",
        "year_cycle": year_cycle,
        "arena_index": arena_index,
        "arena_id": arena_id,
        "label": f"{year_cycle} 年度第 {arena_index}/{int(ec.get('arenas_per_year') or 12)} 轮擂台",
        "started_at": now.isoformat(),
        "ends_at": ends.isoformat(),
        "days_per_arena": days,
        "arenas_per_year": int(ec.get("arenas_per_year") or 12),
        "status": "active",
        "always_on": bool(ec.get("always_on", True)),
    }


def get_arena_state() -> dict[str, Any]:
    """get_arena_state。
    :return: 返回处理结果。
    """
    assert_greedy_action("read_greedy_memory")
    state = _store_get(_ARENA_STATE_KEY)
    if not state:
        state = _bootstrap_arena_state()
        _store_set(_ARENA_STATE_KEY, state)
    return state


def _sync_role_to_arena(mem: dict[str, Any], state: dict[str, Any]) -> None:
    """_sync_role_to_arena。

    参数说明：
    :param mem: 参数 mem
    :param state: 参数 state
    :return: 返回处理结果。
    """
    aid = state.get("arena_id")
    if mem.get("current_arena_id") != aid:
        mem["score_arena"] = 0
        mem["current_arena_id"] = aid
    mem["year_cycle"] = state.get("year_cycle")


def _collect_arena_leaderboard() -> list[dict[str, Any]]:
    """_collect_arena_leaderboard。
    :return: 返回处理结果。
    """
    from app.services.hermes.agency.role_loader import load_role
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    def _add(rid: str, mem: dict[str, Any]) -> None:
        """_add。

        参数说明：
        :param rid: 参数 rid
        :param mem: 参数 mem
        :return: 返回处理结果。
        """
        if rid in seen:
            return
        seen.add(rid)
        role = load_role(rid)
        rows.append(
            {
                "role_id": rid,
                "name": (role or {}).get("name") or rid.split("/")[-1],
                "score_arena": int(mem.get("score_arena") or mem.get("score_30d") or 0),
                "score_year": int(mem.get("score_year") or 0),
                "total_score": int(mem.get("total_score") or 0),
            }
        )

    if redis_client:
        try:
            for key in redis_client.scan_iter(match=f"{_MEM_PREFIX}*", count=100) or []:
                raw = redis_client.get(key)
                if not raw:
                    continue
                mem = json.loads(raw)
                rid = mem.get("role_id") or str(key).replace(_MEM_PREFIX, "")
                _add(rid, mem)
        except Exception:
            pass

    for key, val in _fallback.items():
        if not str(key).startswith(_MEM_PREFIX) or not isinstance(val, dict):
            continue
        rid = val.get("role_id") or str(key).replace(_MEM_PREFIX, "")
        _add(rid, val)

    rows.sort(key=lambda x: (-x["score_arena"], -x["score_year"], -x["total_score"]))
    return rows


def _close_arena_and_open_next(state: dict[str, Any], *, trigger: str) -> dict[str, Any]:
    """_close_arena_and_open_next。

    参数说明：
    :param state: 参数 state
    :param trigger: 参数 trigger
    :return: 返回处理结果。
    """
    assert_greedy_action("run_money_contest")
    cfg = load_contest_config()
    ec = _endurance_cfg()
    scoring = cfg.get("scoring") or {}
    prot = cfg.get("protection") or {}
    top_n = int(ec.get("arena_winners_top_n") or 3)
    arenas_per_year = int(ec.get("arenas_per_year") or 12)
    board = _collect_arena_leaderboard()
    winners = board[:top_n]
    closed_id = state.get("arena_id")
    closed_at = datetime.now(timezone.utc).isoformat()
    winners, closed_id, year_rollover, next_year, next_index = _apply_arena_winners(
        state, winners, closed_id, closed_at, scoring, prot, cfg, top_n, arenas_per_year, trigger,
    )
    new_state = _finalize_arena_state(
        state, closed_id, closed_at, winners, year_rollover, next_year, next_index, ec, trigger,
    )
    return {
        "rollover": True,
        "closed_arena_id": closed_id,
        "new_arena_id": new_state["arena_id"],
        "winners": winners,
        "year_rollover": year_rollover,
        "new_year_cycle": next_year,
        "new_arena_index": next_index,
    }


def tick_endurance_arena(*, trigger: str = "7x24") -> dict[str, Any]:
    """7×24 耐力 tick：满 30 天自动开启下一轮擂台。"""
    state = get_arena_state()
    now = datetime.now(timezone.utc)
    ends = _parse_dt(state.get("ends_at"))
    checked = now.isoformat()
    if ends and now >= ends:
        rolled = _close_arena_and_open_next(state, trigger=trigger)
        rolled["checked_at"] = checked
        return rolled
    remaining = (ends - now).total_seconds() if ends else None
    return {
        "rollover": False,
        "checked_at": checked,
        "trigger": trigger,
        "arena": state,
        "seconds_until_rollover": int(remaining) if remaining is not None else None,
        "days_until_rollover": round(remaining / 86400, 2) if remaining is not None else None,
    }


def get_endurance_status() -> dict[str, Any]:
    """get_endurance_status。
    :return: 返回处理结果。
    """
    state = get_arena_state()
    ec = _endurance_cfg()
    tick = tick_endurance_arena(trigger="status_read")
    if tick.get("rollover"):
        state = get_arena_state()
    board = _collect_arena_leaderboard()
    history = (_store_get(_ARENA_HISTORY_KEY) or {}).get("arenas") or []
    return {
        "mode": ec.get("mode") or "7x24x30x12",
        "always_on": ec.get("always_on", True),
        "current_arena": state,
        "arena_leaderboard_top5": board[:5],
        "days_per_arena": ec.get("days_per_arena"),
        "arenas_per_year": ec.get("arenas_per_year"),
        "seconds_until_rollover": tick.get("seconds_until_rollover"),
        "days_until_rollover": tick.get("days_until_rollover"),
        "recent_arena_history": history[:3],
        "total_arenas_completed": len(history),
    }


def _compute_tier(mem: dict[str, Any], cfg: dict[str, Any]) -> tuple[str, bool]:
    """_compute_tier。

    参数说明：
    :param mem: 参数 mem
    :param cfg: 参数 cfg
    :return: 返回处理结果。
    """
    prot = cfg.get("protection") or {}
    score_arena = int(mem.get("score_arena") or mem.get("score_30d") or 0)
    rev = int(mem.get("revenue_attributed_cny_minor") or 0)
    deps = int(mem.get("deployments") or 0)
    streak = int(mem.get("win_streak_weeks") or 0)
    arenas_won = list(mem.get("arenas_won") or [])
    if arenas_won and prot.get("arena_winner_protected_next_arena", True):
        return "champion", True

    champ_min = int(prot.get("champion_min_score_arena") or prot.get("champion_min_score_30d") or 400)
    vet_min = int(prot.get("veteran_min_score_arena") or prot.get("veteran_min_score_30d") or 150)
    if (
        score_arena >= champ_min
        or rev >= int(prot.get("champion_min_revenue_cny_minor") or 50000)
        or streak >= int(prot.get("streak_weeks_for_champion") or 4)
    ):
        return "champion", True
    if score_arena >= vet_min or deps >= int(prot.get("veteran_min_deployments") or 8):
        return "veteran", True
    return "rookie", False


def get_role_memory(role_id: str) -> dict[str, Any]:
    """get_role_memory。

    参数说明：
    :param role_id: 参数 role_id
    :return: 返回处理结果。
    """
    assert_greedy_action("read_greedy_memory")
    rid = (role_id or "").strip().strip("/")
    mem = _store_get(_mem_key(rid)) or _default_role_memory(rid)
    tier, protected = _compute_tier(mem, load_contest_config())
    mem["contest_tier"] = tier
    mem["protected"] = protected
    mem["never_offline"] = protected
    return mem


def get_mojin_memory() -> dict[str, Any]:
    """get_mojin_memory。
    :return: 返回处理结果。
    """
    assert_greedy_action("read_greedy_memory")
    return _store_get(_MOJIN_KEY) or _default_mojin_memory()


def is_role_contest_protected(role_id: str) -> bool:
    """is_role_contest_protected。

    参数说明：
    :param role_id: 参数 role_id
    :return: 返回处理结果。
    """
    try:
        return bool(get_role_memory(role_id).get("protected"))
    except Exception:
        return False


def _append_lesson(mem: dict[str, Any], lesson: str, *, max_lessons: int) -> None:
    """_append_lesson。

    参数说明：
    :param mem: 参数 mem
    :param lesson: 参数 lesson
    :param max_lessons: 参数 max_lessons
    :return: 返回处理结果。
    """
    text = (lesson or "").strip()[: int((load_contest_config().get("memory") or {}).get("lesson_max_chars") or 480)]
    if not text:
        return
    lessons = list(mem.get("lessons") or [])
    if text in lessons:
        return
    lessons.insert(0, text)
    mem["lessons"] = lessons[:max_lessons]


def _bump_score(mem: dict[str, Any], points: int, reason: str, *, skip_arena_sync: bool = False) -> None:
    """_bump_score。

    参数说明：
    :param mem: 参数 mem
    :param points: 参数 points
    :param reason: 参数 reason
    :param skip_arena_sync: 参数 skip_arena_sync
    :return: 返回处理结果。
    """
    if not skip_arena_sync:
        tick_endurance_arena(trigger="score_bump")
        _sync_role_to_arena(mem, get_arena_state())
    pts = max(int(points), 0)
    mem["experience_points"] = int(mem.get("experience_points") or 0) + pts
    mem["total_score"] = int(mem.get("total_score") or 0) + pts
    mem["score_30d"] = int(mem.get("score_30d") or 0) + pts
    mem["score_arena"] = int(mem.get("score_arena") or 0) + pts
    mem["score_year"] = int(mem.get("score_year") or 0) + pts
    mem["last_score_reason"] = reason
    mem["last_active_at"] = datetime.now(timezone.utc).isoformat()


def record_role_deployment(
    role_id: str,
    *,
    loop_id: str | None = None,
    intent: str | None = None,
    lesson: str | None = None,
    points: int | None = None,
) -> dict[str, Any]:
    """record_role_deployment。

    参数说明：
    :param role_id: 参数 role_id
    :param loop_id: 参数 loop_id
    :param intent: 参数 intent
    :param lesson: 参数 lesson
    :param points: 参数 points
    :return: 返回处理结果。
    """
    assert_greedy_action("write_greedy_memory")
    tick_endurance_arena(trigger="deploy")
    cfg = load_contest_config()
    scoring = cfg.get("scoring") or {}
    rid = role_id.strip().strip("/")
    mem = _store_get(_mem_key(rid)) or _default_role_memory(rid)
    _sync_role_to_arena(mem, get_arena_state())
    mem["deployments"] = int(mem.get("deployments") or 0) + 1
    _bump_score(mem, points if points is not None else int(scoring.get("deploy_points") or 10), "deploy")
    if lesson:
        _append_lesson(mem, lesson, max_lessons=int((cfg.get("memory") or {}).get("max_lessons_per_role") or 24))
    if loop_id:
        mem["last_loop_id"] = loop_id
    if intent:
        mem["last_intent"] = intent
    tier, protected = _compute_tier(mem, cfg)
    mem["contest_tier"] = tier
    mem["protected"] = protected
    _store_set(_mem_key(rid), mem)
    return mem


def record_publish_credits(role_ids: list[str], *, skus: list[str] | None = None) -> None:
    """record_publish_credits。

    参数说明：
    :param role_ids: 参数 role_ids
    :param skus: 参数 skus
    :return: 返回处理结果。
    """
    assert_greedy_action("write_greedy_memory")
    cfg = load_contest_config()
    pts = int((cfg.get("scoring") or {}).get("publish_sku_points") or 25) * max(len(skus or []), 1)
    per_role = max(pts // max(len(role_ids), 1), 1)
    for rid in role_ids:
        mem = _store_get(_mem_key(rid)) or _default_role_memory(rid)
        mem["publish_credits"] = int(mem.get("publish_credits") or 0) + len(skus or [])
        _bump_score(mem, per_role, "publish_sku")
        tier, protected = _compute_tier(mem, cfg)
        mem["contest_tier"] = tier
        mem["protected"] = protected
        _store_set(_mem_key(rid), mem)


def _save_last_participants(role_ids: list[str], loop_id: str) -> None:
    """_save_last_participants。

    参数说明：
    :param role_ids: 参数 role_ids
    :param loop_id: 参数 loop_id
    :return: 返回处理结果。
    """
    payload = {
        "loop_id": loop_id,
        "role_ids": role_ids,
        "saved_at": datetime.now(timezone.utc).isoformat(),
    }
    if redis_client:
        try:
            redis_client.set(
                _LAST_PARTICIPANTS_KEY,
                json.dumps(payload, ensure_ascii=False),
                ex=_ttl_seconds(),
            )
        except Exception:
            pass
    _fallback[_LAST_PARTICIPANTS_KEY] = payload


def _load_last_participants() -> dict[str, Any]:
    """_load_last_participants。
    :return: 返回处理结果。
    """
    if redis_client:
        try:
            raw = redis_client.get(_LAST_PARTICIPANTS_KEY)
            if raw:
                return json.loads(raw)
        except Exception:
            pass
    return dict(_fallback.get(_LAST_PARTICIPANTS_KEY) or {})


def attribute_settlement_to_contest(
    *,
    amount_base_minor: int,
    currency: str = "CNY",
    provider_payment_id: str | None = None,
) -> dict[str, Any]:
    """WorldFirst / survival 入账 → 全球累计 + 人格 + 专家归因。"""
    assert_greedy_action("run_money_contest")
    from app.services.hermes.greedy_cumulative_personality_service import (
        apply_role_settlement_personality,
        record_cumulative_settlement,
    )
    cum = record_cumulative_settlement(
        amount_base_minor=amount_base_minor,
        currency=currency,
        provider_payment_id=provider_payment_id,
    )
    pers = cum.get("personality") or {}
    bonus = int(cum.get("improvement_bonus_points") or 0)
    cfg = load_contest_config()
    scoring = cfg.get("scoring") or {}
    pending = _load_last_participants()
    role_ids = list(pending.get("role_ids") or [])
    if not role_ids:
        role_ids = ["project-management/project-management-project-shepherd"]

    rev_pts = int((amount_base_minor / 10000) * int(scoring.get("revenue_per_100_cny_minor") or 80))
    per_role_rev = amount_base_minor // max(len(role_ids), 1)
    per_role_pts = max(rev_pts // max(len(role_ids), 1), 1)
    per_bonus = max(bonus // max(len(role_ids), 1), 0) if bonus else 0
    attributed: list[dict[str, Any]] = []
    for rid in role_ids:
        mem = _store_get(_mem_key(rid)) or _default_role_memory(rid)
        mem["revenue_attributed_cny_minor"] = int(mem.get("revenue_attributed_cny_minor") or 0) + per_role_rev
        mem["win_streak_weeks"] = int(mem.get("win_streak_weeks") or 0) + 1
        _bump_score(mem, per_role_pts, "revenue_settlement")
        mem = apply_role_settlement_personality(mem, share_minor=per_role_rev, global_personality=pers)
        if per_bonus:
            _bump_score(mem, per_bonus, "improvement_vs_last", skip_arena_sync=True)
        _append_lesson(
            mem,
            mem.get("personality_note")
            or f"真钱入账 ¥{amount_base_minor / 100:.2f}（分摊）payment={provider_payment_id or 'n/a'}",
            max_lessons=int((cfg.get("memory") or {}).get("max_lessons_per_role") or 24),
        )
        tier, protected = _compute_tier(mem, cfg)
        mem["contest_tier"] = tier
        mem["protected"] = protected
        _store_set(_mem_key(rid), mem)
        attributed.append(
            {
                "role_id": rid,
                "tier": tier,
                "protected": protected,
                "personality_mood": mem.get("personality_mood"),
                "revenue_week_minor": mem.get("revenue_week_minor"),
            }
        )

    return {
        "ok": True,
        "amount_base_minor": amount_base_minor,
        "currency": currency.upper(),
        "attributed_roles": attributed,
        "loop_id": pending.get("loop_id"),
        "cumulative": cum.get("cumulative"),
        "personality": pers,
    }


def settle_revenue_loop_contest(report: dict[str, Any]) -> dict[str, Any]:
    """一轮 L1–L6 结束后记分、写记忆、锁定待归因参与者。"""
    assert_greedy_action("run_money_contest")
    cfg = load_contest_config()
    scoring = cfg.get("scoring") or {}
    loop_id = report.get("generated_at") or str(uuid.uuid4())
    role_ids: list[str] = []
    lesson = ""
    skus: list[str] = []
    round_kpi = None
    for stage in report.get("stages") or []:
        if not isinstance(stage, dict):
            continue
        sid = stage.get("stage") or ""
        if sid == "L6_collect":
            round_kpi = (stage.get("survival_pulse") or {}).get("progress_pct")
        if sid == "L2_orchestrate":
            inner = (stage.get("result") or {}).get("greedy_plan") or {}
            for ex in inner.get("experts_selected") or []:
                if isinstance(ex, dict) and ex.get("role_id"):
                    role_ids.append(str(ex["role_id"]))
            wf = (stage.get("result") or {}).get("outputs") or {}
            lesson = str(wf.get("greedy_summary") or wf.get("battle_plan") or "")[:480]
        if sid == "L3_compose":
            asset = stage.get("asset") or {}
            if not lesson:
                lesson = str(asset.get("greedy_summary") or asset.get("marketing_plan") or "")[:480]
            skus = list(asset.get("deliverable_skus") or [])
        if sid == "L4_publish":
            for item in stage.get("publish_items") or []:
                if isinstance(item, dict) and item.get("sku"):
                    skus.append(str(item["sku"]))

    role_ids = list(dict.fromkeys(role_ids))
    if not role_ids:
        role_ids = ["project-management/project-management-project-shepherd"]

    loop_pts = int(scoring.get("loop_complete_points") or 15)
    for rid in role_ids:
        record_role_deployment(rid, loop_id=loop_id, lesson=lesson, points=loop_pts)

    if skus:
        record_publish_credits(role_ids, skus=list(dict.fromkeys(skus)))

    _save_last_participants(role_ids, loop_id)
    mojin = _store_get(_MOJIN_KEY) or _default_mojin_memory()
    mojin["loops_completed"] = int(mojin.get("loops_completed") or 0) + 1
    mojin["experience_points"] = int(mojin.get("experience_points") or 0) + loop_pts * len(role_ids)
    if lesson:
        _append_lesson(mojin, f"[{loop_id[:19]}] {lesson}", max_lessons=int((cfg.get("memory") or {}).get("max_lessons_mojin") or 40))
    _store_set(_MOJIN_KEY, mojin)
    round_row = {
        "loop_id": loop_id,
        "trigger": report.get("trigger"),
        "participants": role_ids,
        "skus": list(dict.fromkeys(skus)),
        "kpi_pct": round_kpi,
        "settled_at": datetime.now(timezone.utc).isoformat(),
    }
    rounds = _store_get(_ROUNDS_KEY) or {"rounds": []}
    rs = list(rounds.get("rounds") or [])
    rs.insert(0, round_row)
    _store_set(_ROUNDS_KEY, {"rounds": rs[:50]})
    return {
        "loop_id": loop_id,
        "participants": len(role_ids),
        "skus": len(set(skus)),
        "contest_season": (cfg.get("contest_season") or {}).get("label"),
    }


def get_contest_leaderboard(*, limit: int = 30) -> dict[str, Any]:
    """get_contest_leaderboard。

    参数说明：
    :param limit: 参数 limit
    :return: 返回处理结果。
    """
    assert_greedy_action("read_greedy_memory")
    from app.services.hermes.agency.role_loader import load_role
    cfg = load_contest_config()
    rows: list[dict[str, Any]] = []
    if redis_client:
        try:
            keys = list(redis_client.scan_iter(match=f"{_MEM_PREFIX}*", count=100))
            for key in keys or []:
                raw = redis_client.get(key)
                if not raw:
                    continue
                mem = json.loads(raw)
                rid = mem.get("role_id") or key.replace(_MEM_PREFIX, "")
                tier, protected = _compute_tier(mem, cfg)
                mem["contest_tier"] = tier
                mem["protected"] = protected
                role = load_role(rid)
                rows.append(
                    {
                        "role_id": rid,
                        "name": (role or {}).get("name") or rid.split("/")[-1],
                        "emoji": (role or {}).get("emoji"),
                        "total_score": mem.get("total_score"),
                        "score_30d": mem.get("score_30d"),
                        "score_arena": mem.get("score_arena"),
                        "score_year": mem.get("score_year"),
                        "experience_points": mem.get("experience_points"),
                        "deployments": mem.get("deployments"),
                        "revenue_attributed_cny_minor": mem.get("revenue_attributed_cny_minor"),
                        "contest_tier": tier,
                        "protected": protected,
                        "never_offline": protected,
                        "lessons_count": len(mem.get("lessons") or []),
                    }
                )
        except Exception as exc:
            logger.debug("leaderboard scan failed: %s", exc)

    if not rows:
        for key, val in _fallback.items():
            if not key.startswith(_MEM_PREFIX) or not isinstance(val, dict):
                continue
            mem = val
            rid = mem.get("role_id") or key.replace(_MEM_PREFIX, "")
            tier, protected = _compute_tier(mem, cfg)
            role = load_role(rid)
            rows.append(
                {
                    "role_id": rid,
                    "name": (role or {}).get("name") or rid.split("/")[-1],
                    "total_score": mem.get("total_score"),
                    "score_30d": mem.get("score_30d"),
                    "contest_tier": tier,
                    "protected": protected,
                    "never_offline": protected,
                }
            )

    rows.sort(
        key=lambda x: (
            -int(x.get("score_arena") or x.get("score_30d") or 0),
            -int(x.get("score_year") or 0),
            -int(x.get("total_score") or 0),
            -int(x.get("revenue_attributed_cny_minor") or 0),
        )
    )
    champions = [r for r in rows if r.get("contest_tier") == "champion"]
    endurance = get_endurance_status()
    return {
        "season": _format_contest_season(cfg.get("contest_season")),
        "title": cfg.get("title"),
        "tagline": cfg.get("tagline"),
        "endurance": endurance,
        "current_arena": endurance.get("current_arena"),
        "leaderboard": rows[: max(1, min(limit, 100))],
        "protected_count": sum(1 for r in rows if r.get("protected")),
        "champion_count": len(champions),
        "mojin": get_mojin_memory(),
        "recent_rounds": (_store_get(_ROUNDS_KEY) or {}).get("rounds", [])[:5],
    }


def format_expert_memory_prompt(role_ids: list[str], *, max_roles: int = 6) -> str:
    """注入 agency 编排 — 防止专家失忆。"""
    assert_greedy_action("read_greedy_memory")
    blocks: list[str] = []
    endurance = get_endurance_status()
    arena = (endurance.get("current_arena") or {}).get("label")
    if arena:
        blocks.append(f"【耐力赛·{arena}】7×24 持续记分中")
    try:
        from app.services.hermes.greedy_cumulative_personality_service import format_personality_prompt_block
        blocks.append(format_personality_prompt_block())
    except Exception:
        pass
    mojin = get_mojin_memory()
    m_lessons = list(mojin.get("lessons") or [])[:2]
    if m_lessons:
        blocks.append("【摸金校尉记忆】" + " | ".join(m_lessons))

    for rid in role_ids[:max_roles]:
        mem = get_role_memory(rid)
        lessons = list(mem.get("lessons") or [])[:2]
        if not lessons:
            continue
        tier = mem.get("contest_tier") or "rookie"
        blocks.append(f"【{rid}·{tier}·经验{mem.get('experience_points', 0)}】" + " | ".join(lessons))

    if not blocks:
        return ""
    return "\n".join(blocks)[:3000]


def contest_status_summary() -> dict[str, Any]:
    """contest_status_summary。
    :return: 返回处理结果。
    """
    lb = get_contest_leaderboard(limit=5)
    cumulative = None
    try:
        from app.services.hermes.greedy_cumulative_personality_service import get_cumulative_stats
        cumulative = get_cumulative_stats()
    except Exception:
        pass
    return {
        "season": lb.get("season"),
        "endurance_mode": (lb.get("endurance") or {}).get("mode"),
        "current_arena": lb.get("current_arena"),
        "days_until_rollover": (lb.get("endurance") or {}).get("days_until_rollover"),
        "protected_count": lb.get("protected_count"),
        "champion_count": lb.get("champion_count"),
        "top5": lb.get("leaderboard"),
        "mojin_loops": (lb.get("mojin") or {}).get("loops_completed"),
        "cumulative": cumulative,
        "personality_mood": (cumulative or {}).get("personality", {}).get("mood"),
    }

def _apply_arena_winners(
    state: dict[str, Any],
    winners: list[dict[str, Any]],
    closed_id: str,
    closed_at: str,
    scoring: dict[str, Any],
    prot: dict[str, Any],
    cfg: dict[str, Any],
    top_n: int,
    arenas_per_year: int,
    trigger: str,
) -> tuple[list[dict[str, Any]], str, bool, int, int]:
    """_apply_arena_winners。

    参数说明：
    :return: 返回 (winners, closed_id, year_rollover, next_year, next_index)。
    """
    winner_bonus = int(scoring.get("arena_winner_bonus") or 120)
    for rank, w in enumerate(winners, start=1):
        rid = w["role_id"]
        mem = _store_get(_mem_key(rid)) or _default_role_memory(rid)
        wins = list(mem.get("arenas_won") or [])
        wins.insert(
            0,
            {
                "arena_id": closed_id,
                "rank": rank,
                "score_arena": w.get("score_arena"),
                "closed_at": closed_at,
            },
        )
        mem["arenas_won"] = wins[:24]
        _bump_score(mem, winner_bonus, "arena_winner", skip_arena_sync=True)
        if prot.get("arena_winner_protected_next_arena", True):
            mem["protected"] = True
            mem["never_offline"] = True
            mem["protected_reason"] = f"arena_winner_rank_{rank}"
        _append_lesson(
            mem,
            f"擂台 {closed_id} 第{rank}名 · score={w.get('score_arena')} · 下轮继续上场",
            max_lessons=int((cfg.get("memory") or {}).get("max_lessons_per_role") or 36),
        )
        _store_set(_mem_key(rid), mem)

    year_rollover = int(state.get("arena_index") or 1) >= arenas_per_year
    next_year = int(state.get("year_cycle") or datetime.now(timezone.utc).year)
    next_index = int(state.get("arena_index") or 1) + 1
    if year_rollover:
        next_index = 1
        next_year += 1
        year_bonus = int(scoring.get("year_cycle_champion_bonus") or 500)
        if winners:
            champ = winners[0]
            mem = _store_get(_mem_key(champ["role_id"])) or _default_role_memory(champ["role_id"])
            _bump_score(mem, year_bonus, "year_cycle_champion", skip_arena_sync=True)
            _append_lesson(mem, f"年度耐力赛 {state.get('year_cycle')} 总冠军", max_lessons=36)
            _store_set(_mem_key(champ["role_id"]), mem)
        mojin = _store_get(_MOJIN_KEY) or _default_mojin_memory()
        _append_lesson(mojin, f"年度 {state.get('year_cycle')} 12 轮满期 → 新年度 {next_year} 擂台开启", max_lessons=48)
        _store_set(_MOJIN_KEY, mojin)
    return winners, closed_id, year_rollover, next_year, next_index


def _finalize_arena_state(
    state: dict[str, Any],
    closed_id: str,
    closed_at: str,
    winners: list[dict[str, Any]],
    year_rollover: bool,
    next_year: int,
    next_index: int,
    ec: dict[str, Any],
    trigger: str,
) -> dict[str, Any]:
    """_finalize_arena_state。

    参数说明：
    :return: 返回新的 arena state。
    """
    for key, val in list(_fallback.items()):
        if not str(key).startswith(_MEM_PREFIX) or not isinstance(val, dict):
            continue
        val["score_arena"] = 0
        if year_rollover and ec.get("year_rollover_resets_arena_score", True):
            val["score_year"] = 0
        _fallback[key] = val

    if redis_client:
        try:
            for key in redis_client.scan_iter(match=f"{_MEM_PREFIX}*", count=100) or []:
                raw = redis_client.get(key)
                if not raw:
                    continue
                mem = json.loads(raw)
                mem["score_arena"] = 0
                if year_rollover and ec.get("year_rollover_resets_arena_score", True):
                    mem["score_year"] = 0
                redis_client.set(key, json.dumps(mem, ensure_ascii=False), ex=_ttl_seconds())
        except Exception as exc:
            logger.debug("arena score reset failed: %s", exc)

    history = _store_get(_ARENA_HISTORY_KEY) or {"arenas": []}
    hist = list(history.get("arenas") or [])
    hist.insert(
        0,
        {
            "arena_id": closed_id,
            "year_cycle": state.get("year_cycle"),
            "arena_index": state.get("arena_index"),
            "closed_at": closed_at,
            "trigger": trigger,
            "winners": winners,
            "year_rollover": year_rollover,
        },
    )
    _store_set(_ARENA_HISTORY_KEY, {"arenas": hist[:48]})
    now = datetime.now(timezone.utc)
    days = int(ec.get("days_per_arena") or 30)
    new_state = {
        "mode": ec.get("mode") or "7x24x30x12",
        "year_cycle": next_year,
        "arena_index": next_index,
        "arena_id": f"{next_year}-arena-{next_index:02d}",
        "label": f"{next_year} 年度第 {next_index}/{arenas_per_year} 轮擂台",
        "started_at": now.isoformat(),
        "ends_at": (now + timedelta(days=days)).isoformat(),
        "days_per_arena": days,
        "arenas_per_year": arenas_per_year,
        "status": "active",
        "always_on": bool(ec.get("always_on", True)),
        "previous_arena_id": closed_id,
    }
    _store_set(_ARENA_STATE_KEY, new_state)
    return new_state

