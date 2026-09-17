# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""P1-06：裂变奖励类型（Token / 现金券 / 免费月 / 套餐升级）。"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.referral import ReferralCode, ReferralRecord

TIER_REWARDS: list[tuple[int, str, str, int]] = [
    (1, "token", "邀请 1 人 · Token 额度", 5000),
    (3, "free_month", "邀请 3 人 · 免费 1 个月", 1),
    (5, "cash_coupon", "邀请 5 人 · 现金券", 10000),
    (10, "package_upgrade", "邀请 10 人 · 套餐升级券", 1),
]


def reward_for_invite_count(count: int) -> tuple[str, str, int] | None:
    """reward_for_invite_count。

    参数说明：
    :param count: 参数 count
    :return: 返回处理结果。
    """
    matched = None
    for threshold, rtype, label, amount in TIER_REWARDS:
        if count >= threshold:
            matched = (rtype, label, amount)
    return matched


def reward_at_position(invite_index: int) -> tuple[str, str, int]:
    """reward_at_position。

    参数说明：
    :param invite_index: 参数 invite_index
    :return: 返回处理结果。
    """
    for threshold, rtype, label, amount in TIER_REWARDS:
        if invite_index == threshold:
            return rtype, label, amount
    return "token", "邀请成功奖励", 1000


def process_pending_rewards(db: Session, tenant_id: str) -> list[dict]:
    """将 pending 邀请记录发放奖励（含 cash_coupon / 非 Token 类型）。"""
    code = (
        db.query(ReferralCode)
        .filter(ReferralCode.tenant_id == tenant_id, ReferralCode.is_active)
        .first()
    )
    if not code:
        return []
    granted: list[dict] = []
    rewarded_count = (
        db.query(ReferralRecord)
        .filter(ReferralRecord.code_id == code.id, ReferralRecord.status == "rewarded")
        .count()
    )
    pending = (
        db.query(ReferralRecord)
        .filter(
            ReferralRecord.code_id == code.id,
            ReferralRecord.status == "pending",
        )
        .order_by(ReferralRecord.invited_at)
        .all()
    )
    for offset, record in enumerate(pending):
        invite_index = rewarded_count + offset + 1
        rtype, label, amount = reward_at_position(invite_index)
        record.status = "rewarded"
        record.reward_type = rtype
        record.reward_amount = amount
        record.rewarded_at = datetime.now(timezone.utc)
        if rtype == "cash_coupon":
            record.redemption_status = "pending_redemption"
        granted.append(
            {
                "record_id": record.id,
                "reward_type": rtype,
                "reward_label": label,
                "reward_amount": amount,
                "invite_index": invite_index,
            }
        )
    if granted:
        db.commit()
    return granted
