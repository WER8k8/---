# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""开户首篇 — SEO 引用种子 + GeneratedContent + PublishTask 真入队。"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.content import GeneratedContent, PlatformAccount, PublishTask
from app.models.region import City, District, GeneratedKeyword, IndustryKeyword, Province
from app.models.tenant import Tenant
from app.services.trade_intel_data import load_country_index


def _market_label(top_market: dict[str, Any] | None) -> str | None:
    """_market_label。

    参数说明：
    :param top_market: 参数 top_market
    :return: 返回处理结果。
    """
    if not top_market:
        return None
    label = str(top_market.get("country_label") or "").strip()
    if label:
        return label
    code = str(top_market.get("country_code") or "").upper()
    if code:
        return load_country_index().get(code, {}).get("name_zh") or code
    return None

_ONBOARDING_PROVINCE_CODE = "ONBOARDING-EXP"
_ONBOARDING_CITY_CODE = "ONBOARDING-EXP-CITY"
_ONBOARDING_DISTRICT_CODE = "ONBOARDING-EXP-DIST"


def _utcnow() -> datetime:
    """_utcnow。
    :return: 返回处理结果。
    """
    return datetime.now(timezone.utc)


def ensure_onboarding_seo_refs(db: Session, product: str) -> tuple[str, str]:
    """确保 GeneratedContent 所需的 district_id + keyword_id 存在。"""
    product = (product or "export product").strip()[:200]
    province = db.query(Province).filter_by(code=_ONBOARDING_PROVINCE_CODE).first()
    if not province:
        province = Province(
            id=str(uuid.uuid4()),
            code=_ONBOARDING_PROVINCE_CODE,
            name="出口示范省",
            name_en="Export Demo Province",
            is_active=True,
        )
        db.add(province)
        db.flush()

    city = db.query(City).filter_by(code=_ONBOARDING_CITY_CODE).first()
    if not city:
        city = City(
            id=str(uuid.uuid4()),
            code=_ONBOARDING_CITY_CODE,
            name="出口示范市",
            name_en="Export Demo City",
            province_id=province.id,
            is_active=True,
        )
        db.add(city)
        db.flush()

    district = db.query(District).filter_by(code=_ONBOARDING_DISTRICT_CODE).first()
    if not district:
        district = District(
            id=str(uuid.uuid4()),
            code=_ONBOARDING_DISTRICT_CODE,
            name="出口示范区",
            name_en="Export Demo District",
            city_id=city.id,
            province_id=province.id,
            is_active=True,
        )
        db.add(district)
        db.flush()

    ik = (
        db.query(IndustryKeyword)
        .filter_by(keyword=product, is_active=True)
        .first()
    )
    if not ik:
        ik = IndustryKeyword(
            id=str(uuid.uuid4()),
            keyword=product,
            keyword_type="product",
            search_volume=0,
            difficulty=0.0,
            category="onboarding",
            is_active=True,
        )
        db.add(ik)
        db.flush()

    gk_text = f"{district.name}{product}出口"
    gk = db.query(GeneratedKeyword).filter_by(keyword=gk_text).first()
    if not gk:
        gk = GeneratedKeyword(
            id=str(uuid.uuid4()),
            keyword=gk_text,
            district_id=district.id,
            industry_keyword_id=ik.id,
            is_valid=True,
        )
        db.add(gk)
        db.flush()

    return str(district.id), str(gk.id)


def create_onboarding_first_publish(
    db: Session,
    tenant: Tenant,
    *,
    title: str,
    body: str,
    product: str,
    top_market: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """创建 GeneratedContent + PublishTask（pending）。"""
    tid = str(tenant.id)
    district_id, keyword_id = ensure_onboarding_seo_refs(db, product)
    if top_market and _market_label(top_market):
        label = _market_label(top_market)
        body = (
            f"{body.rstrip()}\n\n"
            f"Suggested pilot market: {label}"
            f" ({top_market.get('growth') or ''}) — {top_market.get('reason') or ''}"
        )

    gc = GeneratedContent(
        id=str(uuid.uuid4()),
        title=title,
        content=body,
        district_id=district_id,
        keyword_id=keyword_id,
        word_count=len(body),
        status="draft",
    )
    db.add(gc)
    db.flush()
    task_id: str | None = None
    platform_name: str | None = None
    account = (
        db.query(PlatformAccount)
        .filter(
            PlatformAccount.tenant_id == tid,
            PlatformAccount.is_active.is_(True),
        )
        .order_by(PlatformAccount.created_at.asc())
        .first()
    )
    if account:
        task = PublishTask(
            id=str(uuid.uuid4()),
            content_id=gc.id,
            platform_id=account.platform_id,
            account_id=account.id,
            publish_type="immediate",
            status="pending",
            region=getattr(account, "region", None) or "cn",
        )
        db.add(task)
        db.flush()
        task_id = str(task.id)
        platform_name = account.account_name

    return {
        "content_id": str(gc.id),
        "task_id": task_id,
        "platform_account": platform_name,
        "title": title,
        "preview": body[:280],
        "queued": bool(task_id),
    }


def queue_publish_for_content(
    db: Session,
    tenant: Tenant,
    *,
    content_id: str,
) -> dict[str, Any]:
    """平台绑定后补建 PublishTask。"""
    tid = str(tenant.id)
    gc = db.query(GeneratedContent).filter(GeneratedContent.id == content_id).first()
    if not gc:
        return {"task_id": None, "error": "content_not_found"}

    existing = (
        db.query(PublishTask)
        .filter(PublishTask.content_id == content_id)
        .first()
    )
    if existing:
        return {"task_id": str(existing.id), "already_queued": True}

    account = (
        db.query(PlatformAccount)
        .filter(
            PlatformAccount.tenant_id == tid,
            PlatformAccount.is_active.is_(True),
        )
        .order_by(PlatformAccount.created_at.asc())
        .first()
    )
    if not account:
        return {"task_id": None, "error": "no_platform_account"}

    task = PublishTask(
        id=str(uuid.uuid4()),
        content_id=gc.id,
        platform_id=account.platform_id,
        account_id=account.id,
        publish_type="immediate",
        status="pending",
        region=getattr(account, "region", None) or "cn",
    )
    db.add(task)
    db.flush()
    return {"task_id": str(task.id), "platform_account": account.account_name}
