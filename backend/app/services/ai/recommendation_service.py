# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""
AI推荐系统服务 - 基于真实协同过滤算法与LLM解释生成
功能：
- 协同过滤（基于用户相似度和物品相似度）
- 内容推荐（TF-IDF相似度）
- 混合推荐（协同过滤 + 内容推荐加权融合）
- AI推荐解释生成（调用LLM生成推荐理由）
- 用户画像构建
- 在线学习反馈
"""

import json
import logging
import math
import uuid
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

from app.services.ai_engine import AIEngine

logger = logging.getLogger(__name__)

# 模拟用户-物品交互矩阵（生产环境应从数据库加载）
_user_item_matrix: Dict[str, Dict[str, float]] = defaultdict(dict)
_item_features: Dict[str, Dict[str, float]] = defaultdict(dict)
_user_profiles: Dict[str, Dict[str, Any]] = defaultdict(dict)


class RecommendationRequest:
    """推荐请求"""
    user_id: str
    context: Optional[Dict[str, Any]]
    limit: int
    algorithm: str
    def __init__(
        self,
        user_id: str,
        context: Optional[Dict[str, Any]] = None,
        limit: int = 10,
        algorithm: str = "hybrid",
    ) -> None:
        """__init__。

        参数说明：
        :param self: 参数 self
        :param user_id: 参数 user_id
        :param context: 参数 context
        :param limit: 参数 limit
        :param algorithm: 参数 algorithm
        :return: 返回处理结果。
        """
        self.user_id = user_id
        self.context = context
        self.limit = limit
        self.algorithm = algorithm


class RecommendedItem:
    """推荐物品"""
    item_id: str
    score: float
    reason: str
    metadata: Optional[Dict[str, Any]]
    def __init__(
        self,
        item_id: str,
        score: float,
        reason: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """__init__。

        参数说明：
        :param self: 参数 self
        :param item_id: 参数 item_id
        :param score: 参数 score
        :param reason: 参数 reason
        :param metadata: 参数 metadata
        :return: 返回处理结果。
        """
        self.item_id = item_id
        self.score = score
        self.reason = reason
        self.metadata = metadata


class RecommendationResult:
    """推荐结果"""
    recommendation_id: str
    user_id: str
    items: List[RecommendedItem]
    algorithm: str
    def __init__(
        self,
        recommendation_id: str,
        user_id: str,
        items: List[RecommendedItem],
        algorithm: str,
    ) -> None:
        """__init__。

        参数说明：
        :param self: 参数 self
        :param recommendation_id: 参数 recommendation_id
        :param user_id: 参数 user_id
        :param items: 参数 items
        :param algorithm: 参数 algorithm
        :return: 返回处理结果。
        """
        self.recommendation_id = recommendation_id
        self.user_id = user_id
        self.items = items
        self.algorithm = algorithm


def _cosine_similarity(vec_a: Dict[str, float], vec_b: Dict[str, float]) -> float:
    """计算两个稀疏向量的余弦相似度

    Args:
        vec_a: 稀疏向量A（键为维度，值为权重）
        vec_b: 稀疏向量B

    Returns:
        余弦相似度，范围[-1, 1]
    """
    common_keys = set(vec_a.keys()) & set(vec_b.keys())
    if not common_keys:
        return 0.0

    dot_product = sum(vec_a[k] * vec_b[k] for k in common_keys)
    norm_a = math.sqrt(sum(v * v for v in vec_a.values()))
    norm_b = math.sqrt(sum(v * v for v in vec_b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot_product / (norm_a * norm_b)


def _collaborative_filtering(
    user_id: str, limit: int
) -> List[Tuple[str, float]]:
    """基于用户的协同过滤推荐

    步骤：
    1. 找到与目标用户最相似的K个用户
    2. 基于相似用户的偏好预测目标用户对未交互物品的评分
    3. 按预测评分排序返回

    Args:
        user_id: 目标用户ID
        limit: 返回物品数量上限

    Returns:
        (item_id, predicted_score) 列表
    """
    if user_id not in _user_item_matrix:
        return []

    target_prefs = _user_item_matrix[user_id]
    # 计算与所有其他用户的相似度
    similarities: List[Tuple[str, float]] = []
    for other_uid, other_prefs in _user_item_matrix.items():
        if other_uid == user_id:
            continue
        sim = _cosine_similarity(target_prefs, other_prefs)
        if sim > 0:
            similarities.append((other_uid, sim))

    # 取Top-K相似用户（K=20）
    similarities.sort(key=lambda x: x[1], reverse=True)
    top_k = similarities[:20]
    if not top_k:
        return []

    # 预测目标用户对未交互物品的评分
    predictions: Dict[str, float] = defaultdict(float)
    sim_sum: Dict[str, float] = defaultdict(float)
    for other_uid, sim in top_k:
        for item_id, rating in _user_item_matrix[other_uid].items():
            if item_id not in target_prefs:  # 只推荐用户未交互过的物品
                predictions[item_id] += sim * rating
                sim_sum[item_id] += abs(sim)

    # 归一化预测评分
    scored_items = [
        (item_id, predictions[item_id] / sim_sum[item_id])
        for item_id in predictions
        if sim_sum[item_id] > 0
    ]
    scored_items.sort(key=lambda x: x[1], reverse=True)
    return scored_items[:limit]


def _content_based_recommendation(
    user_id: str, limit: int
) -> List[Tuple[str, float]]:
    """基于内容的推荐

    根据用户已交互物品的特征，推荐具有相似特征的其他物品

    Args:
        user_id: 目标用户ID
        limit: 返回物品数量上限

    Returns:
        (item_id, similarity_score) 列表
    """
    if user_id not in _user_item_matrix:
        return []

    user_prefs = _user_item_matrix[user_id]
    # 构建用户偏好特征向量（已交互物品特征的加权平均）
    user_profile: Dict[str, float] = defaultdict(float)
    total_weight = 0.0
    for item_id, rating in user_prefs.items():
        if item_id in _item_features:
            for feat, val in _item_features[item_id].items():
                user_profile[feat] += rating * val
            total_weight += abs(rating)

    if total_weight > 0:
        for feat in user_profile:
            user_profile[feat] /= total_weight

    if not user_profile:
        return []

    # 计算用户偏好与所有未交互物品的相似度
    scored_items: List[Tuple[str, float]] = []
    interacted_items = set(user_prefs.keys())
    for item_id, features in _item_features.items():
        if item_id not in interacted_items:
            sim = _cosine_similarity(user_profile, features)
            if sim > 0:
                scored_items.append((item_id, sim))

    scored_items.sort(key=lambda x: x[1], reverse=True)
    return scored_items[:limit]


def _hybrid_recommendation(
    user_id: str, limit: int
) -> List[Tuple[str, float]]:
    """混合推荐：协同过滤 + 内容推荐加权融合

    协同过滤权重0.6，内容推荐权重0.4

    Args:
        user_id: 目标用户ID
        limit: 返回物品数量上限

    Returns:
        (item_id, combined_score) 列表
    """
    cf_results = _collaborative_filtering(user_id, limit * 2)
    cb_results = _content_based_recommendation(user_id, limit * 2)
    cf_weight = 0.6
    cb_weight = 0.4
    # 合并分数
    combined: Dict[str, float] = defaultdict(float)
    for item_id, score in cf_results:
        combined[item_id] += cf_weight * score
    for item_id, score in cb_results:
        combined[item_id] += cb_weight * score

    scored_items = list(combined.items())
    scored_items.sort(key=lambda x: x[1], reverse=True)
    return scored_items[:limit]


async def _generate_recommendation_explanations(
    user_id: str, items: List[Tuple[str, float]], algorithm: str
) -> Dict[str, str]:
    """调用LLM生成推荐解释

    Args:
        user_id: 用户ID
        items: (item_id, score) 列表
        algorithm: 使用的推荐算法

    Returns:
        item_id -> 推荐理由 的映射
    """
    engine = AIEngine()
    if not engine.is_available():
        return {
            item_id: "基于您的浏览偏好推荐" for item_id, _ in items
        }

    try:
        user_profile = _user_profiles.get(user_id, {})
        items_desc = "\n".join(
            f"- 物品{item_id}（匹配度: {score:.2f}）"
            for item_id, score in items[:5]  # 限制最多5个以控制token
        )
        prompt = f"""为以下推荐结果生成简短的中文推荐理由（每条10-30字）。

用户画像：{json.dumps(user_profile, ensure_ascii=False) if user_profile else '新用户'}
推荐算法：{algorithm}

推荐物品：
{items_desc}

请返回JSON格式：
{{"item_id": "推荐理由"}}

只返回JSON，不要添加其他文本。"""

        result = await engine.generate(
            prompt=prompt,
            max_tokens=800,
            task_complexity="simple",
        )
        content = result.get("content", "").strip()
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        return json.loads(content)
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        logger.warning(f"Failed to parse recommendation explanations: {e}")
        return {item_id: "基于您的偏好推荐" for item_id, _ in items}
    except Exception as e:
        logger.error(f"generate_recommendation_explanations failed: {e}")
        return {item_id: "基于您的偏好推荐" for item_id, _ in items}


async def generate_recommendations(
    request: RecommendationRequest,
) -> RecommendationResult:
    """AI驱动的推荐生成

    根据指定算法生成推荐结果：
    - collaborative: 纯协同过滤
    - content: 纯内容推荐
    - hybrid: 混合推荐（默认）

    Args:
        request: 推荐请求

    Returns:
        RecommendationResult包含推荐物品列表
    """
    rec_id = f"rec-{uuid.uuid4().hex[:8]}"
    # 选择推荐算法
    if request.algorithm == "collaborative":
        scored_items = _collaborative_filtering(request.user_id, request.limit)
    elif request.algorithm == "content":
        scored_items = _content_based_recommendation(request.user_id, request.limit)
    else:
        scored_items = _hybrid_recommendation(request.user_id, request.limit)

    # 如果没有足够数据，返回空结果
    if not scored_items:
        return RecommendationResult(
            recommendation_id=rec_id,
            user_id=request.user_id,
            items=[],
            algorithm=request.algorithm,
        )

    # 生成推荐解释
    explanations = await _generate_recommendation_explanations(
        request.user_id, scored_items, request.algorithm
    )
    # 构建推荐物品列表
    recommended_items = [
        RecommendedItem(
            item_id=item_id,
            score=round(score, 4),
            reason=explanations.get(item_id, "基于您的偏好推荐"),
            metadata={"algorithm": request.algorithm},
        )
        for item_id, score in scored_items
    ]
    return RecommendationResult(
        recommendation_id=rec_id,
        user_id=request.user_id,
        items=recommended_items,
        algorithm=request.algorithm,
    )


async def build_user_profile(user_id: str) -> Dict[str, Any]:
    """构建用户画像

    基于用户交互历史和偏好数据构建用户画像

    Args:
        user_id: 用户ID

    Returns:
        包含用户偏好、行为标签和兴趣分布的字典
    """
    if user_id not in _user_item_matrix:
        return {
            "user_id": user_id,
            "preferences": {},
            "behavior_tags": [],
            "interests": [],
        }

    prefs = _user_item_matrix[user_id]
    profile = _user_profiles.get(user_id, {})
    # 统计偏好分布
    if prefs:
        avg_rating = sum(prefs.values()) / len(prefs) if prefs else 0
        top_items = sorted(prefs.items(), key=lambda x: x[1], reverse=True)[:5]
        behavior_tags = [f"偏好物品{iid}" for iid, _ in top_items]
    else:
        avg_rating = 0
        behavior_tags = []

    return {
        "user_id": user_id,
        "preferences": prefs,
        "behavior_tags": behavior_tags,
        "interests": profile.get("interests", []),
        "avg_rating": round(avg_rating, 2),
        "interaction_count": len(prefs),
    }


async def update_recommendation_model(feedback: Dict[str, Any]) -> Dict[str, Any]:
    """更新推荐模型（在线学习）

    根据用户反馈更新用户-物品交互矩阵

    Args:
        feedback: 反馈数据，包含user_id/item_id/rating等

    Returns:
        更新状态字典
    """
    user_id = feedback.get("user_id")
    item_id = feedback.get("item_id")
    rating = feedback.get("rating", 0.0)
    if not user_id or not item_id:
        return {"status": "error", "message": "Missing user_id or item_id"}

    # 更新交互矩阵
    _user_item_matrix[user_id][item_id] = rating
    # 更新用户画像
    if user_id not in _user_profiles:
        _user_profiles[user_id] = {"interests": [], "updated_count": 0}
    _user_profiles[user_id]["updated_count"] = _user_profiles[user_id].get(
        "updated_count", 0
    ) + 1
    return {
        "status": "updated",
        "user_id": user_id,
        "item_id": item_id,
        "new_rating": rating,
    }
