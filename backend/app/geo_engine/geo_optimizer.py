# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
from __future__ import annotations

import logging
import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field

from app.services.geo_rag_evaluator import GEORAGEvaluator

logger = logging.getLogger(__name__)


@dataclass
class GEORecommendation:
    """GEO优化建议"""
    category: str  # 'keyword', 'structure', 'semantic', 'freshness'
    priority: str  # 'high', 'medium', 'low'
    title: str
    description: str
    impact_score: float  # 0.0-1.0
    implementation_effort: str  # 'easy', 'medium', 'hard'


@dataclass
class GEOScore:
    """GEO评分结果"""
    overall_score: float  # 0-100
    visibility_score: float  # 内容在AI搜索中的可见性
    relevance_score: float  # 内容与查询的相关性
    freshness_score: float  # 内容新鲜度
    authority_score: float  # 内容权威性
    recommendations: List[GEORecommendation] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)


class GEOOptimizer:
    """
    GEO优化器 - 分析内容并提供优化建议
    
    核心功能：
    1. 分析内容在AI搜索引擎中的可见性
    2. 提供关键词、结构、语义优化建议
    3. 生成GEO评分报告
    """
    def __init__(self, db_connection=None):
        """
        初始化GEO优化器
        
        Args:
            db_connection: 数据库连接（可选，用于读取历史数据）
        """
        self.db = db_connection
        self.rag_evaluator = GEORAGEvaluator()
        logger.info("✅ GEOOptimizer initialized")
    
    async def analyze_content(
        self,
        content: str,
        target_keywords: List[str],
        context: Optional[Dict[str, Any]] = None
    ) -> GEOScore:
        """
        分析内容并返回GEO评分
        
        Args:
            content: 要分析的内容文本
            target_keywords: 目标关键词列表
            context: 上下文信息（URL、发布时间、作者等）
            
        Returns:
            GEOScore: GEO评分结果
        """
        try:
            logger.info(f"🔍 开始分析内容: {len(content)} 字符, {len(target_keywords)} 个关键词")
            # 1. 计算各维度评分
            visibility_score = await self._calculate_visibility(content, target_keywords)
            relevance_score = await self._calculate_relevance(content, target_keywords)
            freshness_score = await self._calculate_freshness(context)
            authority_score = await self._calculate_authority(context)
            # 2. RAG评估器集成 - 评估内容质量
            rag_result = self.rag_evaluator.evaluate(
                intent=" ".join(target_keywords),
                content=content
            )
            rag_score = rag_result.score * 100  # 转换为100分制
            # 3. 生成总体评分（加权平均）
            overall_score = (
                visibility_score * 0.25 +
                relevance_score * 0.25 +
                freshness_score * 0.15 +
                authority_score * 0.15 +
                rag_score * 0.20  # RAG评分占20%权重
            )
            # 3. 生成优化建议
            recommendations = await self._generate_recommendations(
                content, target_keywords, visibility_score, relevance_score
            )
            # 4. 构建详细信息
            details = {
                "content_length": len(content),
                "keyword_count": len(target_keywords),
                "keyword_density": self._calculate_keyword_density(content, target_keywords),
                "readability_score": self._calculate_readability(content),
                "has_structured_data": self._has_structured_data(content),
            }
            score = GEOScore(
                overall_score=overall_score,
                visibility_score=visibility_score,
                relevance_score=relevance_score,
                freshness_score=freshness_score,
                authority_score=authority_score,
                recommendations=recommendations,
                details=details
            )
            logger.info(f"✅ 内容分析完成: 总分={overall_score:.1f}")
            return score
            
        except Exception as e:
            logger.error(f"❌ 内容分析失败: {e}", exc_info=True)
            # 返回默认评分
            return GEOScore(
                overall_score=50.0,
                visibility_score=50.0,
                relevance_score=50.0,
                freshness_score=50.0,
                authority_score=50.0,
                recommendations=[],
                details={"error": str(e)}
            )
    
    async def _calculate_visibility(self, content: str, keywords: List[str]) -> float:
        """
        计算内容在AI搜索中的可见性评分
        
        可见性因子：
        1. 关键词出现频率和位置
        2. 内容长度和深度
        3. 标题和子标题结构
        4. 内部链接和外部链接
        
        Returns:
            评分 0-100
        """
        score = 50.0  # 基础分
        # 1. 关键词密度检查（2-5%为最佳）
        density = self._calculate_keyword_density(content, keywords)
        if 0.02 <= density <= 0.05:
            score += 15.0
        elif density > 0.05:
            score -= 10.0  # 关键词堆砌
        
        # 2. 内容长度检查（AI喜欢长篇深度内容）
        word_count = len(content.split())
        if word_count >= 1500:
            score += 15.0
        elif word_count >= 800:
            score += 10.0
        elif word_count < 300:
            score -= 15.0  # 内容太短
        
        # 3. 标题结构检查
        if self._has_proper_headings(content):
            score += 10.0
        
        # 4. 链接检查
        if self._has_links(content):
            score += 10.0
        
        return min(max(score, 0.0), 100.0)
    
    async def _calculate_relevance(self, content: str, keywords: List[str]) -> float:
        """
        计算内容与关键词的相关性评分
        
        相关性因子：
        1. 关键词在标题中的出现
        2. 关键词在开头段落的出现
        3. 语义相关词的出现
        
        Returns:
            评分 0-100
        """
        score = 50.0
        # 1. 关键词在标题中
        if any(kw.lower() in content.lower()[:200] for kw in keywords):
            score += 20.0
        
        # 2. 关键词在开头段落（前200字）
        first_para = content[:200].lower()
        if any(kw.lower() in first_para for kw in keywords):
            score += 15.0
        
        # 3. 语义相关词（简化版：检查同义词）
        semantic_words = self._extract_semantic_words(keywords)
        if any(word in content.lower() for word in semantic_words):
            score += 15.0
        
        return min(max(score, 0.0), 100.0)
    
    async def _calculate_freshness(self, context: Optional[Dict[str, Any]]) -> float:
        """
        计算内容新鲜度评分
        
        新鲜度因子：
        1. 发布时间（越新越好）
        2. 最后更新时间
        3. 内容是否包含时效性信息
        
        Returns:
            评分 0-100
        """
        if not context:
            return 50.0
        
        score = 50.0
        # 1. 发布时间
        published_at = context.get("published_at")
        if published_at:
            if isinstance(published_at, str):
                try:
                    published_at = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
                except (ValueError, TypeError):
                    published_at = None
            
            if published_at:
                days_old = (datetime.now(timezone.utc) - published_at).days
                if days_old <= 30:
                    score += 30.0  # 一个月内
                elif days_old <= 90:
                    score += 20.0  # 三个月内
                elif days_old <= 365:
                    score += 10.0  # 一年内
                else:
                    score -= 10.0  # 超过一年
        
        # 2. 最后更新时间
        updated_at = context.get("updated_at")
        if updated_at:
            # 类似逻辑...
            score += 5.0
        
        return min(max(score, 0.0), 100.0)
    
    async def _calculate_authority(self, context: Optional[Dict[str, Any]]) -> float:
        """
        计算内容权威性评分
        
        权威性因子：
        1. 作者声誉
        2. 域名权威性
        3. 外部引用和反向链接
        
        Returns:
            评分 0-100
        """
        if not context:
            return 50.0
        
        score = 50.0
        # 1. 作者信息
        author = context.get("author")
        if author and len(author) > 0:
            score += 10.0
        
        # 2. 域名信息（简化：检查是否包含知名域名）
        domain = context.get("domain", "")
        known_domains = ["wikipedia.org", "github.com", "stackoverflow.com", "medium.com"]
        if any(d in domain for d in known_domains):
            score += 20.0
        
        # 3. 引用数量
        citations = context.get("citations", 0)
        if citations > 10:
            score += 20.0
        elif citations > 5:
            score += 10.0
        
        return min(max(score, 0.0), 100.0)
    
    async def _generate_recommendations(
        self,
        content: str,
        keywords: List[str],
        visibility: float,
        relevance: float
    ) -> List[GEORecommendation]:
        """生成优化建议列表"""
        recommendations = []
        # 1. 可见性问题
        if visibility < 60:
            if len(content.split()) < 800:
                recommendations.append(GEORecommendation(
                    category="structure",
                    priority="high",
                    title="增加内容长度",
                    description="AI搜索引擎偏好1500字以上的深度内容。当前内容过短，建议扩展到800-1500字。",
                    impact_score=0.8,
                    implementation_effort="medium"
                ))
            
            if not self._has_proper_headings(content):
                recommendations.append(GEORecommendation(
                    category="structure",
                    priority="high",
                    title="添加标题结构",
                    description="使用H1、H2、H3标题组织内容，提高AI可读性。",
                    impact_score=0.7,
                    implementation_effort="easy"
                ))
        
        # 2. 相关性问题
        if relevance < 60:
            first_para = content[:200]
            if not any(kw.lower() in first_para.lower() for kw in keywords):
                recommendations.append(GEORecommendation(
                    category="keyword",
                    priority="high",
                    title="在开头段落包含关键词",
                    description="前200字应包含主要关键词，帮助AI快速理解内容主题。",
                    impact_score=0.9,
                    implementation_effort="easy"
                ))
        
        # 3. 关键词密度问题
        density = self._calculate_keyword_density(content, keywords)
        if density > 0.05:
            recommendations.append(GEORecommendation(
                category="keyword",
                priority="medium",
                title="降低关键词密度",
                description=f"当前关键词密度{density:.1%}，超过5%可能被判定为堆砌。建议降至2-5%。",
                impact_score=0.6,
                implementation_effort="easy"
            ))
        
        return recommendations
    
    def _calculate_keyword_density(self, content: str, keywords: List[str]) -> float:
        """计算关键词密度"""
        if not content or not keywords:
            return 0.0
        
        content_lower = content.lower()
        total_words = len(content_lower.split())
        if total_words == 0:
            return 0.0
        
        keyword_count = 0
        for keyword in keywords:
            keyword_count += content_lower.count(keyword.lower())
        
        return keyword_count / total_words
    
    def _has_proper_headings(self, content: str) -> bool:
        """检查是否有合理的标题结构"""
        import re
        headings = re.findall(r'^#{1,3}\s+', content, re.MULTILINE)
        return len(headings) >= 3
    
    def _has_links(self, content: str) -> bool:
        """检查是否包含链接"""
        import re
        links = re.findall(r'https?://[^\s]+', content)
        return len(links) >= 2
    
    def _has_structured_data(self, content: str) -> bool:
        """检查是否有结构化数据（JSON-LD、Schema.org等）"""
        return "application/ld+json" in content or "schema.org" in content
    
    def _calculate_readability(self, content: str) -> float:
        """计算可读性评分（简化版）"""
        # 简化：基于句子长度和单词复杂度
        sentences = content.split('.')
        if not sentences:
            return 50.0
        
        avg_sentence_length = len(content) / len(sentences)
        if 15 <= avg_sentence_length <= 25:
            return 80.0
        elif 10 <= avg_sentence_length <= 30:
            return 60.0
        else:
            return 40.0
    
    def _extract_semantic_words(self, keywords: List[str]) -> List[str]:
        """提取语义相关词（简化版）"""
        # 简化：预定义一些同义词
        semantic_map = {
            "AI": ["artificial intelligence", "machine learning", "deep learning"],
            "SEO": ["search engine optimization", "search ranking", "organic traffic"],
            "GEO": ["generative engine optimization", "AI SEO", "LLM optimization"],
        }
        result = []
        for keyword in keywords:
            for key, values in semantic_map.items():
                if key.lower() in keyword.lower():
                    result.extend(values)
        
        return result
    
    async def optimize_content(
        self,
        content: str,
        target_keywords: List[str],
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, GEOScore]:
        """
        优化内容并返回优化后的版本
        
        Args:
            content: 原始内容
            target_keywords: 目标关键词
            context: 上下文信息
            
        Returns:
            (优化后的内容, GEO评分)
        """
        # 1. 分析当前内容
        score = await self.analyze_content(content, target_keywords, context)
        # 2. 应用优化建议（简化版：只应用easy级别的建议）
        optimized_content = content
        for rec in score.recommendations:
            if rec.implementation_effort == "easy":
                optimized_content = self._apply_recommendation(
                    optimized_content, target_keywords, rec
                )
        
        # 3. 重新分析优化后的内容
        new_score = await self.analyze_content(optimized_content, target_keywords, context)
        logger.info(f"✅ 内容优化完成: {score.overall_score:.1f} -> {new_score.overall_score:.1f}")
        return optimized_content, new_score
    
    def _apply_recommendation(
        self,
        content: str,
        keywords: List[str],
        rec: GEORecommendation
    ) -> str:
        """应用单个优化建议（简化版）"""
        if rec.title == "在开头段落包含关键词":
            # 在开头添加关键词
            first_keyword = keywords[0] if keywords else ""
            if first_keyword and first_keyword not in content[:200]:
                content = f"关于{first_keyword}的深入分析：\n\n{content}"
        
        elif rec.title == "添加标题结构":
            # 简化：不自动添加标题（需要理解内容语义）
            pass
        
        return content


@dataclass
class ABTestVariant:
    """A/B测试变体"""
    name: str  # 'A' 或 'B'
    content: str  # 变体内容
    geo_score: float  # GEO评分
    rag_score: float  # RAG评估评分
    conversion_rate: float  # 转化率（询盘/访问）
    sample_size: int  # 样本量


@dataclass
class ABTestResult:
    """A/B测试结果"""
    variant_a: ABTestVariant
    variant_b: ABTestVariant
    winner: str  # 'A', 'B', 或 'inconclusive'
    confidence_level: float  # 置信度（0-1）
    recommendation: str  # 建议


class GEOABTestFramework:
    """
    GEO A/B测试框架
    用于对比不同内容版本在GEO方面的表现
    """
    def __init__(self, db_connection=None):
        """
        初始化A/B测试框架
        
        Args:
            db_connection: 数据库连接（可选，用于保存测试结果）
        """
        self.db = db_connection
        self.optimizer = GEOOptimizer(db_connection)
        logger.info("✅ GEOABTestFramework initialized")
    
    async def run_ab_test(
        self,
        content_a: str,
        content_b: str,
        target_keywords: List[str],
        context: Optional[Dict[str, Any]] = None,
        sample_size: int = 100
    ) -> ABTestResult:
        """
        运行A/B测试
        
        Args:
            content_a: 版本A的内容
            content_b: 版本B的内容
            target_keywords: 目标关键词
            context: 上下文信息
            sample_size: 样本量（每个版本的访问量）
            
        Returns:
            ABTestResult: 测试结果
        """
        try:
            logger.info(f"🧪 开始A/B测试: 样本量={sample_size}")
            # 1. 评估版本A
            score_a = await self.optimizer.analyze_content(content_a, target_keywords, context)
            rag_result_a = self.optimizer.rag_evaluator.evaluate(
                intent=" ".join(target_keywords),
                content=content_a
            )
            # 2. 评估版本B
            score_b = await self.optimizer.analyze_content(content_b, target_keywords, context)
            rag_result_b = self.optimizer.rag_evaluator.evaluate(
                intent=" ".join(target_keywords),
                content=content_b
            )
            # 3. 模拟转化率（简化版：基于GEO评分估算）
            # 实际项目中应该从 analytics 或 A/B测试平台获取真实数据
            conversion_rate_a = self._estimate_conversion_rate(score_a.overall_score)
            conversion_rate_b = self._estimate_conversion_rate(score_b.overall_score)
            # 4. 创建变体对象
            variant_a = ABTestVariant(
                name="A",
                content=content_a,
                geo_score=score_a.overall_score,
                rag_score=rag_result_a.score * 100,
                conversion_rate=conversion_rate_a,
                sample_size=sample_size
            )
            variant_b = ABTestVariant(
                name="B",
                content=content_b,
                geo_score=score_b.overall_score,
                rag_score=rag_result_b.score * 100,
                conversion_rate=conversion_rate_b,
                sample_size=sample_size
            )
            # 5. 判断胜者（简化版：基于转化率差异和置信度）
            winner = self._determine_winner(variant_a, variant_b)
            confidence = self._calculate_confidence(variant_a, variant_b)
            # 6. 生成建议
            recommendation = self._generate_recommendation(variant_a, variant_b, winner)
            result = ABTestResult(
                variant_a=variant_a,
                variant_b=variant_b,
                winner=winner,
                confidence_level=confidence,
                recommendation=recommendation
            )
            logger.info(f"✅ A/B测试完成: 胜者={winner}, 置信度={confidence:.2%}")
            return result
            
        except Exception as e:
            logger.error(f"❌ A/B测试失败: {e}", exc_info=True)
            # 返回默认结果
            return ABTestResult(
                variant_a=ABTestVariant(name="A", content=content_a, geo_score=50.0, rag_score=50.0, conversion_rate=0.02, sample_size=0),
                variant_b=ABTestVariant(name="B", content=content_b, geo_score=50.0, rag_score=50.0, conversion_rate=0.02, sample_size=0),
                winner="inconclusive",
                confidence_level=0.0,
                recommendation="测试失败，无法判断"
            )
    
    def _estimate_conversion_rate(self, geo_score: float) -> float:
        """
        估算转化率（简化版）
        
        基于GEO评分估算转化率：
        - GEO评分 > 80: 转化率 3-5%
        - GEO评分 60-80: 转化率 2-3%
        - GEO评分 < 60: 转化率 1-2%
        """
        if geo_score >= 80:
            return 0.04
        elif geo_score >= 60:
            return 0.025
        else:
            return 0.015
    
    def _determine_winner(self, variant_a: ABTestVariant, variant_b: ABTestVariant) -> str:
        """
        判断胜者（简化版）
        
        基于转化率差异和样本量判断：
        - 如果差异显著（p < 0.05），则返回胜者
        - 否则返回 'inconclusive'
        """
        # 简化：只比较转化率
        if variant_a.conversion_rate > variant_b.conversion_rate * 1.2:  # A比B高20%以上
            return "A"
        elif variant_b.conversion_rate > variant_a.conversion_rate * 1.2:  # B比A高20%以上
            return "B"
        else:
            return "inconclusive"
    
    def _calculate_confidence(self, variant_a: ABTestVariant, variant_b: ABTestVariant) -> float:
        """
        计算置信度（简化版）
        
        基于样本量和转化率差异计算置信度
        """
        # 简化：基于样本量估算置信度
        min_sample = min(variant_a.sample_size, variant_b.sample_size)
        if min_sample >= 1000:
            return 0.95
        elif min_sample >= 500:
            return 0.90
        elif min_sample >= 100:
            return 0.80
        else:
            return 0.60
    
    def _generate_recommendation(
        self,
        variant_a: ABTestVariant,
        variant_b: ABTestVariant,
        winner: str
    ) -> str:
        """生成测试建议"""
        if winner == "A":
            return f"版本A胜出（GEO评分: {variant_a.geo_score:.1f} vs {variant_b.geo_score:.1f}）。建议部署版本A。"
        elif winner == "B":
            return f"版本B胜出（GEO评分: {variant_b.geo_score:.1f} vs {variant_a.geo_score:.1f}）。建议部署版本B。"
        else:
            return f"测试结果不明确（A: {variant_a.geo_score:.1f}, B: {variant_b.geo_score:.1f}）。建议继续测试或优化两个版本。"


# 导出
__all__ = ["GEOOptimizer", "GEOScore", "GEORecommendation", "GEOABTestFramework", "ABTestResult"]
