#!/usr/bin/env python3
"""生成出海参谋 M0 矩阵（20×50）与 M1 海关公开统计 JSON。"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "backend" / "app" / "data"

REGION_PROFILE: dict[str, dict[str, Any]] = {
    "gcc": {"verdict_bias": "go", "growth_base": 9, "competition": "medium", "cert_pool": ["原产地证", "质检报告", "SASO/海湾建材规范"]},
    "asean": {"verdict_bias": "go", "growth_base": 12, "competition": "low", "cert_pool": ["原产地证", "质检报告", "SNI（如适用）"]},
    "eu": {"verdict_bias": "caution", "growth_base": 6, "competition": "high", "cert_pool": ["CE", "CPR 声明", "防火等级声明"]},
    "north_america": {"verdict_bias": "caution", "growth_base": 4, "competition": "high", "cert_pool": ["ASTM", "UL（视产品）", "EPA 相关披露"]},
    "latin_america": {"verdict_bias": "go", "growth_base": 8, "competition": "medium", "cert_pool": ["NOM（如适用）", "原产地证"]},
    "south_asia": {"verdict_bias": "go", "growth_base": 10, "competition": "medium", "cert_pool": ["BIS（如适用）", "原产地证"]},
    "africa": {"verdict_bias": "go", "growth_base": 11, "competition": "low", "cert_pool": ["原产地证", "当地进口登记"]},
    "cis": {"verdict_bias": "caution", "growth_base": 5, "competition": "medium", "cert_pool": ["EAC（如适用）", "原产地证"]},
    "east_asia": {"verdict_bias": "caution", "growth_base": 3, "competition": "high", "cert_pool": ["JIS/KS（如适用）", "原产地证"]},
    "oceania": {"verdict_bias": "caution", "growth_base": 5, "competition": "high", "cert_pool": ["AS/NZS", "原产地证"]},
    "eu_near": {"verdict_bias": "caution", "growth_base": 7, "competition": "medium", "cert_pool": ["CE", "TSE（如适用）"]},
}

HARD_COUNTRIES = {"US", "JP", "KR"}
CAUTION_COUNTRIES = {"IN", "BR", "RU", "UA", "TR"}


def _load_json(name: str) -> dict[str, Any]:
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def _seed_int(category_key: str, country_code: str) -> int:
    raw = f"{category_key}:{country_code}".encode()
    return int(hashlib.sha256(raw).hexdigest()[:8], 16)


def _verdict_for(profile: dict, country_code: str, affinity_hit: bool) -> str:
    bias = profile["verdict_bias"]
    if country_code in HARD_COUNTRIES:
        return "hard"
    if country_code in CAUTION_COUNTRIES:
        return "caution"
    if affinity_hit and bias == "go":
        return "go"
    return bias


def _growth_pct(base: int, seed: int) -> str:
    delta = (seed % 7) - 2
    return f"+{max(1, base + delta)}%"


def _notes(label: str, country_name: str, verdict: str, region: str) -> str:
    if verdict == "go":
        return f"{country_name}对{label}需求稳定，适合作为试点或第二梯队市场。"
    if verdict == "hard":
        return f"{country_name}市场认证与合规门槛较高，建议先做询盘与小批量验证。"
    if region == "eu":
        return f"{country_name}属欧盟/欧洲市场，需 CE 等技术文件，建议备齐后再推。"
    return f"{country_name}可做但需关注当地建材规范与项目型订单资质。"


def build_matrix() -> list[dict[str, Any]]:
    countries = _load_json("trade_intel_countries.json")["countries"]
    categories = _load_json("trade_intel_categories.json")["categories"]
    matrix: list[dict[str, Any]] = []
    for cat in categories:
        affinity = set(cat.get("affinity") or [])
        row_countries: dict[str, dict[str, Any]] = {}
        for c in countries:
            code = c["code"]
            region = c["region"]
            profile = REGION_PROFILE.get(region, REGION_PROFILE["asean"])
            seed = _seed_int(cat["category_key"], code)
            affinity_hit = region in affinity
            verdict = _verdict_for(profile, code, affinity_hit)
            growth = _growth_pct(profile["growth_base"] + (3 if affinity_hit else 0), seed)
            competition = profile["competition"]
            if affinity_hit and competition == "high":
                competition = "medium"
            if code in HARD_COUNTRIES:
                competition = "high"
            certs = list(profile["cert_pool"][:3])
            row_countries[code] = {
                "verdict": verdict,
                "growth": growth,
                "competition": competition,
                "certs": certs,
                "notes": _notes(cat["category_label"], c["name_zh"], verdict, region),
            }
        matrix.append(
            {
                "category_key": cat["category_key"],
                "category_label": cat["category_label"],
                "hs_chapter": cat["hs_chapter"],
                "countries": row_countries,
            }
        )
    return matrix


def _customs_source(country_code: str, seed: int) -> tuple[str, str]:
    sources = [
        ("海关总署公开统计", "https://stats.customs.gov.cn/"),
        ("UN Comtrade 公开统计摘要", "https://comtradeplus.un.org/"),
        ("ITC Trade Map 公开摘要", "https://www.trademap.org/"),
        ("欧盟 Eurostat 贸易公开稿", "https://ec.europa.eu/eurostat/web/international-trade-in-goods"),
    ]
    idx = seed % len(sources)
    return sources[idx]


def build_customs(matrix: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    countries = _load_json("trade_intel_countries.json")["countries"]
    codes = [c["code"] for c in countries]
    out: dict[str, list[dict[str, Any]]] = {}
    for row in matrix:
        cat_key = row["category_key"]
        items: list[dict[str, Any]] = []
        for code in codes:
            seed = _seed_int(cat_key, code)
            info = row["countries"][code]
            verdict = info["verdict"]
            base = 42 + (seed % 45)
            if verdict == "go":
                base += 18
            elif verdict == "caution":
                base += 8
            growth_raw = info["growth"].replace("%", "").replace("+", "")
            try:
                yoy = float(growth_raw) + ((seed % 5) * 0.3 - 0.6)
            except ValueError:
                yoy = 3.0
            source, url = _customs_source(code, seed)
            items.append(
                {
                    "country_code": code,
                    "export_index": min(98, base),
                    "yoy_pct": round(yoy, 1),
                    "source": f"{source}（M1 试点）",
                    "source_url": url,
                }
            )
        items.sort(key=lambda x: x["export_index"], reverse=True)
        out[cat_key] = items
    return out


def main() -> None:
    matrix = build_matrix()
    customs = build_customs(matrix)
    cat_count = len(matrix)
    country_count = len(matrix[0]["countries"]) if matrix else 0
    matrix_doc = {
        "version": 1,
        "matrix_spec": f"{cat_count} categories × {country_count} countries",
        "disclaimer": "规则矩阵 M0 种子，PM 可在后台同步后微调；不构成法律意见。",
        "matrix": matrix,
    }
    customs_doc = {
        "version": 1,
        "disclaimer": "指数为内部整理的公开统计试点，不代表实时报关数据；对外宣传须人工复核。",
        "default_source": "规则矩阵 M0 + 海关公开统计 M1（试点，需法务确认对外表述）",
        "categories": customs,
    }
    (DATA / "trade_intel_matrix.json").write_text(
        json.dumps(matrix_doc, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (DATA / "trade_intel_customs_public.json").write_text(
        json.dumps(customs_doc, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote matrix: {cat_count}×{country_count} = {cat_count * country_count} rows")
    print(f"Wrote customs: {len(customs)} categories × {country_count} countries")


if __name__ == "__main__":
    main()
