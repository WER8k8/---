# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Industry Profile 行业参数包（修正设计稿 模块2 / 第一章去行业化 / Gate——对应验收）。

目标：Core Runtime = Industry Profile 的注入点，行业差异（建材/机械/化工…）
不再硬编码进核心模型与计算器：
- boq_rules 携带核价引擎参数包（材料基价表/密度/工艺费/等级系数/MOQ 折扣档），
  由 services.boq_pipeline_service 与 boq_calculator 消费；
- 版本化（version + status draft/active/retired）；status=active 唯一生效；
- 迁移：building_material_specs 等建材专表映射到 code="building_materials" 后转只读。
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, Integer, String, UniqueConstraint

from app.core.database import UUID_TYPE, Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class IndustryProfile(Base):
    """行业参数包（版本化；同 code 多版本，active 唯一生效）。"""

    __tablename__ = "industry_profiles"
    __table_args__ = (
        UniqueConstraint("code", "version", name="uq_industry_profile_code_version"),
    )

    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    code = Column(String(60), nullable=False, index=True)  # building_materials / machinery / …
    name = Column(String(120), nullable=False)
    version = Column(Integer, nullable=False, default=1)
    status = Column(String(20), nullable=False, default="draft", index=True)  # draft/active/retired

    unit_system = Column(String(30), nullable=False, default="metric")
    currency_defaults = Column(JSON, default=dict)
    incoterm_defaults = Column(JSON, default=list)

    product_schema = Column(JSON, default=dict)
    technical_fields = Column(JSON, default=dict)
    commercial_fields = Column(JSON, default=dict)
    certification_schema = Column(JSON, default=dict)

    boq_rules = Column(JSON, default=dict)  # 核价引擎参数包（材料基价/密度/工艺费/等级/MOQ 档）
    seo_taxonomy = Column(JSON, default=dict)
    content_taxonomy = Column(JSON, default=dict)
    fulfillment_rules = Column(JSON, default=dict)
    ui_labels = Column(JSON, default=dict)
    metadata_json = Column("metadata", JSON, default=dict)

    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)
