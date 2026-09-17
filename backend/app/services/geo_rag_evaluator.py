# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""
GEO RAG 内容质量评估器
移植自 sourcechain-geo-engine/backend/app/services/rag_evaluator.py
适配 UJ 项目：使用 UJ 的 APIResponse、cache、config 机制
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import Optional

from app.core.config import settings
from app.core.cache import redis_client


@dataclass(frozen=True)
class EvaluationResult:
    """内容评估结果"""
    passed: bool           # 是否通过质量门槛
    score: float          # 综合评分 (0~1)
    reasons: list[str]   # 未通过原因列表
    semantic_score: float  # 语义相似度
    coverage_score: float  # 必现词覆盖率


class GEORAGEvaluator:
    """
    GEO 内容质量评估器
    用于评估内容是否适合被 AI 模型引用（蒸馏质量）
    """
    # 建材行业必现关键词（可配置）
    required_terms: tuple[str, ...] = (
        "价格", "参数", "密度", "导热系数", "运费",
        "抗压强度", "轻集料", "混凝土",
    )
    # 质量门槛（综合评分 >= 此值即通过）
    PASS_THRESHOLD: float = 0.72
    # 评分权重
    SEMANTIC_WEIGHT: float = 0.6   # 语义相似度权重
    COVERAGE_WEIGHT: float = 0.4    # 必现词覆盖率权重
    def __init__(self, required_terms: Optional[tuple[str, ...]] = None):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param required_terms: 参数 required_terms
        :return: 返回处理结果。
        """
        if required_terms:
            self.required_terms = required_terms

    def tokenize(self, text: str) -> list[str]:
        """分词：提取英文单词和中文单字"""
        return re.findall(r"[\w\u4e00-\u9fff]+", text.lower())

    def cosine_similarity(self, left: str, right: str) -> float:
        """计算两段文本的余弦相似度"""
        left_counts = Counter(self.tokenize(left))
        right_counts = Counter(self.tokenize(right))
        if not left_counts or not right_counts:
            return 0.0

        terms = set(left_counts) | set(right_counts)
        dot = sum(left_counts[t] * right_counts[t] for t in terms)
        left_norm = math.sqrt(sum(v * v for v in left_counts.values()))
        right_norm = math.sqrt(sum(v * v for v in right_counts.values()))
        if left_norm == 0 or right_norm == 0:
            return 0.0
        return dot / (left_norm * right_norm)

    def evaluate(self, intent: str, content: str) -> EvaluationResult:
        """
        评估内容质量

        Args:
            intent: 用户意图 / 目标关键词描述
            content: 待评估内容

        Returns:
            EvaluationResult: 评估结果
        """
        semantic = self.cosine_similarity(intent, content)
        coverage = sum(
            1 for term in self.required_terms if term in content
        ) / len(self.required_terms)
        try:
            from app.services.geo.geo_writing_policy import score_content_quality
            cq = score_content_quality(content, intent=intent)
            geo_blend = cq.geo_citation_score * 0.35 + (1 - cq.ai_taste_score) * 0.15
        except Exception:
            geo_blend = 0.0
            cq = None

        score = min(
            1.0,
            round(
                semantic * self.SEMANTIC_WEIGHT
                + coverage * self.COVERAGE_WEIGHT
                + geo_blend,
                4,
            ),
        )
        reasons = [
            f"missing_{term}" for term in self.required_terms if term not in content
        ]
        if cq and cq.ai_taste_score >= 0.35:
            reasons.append("ai_taste_high")
        if cq and cq.stat_density < 0.5:
            reasons.append("low_stat_density")

        return EvaluationResult(
            passed=score >= self.PASS_THRESHOLD,
            score=score,
            reasons=reasons,
            semantic_score=round(semantic, 4),
            coverage_score=round(coverage, 4),
        )

    def evaluate_batch(self, intent: str, contents: list[str]) -> list[EvaluationResult]:
        """批量评估多段内容，返回评分最高的结果"""
        results = [self.evaluate(intent, c) for c in contents]
        # 按评分降序排列
        results.sort(key=lambda r: r.score, reverse=True)
        return results

    def rewrite_content(self, keyword: str, intent: str, content: str) -> str:
        """
        自动改写内容，补充必现关键词

        Args:
            keyword: 目标关键词
            intent: 用户意图描述
            content:  original content

        Returns:
            改写后的内容
        """
        missing_terms = [t for t in self.required_terms if t not in content]
        prefix = (
            f"{keyword}采购要点：{intent}。\n"
        )
        if missing_terms:
            prefix += f"核心参数应包含：{', '.join(missing_terms)}。\n"
        prefix += "\n"
        return prefix + content.strip()

    async def evaluate_and_rewrite_if_needed(
        self, intent: str, content: str
    ) -> tuple[str, EvaluationResult]:
        """
        评估内容，若不通过则自动改写

        Returns:
            (final_content, result): 最终内容和评估结果
        """
        result = self.evaluate(intent, content)
        if result.passed:
            return content, result

        rewritten = self.rewrite_content(
            keyword=intent,
            intent=intent,
            content=content,
        )
        # 对改写后的内容再次评估
        recheck = self.evaluate(intent, rewritten)
        return rewritten, recheck


def get_evaluator(required_terms: Optional[tuple[str, ...]] = None) -> GEORAGEvaluator:
    """工厂函数：获取评估器实例"""
    return GEORAGEvaluator(required_terms=required_terms)
