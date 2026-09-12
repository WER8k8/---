"""Product Finder 匹配引擎 — 请求 / 响应 Pydantic 模型。

这些模型仅描述数据结构，不包含任何业务逻辑，可被路由层与引擎层共用。
所有判定严格基于真实 Product 字段与用户输入，绝不编造认证或测试数据。
"""
from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class ProductMatchRequest(BaseModel):
    """找产品（Product Finder）匹配请求。

    application 为必填项；其余均为可选约束，仅参与评分或硬条件过滤。
    """
    application: str = Field(
        ...,
        min_length=1,
        description="应用场景，必填。例如 '管道保温'、'外墙保温'。",
    )
    fire_rating: Optional[str] = Field(
        None,
        description="要求的最低防火等级（EN 13501），例如 'A2'。低于此等级将被硬拒绝。",
    )
    max_thermal_conductivity: Optional[float] = Field(
        None,
        gt=0,
        description="导热系数上限，单位 W/(m·K)。产品导热系数超过该值将被硬拒绝。",
    )
    standard: Optional[str] = Field(
        None,
        description="要求的执行标准 / 认证，例如 'EN 14303'、'GB/T 25975'。",
    )
    environment: Optional[str] = Field(
        None,
        description="要求的使用环境，例如 '高温'、'潮湿'、'腐蚀'。",
    )
    country: Optional[str] = Field(
        None,
        description="目标国家 / 市场（无对应字段时仅作中性参考）。",
    )
    installation: Optional[str] = Field(
        None,
        description="施工 / 安装方式要求，例如 '粘贴'、'干挂'、'装配式'。",
    )
    top_n: int = Field(
        5,
        ge=1,
        le=50,
        description="返回前 N 条匹配结果（按综合分降序）。",
    )
    model_config = {"extra": "ignore"}


class DimensionScores(BaseModel):
    """八个维度的子分（0~100）。"""
    fireRating: float = 0.0
    standard: float = 0.0
    application: float = 0.0
    environment: float = 0.0
    market: float = 0.0
    installation: float = 0.0
    commercial: float = 0.0
    availability: float = 0.0


class MatchItem(BaseModel):
    """单条匹配结果。"""
    product_id: str
    name: str
    slug: str
    image_url: Optional[str] = None
    fire_rating: Optional[str] = None
    thermal_conductivity: Optional[str] = None
    score: float
    tier: str
    dimensions: DimensionScores
    evidence: list[str]
    explanation: str


class RejectedItem(BaseModel):
    """被硬条件拒绝的产品。"""
    product_id: str
    name: str
    reason: str


class MatchResponse(BaseModel):
    """匹配接口完整响应。"""
    query: dict[str, Any]
    total_products: int
    matches: list[MatchItem]
    rejected: list[RejectedItem]
