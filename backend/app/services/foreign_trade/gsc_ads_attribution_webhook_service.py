# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""GW-P-GSC-02 — Google Search Console / Google Ads 归因 webhook 回环。"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.site_analytics import SiteAnalyticsEvent


def _webhook_secret() -> str:
    """实现 webhook密钥 的功能。
    
    :return: 返回 str 结果
    """
    import os
    try:
        from app.core.config import settings
        return (getattr(settings, "GSC_ADS_WEBHOOK_SECRET", None) or os.getenv("GSC_ADS_WEBHOOK_SECRET") or "").strip()
    except Exception:
        return (os.getenv("GSC_ADS_WEBHOOK_SECRET") or "").strip()


def verify_gsc_ads_signature(payload: bytes, signature: str, secret: str) -> bool:
    """实现 校验gscadssignature 的功能。
    
    :param payload: 参数 payload（类型: bytes）
    :param signature: 参数 signature（类型: str）
    :param secret: 参数 secret（类型: str）
    :return: 返回 bool 结果
    """
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def gsc_ads_webhook_status() -> dict[str, Any]:
    """实现 gscadswebhook状态 的功能。
    
    :return: 返回 dict[str, Any] 结果
    """
    secret = _webhook_secret()
    return {
        "configured": bool(secret),
        "endpoint": "/api/v1/foreign-trade/attribution/gsc-ads-webhook",
        "gw_task": "GW-P-GSC-02",
        "accepted_signals": ["gsc_click", "ads_click", "ads_conversion", "gsc_impression"],
        "honesty_note": "未配置密钥时返回 503；dev 禁止伪造已归因转化",
    }


def ingest_gsc_ads_webhook(
    db: Session,
    *,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """写入 site_analytics_events 并返回 UTM 归一化字段。"""
    signal = str(payload.get("signal") or payload.get("event_type") or "gsc_ads_signal").strip()[:64]
    tenant_id = str(payload.get("tenant_id") or "").strip() or None
    session_id = str(payload.get("session_id") or payload.get("gclid") or payload.get("click_id") or uuid.uuid4().hex)[:64]
    utm = {
        "utm_source": str(payload.get("utm_source") or payload.get("source") or "google")[:120],
        "utm_medium": str(payload.get("utm_medium") or _medium_for_signal(signal))[:120],
        "utm_campaign": str(payload.get("utm_campaign") or payload.get("campaign") or "")[:200],
        "utm_content": str(payload.get("utm_content") or payload.get("ad_group") or "")[:200],
        "utm_term": str(payload.get("utm_term") or payload.get("keyword") or "")[:200],
    }
    utm = {k: v for k, v in utm.items() if v}
    landing = str(payload.get("landing_url") or payload.get("page_url") or "")[:500] or None
    publish_task_id = str(payload.get("publish_task_id") or "").strip() or None
    content_ref = f"publish_task:{publish_task_id}" if publish_task_id else None
    row = SiteAnalyticsEvent(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        session_id=session_id,
        event_type=f"gsc_ads_{signal}"[:64],
        page_path=landing,
        content_ref=content_ref,
        meta_json=json.dumps(
            {
                "gw_task": "GW-P-GSC-02",
                "signal": signal,
                "utm": utm,
                "gclid": payload.get("gclid"),
                "conversion_value": payload.get("conversion_value"),
                "currency": payload.get("currency"),
                "received_at": datetime.now(timezone.utc).isoformat(),
                "raw_keys": sorted(payload.keys()),
            },
            ensure_ascii=False,
        ),
        created_at=datetime.now(timezone.utc),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return {
        "ok": True,
        "event_id": str(row.id),
        "event_type": row.event_type,
        "utm": utm,
        "session_id": session_id,
        "linked_publish_task": publish_task_id,
        "gw_task": "GW-P-GSC-02",
    }


def _medium_for_signal(signal: str) -> str:
    """实现 mediumforsignal 的功能。
    
    :param signal: 参数 signal（类型: str）
    :return: 返回 str 结果
    """
    low = signal.lower()
    if "ads" in low or "conversion" in low:
        return "cpc"
    if "gsc" in low:
        return "organic"
    return "referral"


def gsc_ads_attribution_summary(
    db: Session,
    *,
    tenant_id: str | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    """实现 gscadsattributionsummary 的功能。
    
    :param db: 参数 db（类型: Session）
    :param tenant_id: 参数 tenant_id（类型: str | None）
    :param limit: 参数 limit（类型: int）
    :return: 返回 dict[str, Any] 结果
    """
    q = db.query(SiteAnalyticsEvent).filter(SiteAnalyticsEvent.event_type.like("gsc_ads_%"))
    if tenant_id:
        q = q.filter(SiteAnalyticsEvent.tenant_id == tenant_id)
    rows = q.order_by(SiteAnalyticsEvent.created_at.desc()).limit(max(1, limit)).all()
    by_medium: dict[str, int] = {}
    items: list[dict[str, Any]] = []
    for row in rows:
        meta: dict[str, Any] = {}
        if row.meta_json:
            try:
                meta = json.loads(row.meta_json)
            except (json.JSONDecodeError, TypeError):
                meta = {}
        utm = meta.get("utm") if isinstance(meta.get("utm"), dict) else {}
        medium = str(utm.get("utm_medium") or "unknown")
        by_medium[medium] = by_medium.get(medium, 0) + 1
        items.append(
            {
                "event_id": str(row.id),
                "event_type": row.event_type,
                "session_id": row.session_id,
                "utm": utm,
                "page_path": row.page_path,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
        )

    return {
        "events_total": len(items),
        "by_medium": by_medium,
        "items": items,
        "gw_task": "GW-P-GSC-02",
        "webhook": gsc_ads_webhook_status(),
    }


def validate_webhook_request(
    *,
    body: bytes,
    signature: str | None,
    timestamp: str | None,
) -> tuple[bool, str | None]:
    """实现 校验webhook请求 的功能。
    
    :param body: 参数 body（类型: bytes）
    :param signature: 参数 signature（类型: str | None）
    :param timestamp: 参数 timestamp（类型: str | None）
    :return: 返回 tuple[bool, str | None] 结果
    """
    secret = _webhook_secret()
    if not secret:
        return False, "GSC_ADS_WEBHOOK_NOT_CONFIGURED"
    if not signature:
        return False, "MISSING_SIGNATURE"
    if not verify_gsc_ads_signature(body, signature, secret):
        return False, "INVALID_SIGNATURE"
    if not timestamp:
        return False, "MISSING_TIMESTAMP"
    try:
        ts = int(timestamp)
    except ValueError:
        return False, "INVALID_TIMESTAMP"
    if abs(time.time() - ts) > 300:
        return False, "REQUEST_EXPIRED"
    return True, None
