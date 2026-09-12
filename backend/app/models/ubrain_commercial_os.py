"""DeerFlow ↔ Accio 商业 OS：研究洞察、编排执行、效果回流。"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text

from app.core.database import UUID_TYPE, Base


class UbrainResearchInsight(Base):
    """DeerFlow/研究结论沉淀（Mem0 等价层，可接外部向量库）。"""
    __tablename__ = "ubrain_research_insights"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(UUID_TYPE, ForeignKey("tenants.id"), nullable=False, index=True)
    source = Column(String(40), nullable=False, default="deerflow")  # deerflow | manual | n8n
    source_job_id = Column(UUID_TYPE, nullable=True, index=True)
    intent = Column(String(64), nullable=False)
    title = Column(String(200), nullable=False)
    summary = Column(Text, nullable=False)
    entities_json = Column(Text, default="[]")  # [{type, value, relation}]
    tags_json = Column(Text, default="[]")
    regions_json = Column(Text, default="[]")
    categories_json = Column(Text, default="[]")
    quality_score = Column(Float, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )


class UbrainPipelineRun(Base):
    """研究 → Accio 自动编排（n8n 等价层）。"""
    __tablename__ = "ubrain_pipeline_runs"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(UUID_TYPE, ForeignKey("tenants.id"), nullable=False, index=True)
    trigger_job_id = Column(UUID_TYPE, nullable=True, index=True)
    insight_id = Column(UUID_TYPE, ForeignKey("ubrain_research_insights.id"), nullable=True)
    status = Column(String(20), nullable=False, default="pending", index=True)
    steps_json = Column(Text, default="[]")
    created_job_ids_json = Column(Text, default="[]")
    error_message = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    finished_at = Column(DateTime(timezone=True), nullable=True)


class UbrainActionAudit(Base):
    """Accio A5：副驾对外相关动作审计（chat / 确认发送等）。"""
    __tablename__ = "ubrain_action_audits"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(UUID_TYPE, ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(UUID_TYPE, nullable=True, index=True)
    action_type = Column(String(40), nullable=False, index=True)  # chat | confirm_send
    intent = Column(String(64), nullable=True)
    tool = Column(String(64), nullable=True)
    message_preview = Column(String(400), nullable=True)
    needs_confirmation = Column(String(5), nullable=False, default="false")
    outcome = Column(String(20), nullable=False, default="ok")
    meta_json = Column(Text, default="{}")
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )


class UbrainFeedbackSnapshot(Base):
    """Accio 执行效果快照 → 反哺 DeerFlow 研究策略。"""
    __tablename__ = "ubrain_feedback_snapshots"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(UUID_TYPE, ForeignKey("tenants.id"), nullable=False, index=True)
    period_days = Column(Integer, nullable=False, default=7)
    metrics_json = Column(Text, nullable=False, default="{}")
    recommendations_json = Column(Text, default="[]")
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
