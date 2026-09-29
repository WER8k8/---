# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""ContentAsset 统一对象 DTO（修正设计稿 模块4 / 契约 §4）。

ContentAsset **不是一张新表**，而是既有内容的**统一收敛层（读模型 / facade）**：
由 `services/content_asset_service.build_content_asset` 把 `ContentMaster` +
`FactKernel` + `Tenant`（+ 模块2 IndustryProfile）+ `PublishTask` 聚合 +
`MarketingTouchpoint` 组装为本 DTO。

字段严格按契约 §4 表逐行实现（设计稿 4.3 的 14 个 + `asset_id` 主键 = 15 个），
**不增不减、顺序一致**。Pydantic v2 风格（与仓库其它 schemas 一致）。
"""
from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class ContentAssetOut(BaseModel):
    """统一内容资产对象（15 字段，契约 §4 冻结顺序）。"""

    asset_id: str                                  # content_masters.id
    tenant_id: str                                 # content_masters.tenant_id（租户隔离红线）
    site_id: Optional[str] = None                  # 派生：Tenant.domain（一租户一站）
    industry_profile_id: Optional[str] = None      # 派生：模块2 resolve_profile_for_tenant().id
    # —— 6 个净新增溯源/上下文字段（读 master.asset_meta；NULL → null/[]）——
    product_id: Optional[str] = None
    market: Optional[str] = None
    language: Optional[str] = "zh"                 # 缺省租户默认语 zh
    source_refs: list[Any] = Field(default_factory=list)
    # —— 派生字段 ——
    evidence_refs: list[Any] = Field(default_factory=list)   # fact_kernel_json.evidence[]
    prompt_version: Optional[str] = None                     # 净新增（asset_meta）
    model_version: Optional[str] = None                      # 净新增（asset_meta）
    content_status: str = "draft"                            # 状态机派生（契约 §4.1）
    publish_status: Optional[str] = "unpublished"            # publish_tasks 聚合
    canonical_url: Optional[str] = None                      # 租户主域收口（契约 §4.2）
    attribution_context: dict[str, Any] = Field(default_factory=dict)  # 触点聚合


class ContentAssetListOut(BaseModel):
    """分页列表外壳（items 为 ContentAssetOut）。"""

    items: list[ContentAssetOut] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    size: int = 20


class ContentStatusTransitionIn(BaseModel):
    """状态跃迁请求体。

    只接受既有值 `draft` / `ready` / `published`（裁定 裁-3：严禁写入
    `archived` / `verification_failed`）。具体跃迁合法性由服务/路由校验，
    非法跃迁返回 409 `illegal_content_status_transition`。
    """

    content_status: str = Field(..., min_length=1, max_length=20)


__all__ = [
    "ContentAssetOut",
    "ContentAssetListOut",
    "ContentStatusTransitionIn",
]
