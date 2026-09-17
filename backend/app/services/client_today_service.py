# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Client / 出海计 App — 今日一件事 + 出海参谋蓝海 Top1。"""

from __future__ import annotations

import json
from typing import Any, TYPE_CHECKING

from app.services.journey_health_service import build_journey_health
from app.services.tenant_product_context import resolve_tenant_product_hint
from app.services.trade_intel_data import load_category_aliases, load_country_index
from app.services.trade_intel_service import DISCLAIMER, _resolve_category, blue_ocean

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from app.models.tenant import Tenant


def _tenant_settings(tenant: Tenant) -> dict[str, Any]:
    """_tenant_settings。

    参数说明：
    :param tenant: 参数 tenant
    :return: 返回处理结果。
    """
    raw = tenant.settings
    if not raw:
        return {}
    try:
        data = json.loads(raw) if isinstance(raw, str) else raw
    except (json.JSONDecodeError, TypeError):
        return {}
    return data if isinstance(data, dict) else {}


def resolve_tenant_category_key(*, product_hint: str | None, message: str = "") -> str:
    """resolve_tenant_category_key。

    参数说明：
    :param product_hint: 参数 product_hint
    :param message: 参数 message
    :return: 返回处理结果。
    """
    text = f"{message} {product_hint or ''}".strip()
    key = _resolve_category(text)
    if key:
        return key
    hint = (product_hint or "").strip()
    if hint:
        for alias, cat in load_category_aliases().items():
            if alias in hint:
                return cat
    return "insulation_board"


def build_blue_ocean_hint(
    *,
    db: Session,
    category_key: str,
    product_hint: str | None,
) -> dict[str, Any]:
    """build_blue_ocean_hint。

    参数说明：
    :param db: 参数 db
    :param category_key: 参数 category_key
    :param product_hint: 参数 product_hint
    :return: 返回处理结果。
    """
    msg = f"{product_hint or '建材'}蓝海市场"
    insight = blue_ocean(msg, category=category_key, db=db)
    top = (insight.get("recommendations") or [{}])[0]
    code = str(top.get("country_code") or "").upper()
    country_idx = load_country_index()
    return {
        "country_code": code,
        "country_label": country_idx.get(code, {}).get("name_zh") or code,
        "category": insight.get("category"),
        "category_key": category_key,
        "reason": (top.get("reason") or "")[:120],
        "growth": top.get("growth"),
        "verdict": top.get("verdict"),
        "disclaimer": insight.get("disclaimer") or DISCLAIMER,
        "sources": insight.get("sources") or [],
    }


def build_today_payload(
    *,
    db: Session,
    tenant: Tenant,
    pending_inquiries: int,
    publish_in_progress: int = 0,
) -> dict[str, Any]:
    """build_today_payload。

    参数说明：
    :param db: 参数 db
    :param tenant: 参数 tenant
    :param pending_inquiries: 参数 pending_inquiries
    :param publish_in_progress: 参数 publish_in_progress
    :return: 返回处理结果。
    """
    product_hint = resolve_tenant_product_hint(tenant)
    category_key = resolve_tenant_category_key(product_hint=product_hint)
    blue = build_blue_ocean_hint(db=db, category_key=category_key, product_hint=product_hint)
    journey_health = build_journey_health(db, tenant)
    sales_gaps = journey_health.get("sales_channel_gaps") or []
    next_action = journey_health.get("next_action")
    critical_pct = int(journey_health.get("score_pct") or 0)
    queue: list[dict[str, str]] = []
    if pending_inquiries > 0:
        queue.append(
            {
                "id": "inquiry",
                "label": f"回复 {pending_inquiries} 条待办询盘",
                "priority": "high",
            }
        )
        today_one = f"您有 {pending_inquiries} 条待回复询盘，建议优先回复"
    elif sales_gaps:
        gap = sales_gaps[0]
        title = gap.get("title") or "销售通知"
        today_one = f"今日一件事：完成「{title}」— 留言可能已进系统，销售手机还需单独配置"
        queue.append(
            {
                "id": "sales_channel",
                "label": f"开户主链 · {title}",
                "priority": "high",
            }
        )
    elif critical_pct < 100 and next_action:
        title = next_action.get("title") or "继续开户"
        today_one = f"今日一件事：{title}"
        queue.append(
            {
                "id": "onboarding",
                "label": title,
                "priority": "high",
            }
        )
    else:
        country = blue.get("country_label") or blue.get("country_code") or ""
        cat = blue.get("category") or "主力品类"
        reason = str(blue.get("reason") or "").strip()
        today_one = f"今日一件事：聚焦 {country} 蓝海（{cat}）"
        if reason:
            today_one += f" — {reason[:60]}"
        queue.append(
            {
                "id": "blue_ocean",
                "label": f"出海参谋 · {country} 蓝海机会（{cat}）",
                "priority": "normal",
            }
        )

    if publish_in_progress > 0:
        queue.append(
            {
                "id": "publish",
                "label": f"跟进 {publish_in_progress} 批待发/发布中",
                "priority": "high",
            }
        )
    else:
        queue.append(
            {
                "id": "publish",
                "label": "选母版发一批产品到多平台",
                "priority": "normal",
            }
        )

    return {
        "today_one_thing": today_one,
        "today_queue": queue,
        "blue_ocean_hint": blue,
        "product_hint": product_hint,
        "journey_health": {
            "score_pct": journey_health.get("score_pct"),
            "checklist_done": journey_health.get("checklist_done"),
            "checklist_total": journey_health.get("checklist_total"),
            "critical_done": journey_health.get("critical_done"),
            "critical_total": journey_health.get("critical_total"),
            "sales_channel_gaps": sales_gaps,
            "next_action": next_action,
            "role_insights": journey_health.get("role_insights") or [],
            "data_notes": journey_health.get("data_notes") or {},
        },
    }
