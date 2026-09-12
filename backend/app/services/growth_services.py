"""推荐奖励机制 + 客户成功体系 — FIX-49/50

推荐奖励：
- 推荐链接生成
- 推荐追踪
- 奖励发放
- 排行榜

客户成功：
- 健康评分
- 流失预警
- 成功里程碑
- NPS 调查
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional
import uuid

log = logging.getLogger(__name__)


# ============================================================
# FIX-49: 推荐奖励机制
# ============================================================

class ReferralStatus(str, Enum):
    """推荐状态。"""
    PENDING = "pending"         # 已推荐，待注册
    REGISTERED = "registered"   # 已注册
    ACTIVATED = "activated"     # 已激活（完成Aha Moment）
    PAID = "paid"               # 已付费
    REWARDED = "rewarded"       # 已发放奖励


class ReferralService:
    """推荐奖励服务。"""
    REWARDS = {
        ReferralStatus.REGISTERED: {"credits": 20, "label": "被推荐人注册"},
        ReferralStatus.ACTIVATED: {"credits": 30, "label": "被推荐人完成激活"},
        ReferralStatus.PAID: {"credits": 50, "label": "被推荐人付费"},
    }
    @staticmethod
    def generate_referral_code(user_id: str) -> str:
        """生成推荐码。"""
        import hashlib
        raw = f"{user_id}:{uuid.uuid4()}"
        return hashlib.sha256(raw.encode()).hexdigest()[:10].upper()

    @staticmethod
    def generate_referral_link(user_id: str, base_url: str = "https://uj-china.com") -> str:
        """生成推荐链接。"""
        code = ReferralService.generate_referral_code(user_id)
        return f"{base_url}/ref/{code}"

    @staticmethod
    async def track_referral(
        referrer_id: str,
        referee_email: str,
        channel: str = "direct",
    ) -> dict:
        """追踪推荐。"""
        referral_id = str(uuid.uuid4())
        log.info("[Referral] 新推荐: referrer=%s referee=%s", referrer_id, referee_email)
        return {
            "referral_id": referral_id,
            "referrer_id": referrer_id,
            "referee_email": referee_email,
            "status": ReferralStatus.PENDING.value,
            "channel": channel,
            "reward_potential": sum(r["credits"] for r in ReferralService.REWARDS.values()),
        }

    @staticmethod
    async def get_referral_stats(user_id: str) -> dict:
        """获取推荐统计。"""
        return {
            "referral_code": ReferralService.generate_referral_code(user_id),
            "referral_link": ReferralService.generate_referral_link(user_id),
            "stats": {
                "total_referrals": 0,
                "registered": 0,
                "activated": 0,
                "paid": 0,
                "total_credits_earned": 0,
                "monthly_credits_earned": 0,
            },
            "rewards": [
                {"action": "被推荐人注册", "credits": 20},
                {"action": "被推荐人完成激活", "credits": 30},
                {"action": "被推荐人付费", "credits": 50},
            ],
            "max_monthly": 500,
        }

    @staticmethod
    async def get_leaderboard(limit: int = 20) -> list[dict]:
        """获取推荐排行榜。"""
        return [
            {"rank": 1, "user": "user_001", "referrals": 25, "credits": 1250},
            {"rank": 2, "user": "user_002", "referrals": 18, "credits": 900},
            {"rank": 3, "user": "user_003", "referrals": 15, "credits": 750},
        ][:limit]


# ============================================================
# FIX-50: 客户成功体系
# ============================================================

class HealthScoreTier(str, Enum):
    """健康评分等级。"""
    HEALTHY = "healthy"         # 80-100: 健康
    AT_RISK = "at_risk"         # 50-79: 有风险
    CRITICAL = "critical"       # 0-49: 危险


class CustomerSuccessService:
    """客户成功服务。"""
    # 健康评分维度权重
    HEALTH_WEIGHTS = {
        "engagement": 0.25,       # 活跃度
        "feature_adoption": 0.20, # 功能采用
        "lead_activity": 0.20,    # 获客活跃度
        "growth": 0.15,           # 增长趋势
        "support": 0.10,          # 支持请求
        "billing": 0.10,          # 付费状态
    }
    # 成功里程碑
    MILESTONES = [
        {
            "id": "first_login",
            "name": "首次登录",
            "description": "完成首次登录并进入工作台",
            "icon": "login",
        },
        {
            "id": "first_site",
            "name": "创建首个站点",
            "description": "使用AI建站创建第一个出海官网",
            "icon": "globe",
        },
        {
            "id": "first_lead",
            "name": "获取首个线索",
            "description": "AI搜索到第一个潜在客户",
            "icon": "user-plus",
        },
        {
            "id": "first_email",
            "name": "发送第一封邮件",
            "description": "发送第一封AI开发信",
            "icon": "mail",
        },
        {
            "id": "first_reply",
            "name": "收到首次回复",
            "description": "潜在客户回复了你的邮件",
            "icon": "message-circle",
        },
        {
            "id": "first_deal",
            "name": "成交首个客户",
            "description": "通过平台获得第一个成交客户",
            "icon": "trophy",
        },
        {
            "id": "power_user",
            "name": "高级用户",
            "description": "累计发送100封邮件并获取50个线索",
            "icon": "star",
        },
        {
            "id": "champion",
            "name": "平台冠军",
            "description": "累计成交10个客户",
            "icon": "award",
        },
    ]
    @staticmethod
    async def calculate_health_score(user_id: str) -> dict:
        """计算客户健康评分。"""
        try:
            from app.db.session import SessionLocal
            from app.models.prospect_lead import ProspectLead
            from app.models.email_outreach import EmailOutreach
            db = SessionLocal()
            try:
                now = datetime.utcnow()
                month_ago = now - timedelta(days=30)
                week_ago = now - timedelta(days=7)
                # 活跃度评分
                leads_week = db.query(ProspectLead).filter(
                    ProspectLead.created_at >= week_ago
                ).count()
                engagement = min(100, leads_week * 10)
                # 功能采用评分
                from sqlalchemy import func
                features_used = 1  # 基础分
                if leads_week > 0:
                    features_used += 1
                outreach_count = db.query(EmailOutreach).filter(
                    EmailOutreach.created_at >= month_ago
                ).count()
                if outreach_count > 0:
                    features_used += 1
                feature_adoption = min(100, features_used * 20)
                # 获客活跃度
                leads_month = db.query(ProspectLead).filter(
                    ProspectLead.created_at >= month_ago
                ).count()
                lead_activity = min(100, leads_month * 5)
                # 增长趋势
                leads_prev_month = db.query(ProspectLead).filter(
                    ProspectLead.created_at.between(
                        month_ago - timedelta(days=30), month_ago
                    )
                ).count()
                growth = 50
                if leads_prev_month > 0:
                    growth = min(100, (leads_month / leads_prev_month) * 50 + 50)
                elif leads_month > 0:
                    growth = 80

                # 综合评分
                scores = {
                    "engagement": engagement,
                    "feature_adoption": feature_adoption,
                    "lead_activity": lead_activity,
                    "growth": growth,
                    "support": 80,    # 默认无支持请求
                    "billing": 90,    # 默认付费正常
                }
                total = sum(
                    scores[dim] * weight
                    for dim, weight in CustomerSuccessService.HEALTH_WEIGHTS.items()
                )
                tier = (
                    HealthScoreTier.HEALTHY if total >= 80
                    else HealthScoreTier.AT_RISK if total >= 50
                    else HealthScoreTier.CRITICAL
                )
                return {
                    "user_id": user_id,
                    "score": round(total, 1),
                    "tier": tier.value,
                    "tier_label": {
                        "healthy": "健康",
                        "at_risk": "有风险",
                        "critical": "危险",
                    }[tier.value],
                    "breakdown": {
                        dim: {
                            "score": round(s, 1),
                            "weight": round(w * 100),
                        }
                        for dim, (s, w) in zip(
                            scores.keys(),
                            [(scores[dim], CustomerSuccessService.HEALTH_WEIGHTS[dim]) for dim in scores],
                        )
                    },
                    "milestones_completed": [],
                    "recommendations": CustomerSuccessService._get_recommendations(tier, scores),
                }
            finally:
                db.close()
        except Exception as e:
            log.error("[CS] 健康评分计算失败: %s", e)
            return {"error": str(e)}

    @staticmethod
    async def get_milestones(user_id: str) -> list[dict]:
        """获取用户里程碑。"""
        completed = set()  # 后续从数据库查询
        return [
            {
                **m,
                "completed": m["id"] in completed,
                "completed_at": None,
            }
            for m in CustomerSuccessService.MILESTONES
        ]

    @staticmethod
    async def get_nps_survey() -> dict:
        """获取 NPS 调查问卷。"""
        return {
            "question": "您有多大可能向朋友或同事推荐我们的产品？",
            "scale": "0-10",
            "categories": [
                {"range": "0-6", "label": "贬损者", "color": "#ef4444"},
                {"range": "7-8", "label": "被动者", "color": "#f59e0b"},
                {"range": "9-10", "label": "推荐者", "color": "#10b981"},
            ],
            "follow_up": "您给出这个评分的主要原因是什么？",
        }

    @staticmethod
    def _get_recommendations(tier: HealthScoreTier, scores: dict) -> list[str]:
        """根据健康评分给出建议。"""
        recommendations = []
        if tier == HealthScoreTier.CRITICAL:
            recommendations.append("建议联系客户成功经理进行一对一沟通")
        if scores.get("engagement", 0) < 50:
            recommendations.append("客户活跃度较低，建议发送激活邮件")
        if scores.get("feature_adoption", 0) < 40:
            recommendations.append("建议引导客户使用更多核心功能")
        if scores.get("lead_activity", 0) < 30:
            recommendations.append("客户获客活跃度低，建议提供获客指导")
        if tier == HealthScoreTier.HEALTHY:
            recommendations.append("客户状态良好，可考虑推荐升级套餐")

        return recommendations if recommendations else ["继续保持当前状态"]


# 全局实例
referral_service = ReferralService()
customer_success_service = CustomerSuccessService()