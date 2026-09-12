"""线索评分引擎 v2 — FIX-36

多维加权评分模型，从以下维度评估线索质量：
1. 邮箱质量（30%）：是否验证通过、域名类型
2. 公司信息完整度（20%）：公司名、网站、行业
3. 职位匹配度（15%）：决策者 > 影响者 > 普通员工
4. 数据来源质量（15%）：LinkedIn > 官网 > 第三方
5. 活跃度信号（10%）：近期活动、社交存在
6. 地域匹配（10%）：目标市场匹配度

评分范围：0-100
- 80-100: 高价值线索（Hot）
- 60-79: 中等价值线索（Warm）
- 40-59: 低价值线索（Cool）
- 0-39: 冷线索（Cold）
"""

from __future__ import annotations

import logging
from enum import Enum
from typing import Any, Optional

log = logging.getLogger(__name__)


class LeadGrade(str, Enum):
    """线索等级。"""
    HOT = "hot"        # 80-100: 立即跟进
    WARM = "warm"      # 60-79: 本周内跟进
    COOL = "cool"      # 40-59: 加入培育序列
    COLD = "cold"      # 0-39: 低优先级


# 评分维度权重
SCORE_WEIGHTS = {
    "email_quality": 0.30,
    "company_completeness": 0.20,
    "title_match": 0.15,
    "source_quality": 0.15,
    "activity_signals": 0.10,
    "geo_match": 0.10,
}

# 职位关键词权重
TITLE_WEIGHTS = {
    # 决策者 - 最高权重
    "ceo": 100, "cto": 95, "cfo": 95, "cmo": 95, "coo": 95,
    "founder": 100, "owner": 100, "president": 95, "managing director": 95,
    "general manager": 90, "director": 85, "vp": 90, "vice president": 90,
    "head": 80, "chief": 95,
    # 影响者
    "manager": 70, "senior": 75, "lead": 65, "supervisor": 60,
    "team lead": 65, "principal": 70,
    # 采购/业务相关
    "procurement": 85, "purchasing": 85, "buyer": 80, "sourcing": 80,
    "supply chain": 75, "import": 80, "export": 80, "trade": 75,
    "merchandiser": 70, "sales": 60,
    # 技术相关
    "engineer": 50, "developer": 45, "architect": 55, "analyst": 50,
    "specialist": 50, "coordinator": 45, "assistant": 35,
    "intern": 20, "trainee": 20,
}

# 来源权重
SOURCE_WEIGHTS = {
    "linkedin": 100,
    "linkedin_sales_navigator": 95,
    "company_website": 85,
    "trade_show": 80,
    "referral": 90,
    "whatsapp": 70,
    "email_signature": 60,
    "web_scrape": 65,
    "csv_import": 50,
    "manual": 55,
    "unknown": 30,
    "b2b_platform": 75,
    "google_search": 60,
}

# 邮箱域名质量
EMAIL_DOMAIN_QUALITY = {
    "gmail.com": 70,
    "outlook.com": 65,
    "yahoo.com": 55,
    "hotmail.com": 55,
    "icloud.com": 60,
    "protonmail.com": 65,
    "aol.com": 40,
    "qq.com": 60,
    "163.com": 60,
    "126.com": 55,
    "sina.com": 55,
    "foxmail.com": 60,
    # 企业邮箱默认高分（在评分逻辑中处理）
}

# 目标市场国家权重
TARGET_MARKET_WEIGHTS = {
    "US": 100, "CA": 90, "GB": 90, "DE": 95, "FR": 90,
    "IT": 85, "ES": 85, "NL": 85, "BE": 80, "CH": 85,
    "AU": 90, "NZ": 80, "JP": 85, "KR": 80, "SG": 80,
    "AE": 85, "SA": 80, "QA": 80, "KW": 75,
    "BR": 75, "MX": 70, "AR": 65, "CL": 65,
    "IN": 60, "ID": 60, "VN": 55, "TH": 60, "PH": 55,
    "MY": 65, "ZA": 65, "NG": 50, "EG": 55,
    "RU": 50, "TR": 60, "PL": 70, "CZ": 70, "RO": 65,
    # 默认
    "DEFAULT": 50,
}


class LeadScoringEngine:
    """线索评分引擎 v2 — 多维加权模型。"""
    async def score(
        self,
        lead_data: dict[str, Any],
        verification_result: Optional[dict] = None,
    ) -> dict:
        """对线索进行评分。

        Args:
            lead_data: 标准化后的线索数据
            verification_result: 邮箱验证结果（可选）

        Returns:
            {"score": float, "grade": str, "breakdown": {...}}
        """
        scores = {}
        # 1. 邮箱质量评分（30%）
        scores["email_quality"] = self._score_email_quality(
            lead_data.get("email", ""),
            verification_result,
        )
        # 2. 公司信息完整度（20%）
        scores["company_completeness"] = self._score_company_completeness(lead_data)
        # 3. 职位匹配度（15%）
        scores["title_match"] = self._score_title_match(lead_data.get("title", ""))
        # 4. 数据来源质量（15%）
        scores["source_quality"] = self._score_source_quality(lead_data.get("source", "unknown"))
        # 5. 活跃度信号（10%）
        scores["activity_signals"] = self._score_activity_signals(lead_data)
        # 6. 地域匹配（10%）
        scores["geo_match"] = self._score_geo_match(lead_data.get("country", ""))
        # 加权计算总分
        total_score = sum(
            scores[dim] * weight
            for dim, weight in SCORE_WEIGHTS.items()
        )
        # 确定等级
        grade = self._determine_grade(total_score)
        return {
            "score": round(total_score, 1),
            "grade": grade.value,
            "grade_label": self._grade_label(grade),
            "breakdown": {
                dim: {
                    "score": round(s, 1),
                    "weight": round(w * 100),
                    "weighted": round(s * w, 1),
                }
                for dim, (s, w) in zip(
                    scores.keys(),
                    [(scores[dim], SCORE_WEIGHTS[dim]) for dim in scores],
                )
            },
        }

    def _score_email_quality(
        self, email: str, verification: Optional[dict] = None
    ) -> float:
        """邮箱质量评分。"""
        if not email:
            return 0

        score = 50.0  # 基础分
        # 验证结果加分
        if verification:
            if verification.get("verified"):
                score += 30
            if verification.get("disposable"):
                score -= 40
            if verification.get("role_account"):
                score -= 10

        # 域名质量
        domain = email.split("@")[-1].lower() if "@" in email else ""
        if domain in EMAIL_DOMAIN_QUALITY:
            score = EMAIL_DOMAIN_QUALITY[domain]
        elif domain and not any(
            free_domain in domain for free_domain in EMAIL_DOMAIN_QUALITY
        ):
            # 企业邮箱加分
            score = min(100, score + 20)

        # 格式检查
        if " " in email or ".." in email:
            score -= 30

        return max(0, min(100, score))

    def _score_company_completeness(self, lead_data: dict) -> float:
        """公司信息完整度评分。"""
        score = 0
        fields = {
            "company": 30,
            "website": 25,
            "industry": 20,
            "phone": 10,
            "linkedin_url": 15,
        }
        for field, weight in fields.items():
            if lead_data.get(field):
                score += weight

        return min(100, score)

    def _score_title_match(self, title: str) -> float:
        """职位匹配度评分。"""
        if not title:
            return 30  # 无职位信息给低分

        title_lower = title.lower()
        best_match = 0
        for keyword, weight in TITLE_WEIGHTS.items():
            if keyword in title_lower:
                best_match = max(best_match, weight)

        return float(best_match if best_match > 0 else 30)

    def _score_source_quality(self, source: str) -> float:
        """数据来源质量评分。"""
        source_lower = source.lower()
        return float(SOURCE_WEIGHTS.get(source_lower, 30))

    def _score_activity_signals(self, lead_data: dict) -> float:
        """活跃度信号评分。"""
        score = 50
        # LinkedIn URL 存在 → 社交活跃
        if lead_data.get("linkedin_url"):
            score += 20

        # 有手机号 → 可触达性高
        if lead_data.get("phone"):
            score += 10

        # 有网站 → 企业活跃
        if lead_data.get("website"):
            score += 10

        # 有完整姓名 → 信息完整
        if lead_data.get("first_name") and lead_data.get("last_name"):
            score += 10

        return min(100, score)

    def _score_geo_match(self, country: str) -> float:
        """地域匹配度评分。"""
        if not country:
            return float(TARGET_MARKET_WEIGHTS["DEFAULT"])

        country_upper = country.upper()
        return float(TARGET_MARKET_WEIGHTS.get(country_upper, TARGET_MARKET_WEIGHTS["DEFAULT"]))

    def _determine_grade(self, score: float) -> LeadGrade:
        """根据分数确定等级。"""
        if score >= 80:
            return LeadGrade.HOT
        elif score >= 60:
            return LeadGrade.WARM
        elif score >= 40:
            return LeadGrade.COOL
        return LeadGrade.COLD

    def _grade_label(self, grade: LeadGrade) -> str:
        """等级中文标签。"""
        labels = {
            LeadGrade.HOT: "高价值 - 立即跟进",
            LeadGrade.WARM: "中等价值 - 本周跟进",
            LeadGrade.COOL: "低价值 - 加入培育",
            LeadGrade.COLD: "冷线索 - 低优先级",
        }
        return labels.get(grade, "未知")


# 便捷函数
async def score_lead(
    lead_data: dict[str, Any],
    verification_result: Optional[dict] = None,
) -> dict:
    """快捷评分函数。"""
    engine = LeadScoringEngine()
    return await engine.score(lead_data, verification_result)