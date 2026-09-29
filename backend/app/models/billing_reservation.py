# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""计费预占状态机（修正设计稿 模块18 / 模块10 / Gate G9）。

解决的问题：Celery 重试、API 重试、n8n 重试、支付回调重放、用户刷新页面
→ 重复扣费 / 重复结算。设计红线：

- 禁止直接 created → finance_ledger charge；高成本执行必须
  **reserve → execute → settle / release**；
- 业务幂等身份 = tenant_id + meter_code + subject_type + subject_id + event_version
  （`build_idempotency_key` 唯一约束落库，同身份只允许一个有效 charge）；
- 状态机严格跃迁（非法跃迁服务层拒绝），状态变化追加 history（不覆盖历史）；
- settle → finance_ledger 营收一次；reverse → 负向冲正分录（退款/取消）；
- 计费四表（meter_events/token_ledger/finance_ledger/wallet）不重建（红线 R3）。

meter_code 使用稳定字符串（models/meter.METER_CODES_PLANNED），
不再出现"第 N 类"序号语义（模块9.3）。
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)

from app.core.database import UUID_TYPE, Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# 状态机：created → reserved → settled | released；settled → reversed；任何非终态 → failed
RESERVATION_STATUSES = ("created", "reserved", "settled", "released", "reversed", "failed")

LEGAL_TRANSITIONS: dict[str, tuple[str, ...]] = {
    "created": ("reserved", "released", "failed"),
    "reserved": ("settled", "released", "failed"),
    "settled": ("reversed",),
    "released": (),
    "reversed": (),
    "failed": (),
}


class BillingReservation(Base):
    """一次可计费业务动作的预占/结算状态机（幂等身份唯一）。"""

    __tablename__ = "billing_reservations"
    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_billing_reservation_idem_key"),
        Index("ix_billing_reservations_tenant_status", "tenant_id", "status"),
        Index("ix_billing_reservations_subject", "subject_type", "subject_id"),
    )

    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(UUID_TYPE, nullable=False, index=True)

    # 业务幂等身份（设计稿 模块18.2）
    meter_code = Column(String(60), nullable=False)  # 稳定字符串（METER_CODES_PLANNED）
    subject_type = Column(String(40), nullable=False)  # inquiry / boq_job / research / api_call ...
    subject_id = Column(String(100), nullable=False)
    event_version = Column(Integer, nullable=False, default=1)
    idempotency_key = Column(String(200), nullable=False)

    # 定价快照（模块10.2/14.2：改价后历史账单不可被重新解释）
    pricing_rule_version = Column(String(30), nullable=False, default="v0")
    pricing_snapshot = Column(JSON, default=dict)

    amount_cents = Column(Integer, nullable=False, default=0)
    currency = Column(String(8), nullable=False, default="CNY")

    status = Column(String(20), nullable=False, default="created", index=True)
    history_json = Column(JSON, default=list)  # [{from,to,at,reason?}]
    last_reason = Column(Text, nullable=True)

    trace_id = Column(String(100), nullable=True)
    finance_entry_id = Column(UUID_TYPE, nullable=True)  # settle 落 finance_ledger 的分录
    reversal_entry_id = Column(UUID_TYPE, nullable=True)  # reverse 冲正分录

    reserved_at = Column(DateTime(timezone=True), nullable=True)
    settled_at = Column(DateTime(timezone=True), nullable=True)
    released_at = Column(DateTime(timezone=True), nullable=True)
    reversed_at = Column(DateTime(timezone=True), nullable=True)
    failed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)
