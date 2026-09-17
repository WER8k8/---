# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""统一 Trace 与记分卡数据模型（总纲 §4.6-7 / §8 085_traces）。

- task_traces：链式追踪表（TASK-013）。prompt 正文只存对象存储引用，正文不入库；
  吸收 Claude 表设计的 artifacts / validation_results 字段；人工反馈留证（§3.4）。
- skill_performance / agent_scorecards：版本/Agent 级记分卡，
  吸收 §040 业务指标（Revenue Impact / Conversion / Efficiency / ROI）。
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)

from app.core.database import UUID_TYPE, Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TaskTrace(Base):
    """统一 Trace 链式表 — 每次任务执行的完整追踪（§4.6-7 / TASK-013）。"""
    __tablename__ = "task_traces"

    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(UUID_TYPE, ForeignKey("tenants.id"), nullable=True, index=True)
    # 链式：父 trace（同一任务的多步执行形成链）
    parent_trace_id = Column(UUID_TYPE, nullable=True, index=True)
    # 溯源：ai_task / pipeline_run / skill_call / hermes / deerflow
    trace_type = Column(String(30), nullable=False, index=True)
    source_id = Column(String(64), nullable=True, index=True)
    # 关联统一任务面（ai_tasks）与 pipeline run（弱引用，跨库不设 FK）
    task_id = Column(UUID_TYPE, ForeignKey("ai_tasks.id"), nullable=True, index=True)
    run_id = Column(String(36), nullable=True, index=True)
    # 执行上下文：Skill 版本 + 模型
    skill_id = Column(String(100), nullable=True, index=True)
    skill_version = Column(String(20), nullable=True)
    model_name = Column(String(100), nullable=True)
    # running / success / failed（复合索引 ix_task_traces_status 已覆盖 status 检索）
    status = Column(String(20), nullable=False, default="running")
    success = Column(Boolean, nullable=True)
    # prompt 正文只存对象存储引用（正文不入库，§4.6-7）
    prompt_ref = Column(String(500), nullable=True)
    input_summary = Column(Text, nullable=True)
    output_summary = Column(Text, nullable=True)
    # 吸收 Claude 表设计：产物 / 外部核验结果
    artifacts = Column(JSON, default=list)
    validation_results = Column(JSON, default=list)
    error_code = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)
    # 计量（供计费 / 记分卡聚合）
    duration_ms = Column(Integer, default=0, nullable=False)
    cost = Column(Float, default=0.0, nullable=False)
    tokens_used = Column(Integer, default=0, nullable=False)
    # 人工反馈（§3.4：每次 AI 回复留证）
    feedback = Column(JSON, nullable=True)
    # 扩展上下文：prompt_hash、temperature 等
    metadata_json = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False, index=True)
    updated_at = Column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )
    finished_at = Column(DateTime(timezone=True), nullable=True)
    __table_args__ = (
        Index("ix_task_traces_source", "trace_type", "source_id"),
        Index("ix_task_traces_tenant_created", "tenant_id", "created_at"),
        Index("ix_task_traces_status", "status", "created_at"),
    )


class SkillPerformance(Base):
    """Skill 版本记分卡 — 按（skill_id, skill_version, 窗口）聚合成功率/耗时/成本。"""
    __tablename__ = "skill_performance"

    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(UUID_TYPE, ForeignKey("tenants.id"), nullable=True, index=True)
    skill_id = Column(String(100), nullable=False, index=True)
    skill_version = Column(String(20), nullable=False, default="")
    window_start = Column(DateTime(timezone=True), nullable=False)
    window_end = Column(DateTime(timezone=True), nullable=False)
    total_invocations = Column(Integer, default=0, nullable=False)
    success_count = Column(Integer, default=0, nullable=False)
    failure_count = Column(Integer, default=0, nullable=False)
    success_rate = Column(Float, default=0.0, nullable=False)
    avg_duration_ms = Column(Integer, default=0, nullable=False)
    avg_cost = Column(Float, default=0.0, nullable=False)
    total_tokens = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "skill_id", "skill_version", "window_start",
            name="uq_skill_performance_window",
        ),
        Index("ix_skill_performance_skill", "skill_id", "skill_version"),
    )


class AgentScorecard(Base):
    """Agent 记分卡 — 按（agent_id, task_type）聚合执行质量与业务指标（§040 吸收）。"""
    __tablename__ = "agent_scorecards"

    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(UUID_TYPE, ForeignKey("tenants.id"), nullable=True, index=True)
    agent_id = Column(String(100), nullable=False, index=True)
    agent_name = Column(String(200), nullable=True)
    task_type = Column(String(80), nullable=False, index=True)
    total_invocations = Column(Integer, default=0, nullable=False)
    success_count = Column(Integer, default=0, nullable=False)
    success_rate = Column(Float, default=0.0, nullable=False)
    avg_duration_ms = Column(Integer, default=0, nullable=False)
    avg_cost = Column(Float, default=0.0, nullable=False)
    # §040 业务指标：收入影响 / 转化率 / 效率 / ROI
    revenue_impact = Column(Numeric(14, 2), default=0)
    conversion_rate = Column(Float, default=0.0)
    efficiency = Column(Float, default=0.0)
    roi = Column(Float, default=0.0)
    evaluation_window_days = Column(Integer, default=7, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "agent_id", "task_type", name="uq_agent_scorecard_key"
        ),
        Index("ix_agent_scorecards_agent", "agent_id", "task_type"),
    )
