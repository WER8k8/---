# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""产品价值主张与计费体系 — FIX-32/33/34: 产品商业化核心

价值主张重新定位：
  从"出海营销工具"升级为"AI驱动的出海增长操作系统"

精细化计费体系：
  5档套餐 + 获客积分混合计费模型

获客积分体系：
  信用积分 + 消耗积分双轨制
"""

from __future__ import annotations

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional


# ============================================================
# FIX-32: 价值主张重新定位
# ============================================================

class ValueProposition:
    """产品价值主张定义。"""
    # 核心定位
    CORE_POSITIONING = "AI驱动的出海增长操作系统"
    # 一句话价值主张
    ONE_LINER = (
        "从建站到获客、从SEO到邮件营销，一站式AI出海增长平台。"
        "零成本起步，按效果付费。"
    )
    # 目标客户画像
    TARGET_PERSONAS = {
        "b2b_manufacturer": {
            "label": "B2B制造企业",
            "pain_points": [
                "不懂海外营销",
                "没有专业团队",
                "获客成本高",
                "建站质量差",
            ],
            "value_prop": "10分钟搭建专业出海官网，AI自动获客，零成本起步",
        },
        "trade_company": {
            "label": "外贸公司",
            "pain_points": [
                "客户来源单一",
                "邮件开发效率低",
                "SEO竞争激烈",
                "多语言内容难维护",
            ],
            "value_prop": "AI自动搜索潜在客户，智能邮件外展，多语言SEO优化",
        },
        "soho_trader": {
            "label": "SOHO外贸个体户",
            "pain_points": [
                "预算有限",
                "缺乏技术能力",
                "需要全流程工具",
                "时间精力有限",
            ],
            "value_prop": "免费起步，AI帮你做获客、建站、SEO，一人搞定全流程",
        },
        "agency": {
            "label": "出海服务商/代理",
            "pain_points": [
                "客户管理分散",
                "效果难以量化",
                "多客户运营效率低",
                "白标需求",
            ],
            "value_prop": "多租户管理，白标方案，客户效果仪表板，代理佣金体系",
        },
    }
    # 差异化优势
    DIFFERENTIATORS = [
        {
            "dimension": "AI获客引擎",
            "competitors": "手动搜索或付费工具($100+/月)",
            "us": "零成本AI自动搜索+验证+外展，$0起步",
        },
        {
            "dimension": "全链路闭环",
            "competitors": "建站/SEO/获客/邮件各用不同工具",
            "us": "一站式平台，建站→SEO→获客→邮件→分析全部打通",
        },
        {
            "dimension": "智能体协同",
            "competitors": "传统SaaS，人工操作",
            "us": "39+ AI技能，Agent自动执行，7x24小时运转",
        },
        {
            "dimension": "按效果付费",
            "competitors": "固定月费，不管效果",
            "us": "免费起步 + 获客积分制，找到客户才付费",
        },
        {
            "dimension": "多语言多站点",
            "competitors": "单语言建站，多站点需额外付费",
            "us": "内置全球化多语言，一个后台管理全球站点",
        },
    ]
    # Aha Moment: 10分钟内感受到的价值
    AHA_MOMENT_JOURNEY = [
        {"step": 1, "time": "0-2分钟", "action": "注册账号，选择行业模板"},
        {"step": 2, "time": "2-5分钟", "action": "AI自动生成出海官网（含产品页+SEO）"},
        {"step": 3, "time": "5-8分钟", "action": "AI搜索第一批潜在客户（10个免费线索）"},
        {"step": 4, "time": "8-10分钟", "action": "发送第一封AI开发信，看到打开追踪"},
    ]


# ============================================================
# FIX-33: 精细化计费体系 — 5档套餐 + 获客积分混合计费
# ============================================================

class PlanTier(str, Enum):
    """套餐等级。"""
    FREE = "free"           # 免费版 - 体验核心功能
    STARTER = "starter"     # 入门版 - 小型外贸企业
    GROWTH = "growth"       # 增长版 - 成长型外贸企业
    PRO = "pro"             # 专业版 - 成熟外贸企业
    ENTERPRISE = "enterprise"  # 企业版 - 大型外贸集团


@dataclass
class PlanConfig:
    """套餐配置。"""
    tier: PlanTier
    name: str
    name_cn: str
    price_monthly: float    # 月费（美元）
    price_yearly: float     # 年费（美元，月均）
    lead_credits_monthly: int  # 每月获客积分
    products_limit: int
    sites_limit: int
    seo_pages_limit: int
    ai_skills_limit: int
    team_members: int
    features: list[str]
    highlighted: bool = False


# 5档套餐定义
PLANS: dict[PlanTier, PlanConfig] = {
    PlanTier.FREE: PlanConfig(
        tier=PlanTier.FREE,
        name="Free",
        name_cn="免费版",
        price_monthly=0,
        price_yearly=0,
        lead_credits_monthly=10,
        products_limit=5,
        sites_limit=1,
        seo_pages_limit=3,
        ai_skills_limit=5,
        team_members=1,
        features=[
            "AI建站（1个站点）",
            "5个产品展示",
            "基础SEO优化",
            "10个免费获客积分/月",
            "邮件验证（100次/月）",
            "社区支持",
        ],
    ),
    PlanTier.STARTER: PlanConfig(
        tier=PlanTier.STARTER,
        name="Starter",
        name_cn="入门版",
        price_monthly=29,
        price_yearly=290,  # 月均$24.17
        lead_credits_monthly=50,
        products_limit=50,
        sites_limit=2,
        seo_pages_limit=20,
        ai_skills_limit=15,
        team_members=3,
        features=[
            "AI建站（2个站点）",
            "50个产品展示",
            "高级SEO优化",
            "50个获客积分/月",
            "邮件验证（500次/月）",
            "邮件外展（100封/月）",
            "基础数据分析",
            "邮件支持",
        ],
    ),
    PlanTier.GROWTH: PlanConfig(
        tier=PlanTier.GROWTH,
        name="Growth",
        name_cn="增长版",
        price_monthly=79,
        price_yearly=790,  # 月均$65.83
        lead_credits_monthly=200,
        products_limit=200,
        sites_limit=5,
        seo_pages_limit=100,
        ai_skills_limit=25,
        team_members=10,
        features=[
            "AI建站（5个站点）",
            "200个产品展示",
            "专业SEO优化 + 关键词排名追踪",
            "200个获客积分/月",
            "邮件验证（2000次/月）",
            "邮件外展（500封/月）",
            "邮件序列（Drip Campaign）",
            "高级数据分析 + 归因",
            "多语言站点",
            "优先邮件支持",
        ],
        highlighted=True,  # 推荐套餐
    ),
    PlanTier.PRO: PlanConfig(
        tier=PlanTier.PRO,
        name="Pro",
        name_cn="专业版",
        price_monthly=199,
        price_yearly=1990,  # 月均$165.83
        lead_credits_monthly=500,
        products_limit=1000,
        sites_limit=20,
        seo_pages_limit=500,
        ai_skills_limit=39,
        team_members=30,
        features=[
            "AI建站（20个站点）",
            "1000个产品展示",
            "企业级SEO + GEO优化",
            "500个获客积分/月",
            "邮件验证（10000次/月）",
            "邮件外展（2000封/月）",
            "AI开发信生成 + A/B测试",
            "全链路归因分析",
            "多语言 + 多货币",
            "API 访问",
            "专属客户成功经理",
        ],
    ),
    PlanTier.ENTERPRISE: PlanConfig(
        tier=PlanTier.ENTERPRISE,
        name="Enterprise",
        name_cn="企业版",
        price_monthly=499,
        price_yearly=4990,  # 月均$415.83
        lead_credits_monthly=2000,
        products_limit=99999,
        sites_limit=999,
        seo_pages_limit=9999,
        ai_skills_limit=39,
        team_members=999,
        features=[
            "无限站点",
            "无限产品",
            "全功能SEO/GEO/AEO",
            "2000个获客积分/月",
            "无限制邮件验证",
            "无限制邮件外展",
            "AI智能体定制",
            "白标方案",
            "私有化部署可选",
            "SLA 99.9%",
            "专属技术团队",
            "定制化开发",
        ],
    ),
}


# ============================================================
# FIX-34: 获客积分体系
# ============================================================

class CreditType(str, Enum):
    """积分类型。"""
    MONTHLY = "monthly"       # 月度免费积分（套餐内赠送）
    PURCHASED = "purchased"   # 购买的积分包
    BONUS = "bonus"           # 奖励积分（推荐、活动等）
    ROLLOVER = "rollover"     # 上月结转积分


class CreditAction(str, Enum):
    """积分消耗动作。"""
    SEARCH_LEAD = "search_lead"           # 搜索一个潜在客户: 1积分
    VERIFY_EMAIL = "verify_email"         # 验证一个邮箱: 0.5积分
    SEND_EMAIL = "send_email"             # 发送一封邮件: 1积分
    SCRAPE_WEBSITE = "scrape_website"     # 抓取一个网站邮箱: 2积分
    AI_OUTREACH = "ai_outreach"           # AI生成开发信: 3积分
    DEEP_RESEARCH = "deep_research"       # 深度客户研究: 5积分
    EXPORT_LEADS = "export_leads"         # 导出线索: 10积分/100条


# 积分消耗表
CREDIT_COST: dict[CreditAction, float] = {
    CreditAction.SEARCH_LEAD: 1.0,
    CreditAction.VERIFY_EMAIL: 0.5,
    CreditAction.SEND_EMAIL: 1.0,
    CreditAction.SCRAPE_WEBSITE: 2.0,
    CreditAction.AI_OUTREACH: 3.0,
    CreditAction.DEEP_RESEARCH: 5.0,
    CreditAction.EXPORT_LEADS: 0.1,  # 每条0.1积分
}


# 积分包购买选项
@dataclass
class CreditPack:
    """积分包。"""
    id: str
    name: str
    credits: int
    price_usd: float
    unit_price: float  # 每积分价格
    popular: bool = False


CREDIT_PACKS: list[CreditPack] = [
    CreditPack(
        id="pack-100",
        name="100积分包",
        credits=100,
        price_usd=9.9,
        unit_price=0.099,
    ),
    CreditPack(
        id="pack-500",
        name="500积分包",
        credits=500,
        price_usd=39.9,
        unit_price=0.080,
        popular=True,
    ),
    CreditPack(
        id="pack-1000",
        name="1000积分包",
        credits=1000,
        price_usd=69.9,
        unit_price=0.070,
    ),
    CreditPack(
        id="pack-5000",
        name="5000积分包",
        credits=5000,
        price_usd=299,
        unit_price=0.060,
    ),
]


# 积分过期规则
CREDIT_EXPIRY = {
    CreditType.MONTHLY: "当月有效，不结转",        # 月度积分月底清零
    CreditType.PURCHASED: "购买后12个月有效",       # 购买积分1年有效
    CreditType.BONUS: "发放后3个月有效",            # 奖励积分3个月
    CreditType.ROLLOVER: "结转后1个月有效",          # 结转积分下月用完
}


# 积分消耗优先级：月度 → 结转 → 奖励 → 购买
CREDIT_CONSUMPTION_PRIORITY = [
    CreditType.MONTHLY,
    CreditType.ROLLOVER,
    CreditType.BONUS,
    CreditType.PURCHASED,
]


# 推荐奖励积分
REFERRAL_BONUS = {
    "referrer": 50,   # 推荐人获得50积分
    "referee": 20,    # 被推荐人获得20积分
    "max_monthly": 500,  # 每月推荐奖励上限
}


# ============================================================
# 产品商业化 API 数据接口
# ============================================================

def get_plans_for_display() -> list[dict]:
    """返回套餐列表（前端展示用）。"""
    return [
        {
            "tier": p.tier.value,
            "name": p.name,
            "name_cn": p.name_cn,
            "price_monthly": p.price_monthly,
            "price_yearly": p.price_yearly,
            "monthly_yearly": round(p.price_yearly / 12, 2),
            "lead_credits_monthly": p.lead_credits_monthly,
            "products_limit": p.products_limit,
            "sites_limit": p.sites_limit,
            "features": p.features,
            "highlighted": p.highlighted,
        }
        for p in PLANS.values()
    ]


def get_value_proposition() -> dict:
    """返回价值主张（前端展示用）。"""
    return {
        "core_positioning": ValueProposition.CORE_POSITIONING,
        "one_liner": ValueProposition.ONE_LINER,
        "target_personas": {
            k: {"label": v["label"], "pain_points": v["pain_points"], "value_prop": v["value_prop"]}
            for k, v in ValueProposition.TARGET_PERSONAS.items()
        },
        "differentiators": ValueProposition.DIFFERENTIATORS,
        "aha_moment": ValueProposition.AHA_MOMENT_JOURNEY,
    }


def get_credit_system() -> dict:
    """返回积分体系（前端展示用）。"""
    return {
        "credit_types": {t.value: t.name for t in CreditType},
        "credit_costs": {a.value: cost for a, cost in CREDIT_COST.items()},
        "credit_packs": [
            {"id": p.id, "name": p.name, "credits": p.credits, "price": p.price_usd, "popular": p.popular}
            for p in CREDIT_PACKS
        ],
        "expiry_rules": {t.value: rule for t, rule in CREDIT_EXPIRY.items()},
        "referral_bonus": REFERRAL_BONUS,
    }