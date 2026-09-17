# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""统一任务控制面模型（总纲 §4.6-1 / §8 082_unify_ai_tasks；轮23 补 ORM 映射）。

ai_tasks 表由迁移 082 建好（11 态状态机 + 幂等 + checkpoint + lease），
本模块只做模型映射，**无需新迁移**。收编 DeerflowJob/PaperclipTask 的任务真相源
（双写过渡期并行，2 个迭代后降级为从表）。

字段与迁移 082 严格一致；状态枚举 TASK_STATUSES 为唯一权威（红线：终态不可再转移）。
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)

from app.core.database import UUID_TYPE, Base

# 与迁移 082 的 TASK_STATUSES 严格一致（§4.6-2 基线 9 态 + §5.2 增补 paused）
TASK_STATUSES = (
    "created", "planning", "executing", "review", "paused",
    "retrying", "wait_human", "done", "failed", "cancelled", "timeout",
)

# 终态（红线：不可再转移）
TERMINAL_TASK_STATUSES = ("done", "failed", "cancelled", "timeout")


def _utcnow() -> datetime:
    """_utcnow。
    :return: 返回当前 UTC 时间。
    """
    return datetime.now(timezone.utc)


def _new_uuid() -> str:
    """_new_uuid。
    :return: 返回新 UUID 字符串。
    """
    return str(uuid.uuid4())


class AiTask(Base):
    """统一任务控制面（总纲 §4.6-1）。"""

    __tablename__ = "ai_tasks"

    id = Column(UUID_TYPE, primary_key=True, default=_new_uuid)
    tenant_id = Column(UUID_TYPE, ForeignKey("tenants.id"), nullable=False, index=True)
    parent_task_id = Column(String(36), nullable=True, index=True)
    task_type = Column(String(100), nullable=False)
    status = Column(String(30), nullable=False, default="created")
    priority = Column(Integer, nullable=False, default=5)
    # 输入 / 输出 / 断点（§4.6-1：长任务可恢复）
    input_json = Column(Text, nullable=True)
    output_json = Column(Text, nullable=True)
    checkpoint_json = Column(Text, nullable=True)
    # 幂等与预算
    idempotency_key = Column(String(128), nullable=True)
    budget_used = Column(Numeric(precision=12, scale=4), nullable=False, default=0)
    budget_limit = Column(Numeric(precision=12, scale=4), nullable=True)
    # 有界重试（§4.8 红线：≤3 次，超限转 wait_human）
    retry_count = Column(Integer, nullable=False, default=0)
    # GoodJob 模式：单泳道锁 + 节流键（§5.1.4）
    lease_owner = Column(String(100), nullable=True)
    lease_expires_at = Column(DateTime(timezone=True), nullable=True)
    throttle_key = Column(String(128), nullable=True)
    # 追踪与归属
    trace_id = Column(String(64), nullable=True)
    source = Column(String(50), nullable=True)
    created_by = Column(String(36), nullable=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        onupdate=_utcnow,
    )

    __table_args__ = (
        Index("ix_ai_tasks_tenant_status", "tenant_id", "status"),
        Index("ix_ai_tasks_tenant_type", "tenant_id", "task_type"),
        Index("ix_ai_tasks_lease_expires", "lease_expires_at"),
        Index(
            "uq_ai_tasks_tenant_idempotency", "tenant_id", "idempotency_key",
            unique=True,
        ),
        CheckConstraint(
            "status IN ({})".format(", ".join(f"'{s}'" for s in TASK_STATUSES)),
            name="ck_ai_tasks_status",
        ),
    )
