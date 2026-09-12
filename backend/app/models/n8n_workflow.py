"""n8n 工作流注册表模型。"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
)

from app.core.database import UUID_TYPE, Base


class N8nWorkflow(Base):
    """n8n 工作流注册表。

    存储已注册的 n8n 工作流配置，用于触发和Webhook管理。
    """
    __tablename__ = "n8n_workflows"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(UUID_TYPE, ForeignKey("tenants.id"), nullable=True, index=True)
    workflow_id = Column(String(100), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    endpoint_url = Column(String(500), nullable=False)
    auth_type = Column(String(30), default="none")
    auth_config = Column(JSON, default=dict)
    scene = Column(String(50), nullable=True, index=True)
    enabled = Column(Boolean, default=True, nullable=False)
    last_triggered_at = Column(DateTime(timezone=True), nullable=True)
    trigger_count = Column(Integer, default=0)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    __table_args__ = (
        Index("idx_n8n_workflow_scene", "scene", "enabled"),
    )
