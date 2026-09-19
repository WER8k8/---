# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""AccioWork 39+ 技能包对标目录（本系统实现状态）。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.services.ubrain.accio_gap_constants import GAP_MVP_SKILL_IDS

_CATALOG_PATH = Path(__file__).resolve().parents[2] / "data" / "accio_skill_catalog.json"


_EMPTY_CATALOG: dict[str, Any] = {
    "catalog_version": "missing",
    "groups": [],
}


def load_skill_catalog() -> dict[str, Any]:
    """load_skill_catalog。
    :return: 返回处理结果。
    """
    if not _CATALOG_PATH.is_file():
        # 缺文件时诚实返回空目录，禁止 500（假交付红线）
        return dict(_EMPTY_CATALOG)
    with open(_CATALOG_PATH, encoding="utf-8") as f:
        return json.load(f)


def iter_skills() -> list[tuple[dict[str, Any], dict[str, Any]]]:
    """(group, skill) 扁平迭代。"""
    data = load_skill_catalog()
    pairs: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for group in data.get("groups", []):
        for sk in group.get("skills", []):
            pairs.append((group, sk))
    return pairs


def get_skill(skill_id: str) -> dict[str, Any] | None:
    """get_skill。

    参数说明：
    :param skill_id: 参数 skill_id
    :return: 返回处理结果。
    """
    for group, sk in iter_skills():
        if sk.get("id") == skill_id:
            return {
                **sk,
                "group_id": group.get("id"),
                "group_name": group.get("name"),
            }
    return None


def list_gap_skills() -> list[dict[str, Any]]:
    """Accio 对标目录中尚未完整实现的技能（implemented=partial）。"""
    gaps: list[dict[str, Any]] = []
    for group, sk in iter_skills():
        impl = sk.get("implemented")
        if impl is True:
            continue
        if impl != "partial":
            continue
        gaps.append(
            {
                "id": sk.get("id"),
                "accio_analog": sk.get("accio_analog"),
                "implemented": impl,
                "gap": sk.get("gap"),
                "api": sk.get("api"),
                "group_id": group.get("id"),
                "group_name": group.get("name"),
            }
        )
    return gaps


def list_partial_mvp_skills() -> list[dict[str, Any]]:
    """catalog 中 implemented=partial 的技能。"""
    items: list[dict[str, Any]] = []
    for group, sk in iter_skills():
        if sk.get("implemented") != "partial":
            continue
        sid = sk.get("id")
        items.append(
            {
                "id": sid,
                "accio_analog": sk.get("accio_analog"),
                "implemented": sk.get("implemented"),
                "gap": sk.get("gap"),
                "api": sk.get("api"),
                "group_id": group.get("id"),
                "group_name": group.get("name"),
                "mvp": sid in GAP_MVP_SKILL_IDS,
            }
        )
    return items


def catalog_summary() -> dict[str, Any]:
    """catalog_summary。
    :return: 返回处理结果。
    """
    data = load_skill_catalog()
    total = 0
    implemented = 0
    partial = 0
    for group in data.get("groups", []):
        for sk in group.get("skills", []):
            total += 1
            st = sk.get("implemented")
            if st is True:
                implemented += 1
            elif st == "partial":
                partial += 1
    return {
        "total_skills": total,
        "implemented": implemented,
        "partial": partial,
        "not_implemented": total - implemented - partial,
        "coverage_pct": round((implemented + partial * 0.5) / max(total, 1) * 100, 1),
    }
