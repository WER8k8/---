# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""统一计量埋点（总纲 §4.6-8 / §6.6 P4 / 迁移总表 086）

meter_events：append-only 计量事件表，只增不改。
7 类埋点动作（§4.6-8）：ai_generation / content_publish / lead_generated /
rfq_created / api_call / export / video_job。
Celery beat 周期汇总进既有计费四表（红线 R3：禁止重建计费）；配额走 plan_gate_service。
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
)

from app.core.database import UUID_TYPE, Base

# §4.6-8：7 类埋点动作
METER_TYPES = (
    "ai_generation",
    "content_publish",
    "lead_generated",
    "rfq_created",
    "api_call",
    "export",
    "video_job",
)

# 修正设计稿 模块9.3：计量标识改用稳定字符串 meter_code，不再用"第 N 类"序号语义。
# METER_CODE_BY_TYPE 把既有 7 类映射到稳定 code（DB 的 meter_type 列与 CheckConstraint
# 保持不动，历史事件不迁移）；七轨新计量（轨2/6/7 等）落库时一律引用 METER_CODES_PLANNED
# 词表，禁止再新增数字序号类语义。
METER_CODE_BY_TYPE = {
    "ai_generation": "ai.token",
    "content_publish": "usage.content_publish",
    "lead_generated": "usage.qualified_inquiry",
    "rfq_created": "usage.rfq",
    "api_call": "api.request",
    "export": "usage.export",
    "video_job": "usage.video_job",
}

# 七轨计费稳定 meter_code 词表（轨1/2/5/6/7 目前无 meter 落点，先冻结语义防止漂移）
METER_CODES_PLANNED = (
    "saas.subscription",      # 轨1 SaaS 订阅
    "usage.qualified_inquiry",  # 轨2 按次：优质询盘
    "usage.boq_processing",     # 轨2 按次：BOQ/标书处理
    "usage.premium_research",   # 轨2 按次：高级研究（设计稿模块十词表）
    "ai.token",               # 轨3 AI Token
    "egress.ip_slot",         # 轨4 IP/指纹槽位
    "commission.deal",        # 轨5 佣金
    "referral.revenue",       # 轨6 裂变
    "api.request",            # 轨7 API 市场计量
    "api.compute",            # 轨7 API 市场算力
)

# ── 模块9 · Meter Definition（唯一权威，纯常量，禁止建表/迁移）──
# 设计 14.1 统一调用链「Meter Definition」步的落点：每个稳定 meter_code 的
# 单位 / 业务主体 / 是否可计费 / 是否走预占 / 所属轨。
# 取值来源（回源码核对，非臆造）：
#   - unit：与既有 emit_* 实际写入值一致 —— ai.token=call / usage.qualified_inquiry=lead /
#     api.request=call 分别取自 meter_event.py 的 emit_ai_generation / emit_lead_generated /
#     emit_api_call；其余 code 尚无 emit_* 落点，按设计稿语义取稳定字符串。
#   - subject_type：与 billing_reservations/测试既有取值一致 ——
#     inquiry / boq_job / research / api_call / order（models/billing_reservation.py:70 及
#     tests/unit/test_billing_reservation.py 的实际调用）。
#   - track：设计稿七轨编号（1 SaaS / 2 Pay-per-use / 3 AI Token / 4 IP Slot /
#     5 Commission / 6 Referral / 7 API Marketplace）。
# 红线：不得据此新建 meter_definitions 表（设计 9.2「不得重建计费四表」；定义属发布期稳定词表）。
METER_DEFINITIONS: dict[str, dict] = {
    "saas.subscription": {
        "unit": "subscription", "subject_type": "tenant",
        "billable": True, "requires_reservation": False, "track": 1,
    },
    "usage.qualified_inquiry": {
        "unit": "lead", "subject_type": "inquiry",
        "billable": True, "requires_reservation": False, "track": 2,
    },
    "usage.boq_processing": {
        "unit": "job", "subject_type": "boq_job",
        "billable": True, "requires_reservation": True, "track": 2,
    },
    "usage.premium_research": {
        "unit": "report", "subject_type": "research",
        "billable": True, "requires_reservation": True, "track": 2,
    },
    "ai.token": {
        "unit": "call", "subject_type": "task",
        "billable": True, "requires_reservation": False, "track": 3,
    },
    "egress.ip_slot": {
        "unit": "slot", "subject_type": "egress_slot",
        "billable": True, "requires_reservation": True, "track": 4,
    },
    "commission.deal": {
        "unit": "deal", "subject_type": "order",
        "billable": True, "requires_reservation": False, "track": 5,
    },
    "referral.revenue": {
        "unit": "reward", "subject_type": "referral",
        "billable": True, "requires_reservation": False, "track": 6,
    },
    "api.request": {
        "unit": "call", "subject_type": "api_call",
        "billable": True, "requires_reservation": False, "track": 7,
    },
    "api.compute": {
        "unit": "compute", "subject_type": "api_call",
        "billable": True, "requires_reservation": False, "track": 7,
    },
}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class MeterEvent(Base):
    """计量事件（append-only）。event_key 幂等去重；aggregated_at 标记已并入账本。"""
    __tablename__ = "meter_events"
    __table_args__ = (
        Index("ix_meter_events_tenant_occurred", "tenant_id", "occurred_at"),
        Index("ix_meter_events_type_occurred", "meter_type", "occurred_at"),
        Index("ix_meter_events_source", "source_ref_type", "source_ref_id"),
        CheckConstraint(
            "meter_type IN ('ai_generation', 'content_publish', 'lead_generated', "
            "'rfq_created', 'api_call', 'export', 'video_job')",
            name="ck_meter_events_type",
        ),
    )
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(UUID_TYPE, ForeignKey("tenants.id"), nullable=True, index=True)
    event_key = Column(String(100), unique=True, nullable=True, index=True)  # 幂等键
    meter_type = Column(String(30), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)  # 计量数量
    unit = Column(String(20), nullable=False, default="count")
    token_delta = Column(Integer, nullable=False, default=0)  # ai_generation 扣减 token
    cost_cents = Column(Integer, nullable=False, default=0)  # 金额（分），对账锚点
    currency = Column(String(8), nullable=False, default="CNY")
    source_ref_type = Column(String(30), nullable=True)  # task/order/content/lead/rfq/export/video
    source_ref_id = Column(String(100), nullable=True)
    # 修正设计稿 模块10.2：计量事件携带业务主体与定价快照（与 billing_reservations 对齐）
    meter_code = Column(String(60), nullable=True, index=True)  # 稳定字符串（METER_CODES_PLANNED）
    subject_type = Column(String(40), nullable=True)
    subject_id = Column(String(100), nullable=True)
    pricing_rule_version = Column(String(30), nullable=True)
    pricing_snapshot = Column(JSON, nullable=True)
    bill_status = Column(String(20), nullable=True)  # unlinked / reserved / settled / released / reversed
    model_name = Column(String(100), nullable=True)
    metadata_json = Column("metadata", JSON, default=dict)
    # 已并入计费账本的时间；NULL=尚未汇总（对账 pending 数依据）
    aggregated_at = Column(DateTime(timezone=True), nullable=True, index=True)
    occurred_at = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
