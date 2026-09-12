"""GW-P-TR-01 — UTM 全链路：矩阵 publish_task → 独立域 → 询盘。"""

from __future__ import annotations

import json
from typing import Any, Optional
from urllib.parse import parse_qs, urlparse

from sqlalchemy.orm import Session

from app.models.content import PublishTask
from app.models.inquiry import Inquiry


def parse_utm_from_url(url: str | None) -> dict[str, str]:
    """实现 解析utmfromURL 的功能。
    
    :param url: 参数 url（类型: str | None）
    :return: 返回 dict[str, str] 结果
    """
    if not url:
        return {}
    parsed = urlparse(url.strip())
    qs = parse_qs(parsed.query, keep_blank_values=False)
    out: dict[str, str] = {}
    for key in ("utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term"):
        vals = qs.get(key)
        if vals and vals[0]:
            out[key] = vals[0][:200]
    return out


def serialize_utm(utm: dict[str, str]) -> str:
    """实现 serializeutm 的功能。
    
    :param utm: 参数 utm（类型: dict[str, str]）
    :return: 返回 str 结果
    """
    return json.dumps({k: v for k, v in utm.items() if v}, ensure_ascii=False)


def deserialize_utm(raw: str | None) -> dict[str, str]:
    """实现 deserializeutm 的功能。
    
    :param raw: 参数 raw（类型: str | None）
    :return: 返回 dict[str, str] 结果
    """
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            return {str(k): str(v) for k, v in data.items() if v}
    except (json.JSONDecodeError, TypeError):
        pass
    return {}


def stamp_publish_task_utm(
    task: PublishTask,
    *,
    utm: dict[str, str] | None = None,
    tenant_id: str | None = None,
) -> None:
    """实现 stamp发布任务utm 的功能。
    
    :param task: 参数 task（类型: PublishTask）
    :param utm: 参数 utm（类型: dict[str, str] | None）
    :param tenant_id: 参数 tenant_id（类型: str | None）
    :return: 返回 None 结果
    """
    utm = utm or {}
    if tenant_id:
        task.tenant_id = tenant_id
    if utm.get("utm_source"):
        task.utm_source = utm["utm_source"][:120]
    if utm.get("utm_medium"):
        task.utm_medium = utm["utm_medium"][:120]
    if utm.get("utm_campaign"):
        task.utm_campaign = utm["utm_campaign"][:200]
    if utm.get("utm_content"):
        task.utm_content = utm["utm_content"][:200]


def build_default_publish_utm(
    *,
    platform_name: str,
    campaign: str | None = None,
    content_master_id: str | None = None,
) -> dict[str, str]:
    """实现 构建default发布utm 的功能。
    
    :param platform_name: 参数 platform_name（类型: str）
    :param campaign: 参数 campaign（类型: str | None）
    :param content_master_id: 参数 content_master_id（类型: str | None）
    :return: 返回 dict[str, str] 结果
    """
    slug = (platform_name or "matrix").split("(")[0].strip().lower().replace(" ", "_")[:32]
    return {
        "utm_source": slug or "matrix",
        "utm_medium": "social",
        "utm_campaign": (campaign or "b2b_matrix")[:200],
        "utm_content": (content_master_id or "")[:200] if content_master_id else "",
    }


def resolve_publish_task_for_inquiry(
    db: Session,
    *,
    tenant_id: str | None,
    publish_task_id: str | None = None,
    utm: dict[str, str] | None = None,
    session_id: str | None = None,
) -> PublishTask | None:
    """实现 解析发布任务forinquiry 的功能。
    
    :param db: 参数 db（类型: Session）
    :param tenant_id: 参数 tenant_id（类型: str | None）
    :param publish_task_id: 参数 publish_task_id（类型: str | None）
    :param utm: 参数 utm（类型: dict[str, str] | None）
    :param session_id: 参数 session_id（类型: str | None）
    :return: 返回 PublishTask | None 结果
    """
    if publish_task_id:
        row = db.query(PublishTask).filter(PublishTask.id == publish_task_id).first()
        if row:
            return row

    utm = utm or {}
    campaign = utm.get("utm_campaign")
    if campaign:
        q = db.query(PublishTask).filter(PublishTask.utm_campaign == campaign)
        if tenant_id:
            q = q.filter(PublishTask.tenant_id == tenant_id)
        row = q.order_by(PublishTask.created_at.desc()).first()
        if row:
            return row

    if session_id:
        try:
            from app.models.site_analytics import SiteAnalyticsEvent
            ev = (
                db.query(SiteAnalyticsEvent)
                .filter(
                    SiteAnalyticsEvent.session_id == session_id,
                    SiteAnalyticsEvent.content_ref.isnot(None),
                )
                .order_by(SiteAnalyticsEvent.created_at.desc())
                .first()
            )
            if ev and ev.content_ref:
                ref = str(ev.content_ref)
                if ref.startswith("publish_task:"):
                    tid = ref.split(":", 1)[1]
                    row = db.query(PublishTask).filter(PublishTask.id == tid).first()
                    if row:
                        return row
        except Exception:
            pass
    return None


def attach_utm_to_inquiry(
    db: Session,
    inquiry: Inquiry,
    *,
    landing_path: str | None = None,
    utm: dict[str, str] | None = None,
    publish_task_id: str | None = None,
    session_id: str | None = None,
    tenant_id: str | None = None,
) -> dict[str, Any]:
    """写入 inquiry UTM 并尝试关联 publish_task。"""
    cols = {c.key for c in Inquiry.__table__.columns}
    merged = dict(utm or {})
    if landing_path:
        merged = {**parse_utm_from_url(landing_path), **merged}

    task = resolve_publish_task_for_inquiry(
        db,
        tenant_id=tenant_id or getattr(inquiry, "tenant_id", None),
        publish_task_id=publish_task_id,
        utm=merged,
        session_id=session_id or getattr(inquiry, "session_id", None),
    )
    if task and not merged.get("utm_campaign") and task.utm_campaign:
        merged.setdefault("utm_campaign", task.utm_campaign)
        merged.setdefault("utm_source", task.utm_source or "")
        merged.setdefault("utm_medium", task.utm_medium or "")
        merged.setdefault("utm_content", task.utm_content or "")

    if "source_utm" in cols and merged:
        inquiry.source_utm = serialize_utm(merged)
    if task and "publish_task_id" in cols:
        inquiry.publish_task_id = str(task.id)

    return {
        "utm": merged,
        "publish_task_id": str(task.id) if task else None,
        "linked": task is not None,
    }


def attribution_report(
    db: Session,
    *,
    tenant_id: str | None = None,
    campaign: str | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    """实现 attribution报告 的功能。
    
    :param db: 参数 db（类型: Session）
    :param tenant_id: 参数 tenant_id（类型: str | None）
    :param campaign: 参数 campaign（类型: str | None）
    :param limit: 参数 limit（类型: int）
    :return: 返回 dict[str, Any] 结果
    """
    q = db.query(Inquiry)
    if tenant_id:
        q = q.filter(Inquiry.tenant_id == tenant_id)
    rows = q.order_by(Inquiry.created_at.desc()).limit(max(limit, 1)).all()
    by_campaign: dict[str, dict[str, int]] = {}
    items: list[dict[str, Any]] = []
    for row in rows:
        utm = deserialize_utm(getattr(row, "source_utm", None))
        camp = utm.get("utm_campaign") or "direct"
        if campaign and camp != campaign:
            continue
        bucket = by_campaign.setdefault(camp, {"inquiries": 0, "linked_tasks": 0})
        bucket["inquiries"] += 1
        if getattr(row, "publish_task_id", None):
            bucket["linked_tasks"] += 1
        items.append(
            {
                "inquiry_id": str(row.id),
                "utm": utm,
                "publish_task_id": getattr(row, "publish_task_id", None),
                "source_channel": row.source_channel,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
        )

    task_q = db.query(PublishTask)
    if tenant_id:
        task_q = task_q.filter(PublishTask.tenant_id == tenant_id)
    if campaign:
        task_q = task_q.filter(PublishTask.utm_campaign == campaign)
    publish_tasks = task_q.order_by(PublishTask.created_at.desc()).limit(limit).all()
    gsc_ads: dict[str, Any] = {}
    try:
        from app.services.foreign_trade.gsc_ads_attribution_webhook_service import (
            gsc_ads_attribution_summary,
        )
        gsc_ads = gsc_ads_attribution_summary(db, tenant_id=tenant_id, limit=30)
    except Exception:
        gsc_ads = {"events_total": 0, "gw_task": "GW-P-GSC-02"}

    return {
        "campaign_filter": campaign,
        "tenant_id": tenant_id,
        "inquiries": items,
        "by_campaign": by_campaign,
        "gsc_ads_signals": gsc_ads,
        "publish_tasks": [
            {
                "id": str(t.id),
                "utm_campaign": t.utm_campaign,
                "utm_source": t.utm_source,
                "platform_id": str(t.platform_id),
                "status": t.status,
                "published_url": t.published_url,
            }
            for t in publish_tasks
        ],
    }
