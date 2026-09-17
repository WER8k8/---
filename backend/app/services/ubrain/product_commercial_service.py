# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""产品商业化服务 — FIX-74~81

FIX-74: 代理体系落地运营（代理注册 + 佣金结算 + 层级管理）
FIX-75: 模板市场（邮件模板 + 落地页模板 + 行业模板）
FIX-76: 行业解决方案包（建筑/保温/五金/装饰 4 大行业）
FIX-77: 代运营服务上线（服务套餐 + SLA + 交付物）
FIX-78: 白标方案（品牌定制 + 独立域名 + 自定义样式）
FIX-79: 客户成功：降低流失，提升 LTV（健康评分 + 干预策略）
FIX-80: 增长引擎：社区 + 内容营销 + 免费工具
FIX-81: 游戏化设计（积分 + 徽章 + 排行榜 + 里程碑）
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
# FIX-74: 代理体系
# ═══════════════════════════════════════════════════════════

@dataclass
class AgentTier:
    """代理层级"""
    name: str
    commission_rate: float  # 佣金比例
    min_monthly_revenue: float
    benefits: list[str] = field(default_factory=list)


class AgentSystemService:
    """代理体系服务。"""
    TIERS = [
        AgentTier("铜牌代理", 0.10, 0, ["基础培训", "营销素材"]),
        AgentTier("银牌代理", 0.15, 5000, ["专属顾问", "优先支持", "联合品牌"]),
        AgentTier("金牌代理", 0.20, 20000, ["区域保护", "年度峰会", "产品共创"]),
        AgentTier("钻石代理", 0.25, 50000, ["全球权益", "股权投资", "董事会席位"]),
    ]
    def __init__(self):
        """__init__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        self._agents: dict[str, dict] = {}

    def register_agent(self, user_id: str, company_name: str, region: str) -> dict[str, Any]:
        """注册代理。"""
        agent = {
            "user_id": user_id,
            "company_name": company_name,
            "region": region,
            "tier": "铜牌代理",
            "commission_rate": 0.10,
            "total_revenue": 0.0,
            "total_commission": 0.0,
            "registered_at": datetime.now(timezone.utc).isoformat(),
            "status": "active",
        }
        self._agents[user_id] = agent
        return agent

    def calculate_commission(self, user_id: str, sale_amount: float) -> dict[str, Any]:
        """计算佣金。"""
        agent = self._agents.get(user_id)
        if not agent:
            return {"error": "Agent not found"}

        rate = agent["commission_rate"]
        commission = sale_amount * rate
        agent["total_revenue"] += sale_amount
        agent["total_commission"] += commission
        # 检查是否升级
        self._check_tier_upgrade(user_id)
        return {
            "sale_amount": sale_amount,
            "commission_rate": rate,
            "commission": round(commission, 2),
            "tier": agent["tier"],
        }

    def _check_tier_upgrade(self, user_id: str) -> None:
        """检查代理层级升级。"""
        agent = self._agents.get(user_id)
        if not agent:
            return

        monthly_revenue = agent["total_revenue"]
        for tier in reversed(self.TIERS):
            if monthly_revenue >= tier.min_monthly_revenue:
                if agent["tier"] != tier.name:
                    agent["tier"] = tier.name
                    agent["commission_rate"] = tier.commission_rate
                    logger.info("Agent %s upgraded to %s", user_id, tier.name)
                break

    def get_agent_report(self, user_id: str) -> dict[str, Any]:
        """获取代理报告。"""
        agent = self._agents.get(user_id)
        if not agent:
            return {"error": "Agent not found"}
        return agent


# ═══════════════════════════════════════════════════════════
# FIX-75: 模板市场
# ═══════════════════════════════════════════════════════════

class TemplateMarketplaceService:
    """模板市场服务。"""
    TEMPLATES = {
        "email": [
            {"id": "em-001", "name": "初次触达", "category": "cold_outreach", "language": "en", "industry": "general"},
            {"id": "em-002", "name": "跟进邮件", "category": "follow_up", "language": "en", "industry": "general"},
            {"id": "em-003", "name": "产品介绍", "category": "product_intro", "language": "en", "industry": "construction"},
            {"id": "em-004", "name": "报价请求", "category": "quotation", "language": "en", "industry": "general"},
            {"id": "em-005", "name": "节日问候", "category": "relationship", "language": "en", "industry": "general"},
        ],
        "landing_page": [
            {"id": "lp-001", "name": "建材产品展示页", "category": "product_showcase", "industry": "construction"},
            {"id": "lp-002", "name": "保温解决方案页", "category": "solution", "industry": "insulation"},
            {"id": "lp-003", "name": "五金配件目录页", "category": "catalog", "industry": "hardware"},
        ],
        "social": [
            {"id": "so-001", "name": "LinkedIn 公司介绍", "platform": "linkedin", "industry": "general"},
            {"id": "so-002", "name": "Facebook 产品推广", "platform": "facebook", "industry": "general"},
        ],
    }
    def list_templates(self, category: str = "", industry: str = "", language: str = "") -> list[dict]:
        """列出模板。"""
        results = []
        for cat, templates in self.TEMPLATES.items():
            for t in templates:
                if category and t.get("category") != category:
                    continue
                if industry and t.get("industry") != industry:
                    continue
                if language and t.get("language") != language:
                    continue
                results.append({"type": cat, **t})
        return results

    def get_template(self, template_id: str) -> dict[str, Any] | None:
        """获取模板详情。"""
        for cat, templates in self.TEMPLATES.items():
            for t in templates:
                if t["id"] == template_id:
                    return {"type": cat, **t}
        return None


# ═══════════════════════════════════════════════════════════
# FIX-76: 行业解决方案包
# ═══════════════════════════════════════════════════════════

class IndustrySolutionService:
    """行业解决方案包服务。"""
    SOLUTIONS = {
        "construction": {
            "name": "建筑工程外贸解决方案",
            "description": "面向建筑承包商、工程公司的全套外贸获客方案",
            "target_roles": ["Purchasing Manager", "Project Manager", "Contractor"],
            "keywords": ["building materials", "construction supplies", "concrete", "steel"],
            "channels": ["email", "linkedin", "alibaba"],
            "templates": ["em-003", "lp-001"],
            "estimated_leads_per_month": 150,
        },
        "insulation": {
            "name": "保温材料外贸解决方案",
            "description": "面向绿色建筑、节能改造市场的保温隔热材料出口方案",
            "target_roles": ["Sourcing Manager", "Technical Director", "Procurement"],
            "keywords": ["insulation", "thermal insulation", "rock wool", "glass wool"],
            "channels": ["email", "linkedin", "trade_show"],
            "templates": ["lp-002"],
            "estimated_leads_per_month": 80,
        },
        "hardware": {
            "name": "五金配件外贸解决方案",
            "description": "面向建材批发商、五金连锁的配件出口方案",
            "target_roles": ["Buyer", "Category Manager", "Importer"],
            "keywords": ["hardware", "fasteners", "fittings", "tools"],
            "channels": ["email", "whatsapp", "b2b_platform"],
            "templates": ["lp-003"],
            "estimated_leads_per_month": 200,
        },
        "decoration": {
            "name": "装饰材料外贸解决方案",
            "description": "面向室内设计师、装饰公司的材料出口方案",
            "target_roles": ["Interior Designer", "Decorator", "Architect"],
            "keywords": ["decoration", "flooring", "wall panel", "ceiling"],
            "channels": ["email", "linkedin", "pinterest"],
            "templates": [],
            "estimated_leads_per_month": 100,
        },
    }
    def list_solutions(self) -> list[dict]:
        """列出所有行业解决方案。"""
        return [{"id": k, **v} for k, v in self.SOLUTIONS.items()]

    def get_solution(self, industry: str) -> dict[str, Any] | None:
        """获取指定行业方案。"""
        sol = self.SOLUTIONS.get(industry)
        if sol:
            return {"id": industry, **sol}
        return None


# ═══════════════════════════════════════════════════════════
# FIX-77: 代运营服务
# ═══════════════════════════════════════════════════════════

class ManagedServiceService:
    """代运营服务。"""
    PACKAGES = [
        {
            "id": "msp-starter",
            "name": "起步版",
            "price_monthly": 2999,
            "description": "适合初创外贸企业",
            "includes": [
                "每月 50 封 AI 开发信",
                "3 个 LinkedIn 账号运营",
                "基础数据报告",
                "1 次月度策略会议",
            ],
            "sla": {"response_time_hours": 48, "uptime_percent": 99},
        },
        {
            "id": "msp-growth",
            "name": "成长版",
            "price_monthly": 7999,
            "description": "适合快速扩张期企业",
            "includes": [
                "每月 200 封 AI 开发信",
                "10 个 LinkedIn 账号运营",
                "WhatsApp 客服托管",
                "每周数据报告 + A/B 测试",
                "2 次月度策略会议",
            ],
            "sla": {"response_time_hours": 24, "uptime_percent": 99.5},
        },
        {
            "id": "msp-enterprise",
            "name": "企业版",
            "price_monthly": 19999,
            "description": "适合成熟外贸企业",
            "includes": [
                "无限 AI 开发信",
                "全渠道托管（Email + LinkedIn + WhatsApp）",
                "专属客户成功经理",
                "实时数据看板",
                "每周策略会议",
                "行业峰会优先参与",
            ],
            "sla": {"response_time_hours": 4, "uptime_percent": 99.9},
        },
    ]
    def list_packages(self) -> list[dict]:
        """list_packages。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return self.PACKAGES

    def get_package(self, package_id: str) -> dict | None:
        """get_package。

        参数说明：
        :param self: 参数 self
        :param package_id: 参数 package_id
        :return: 返回处理结果。
        """
        for p in self.PACKAGES:
            if p["id"] == package_id:
                return p
        return None


# ═══════════════════════════════════════════════════════════
# FIX-78: 白标方案
# ═══════════════════════════════════════════════════════════

class WhiteLabelService:
    """白标方案服务。"""
    def generate_brand_config(
        self,
        brand_name: str,
        primary_color: str,
        logo_url: str,
        domain: str,
    ) -> dict[str, Any]:
        """生成白标品牌配置。"""
        return {
            "brand_name": brand_name,
            "primary_color": primary_color,
            "logo_url": logo_url,
            "custom_domain": domain,
            "email_sender": f"noreply@{domain}",
            "login_page": {
                "background_image": "",
                "welcome_text": f"Welcome to {brand_name}",
            },
            "dashboard": {
                "hide_powered_by": True,
                "custom_css": "",
            },
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    def get_pricing(self) -> dict[str, Any]:
        """白标定价。"""
        return {
            "setup_fee": 50000,
            "monthly_fee": 15000,
            "per_user_fee": 50,
            "revenue_share_percent": 15,
            "min_contract_months": 12,
        }


# ═══════════════════════════════════════════════════════════
# FIX-79: 客户成功
# ═══════════════════════════════════════════════════════════

class CustomerSuccessService:
    """客户成功服务。"""
    def calculate_health_score(self, tenant_data: dict[str, Any]) -> dict[str, Any]:
        """计算租户健康评分。"""
        # 6 维度评分
        dimensions = {
            "onboarding_completion": min(100, tenant_data.get("onboarding_step", 0) * 20),
            "feature_adoption": min(100, len(tenant_data.get("used_features", [])) * 10),
            "engagement": min(100, tenant_data.get("weekly_logins", 0) * 10),
            "data_quality": min(100, tenant_data.get("profile_completion", 0)),
            "support_satisfaction": tenant_data.get("csat_score", 80),
            "outcome_achievement": min(100, tenant_data.get("leads_generated", 0)),
        }
        score = sum(dimensions.values()) / len(dimensions)
        risk = "low"
        if score < 40:
            risk = "critical"
        elif score < 60:
            risk = "high"
        elif score < 75:
            risk = "medium"

        interventions = []
        if dimensions["onboarding_completion"] < 60:
            interventions.append("安排 onboarding 专项辅导")
        if dimensions["engagement"] < 40:
            interventions.append("发送激活邮件 + 优惠激励")
        if dimensions["feature_adoption"] < 50:
            interventions.append("推送功能教程 + 案例分享")

        return {
            "overall_score": round(score, 1),
            "risk_level": risk,
            "dimensions": dimensions,
            "recommended_interventions": interventions,
        }

    def calculate_ltv(self, monthly_revenue: float, churn_rate: float, gross_margin: float = 0.7) -> dict[str, Any]:
        """计算 LTV。"""
        if churn_rate <= 0:
            churn_rate = 0.01
        ltv = (monthly_revenue * gross_margin) / churn_rate
        return {
            "monthly_revenue": monthly_revenue,
            "churn_rate": churn_rate,
            "gross_margin": gross_margin,
            "ltv": round(ltv, 2),
            "ltv_cac_ratio": "N/A",  # 需要 CAC 数据
        }


# ═══════════════════════════════════════════════════════════
# FIX-80: 增长引擎
# ═══════════════════════════════════════════════════════════

class GrowthEngineService:
    """增长引擎服务。"""
    def get_community_strategy(self) -> dict[str, Any]:
        """获取社区建设策略。"""
        return {
            "channels": [
                {"name": "微信社群", "target": "国内客户", "content": "案例分享 + 行业资讯"},
                {"name": "Discord", "target": "海外用户", "content": "产品更新 + 技术支持"},
                {"name": "LinkedIn Group", "target": "B2B 决策者", "content": "行业洞察 + 网络活动"},
            ],
            "kpis": {
                "members_3m": 1000,
                "engagement_rate": 0.15,
                "ugc_per_month": 50,
            },
        }

    def get_content_marketing_plan(self) -> dict[str, Any]:
        """获取内容营销计划。"""
        return {
            "blog": {"frequency": "每周 2 篇", "topics": ["外贸获客技巧", "行业趋势", "客户案例"]},
            "video": {"frequency": "每周 1 个", "platforms": ["YouTube", "TikTok", "Bilibili"]},
            "newsletter": {"frequency": "双周刊", "subscribers_target": 10000},
            "seo": {"target_keywords": 50, "monthly_articles": 8},
        }

    def get_free_tools(self) -> list[dict]:
        """获取免费工具列表。"""
        return [
            {"name": "外贸邮箱验证器", "description": "零成本验证邮箱有效性", "url": "/tools/email-verifier"},
            {"name": "HS 编码查询", "description": "海关编码快速查询", "url": "/tools/hs-code"},
            {"name": "汇率计算器", "description": "实时汇率 + 历史走势", "url": "/tools/currency"},
            {"name": " Incoterms 指南", "description": "国际贸易术语交互指南", "url": "/tools/incoterms"},
        ]


# ═══════════════════════════════════════════════════════════
# FIX-81: 游戏化设计
# ═══════════════════════════════════════════════════════════

class GamificationService:
    """游戏化服务。"""
    BADGES = [
        {"id": "first_lead", "name": "初出茅庐", "description": "获取第一条线索", "icon": "🎯"},
        {"id": "first_email", "name": "邮件达人", "description": "发送第一封开发信", "icon": "✉️"},
        {"id": "lead_100", "name": "百尺竿头", "description": "累计获取 100 条线索", "icon": "💯"},
        {"id": "reply_10", "name": "互动大师", "description": "收到 10 封回复", "icon": "💬"},
        {"id": "deal_1", "name": "首单成交", "description": "完成第一笔交易", "icon": "🤝"},
        {"id": "streak_7", "name": "七日连击", "description": "连续 7 天登录", "icon": "🔥"},
        {"id": "explorer", "name": "探索者", "description": "使用 10 个不同功能", "icon": "🧭"},
        {"id": "influencer", "name": "影响力", "description": "邀请 3 位好友注册", "icon": "🌟"},
    ]
    LEVELS = [
        {"level": 1, "name": "新手", "min_points": 0, "color": "#94a3b8"},
        {"level": 2, "name": "学徒", "min_points": 100, "color": "#60a5fa"},
        {"level": 3, "name": "专员", "min_points": 500, "color": "#34d399"},
        {"level": 4, "name": "专家", "min_points": 2000, "color": "#f59e0b"},
        {"level": 5, "name": "大师", "min_points": 5000, "color": "#ef4444"},
        {"level": 6, "name": "传奇", "min_points": 10000, "color": "#a855f7"},
    ]
    def __init__(self):
        """__init__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        self._user_points: dict[str, int] = {}
        self._user_badges: dict[str, list[str]] = {}

    def award_points(self, user_id: str, action: str, points: int = 10) -> dict[str, Any]:
        """奖励积分。"""
        current = self._user_points.get(user_id, 0)
        new_total = current + points
        self._user_points[user_id] = new_total
        # 计算等级
        level = self._get_level(new_total)
        return {
            "user_id": user_id,
            "action": action,
            "points_awarded": points,
            "total_points": new_total,
            "level": level,
        }

    def _get_level(self, points: int) -> dict[str, Any]:
        """根据积分获取等级。"""
        current_level = self.LEVELS[0]
        for level in self.LEVELS:
            if points >= level["min_points"]:
                current_level = level
        return current_level

    def award_badge(self, user_id: str, badge_id: str) -> dict[str, Any]:
        """授予徽章。"""
        if user_id not in self._user_badges:
            self._user_badges[user_id] = []

        if badge_id not in self._user_badges[user_id]:
            self._user_badges[user_id].append(badge_id)

        badge = next((b for b in self.BADGES if b["id"] == badge_id), None)
        return {
            "user_id": user_id,
            "badge": badge,
            "total_badges": len(self._user_badges[user_id]),
        }

    def get_user_gamification(self, user_id: str) -> dict[str, Any]:
        """获取用户游戏化数据。"""
        points = self._user_points.get(user_id, 0)
        badges = self._user_badges.get(user_id, [])
        return {
            "user_id": user_id,
            "points": points,
            "level": self._get_level(points),
            "badges": [b for b in self.BADGES if b["id"] in badges],
            "next_level_progress": self._next_level_progress(points),
        }

    def _next_level_progress(self, points: int) -> dict[str, Any]:
        """计算下一级进度。"""
        current_level = self._get_level(points)
        current_idx = self.LEVELS.index(current_level)
        if current_idx >= len(self.LEVELS) - 1:
            return {"progress": 1.0, "points_needed": 0}

        next_level = self.LEVELS[current_idx + 1]
        needed = next_level["min_points"] - current_level["min_points"]
        earned = points - current_level["min_points"]
        return {
            "progress": round(earned / needed, 2),
            "points_needed": next_level["min_points"] - points,
        }

    def get_leaderboard(self, limit: int = 10) -> list[dict]:
        """获取排行榜。"""
        sorted_users = sorted(self._user_points.items(), key=lambda x: x[1], reverse=True)
        return [
            {
                "rank": i + 1,
                "user_id": uid,
                "points": points,
                "level": self._get_level(points)["name"],
            }
            for i, (uid, points) in enumerate(sorted_users[:limit])
        ]


# 单例
agent_system_service = AgentSystemService()
template_marketplace_service = TemplateMarketplaceService()
industry_solution_service = IndustrySolutionService()
managed_service_service = ManagedServiceService()
white_label_service = WhiteLabelService()
customer_success_service = CustomerSuccessService()
growth_engine_service = GrowthEngineService()
gamification_service = GamificationService()