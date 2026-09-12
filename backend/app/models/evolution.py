"""AI 进化引擎数据模型。

存储进化闭环产生的所有数据：任务执行记录、经验条目、Skill/SOP版本、
灰度发布状态、审批记录。
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
    String,
    Text,
)

from app.core.database import UUID_TYPE, Base


class EvolutionTaskRecord(Base):
    """任务执行记录 — 数据收集阶段。

    每次 AI 任务执行后记录成功/失败/耗时/成本，作为进化引擎的原始输入。
    """
    __tablename__ = "evolution_task_records"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(UUID_TYPE, ForeignKey("tenants.id"), nullable=True, index=True)
    task_type = Column(String(80), nullable=False, index=True)
    # skill / sop / agent / workflow
    executor_type = Column(String(30), nullable=False, default="skill")
    executor_id = Column(String(100), nullable=False, index=True)
    success = Column(Boolean, nullable=False, index=True)
    duration_ms = Column(Integer, default=0, nullable=False)
    cost = Column(Float, default=0.0, nullable=False)
    tokens_used = Column(Integer, default=0)
    error_code = Column(String(50))
    error_message = Column(Text)
    input_summary = Column(Text)
    output_summary = Column(Text)
    # 扩展上下文：prompt_hash、model_name、temperature 等
    metadata_json = Column("metadata", JSON, default=dict)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    __table_args__ = (
        Index("idx_evolution_task_type_success", "task_type", "success"),
        Index("idx_evolution_executor_time", "executor_type", "executor_id", "created_at"),
        Index("idx_evolution_tenant_time", "tenant_id", "created_at"),
    )


class ExperienceEntry(Base):
    """经验条目 — 经验沉淀阶段。

    从任务执行记录中提取的可复用模式，存入经验库。
    使用 JSON 存储模式细节，支持灵活查询。
    """
    __tablename__ = "evolution_experiences"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    task_type = Column(String(80), nullable=False, index=True)
    # success_pattern / failure_pattern / optimization_hint
    pattern_type = Column(String(30), nullable=False, index=True)
    # 经验成熟度分级（§4.6-7 阈值控制）：raw → validated → pattern → sop → skill
    stage = Column(String(20), nullable=False, default="raw", index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    # 可复用模式详情：触发条件、适用场景、改进建议等
    pattern_data = Column(JSON, default=dict)
    # 经验来源关联
    source_record_ids = Column(JSON, default=list)
    # 经验质量指标
    confidence = Column(Float, default=0.5, nullable=False)
    occurrence_count = Column(Integer, default=1, nullable=False)
    # 是否已应用于 Skill/SOP 优化
    applied = Column(Boolean, default=False, nullable=False, index=True)
    applied_at = Column(DateTime(timezone=True))
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    __table_args__ = (
        Index("idx_evolution_pattern_unapplied", "pattern_type", "applied"),
        Index("idx_evolution_confidence", "confidence"),
    )


class SkillVersion(Base):
    """Skill 版本 — Skill 优化阶段。

    基于经验自动调整 Prompt/参数后生成新版本，使用语义化版本号。
    """
    __tablename__ = "evolution_skill_versions"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    skill_id = Column(String(100), nullable=False, index=True)
    skill_name = Column(String(200), nullable=False)
    # 语义化版本: major.minor.patch
    version = Column(String(20), nullable=False, index=True)
    major = Column(Integer, default=0, nullable=False)
    minor = Column(Integer, default=0, nullable=False)
    patch = Column(Integer, default=0, nullable=False)
    # draft / evaluation / canary / approved / production / archived
    status = Column(String(20), nullable=False, default="draft", index=True)
    # Prompt 与参数
    prompt_template = Column(Text)
    parameters = Column(JSON, default=dict)
    # 变更说明
    changelog = Column(Text)
    # 关联经验条目
    based_on_experience_ids = Column(JSON, default=list)
    # 效果指标
    success_rate = Column(Float)
    avg_duration_ms = Column(Integer)
    total_invocations = Column(Integer, default=0)
    # 版本血缘
    parent_version_id = Column(
        UUID_TYPE, ForeignKey("evolution_skill_versions.id"), nullable=True
    )
    # 灰度配置
    canary_percentage = Column(Float, default=0.0)
    canary_tenant_ids = Column(JSON, default=list)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    __table_args__ = (
        Index("idx_evolution_skill_status", "skill_id", "status"),
        Index("idx_evolution_skill_version_unique", "skill_id", "version", unique=True),
    )


class SOPVersion(Base):
    """SOP 版本 — SOP 优化阶段。

    标准操作流程版本管理，支持与 Skill 版本联动。
    """
    __tablename__ = "evolution_sop_versions"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    sop_id = Column(String(100), nullable=False, index=True)
    sop_name = Column(String(200), nullable=False)
    version = Column(String(20), nullable=False, index=True)
    major = Column(Integer, default=0, nullable=False)
    minor = Column(Integer, default=0, nullable=False)
    patch = Column(Integer, default=0, nullable=False)
    status = Column(String(20), nullable=False, default="draft", index=True)
    # SOP 内容：步骤列表、决策树、异常处理
    steps = Column(JSON, default=list)
    decision_tree = Column(JSON, default=dict)
    exception_handling = Column(JSON, default=dict)
    changelog = Column(Text)
    based_on_experience_ids = Column(JSON, default=list)
    # 关联 Skill 版本
    linked_skill_version_ids = Column(JSON, default=list)
    # 效果指标
    completion_rate = Column(Float)
    avg_completion_time_ms = Column(Integer)
    total_executions = Column(Integer, default=0)
    parent_version_id = Column(
        UUID_TYPE, ForeignKey("evolution_sop_versions.id"), nullable=True
    )
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    __table_args__ = (
        Index("idx_evolution_sop_status", "sop_id", "status"),
        Index("idx_evolution_sop_version_unique", "sop_id", "version", unique=True),
    )


class ApprovalRecord(Base):
    """审批记录 — 灰度发布人工审批。

    进化操作需要人工审批才能进入 Production 状态。
    """
    __tablename__ = "evolution_approvals"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    # skill_version / sop_version
    target_type = Column(String(30), nullable=False, index=True)
    target_id = Column(UUID_TYPE, nullable=False, index=True)
    # 审批动作: promote_to_production / abort_canary
    action = Column(String(30), nullable=False)
    # pending / approved / rejected
    status = Column(String(20), nullable=False, default="pending", index=True)
    requester = Column(String(100), nullable=False)
    reviewer = Column(String(100))
    review_comment = Column(Text)
    # 审批依据：效果对比数据
    evidence = Column(JSON, default=dict)
    submitted_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    reviewed_at = Column(DateTime(timezone=True))
    __table_args__ = (
        Index("idx_evolution_approval_pending", "target_type", "status"),
    )


class CanaryRouteRecord(Base):
    """灰度路由记录 — 记录每次请求的灰度分流结果。

    用于追踪哪个租户/请求命中了哪个版本，支持效果对比分析。
    """
    __tablename__ = "evolution_canary_routes"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(UUID_TYPE, nullable=True, index=True)
    skill_id = Column(String(100), nullable=False, index=True)
    # 命中的版本
    routed_version = Column(String(20), nullable=True)
    routed_version_id = Column(UUID_TYPE, nullable=True)
    # 是否命中灰度组
    is_canary = Column(Boolean, default=False, nullable=False)
    request_hash = Column(String(64))
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    __table_args__ = (
        Index("idx_evolution_canary_analysis", "skill_id", "is_canary", "created_at"),
    )
