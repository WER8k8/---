"""新询盘 → Push 通知商家（APP-1b 生产链路）。"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session

from app.models.inquiry import Inquiry
from app.models.tenant import UserTenant
from app.models.user import User
from app.services.push_notification_service import notify_inquiry_pending

logger = logging.getLogger(__name__)


def _merchant_user_ids(db: Session, inquiry: Inquiry) -> list[str]:
    """_merchant_user_ids。

    参数说明：
    :param db: 参数 db
    :param inquiry: 参数 inquiry
    :return: 返回处理结果。
    """
    mids: list[str] = []
    if hasattr(inquiry, "merchant_id") and inquiry.merchant_id:
        mids.append(str(inquiry.merchant_id))
    tenant_links = db.query(UserTenant).filter(UserTenant.is_active).limit(200).all()
    for link in tenant_links:
        uid = str(link.user_id)
        if uid not in mids:
            user = db.query(User).filter(User.id == link.user_id, User.is_active).first()
            if user and user.role in ("tenant_admin", "admin", "super_admin", "merchant"):
                mids.append(uid)
    return mids[:10]


def notify_new_public_inquiry(db: Session, inquiry: Inquiry) -> dict[str, Any]:
    """公开询盘创建后通知相关用户设备。"""
    user_ids = _merchant_user_ids(db, inquiry)
    if not user_ids:
        return {"notified": 0, "reason": "no_merchant_users"}

    q = db.query(Inquiry).filter(Inquiry.status == "pending")
    if hasattr(Inquiry, "is_active"):
        q = q.filter(Inquiry.is_active.is_(True))
    pending = q.count()
    results = []
    for uid in user_ids:
        try:
            r = notify_inquiry_pending(db, uid, max(pending, 1))
            results.append({"user_id": uid, **r})
        except Exception as exc:
            logger.warning("inquiry push failed user=%s: %s", uid, exc)
    sent = sum(1 for r in results if (r.get("sent") or 0) > 0)
    wecom_result: dict[str, Any] = {"skipped": True}
    try:
        from app.services.sales_push_service import notify_inquiry_wecom
        wecom_result = notify_inquiry_wecom(db, inquiry)
    except Exception as exc:
        logger.warning("wecom inquiry push failed: %s", exc)
        wecom_result = {"sent": False, "error": str(exc)}

    return {
        "notified": sent,
        "users": len(user_ids),
        "results": results[:5],
        "wecom": wecom_result,
    }
