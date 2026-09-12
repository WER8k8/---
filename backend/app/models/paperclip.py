"""Paperclip Agent 编排层数据模型。

融合 Paperclip 理念到现有 Hermes + DeerFlow 2.0 架构：
- Company: 公司/租户级实体，对齐目标和预算
- Agent: Agent 雇员，绑定 Hermes 插件或 DeerFlow 意图
- Goal: 目标链（公司使命 -> 项目目标 -> Agent 任务）
- Heartbeat: 心跳调度记录
- Budget: Agent 月度预算
- Approval: 审批门记录
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text,
)

from app.core.database import UUID_TYPE, Base


class PaperclipCompany(Base):
    """公司/组织实体，绑定租户。"""
    __tablename__ = "paperclip_companies"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(UUID_TYPE, ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String(128), nullable=False)
    mission = Column(Text, default="")  # 公司使命
    status = Column(String(20), default="active")  # active | paused | archived
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class PaperclipAgent(Base):
    """Agent 雇员，可绑定 Hermes 插件、DeerFlow intent 或 agency 角色。"""
    __tablename__ = "paperclip_agents"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(UUID_TYPE, ForeignKey("paperclip_companies.id"), nullable=False, index=True)
    name = Column(String(128), nullable=False)
    title = Column(String(128), default="")  # 职位头衔
    role = Column(String(64), default="worker")  # ceo | cto | cmo | worker | reviewer
    provider = Column(String(64), default="hermes")  # hermes | deerflow | claude | codex | cursor | bash | http
    agent_ref = Column(String(128), default="")  # 关联的 Hermes 插件 ID 或 agency role ID
    parent_id = Column(UUID_TYPE, ForeignKey("paperclip_agents.id"), nullable=True)  # 上级 Agent
    heartbeat_interval_minutes = Column(Integer, default=240)  # 心跳间隔（分钟）
    heartbeat_enabled = Column(Boolean, default=True)
    monthly_budget_credits = Column(Float, default=1000.0)  # 月度预算（积分）
    used_credits = Column(Float, default=0.0)  # 已用积分
    status = Column(String(20), default="active")  # active | paused | terminated
    skills_json = Column(Text, default="[]")  # 技能列表 JSON
    config_json = Column(Text, default="{}")  # 额外配置
    last_heartbeat_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class PaperclipGoal(Base):
    """目标链：公司使命 -> 项目目标 -> Agent 任务。"""
    __tablename__ = "paperclip_goals"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(UUID_TYPE, ForeignKey("paperclip_companies.id"), nullable=False, index=True)
    parent_id = Column(UUID_TYPE, ForeignKey("paperclip_goals.id"), nullable=True)  # 上级目标
    owner_agent_id = Column(UUID_TYPE, ForeignKey("paperclip_agents.id"), nullable=True)  # 负责 Agent
    title = Column(String(256), nullable=False)
    description = Column(Text, default="")
    level = Column(String(20), default="task")  # mission | project | goal | task
    status = Column(String(20), default="active")  # active | completed | blocked | cancelled
    priority = Column(Integer, default=0)  # 0=最高
    progress = Column(Float, default=0.0)  # 0.0 ~ 1.0
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class PaperclipHeartbeat(Base):
    """心跳执行记录。"""
    __tablename__ = "paperclip_heartbeats"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(UUID_TYPE, ForeignKey("paperclip_agents.id"), nullable=False, index=True)
    company_id = Column(UUID_TYPE, ForeignKey("paperclip_companies.id"), nullable=False, index=True)
    status = Column(String(20), default="pending")  # pending | running | success | failed | skipped
    trigger = Column(String(20), default="schedule")  # schedule | manual | event
    tasks_checked = Column(Integer, default=0)
    tasks_executed = Column(Integer, default=0)
    credits_used = Column(Float, default=0.0)
    result_json = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class PaperclipApproval(Base):
    """审批门记录。"""
    __tablename__ = "paperclip_approvals"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(UUID_TYPE, ForeignKey("paperclip_companies.id"), nullable=False, index=True)
    agent_id = Column(UUID_TYPE, ForeignKey("paperclip_agents.id"), nullable=True)
    action_type = Column(String(64), nullable=False)  # hire_agent | fire_agent | budget_change | goal_change | task_execute
    action_payload_json = Column(Text, default="{}")
    status = Column(String(20), default="pending")  # pending | approved | rejected | expired
    reviewer_id = Column(UUID_TYPE, ForeignKey("users.id"), nullable=True)
    review_comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    reviewed_at = Column(DateTime(timezone=True), nullable=True)


class PaperclipTask(Base):
    """Agent 任务（绑定 DeerFlow job 或 Hermes 插件执行）。"""
    __tablename__ = "paperclip_tasks"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(UUID_TYPE, ForeignKey("paperclip_companies.id"), nullable=False, index=True)
    goal_id = Column(UUID_TYPE, ForeignKey("paperclip_goals.id"), nullable=True)
    assigned_agent_id = Column(UUID_TYPE, ForeignKey("paperclip_agents.id"), nullable=True)
    title = Column(String(256), nullable=False)
    description = Column(Text, default="")
    intent = Column(String(64), default="")  # DeerFlow intent 或 Hermes plugin kind
    status = Column(String(20), default="queued")  # queued | running | success | failed | blocked | cancelled
    priority = Column(Integer, default=0)
    deerflow_job_id = Column(UUID_TYPE, ForeignKey("deerflow_jobs.id"), nullable=True)  # 绑定 DeerFlow 任务
    result_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)
