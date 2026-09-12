"""AI推荐系统服务 - 协同过滤与内容推荐算法"""

import logging
import numpy as np
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

from app.core.logging_config import LogConfig
from app.services.ai_engine import AIEngine
from app.models.product import Product
from app.models.user import User
from app.models.inquiry import Inquiry

logger = LogConfig.get_logger("ai_recommendation_service")


class RecommendationService:
    """AI推荐系统服务
    
    实现协同过滤、内容推荐等算法，使用AI生成推荐解释。
    """
    def __init__(self):
        """__init__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        self.ai_engine = AIEngine()
        logger.info("RecommendationService initialized")

    # ==================== 协同过滤算法 ====================
    def collaborative_filtering_user_based(
        self, 
        user_id: str,
        user_item_matrix: Dict[str, Dict[str, float]],
        n_neighbors: int = 10,
        n_recommendations: int = 10
    ) -> List[Tuple[str, float]]:
        """基于用户的协同过滤
        
        Args:
            user_id: 目标用户ID
            user_item_matrix: 用户-物品交互矩阵 {user_id: {item_id: rating}}
            n_neighbors: 邻居数量
            n_recommendations: 推荐数量
            
        Returns:
            List[Tuple[str, float]]: 推荐物品列表 [(item_id, score), ...]
        """
        if user_id not in user_item_matrix:
            return []
        
        # 计算用户相似度
        user_ratings = user_item_matrix[user_id]
        similarities = {}
        for other_user_id, other_ratings in user_item_matrix.items():
            if other_user_id == user_id:
                continue
            
            # 计算皮尔逊相关系数
            similarity = self._pearson_correlation(user_ratings, other_ratings)
            if similarity > 0:  # 只保留正相关的用户
                similarities[other_user_id] = similarity
        
        # 选择最相似的N个邻居
        top_neighbors = sorted(similarities.items(), key=lambda x: x[1], reverse=True)[:n_neighbors]
        # 预测评分
        item_scores = defaultdict(float)
        item_weights = defaultdict(float)
        for neighbor_id, similarity in top_neighbors:
            neighbor_ratings = user_item_matrix[neighbor_id]
            for item_id, rating in neighbor_ratings.items():
                if item_id not in user_ratings:  # 只推荐未交互的物品
                    item_scores[item_id] += similarity * rating
                    item_weights[item_id] += similarity
        
        # 归一化评分
        recommendations = []
        for item_id, score in item_scores.items():
            if item_weights[item_id] > 0:
                normalized_score = score / item_weights[item_id]
                recommendations.append((item_id, normalized_score))
        
        # 排序并返回Top N
        recommendations.sort(key=lambda x: x[1], reverse=True)
        return recommendations[:n_recommendations]

    def collaborative_filtering_item_based(
        self,
        user_id: str,
        user_item_matrix: Dict[str, Dict[str, float]],
        n_recommendations: int = 10
    ) -> List[Tuple[str, float]]:
        """基于物品的协同过滤
        
        Args:
            user_id: 目标用户ID
            user_item_matrix: 用户-物品交互矩阵
            n_recommendations: 推荐数量
            
        Returns:
            List[Tuple[str, float]]: 推荐物品列表
        """
        if user_id not in user_item_matrix:
            return []
        
        user_ratings = user_item_matrix[user_id]
        # 计算物品相似度矩阵（简化版，实际应使用预计算的物品相似度）
        item_similarities = self._calculate_item_similarities(user_item_matrix)
        # 基于用户历史交互预测评分
        item_scores = defaultdict(float)
        for item_id, rating in user_ratings.items():
            if item_id not in item_similarities:
                continue
            
            for similar_item_id, similarity in item_similarities[item_id].items():
                if similar_item_id not in user_ratings:  # 未交互的物品
                    item_scores[similar_item_id] += rating * similarity
        
        # 排序并返回Top N
        recommendations = sorted(item_scores.items(), key=lambda x: x[1], reverse=True)
        return recommendations[:n_recommendations]

    # ==================== 内容推荐算法 ====================
    def content_based_filtering(
        self,
        user_id: str,
        user_profile: Dict[str, float],
        item_features: Dict[str, Dict[str, float]],
        n_recommendations: int = 10
    ) -> List[Tuple[str, float]]:
        """基于内容的推荐
        
        Args:
            user_id: 目标用户ID
            user_profile: 用户画像 {feature: weight}
            item_features: 物品特征 {item_id: {feature: value}}
            n_recommendations: 推荐数量
            
        Returns:
            List[Tuple[str, float]]: 推荐物品列表
        """
        # 计算用户画像与物品特征的余弦相似度
        recommendations = []
        for item_id, features in item_features.items():
            similarity = self._cosine_similarity(user_profile, features)
            recommendations.append((item_id, similarity))
        
        # 排序并返回Top N
        recommendations.sort(key=lambda x: x[1], reverse=True)
        return recommendations[:n_recommendations]

    def hybrid_recommendation(
        self,
        user_id: str,
        user_item_matrix: Dict[str, Dict[str, float]],
        item_features: Dict[str, Dict[str, float]],
        weights: Tuple[float, float] = (0.5, 0.5),
        n_recommendations: int = 10
    ) -> List[Tuple[str, float]]:
        """混合推荐（协同过滤 + 内容推荐）
        
        Args:
            user_id: 目标用户ID
            user_item_matrix: 用户-物品交互矩阵
            item_features: 物品特征
            weights: (协同过滤权重, 内容推荐权重)
            n_recommendations: 推荐数量
            
        Returns:
            List[Tuple[str, float]]: 推荐物品列表
        """
        # 协同过滤推荐
        cf_recs = self.collaborative_filtering_user_based(
            user_id, user_item_matrix, n_recommendations=n_recommendations*2
        )
        # 内容推荐（需要用户画像，这里简化使用用户历史交互作为画像）
        user_profile = self._build_user_profile_from_history(user_id, user_item_matrix, item_features)
        cb_recs = self.content_based_filtering(
            user_id, user_profile, item_features, n_recommendations=n_recommendations*2
        )
        # 合并推荐结果
        combined_scores = defaultdict(float)
        for item_id, score in cf_recs:
            combined_scores[item_id] += weights[0] * score
        
        for item_id, score in cb_recs:
            combined_scores[item_id] += weights[1] * score
        
        # 排序并返回Top N
        recommendations = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
        return recommendations[:n_recommendations]

    # ==================== AI推荐解释 ====================
    async def generate_recommendation_explanation(
        self,
        user_id: str,
        item_id: str,
        item_name: str,
        user_history: List[str],
        reason: str
    ) -> str:
        """使用AI生成推荐解释
        
        Args:
            user_id: 用户ID
            item_id: 物品ID
            item_name: 物品名称
            user_history: 用户历史交互物品名称列表
            reason: 推荐原因（协同过滤/内容推荐等）
            
        Returns:
            str: AI生成的推荐解释
        """
        if not self.ai_engine.is_available():
            return f"根据您的浏览历史，为您推荐{item_name}"
        
        prompt = f"""请生成一段友好的推荐解释，说明为什么向用户推荐这个产品。

用户信息：
- 用户ID: {user_id}
- 历史浏览: {', '.join(user_history[:5])}

推荐产品：{item_name}
推荐算法：{reason}

要求：
1. 语言友好、自然
2. 突出产品与用户兴趣的关联
3. 不超过50字
4. 不要使用"根据协同过滤"等技术术语"""

        try:
            response = await self.ai_engine.generate(
                prompt=prompt,
                model="general",
                task_complexity="simple"
            )
            return response.get("content", "").strip()
        except Exception as e:
            logger.error(f"生成推荐解释失败: {e}")
            return f"根据您的浏览历史，为您推荐{item_name}"

    # ==================== 辅助方法 ====================
    def _pearson_correlation(
        self, 
        ratings1: Dict[str, float], 
        ratings2: Dict[str, float]
    ) -> float:
        """计算皮尔逊相关系数"""
        common_items = set(ratings1.keys()) & set(ratings2.keys())
        if len(common_items) < 2:
            return 0.0
        
        # 提取共同评分
        ratings1_common = [ratings1[item] for item in common_items]
        ratings2_common = [ratings2[item] for item in common_items]
        # 计算相关系数
        correlation_matrix = np.corrcoef(ratings1_common, ratings2_common)
        return correlation_matrix[0, 1]

    def _cosine_similarity(
        self, 
        vec1: Dict[str, float], 
        vec2: Dict[str, float]
    ) -> float:
        """计算余弦相似度"""
        # 获取所有特征
        all_features = set(vec1.keys()) | set(vec2.keys())
        # 构建向量
        vec1_array = [vec1.get(f, 0.0) for f in all_features]
        vec2_array = [vec2.get(f, 0.0) for f in all_features]
        # 计算余弦相似度
        dot_product = sum(a * b for a, b in zip(vec1_array, vec2_array))
        norm1 = sum(a * a for a in vec1_array) ** 0.5
        norm2 = sum(b * b for b in vec2_array) ** 0.5
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)

    def _calculate_item_similarities(
        self, 
        user_item_matrix: Dict[str, Dict[str, float]]
    ) -> Dict[str, Dict[str, float]]:
        """计算物品相似度矩阵（简化版）"""
        # 构建物品-用户矩阵
        item_users = defaultdict(dict)
        for user_id, ratings in user_item_matrix.items():
            for item_id, rating in ratings.items():
                item_users[item_id][user_id] = rating
        
        # 计算物品相似度
        item_similarities = defaultdict(dict)
        items = list(item_users.keys())
        for i, item1 in enumerate(items):
            for item2 in items[i+1:]:
                similarity = self._cosine_similarity(item_users[item1], item_users[item2])
                item_similarities[item1][item2] = similarity
                item_similarities[item2][item1] = similarity
        
        return dict(item_similarities)

    def _build_user_profile_from_history(
        self,
        user_id: str,
        user_item_matrix: Dict[str, Dict[str, float]],
        item_features: Dict[str, Dict[str, float]]
    ) -> Dict[str, float]:
        """从用户历史交互构建用户画像"""
        if user_id not in user_item_matrix:
            return {}
        
        user_ratings = user_item_matrix[user_id]
        profile = defaultdict(float)
        # 加权平均物品特征
        total_weight = 0.0
        for item_id, rating in user_ratings.items():
            if item_id in item_features:
                for feature, value in item_features[item_id].items():
                    profile[feature] += rating * value
                total_weight += rating
        
        # 归一化
        if total_weight > 0:
            for feature in profile:
                profile[feature] /= total_weight
        
        return dict(profile)


# 全局推荐服务实例
recommendation_service = RecommendationService()
