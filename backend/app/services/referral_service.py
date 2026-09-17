# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""客户裂变推荐系统服务"""

import secrets
import string

from sqlalchemy.orm import Session

from app.models.referral import ReferralCode, ReferralRecord
from app.models.tenant import Tenant


class ReferralService:
    def __init__(self, db: Session):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param db: 参数 db
        :return: 返回处理结果。
        """
        self.db = db

    def _generate_code(self) -> str:
        """生成唯一6位邀请码"""
        chars = string.ascii_uppercase + string.digits
        for _ in range(100):
            code = "".join(secrets.choice(chars) for _ in range(6))
            if not self.db.query(ReferralCode).filter(ReferralCode.code == code).first():
                return code
        return "".join(secrets.choice(chars) for _ in range(8))

    def generate_code(self, tenant_id: str) -> ReferralCode:
        """为租户生成邀请码"""
        existing = self.db.query(ReferralCode).filter(
            ReferralCode.tenant_id == tenant_id,
            ReferralCode.is_active,
        ).first()
        if existing:
            return existing
        code = ReferralCode(
            tenant_id=tenant_id,
            code=self._generate_code(),
        )
        self.db.add(code)
        self.db.commit()
        self.db.refresh(code)
        return code

    def get_referral_stats(self, tenant_id: str) -> dict:
        """获取邀请统计"""
        code = self.db.query(ReferralCode).filter(
            ReferralCode.tenant_id == tenant_id,
            ReferralCode.is_active,
        ).first()
        if not code:
            return {"total_invited": 0, "total_rewarded": 0, "pending_rewards": 0,
                    "current_tier": 0, "next_tier_at": 1, "next_tier_reward": "15%月费折扣",
                    "estimated_discount": 0}

        total_invited = code.total_referred
        rewarded = self.db.query(ReferralRecord).filter(
            ReferralRecord.code_id == code.id,
            ReferralRecord.status == "rewarded",
        ).count()
        tiers = [(1, "15%月费折扣"), (3, "免费1个月"), (5, "套餐免费升级")]
        current_tier = 0
        next_tier_at = 1
        next_reward = tiers[0][1]
        for t, r in tiers:
            if total_invited >= t:
                current_tier = t
        for t, r in tiers:
            if total_invited < t:
                next_tier_at = t
                next_reward = r
                break
        else:
            next_tier_at = total_invited + 1
            next_reward = "联系客服获取专属奖励"

        return {
            "total_invited": total_invited,
            "total_rewarded": rewarded,
            "pending_rewards": total_invited - rewarded,
            "current_tier": current_tier,
            "next_tier_at": next_tier_at,
            "next_tier_reward": next_reward,
            "estimated_discount": total_invited * 15,
        }

    def get_my_records(self, tenant_id: str, page: int = 1, page_size: int = 20) -> tuple:
        """获取邀请记录"""
        code = self.db.query(ReferralCode).filter(
            ReferralCode.tenant_id == tenant_id,
            ReferralCode.is_active,
        ).first()
        if not code:
            return [], 0

        q = self.db.query(ReferralRecord).filter(ReferralRecord.code_id == code.id)
        total = q.count()
        items = q.order_by(ReferralRecord.invited_at.desc()).offset(
            (page - 1) * page_size).limit(page_size).all()

        # 填充邀请方和被邀请方名称
        result = []
        for r in items:
            invited = self.db.query(Tenant).filter(Tenant.id == r.invited_tenant_id).first()
            result.append({
                "id": r.id,
                "invited_name": invited.name if invited else "未知",
                "status": r.status,
                "reward_type": r.reward_type or "",
                "reward_amount": r.reward_amount,
                "invited_at": r.invited_at,
                "rewarded_at": r.rewarded_at,
            })
        return result, total

    def apply_referral(self, code: str, new_tenant_id: str) -> dict:
        """新用户注册时应用邀请码"""
        ref_code = self.db.query(ReferralCode).filter(
            ReferralCode.code == code,
            ReferralCode.is_active,
        ).first()
        if not ref_code:
            return {"success": False, "message": "邀请码无效", "extra_days": 0}

        if ref_code.tenant_id == new_tenant_id:
            return {"success": False, "message": "不能邀请自己", "extra_days": 0}

        record = ReferralRecord(
            code_id=ref_code.id,
            inviter_tenant_id=ref_code.tenant_id,
            invited_tenant_id=new_tenant_id,
            status="pending",
        )
        self.db.add(record)
        ref_code.total_referred += 1
        self.db.commit()
        from app.services.referral_reward_service import process_pending_rewards
        rewards = process_pending_rewards(self.db, ref_code.tenant_id)
        return {
            "success": True,
            "message": "邀请码已应用",
            "extra_days": 16,
            "rewards_granted": rewards,
        }

    def get_leaderboard(self, limit: int = 20) -> list:
        """获取邀请排行榜"""
        rows = (
            self.db.query(
                ReferralCode.tenant_id,
                ReferralCode.total_referred,
                Tenant.name,
            )
            .join(Tenant, ReferralCode.tenant_id == Tenant.id)
            .filter(ReferralCode.is_active, Tenant.is_active)
            .order_by(ReferralCode.total_referred.desc())
            .limit(limit)
            .all()
        )
        return [
            {"rank": i + 1, "company_name": r.name, "invite_count": r.total_referred}
            for i, r in enumerate(rows)
        ]

    def get_my_code(self, tenant_id: str) -> ReferralCode:
        """获取我的邀请码"""
        return self.db.query(ReferralCode).filter(
            ReferralCode.tenant_id == tenant_id,
            ReferralCode.is_active,
        ).first()
