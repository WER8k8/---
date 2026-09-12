"""静态 IP 槽位与浏览器指纹环境"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, String, Text

from app.core.database import UUID_TYPE, Base

# slot_status: available(池中待分配) | provisioning(开通过程中) | assigned(已分配租户) |
#              pending_manual(待运营) | failed(失败) | disabled(禁用/过期)


class EgressEndpoint(Base):
    __tablename__ = "egress_endpoints"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    region = Column(String(20), nullable=False, index=True)  # cn | global
    host = Column(String(255), nullable=False)
    port = Column(Integer, default=0)
    provider = Column(String(100))
    slot_status = Column(String(20), default="available")
    tenant_id = Column(UUID_TYPE, ForeignKey("tenants.id"), nullable=True, index=True)
    label = Column(String(200))
    upstream_ref = Column(String(200), nullable=True)
    proxy_username = Column(String(200), nullable=True)
    proxy_password = Column(String(200), nullable=True)
    qc_meta = Column(JSON, nullable=True)
    provision_error = Column(String(500), nullable=True)
    # IPRoyal 长期养号：订单ID、到期时间、续费次数
    iproyal_order_id = Column(Integer, nullable=True, index=True)
    expire_date = Column(DateTime(timezone=True), nullable=True)
    renew_count = Column(Integer, default=0, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class EgressProvisionJob(Base):
    """按需向上游采购静态 ISP 并绑定租户槽位。"""
    __tablename__ = "egress_provision_jobs"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(UUID_TYPE, ForeignKey("tenants.id"), nullable=False, index=True)
    endpoint_id = Column(
        UUID_TYPE, ForeignKey("egress_endpoints.id"), nullable=False, index=True
    )
    provider = Column(String(50), nullable=False, default="mock")
    region = Column(String(20), nullable=False, default="global")
    country = Column(String(10), nullable=False, default="US")
    status = Column(
        String(20),
        default="queued",
        nullable=False,
        index=True,
    )  # queued | running | succeeded | failed
    attempts = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)
    upstream_ref = Column(String(200), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)


class EgressCostRecord(Base):
    """每次采购/续费的成本记录。"""
    __tablename__ = "egress_cost_records"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    endpoint_id = Column(
        UUID_TYPE, ForeignKey("egress_endpoints.id", ondelete="SET NULL"), nullable=True, index=True
    )
    provider = Column(String(50), nullable=False, default="iproyal")
    operation = Column(
        String(20), nullable=False, default="purchase"
    )  # purchase | renew | renew_failed
    iproyal_order_id = Column(Integer, nullable=True, index=True)
    quantity = Column(Integer, default=1)
    unit_price_cents = Column(Integer, default=0)   # 单价（美分）
    total_price_cents = Column(Integer, default=0)   # 总价（美分）
    currency = Column(String(10), default="USD")
    plan_days = Column(Integer, default=60)          # 购买天数
    raw_response = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )


class EgressPoolReplenishJob(Base):
    """缓冲池批量补充任务。"""
    __tablename__ = "egress_pool_replenish_jobs"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    status = Column(
        String(20), nullable=False, default="queued"
    )  # queued | ordering | stocking | completed | failed
    batch_size = Column(Integer, default=5)
    iproyal_order_id = Column(Integer, nullable=True)
    endpoints_created = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    finished_at = Column(DateTime(timezone=True), nullable=True)


class BrowserProfile(Base):
    __tablename__ = "browser_profiles"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(UUID_TYPE, ForeignKey("tenants.id"), nullable=True, index=True)
    egress_endpoint_id = Column(
        UUID_TYPE, ForeignKey("egress_endpoints.id"), nullable=True, index=True
    )
    name = Column(String(200), nullable=False)
    fingerprint = Column(JSON, default=dict)
    platform_account_id = Column(
        UUID_TYPE, ForeignKey("platform_accounts.id"), nullable=True, index=True
    )
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class EgressSupplier(Base):
    """平台静态 IP 上游供应商（可增删改、切换启用）。"""
    __tablename__ = "egress_suppliers"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    code = Column(String(50), nullable=False, unique=True, index=True)
    name = Column(String(100), nullable=False)
    subtitle = Column(String(200))
    adapter = Column(String(30), nullable=False, default="manual")
    ip_type = Column(String(40), nullable=False, default="static_residential")
    long_term_fixed = Column(Boolean, default=True, nullable=False)
    description = Column(Text)
    config_json = Column(JSON, default=dict)
    supports_pool_replenish = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=False, nullable=False, index=True)
    is_builtin = Column(Boolean, default=False, nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
