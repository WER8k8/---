# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""租户域名状态真源（修正设计稿 模块1 / Production Gate G2）。

为什么需要本表：既有绑定入口（routes/domain.py）把域名存 `tenant.custom_domains`
JSON —— 无法承载验证状态机、主域唯一性、激活语义，且 middleware 对 JSON 命中
即解析（**未验证域名也公开**，违反 G2 红线）。本表作为状态真源：

- verification_status：pending → verified / failed（DNS TXT token 或 CNAME 探测）
- ssl_status：pending / issued / failed / expired（桥接 ssl_certificate_service）
- is_primary：每租户唯一（服务层保证）；未 verified 不得设主域
- is_active：激活后 middleware 才把该 Host 解析到租户

与 legacy 的关系：`tenant.custom_domains` JSON 进入只读兼容（存量命中仍可解析，
标注 deprecated）；新建绑定只写本表，验证+激活后才进入公开解析 —— 收敛完成后
JSON 路径下线（对照表 T1 收敛项）。
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
)

from app.core.database import UUID_TYPE, Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TenantDomain(Base):
    """租户自定义域名（验证/SSL/主域/激活 状态真源）。"""

    __tablename__ = "tenant_domains"
    __table_args__ = (
        UniqueConstraint("normalized_hostname", name="uq_tenant_domains_normalized"),
        Index("ix_tenant_domains_tenant", "tenant_id"),
        Index("ix_tenant_domains_verify", "verification_status"),
    )

    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(UUID_TYPE, ForeignKey("tenants.id"), nullable=False)
    hostname = Column(String(255), nullable=False)
    normalized_hostname = Column(String(255), nullable=False)
    domain_type = Column(String(30), nullable=False, default="custom")  # system_subdomain / custom
    verification_method = Column(String(20), nullable=False, default="dns_txt")  # dns_txt / dns_cname
    verification_token_hash = Column(String(128), nullable=True)  # sha256(token)
    verification_status = Column(String(20), nullable=False, default="pending")  # pending/verified/failed
    verification_failed_reason = Column(String(255), nullable=True)
    ssl_status = Column(String(20), nullable=False, default="pending")  # pending/issued/failed/expired
    is_primary = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=False)
    canonical_redirect_to = Column(String(255), nullable=True)
    last_verified_at = Column(DateTime(timezone=True), nullable=True)
    last_ssl_checked_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)
