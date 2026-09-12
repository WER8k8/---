"""UN Comtrade 公开 API — 中国出口按 HS 章别拉取目的国贸易额。"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger("uj-admin.trade_intel_comtrade")

_DATA_DIR = Path(__file__).resolve().parents[1] / "data"
_PREVIEW_URL = "https://comtradeapi.un.org/public/v1/preview/C/A/HS"
_API_URL = "https://comtradeapi.un.org/data/v1/get/C/A/HS"


def _partner_map() -> dict[str, int]:
    """_partner_map。
    :return: 返回处理结果。
    """
    doc = json.loads((_DATA_DIR / "trade_intel_comtrade_partners.json").read_text(encoding="utf-8"))
    return {k.upper(): int(v) for k, v in (doc.get("iso2_to_m49") or {}).items()}


def _reporter_china() -> int:
    """_reporter_china。
    :return: 返回处理结果。
    """
    doc = json.loads((_DATA_DIR / "trade_intel_comtrade_partners.json").read_text(encoding="utf-8"))
    return int(doc.get("reporter_china_m49") or 156)


def _m49_to_iso() -> dict[int, str]:
    """_m49_to_iso。
    :return: 返回处理结果。
    """
    return {v: k for k, v in _partner_map().items()}


def fetch_china_exports_by_hs(
    hs_chapter: str,
    period: int,
    *,
    sleep_sec: float = 0.6,
) -> dict[str, float]:
    """
    返回 {ISO2: primaryValueUSD}，仅含映射表内的目的国。
    失败返回空 dict。
    """
    hs = str(hs_chapter).strip()[:4]
    if not hs.isdigit():
        return {}

    params: dict[str, Any] = {
        "reporterCode": _reporter_china(),
        "period": str(period),
        "flowCode": "X",
        "cmdCode": hs,
    }
    key = getattr(settings, "UN_COMTRADE_SUBSCRIPTION_KEY", None) or ""
    use_preview = bool(getattr(settings, "UN_COMTRADE_USE_PREVIEW", True))
    url = _PREVIEW_URL if (use_preview and not key) else _API_URL
    if key:
        params["subscription-key"] = key

    try:
        with httpx.Client(timeout=90.0) as client:
            resp = client.get(url, params=params)
        if resp.status_code != 200:
            logger.warning("Comtrade HTTP %s hs=%s period=%s", resp.status_code, hs, period)
            return {}
        payload = resp.json()
        rows = payload.get("data") or []
    except Exception as exc:
        logger.warning("Comtrade fetch failed hs=%s period=%s: %s", hs, period, exc)
        return {}
    finally:
        if sleep_sec > 0:
            time.sleep(sleep_sec)

    iso_by_m49 = _m49_to_iso()
    out: dict[str, float] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        try:
            m49 = int(row.get("partnerCode") or 0)
        except (TypeError, ValueError):
            continue
        iso = iso_by_m49.get(m49)
        if not iso:
            continue
        try:
            val = float(row.get("primaryValue") or row.get("tradeValue") or 0)
        except (TypeError, ValueError):
            val = 0.0
        if val <= 0:
            continue
        out[iso] = out.get(iso, 0.0) + val
    return out


def fetch_hs_pair_years(hs_chapter: str, year_new: int, year_old: int) -> tuple[dict[str, float], dict[str, float]]:
    """fetch_hs_pair_years。

    参数说明：
    :param hs_chapter: 参数 hs_chapter
    :param year_new: 参数 year_new
    :param year_old: 参数 year_old
    :return: 返回处理结果。
    """
    return (
        fetch_china_exports_by_hs(hs_chapter, year_new),
        fetch_china_exports_by_hs(hs_chapter, year_old),
    )
