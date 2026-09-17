# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""潜客数据清洗 — 改编自 EricHong123/Eric_Frank DataCleanerSkill（核心逻辑，无 pandas）。"""

from __future__ import annotations

import re
from typing import Any


def _norm_email(v: str | None) -> str:
    """实现 norm邮件 的功能。
    
    :param v: 参数 v（类型: str | None）
    :return: 返回 str 结果
    """
    return (v or "").strip().lower()


def _norm_phone(v: str | None) -> str:
    """实现 norm电话 的功能。
    
    :param v: 参数 v（类型: str | None）
    :return: 返回 str 结果
    """
    if not v:
        return ""
    digits = re.sub(r"\D", "", v)
    return digits[-11:] if len(digits) >= 7 else digits


def clean_prospect_records(
    customers: list[dict[str, Any]],
    *,
    existing: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """去重、标准化、打标签（客户类型/意向/国家）。"""
    existing = existing or []
    seen_emails = {_norm_email(c.get("email")) for c in existing if c.get("email")}
    seen_phones = {_norm_phone(c.get("phone")) for c in existing if c.get("phone")}
    cleaned: list[dict[str, Any]] = []
    dup_removed = 0
    invalid_removed = 0
    for raw in customers:
        row = dict(raw)
        email = _norm_email(row.get("email"))
        phone = _norm_phone(row.get("phone"))
        if not email and not phone:
            invalid_removed += 1
            continue
        if email and email in seen_emails:
            dup_removed += 1
            continue
        if phone and phone in seen_phones:
            dup_removed += 1
            continue

        row["email"] = email or row.get("email")
        row["phone"] = phone or row.get("phone")
        row["tags"] = _auto_tags(row)
        row["intent_level"] = _intent_level(row)
        cleaned.append(row)
        if email:
            seen_emails.add(email)
        if phone:
            seen_phones.add(phone)

    return {
        "cleaned_customers": cleaned,
        "stats": {
            "total_in": len(customers),
            "total_out": len(cleaned),
            "duplicates_removed": dup_removed,
            "invalid_removed": invalid_removed,
        },
        "source": "Eric_Frank/data_cleaner (adapted)",
    }


def _auto_tags(row: dict[str, Any]) -> list[str]:
    """实现 autotags 的功能。
    
    :param row: 参数 row（类型: dict[str, Any]）
    :return: 返回 list[str] 结果
    """
    text = " ".join(str(row.get(k) or "") for k in ("category", "bio", "notes", "platform", "title"))
    tags: list[str] = []
    lower = text.lower()
    if any(k in lower for k in ("brand", "品牌")):
        tags.append("brand")
    if any(k in lower for k in ("wholesale", "批发", "distributor")):
        tags.append("wholesaler")
    if any(k in lower for k in ("mcn", "influencer", "达人")):
        tags.append("influencer")
    if row.get("website"):
        tags.append("has_website")
    return tags or ["prospect"]


def _intent_level(row: dict[str, Any]) -> str:
    """实现 intent级别 的功能。
    
    :param row: 参数 row（类型: dict[str, Any]）
    :return: 返回 str 结果
    """
    text = (row.get("notes") or row.get("message") or "").lower()
    if re.search(r"(urgent|asap|quote|rfq|采购|报价)", text):
        return "high"
    if row.get("email") and row.get("phone"):
        return "medium"
    return "low"
