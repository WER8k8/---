"""Product Finder 匹配引擎包。

暴露 ``MatchingEngine`` 及请求/响应模型，供路由层调用。
"""
from app.services.matching_engine.engine import MatchingEngine
from app.services.matching_engine.schemas import (
    DimensionScores,
    MatchItem,
    MatchResponse,
    ProductMatchRequest,
    RejectedItem,
)

__all__ = [
    "MatchingEngine",
    "ProductMatchRequest",
    "MatchResponse",
    "MatchItem",
    "RejectedItem",
    "DimensionScores",
]
