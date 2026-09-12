"""产品智能匹配（Product Finder）公开路由。

端点：POST /api/v1/matching/product-match
该模块定义 ``router``，由 routes 自动发现机制挂载到 /api/v1/matching。
此端点为公开端点（无需登录），已在 csrf_middleware 的 _API_EXEMPT_PREFIXES 中加入
"/api/v1/matching" 以跳过 CSRF 校验。

CHAIN-02: 添加候选缓存，避免重复计算。
"""
from __future__ import annotations

from typing import Any
from datetime import timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.response import error_response, success_response
from app.db.session import get_db
from app.models.product import Product
from app.services.matching_engine.engine import MatchingEngine
from app.services.matching_engine.schemas import ProductMatchRequest
from app.core.cache import multi_level_get, multi_level_set
import logging
logger = logging.getLogger(__name__)

router = APIRouter()

# CHAIN-02: 候选缓存key前缀
_MATCHING_CACHE_PREFIX = "matching:product"


def _serialize_product(p: Product) -> dict[str, Any]:
    """将 Product ORM 对象转为引擎可消费的视图字典（只读真实字段）。"""
    specs = p.specifications
    if not isinstance(specs, dict):
        specs = {}
    return {
        "id": p.id,
        "name": p.name,
        "slug": p.slug,
        "subtitle": p.subtitle,
        "image_url": p.image_url,
        "fire_rating": p.fire_rating,
        "thermal_conductivity": p.thermal_conductivity,
        "technical_params": p.technical_params or "",
        "application_scenarios": p.application_scenarios or "",
        "advantages": p.advantages or "",
        "specifications": specs,
        "category_id": p.category_id,
        "is_active": bool(p.is_active),
    }


@router.post("/product-match", summary="产品智能匹配（Product Finder）")
def product_match(
    payload: ProductMatchRequest,
    db: Session = Depends(get_db),
) -> Any:
    """根据应用场景 / 防火等级 / 导热系数 / 标准等要求，对活跃且未删除的产品做

    硬条件过滤 + 加权评分 + 证据解释，返回推荐产品列表与被拒绝产品列表。
    """
    try:
        # CHAIN-02: 生成缓存key
        cache_key = f"{_MATCHING_CACHE_PREFIX}:{payload.model_dump_json()}"
        # 尝试从缓存获取
        cached_result = multi_level_get(cache_key)
        if cached_result is not None:
            logger.info("Matching cache HIT for query: %s", cache_key[:50])
            return success_response(data=cached_result)

        # 缓存未命中，执行查询和匹配
        products = (
            db.query(Product)
            .filter(Product.deleted_at.is_(None), Product.is_active.is_(True))
            .all()
        )
        product_views = [_serialize_product(p) for p in products]
        result = MatchingEngine.match(product_views, payload.model_dump())
        # 写入缓存（TTL 5分钟）
        multi_level_set(cache_key, result, ttl_sec=300)
        logger.info("Matching cache SET for query: %s", cache_key[:50])
        return success_response(data=result)
    except Exception as exc:  # noqa: BLE001
        logger = __import__("logging").getLogger(__name__)
        logger.exception("Product match failed: %s", exc)
        return error_response(500, f"匹配计算失败：{exc}")
