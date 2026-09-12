"""
GEO Alert Models - 预警数据模型
从 sourcechain-geo-engine 的 models/alerts.py 转移而来
用于 GEO 排名监控、性能异常、询盘转化率等预警
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class AlertSeverity(str, Enum):
    """预警严重程度"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertType(str, Enum):
    """预警类型"""
    PERFORMANCE = "performance"
    AVAILABILITY = "availability"
    DATA_QUALITY = "data_quality"
    USER_BEHAVIOR = "user_behavior"
    BUSINESS = "business"
    SYSTEM = "system"
    SECURITY = "security"
    GEO_RANK = "geo_rank"  # GEO 排名异常
    GEO_INQUIRY = "geo_inquiry"  # GEO 询盘转化率异常


class AlertStatus(str, Enum):
    """预警状态"""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class AlertRuleCreate(BaseModel):
    """创建预警规则"""
    name: str = Field(..., min_length=1, max_length=255, description="规则名称")
    description: str = Field("", max_length=1000, description="规则描述")
    alert_type: AlertType = Field(..., description="预警类型")
    severity: AlertSeverity = Field(..., description="严重程度")
    enabled: bool = Field(True, description="是否启用")
    rule_config: dict[str, Any] = Field(default_factory=dict, description="规则配置")
    check_interval_seconds: int = Field(60, ge=10, description="检查间隔（秒）")


class AlertRuleResponse(AlertRuleCreate):
    """预警规则响应"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_triggered_at: Optional[datetime] = None
    trigger_count: int = 0


class AlertCreate(BaseModel):
    """创建预警"""
    rule_id: Optional[int] = Field(None, description="关联的规则ID")
    alert_type: AlertType = Field(..., description="预警类型")
    severity: AlertSeverity = Field(..., description="严重程度")
    title: str = Field(..., min_length=1, max_length=255, description="预警标题")
    description: str = Field(..., max_length=5000, description="预警描述")
    impact_scope: str = Field("", max_length=1000, description="影响范围")
    proposed_solution: str = Field("", max_length=2000, description="建议解决方案")
    extra_data: dict[str, Any] = Field(default_factory=dict, description="元数据")


class AlertResponse(AlertCreate):
    """预警响应"""
    id: int
    status: AlertStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    resolved_by: Optional[str] = None
    resolution_notes: Optional[str] = None


class AlertAcknowledge(BaseModel):
    """确认预警"""
    acknowledged_by: str = Field(..., min_length=1, max_length=100)
    notes: str = Field("", max_length=2000)


class AlertResolve(BaseModel):
    """解决预警"""
    resolved_by: str = Field(..., min_length=1, max_length=100)
    resolution_notes: str = Field(..., min_length=1, max_length=2000)


class AlertListResponse(BaseModel):
    """预警列表响应"""
    total: int
    page: int
    page_size: int
    items: list[AlertResponse]


class AlertStatisticsResponse(BaseModel):
    """预警统计响应"""
    total_alerts: int
    active_alerts: int
    resolved_today: int
    by_severity: dict[str, int]
    by_type: dict[str, int]
    trend_last_7_days: list[dict[str, Any]]
