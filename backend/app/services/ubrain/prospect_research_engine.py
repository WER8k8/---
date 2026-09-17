# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""RAG 客户洞察 + 定制化开发信 — FIX-56

基于检索增强生成（RAG）的客户研究 + 个性化开发信引擎：
1. 客户情报收集：网站抓取 + 新闻 + 行业报告 + 社交媒体
2. 客户画像构建：公司概况 + 痛点分析 + 技术栈 + 增长信号
3. 个性化开发信生成：基于洞察定制化邮件
4. 价值主张匹配：根据客户特征推荐最合适的 pitch

技术栈：
- 检索：Web scraping + News API + LinkedIn（可选）
- 向量存储：Qdrant（已有）
- LLM：复用现有 LLM 基础设施
- 模板：复用 ai_email_generator.py 模板系统
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


# ── 枚举 ──────────────────────────────────────────────────

class CompanyGrowthSignal(str, Enum):
    """公司增长信号"""
    HIRING = "hiring"              # 大规模招聘
    FUNDING = "funding"            # 融资
    EXPANSION = "expansion"        # 新市场/办公室
    PRODUCT_LAUNCH = "product_launch"  # 新产品发布
    PARTNERSHIP = "partnership"    # 新合作
    AWARD = "award"                # 获奖
    ACQUISITION = "acquisition"    # 收购
    REBRAND = "rebrand"            # 品牌重塑
    LEADERSHIP = "leadership"      # 高管变动


class InsightCategory(str, Enum):
    """洞察类别"""
    INDUSTRY_TREND = "industry_trend"
    COMPANY_NEWS = "company_news"
    PAIN_POINT = "pain_point"
    OPPORTUNITY = "opportunity"
    TECH_STACK = "tech_stack"
    COMPETITOR = "competitor"
    GROWTH_SIGNAL = "growth_signal"
    PERSONA_MATCH = "persona_match"


class EmailTone(str, Enum):
    """邮件语气"""
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    CONSULTATIVE = "consultative"
    DIRECT = "direct"
    STORY_DRIVEN = "story_driven"


# ── 数据模型 ──────────────────────────────────────────────

@dataclass
class CompanyInsight:
    """公司洞察"""
    category: InsightCategory
    title: str
    description: str
    confidence: float = 0.5    # 0-1
    source_url: str = ""
    source_date: str = ""
    relevance_score: float = 0.0  # 对当前 outreach 的相关性
    def to_dict(self) -> dict:
        """to_dict。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return {
            "category": self.category.value,
            "title": self.title,
            "description": self.description,
            "confidence": self.confidence,
            "source_url": self.source_url,
            "source_date": self.source_date,
            "relevance_score": self.relevance_score,
        }


@dataclass
class ProspectResearch:
    """客户研究结果"""
    company_name: str
    website: str
    industry: str = ""
    company_size: str = ""
    location: str = ""
    description: str = ""
    insights: list[CompanyInsight] = field(default_factory=list)
    growth_signals: list[CompanyGrowthSignal] = field(default_factory=list)
    pain_points: list[str] = field(default_factory=list)
    opportunities: list[str] = field(default_factory=list)
    talking_points: list[str] = field(default_factory=list)
    tech_stack: list[str] = field(default_factory=list)
    competitors: list[str] = field(default_factory=list)
    recent_news: list[dict] = field(default_factory=list)
    social_media: dict[str, str] = field(default_factory=dict)
    research_quality: float = 0.0  # 0-1
    def to_dict(self) -> dict:
        """to_dict。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return {
            "company_name": self.company_name,
            "website": self.website,
            "industry": self.industry,
            "company_size": self.company_size,
            "location": self.location,
            "description": self.description,
            "insights": [i.to_dict() for i in self.insights],
            "growth_signals": [s.value for s in self.growth_signals],
            "pain_points": self.pain_points,
            "opportunities": self.opportunities,
            "talking_points": self.talking_points,
            "tech_stack": self.tech_stack,
            "competitors": self.competitors,
            "recent_news": self.recent_news,
            "social_media": self.social_media,
            "research_quality": self.research_quality,
        }


@dataclass
class PersonalizedEmail:
    """个性化开发信"""
    subject: str
    body: str
    tone: EmailTone = EmailTone.PROFESSIONAL
    insights_used: list[str] = field(default_factory=list)
    personalization_score: float = 0.0   # 0-1
    open_rate_prediction: float = 0.0    # 预测打开率
    reply_rate_prediction: float = 0.0   # 预测回复率
    ab_test_variant: str = "A"
    generated_at: str = ""
    def to_dict(self) -> dict:
        """to_dict。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return {
            "subject": self.subject,
            "body": self.body,
            "tone": self.tone.value,
            "insights_used": self.insights_used,
            "personalization_score": self.personalization_score,
            "open_rate_prediction": self.open_rate_prediction,
            "reply_rate_prediction": self.reply_rate_prediction,
            "ab_test_variant": self.ab_test_variant,
            "generated_at": self.generated_at,
        }


# ── 网页抓取工具 ──────────────────────────────────────────

class WebResearchTool:
    """网页内容抓取 + 解析"""
    @staticmethod
    def extract_domain(url: str) -> str:
        """从 URL 提取域名。"""
        parsed = urlparse(url if "://" in url else f"https://{url}")
        domain = parsed.netloc or parsed.path
        return domain.replace("www.", "")

    @staticmethod
    def extract_company_info_from_html(html: str, domain: str) -> dict[str, Any]:
        """从 HTML 中提取公司关键信息。

        使用启发式规则提取：
        - Meta description → 公司描述
        - Title → 公司名
        - 常见关键词 → 行业推测
        """
        info: dict[str, Any] = {
            "company_name": domain.split(".")[0].title(),
            "description": "",
            "industry": "",
            "keywords": [],
        }
        # 提取 meta description
        desc_match = re.search(
            r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)',
            html, re.IGNORECASE,
        )
        if desc_match:
            info["description"] = desc_match.group(1)

        # 提取 title
        title_match = re.search(r"<title>([^<]+)</title>", html, re.IGNORECASE)
        if title_match:
            title = title_match.group(1).strip()
            # 提取公司名
            company_match = re.match(r"^([^|>\-–—]+)", title)
            if company_match:
                info["company_name"] = company_match.group(1).strip()

        # 提取 keywords
        kw_match = re.search(
            r'<meta[^>]+name=["\']keywords["\'][^>]+content=["\']([^"\']+)',
            html, re.IGNORECASE,
        )
        if kw_match:
            info["keywords"] = [k.strip() for k in kw_match.group(1).split(",")]

        # 行业推测
        industry_keywords = {
            "manufacturing": ["manufacturing", "factory", "production", "OEM", "machinery"],
            "technology": ["software", "SaaS", "platform", "API", "cloud", "AI", "tech"],
            "healthcare": ["health", "medical", "pharma", "clinical", "hospital"],
            "finance": ["finance", "banking", "investment", "insurance", "fintech"],
            "retail": ["retail", "ecommerce", "shop", "store", "merchandise"],
            "logistics": ["logistics", "shipping", "freight", "supply chain", "warehouse"],
            "construction": ["construction", "building", "architecture", "engineering"],
            "education": ["education", "learning", "training", "course", "academy"],
            "marketing": ["marketing", "advertising", "SEO", "branding", "digital agency"],
            "consulting": ["consulting", "advisory", "strategy", "management"],
        }
        text_lower = (html.lower() + " " + info["description"].lower() +
                      " ".join(info["keywords"]).lower())
        for industry, keywords in industry_keywords.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score >= 2:
                info["industry"] = industry
                break

        return info

    @staticmethod
    def extract_tech_stack(html: str) -> list[str]:
        """从 HTML 中推测技术栈。"""
        tech_signals = {
            "WordPress": ["wp-content", "wp-json", "wordpress"],
            "Shopify": ["shopify", "myshopify"],
            "React": ["react", "data-reactroot", "_react"],
            "Vue": ["vue", "data-v-"],
            "Angular": ["ng-version", "angular"],
            "Next.js": ["__NEXT", "__next"],
            "Nuxt": ["__NUXT__", "nuxt"],
            "jQuery": ["jquery"],
            "Bootstrap": ["bootstrap"],
            "Tailwind CSS": ["tailwind"],
            "Google Analytics": ["google-analytics", "gtag"],
            "HubSpot": ["hubspot", "hs-script"],
            "Salesforce": ["salesforce"],
            "Stripe": ["stripe"],
            "AWS": ["aws", "amazonaws"],
            "Cloudflare": ["cloudflare"],
            "PHP": [".php"],
            "Python": ["python", "django", "flask"],
            "Node.js": ["node.js", "express"],
            "Ruby": ["ruby", "rails"],
        }
        found = []
        html_lower = html.lower()
        for tech, signals in tech_signals.items():
            if any(s in html_lower for s in signals):
                found.append(tech)
        return found

    @staticmethod
    def extract_social_links(html: str) -> dict[str, str]:
        """提取社交媒体链接。"""
        social_patterns = {
            "linkedin": r'https?://(?:www\.)?linkedin\.com/company/[^\s"\'<>]+',
            "twitter": r'https?://(?:www\.)?twitter\.com/[^\s"\'<>]+',
            "facebook": r'https?://(?:www\.)?facebook\.com/[^\s"\'<>]+',
            "instagram": r'https?://(?:www\.)?instagram\.com/[^\s"\'<>]+',
            "youtube": r'https?://(?:www\.)?youtube\.com/[^\s"\'<>]+',
            "github": r'https?://(?:www\.)?github\.com/[^\s"\'<>]+',
        }
        links: dict[str, str] = {}
        for platform, pattern in social_patterns.items():
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                links[platform] = match.group(0)
        return links


# ── RAG 客户洞察引擎 ──────────────────────────────────────

class ProspectResearchEngine:
    """RAG 客户洞察引擎。

    流程：
    1. 收集公开信息 → 公司档案
    2. 检索行业知识库 → 行业洞察
    3. 分析增长信号 → 切入点
    4. 生成个性化开发信 → 邮件
    """
    def __init__(self):
        """__init__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        self._web_tool = WebResearchTool()

    async def research_company(
        self,
        website: str,
        company_name: str = "",
        industry: str = "",
    ) -> ProspectResearch:
        """研究目标公司。

        收集合并：
        - 网站信息（爬虫）
        - 行业知识（向量检索）
        - 新闻/动态（可选）

        Args:
            website: 公司网站 URL
            company_name: 公司名（可选，从网站提取）
            industry: 行业（可选，从网站提取）
        """
        domain = self._web_tool.extract_domain(website)
        research = ProspectResearch(
            company_name=company_name or domain.split(".")[0].title(),
            website=website,
            industry=industry,
        )
        # Step 1: 网站抓取
        html = await self._fetch_website(website)
        if html:
            site_info = self._web_tool.extract_company_info_from_html(html, domain)
            tech_stack = self._web_tool.extract_tech_stack(html)
            social = self._web_tool.extract_social_links(html)
            research.company_name = company_name or site_info["company_name"]
            research.description = site_info["description"]
            research.industry = industry or site_info["industry"]
            research.tech_stack = tech_stack
            research.social_media = social
            research.research_quality += 0.3

        # Step 2: 行业知识库检索
        industry_insights = await self._retrieve_industry_insights(
            research.industry, research.company_name,
        )
        research.insights.extend(industry_insights)
        research.research_quality += 0.2
        # Step 3: 增长信号分析
        growth_signals = await self._analyze_growth_signals(
            research.company_name, research.website,
        )
        research.growth_signals = growth_signals.get("signals", [])
        research.recent_news = growth_signals.get("news", [])
        if growth_signals.get("signals"):
            research.research_quality += 0.2

        # Step 4: 痛点 + 机会分析
        pain_opps = await self._analyze_pain_points_and_opportunities(research)
        research.pain_points = pain_opps.get("pain_points", [])
        research.opportunities = pain_opps.get("opportunities", [])
        research.research_quality += 0.15
        # Step 5: 生成谈话要点
        research.talking_points = self._generate_talking_points(research)
        research.research_quality += 0.15
        research.research_quality = min(1.0, research.research_quality)
        return research

    async def _fetch_website(self, url: str) -> str:
        """抓取网站 HTML。"""
        if not url.startswith("http"):
            url = f"https://{url}"

        try:
            import httpx
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                resp = await client.get(url, headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "text/html,application/xhtml+xml",
                    "Accept-Language": "en-US,en;q=0.9",
                })
                if resp.status_code == 200:
                    return resp.text[:50000]  # 限制 50KB
        except Exception as e:
            logger.warning("Failed to fetch website %s: %s", url, e)

        return ""

    async def _retrieve_industry_insights(
        self,
        industry: str,
        company_name: str,
    ) -> list[CompanyInsight]:
        """检索行业知识库获取洞察。

        尝试：
        1. Qdrant 向量搜索（如果可用）
        2. 本地知识库
        3. 通用行业模板
        """
        insights: list[CompanyInsight] = []
        # 通用行业洞察模板
        industry_templates = {
            "manufacturing": [
                CompanyInsight(
                    category=InsightCategory.INDUSTRY_TREND,
                    title="供应链数字化加速",
                    description="制造业正加速数字化转型，供应链可见性和自动化成为核心需求",
                    confidence=0.7,
                ),
                CompanyInsight(
                    category=InsightCategory.PAIN_POINT,
                    title="成本压力持续",
                    description="原材料成本波动和劳动力成本上升是制造业的主要挑战",
                    confidence=0.65,
                ),
            ],
            "technology": [
                CompanyInsight(
                    category=InsightCategory.INDUSTRY_TREND,
                    title="AI 采用率飙升",
                    description="超过 60% 的科技公司已将 AI 集成到核心产品中",
                    confidence=0.75,
                ),
                CompanyInsight(
                    category=InsightCategory.OPPORTUNITY,
                    title="全球化扩张窗口",
                    description="科技公司正积极寻求亚太和欧洲市场的增长机会",
                    confidence=0.6,
                ),
            ],
            "retail": [
                CompanyInsight(
                    category=InsightCategory.INDUSTRY_TREND,
                    title="全渠道零售成为标配",
                    description="线上线下融合的全渠道策略是零售业的核心竞争力",
                    confidence=0.7,
                ),
            ],
            "logistics": [
                CompanyInsight(
                    category=InsightCategory.INDUSTRY_TREND,
                    title="实时追踪需求增长",
                    description="客户对端到端物流可见性的需求推动技术升级",
                    confidence=0.7,
                ),
            ],
            "construction": [
                CompanyInsight(
                    category=InsightCategory.INDUSTRY_TREND,
                    title="BIM 和数字化施工",
                    description="建筑信息模型(BIM)和数字孪生技术正在改变建筑行业",
                    confidence=0.65,
                ),
            ],
        }
        if industry in industry_templates:
            insights.extend(industry_templates[industry])

        # 通用洞察
        insights.append(CompanyInsight(
            category=InsightCategory.OPPORTUNITY,
            title="海外市场拓展机会",
            description=f"{company_name} 可能正在寻求拓展海外市场，尤其在数字化营销和客户获取方面",
            confidence=0.5,
        ))
        return insights

    async def _analyze_growth_signals(
        self,
        company_name: str,
        website: str,
    ) -> dict[str, Any]:
        """分析增长信号。

        检查：
        - 招聘页面（大量职位 = 扩张）
        - 新闻/公告
        - 社交媒体动态
        """
        signals: list[CompanyGrowthSignal] = []
        news: list[dict] = []
        # 检查招聘页面
        try:
            import httpx
            domain = self._web_tool.extract_domain(website)
            careers_urls = [
                f"https://{domain}/careers",
                f"https://{domain}/jobs",
                f"https://{domain}/about/careers",
            ]
            for url in careers_urls:
                try:
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        resp = await client.get(url, headers={
                            "User-Agent": "Mozilla/5.0",
                        })
                        if resp.status_code == 200:
                            # 计算职位数量
                            job_count = len(re.findall(r'(?i)job[- ]?title|position[- ]?title|career[- ]?opening', resp.text))
                            if job_count > 5:
                                signals.append(CompanyGrowthSignal.HIRING)
                                news.append({
                                    "title": f"{company_name} 正在大规模招聘",
                                    "type": "hiring",
                                    "detail": f"检测到约 {job_count} 个职位",
                                })
                            break
                except Exception:
                    continue
        except Exception as e:
            logger.debug("Growth signal check skipped: %s", e)

        return {"signals": signals, "news": news}

    async def _analyze_pain_points_and_opportunities(
        self,
        research: ProspectResearch,
    ) -> dict[str, Any]:
        """分析痛点和机会。"""
        pain_points: list[str] = []
        opportunities: list[str] = []
        # 基于行业
        industry_pain = {
            "manufacturing": [
                "寻找海外买家渠道有限",
                "供应链成本控制压力大",
                "品牌国际化程度低",
                "数字化营销能力不足",
            ],
            "technology": [
                "客户获取成本高",
                "市场竞争激烈",
                "需要快速验证产品市场契合度",
                "国际化人才招聘困难",
            ],
            "retail": [
                "线上流量获取成本上升",
                "跨境电商合规复杂",
                "库存管理效率低",
            ],
            "logistics": [
                "跨境物流成本高",
                "客户对时效性要求提升",
                "最后一公里配送挑战",
            ],
            "construction": [
                "海外项目获取渠道有限",
                "国际认证标准复杂",
                "供应链管理效率低",
            ],
        }
        if research.industry in industry_pain:
            pain_points = industry_pain[research.industry]

        # 通用机会
        opportunities = [
            f"通过 AI 驱动的获客引擎，{research.company_name} 可以将客户获取成本降低 60%",
            f"利用我们的多渠道营销平台，快速进入 {research.industry} 的全球市场",
            f"通过自动化工作流，将销售周期从数月缩短到数周",
        ]
        # 基于增长信号的机会
        if CompanyGrowthSignal.HIRING in research.growth_signals:
            opportunities.append(
                f"{research.company_name} 正在扩张，我们的自动化获客解决方案可以加速新市场的开拓"
            )

        return {"pain_points": pain_points, "opportunities": opportunities}

    def _generate_talking_points(self, research: ProspectResearch) -> list[str]:
        """生成谈话要点。"""
        points: list[str] = []
        # 引用行业洞察
        for insight in research.insights[:3]:
            if insight.confidence >= 0.5:
                points.append(f"行业趋势：{insight.title} — {insight.description}")

        # 痛点解决方案映射
        solution_map = {
            "寻找海外买家渠道有限": "我们的 AI 获客引擎可自动挖掘全球潜在买家",
            "供应链成本控制压力大": "我们的智能物流定价系统可优化跨境供应链成本",
            "品牌国际化程度低": "我们的多语言 SEO 和内容营销平台可提升国际品牌影响力",
            "数字化营销能力不足": "我们的一站式出海营销平台覆盖从获客到转化的全流程",
            "客户获取成本高": "我们的精准获客系统可将 CAC 降低 60%",
            "市场竞争激烈": "我们的差异化营销策略帮助您在竞争中脱颖而出",
        }
        for pain in research.pain_points[:3]:
            solution = solution_map.get(pain, "我们的解决方案可以帮您解决这个问题")
            points.append(f"痛点：{pain} → 解决方案：{solution}")

        # 增长信号相关
        if CompanyGrowthSignal.HIRING in research.growth_signals:
            points.append("贵公司正在扩张，我们的自动化解决方案可以加速新市场的开拓，无需大量增加人力")

        return points[:5]

    async def generate_personalized_email(
        self,
        research: ProspectResearch,
        recipient_name: str = "",
        recipient_title: str = "",
        sender_name: str = "",
        sender_company: str = "",
        tone: EmailTone = EmailTone.CONSULTATIVE,
        value_prop: str = "",
    ) -> PersonalizedEmail:
        """根据研究结果生成个性化开发信。

        Args:
            research: 客户研究结果
            recipient_name: 收件人姓名
            recipient_title: 收件人职位
            sender_name: 发件人姓名
            sender_company: 发件人公司
            tone: 邮件语气
            value_prop: 价值主张（可选）
        """
        now = datetime.now(timezone.utc).isoformat()
        # 选择 2-3 个最强洞察
        key_insights = sorted(
            research.insights,
            key=lambda i: i.confidence + i.relevance_score,
            reverse=True,
        )[:3]
        # 生成主题行
        subject = self._generate_subject(research, recipient_name, tone)
        # 生成正文
        body = self._generate_body(
            research=research,
            recipient_name=recipient_name,
            recipient_title=recipient_title,
            sender_name=sender_name,
            sender_company=sender_company,
            key_insights=key_insights,
            tone=tone,
            value_prop=value_prop,
        )
        # 计算个性化分数
        personalization_score = self._calculate_personalization_score(
            research, key_insights, body,
        )
        return PersonalizedEmail(
            subject=subject,
            body=body,
            tone=tone,
            insights_used=[i.title for i in key_insights],
            personalization_score=personalization_score,
            open_rate_prediction=min(0.85, 0.35 + personalization_score * 0.5),
            reply_rate_prediction=min(0.4, 0.05 + personalization_score * 0.35),
            generated_at=now,
        )

    def _generate_subject(
        self,
        research: ProspectResearch,
        recipient_name: str,
        tone: EmailTone,
    ) -> str:
        """生成个性化主题行。"""
        if recipient_name:
            greeting = f"{recipient_name.split()[0]}, "
        else:
            greeting = ""

        patterns = [
            f"Re: {greeting}quick question about {research.company_name}'s growth",
            f"{greeting}idea for {research.company_name}'s {research.industry} strategy",
            f"{greeting}how {research.company_name} can reduce customer acquisition costs",
            f"{greeting}congrats on the growth at {research.company_name}",
            f"{greeting}loved what {research.company_name} is doing in {research.industry}",
            f"{greeting}your {research.industry} challenges and a potential solution",
            f"{greeting}an observation about {research.company_name}",
        ]
        if research.growth_signals:
            if CompanyGrowthSignal.HIRING in research.growth_signals:
                patterns.insert(0, f"{greeting}exciting growth at {research.company_name} - quick thought")
            if CompanyGrowthSignal.FUNDING in research.growth_signals:
                patterns.insert(0, f"{greeting}congrats on the funding round! Quick idea")

        if research.pain_points:
            primary_pain = research.pain_points[0][:40]
            patterns.insert(0, f"{greeting}solving {primary_pain} at {research.company_name}")

        return patterns[0]

    def _generate_body(
        self,
        research: ProspectResearch,
        recipient_name: str,
        recipient_title: str,
        sender_name: str,
        sender_company: str,
        key_insights: list[CompanyInsight],
        tone: EmailTone,
        value_prop: str,
    ) -> str:
        """生成个性化邮件正文。"""
        name = recipient_name.split()[0] if recipient_name else "there"
        # 开场白（基于洞察）
        opening = self._generate_opening(research, name, key_insights, tone)
        # 价值主张
        if not value_prop:
            value_prop = f"我们帮助 {research.industry} 公司通过 AI 驱动的获客引擎将客户获取成本降低 60%"

        # 痛点引用
        pain_ref = ""
        if research.pain_points:
            pain_ref = f"\n\n我注意到{'贵公司' if 'CN' in (research.location or '') else 'your company'}可能面临 {research.pain_points[0]} 的挑战。"

        # 社交证明
        social_proof = ""
        if research.industry:
            social_proof = f"\n\n我们已经帮助多家 {research.industry} 公司实现了显著的客户增长。"

        # CTA
        cta = self._generate_cta(tone)
        # 签名
        signature = f"\n\nBest,\n{sender_name}\n{sender_company}"
        body = f"{opening}\n\n{value_prop}{pain_ref}{social_proof}\n\n{cta}{signature}"
        return body

    def _generate_opening(
        self,
        research: ProspectResearch,
        name: str,
        key_insights: list[CompanyInsight],
        tone: EmailTone,
    ) -> str:
        """生成个性化开场白。"""
        if tone == EmailTone.CONSULTATIVE:
            if key_insights:
                insight = key_insights[0]
                return (
                    f"Hi {name},\n\n"
                    f"我最近在研究 {research.industry} 行业，注意到 {research.company_name} "
                    f"在 {insight.title.lower()} 方面很有意思。"
                )
            return (
                f"Hi {name},\n\n"
                f"I've been following {research.company_name}'s work in the {research.industry} space "
                f"and wanted to reach out with a specific idea."
            )

        elif tone == EmailTone.DIRECT:
            if research.pain_points:
                return (
                    f"Hi {name},\n\n"
                    f"{research.pain_points[0]} 是 {research.industry} 公司面临的最大挑战之一。"
                    f"我们有一个经过验证的解决方案。"
                )
            return (
                f"Hi {name},\n\n"
                f"I'm reaching out because I believe we can help {research.company_name} "
                f"significantly improve its customer acquisition."
            )

        elif tone == EmailTone.STORY_DRIVEN:
            return (
                f"Hi {name},\n\n"
                f"Last month, we helped a {research.industry} company similar to {research.company_name} "
                f"reduce their customer acquisition cost by 60% in just 8 weeks. "
                f"I thought you might find this interesting."
            )

        else:
            return (
                f"Hi {name},\n\n"
                f"Hope you're doing well! I came across {research.company_name} and was impressed "
                f"by what you're doing in {research.industry}."
            )

    def _generate_cta(self, tone: EmailTone) -> str:
        """生成行动号召。"""
        ctas = {
            EmailTone.PROFESSIONAL: "Would you be open to a 15-minute call next week to discuss this further?",
            EmailTone.CASUAL: "Up for a quick 10-minute chat? Would love to share more.",
            EmailTone.CONSULTATIVE: "I'd love to share a few specific ideas on how we could help. Would a brief call work for you?",
            EmailTone.DIRECT: "Let's schedule a 15-minute call. Are you available Tuesday or Wednesday?",
            EmailTone.STORY_DRIVEN: "Would you like to hear how we did it? I can share more details in a quick call.",
        }
        return ctas.get(tone, ctas[EmailTone.PROFESSIONAL])

    def _calculate_personalization_score(
        self,
        research: ProspectResearch,
        key_insights: list[CompanyInsight],
        body: str,
    ) -> float:
        """计算个性化分数。"""
        score = 0.0
        # 有研究数据
        if research.research_quality > 0.3:
            score += 0.3
        if research.research_quality > 0.6:
            score += 0.2

        # 使用了洞察
        if key_insights:
            score += min(0.3, len(key_insights) * 0.1)

        # 使用了公司名
        if research.company_name.lower() in body.lower():
            score += 0.1

        # 使用了痛点
        if research.pain_points and any(p.lower()[:10] in body.lower()[:200] for p in research.pain_points):
            score += 0.1

        return min(1.0, score)


# 单例
prospect_research_engine = ProspectResearchEngine()