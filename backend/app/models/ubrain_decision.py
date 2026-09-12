"""UBrain AI Agent 决策追踪模型"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, Index, JSON, String, Text

from app.core.database import UUID_TYPE, Base


class UBrainDecisionRecord(Base):
    """AI Agent 决策记录

    记录 AI Agent 在某个树节点上的决策输入、输出及置信度。
    """
    __tablename__ = "ubrain_decision_records"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    decision_id = Column(String(64), nullable=False, index=True, unique=True)
    agent_tree_node_id = Column(String(64), nullable=False, index=True)
    decision_type = Column(String(64), nullable=False, index=True)
    input_context = Column(JSON, default=dict)
    output_action = Column(JSON, default=dict)
    confidence_score = Column(Float, nullable=True)
    tenant_id = Column(UUID_TYPE, nullable=True, index=True)
    user_id = Column(UUID_TYPE, nullable=True, index=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    __table_args__ = (
        Index("ix_ubrain_decision_agent_created", "agent_tree_node_id", "created_at"),
        Index("ix_ubrain_decision_tenant_created", "tenant_id", "created_at"),
    )


class UBrainExecutionRecord(Base):
    """AI Agent 决策执行记录

    追踪决策被调度执行后的状态、结果与耗时。
    """
    __tablename__ = "ubrain_execution_records"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    execution_id = Column(String(64), nullable=False, index=True, unique=True)
    decision_id = Column(String(64), nullable=False, index=True)
    status = Column(String(32), nullable=False, index=True)
    result = Column(JSON, nullable=True)
    latency_ms = Column(Float, nullable=True)
    tenant_id = Column(UUID_TYPE, nullable=True, index=True)
    user_id = Column(UUID_TYPE, nullable=True, index=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    __table_args__ = (
        Index("ix_ubrain_exec_decision_created", "decision_id", "created_at"),
        Index("ix_ubrain_exec_status_created", "status", "created_at"),
    )


class UBrainFeedbackRecord(Base):
    """AI Agent 决策执行反馈记录

    用户对 AI 执行结果的人工反馈，用于闭环优化。
    """
    __tablename__ = "ubrain_feedback_records"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    execution_id = Column(String(64), nullable=False, index=True)
    feedback_score = Column(Float, nullable=True)
    feedback_text = Column(Text, nullable=True)
    tenant_id = Column(UUID_TYPE, nullable=True, index=True)
    user_id = Column(UUID_TYPE, nullable=True, index=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    __table_args__ = (
        Index("ix_ubrain_feedback_exec_created", "execution_id", "created_at"),
    )
