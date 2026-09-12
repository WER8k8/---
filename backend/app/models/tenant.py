"""SaaS多租户模型"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import UUID_TYPE, Base


class TenantPlan(Base):
    """套餐定义"""
    __tablename__ = "tenant_plans"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)  # 免费版/基础版/专业版/企业版/旗舰版
    code = Column(String(50), unique=True, nullable=False, index=True)  # free/basic/pro/enterprise/flagship
    price_monthly = Column(Integer, default=0, nullable=False)  # 月付价格(分)
    price_yearly = Column(Integer, default=0, nullable=False)   # 年付价格(分)
    max_users = Column(Integer, default=1, nullable=False)      # 最大用户数
    max_sites = Column(Integer, default=1, nullable=False)      # 最大站点数
    max_products = Column(Integer, default=10, nullable=False)  # 最大产品数
    max_ai_quota = Column(Integer, default=0, nullable=False)   # AI调用额度/月
    features = Column(Text, default="[]")                        # JSON: 功能列表 ["seo","globalization","international",...]
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    tenants = relationship("Tenant", back_populates="plan", lazy="select")
    subscriptions = relationship("TenantSubscription", back_populates="plan", lazy="select")


class Tenant(Base):
    """租户"""
    __tablename__ = "tenants"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), nullable=False)
    contact_name = Column(String(100))
    contact_email = Column(String(200))
    contact_phone = Column(String(50))
    domain = Column(String(200), unique=True, nullable=False, index=True)  # 客户子域名
    custom_domains = Column(Text, default="")  # JSON数组，如 ["www.abc.com", "abc.com"]
    plan_id = Column(UUID_TYPE, ForeignKey("tenant_plans.id"), nullable=False, index=True)
    status = Column(String(20), default="trial", nullable=False, index=True)  # trial/active/suspended/cancelled
    trial_ends_at = Column(DateTime(timezone=True))
    subscribed_at = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True))
    ai_quota_used = Column(Integer, default=0, nullable=False)
    purchased_token_bonus = Column(Integer, default=0, nullable=False)  # 已购 Token 额度（充值/推荐奖励，独立于套餐基础额度）
    storage_used = Column(Integer, default=0, nullable=False)  # MB
    settings = Column(Text)  # JSON 自定义设置
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    plan = relationship("TenantPlan", back_populates="tenants", lazy="joined")
    subscriptions = relationship("TenantSubscription", back_populates="tenant", lazy="select")
    invoices = relationship("TenantInvoice", back_populates="tenant", lazy="select")
    ssl_certificates = relationship("SSLCertificate", back_populates="tenant", lazy="select")


class TenantSubscription(Base):
    """订阅记录"""
    __tablename__ = "tenant_subscriptions"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(UUID_TYPE, ForeignKey("tenants.id"), nullable=False, index=True)
    plan_id = Column(UUID_TYPE, ForeignKey("tenant_plans.id"), nullable=False, index=True)
    billing_cycle = Column(String(20), default="monthly", nullable=False)  # monthly/yearly
    amount = Column(Integer, default=0, nullable=False)
    status = Column(String(20), default="active", nullable=False, index=True)  # active/cancelled/expired
    started_at = Column(DateTime(timezone=True), nullable=False)
    ended_at = Column(DateTime(timezone=True))
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    tenant = relationship("Tenant", back_populates="subscriptions", lazy="joined")
    plan = relationship("TenantPlan", back_populates="subscriptions", lazy="joined")
    invoices = relationship("TenantInvoice", back_populates="subscription", lazy="select")


class TenantInvoice(Base):
    """账单"""
    __tablename__ = "tenant_invoices"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(UUID_TYPE, ForeignKey("tenants.id"), nullable=False, index=True)
    subscription_id = Column(UUID_TYPE, ForeignKey("tenant_subscriptions.id"), nullable=True, index=True)
    amount = Column(Integer, default=0, nullable=False)
    status = Column(String(20), default="pending", nullable=False, index=True)  # pending/paid/overdue/cancelled
    paid_at = Column(DateTime(timezone=True))
    due_at = Column(DateTime(timezone=True))
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    tenant = relationship("Tenant", back_populates="invoices", lazy="joined")
    subscription = relationship("TenantSubscription", back_populates="invoices", lazy="joined")


class UserTenant(Base):
    """用户-租户关联"""
    __tablename__ = "user_tenants"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(UUID_TYPE, ForeignKey("users.id"), nullable=False, index=True)
    tenant_id = Column(UUID_TYPE, ForeignKey("tenants.id"), nullable=False, index=True)
    role = Column(String(20), default="admin")
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
