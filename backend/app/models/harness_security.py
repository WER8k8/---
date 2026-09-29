# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""DSH/Agent 安全审计事件（修正设计稿 模块15.6 / Production Gate G10）。

记录沙箱治理的每一次关键判定：网络目标放行/拒绝、生产模式违规、令牌验签失败、
越权操作尝试等。设计稿 15.6 字段：tenant_id / task_id / network_target /
operation / policy / decision / trace_id。

验收映射（模块 15.6）：
- 伪造 tenant_id → Gateway 拒绝（审计 decision=deny）
- 容器直连 PG → 网络层拒绝（decision=deny, policy=db_no_direct）
- 未授权域名访问 → egress 层拒绝（decision=deny, policy=egress_allowlist）
- 绕过 API 写数据库 → 凭据不存在（沙箱容器内不发放 PG 凭据，拓扑由部署保证）
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Index, String, Text

from app.core.database import UUID_TYPE, Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class HarnessSecurityEvent(Base):
    """沙箱安全审计事件（append-only）。"""

    __tablename__ = "harness_security_events"
    __table_args__ = (
        Index("ix_harness_sec_tenant_created", "tenant_id", "created_at"),
        Index("ix_harness_sec_decision", "decision"),
    )

    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(UUID_TYPE, nullable=True, index=True)
    task_id = Column(String(100), nullable=True, index=True)
    network_target = Column(String(255), nullable=True)
    operation = Column(String(60), nullable=False)  # run_turn / egress_check / token_verify / mode_check
    policy = Column(String(60), nullable=False)  # sandbox_mode / egress_allowlist / db_no_direct / token_sign
    decision = Column(String(20), nullable=False)  # allow / deny
    detail = Column(Text, nullable=True)
    trace_id = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
