# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""AI 辅助搜索策略构建器 — FIX-60

智能搜索策略引擎：
1. 行业搜索模板库（自动匹配行业最佳搜索词）
2. 布尔搜索构建器（AND/OR/NOT 语法）
3. 多平台搜索策略（Google Dork / LinkedIn Sales / Hunter / Apollo）
4. 搜索词扩展（同义词/相关词/翻译）
5. 搜索结果去重 + 排序
6. 搜索策略优化建议
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


# ── 枚举 ──────────────────────────────────────────────────

class SearchPlatform(str, Enum):
    """搜索平台"""
    GOOGLE = "google"
    LINKEDIN = "linkedin"
    HUNTER = "hunter"
    APOLLO = "apollo"
    GOOGLE_DORK = "google_dork"  # Google Dork 高级搜索
    CUSTOM = "custom"


class SearchIntent(str, Enum):
    """搜索意图"""
    FIND_DECISION_MAKERS = "find_decision_makers"
    FIND_COMPANY = "find_company"
    FIND_EMAIL = "find_email"
    FIND_COMPETITORS = "find_competitors"
    MARKET_RESEARCH = "market_research"
    FIND_PARTNERS = "find_partners"


# ── 数据模型 ──────────────────────────────────────────────

@dataclass
class SearchQuery:
    """搜索查询"""
    platform: SearchPlatform
    query: str
    description: str = ""
    expected_results: int = 0
    difficulty: str = "medium"  # easy/medium/hard
    priority: int = 1           # 1-5
    def to_dict(self) -> dict:
        """to_dict。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return {
            "platform": self.platform.value,
            "query": self.query,
            "description": self.description,
            "expected_results": self.expected_results,
            "difficulty": self.difficulty,
            "priority": self.priority,
        }


@dataclass
class SearchStrategy:
    """搜索策略"""
    strategy_id: str
    industry: str = ""
    target_roles: list[str] = field(default_factory=list)
    target_countries: list[str] = field(default_factory=list)
    company_size: str = ""
    intent: SearchIntent = SearchIntent.FIND_DECISION_MAKERS
    queries: list[SearchQuery] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    expanded_keywords: list[str] = field(default_factory=list)
    total_estimated_leads: int = 0
    created_at: str = ""
    def to_dict(self) -> dict:
        """to_dict。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return {
            "strategy_id": self.strategy_id,
            "industry": self.industry,
            "target_roles": self.target_roles,
            "target_countries": self.target_countries,
            "company_size": self.company_size,
            "intent": self.intent.value,
            "queries": [q.to_dict() for q in self.queries],
            "keywords": self.keywords,
            "expanded_keywords": self.expanded_keywords[:20],
            "total_estimated_leads": self.total_estimated_leads,
            "created_at": self.created_at,
        }


# ── 行业搜索模板库 ────────────────────────────────────────

INDUSTRY_SEARCH_TEMPLATES: dict[str, dict] = {
    "manufacturing": {
        "keywords": [
            "manufacturing", "factory", "OEM", "ODM", "production",
            "machinery", "industrial", "assembly", "fabrication",
            "supply chain", "procurement", "sourcing",
        ],
        "roles": [
            "Purchasing Manager", "Procurement Director", "Supply Chain Manager",
            "Sourcing Manager", "Operations Director", "VP of Operations",
            "CEO", "COO", "General Manager", "Import Manager",
            "Quality Control Manager", "Production Manager",
        ],
        "google_dorks": [
            'site:linkedin.com/in "purchasing manager" "manufacturing"',
            'site:linkedin.com/in "procurement director" "manufacturing"',
            'intitle:"sourcing manager" "manufacturing"',
            '"supply chain" "director" site:linkedin.com/in',
        ],
        "linkedin_filters": {
            "industries": ["manufacturing", "industrial automation", "mechanical engineering"],
            "seniorities": ["Director", "VP", "Owner", "CXO", "Manager"],
        },
    },
    "technology": {
        "keywords": [
            "software", "SaaS", "platform", "technology", "IT", "cloud",
            "AI", "machine learning", "data", "digital", "automation",
            "API", "developer", "cybersecurity", "DevOps",
        ],
        "roles": [
            "CTO", "VP of Engineering", "VP of Product", "Head of IT",
            "CEO", "Director of Technology", "CIO", "Technical Director",
            "Engineering Manager", "Product Manager",
        ],
        "google_dorks": [
            'site:linkedin.com/in "CTO" "software"',
            'site:linkedin.com/in "VP of Engineering" "SaaS"',
            'intitle:"head of IT" "technology"',
            '"chief technology officer" site:linkedin.com/in',
        ],
        "linkedin_filters": {
            "industries": ["technology", "software development", "IT services"],
            "seniorities": ["Director", "VP", "CXO", "Owner"],
        },
    },
    "retail": {
        "keywords": [
            "retail", "ecommerce", "wholesale", "distribution",
            "merchandise", "buyer", "category manager", "retail chain",
            "direct-to-consumer", "DTC", "omnichannel",
        ],
        "roles": [
            "Buyer", "Category Manager", "Merchandising Director",
            "VP of Retail", "Head of Ecommerce", "Purchasing Director",
            "CEO", "Retail Director", "Import Manager",
        ],
        "google_dorks": [
            'site:linkedin.com/in "buyer" "retail"',
            'site:linkedin.com/in "category manager" "retail"',
            '"ecommerce director" site:linkedin.com/in',
        ],
        "linkedin_filters": {
            "industries": ["retail", "apparel", "luxury goods"],
            "seniorities": ["Director", "VP", "Manager", "Owner"],
        },
    },
    "logistics": {
        "keywords": [
            "logistics", "freight", "shipping", "supply chain",
            "warehouse", "transportation", "3PL", "forwarding",
            "customs", "import", "export", "cargo",
        ],
        "roles": [
            "Logistics Director", "Supply Chain Director", "Operations Manager",
            "Freight Manager", "Import/Export Manager", "Warehouse Manager",
            "CEO", "COO", "Transportation Manager",
        ],
        "google_dorks": [
            'site:linkedin.com/in "logistics director"',
            'site:linkedin.com/in "freight manager" "import"',
            '"supply chain director" site:linkedin.com/in',
        ],
        "linkedin_filters": {
            "industries": ["logistics", "transportation", "supply chain"],
            "seniorities": ["Director", "VP", "Manager", "Owner"],
        },
    },
    "construction": {
        "keywords": [
            "construction", "building", "contractor", "architecture",
            "engineering", "real estate", "development", "infrastructure",
            "civil engineering", "project management", "BIM",
        ],
        "roles": [
            "Project Director", "Construction Manager", "Procurement Manager",
            "CEO", "COO", "General Manager", "Chief Engineer",
            "Development Director", "Quantity Surveyor",
        ],
        "google_dorks": [
            'site:linkedin.com/in "construction manager" "procurement"',
            'site:linkedin.com/in "project director" "construction"',
            '"chief engineer" "construction" site:linkedin.com/in',
        ],
        "linkedin_filters": {
            "industries": ["construction", "civil engineering", "real estate"],
            "seniorities": ["Director", "VP", "Manager", "Owner"],
        },
    },
    "healthcare": {
        "keywords": [
            "healthcare", "medical", "pharmaceutical", "hospital",
            "clinic", "biotech", "health", "medical device",
            "diagnostics", "therapeutics",
        ],
        "roles": [
            "Chief Medical Officer", "Hospital Director", "Procurement Director",
            "CEO", "COO", "Head of Purchasing", "Medical Director",
            "VP of Operations", "Supply Chain Manager",
        ],
        "google_dorks": [
            'site:linkedin.com/in "chief medical officer"',
            'site:linkedin.com/in "hospital director" "procurement"',
            '"medical director" site:linkedin.com/in',
        ],
        "linkedin_filters": {
            "industries": ["healthcare", "medical practice", "pharmaceuticals"],
            "seniorities": ["Director", "VP", "CXO", "Owner"],
        },
    },
    "automotive": {
        "keywords": [
            "automotive", "auto parts", "vehicle", "car", "OEM",
            "tier 1", "tier 2", "aftermarket", "EV", "electric vehicle",
            "automotive supplier", "assembly",
        ],
        "roles": [
            "Purchasing Director", "Supply Chain Director", "VP of Procurement",
            "CEO", "COO", "Plant Manager", "Quality Director",
            "Sourcing Manager", "Commodity Manager",
        ],
        "google_dorks": [
            'site:linkedin.com/in "purchasing director" "automotive"',
            'site:linkedin.com/in "sourcing manager" "auto parts"',
            '"commodity manager" "automotive" site:linkedin.com/in',
        ],
        "linkedin_filters": {
            "industries": ["automotive", "motor vehicle manufacturing"],
            "seniorities": ["Director", "VP", "Manager", "CXO"],
        },
    },
}


# ── 关键词扩展器 ──────────────────────────────────────────

KEYWORD_EXPANSIONS: dict[str, list[str]] = {
    "buyer": ["purchaser", "procurement", "sourcing", "buying", "acquisition"],
    "manager": ["director", "head", "lead", "supervisor", "chief"],
    "director": ["VP", "head", "chief", "senior manager", "executive"],
    "import": ["importing", "overseas", "international", "global sourcing", "cross-border"],
    "export": ["exporting", "international trade", "overseas sales", "global"],
    "sourcing": ["procurement", "purchasing", "buying", "supply", "vendor management"],
    "supply chain": ["logistics", "procurement", "operations", "inventory", "distribution"],
    "sales": ["business development", "account management", "revenue", "commercial"],
    "marketing": ["brand", "digital marketing", "growth", "demand generation"],
    "CEO": ["chief executive", "president", "founder", "managing director", "owner"],
    "CTO": ["chief technology officer", "technical director", "head of engineering"],
    "CFO": ["chief financial officer", "finance director", "VP finance"],
    "manufacturing": ["production", "factory", "industrial", "fabrication", "assembly"],
    "technology": ["software", "IT", "tech", "digital", "SaaS", "platform"],
    "ecommerce": ["online retail", "digital commerce", "DTC", "marketplace"],
}


# ── 国家/地区搜索模板 ─────────────────────────────────────

COUNTRY_PATTERNS: dict[str, dict] = {
    "US": {"domain_tld": ".com", "linkedin_geo": "us", "linkedin_geo_id": "103644278"},
    "UK": {"domain_tld": ".co.uk", "linkedin_geo": "gb", "linkedin_geo_id": "101165590"},
    "DE": {"domain_tld": ".de", "linkedin_geo": "de", "linkedin_geo_id": "101282230"},
    "FR": {"domain_tld": ".fr", "linkedin_geo": "fr", "linkedin_geo_id": "105015875"},
    "JP": {"domain_tld": ".co.jp", "linkedin_geo": "jp", "linkedin_geo_id": "101355337"},
    "CN": {"domain_tld": ".cn", "linkedin_geo": "cn", "linkedin_geo_id": "102890883"},
    "IN": {"domain_tld": ".in", "linkedin_geo": "in", "linkedin_geo_id": "102713980"},
    "BR": {"domain_tld": ".com.br", "linkedin_geo": "br", "linkedin_geo_id": "106057199"},
    "AU": {"domain_tld": ".com.au", "linkedin_geo": "au", "linkedin_geo_id": "101452733"},
    "CA": {"domain_tld": ".ca", "linkedin_geo": "ca", "linkedin_geo_id": "101174742"},
    "IT": {"domain_tld": ".it", "linkedin_geo": "it", "linkedin_geo_id": "103350119"},
    "ES": {"domain_tld": ".es", "linkedin_geo": "es", "linkedin_geo_id": "105646813"},
    "NL": {"domain_tld": ".nl", "linkedin_geo": "nl", "linkedin_geo_id": "102890719"},
    "KR": {"domain_tld": ".co.kr", "linkedin_geo": "kr", "linkedin_geo_id": "104263586"},
    "MX": {"domain_tld": ".com.mx", "linkedin_geo": "mx", "linkedin_geo_id": "103685418"},
    "SG": {"domain_tld": ".com.sg", "linkedin_geo": "sg", "linkedin_geo_id": "102454443"},
    "AE": {"domain_tld": ".ae", "linkedin_geo": "ae", "linkedin_geo_id": "104262586"},
    "SA": {"domain_tld": ".com.sa", "linkedin_geo": "sa", "linkedin_geo_id": "103940692"},
}


# ── 智能搜索策略构建器 ────────────────────────────────────

class SearchStrategyBuilder:
    """AI 辅助搜索策略构建器"""
    def __init__(self):
        """__init__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        self._templates = INDUSTRY_SEARCH_TEMPLATES
        self._expansions = KEYWORD_EXPANSIONS
        self._countries = COUNTRY_PATTERNS

    def build_strategy(
        self,
        industry: str,
        target_roles: list[str] | None = None,
        target_countries: list[str] | None = None,
        company_size: str = "",
        intent: SearchIntent = SearchIntent.FIND_DECISION_MAKERS,
        custom_keywords: list[str] | None = None,
    ) -> SearchStrategy:
        """构建完整搜索策略。

        Args:
            industry: 目标行业
            target_roles: 目标职位列表
            target_countries: 目标国家列表
            company_size: 公司规模
            intent: 搜索意图
            custom_keywords: 自定义关键词

        Returns:
            完整的搜索策略
        """
        now = datetime.now(timezone.utc).isoformat()
        strategy_id = f"ss_{industry}_{intent.value}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M')}"
        # 获取行业模板
        template = self._templates.get(industry, self._templates.get("manufacturing", {}))
        base_keywords = template.get("keywords", [])
        base_roles = template.get("roles", [])
        # 合并关键词
        keywords = list(set(
            base_keywords +
            (custom_keywords or []) +
            (target_roles or [])
        ))
        # 扩展关键词
        expanded = self._expand_keywords(keywords)
        # 角色
        roles = target_roles or base_roles
        # 构建多平台查询
        queries: list[SearchQuery] = []
        # 1. Google Dork 查询
        if target_countries:
            for country in target_countries[:3]:
                country_info = self._countries.get(country, {})
                geo = country_info.get("linkedin_geo", "")
                for role in roles[:3]:
                    queries.append(SearchQuery(
                        platform=SearchPlatform.GOOGLE_DORK,
                        query=f'site:linkedin.com/in "{role.lower()}" "{industry}"',
                        description=f"在 LinkedIn 上搜索 {country} 的 {role}",
                        priority=5,
                        difficulty="easy",
                        expected_results=50,
                    ))
        else:
            for role in roles[:3]:
                queries.append(SearchQuery(
                    platform=SearchPlatform.GOOGLE_DORK,
                    query=f'site:linkedin.com/in "{role.lower()}" "{industry}"',
                    description=f"搜索 {role} 职位",
                    priority=5,
                    difficulty="easy",
                    expected_results=100,
                ))

        # 2. LinkedIn 搜索
        linkedin_filters = template.get("linkedin_filters", {})
        for role in roles[:5]:
            queries.append(SearchQuery(
                platform=SearchPlatform.LINKEDIN,
                query=f'"{role}" AND "{industry}"',
                description=f"LinkedIn Sales Navigator 搜索 {role}",
                priority=4,
                difficulty="easy",
                expected_results=200,
            ))

        # 3. Boolean 搜索
        boolean_queries = self._build_boolean_queries(roles, keywords, target_countries)
        for bq in boolean_queries:
            queries.append(SearchQuery(
                platform=SearchPlatform.GOOGLE,
                query=bq["query"],
                description=bq["desc"],
                priority=3,
                difficulty="medium",
                expected_results=100,
            ))

        # 4. Apollo/Hunter
        for role in roles[:3]:
            queries.append(SearchQuery(
                platform=SearchPlatform.APOLLO,
                query=f'title:"{role}" industry:"{industry}"',
                description=f"Apollo.io 搜索 {role}",
                priority=2,
                difficulty="easy",
                expected_results=150,
            ))

        # 估算总量
        total = sum(q.expected_results for q in queries)
        return SearchStrategy(
            strategy_id=strategy_id,
            industry=industry,
            target_roles=roles,
            target_countries=target_countries or [],
            company_size=company_size,
            intent=intent,
            queries=queries,
            keywords=keywords,
            expanded_keywords=expanded,
            total_estimated_leads=total,
            created_at=now,
        )

    def _expand_keywords(self, keywords: list[str]) -> list[str]:
        """扩展关键词（同义词/相关词）。"""
        expanded = set(keywords)
        for kw in keywords:
            kw_lower = kw.lower()
            if kw_lower in self._expansions:
                expanded.update(self._expansions[kw_lower])
        return list(expanded)

    def _build_boolean_queries(
        self,
        roles: list[str],
        keywords: list[str],
        countries: list[str] | None,
    ) -> list[dict]:
        """构建布尔搜索查询。"""
        queries = []
        # 基础查询：角色 AND 行业
        for role in roles[:3]:
            # 精确匹配
            role_terms = role.split()
            role_query = " AND ".join(f'"{t}"' for t in role_terms[:3])
            kw_terms = keywords[:5]
            kw_query = " OR ".join(f'"{k}"' for k in kw_terms)
            if countries:
                country_query = " OR ".join(f'"{c}"' for c in countries[:3])
                query = f'({role_query}) AND ({kw_query}) AND ({country_query})'
            else:
                query = f'({role_query}) AND ({kw_query})'

            queries.append({
                "query": query,
                "desc": f"布尔搜索: {role} 在 {', '.join(keywords[:3])} 行业",
            })

        # 排除查询（排除不相关结果）
        exclude_terms = ["job", "career", "hiring", "recruiter", "looking for"]
        exclude_query = " NOT ".join(f'"{e}"' for e in exclude_terms[:3])
        for role in roles[:2]:
            kw_terms = keywords[:3]
            kw_query = " OR ".join(f'"{k}"' for k in kw_terms)
            query = f'("{role}") AND ({kw_query}) NOT ({exclude_query})'
            queries.append({
                "query": query,
                "desc": f"排除招聘帖的布尔搜索: {role}",
            })

        return queries

    def build_google_dork(
        self,
        role: str,
        industry: str,
        country: str = "",
        exclude_terms: list[str] | None = None,
    ) -> str:
        """构建 Google Dork 高级搜索语法。

        Args:
            role: 目标职位
            industry: 行业
            country: 国家
            exclude_terms: 排除词
        """
        dork = f'site:linkedin.com/in "{role}" "{industry}"'
        if country:
            country_info = self._countries.get(country, {})
            geo = country_info.get("linkedin_geo", "")
            if geo:
                dork += f' location:"{country}"'

        if exclude_terms:
            for term in exclude_terms[:3]:
                dork += f' -"{term}"'

        # 添加文件类型过滤
        dork += ' -inurl:jobs -inurl:careers'
        return dork

    def build_linkedin_search_url(
        self,
        keywords: str = "",
        title: str = "",
        company: str = "",
        industry: str = "",
        country: str = "",
    ) -> str:
        """构建 LinkedIn Sales Navigator 搜索 URL。

        Args:
            keywords: 关键词
            title: 职位
            company: 公司
            industry: 行业
            country: 国家
        """
        base = "https://www.linkedin.com/sales/search/people?"
        params = []
        if keywords:
            params.append(f"keywords={keywords.replace(' ', '%20')}")
        if title:
            params.append(f"title={title.replace(' ', '%20')}")
        if company:
            params.append(f"company={company.replace(' ', '%20')}")
        if industry:
            params.append(f"industry={industry}")
        if country:
            country_info = self._countries.get(country, {})
            geo_id = country_info.get("linkedin_geo_id", "")
            if geo_id:
                params.append(f"geoRegion={geo_id}")

        return base + "&".join(params)

    def get_industry_insights(self, industry: str) -> dict[str, Any]:
        """获取行业搜索洞察。

        Args:
            industry: 行业名

        Returns:
            行业搜索建议
        """
        template = self._templates.get(industry, {})
        if not template:
            # 尝试模糊匹配
            for key in self._templates:
                if industry.lower() in key.lower() or key.lower() in industry.lower():
                    template = self._templates[key]
                    break

        if not template:
            return {"industry": industry, "found": False, "message": "未找到行业模板，请使用自定义关键词"}

        return {
            "industry": industry,
            "found": True,
            "recommended_roles": template.get("roles", []),
            "recommended_keywords": template.get("keywords", []),
            "sample_dorks": template.get("google_dorks", [])[:3],
            "linkedin_filters": template.get("linkedin_filters", {}),
        }

    def optimize_strategy(
        self,
        strategy: SearchStrategy,
        performance_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """优化搜索策略。

        基于历史表现数据给出优化建议。

        Args:
            strategy: 当前策略
            performance_data: 历史表现数据

        Returns:
            优化建议
        """
        suggestions = []
        # 查询数量建议
        if len(strategy.queries) < 5:
            suggestions.append("搜索查询数量偏少，建议增加到 10+ 条查询覆盖更多角度")
        elif len(strategy.queries) > 30:
            suggestions.append("查询数量过多，建议聚焦 10-15 条高质量查询")

        # 关键词多样性
        if len(set(strategy.keywords)) < 5:
            suggestions.append("关键词太少，建议添加同义词和相关词扩展搜索覆盖面")

        # 平台覆盖
        platforms = {q.platform for q in strategy.queries}
        if len(platforms) < 3:
            suggestions.append(f"只覆盖了 {len(platforms)} 个平台，建议增加 Google Dork + LinkedIn + Apollo")

        # 角色覆盖
        if len(strategy.target_roles) < 3:
            suggestions.append("目标角色太少，建议搜索 5-10 个相关职位")

        # 国家覆盖
        if not strategy.target_countries:
            suggestions.append("未指定目标国家，建议明确 3-5 个目标市场")

        return {
            "strategy_id": strategy.strategy_id,
            "suggestions": suggestions,
            "optimization_score": max(0, 100 - len(suggestions) * 15),
        }


# 单例
search_strategy_builder = SearchStrategyBuilder()