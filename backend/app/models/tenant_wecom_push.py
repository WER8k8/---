"""租户企微推送配置 — 客户自有 CorpID / 应用 / 接收人。"""

from __future__ import annotations

import uuid as _uuid_lib

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.sql import func

from app.core.database import Base, UUID_TYPE


class TenantWecomPushConfig(Base):
    __tablename__ = "tenant_wecom_push_configs"
    id = Column(String(36), primary_key=True, default=lambda: str(_uuid_lib.uuid4()))
    tenant_id = Column(UUID_TYPE, ForeignKey("tenants.id"), nullable=False, unique=True, index=True)
    enabled = Column(Boolean, nullable=False, default=False)
    corp_id = Column(String(64), nullable=True)
    agent_id = Column(String(32), nullable=True)
    agent_secret = Column(String(200), nullable=True)  # 客户密钥，仅服务端使用
    push_userids = Column(Text, nullable=True)  # 企微 UserID，| 或 , 分隔
    webhook_url = Column(String(500), nullable=True)  # 客户销售群机器人（可选）
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
