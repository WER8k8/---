# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""产业带 AI 调研 → 产品库候选（须人工勾选导入，默认未上架）。"""

from __future__ import annotations

import json
import re
import uuid
from pathlib import Path
from typing import Any

from pypinyin import lazy_pinyin
from sqlalchemy.orm import Session

from app.models.product import Category, Product
from app.schemas.product import ProductCreate
from app.services.product_service import ProductService

_SURVEY_DIR = Path(__file__).resolve().parents[2] / "data" / "industry_belt_survey_samples"
_DEFAULT_SURVEY = "ai_dacheng_hejian_20260609.json"
_CANDIDATE_CATEGORY = "产业带参考候选"


def _slugify(name: str) -> str:
    """实现 slugify 的功能。
    
    :param name: 参数 name（类型: str）
    :return: 返回 str 结果
    """
    base = "-".join(lazy_pinyin(name))[:80] or "product"
    base = re.sub(r"[^a-z0-9-]", "-", base.lower())
    base = re.sub(r"-+", "-", base).strip("-") or "product"
    return f"{base}-{uuid.uuid4().hex[:6]}"


def load_survey_payload(survey_id: str | None = None) -> dict[str, Any]:
    """实现 加载surveypayload 的功能。
    
    :param survey_id: 参数 survey_id（类型: str | None）
    :return: 返回 dict[str, Any] 结果
    """
    sid = (survey_id or _DEFAULT_SURVEY).replace(".json", "")
    path = _SURVEY_DIR / f"{sid}.json"
    if not path.is_file():
        path = _SURVEY_DIR / _DEFAULT_SURVEY
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _flatten_candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """实现 flattencandidates 的功能。
    
    :param payload: 参数 payload（类型: dict[str, Any]）
    :return: 返回 list[dict[str, Any]] 结果
    """
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for cat in payload.get("categories") or []:
        if not isinstance(cat, dict):
            continue
        cat_id = str(cat.get("category_id") or "")
        cat_name = str(cat.get("category_name_zh") or cat_id)
        for prod in cat.get("products") or []:
            if not isinstance(prod, dict):
                continue
            name = str(prod.get("name") or "").strip()
            if not name or name in seen:
                continue
            seen.add(name)
            key = f"{cat_id}:{name}"
            out.append(
                {
                    "candidate_id": key,
                    "name": name,
                    "category_id": cat_id,
                    "category_name_zh": cat_name,
                    "aliases": prod.get("aliases") or [],
                    "specs_common": prod.get("specs_common") or [],
                    "town_cluster": prod.get("town_cluster") or "",
                    "export_suitable": bool(prod.get("export_suitable")),
                    "notes": prod.get("notes") or "",
                    "evidence": prod.get("evidence") or "",
                    "pm_review_status": (payload.get("pm_review") or {}).get("status") or "pending",
                }
            )
    return out


def list_product_candidates(
    *,
    survey_id: str | None = None,
    category_id: str | None = None,
    search: str | None = None,
    page: int = 1,
    page_size: int = 30,
) -> dict[str, Any]:
    """实现 列出产品candidates 的功能。
    
    :param survey_id: 参数 survey_id（类型: str | None）
    :param category_id: 参数 category_id（类型: str | None）
    :param search: 参数 search（类型: str | None）
    :param page: 参数 page（类型: int）
    :param page_size: 参数 page_size（类型: int）
    :return: 返回 dict[str, Any] 结果
    """
    payload = load_survey_payload(survey_id)
    items = _flatten_candidates(payload)
    if category_id:
        items = [i for i in items if i.get("category_id") == category_id]
    if search:
        q = search.strip().lower()
        items = [
            i
            for i in items
            if q in i.get("name", "").lower()
            or any(q in str(a).lower() for a in (i.get("aliases") or []))
        ]
    total = len(items)
    start = max(0, (page - 1) * page_size)
    page_items = items[start : start + page_size]
    categories = []
    seen_cats: set[str] = set()
    for cat in payload.get("categories") or []:
        if not isinstance(cat, dict):
            continue
        cid = str(cat.get("category_id") or "")
        if cid and cid not in seen_cats:
            seen_cats.add(cid)
            categories.append({"id": cid, "name": cat.get("category_name_zh") or cid})
    pm = payload.get("pm_review") if isinstance(payload.get("pm_review"), dict) else {}
    return {
        "survey_id": payload.get("survey_id") or survey_id,
        "region": payload.get("region_county"),
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": page_items,
        "categories": categories,
        "pm_review_status": pm.get("status") or "pending",
        "honest_note": (
            "以下为 AI 调研候选名，非成交数据；导入后默认未上架，请核对规格后再启用。"
        ),
    }


def _ensure_candidate_category(db: Session) -> Category:
    """实现 确保candidate分类 的功能。
    
    :param db: 参数 db（类型: Session）
    :return: 返回 Category 结果
    """
    row = db.query(Category).filter(Category.name == _CANDIDATE_CATEGORY).first()
    if row:
        return row
    slug = _slugify(_CANDIDATE_CATEGORY)
    row = Category(name=_CANDIDATE_CATEGORY, slug=slug, description="产业带调研候选，导入后须人工核对", is_active=True)
    db.add(row)
    db.flush()
    return row


def import_product_candidates(
    db: Session,
    *,
    candidate_ids: list[str],
    survey_id: str | None = None,
    created_by: str | None = None,
    activate: bool = False,
) -> dict[str, Any]:
    """实现 导入产品candidates 的功能。
    
    :param db: 参数 db（类型: Session）
    :param candidate_ids: 参数 candidate_ids（类型: list[str]）
    :param survey_id: 参数 survey_id（类型: str | None）
    :param created_by: 参数 created_by（类型: str | None）
    :param activate: 参数 activate（类型: bool）
    :return: 返回 dict[str, Any] 结果
    """
    payload = load_survey_payload(survey_id)
    catalog = {c["candidate_id"]: c for c in _flatten_candidates(payload)}
    category = _ensure_candidate_category(db)
    service = ProductService(db)
    imported: list[dict[str, str]] = []
    skipped: list[dict[str, str]] = []
    for cid in candidate_ids:
        item = catalog.get(cid)
        if not item:
            skipped.append({"candidate_id": cid, "reason": "未找到"})
            continue
        name = item["name"]
        exists = db.query(Product).filter(Product.name == name).first()
        if exists:
            skipped.append({"candidate_id": cid, "reason": "产品库已有同名", "product_id": str(exists.id)})
            continue
        specs = "；".join(str(s) for s in (item.get("specs_common") or []) if s)
        desc = (
            f"【产业带候选 · {item.get('pm_review_status')}】\n"
            f"来源调研: {payload.get('survey_id') or survey_id}\n"
            f"品类: {item.get('category_name_zh')}\n"
            f"集群: {item.get('town_cluster') or '—'}\n"
            f"备注: {item.get('notes') or '待实地核对'}\n"
            f"证据: {item.get('evidence') or '—'}"
        )
        try:
            product = service.create_product(
                ProductCreate(
                    category_id=str(category.id),
                    name=name,
                    slug=_slugify(name),
                    subtitle=(item.get("aliases") or [""])[0] if item.get("aliases") else None,
                    description=desc,
                    technical_params=specs or None,
                    application_scenarios=item.get("town_cluster") or None,
                    is_active=bool(activate),
                    sort_order=999,
                ),
                created_by=created_by,
            )
            imported.append({"candidate_id": cid, "product_id": str(product.id), "name": name})
        except ValueError as exc:
            skipped.append({"candidate_id": cid, "reason": str(exc)})

    return {
        "imported_count": len(imported),
        "skipped_count": len(skipped),
        "imported": imported,
        "skipped": skipped,
        "honest_note": "导入项默认未上架（is_active=false），核对后请在产品库启用。",
    }
