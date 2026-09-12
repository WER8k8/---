"""全球累计（周/月/年）+ 摸金打江山人格（羞耻感·奋发图强·比上次更强）。"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from app.core.cache import redis_client
from app.services.hermes.greedy_avatar_constitution import assert_greedy_action

logger = logging.getLogger("uj-admin.greedy_cumulative")

_CONFIG_PATH = Path(__file__).resolve().parents[2] / "data" / "hermes_greedy_money_contest.json"
_CUMULATIVE_KEY = "hermes:greedy:cumulative:global"
_MOJIN_KEY = "hermes:greedy:mem:mojin"
_fallback: dict[str, Any] = {}


@lru_cache(maxsize=1)
def _contest_cfg() -> dict[str, Any]:
    """_contest_cfg。
    :return: 返回处理结果。
    """
    if not _CONFIG_PATH.is_file():
        return {}
    with open(_CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def _tz() -> ZoneInfo:
    """_tz。
    :return: 返回处理结果。
    """
    tz_name = (_contest_cfg().get("cumulative") or {}).get("timezone") or "Asia/Shanghai"
    try:
        return ZoneInfo(tz_name)
    except Exception:
        return ZoneInfo("UTC")


def _now_local() -> datetime:
    """_now_local。
    :return: 返回处理结果。
    """
    return datetime.now(_tz())


def period_keys(now: datetime | None = None) -> dict[str, str]:
    """period_keys。

    参数说明：
    :param now: 参数 now
    :return: 返回处理结果。
    """
    dt = now or _now_local()
    iso = dt.isocalendar()
    return {
        "week_key": f"{iso.year}-W{iso.week:02d}",
        "month_key": dt.strftime("%Y-%m"),
        "year_key": str(dt.year),
    }


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
        except Exception:
            pass
    val = _fallback.get(key)
    return dict(val) if isinstance(val, dict) else None


def _store_set(key: str, payload: dict[str, Any]) -> None:
    """_store_set。

    参数说明：
    :param key: 参数 key
    :param payload: 参数 payload
    :return: 返回处理结果。
    """
    ttl = int((_contest_cfg().get("memory") or {}).get("redis_ttl_days") or 400) * 86400
    if redis_client:
        try:
            redis_client.set(key, json.dumps(payload, ensure_ascii=False), ex=ttl)
            return
        except Exception:
            pass
    _fallback[key] = dict(payload)


def _default_cumulative() -> dict[str, Any]:
    """_default_cumulative。
    :return: 返回处理结果。
    """
    keys = period_keys()
    gr = _contest_cfg().get("global_revenue") or {}
    return {
        "scope": gr.get("scope") or "unrestricted",
        **keys,
        "week_revenue_minor": 0,
        "month_revenue_minor": 0,
        "year_revenue_minor": 0,
        "lifetime_revenue_minor": 0,
        "last_settlement_minor": 0,
        "prev_settlement_minor": 0,
        "prev_week_total_minor": 0,
        "prev_month_total_minor": 0,
        "prev_year_total_minor": 0,
        "settlements_count": 0,
        "personality_mood": "conquest",
        "last_mood": "conquest",
        "redemption_streak": 0,
        "global_markets": "domestic_and_foreign_unrestricted",
    }


def _rotate_period_buckets(data: dict[str, Any]) -> dict[str, Any]:
    """_rotate_period_buckets。

    参数说明：
    :param data: 参数 data
    :return: 返回处理结果。
    """
    keys = period_keys()
    if data.get("week_key") != keys["week_key"]:
        data["prev_week_total_minor"] = int(data.get("week_revenue_minor") or 0)
        data["week_revenue_minor"] = 0
        data["week_key"] = keys["week_key"]
    if data.get("month_key") != keys["month_key"]:
        data["prev_month_total_minor"] = int(data.get("month_revenue_minor") or 0)
        data["month_revenue_minor"] = 0
        data["month_key"] = keys["month_key"]
    if data.get("year_key") != keys["year_key"]:
        data["prev_year_total_minor"] = int(data.get("year_revenue_minor") or 0)
        data["year_revenue_minor"] = 0
        data["year_key"] = keys["year_key"]
    return data


def evaluate_personality(
    *,
    last_settlement: int,
    prev_settlement: int,
    week_total: int,
    prev_week_total: int,
    last_mood: str,
) -> dict[str, Any]:
    """evaluate_personality。

    参数说明：
    :param last_settlement: 参数 last_settlement
    :param prev_settlement: 参数 prev_settlement
    :param week_total: 参数 week_total
    :param prev_week_total: 参数 prev_week_total
    :param last_mood: 参数 last_mood
    :return: 返回处理结果。
    """
    p = _contest_cfg().get("personality") or {}
    moods = p.get("moods") or {}
    delta_settlement = last_settlement - prev_settlement if prev_settlement > 0 else last_settlement
    delta_pct = round(100.0 * delta_settlement / prev_settlement, 1) if prev_settlement > 0 else None
    if prev_settlement > 0 and last_settlement < prev_settlement:
        mood = "ashamed"
        line = moods.get("ashamed") or "比上次少 — 羞耻感，下轮必须更强"
    elif last_mood == "ashamed" and last_settlement >= prev_settlement and prev_settlement > 0:
        mood = "redemption"
        line = moods.get("redemption") or "从低谷拉回 — 奋发图强"
    elif prev_settlement > 0 and last_settlement > prev_settlement:
        mood = "ambitious"
        line = moods.get("ambitious") or f"比上次强 {delta_pct}%"
    else:
        mood = "conquest"
        line = moods.get("conquest") or p.get("conquest_line") or "打江山"

    week_delta = week_total - prev_week_total if prev_week_total > 0 else week_total
    return {
        "mood": mood,
        "line": line,
        "delta_settlement_minor": delta_settlement,
        "delta_settlement_pct": delta_pct,
        "week_delta_minor": week_delta,
        "codename": p.get("codename") or "摸金打江山",
        "traits": list(p.get("traits") or []),
        "vs_last": "stronger" if delta_settlement > 0 else ("weaker" if delta_settlement < 0 else "same"),
    }


def get_cumulative_stats(*, refresh_periods: bool = True) -> dict[str, Any]:
    """get_cumulative_stats。

    参数说明：
    :param refresh_periods: 参数 refresh_periods
    :return: 返回处理结果。
    """
    assert_greedy_action("read_greedy_memory")
    data = _store_get(_CUMULATIVE_KEY) or _default_cumulative()
    if refresh_periods:
        data = _rotate_period_buckets(data)
        _store_set(_CUMULATIVE_KEY, data)
    pers = evaluate_personality(
        last_settlement=int(data.get("last_settlement_minor") or 0),
        prev_settlement=int(data.get("prev_settlement_minor") or 0),
        week_total=int(data.get("week_revenue_minor") or 0),
        prev_week_total=int(data.get("prev_week_total_minor") or 0),
        last_mood=str(data.get("last_mood") or "conquest"),
    )
    return {
        **data,
        "personality": pers,
        "global_revenue_policy": _contest_cfg().get("global_revenue"),
        "display": {
            "week_cny": round(int(data.get("week_revenue_minor") or 0) / 100, 2),
            "month_cny": round(int(data.get("month_revenue_minor") or 0) / 100, 2),
            "year_cny": round(int(data.get("year_revenue_minor") or 0) / 100, 2),
            "lifetime_cny": round(int(data.get("lifetime_revenue_minor") or 0) / 100, 2),
            "last_settlement_cny": round(int(data.get("last_settlement_minor") or 0) / 100, 2),
            "prev_settlement_cny": round(int(data.get("prev_settlement_minor") or 0) / 100, 2),
        },
    }


def record_cumulative_settlement(
    *,
    amount_base_minor: int,
    currency: str = "CNY",
    provider_payment_id: str | None = None,
) -> dict[str, Any]:
    """record_cumulative_settlement。

    参数说明：
    :param amount_base_minor: 参数 amount_base_minor
    :param currency: 参数 currency
    :param provider_payment_id: 参数 provider_payment_id
    :return: 返回处理结果。
    """
    assert_greedy_action("write_greedy_memory")
    amt = max(int(amount_base_minor), 0)
    data = _store_get(_CUMULATIVE_KEY) or _default_cumulative()
    data = _rotate_period_buckets(data)
    prev_before = int(data.get("last_settlement_minor") or 0)
    data["prev_settlement_minor"] = prev_before
    data["last_settlement_minor"] = amt
    data["last_settlement_currency"] = (currency or "CNY").upper()
    data["last_settlement_at"] = datetime.now(timezone.utc).isoformat()
    data["last_payment_id"] = provider_payment_id
    data["settlements_count"] = int(data.get("settlements_count") or 0) + 1
    data["week_revenue_minor"] = int(data.get("week_revenue_minor") or 0) + amt
    data["month_revenue_minor"] = int(data.get("month_revenue_minor") or 0) + amt
    data["year_revenue_minor"] = int(data.get("year_revenue_minor") or 0) + amt
    data["lifetime_revenue_minor"] = int(data.get("lifetime_revenue_minor") or 0) + amt
    pers = evaluate_personality(
        last_settlement=amt,
        prev_settlement=prev_before,
        week_total=int(data.get("week_revenue_minor") or 0),
        prev_week_total=int(data.get("prev_week_total_minor") or 0),
        last_mood=str(data.get("personality_mood") or "conquest"),
    )
    data["last_mood"] = data.get("personality_mood") or "conquest"
    data["personality_mood"] = pers["mood"]
    if pers["mood"] == "redemption":
        data["redemption_streak"] = int(data.get("redemption_streak") or 0) + 1
    elif pers["mood"] == "ashamed":
        data["redemption_streak"] = 0

    _store_set(_CUMULATIVE_KEY, data)
    cum_cfg = _contest_cfg().get("cumulative") or {}
    bonus = 0
    if pers["vs_last"] == "stronger" and prev_before > 0:
        bonus = int(cum_cfg.get("improvement_bonus_points") or 35)
        if pers["mood"] == "redemption":
            bonus = int(cum_cfg.get("redemption_bonus_points") or 50)

    mojin = _store_get(_MOJIN_KEY) or {}
    mojin["cumulative"] = get_cumulative_stats(refresh_periods=False)
    mojin["personality_mood"] = pers["mood"]
    mojin["personality_line"] = pers["line"]
    lessons = list(mojin.get("lessons") or [])
    lesson = (
        f"[{pers['mood']}] ¥{amt/100:.2f} {currency.upper()} global · "
        f"周累计¥{int(data['week_revenue_minor'])/100:.2f} · {pers['line'][:120]}"
    )
    lessons.insert(0, lesson[:480])
    mojin["lessons"] = lessons[: int((_contest_cfg().get("memory") or {}).get("max_lessons_mojin") or 48)]
    _store_set(_MOJIN_KEY, mojin)
    return {
        "ok": True,
        "amount_base_minor": amt,
        "currency": currency.upper(),
        "cumulative": get_cumulative_stats(refresh_periods=False),
        "personality": pers,
        "improvement_bonus_points": bonus,
    }


def apply_role_settlement_personality(
    mem: dict[str, Any],
    *,
    share_minor: int,
    global_personality: dict[str, Any],
) -> dict[str, Any]:
    """apply_role_settlement_personality。

    参数说明：
    :param mem: 参数 mem
    :param share_minor: 参数 share_minor
    :param global_personality: 参数 global_personality
    :return: 返回处理结果。
    """
    keys = period_keys()
    if mem.get("cum_week_key") != keys["week_key"]:
        mem["prev_week_share_minor"] = int(mem.get("revenue_week_minor") or 0)
        mem["revenue_week_minor"] = 0
        mem["cum_week_key"] = keys["week_key"]
    if mem.get("cum_month_key") != keys["month_key"]:
        mem["prev_month_share_minor"] = int(mem.get("revenue_month_minor") or 0)
        mem["revenue_month_minor"] = 0
        mem["cum_month_key"] = keys["month_key"]
    if mem.get("cum_year_key") != keys["year_key"]:
        mem["prev_year_share_minor"] = int(mem.get("revenue_year_minor") or 0)
        mem["revenue_year_minor"] = 0
        mem["cum_year_key"] = keys["year_key"]

    prev = int(mem.get("last_settlement_share_minor") or 0)
    mem["last_settlement_share_minor"] = share_minor
    mem["revenue_week_minor"] = int(mem.get("revenue_week_minor") or 0) + share_minor
    mem["revenue_month_minor"] = int(mem.get("revenue_month_minor") or 0) + share_minor
    mem["revenue_year_minor"] = int(mem.get("revenue_year_minor") or 0) + share_minor
    mood = global_personality.get("mood") or "conquest"
    mem["personality_mood"] = mood
    if prev > 0 and share_minor < prev:
        mem["personality_note"] = f"羞耻：本次分摊¥{share_minor/100:.2f} < 上次¥{prev/100:.2f}，下轮更强"
    elif prev > 0 and share_minor > prev:
        mem["personality_note"] = f"奋发：比上次强 {round(100*(share_minor-prev)/prev,1)}%"
    else:
        mem["personality_note"] = global_personality.get("line") or "打江山"
    return mem


def format_personality_prompt_block() -> str:
    """format_personality_prompt_block。
    :return: 返回处理结果。
    """
    stats = get_cumulative_stats()
    p = stats.get("personality") or {}
    d = stats.get("display") or {}
    return (
        f"【{p.get('codename', '摸金打江山')}·{p.get('mood', 'conquest')}】"
        f"全球不限境内外 · 周¥{d.get('week_cny', 0)} 月¥{d.get('month_cny', 0)} 年¥{d.get('year_cny', 0)} · "
        f"上次¥{d.get('prev_settlement_cny', 0)} → 本次¥{d.get('last_settlement_cny', 0)} · "
        f"{p.get('line', '')}"
    )[:900]
