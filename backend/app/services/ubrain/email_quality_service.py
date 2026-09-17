# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""开发信质量评估 + A/B 测试 + 获客流程标准化 — FIX-58 & FIX-59

FIX-58: 开发信质量评估 + A/B 测试
  1. 多维度质量评分（主题行/正文/CTA/个性化/格式）
  2. A/B 测试框架（变体生成 + 流量分配 + 结果分析）
  3. 最佳实践检查清单
  4. 改进建议自动生成

FIX-59: 获客流程一致性（四步标准流程）
  1. 标准化四步流程：研究 → 触达 → 跟进 → 转化
  2. 阶段门控检查
  3. 流程审计
  4. 最佳实践模板
"""

from __future__ import annotations

import json
import logging
import math
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
# FIX-58: 开发信质量评估
# ═══════════════════════════════════════════════════════════

class EmailQualityDimension(str, Enum):
    """质量评估维度"""
    SUBJECT_LINE = "subject_line"         # 主题行
    BODY_CONTENT = "body_content"         # 正文内容
    PERSONALIZATION = "personalization"   # 个性化
    CTA = "cta"                          # 行动号召
    FORMAT = "format"                    # 格式
    SPAM_RISK = "spam_risk"              # 垃圾邮件风险
    VALUE_PROP = "value_prop"            # 价值主张
    READABILITY = "readability"          # 可读性


@dataclass
class QualityDimensionScore:
    """维度评分"""
    dimension: EmailQualityDimension
    score: float        # 0-10
    weight: float       # 0-1
    issues: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    def to_dict(self) -> dict:
        """to_dict。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return {
            "dimension": self.dimension.value,
            "score": round(self.score, 1),
            "weight": self.weight,
            "issues": self.issues,
            "suggestions": self.suggestions,
        }


@dataclass
class EmailQualityReport:
    """开发信质量报告"""
    email_subject: str
    email_body: str
    overall_score: float = 0.0          # 0-100
    grade: str = ""                      # A+ / A / B / C / D / F
    dimensions: list[QualityDimensionScore] = field(default_factory=list)
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    improvement_plan: list[str] = field(default_factory=list)
    # 预测指标
    predicted_open_rate: float = 0.0
    predicted_reply_rate: float = 0.0
    predicted_spam_rate: float = 0.0
    evaluated_at: str = ""
    def to_dict(self) -> dict:
        """to_dict。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return {
            "email_subject": self.email_subject,
            "email_body": self.email_body[:100],
            "overall_score": round(self.overall_score, 1),
            "grade": self.grade,
            "dimensions": [d.to_dict() for d in self.dimensions],
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "improvement_plan": self.improvement_plan,
            "predicted_open_rate": round(self.predicted_open_rate, 2),
            "predicted_reply_rate": round(self.predicted_reply_rate, 2),
            "predicted_spam_rate": round(self.predicted_spam_rate, 2),
            "evaluated_at": self.evaluated_at,
        }


# ── 质量评估器 ────────────────────────────────────────────

class EmailQualityEvaluator:
    """开发信质量评估器"""
    # 评分权重
    DIMENSION_WEIGHTS = {
        EmailQualityDimension.SUBJECT_LINE: 0.25,
        EmailQualityDimension.BODY_CONTENT: 0.25,
        EmailQualityDimension.PERSONALIZATION: 0.20,
        EmailQualityDimension.CTA: 0.10,
        EmailQualityDimension.FORMAT: 0.05,
        EmailQualityDimension.SPAM_RISK: 0.05,
        EmailQualityDimension.VALUE_PROP: 0.05,
        EmailQualityDimension.READABILITY: 0.05,
    }
    # 垃圾邮件关键词
    SPAM_KEYWORDS = [
        "free", "buy now", "act now", "limited time", "click here",
        "!!", "100% free", "best price", "cheap", "discount",
        "earn money", "guaranteed", "money back", "no obligation",
        "order now", "special promotion", "winner", "you won",
        "urgent", "exclusive deal", "once in a lifetime",
    ]
    # 强力 CTA 短语
    STRONG_CTAS = [
        "schedule a call", "book a demo", "let me know your thoughts",
        "would you be interested", "are you available",
        "I'd love to share", "let's discuss",
        "can I send you", "would you like to see",
    ]
    # 弱 CTA 短语
    WEAK_CTAS = [
        "let me know", "feel free to", "at your convenience",
        "whenever you have time", "no rush",
        "if you're interested", "maybe we could",
    ]
    def evaluate(self, subject: str, body: str, recipient_name: str = "") -> EmailQualityReport:
        """评估开发信质量。

        Args:
            subject: 主题行
            body: 邮件正文
            recipient_name: 收件人姓名（用于个性化评估）

        Returns:
            质量评估报告
        """
        now = datetime.now(timezone.utc).isoformat()
        dimensions: list[QualityDimensionScore] = []
        # 1. 主题行评分
        subj_score = self._evaluate_subject_line(subject)
        dimensions.append(subj_score)
        # 2. 正文内容评分
        body_score = self._evaluate_body_content(body)
        dimensions.append(body_score)
        # 3. 个性化评分
        pers_score = self._evaluate_personalization(body, recipient_name)
        dimensions.append(pers_score)
        # 4. CTA 评分
        cta_score = self._evaluate_cta(body)
        dimensions.append(cta_score)
        # 5. 格式评分
        fmt_score = self._evaluate_format(body)
        dimensions.append(fmt_score)
        # 6. 垃圾邮件风险
        spam_score = self._evaluate_spam_risk(subject, body)
        dimensions.append(spam_score)
        # 7. 价值主张
        vp_score = self._evaluate_value_prop(body)
        dimensions.append(vp_score)
        # 8. 可读性
        read_score = self._evaluate_readability(body)
        dimensions.append(read_score)
        # 计算加权总分
        overall = sum(
            d.score * 10 * d.weight
            for d in dimensions
        )
        # 收集强弱项
        strengths = []
        weaknesses = []
        improvement = []
        for d in dimensions:
            if d.score >= 8:
                strengths.append(f"{d.dimension.value}: {d.score}/10")
            elif d.score < 5:
                weaknesses.append(f"{d.dimension.value}: {d.score}/10")
                improvement.extend(d.suggestions[:2])

        # 评分等级
        grade = self._calculate_grade(overall)
        # 预测指标
        predicted_open = self._predict_open_rate(subj_score.score, pers_score.score)
        predicted_reply = self._predict_reply_rate(body_score.score, cta_score.score, pers_score.score)
        predicted_spam = self._predict_spam_rate(spam_score.score)
        return EmailQualityReport(
            email_subject=subject,
            email_body=body,
            overall_score=overall,
            grade=grade,
            dimensions=dimensions,
            strengths=strengths[:5],
            weaknesses=weaknesses[:5],
            improvement_plan=improvement[:5],
            predicted_open_rate=predicted_open,
            predicted_reply_rate=predicted_reply,
            predicted_spam_rate=predicted_spam,
            evaluated_at=now,
        )

    def _evaluate_subject_line(self, subject: str) -> QualityDimensionScore:
        """评估主题行。"""
        issues = []
        suggestions = []
        score = 5.0
        if not subject:
            return QualityDimensionScore(
                dimension=EmailQualityDimension.SUBJECT_LINE,
                score=0, weight=self.DIMENSION_WEIGHTS[EmailQualityDimension.SUBJECT_LINE],
                issues=["主题行为空"],
                suggestions=["必须写主题行"],
            )

        length = len(subject)
        # 长度检查
        if length < 10:
            score -= 2
            issues.append("主题行太短（<10 字符）")
            suggestions.append("主题行建议 30-50 字符")
        elif length < 20:
            score -= 0.5
        elif length > 80:
            score -= 1
            issues.append("主题行太长（>80 字符）")
            suggestions.append("主题行建议 30-50 字符，移动端显示约 40 字符")
        elif 30 <= length <= 60:
            score += 2

        # 个性化检查
        if "?" in subject:
            score += 1  # 问句主题行通常更好

        # 关键词检查
        spammy = any(kw in subject.lower() for kw in self.SPAM_KEYWORDS)
        if spammy:
            score -= 3
            issues.append("主题行包含垃圾邮件关键词")
            suggestions.append("避免使用 FREE、BUY NOW、限时 等词汇")

        # 个性化标记
        if "Re:" in subject:
            score += 1

        return QualityDimensionScore(
            dimension=EmailQualityDimension.SUBJECT_LINE,
            score=max(0, min(10, score)),
            weight=self.DIMENSION_WEIGHTS[EmailQualityDimension.SUBJECT_LINE],
            issues=issues,
            suggestions=suggestions,
        )

    def _evaluate_body_content(self, body: str) -> QualityDimensionScore:
        """评估正文内容。"""
        issues = []
        suggestions = []
        score = 5.0
        if not body:
            return QualityDimensionScore(
                dimension=EmailQualityDimension.BODY_CONTENT,
                score=0, weight=self.DIMENSION_WEIGHTS[EmailQualityDimension.BODY_CONTENT],
                issues=["正文为空"],
            )

        word_count = len(body.split())
        # 长度检查
        if word_count < 20:
            score -= 3
            issues.append("正文太短（<20 词）")
            suggestions.append("建议正文 50-150 词，足够表达价值又不冗长")
        elif word_count > 300:
            score -= 2
            issues.append("正文太长（>300 词）")
            suggestions.append("精简内容，保持 50-150 词")
        elif 50 <= word_count <= 200:
            score += 2

        # 段落结构
        paragraphs = [p.strip() for p in body.split("\n\n") if p.strip()]
        if len(paragraphs) < 2:
            score -= 1
            issues.append("缺少段落分隔")
            suggestions.append("使用 2-3 个段落，每段 1-2 句话")
        elif 2 <= len(paragraphs) <= 4:
            score += 1

        # 句子长度
        sentences = [s.strip() for s in re.split(r"[.!?]+", body) if s.strip()]
        if sentences:
            avg_words = sum(len(s.split()) for s in sentences) / len(sentences)
            if avg_words > 25:
                score -= 1
                issues.append("句子过长")
                suggestions.append("缩短句子，平均每句 10-20 词")

        return QualityDimensionScore(
            dimension=EmailQualityDimension.BODY_CONTENT,
            score=max(0, min(10, score)),
            weight=self.DIMENSION_WEIGHTS[EmailQualityDimension.BODY_CONTENT],
            issues=issues,
            suggestions=suggestions,
        )

    def _evaluate_personalization(self, body: str, recipient_name: str) -> QualityDimensionScore:
        """评估个性化程度。"""
        issues = []
        suggestions = []
        score = 3.0
        # 收件人姓名
        if recipient_name and recipient_name.lower() in body.lower():
            score += 3
        elif recipient_name:
            score += 1
            suggestions.append(f"在正文中提及收件人姓名 {recipient_name}")

        # 公司名
        company_patterns = [r"your company", r"贵公司", r"your team", r"your organization"]
        if any(re.search(p, body, re.IGNORECASE) for p in company_patterns):
            score += 1

        # 行业提及
        industry_keywords = ["industry", "sector", "field", "market", "space"]
        if any(kw in body.lower() for kw in industry_keywords):
            score += 1

        # 个性化占位符
        if "{{" in body or "{company}" in body.lower() or "{name}" in body.lower():
            score += 1
            suggestions.append("确保所有变量已被替换为实际值")

        # 泛泛而谈检测
        generic_phrases = ["I hope this email finds you well", "I am writing to",
                          "I would like to introduce", "We are a leading"]
        generic_count = sum(1 for p in generic_phrases if p.lower() in body.lower())
        if generic_count >= 2:
            score -= 2
            issues.append("使用了过多泛泛而谈的套话")
            suggestions.append("用具体的研究洞察替代通用开场白")

        return QualityDimensionScore(
            dimension=EmailQualityDimension.PERSONALIZATION,
            score=max(0, min(10, score)),
            weight=self.DIMENSION_WEIGHTS[EmailQualityDimension.PERSONALIZATION],
            issues=issues,
            suggestions=suggestions,
        )

    def _evaluate_cta(self, body: str) -> QualityDimensionScore:
        """评估行动号召（CTA）。"""
        issues = []
        suggestions = []
        score = 4.0
        body_lower = body.lower()
        # 是否有 CTA
        strong_cta_count = sum(1 for cta in self.STRONG_CTAS if cta in body_lower)
        weak_cta_count = sum(1 for cta in self.WEAK_CTAS if cta in body_lower)
        if strong_cta_count == 0 and weak_cta_count == 0:
            score -= 2
            issues.append("缺少明确的行动号召")
            suggestions.append("添加明确的 CTA，如 'Would you be open to a 15-minute call?'")
        elif strong_cta_count > 0:
            score += 3
        elif weak_cta_count > 0:
            score += 1
            suggestions.append("使用更明确的 CTA 替代模糊表达")

        # CTA 是否在结尾
        lines = body.strip().split("\n")
        if len(lines) >= 3:
            last_few = "\n".join(lines[-3:]).lower()
            if any(cta in last_few for cta in self.STRONG_CTAS + self.WEAK_CTAS):
                score += 2

        # 是否有多个 CTA（分散注意力）
        if strong_cta_count + weak_cta_count > 2:
            score -= 1
            issues.append("CTA 过多，分散注意力")
            suggestions.append("每封邮件只放一个主要 CTA")

        return QualityDimensionScore(
            dimension=EmailQualityDimension.CTA,
            score=max(0, min(10, score)),
            weight=self.DIMENSION_WEIGHTS[EmailQualityDimension.CTA],
            issues=issues,
            suggestions=suggestions,
        )

    def _evaluate_format(self, body: str) -> QualityDimensionScore:
        """评估格式。"""
        issues = []
        suggestions = []
        score = 7.0
        if not body:
            return QualityDimensionScore(
                dimension=EmailQualityDimension.FORMAT,
                score=0, weight=self.DIMENSION_WEIGHTS[EmailQualityDimension.FORMAT],
            )

        # HTML 检查
        if re.search(r"<[^>]+>", body):
            score -= 2
            issues.append("包含 HTML 标签")
            suggestions.append("使用纯文本格式（plain text emails 有更高的送达率）")

        # 链接检查
        urls = re.findall(r"https?://[^\s]+", body)
        if len(urls) > 3:
            score -= 1
            issues.append("链接过多")
            suggestions.append("减少链接数量，最多 1-2 个")

        # 图片检查
        if re.search(r"\[image\]|\[cid:|\.png|\.jpg|\.gif", body, re.IGNORECASE):
            score -= 1
            issues.append("包含图片引用")
            suggestions.append("避免在首次触达邮件中使用图片")

        return QualityDimensionScore(
            dimension=EmailQualityDimension.FORMAT,
            score=max(0, min(10, score)),
            weight=self.DIMENSION_WEIGHTS[EmailQualityDimension.FORMAT],
            issues=issues,
            suggestions=suggestions,
        )

    def _evaluate_spam_risk(self, subject: str, body: str) -> QualityDimensionScore:
        """评估垃圾邮件风险。"""
        issues = []
        suggestions = []
        score = 10.0
        text = (subject + " " + body).lower()
        # 垃圾关键词
        spam_count = sum(1 for kw in self.SPAM_KEYWORDS if kw.lower() in text)
        if spam_count > 0:
            score -= spam_count * 3
            issues.append(f"检测到 {spam_count} 个垃圾邮件关键词")
            suggestions.append("移除垃圾邮件关键词")

        # 全大写
        caps_ratio = sum(1 for c in text if c.isupper()) / max(1, len(text))
        if caps_ratio > 0.3:
            score -= 2
            issues.append("全大写比例过高")
            suggestions.append("避免过多全大写单词")

        # 感叹号
        exclamation_count = text.count("!")
        if exclamation_count > 3:
            score -= 2
            issues.append("感叹号过多")
            suggestions.append("减少感叹号使用")

        return QualityDimensionScore(
            dimension=EmailQualityDimension.SPAM_RISK,
            score=max(0, min(10, score)),
            weight=self.DIMENSION_WEIGHTS[EmailQualityDimension.SPAM_RISK],
            issues=issues,
            suggestions=suggestions,
        )

    def _evaluate_value_prop(self, body: str) -> QualityDimensionScore:
        """评估价值主张。"""
        issues = []
        suggestions = []
        score = 3.0
        body_lower = body.lower()
        # 价值主张信号
        vp_signals = [
            "help you", "improve", "increase", "reduce", "save",
            "grow", "optimize", "streamline", "automate",
            "ROI", "efficiency", "cost", "revenue", "growth",
            "we've helped", "clients", "results", "achieved",
        ]
        signal_count = sum(1 for s in vp_signals if s in body_lower)
        if signal_count >= 3:
            score += 4
        elif signal_count >= 1:
            score += 2

        # 具体数字
        if re.search(r"\d+%", body):
            score += 2
        if re.search(r"\$\d+", body):
            score += 1

        if signal_count == 0:
            issues.append("缺少明确的价值主张")
            suggestions.append("添加具体的数据和成果来支持你的价值主张")

        return QualityDimensionScore(
            dimension=EmailQualityDimension.VALUE_PROP,
            score=max(0, min(10, score)),
            weight=self.DIMENSION_WEIGHTS[EmailQualityDimension.VALUE_PROP],
            issues=issues,
            suggestions=suggestions,
        )

    def _evaluate_readability(self, body: str) -> QualityDimensionScore:
        """评估可读性。"""
        score = 6.0
        issues = []
        suggestions = []
        if not body:
            return QualityDimensionScore(
                dimension=EmailQualityDimension.READABILITY,
                score=0, weight=self.DIMENSION_WEIGHTS[EmailQualityDimension.READABILITY],
            )

        # Flesch-Kincaid 简化版
        sentences = [s.strip() for s in re.split(r"[.!?]+", body) if s.strip()]
        words = body.split()
        syllables = self._count_syllables(body)
        if sentences and words:
            avg_words_per_sentence = len(words) / len(sentences)
            avg_syllables_per_word = syllables / len(words)
            if 10 <= avg_words_per_sentence <= 20:
                score += 1
            elif avg_words_per_sentence > 25:
                score -= 1
                suggestions.append("缩短句子，提高可读性")

            if avg_syllables_per_word < 1.8:
                score += 1

        return QualityDimensionScore(
            dimension=EmailQualityDimension.READABILITY,
            score=max(0, min(10, score)),
            weight=self.DIMENSION_WEIGHTS[EmailQualityDimension.READABILITY],
            issues=issues,
            suggestions=suggestions,
        )

    @staticmethod
    def _count_syllables(text: str) -> int:
        """简化版音节计数。"""
        count = 0
        for word in text.split():
            word = word.lower().strip(".,!?;:()")
            if not word:
                continue
            syllables = len(re.findall(r"[aeiouy]+", word))
            if word.endswith("e") and syllables > 1:
                syllables -= 1
            count += max(1, syllables)
        return count

    @staticmethod
    def _calculate_grade(score: float) -> str:
        """_calculate_grade。

        参数说明：
        :param score: 参数 score
        :return: 返回处理结果。
        """
        if score >= 90:
            return "A+"
        elif score >= 80:
            return "A"
        elif score >= 70:
            return "B"
        elif score >= 60:
            return "C"
        elif score >= 50:
            return "D"
        return "F"

    @staticmethod
    def _predict_open_rate(subject_score: float, personalization_score: float) -> float:
        """_predict_open_rate。

        参数说明：
        :param subject_score: 参数 subject_score
        :param personalization_score: 参数 personalization_score
        :return: 返回处理结果。
        """
        base = 0.25
        return min(0.85, base + subject_score * 0.04 + personalization_score * 0.03)

    @staticmethod
    def _predict_reply_rate(body_score: float, cta_score: float, pers_score: float) -> float:
        """_predict_reply_rate。

        参数说明：
        :param body_score: 参数 body_score
        :param cta_score: 参数 cta_score
        :param pers_score: 参数 pers_score
        :return: 返回处理结果。
        """
        base = 0.05
        return min(0.50, base + body_score * 0.02 + cta_score * 0.03 + pers_score * 0.02)

    @staticmethod
    def _predict_spam_rate(spam_score: float) -> float:
        """_predict_spam_rate。

        参数说明：
        :param spam_score: 参数 spam_score
        :return: 返回处理结果。
        """
        return max(0.01, 0.30 - spam_score * 0.03)


# ── A/B 测试框架 ──────────────────────────────────────────

class ABTestVariant(str, Enum):
    A = "A"
    B = "B"


@dataclass
class ABTestConfig:
    """A/B 测试配置"""
    test_id: str
    variant_a_subject: str
    variant_a_body: str
    variant_b_subject: str
    variant_b_body: str
    test_variable: str = ""           # 测试变量描述
    traffic_split: float = 0.5        # B 变体流量比例
    min_sample_size: int = 100        # 最小样本量
    status: str = "draft"
    created_at: str = ""
    def to_dict(self) -> dict:
        """to_dict。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return {
            "test_id": self.test_id,
            "variant_a": {"subject": self.variant_a_subject, "body": self.variant_a_body[:100]},
            "variant_b": {"subject": self.variant_b_subject, "body": self.variant_b_body[:100]},
            "test_variable": self.test_variable,
            "traffic_split": self.traffic_split,
            "min_sample_size": self.min_sample_size,
            "status": self.status,
        }


@dataclass
class ABTestResult:
    """A/B 测试结果"""
    test_id: str
    variant_a_opens: int = 0
    variant_a_replies: int = 0
    variant_a_sent: int = 0
    variant_b_opens: int = 0
    variant_b_replies: int = 0
    variant_b_sent: int = 0
    winner: str = ""                    # "A" / "B" / "tie"
    confidence: float = 0.0             # 统计置信度
    open_lift: float = 0.0              # 打开率提升
    reply_lift: float = 0.0             # 回复率提升
    recommendation: str = ""
    def to_dict(self) -> dict:
        """to_dict。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return {
            "test_id": self.test_id,
            "variant_a": {
                "sent": self.variant_a_sent,
                "opens": self.variant_a_opens,
                "replies": self.variant_a_replies,
                "open_rate": round(self.variant_a_opens / max(1, self.variant_a_sent) * 100, 1),
                "reply_rate": round(self.variant_a_replies / max(1, self.variant_a_sent) * 100, 1),
            },
            "variant_b": {
                "sent": self.variant_b_sent,
                "opens": self.variant_b_opens,
                "replies": self.variant_b_replies,
                "open_rate": round(self.variant_b_opens / max(1, self.variant_b_sent) * 100, 1),
                "reply_rate": round(self.variant_b_replies / max(1, self.variant_b_sent) * 100, 1),
            },
            "winner": self.winner,
            "confidence": round(self.confidence, 2),
            "open_lift": round(self.open_lift * 100, 1),
            "reply_lift": round(self.reply_lift * 100, 1),
            "recommendation": self.recommendation,
        }


class ABTestEngine:
    """A/B 测试引擎"""
    @staticmethod
    def create_test(
        test_id: str,
        variant_a_subject: str,
        variant_a_body: str,
        variant_b_subject: str,
        variant_b_body: str,
        test_variable: str = "",
        traffic_split: float = 0.5,
        min_sample_size: int = 100,
    ) -> ABTestConfig:
        """create_test。

        参数说明：
        :param test_id: 参数 test_id
        :param variant_a_subject: 参数 variant_a_subject
        :param variant_a_body: 参数 variant_a_body
        :param variant_b_subject: 参数 variant_b_subject
        :param variant_b_body: 参数 variant_b_body
        :param test_variable: 参数 test_variable
        :param traffic_split: 参数 traffic_split
        :param min_sample_size: 参数 min_sample_size
        :return: 返回处理结果。
        """
        return ABTestConfig(
            test_id=test_id,
            variant_a_subject=variant_a_subject,
            variant_a_body=variant_a_body,
            variant_b_subject=variant_b_subject,
            variant_b_body=variant_b_body,
            test_variable=test_variable,
            traffic_split=traffic_split,
            min_sample_size=min_sample_size,
            status="active",
            created_at=datetime.now(timezone.utc).isoformat(),
        )

    @staticmethod
    def analyze_results(
        test_id: str,
        a_sent: int, a_opens: int, a_replies: int,
        b_sent: int, b_opens: int, b_replies: int,
    ) -> ABTestResult:
        """分析 A/B 测试结果。

        使用简化版统计检验判断显著性。
        """
        result = ABTestResult(
            test_id=test_id,
            variant_a_opens=a_opens,
            variant_a_replies=a_replies,
            variant_a_sent=a_sent,
            variant_b_opens=b_opens,
            variant_b_replies=b_replies,
            variant_b_sent=b_sent,
        )
        a_open_rate = a_opens / max(1, a_sent)
        b_open_rate = b_opens / max(1, b_sent)
        a_reply_rate = a_replies / max(1, a_sent)
        b_reply_rate = b_replies / max(1, b_sent)
        result.open_lift = (b_open_rate - a_open_rate) / max(0.001, a_open_rate)
        result.reply_lift = (b_reply_rate - a_reply_rate) / max(0.001, a_reply_rate)
        # 简化显著性检验
        total = a_sent + b_sent
        if total >= 100:
            # 使用 z-test 近似
            p_pool = (a_opens + b_opens) / max(1, total)
            se = math.sqrt(p_pool * (1 - p_pool) * (1 / max(1, a_sent) + 1 / max(1, b_sent)))
            z = (b_open_rate - a_open_rate) / max(0.001, se)
            result.confidence = min(0.99, max(0.5, 0.5 + abs(z) * 0.15))

        # 判断赢家
        if result.confidence >= 0.95 and result.open_lift > 0.05:
            result.winner = "B"
            result.recommendation = "B 变体在打开率上显著优于 A，建议全量切换"
        elif result.confidence >= 0.95 and result.open_lift < -0.05:
            result.winner = "A"
            result.recommendation = "A 变体在打开率上显著优于 B，保持 A 变体"
        elif result.reply_lift > 0.1:
            result.winner = "B"
            result.recommendation = "B 变体在回复率上明显更好，建议切换"
        elif result.reply_lift < -0.1:
            result.winner = "A"
            result.recommendation = "A 变体在回复率上明显更好，保持 A 变体"
        else:
            result.winner = "tie"
            if total < 200:
                result.recommendation = "样本量不足，需要更多数据才能判断"
            else:
                result.recommendation = "两个变体差异不显著，可任选其一或测试新变体"

        return result

    @staticmethod
    def generate_variants(
        base_subject: str,
        base_body: str,
        variable: str = "subject_line",
    ) -> dict[str, tuple[str, str]]:
        """生成 A/B 变体。

        Args:
            base_subject: 基础主题行
            base_body: 基础正文
            variable: 测试变量

        Returns:
            {"A": (subject, body), "B": (subject, body)}
        """
        variants = {
            "A": (base_subject, base_body),
        }
        if variable == "subject_line":
            # 变体 B：不同角度
            alt_subject = base_subject
            if "?" in base_subject:
                alt_subject = base_subject.replace("?", " - quick thought?")
            elif "Re:" in base_subject:
                alt_subject = base_subject.replace("Re:", "Re: quick follow-up -")
            else:
                alt_subject = f"Quick thought about {base_subject[:30]}"

            variants["B"] = (alt_subject, base_body)

        elif variable == "cta":
            # 变体 B：不同的 CTA
            alt_body = base_body.replace(
                "Would you be open to a 15-minute call",
                "I can send you a 2-minute video overview"
            )
            variants["B"] = (base_subject, alt_body)

        elif variable == "opening":
            # 变体 B：故事化开场
            lines = base_body.split("\n")
            if len(lines) > 2:
                lines[1] = "Last week, we helped a company like yours reduce their CAC by 60% in just 8 weeks."
                variants["B"] = (base_subject, "\n".join(lines))

        return variants


# ═══════════════════════════════════════════════════════════
# FIX-59: 获客流程标准化
# ═══════════════════════════════════════════════════════════

class OutreachStage(str, Enum):
    """获客四阶段"""
    RESEARCH = "research"        # 1. 研究
    OUTREACH = "outreach"        # 2. 触达
    FOLLOW_UP = "follow_up"      # 3. 跟进
    CONVERT = "convert"          # 4. 转化


class StageGateStatus(str, Enum):
    """阶段门控状态"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StageGate:
    """阶段门控检查"""
    stage: OutreachStage
    checklist: list[dict] = field(default_factory=list)  # [{item, passed, note}]
    status: StageGateStatus = StageGateStatus.NOT_STARTED
    required_actions: list[str] = field(default_factory=list)
    completed_at: str = ""
    def to_dict(self) -> dict:
        """to_dict。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return {
            "stage": self.stage.value,
            "checklist": self.checklist,
            "status": self.status.value,
            "required_actions": self.required_actions,
            "completed_at": self.completed_at,
        }


@dataclass
class OutreachWorkflow:
    """获客工作流"""
    lead_id: str
    lead_name: str = ""
    lead_company: str = ""
    current_stage: OutreachStage = OutreachStage.RESEARCH
    gates: list[StageGate] = field(default_factory=list)
    overall_progress: float = 0.0  # 0-100
    started_at: str = ""
    updated_at: str = ""
    def to_dict(self) -> dict:
        """to_dict。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return {
            "lead_id": self.lead_id,
            "lead_name": self.lead_name,
            "lead_company": self.lead_company,
            "current_stage": self.current_stage.value,
            "gates": [g.to_dict() for g in self.gates],
            "overall_progress": round(self.overall_progress, 1),
            "started_at": self.started_at,
            "updated_at": self.updated_at,
        }


class OutreachWorkflowEngine:
    """获客流程引擎"""
    # 四阶段标准检查清单
    STAGE_CHECKLISTS = {
        OutreachStage.RESEARCH: [
            {"item": "公司网站已抓取", "category": "data"},
            {"item": "行业/规模已确认", "category": "data"},
            {"item": "至少 3 个决策人已识别", "category": "target"},
            {"item": "增长信号/痛点已分析", "category": "insight"},
            {"item": "个性化开发信已准备", "category": "prepare"},
        ],
        OutreachStage.OUTREACH: [
            {"item": "邮箱已验证", "category": "data"},
            {"item": "发送时间已优化（时区）", "category": "timing"},
            {"item": "开发信质量评分 >=70", "category": "quality"},
            {"item": "追踪像素已嵌入", "category": "tracking"},
            {"item": "无垃圾邮件关键词", "category": "compliance"},
        ],
        OutreachStage.FOLLOW_UP: [
            {"item": "跟进策略已选择", "category": "strategy"},
            {"item": "多渠道协同计划已制定", "category": "strategy"},
            {"item": "上次交互结果已记录", "category": "data"},
            {"item": "停止条件已检查", "category": "compliance"},
            {"item": "跟进内容已个性化", "category": "quality"},
        ],
        OutreachStage.CONVERT: [
            {"item": "客户兴趣已确认", "category": "qualify"},
            {"item": "会议/演示已安排", "category": "action"},
            {"item": "CRM 已更新", "category": "data"},
            {"item": "交接文档已准备", "category": "handoff"},
            {"item": "后续跟进计划已建立", "category": "next_steps"},
        ],
    }
    def create_workflow(
        self,
        lead_id: str,
        lead_name: str = "",
        lead_company: str = "",
    ) -> OutreachWorkflow:
        """创建标准化获客工作流。"""
        now = datetime.now(timezone.utc).isoformat()
        gates = []
        for stage in OutreachStage:
            checklist = [
                {"item": item["item"], "passed": False, "note": ""}
                for item in self.STAGE_CHECKLISTS[stage]
            ]
            gates.append(StageGate(
                stage=stage,
                checklist=checklist,
                status=StageGateStatus.NOT_STARTED,
            ))

        # 第一个阶段自动开始
        gates[0].status = StageGateStatus.IN_PROGRESS
        return OutreachWorkflow(
            lead_id=lead_id,
            lead_name=lead_name,
            lead_company=lead_company,
            current_stage=OutreachStage.RESEARCH,
            gates=gates,
            overall_progress=0.0,
            started_at=now,
            updated_at=now,
        )

    def check_stage_gate(
        self,
        workflow: OutreachWorkflow,
        stage: OutreachStage,
    ) -> tuple[bool, list[str]]:
        """检查阶段门控条件。

        Returns:
            (是否通过, 未通过项列表)
        """
        gate = next((g for g in workflow.gates if g.stage == stage), None)
        if not gate:
            return False, ["阶段不存在"]

        all_passed = all(item["passed"] for item in gate.checklist)
        failed = [
            item["item"]
            for item in gate.checklist
            if not item["passed"]
        ]
        return all_passed, failed

    def advance_stage(
        self,
        workflow: OutreachWorkflow,
        checklist_results: dict[str, bool] | None = None,
    ) -> OutreachWorkflow:
        """推进到下一阶段。

        Args:
            workflow: 当前工作流
            checklist_results: {检查项: 是否通过}

        Returns:
            更新后的工作流
        """
        now = datetime.now(timezone.utc).isoformat()
        # 更新当前阶段检查清单
        current_gate = next(
            (g for g in workflow.gates if g.stage == workflow.current_stage), None
        )
        if current_gate and checklist_results:
            for item in current_gate.checklist:
                if item["item"] in checklist_results:
                    item["passed"] = checklist_results[item["item"]]

        # 检查是否通过
        all_passed, _ = self.check_stage_gate(workflow, workflow.current_stage)
        if all_passed and current_gate:
            current_gate.status = StageGateStatus.PASSED
            current_gate.completed_at = now
            # 推进到下一阶段
            stage_order = list(OutreachStage)
            current_idx = stage_order.index(workflow.current_stage)
            if current_idx < len(stage_order) - 1:
                workflow.current_stage = stage_order[current_idx + 1]
                next_gate = workflow.gates[current_idx + 1]
                next_gate.status = StageGateStatus.IN_PROGRESS

        # 计算进度
        passed_gates = sum(1 for g in workflow.gates if g.status == StageGateStatus.PASSED)
        workflow.overall_progress = (passed_gates / len(workflow.gates)) * 100
        workflow.updated_at = now
        return workflow

    def audit_workflow(self, workflow: OutreachWorkflow) -> dict[str, Any]:
        """审计工作流合规性。"""
        issues = []
        warnings = []
        for gate in workflow.gates:
            failed_items = [item["item"] for item in gate.checklist if not item["passed"]]
            if failed_items and gate.status == StageGateStatus.IN_PROGRESS:
                warnings.append(f"{gate.stage.value}: 还有 {len(failed_items)} 项未完成")
            elif failed_items and gate.status == StageGateStatus.PASSED:
                issues.append(f"{gate.stage.value}: 标记为已通过但 {len(failed_items)} 项未完成")

        return {
            "workflow_id": workflow.lead_id,
            "current_stage": workflow.current_stage.value,
            "progress": workflow.overall_progress,
            "issues": issues,
            "warnings": warnings,
            "healthy": len(issues) == 0,
        }

    def get_best_practices(self, stage: OutreachStage) -> list[str]:
        """获取阶段最佳实践。"""
        practices = {
            OutreachStage.RESEARCH: [
                "使用 RAG 引擎深度研究客户，至少收集 3 个具体洞察",
                "识别客户公司的增长信号（招聘/融资/扩张），找准切入时机",
                "研究客户竞争对手，理解市场定位",
                "了解客户的技术栈，准备技术相关的价值主张",
                "在 LinkedIn 上关注目标客户，建立初步社交触点",
            ],
            OutreachStage.OUTREACH: [
                "个性化程度决定打开率——每封邮件必须包含至少 1 个客户专属洞察",
                "最佳发送时间：周二到周四上午 8-10 点（目标时区）",
                "主题行 30-50 字符，避免垃圾邮件关键词",
                "纯文本格式优于 HTML 格式",
                "每封邮件只放一个明确的 CTA",
            ],
            OutreachStage.FOLLOW_UP: [
                "无响应 3 天后第一次跟进，换角度不换价值",
                "已打开 2 天后跟进，聚焦价值主张",
                "第 3 次跟进尝试切换渠道（LinkedIn/WhatsApp）",
                "告别邮件给客户一个简单的台阶（'Should I stop reaching out?'）",
                "每次跟进必须有新信息，不要重复同样内容",
            ],
            OutreachStage.CONVERT: [
                "客户回复后 4 小时内响应",
                "第一次通话目标：了解需求，不是推销",
                "发送会议邀请时包含议程和预期时长",
                "每次互动后 24 小时内更新 CRM",
                "建立 30-60-90 天后续跟进计划",
            ],
        }
        return practices.get(stage, [])


# 单例
email_quality_evaluator = EmailQualityEvaluator()
ab_test_engine = ABTestEngine()
outreach_workflow_engine = OutreachWorkflowEngine()