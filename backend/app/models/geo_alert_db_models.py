# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""GEO Alert Models - SQLAlchemy 模型
GEO 专用预警系统，与现有 alert.py (AlertRule/AlertEvent) 并存
新表名：geo_alert_rules, geo_alerts, geo_alert_histories
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text, JSON, ForeignKey

from app.core.database import UUID_TYPE, Base


class GEOAlertRule(Base):
    """GEO 预警规则 - 支持 GEO 排名、询盘转化率等专用检查器"""
    __tablename__ = "geo_alert_rules"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    alert_type = Column(String(50), nullable=False, index=True)
    # 类型：performance, availability, data_quality, user_behavior, business, system, security, geo_rank, geo_inquiry
    severity = Column(String(20), nullable=False)
    # 严重程度：info, warning, error, critical
    enabled = Column(Boolean, default=True, nullable=False)
    rule_config = Column(JSON, default=dict)
    # 规则配置：{type: "geo_rank_drop", keyword: "...", baseline_rank: 10, drop_threshold: 5}
    check_interval_seconds = Column(Integer, default=60)
    last_triggered_at = Column(DateTime(timezone=True))
    trigger_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)


class GEOAlert(Base):
    """GEO 预警实例 - 规则触发后创建的预警记录"""
    __tablename__ = "geo_alerts"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    rule_id = Column(UUID_TYPE, ForeignKey("geo_alert_rules.id", ondelete="SET NULL"), index=True)
    alert_type = Column(String(50), nullable=False, index=True)
    severity = Column(String(20), nullable=False, index=True)
    status = Column(String(20), default="active", index=True)
    # 状态：active, acknowledged, resolved, dismissed
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    impact_scope = Column(Text)
    proposed_solution = Column(Text)
    extra_data = Column(JSON, default=dict)  # 原来是 metadata（SQLAlchemy 保留字）
    acknowledged_at = Column(DateTime(timezone=True))
    acknowledged_by = Column(String(100))
    resolved_at = Column(DateTime(timezone=True))
    resolved_by = Column(String(100))
    resolution_notes = Column(Text)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)


class GEOAlertHistory(Base):
    """GEO 预警历史 - 记录预警状态变更历史"""
    __tablename__ = "geo_alert_histories"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    alert_id = Column(UUID_TYPE, ForeignKey("geo_alerts.id", ondelete="CASCADE"), index=True)
    action_type = Column(String(50), nullable=False)
    # 动作类型：created, acknowledged, resolved
    action_by = Column(String(100))
    action_notes = Column(Text)
    old_status = Column(String(20))
    new_status = Column(String(20))
    extra_data = Column(JSON, default=dict)  # 原来是 metadata（SQLAlchemy 保留字）
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
