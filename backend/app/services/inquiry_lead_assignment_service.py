# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""平台落地页线索 — 自动分配销售 + 飞书通知。"""

from __future__ import annotations

import logging
import os
from typing import Any, Optional

import httpx
from fastapi import Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.inquiry import Inquiry
from app.models.user import User

logger = logging.getLogger(__name__)

PLATFORM_LANDING_CHANNEL = "platform_landing"
_ASSIGNABLE_ROLES = ("sales", "admin", "super_admin")


def _assignee_pool(db: Session) -> list[str]:
    """_assignee_pool。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    env_ids = (os.getenv("PLATFORM_LEAD_ASSIGNEE_IDS") or "").strip()
    if env_ids:
        return [x.strip() for x in env_ids.split(",") if x.strip()]
    rows = (
        db.query(User)
        .filter(User.is_active.is_(True), User.role.in_(_ASSIGNABLE_ROLES))
        .order_by(User.created_at.asc())
        .all()
    )
    return [str(u.id) for u in rows]


def pick_assignee(db: Session, *, source_channel: str) -> Optional[str]:
    """按渠道规则选取负责人（platform_landing 走最少负载轮询）。"""
    if source_channel != PLATFORM_LANDING_CHANNEL:
        return None
    pool = _assignee_pool(db)
    if not pool:
        return None
    cols = {c.key for c in Inquiry.__table__.columns}
    if "assigned_to" not in cols:
        return pool[0]

    counts: dict[str, float] = {uid: 0.0 for uid in pool}
    rows = (
        db.query(Inquiry.assigned_to, Inquiry.priority_score)
        .filter(
            Inquiry.source_channel == PLATFORM_LANDING_CHANNEL,
            Inquiry.assigned_to.in_(pool),
        )
        .all()
    )
    # P0-8: 加权负载 —— 高价值线索权重更高，避免资深销售被均摊成「只接普通线索」
    for (uid, ps) in rows:
        if uid and str(uid) in counts:
            weight = 1.0 + (float(ps or 0) / 100.0)
            counts[str(uid)] += weight
    return min(pool, key=lambda uid: (counts.get(uid, 0.0), uid))


def assign_inquiry(
    db: Session,
    inquiry: Inquiry,
    assignee_id: str,
    *,
    notify: bool = True,
    actor_user_id: Optional[str] = None,
    mode: str = "manual",
    request: Optional[Request] = None,
) -> dict[str, Any]:
    """assign_inquiry。

    参数说明：
    :param db: 参数 db
    :param inquiry: 参数 inquiry
    :param assignee_id: 参数 assignee_id
    :param notify: 参数 notify
    :param actor_user_id: 参数 actor_user_id
    :param mode: 参数 mode
    :param request: 参数 request
    :return: 返回处理结果。
    """
    cols = {c.key for c in Inquiry.__table__.columns}
    if "assigned_to" not in cols:
        raise ValueError("inquiries 表缺少 assigned_to 列，请执行数据库迁移")
    from_assignee = getattr(inquiry, "assigned_to", None)
    if from_assignee and str(from_assignee) == str(assignee_id):
        user = db.query(User).filter(User.id == assignee_id).first()
        return {
            "assigned_to": str(assignee_id),
            "assigned_to_name": user.username if user else assignee_id,
            "skipped": True,
        }
    user = (
        db.query(User)
        .filter(User.id == assignee_id, User.is_active.is_(True))
        .first()
    )
    if not user:
        raise ValueError("负责人不存在")
    inquiry.assigned_to = str(user.id)
    db.commit()
    db.refresh(inquiry)
    try:
        from app.services.inquiry_assignment_audit_service import log_inquiry_assignment
        log_inquiry_assignment(
            db,
            inquiry_id=str(inquiry.id),
            from_assignee_id=str(from_assignee) if from_assignee else None,
            to_assignee_id=str(user.id),
            mode="auto" if mode == "auto" else "manual",
            actor_user_id=actor_user_id,
            inquiry_name=getattr(inquiry, "name", None),
            source_channel=getattr(inquiry, "source_channel", None),
            request=request,
        )
    except Exception as exc:
        logger.warning("inquiry assign audit failed: %s", exc)

    result: dict[str, Any] = {
        "assigned_to": str(user.id),
        "assigned_to_name": user.username,
    }
    if notify:
        result["feishu"] = _notify_feishu(inquiry, user.username)
    return result


def auto_assign_platform_lead(db: Session, inquiry: Inquiry) -> dict[str, Any]:
    """公开询盘创建后：platform_landing 自动分配并通知。"""
    channel = getattr(inquiry, "source_channel", None) or ""
    # P0-8: 先算线索价值评分并回写，供分配加权 + 销售队列排序
    cols = {c.key for c in Inquiry.__table__.columns}
    if "priority_score" in cols:
        try:
            from app.services.lead_priority_service import compute_inquiry_priority
            inquiry.priority_score = compute_inquiry_priority(db, inquiry)
            db.commit()
        except Exception as _prio_err:
            logger.warning("compute inquiry priority failed: %s", _prio_err)
    assignee_id = pick_assignee(db, source_channel=channel)
    if not assignee_id:
        return {"assigned": False, "reason": "no_assignee_pool"}
    cols = {c.key for c in Inquiry.__table__.columns}
    if "assigned_to" not in cols:
        return {"assigned": False, "reason": "column_missing"}
    try:
        meta = assign_inquiry(
            db,
            inquiry,
            assignee_id,
            notify=True,
            mode="auto",
        )
        return {"assigned": True, **meta}
    except Exception as exc:
        logger.warning("platform lead auto-assign failed: %s", exc)
        return {"assigned": False, "reason": str(exc)}


def list_assignee_candidates(db: Session) -> list[dict[str, str]]:
    """list_assignee_candidates。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    ids = _assignee_pool(db)
    if not ids:
        return []
    users = db.query(User).filter(User.id.in_(ids)).all()
    by_id = {str(u.id): u for u in users}
    return [
        {"id": uid, "username": by_id[uid].username, "role": by_id[uid].role}
        for uid in ids
        if uid in by_id
    ]


def _notify_feishu(inquiry: Inquiry, assignee_name: str) -> bool:
    """_notify_feishu。

    参数说明：
    :param inquiry: 参数 inquiry
    :param assignee_name: 参数 assignee_name
    :return: 返回处理结果。
    """
    webhook = (settings.FEISHU_WEBHOOK_URL or "").strip()
    if not webhook:
        return False
    name = getattr(inquiry, "name", "") or "未知"
    phone = getattr(inquiry, "phone", "") or "—"
    company = getattr(inquiry, "product", "") or "—"
    message = (getattr(inquiry, "message", "") or "")[:500]
    md = (
        f"**负责人**：{assignee_name}\n"
        f"**联系人**：{name} · {phone}\n"
        f"**公司**：{company}\n"
        f"**需求**：{message}\n"
        f"**来源**：{getattr(inquiry, 'source_channel', '') or '—'}"
    )
    payload = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": "新平台落地页线索"},
                "template": "blue",
            },
            "elements": [{"tag": "div", "text": {"tag": "lark_md", "content": md}}],
        },
    }
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.post(webhook, json=payload)
            return resp.is_success
    except Exception as exc:
        logger.warning("feishu lead notify failed: %s", exc)
        return False
