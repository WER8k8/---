# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""License Model - 许可证管理模型（P1-5 扩展：设备指纹 + 授权码 + 套餐订单）"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from app.core.database import UUID_TYPE, Base


# ── 原有模型 ──

class License(Base):
    """许可证表模型"""
    __tablename__ = "licenses"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    license_key = Column(String(64), unique=True, nullable=False, index=True)
    tenant_id = Column(UUID_TYPE, ForeignKey("tenants.id"), nullable=True, index=True)
    plan_code = Column(String(50), nullable=False)
    status = Column(String(20), default="inactive", nullable=False, index=True)
    activated_at = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True))
    hardware_id = Column(String(255), nullable=True)
    max_devices = Column(Integer, default=1, nullable=False)
    ai_quota = Column(Integer, default=0, nullable=False)
    notes = Column(Text, nullable=True)
    created_by = Column(UUID_TYPE, ForeignKey("users.id"), nullable=True)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    tenant = relationship("Tenant", lazy="select")
    creator = relationship("User", lazy="select")
    def __repr__(self):
        """__repr__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return f"<License(key={self.license_key[:8]}..., status={self.status})>"


# ── P1-5 新增模型 ──

class DeviceFingerprint(Base):
    """设备指纹 —— 绑定用户到具体浏览器/设备，防止账号共享。"""
    __tablename__ = "device_fingerprints"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(UUID_TYPE, ForeignKey("users.id"), nullable=False, index=True)
    fingerprint_hash = Column(String(64), unique=True, nullable=False, index=True)
    device_info = Column(JSON, default=dict)  # {browser, os, screen, timezone, language}
    first_seen_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    last_seen_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class LicenseCode(Base):
    """授权码 —— 格式 TL1.xxxxx.xxxxx，激活后绑定设备。"""
    __tablename__ = "license_codes"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    code = Column(String(50), unique=True, nullable=False, index=True)
    plan_type = Column(String(20), nullable=False)  # half_year / yearly / trial
    user_id = Column(UUID_TYPE, ForeignKey("users.id"), nullable=True, index=True)
    device_fingerprint_id = Column(
        UUID_TYPE, ForeignKey("device_fingerprints.id"), nullable=True
    )
    activated_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    # 状态机：pending → activated → expired / revoked
    status = Column(String(20), nullable=False, default="pending", index=True)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )


class LicenseOrder(Base):
    """授权套餐订单 —— 用户购买后管理员确认开通。"""
    __tablename__ = "license_orders"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(UUID_TYPE, ForeignKey("users.id"), nullable=False, index=True)
    license_code_id = Column(UUID_TYPE, ForeignKey("license_codes.id"), nullable=True)
    plan_type = Column(String(20), nullable=False)  # half_year / yearly
    amount_cents = Column(Integer, nullable=False, default=0)  # 分
    payment_method = Column(String(30), nullable=True)  # alipay / wechat / bank / other
    payment_ref = Column(String(200), nullable=True)  # 交易单号/备注
    status = Column(String(20), nullable=False, default="pending", index=True)
    confirmed_by = Column(UUID_TYPE, ForeignKey("users.id"), nullable=True)
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
