# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""廊坊大城 + 沧州河间 建筑主材/附属 SEO 词库入库 — P0-4。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.models.region import (
    CombinatorialRule,
    District,
    GeneratedKeyword,
    GroupKeyword,
    IndustryKeyword,
    KeywordGroup,
)
from app.models.seo import KeywordRanking

_KEYWORDS_PATH = Path(__file__).resolve().parents[1] / "data" / "dacheng_seo_keywords.json"
_LEGACY_GROUP = "大城保温建材基本盘"


def load_dacheng_keyword_pack() -> dict[str, Any]:
    """兼容旧版单带 JSON；新版以 belts 数组为准。"""
    if not _KEYWORDS_PATH.is_file():
        return {"belts": [], "ranking_keywords": [], "products": []}
    try:
        data = json.loads(_KEYWORDS_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {"belts": [], "ranking_keywords": [], "products": []}


def list_belt_packs(*, belt_id: str | None = None) -> list[dict[str, Any]]:
    """list_belt_packs。

    参数说明：
    :param belt_id: 参数 belt_id
    :return: 返回处理结果。
    """
    root = load_dacheng_keyword_pack()
    belts = root.get("belts")
    if isinstance(belts, list) and belts:
        packs = [b for b in belts if isinstance(b, dict)]
        if belt_id and belt_id not in ("all", "*"):
            packs = [p for p in packs if p.get("belt_id") == belt_id]
        return packs
    if belt_id and belt_id not in ("all", "*", root.get("belt_id")):
        return []
    return [root]


def _merged_ranking_keywords(packs: list[dict[str, Any]]) -> list[str]:
    """_merged_ranking_keywords。

    参数说明：
    :param packs: 参数 packs
    :return: 返回处理结果。
    """
    seen: set[str] = set()
    out: list[str] = []
    for pack in packs:
        for kw in pack.get("ranking_keywords") or []:
            text = str(kw).strip()
            if text and text not in seen:
                seen.add(text)
                out.append(text)
    return out


def seed_ranking_keywords(
    db: Session,
    *,
    belt_id: str | None = None,
) -> dict[str, int]:
    """seed_ranking_keywords。

    参数说明：
    :param db: 参数 db
    :param belt_id: 参数 belt_id
    :return: 返回处理结果。
    """
    packs = list_belt_packs(belt_id=belt_id or "all")
    imported = 0
    skipped = 0
    for keyword_text in _merged_ranking_keywords(packs):
        text = keyword_text.strip()
        if not text:
            continue
        existing = (
            db.query(KeywordRanking)
            .filter(
                KeywordRanking.keyword == text,
                KeywordRanking.search_engine == "baidu",
            )
            .first()
        )
        if existing:
            skipped += 1
            continue
        category = "廊坊大城·河间建筑产业带"
        for pack in packs:
            if any(text in str(k) for k in (pack.get("ranking_keywords") or [])):
                category = pack.get("label") or category
                break
        db.add(
            KeywordRanking(
                keyword=text,
                search_engine="baidu",
                category=category[:100],
                is_tracking=True,
            )
        )
        imported += 1
    db.commit()
    return {"imported": imported, "skipped": skipped}


def _get_or_create_group(db: Session, name: str, description: str) -> KeywordGroup:
    """_get_or_create_group。

    参数说明：
    :param db: 参数 db
    :param name: 参数 name
    :param description: 参数 description
    :return: 返回处理结果。
    """
    row = db.query(KeywordGroup).filter(KeywordGroup.name == name).first()
    if row:
        return row
    row = KeywordGroup(name=name, description=description, is_active=True)
    db.add(row)
    db.flush()
    return row


def _ensure_industry_keyword(
    db: Session,
    keyword: str,
    *,
    keyword_type: str = "product",
    category: str = "建筑建材",
) -> IndustryKeyword:
    """_ensure_industry_keyword。

    参数说明：
    :param db: 参数 db
    :param keyword: 参数 keyword
    :param keyword_type: 参数 keyword_type
    :param category: 参数 category
    :return: 返回处理结果。
    """
    text = keyword.strip()
    row = db.query(IndustryKeyword).filter(IndustryKeyword.keyword == text).first()
    if row:
        return row
    row = IndustryKeyword(
        keyword=text,
        keyword_type=keyword_type,
        category=category[:100],
        is_active=True,
    )
    db.add(row)
    db.flush()
    return row


def _seed_one_belt_matrix(db: Session, pack: dict[str, Any]) -> dict[str, Any]:
    """_seed_one_belt_matrix。

    参数说明：
    :param db: 参数 db
    :param pack: 参数 pack
    :return: 返回处理结果。
    """
    belt_id = pack.get("belt_id") or "unknown"
    group_name = pack.get("group_name") or pack.get("label") or _LEGACY_GROUP
    group = _get_or_create_group(
        db,
        group_name,
        f"{pack.get('label') or group_name}（主材+附属，P0-4）",
    )
    category = (pack.get("label") or "建筑建材")[:100]
    group_links = 0
    generated_imported = 0
    product_set: set[str] = set()
    for product in pack.get("products") or []:
        text = str(product).strip()
        if not text:
            continue
        product_set.add(text)
        ik = _ensure_industry_keyword(db, text, keyword_type="product", category=category)
        link = (
            db.query(GroupKeyword)
            .filter(GroupKeyword.group_id == group.id, GroupKeyword.keyword_id == ik.id)
            .first()
        )
        if not link:
            db.add(GroupKeyword(group_id=group.id, keyword_id=ik.id))
            group_links += 1

    for kw in pack.get("ranking_keywords") or []:
        text = str(kw).strip()
        if not text:
            continue
        ik = _ensure_industry_keyword(db, text, keyword_type="local", category=category)
        link = (
            db.query(GroupKeyword)
            .filter(GroupKeyword.group_id == group.id, GroupKeyword.keyword_id == ik.id)
            .first()
        )
        if not link:
            db.add(GroupKeyword(group_id=group.id, keyword_id=ik.id))
            group_links += 1

    districts: list[District] = []
    for region in pack.get("regions") or []:
        part = (
            db.query(District)
            .filter(District.name.like(f"%{region}%"))
            .limit(5)
            .all()
        )
        for d in part:
            if d not in districts:
                districts.append(d)

    root = load_dacheng_keyword_pack()
    templates = root.get("long_tail_templates") or pack.get("long_tail_templates") or [
        "{region}{product}厂家"
    ]
    products = list(product_set)[:12]
    for district in districts:
        region_name = district.name
        for product in products:
            for tpl in templates[:4]:
                try:
                    text = tpl.format(region=region_name, product=product).strip()
                except (KeyError, ValueError):
                    continue
                if len(text) < 4:
                    continue
                exists = db.query(GeneratedKeyword).filter_by(keyword=text).first()
                if exists:
                    continue
                ik = _ensure_industry_keyword(db, product, keyword_type="product", category=category)
                db.add(
                    GeneratedKeyword(
                        keyword=text,
                        district_id=district.id,
                        industry_keyword_id=ik.id,
                        is_valid=True,
                    )
                )
                generated_imported += 1

    rule_name = f"{group_name}组合规则"
    rule = db.query(CombinatorialRule).filter(CombinatorialRule.name == rule_name).first()
    if not rule:
        db.add(
            CombinatorialRule(
                name=rule_name,
                template="{district}{product}厂家",
                description=f"{pack.get('label')} 默认组合",
                is_active=True,
                priority=5,
            )
        )

    return {
        "belt_id": belt_id,
        "label": pack.get("label"),
        "group_id": str(group.id),
        "group_name": group_name,
        "products_in_pack": len(product_set),
        "group_links": group_links,
        "generated_keywords": generated_imported,
        "districts_matched": [d.name for d in districts],
        "districts_missing": len(districts) == 0,
    }


def seed_matrix_keywords(db: Session, *, belt_id: str | None = None) -> dict[str, Any]:
    """seed_matrix_keywords。

    参数说明：
    :param db: 参数 db
    :param belt_id: 参数 belt_id
    :return: 返回处理结果。
    """
    packs = list_belt_packs(belt_id=belt_id or "all")
    if not packs:
        return {"error": f"未知产业带 {belt_id}", "imported": 0}
    results = [_seed_one_belt_matrix(db, pack) for pack in packs]
    db.commit()
    if len(results) == 1:
        return results[0]
    return {
        "belts_seeded": len(results),
        "results": results,
        "districts_missing": all(r.get("districts_missing") for r in results),
    }


def seed_industry_belt_keywords(
    db: Session,
    *,
    belt_id: str = "all",
    include_ranking: bool = True,
) -> dict[str, Any]:
    """默认导入大城+河间两条产业带词库。"""
    matrix = seed_matrix_keywords(db, belt_id=belt_id)
    ranking = seed_ranking_keywords(db, belt_id=belt_id) if include_ranking else {}
    return {
        "belt_id": belt_id,
        "matrix": matrix,
        "ranking": ranking,
        "message": (
            "大城主材+河间配套词库已入库。"
            "若 districts_missing，请先在「地域管理」维护大城县/河间市后再导入组合词。"
        ),
    }
