# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""客户裂变推荐系统服务"""

import logging
import secrets
import string

from sqlalchemy.orm import Session

from app.models.referral import REFERRAL_TRANSITIONS, ReferralCode, ReferralRecord
from app.models.tenant import Tenant

logger = logging.getLogger(__name__)

# 轨6 计量键（幂等）：同一邀请记录只计一次收入确认；冲回另起 :reversal 行（append-only）
REF_EVENT_KEY_REWARDED = "referral:{id}:rewarded"
REF_EVENT_KEY_REVERSAL = "referral:{id}:rewarded:reversal"


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
            return {
                "total_invited": 0,
                "total_rewarded": 0,
                "pending_rewards": 0,
                "current_tier": 0,
                "next_tier_at": 1,
                "next_tier_reward": "15%月费折扣",
                "estimated_discount": 0,
                "qualification_rule": "first_paid",
                "leaderboard_metric": "registration_invites",
            }

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
            # 诚实口径：折扣估算按注册邀请；有效邀请以 first_paid rewarded 为准
            "estimated_discount": total_invited * 15,
            "estimated_discount_basis": "registration_invites",
            "qualification_rule": "first_paid",
            "leaderboard_metric": "registration_invites",
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

    def mark_invite_qualified(self, invited_tenant_id: str, *, reason: str = "first_paid") -> dict:
        """支付成功后：将该租户的 pending 邀请标为有效（幂等）。

        规则：qualification_rule=first_paid — 仅首次有效付费；已 rewarded 不重复。
        调用方（支付事件）须吞异常，不阻断支付主流程。
        """
        from datetime import datetime, timezone

        tid = str(invited_tenant_id or "").strip()
        if not tid:
            return {"qualified": False, "reason": "missing_tenant"}

        rows = (
            self.db.query(ReferralRecord)
            .filter(
                ReferralRecord.invited_tenant_id == tid,
                ReferralRecord.status == "pending",
            )
            .all()
        )
        if not rows:
            already = (
                self.db.query(ReferralRecord)
                .filter(
                    ReferralRecord.invited_tenant_id == tid,
                    ReferralRecord.status == "rewarded",
                )
                .count()
            )
            return {
                "qualified": bool(already),
                "updated": 0,
                "reason": "already_rewarded" if already else "no_pending_invite",
            }

        now = datetime.now(timezone.utc)
        updated = 0
        for rec in rows:
            rec.status = "rewarded"
            rec.rewarded_at = now
            rec.reward_type = rec.reward_type or reason
            if not rec.reward_amount:
                rec.reward_amount = 1
            code = (
                self.db.query(ReferralCode)
                .filter(ReferralCode.id == rec.code_id)
                .first()
            )
            if code:
                code.total_earned = (code.total_earned or 0) + (rec.reward_amount or 1)
            updated += 1
        self.db.commit()

        # ── 模块9/11 轨6：裂变收入计量（referral.revenue）──
        # 计费时点 = 邀请被判定为有效并发放奖励（pending→rewarded = 收入确认），
        # **不是邀请创建时**（避免「未付费即确认收入」）。
        # 归属裁定：计量落在 inviter_tenant_id（推荐人 = 裂变行为主体，奖励记其名下）；
        # invited_tenant_id 一并写入 metadata 以便追溯核对（口径如需调整可复盘）。
        # meter_type 沿用既有 7 类 lead_generated（推荐带来新客户），
        # meter_code 落七轨稳定词表 referral.revenue（设计 9.3）。
        try:
            from app.services.billing.meter_event import MeterEventService

            for rec in rows:
                tenant_id = str(getattr(rec, "inviter_tenant_id", "") or "").strip()
                if not tenant_id:  # fail-closed：无租户不计量
                    logger.warning("referral_revenue 未计量：inviter 为空 rec_id=%s", rec.id)
                    continue
                MeterEventService(self.db).emit(
                    meter_type="lead_generated",
                    tenant_id=tenant_id,
                    event_key=f"referral:{rec.id}:rewarded",  # 幂等：同一邀请记录只计一次
                    quantity=1,
                    unit="reward",
                    source_ref_type="referral",
                    source_ref_id=str(rec.id),
                    meter_code="referral.revenue",
                    subject_type="referral",
                    subject_id=str(rec.id),
                    bill_status="unlinked",
                    metadata={
                        "meter_code": "referral.revenue",
                        "reason": reason,
                        "reward_amount": rec.reward_amount or 1,
                        "invited_tenant_id": str(getattr(rec, "invited_tenant_id", "") or ""),
                    },
                )
        except Exception:  # noqa: BLE001 —— 计量失败绝不阻断邀请发放主流程（调用方本就吞异常）
            logger.exception("referral_revenue 计量写入失败 invited_tenant=%s", tid)

        return {"qualified": True, "updated": updated, "reason": reason}

    def get_leaderboard(self, limit: int = 20) -> list:
        """邀请排行榜。

        metric=registration_invites：按注册邀请数排序（诚实标注）；
        rewarded_count = 首付费有效邀请数（first_paid）。
        """
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
        ranked = []
        for i, r in enumerate(rows, 1):
            tenant_id, total_referred, name = r[0], r[1], r[2]
            rewarded = self.db.query(ReferralRecord).filter(
                ReferralRecord.inviter_tenant_id == tenant_id,
                ReferralRecord.status == "rewarded",
            ).count()
            ranked.append({
                "rank": i,
                "company_name": name,
                "invite_count": total_referred,
                "rewarded_count": rewarded,
                "metric": "registration_invites",
            })
        return ranked

    def get_my_code(self, tenant_id: str) -> ReferralCode:
        """获取我的邀请码"""
        return self.db.query(ReferralCode).filter(
            ReferralCode.tenant_id == tenant_id,
            ReferralCode.is_active,
        ).first()
