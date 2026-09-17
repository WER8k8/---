# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""出海参谋 M0 — 品类×国家规则矩阵（可解释、可溯源）。"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from dataclasses import dataclass
from typing import Any, TYPE_CHECKING

from app.services.trade_intel_data import (
    load_category_aliases,
    load_country_aliases,
    load_trade_matrix,
)

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

DISCLAIMER = (
    "仅供参考，不构成法律意见；签约前请专业报关/律师确认。"
)

_MATRIX = load_trade_matrix()

_CATEGORY_ALIASES: dict[str, str] = load_category_aliases()

_COUNTRY_ALIASES: dict[str, str] = load_country_aliases()


@dataclass
class FeasibilityResult:
    verdict: str
    verdict_label: str
    category: str
    country_code: str
    hs_chapter: str
    summary: str
    certs: list[str]
    growth: str
    competition: str
    sources: list[str]
    llm_supplemented: bool = False
    matrix_hit: bool = True
    def to_dict(self) -> dict[str, Any]:
        """to_dict。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return {
            "verdict": self.verdict,
            "verdict_label": self.verdict_label,
            "category": self.category,
            "country_code": self.country_code,
            "hs_chapter": self.hs_chapter,
            "summary": self.summary,
            "certs": self.certs,
            "growth": self.growth,
            "competition": self.competition,
            "sources": self.sources,
            "llm_supplemented": self.llm_supplemented,
            "matrix_hit": self.matrix_hit,
            "disclaimer": DISCLAIMER,
        }


_VERDICT_LABEL = {"go": "可做", "caution": "谨慎做", "hard": "难度高"}


def _resolve_category(text: str) -> str | None:
    """_resolve_category。

    参数说明：
    :param text: 参数 text
    :return: 返回处理结果。
    """
    lower = text.lower()
    for key, cat in _CATEGORY_ALIASES.items():
        if key in text or key in lower:
            return cat
    for row in _MATRIX:
        if row["category_label"] in text or row["category_key"] in lower:
            return row["category_key"]
    return "insulation_board"


def _resolve_country(text: str) -> str | None:
    """_resolve_country。

    参数说明：
    :param text: 参数 text
    :return: 返回处理结果。
    """
    import re
    m = re.search(r"\b([A-Z]{2})\b", text.upper())
    if m:
        return m.group(1)
    for name, code in _COUNTRY_ALIASES.items():
        if name in text:
            return code
    return None


def _matrix_row(cat_key: str) -> dict[str, Any]:
    """_matrix_row。

    参数说明：
    :param cat_key: 参数 cat_key
    :return: 返回处理结果。
    """
    return next((r for r in _MATRIX if r["category_key"] == cat_key), _MATRIX[0])


def _db_countries_for_category(db: "Session", cat_key: str) -> dict[str, dict] | None:
    """_db_countries_for_category。

    参数说明：
    :param db: 参数 db
    :param cat_key: 参数 cat_key
    :return: 返回处理结果。
    """
    try:
        from sqlalchemy.exc import OperationalError, ProgrammingError
        from app.models.trade_intel import TradeCountryCategory
        rows = (
            db.query(TradeCountryCategory)
            .filter(
                TradeCountryCategory.category_key == cat_key,
                TradeCountryCategory.is_active.is_(True),
            )
            .all()
        )
        if not rows:
            return None
        out: dict[str, dict] = {}
        for r in rows:
            out[r.country_code.upper()] = {
                "verdict": r.verdict,
                "growth": r.growth or "",
                "competition": r.competition or "medium",
                "certs": json.loads(r.certs_json or "[]"),
                "notes": r.notes or "",
            }
        return out
    except (OperationalError, ProgrammingError, ImportError):
        return None


def _category_label_for_key(cat_key: str, db: "Session | None") -> str:
    """_category_label_for_key。

    参数说明：
    :param cat_key: 参数 cat_key
    :param db: 参数 db
    :return: 返回处理结果。
    """
    row = _matrix_row(cat_key)
    label = row["category_label"]
    if db is None:
        return label
    try:
        from app.models.trade_intel import TradeCountryCategory
        first = (
            db.query(TradeCountryCategory)
            .filter(TradeCountryCategory.category_key == cat_key)
            .first()
        )
        if first:
            return first.category_label
    except Exception:
        pass
    return label


def _parse_llm_feasibility_json(text: str) -> dict[str, Any] | None:
    """_parse_llm_feasibility_json。

    参数说明：
    :param text: 参数 text
    :return: 返回处理结果。
    """
    raw = (text or "").strip()
    if not raw:
        return None
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
    if fence:
        raw = fence.group(1).strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r"\{[\s\S]*\}", raw)
        if not m:
            return None
        try:
            data = json.loads(m.group(0))
        except json.JSONDecodeError:
            return None
    if not isinstance(data, dict):
        return None
    verdict = str(data.get("verdict") or "caution").lower()
    if verdict not in _VERDICT_LABEL:
        verdict = "caution"
    certs = data.get("certs") or []
    if isinstance(certs, str):
        certs = [certs]
    return {
        "verdict": verdict,
        "notes": str(data.get("summary") or data.get("notes") or "").strip(),
        "certs": [str(c).strip() for c in certs if str(c).strip()],
        "growth": str(data.get("growth") or "N/A"),
        "competition": str(data.get("competition") or "unknown"),
        "hs_chapter": str(data.get("hs_chapter") or "").strip(),
        "country_code": str(data.get("country_code") or "").strip().upper(),
    }


def _llm_export_feasibility(
    message: str,
    *,
    category_label: str,
    country_code: str | None,
    hs_chapter: str,
) -> dict[str, Any] | None:
    """规则库/DB 无该国明细时，用大模型补充可解释结论（仍带免责声明）。"""
    from app.services.ai_engine import get_ai_engine
    engine = get_ai_engine()
    if not engine.is_available():
        return None

    country_hint = country_code or "请从用户问题推断 ISO2 国家代码"
    prompt = f"""你是建材外贸出口可行性顾问。用户问题：
{message.strip()}

已知信息：
- 品类：{category_label}
- 目的国代码（若已知）：{country_hint}
- 建议先查 HS 章：第 {hs_chapter} 章（矿物/建材类，具体税号需按材质确认）

请仅输出一个 JSON 对象（不要其它文字），字段：
- verdict: "go" | "caution" | "hard" 之一
- country_code: 两位 ISO 国家代码（大写）
- hs_chapter: 字符串，如 "6806"
- summary: 80～200 字中文，说明能否出口、主要合规点、建议下一步
- certs: 字符串数组，常见证照/认证名称
- growth: 增速描述或 "N/A"（无数据时）
- competition: "low" | "medium" | "high" | "unknown"

要求：保守、可执行；无实时海关票数据时不要编造具体进口额；涉及欧盟可提 CE/CPR 等通用要求。"""

    try:
        result = asyncio.run(
            engine.generate(
                prompt,
                model="chinese",
                max_tokens=700,
                task_complexity="medium",
                max_retries=2,
            )
        )
        parsed = _parse_llm_feasibility_json(str(result.get("content") or ""))
        if parsed and parsed.get("notes"):
            return parsed
    except Exception as exc:
        logger.warning("export_feasibility LLM fallback failed: %s", exc)
    return None


def _static_missing_country_fallback(label: str, country_code: str, hs: str) -> FeasibilityResult:
    """_static_missing_country_fallback。

    参数说明：
    :param label: 参数 label
    :param country_code: 参数 country_code
    :param hs: 参数 hs
    :return: 返回处理结果。
    """
    code = country_code or "未知"
    return FeasibilityResult(
        verdict="caution",
        verdict_label=_VERDICT_LABEL["caution"],
        category=label,
        country_code=code,
        hs_chapter=hs,
        summary=f"暂无 {label}→{code} 的详细规则，且 AI 暂不可用，建议人工复核或补充贸易情报库。",
        certs=["请咨询当地进口法规"],
        growth="N/A",
        competition="unknown",
        sources=[f"规则矩阵 M0 · HS 第{hs}章 · 无明细"],
        llm_supplemented=False,
        matrix_hit=False,
    )


def export_feasibility(
    message: str,
    *,
    category: str | None = None,
    country: str | None = None,
    db: "Session | None" = None,
) -> FeasibilityResult:
    """export_feasibility。

    参数说明：
    :param message: 参数 message
    :param category: 参数 category
    :param country: 参数 country
    :param db: 参数 db
    :return: 返回处理结果。
    """
    cat_key = category or _resolve_category(message) or "insulation_board"
    country_code = (country or _resolve_country(message) or "").upper() or None
    row = _matrix_row(cat_key)
    label = _category_label_for_key(cat_key, db)
    hs = row["hs_chapter"]
    countries = _db_countries_for_category(db, cat_key) if db is not None else None
    matrix_from_db = countries is not None
    if countries is None:
        countries = row["countries"]

    info = countries.get(country_code) if country_code else None
    if info:
        source = "规则矩阵 DB" if matrix_from_db else "规则矩阵 M0"
        return FeasibilityResult(
            verdict=info["verdict"],
            verdict_label=_VERDICT_LABEL.get(info["verdict"], "待评估"),
            category=label,
            country_code=country_code or "",
            hs_chapter=hs,
            summary=info.get("notes") or "",
            certs=list(info.get("certs") or []),
            growth=info.get("growth", ""),
            competition=info.get("competition", ""),
            sources=[f"{source} · HS 第{hs}章"],
            llm_supplemented=False,
            matrix_hit=True,
        )

    llm_info = _llm_export_feasibility(
        message,
        category_label=label,
        country_code=country_code,
        hs_chapter=hs,
    )
    if llm_info:
        resolved_country = llm_info.get("country_code") or country_code or ""
        resolved_hs = llm_info.get("hs_chapter") or hs
        verdict = llm_info["verdict"]
        return FeasibilityResult(
            verdict=verdict,
            verdict_label=_VERDICT_LABEL.get(verdict, "待评估"),
            category=label,
            country_code=resolved_country,
            hs_chapter=resolved_hs,
            summary=llm_info.get("notes") or "",
            certs=list(llm_info.get("certs") or []),
            growth=llm_info.get("growth", ""),
            competition=llm_info.get("competition", ""),
            sources=[
                f"大模型补充 · HS 第{resolved_hs}章",
                "规则矩阵/DB 无该国明细，结论供参考",
            ],
            llm_supplemented=True,
            matrix_hit=False,
        )

    return _static_missing_country_fallback(label, country_code or "", hs)


def blue_ocean(
    message: str,
    *,
    category: str | None = None,
    db: "Session | None" = None,
) -> dict[str, Any]:
    """blue_ocean。

    参数说明：
    :param message: 参数 message
    :param category: 参数 category
    :param db: 参数 db
    :return: 返回处理结果。
    """
    cat_key = category or _resolve_category(message) or "insulation_board"
    row = _matrix_row(cat_key)
    countries = _db_countries_for_category(db, cat_key) if db is not None else None
    if countries is None:
        countries = row["countries"]

    scored: list[tuple[str, dict, int]] = []
    weight = {"go": 3, "caution": 1, "hard": 0}
    for code, info in countries.items():
        growth = info.get("growth", "+0%")
        try:
            g = int(growth.replace("%", "").replace("+", ""))
        except ValueError:
            g = 0
        comp_penalty = {"low": 2, "medium": 1, "high": 0}.get(info.get("competition", "medium"), 1)
        score = g + comp_penalty * 5 + weight.get(info["verdict"], 0) * 10
        scored.append((code, info, score))

    scored.sort(key=lambda x: x[2], reverse=True)
    top = []
    for code, info, sc in scored[:3]:
        top.append(
            {
                "country_code": code,
                "verdict": info["verdict"],
                "growth": info.get("growth"),
                "competition": info.get("competition"),
                "reason": info.get("notes", "")[:120],
                "score": sc,
            }
        )

    return {
        "category": row["category_label"],
        "hs_chapter": row["hs_chapter"],
        "recommendations": top,
        "disclaimer": DISCLAIMER,
        "sources": ["规则矩阵 M0 · 蓝海评分=增速+竞争+可行性"],
    }


def hs_lookup(message: str) -> dict[str, Any]:
    """hs_lookup。

    参数说明：
    :param message: 参数 message
    :return: 返回处理结果。
    """
    cat_key = _resolve_category(message) or "insulation_board"
    row = next((r for r in _MATRIX if r["category_key"] == cat_key), _MATRIX[0])
    return {
        "hs_chapter": row["hs_chapter"],
        "category": row["category_label"],
        "note": f"建材大类建议从 HS 第 {row['hs_chapter']} 章核查具体税号。",
        "disclaimer": DISCLAIMER,
    }
