# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""定价规则版本化（修正设计稿 模块14.2 / 第二层缺口 A / Gate G9）。

解决的问题（第二层 §3）：账单必须能回答"当时为什么按这个价格结算"——
规则修改后历史账单不可被重新解释。

设计：
- (rule_code, version) 唯一；同一 rule_code 的新版本 = 新行（append-only 治理）；
- status: draft / active / retired；生效窗口 effective_from / effective_to；
- plan_id 为空 = 全套餐通用价（否则仅该套餐）；
- 结算时快照进 billing_reservations.pricing_snapshot（模块14.2），
  本表后续修改不影响已生成的快照。
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Index,
    Integer,
    String,
    UniqueConstraint,
)

from app.core.database import UUID_TYPE, Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PricingRule(Base):
    """定价规则版本行（append-only；改价 = 新版本行，不改旧行）。"""

    __tablename__ = "billing_pricing_rules"
    __table_args__ = (
        UniqueConstraint("rule_code", "version", name="uq_pricing_rule_code_version"),
        Index("ix_pricing_rule_meter_status", "meter_code", "status"),
        Index("ix_pricing_rule_effective", "meter_code", "effective_from"),
    )

    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    rule_code = Column(String(80), nullable=False)  # 规则身份（如 qualified-inquiry-default）
    version = Column(Integer, nullable=False, default=1)
    meter_code = Column(String(60), nullable=False)  # 关联稳定计量词表（METER_CODES_PLANNED）
    plan_id = Column(UUID_TYPE, nullable=True, index=True)  # NULL = 全套餐通用

    unit_price_cents = Column(Integer, nullable=False, default=0)  # 单价（分）
    currency = Column(String(8), nullable=False, default="CNY")
    free_quota = Column(Integer, nullable=False, default=0)  # 每周期免费额度
    minimum_charge_cents = Column(Integer, nullable=True)
    maximum_charge_cents = Column(Integer, nullable=True)
    conditions = Column(JSON, default=dict)  # 触发条件（预留：市场/行业/数量阶梯）

    status = Column(String(20), nullable=False, default="draft", index=True)  # draft/active/retired
    is_active = Column(Boolean, nullable=False, default=False)
    effective_from = Column(DateTime(timezone=True), nullable=True)
    effective_to = Column(DateTime(timezone=True), nullable=True)
    note = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)
