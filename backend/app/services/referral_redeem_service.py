# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""现金券线下核销 — 超管确认已兑付。"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.referral import ReferralRecord
from app.models.tenant import Tenant
from app.models.user import User


def _require_admin(user: User) -> str | None:
    """_require_admin。

    参数说明：
    :param user: 参数 user
    :return: 返回处理结果。
    """
    if user.role not in ("admin", "super_admin"):
        return "仅超管可核销现金券"
    return None


def list_pending_cash_coupons(db: Session, *, limit: int = 100) -> list[dict[str, Any]]:
    """list_pending_cash_coupons。

    参数说明：
    :param db: 参数 db
    :param limit: 参数 limit
    :return: 返回处理结果。
    """
    rows = (
        db.query(ReferralRecord)
        .filter(
            ReferralRecord.reward_type == "cash_coupon",
            ReferralRecord.status == "rewarded",
            ReferralRecord.redemption_status == "pending_redemption",
        )
        .order_by(ReferralRecord.rewarded_at.desc())
        .limit(limit)
        .all()
    )
    out: list[dict[str, Any]] = []
    # 批量加载tenant
    tenant_ids = {r.inviter_tenant_id for r in rows if r.inviter_tenant_id} | {r.invited_tenant_id for r in rows if r.invited_tenant_id}
    tenant_map = {str(t.id): t for t in db.query(Tenant).filter(Tenant.id.in_(tenant_ids)).all()}
    for r in rows:
        inviter = tenant_map.get(str(r.inviter_tenant_id))
        invited = tenant_map.get(str(r.invited_tenant_id))
        out.append(
            {
                "id": r.id,
                "inviter_name": inviter.name if inviter else "未知",
                "invited_name": invited.name if invited else "未知",
                "reward_amount": r.reward_amount,
                "rewarded_at": r.rewarded_at,
                "invited_at": r.invited_at,
            }
        )
    return out


def redeem_cash_coupon(
    db: Session,
    *,
    record_id: str,
    admin_user: User,
    note: str = "",
) -> tuple[bool, str, dict[str, Any] | None]:
    """redeem_cash_coupon。

    参数说明：
    :param db: 参数 db
    :param record_id: 参数 record_id
    :param admin_user: 参数 admin_user
    :param note: 参数 note
    :return: 返回处理结果。
    """
    err = _require_admin(admin_user)
    if err:
        return False, err, None
    record = db.query(ReferralRecord).filter(ReferralRecord.id == record_id).first()
    if not record:
        return False, "记录不存在", None
    if record.reward_type != "cash_coupon":
        return False, "非现金券奖励", None
    if record.redemption_status == "redeemed":
        return False, "已核销", None
    if record.redemption_status != "pending_redemption":
        return False, "当前状态不可核销", None
    record.redemption_status = "redeemed"
    record.redeemed_at = datetime.now(timezone.utc)
    record.redeem_note = (note or "").strip()[:500] or None
    db.commit()
    return True, "核销成功", {
        "id": record.id,
        "redemption_status": record.redemption_status,
        "redeemed_at": record.redeemed_at,
    }
