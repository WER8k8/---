"""出海参谋 M1 — 定时从 UN Comtrade 刷新海关公开统计 JSON。"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TYPE_CHECKING

from app.services.trade_intel_comtrade_client import fetch_hs_pair_years
from app.services.trade_intel_data import load_customs_public, reload_trade_intel_cache

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

logger = logging.getLogger("uj-admin.trade_intel_refresh")

_DATA_DIR = Path(__file__).resolve().parents[1] / "data"
_CUSTOMS_PATH = _DATA_DIR / "trade_intel_customs_public.json"
_SNAPSHOT_PATH = _DATA_DIR / "trade_intel_refresh_snapshot.json"


def _load_categories() -> list[dict[str, Any]]:
    """_load_categories。
    :return: 返回处理结果。
    """
    doc = json.loads((_DATA_DIR / "trade_intel_categories.json").read_text(encoding="utf-8"))
    return list(doc.get("categories") or [])


def _load_countries() -> list[str]:
    """_load_countries。
    :return: 返回处理结果。
    """
    doc = json.loads((_DATA_DIR / "trade_intel_countries.json").read_text(encoding="utf-8"))
    return [str(c["code"]).upper() for c in doc.get("countries") or [] if c.get("code")]


def _index_to_100(values: dict[str, float], countries: list[str]) -> dict[str, int]:
    """_index_to_100。

    参数说明：
    :param values: 参数 values
    :param countries: 参数 countries
    :return: 返回处理结果。
    """
    nums = [values.get(c, 0.0) for c in countries if values.get(c, 0.0) > 0]
    if not nums:
        return {}
    lo, hi = min(nums), max(nums)
    span = hi - lo if hi > lo else hi or 1.0
    out: dict[str, int] = {}
    for c in countries:
        v = values.get(c, 0.0)
        if v <= 0:
            continue
        score = 40 + int(58 * (v - lo) / span)
        out[c] = min(98, max(42, score))
    return out


def _yoy_pct(new: float, old: float) -> float | None:
    """_yoy_pct。

    参数说明：
    :param new: 参数 new
    :param old: 参数 old
    :return: 返回处理结果。
    """
    if old <= 0 or new <= 0:
        return None
    return round((new - old) / old * 100.0, 1)


def _default_years() -> tuple[int, int]:
    """Comtrade 年报通常滞后 1～2 年。"""
    y = datetime.now(timezone.utc).year
    return y - 2, y - 3


def _fetch_all_hs_data(
    hs_to_cats: dict[str, list[str]],
    year_new: int,
    year_old: int,
) -> tuple[dict[str, tuple[dict[str, float], dict[str, float]]], list[str]]:
    """抓取各 HS 章别的两年数据，失败记录错误并继续。"""
    hs_fetched: dict[str, tuple[dict[str, float], dict[str, float]]] = {}
    errors: list[str] = []
    for hs in hs_to_cats:
        try:
            hs_fetched[hs] = fetch_hs_pair_years(hs, year_new, year_old)
        except Exception as exc:
            errors.append(f"HS{hs}: {exc}")
            logger.exception("Comtrade HS %s failed", hs)
    return hs_fetched, errors


def _build_category_row(
    code: str,
    *,
    hs: str,
    curr_vals: dict[str, float],
    prev_vals: dict[str, float],
    indices: dict[str, int],
    prev_row: dict[str, Any],
    year_new: int,
) -> tuple[dict[str, Any], bool]:
    """按国家构造单行出口数据，返回（行, 是否 fallback）。"""
    yoy = _yoy_pct(curr_vals.get(code, 0.0), prev_vals.get(code, 0.0))
    if code in indices:
        return {
            "country_code": code,
            "export_index": indices[code],
            "yoy_pct": yoy if yoy is not None else prev_row.get("yoy_pct", 0.0),
            "trade_value_usd": round(curr_vals.get(code, 0.0), 2),
            "source": f"UN Comtrade 中国出口 HS{hs}（{year_new}）",
            "source_url": "https://comtradeplus.un.org/",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }, False
    if prev_row:
        row = dict(prev_row)
        row["fetched_at"] = row.get("fetched_at") or prev_row.get("fetched_at")
        return row, True
    return {
        "country_code": code,
        "export_index": 50,
        "yoy_pct": 0.0,
        "source": "规则种子（Comtrade 无该国数据）",
        "source_url": "https://comtradeplus.un.org/",
    }, True


def _build_updated_categories(
    categories: list[dict[str, Any]],
    *,
    countries: list[str],
    hs_fetched: dict[str, tuple[dict[str, float], dict[str, float]]],
    prev_by_cat: dict[str, dict[str, dict[str, Any]]],
    year_new: int,
) -> tuple[dict[str, list[dict[str, Any]]], int, int]:
    """按品类组装出口指数、同比与 fallback 行。"""
    updated_categories: dict[str, list[dict[str, Any]]] = {}
    rows_updated = 0
    rows_fallback = 0
    for cat in categories:
        key = str(cat["category_key"])
        hs = str(cat.get("hs_chapter") or "")
        curr_vals, prev_vals = hs_fetched.get(hs, ({}, {}))
        indices = _index_to_100(curr_vals, countries)
        items: list[dict[str, Any]] = []
        for code in countries:
            prev_row = (prev_by_cat.get(key) or {}).get(code) or {}
            row, fallback = _build_category_row(
                code,
                hs=hs,
                curr_vals=curr_vals,
                prev_vals=prev_vals,
                indices=indices,
                prev_row=prev_row,
                year_new=year_new,
            )
            if fallback:
                rows_fallback += 1
            else:
                rows_updated += 1
            items.append(row)

        items.sort(key=lambda x: int(x.get("export_index") or 0), reverse=True)
        updated_categories[key] = items
    return updated_categories, rows_updated, rows_fallback


def _seed_db_if_requested(db: "Session | None", seed_db: bool, errors: list[str]) -> dict[str, Any] | None:
    """可选地将新数据播种进数据库（seed_trade_matrix）。"""
    if not seed_db or db is None:
        return None
    try:
        from app.services.trade_intel_seed import seed_trade_matrix
        return seed_trade_matrix(db)
    except Exception as exc:
        errors.append(f"db_seed: {exc}")
        logger.exception("trade matrix seed after refresh failed")
        return None


def _write_refresh_snapshot(
    *,
    trigger: str,
    year_new: int,
    year_old: int,
    hs_fetched: dict,
    updated_categories: dict,
    countries: list[str],
    rows_updated: int,
    rows_fallback: int,
    errors: list[str],
    db_seed: dict[str, Any] | None,
) -> dict[str, Any]:
    """写入刷新 snapshot JSON 并返回内容。"""
    snapshot = {
        "trigger": trigger,
        "saved_at": datetime.now(timezone.utc).isoformat(),
        "years": {"new": year_new, "old": year_old},
        "hs_chapters_fetched": len(hs_fetched),
        "categories": len(updated_categories),
        "countries": len(countries),
        "rows_updated": rows_updated,
        "rows_fallback": rows_fallback,
        "errors": errors,
        "db_seed": db_seed,
    }
    _SNAPSHOT_PATH.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return snapshot


def refresh_customs_from_comtrade(
    *,
    year_new: int | None = None,
    year_old: int | None = None,
    db: "Session | None" = None,
    seed_db: bool = True,
    trigger: str = "manual",
) -> dict[str, Any]:
    """
    按 HS 章别抓取中国出口 → 更新 trade_intel_customs_public.json。
    失败品类保留上一版数值。
    """
    if year_new is None or year_old is None:
        year_new, year_old = _default_years()

    categories = _load_categories()
    countries = _load_countries()
    prev = load_customs_public()
    prev_by_cat = {k: {r["country_code"]: r for r in v} for k, v in prev.items()}
    hs_to_cats: dict[str, list[str]] = {}
    for cat in categories:
        hs = str(cat.get("hs_chapter") or "")
        hs_to_cats.setdefault(hs, []).append(str(cat["category_key"]))

    hs_fetched, errors = _fetch_all_hs_data(hs_to_cats, year_new, year_old)

    updated_categories, rows_updated, rows_fallback = _build_updated_categories(
        categories,
        countries=countries,
        hs_fetched=hs_fetched,
        prev_by_cat=prev_by_cat,
        year_new=year_new,
    )

    doc = {
        "version": 1,
        "disclaimer": (
            "指数为 UN Comtrade 公开统计整理（中国出口按 HS 章别），"
            "不代表实时报关；对外宣传须人工复核。"
        ),
        "default_source": f"UN Comtrade 定时抓取 M1（{year_new}/{year_old} 对比）",
        "categories": updated_categories,
    }
    _CUSTOMS_PATH.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    reload_trade_intel_cache()
    db_seed = _seed_db_if_requested(db, seed_db, errors)

    snapshot = _write_refresh_snapshot(
        trigger=trigger,
        year_new=year_new,
        year_old=year_old,
        hs_fetched=hs_fetched,
        updated_categories=updated_categories,
        countries=countries,
        rows_updated=rows_updated,
        rows_fallback=rows_fallback,
        errors=errors,
        db_seed=db_seed,
    )
    logger.info(
        "Trade intel refresh done trigger=%s updated=%s fallback=%s errors=%s",
        trigger,
        rows_updated,
        rows_fallback,
        len(errors),
    )
    return snapshot


def load_refresh_snapshot() -> dict[str, Any] | None:
    """load_refresh_snapshot。
    :return: 返回处理结果。
    """
    if not _SNAPSHOT_PATH.is_file():
        return None
    try:
        return json.loads(_SNAPSHOT_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
