# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""设备指纹 + 授权码 + 套餐订单 服务（P1-5）。"""

from __future__ import annotations

import hashlib
import secrets
import string
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.license import DeviceFingerprint, LicenseCode, LicenseOrder

# ── 常量 ──
PLAN_DURATIONS = {
    "half_year": timedelta(days=182),
    "yearly": timedelta(days=365),
    "trial": timedelta(days=14),
}
PLAN_PRICES = {
    "half_year": 49900,   # 499 元 = 49900 分
    "yearly": 79900,
    "trial": 0,
}
CODE_PREFIX = "TL1"


def generate_license_code() -> str:
    """生成授权码：TL1.xxxxx.xxxxx（10 位随机，易人工核销）。"""
    alphabet = string.ascii_lowercase + string.digits
    part1 = "".join(secrets.choice(alphabet) for _ in range(5))
    part2 = "".join(secrets.choice(alphabet) for _ in range(5))
    return f"{CODE_PREFIX}.{part1}.{part2}"


def get_or_create_device(
    db: Session,
    user_id: str,
    fingerprint_hash: str,
    device_info: Optional[dict] = None,
) -> DeviceFingerprint:
    """获取或创建设备指纹记录。"""
    device = (
        db.query(DeviceFingerprint)
        .filter(DeviceFingerprint.fingerprint_hash == fingerprint_hash)
        .first()
    )
    if device:
        device.last_seen_at = datetime.now(timezone.utc)
        if device_info:
            device.device_info = device_info
        db.flush()
        return device

    device = DeviceFingerprint(
        user_id=user_id,
        fingerprint_hash=fingerprint_hash,
        device_info=device_info or {},
    )
    db.add(device)
    db.flush()
    return device


def create_order(
    db: Session,
    user_id: str,
    plan_type: str,
    payment_method: Optional[str] = None,
    payment_ref: Optional[str] = None,
) -> LicenseOrder:
    """创建授权套餐订单（待管理员确认）。"""
    order = LicenseOrder(
        user_id=user_id,
        plan_type=plan_type,
        amount_cents=PLAN_PRICES.get(plan_type, 0),
        payment_method=payment_method,
        payment_ref=payment_ref,
        status="pending",
    )
    db.add(order)
    db.flush()
    return order


def activate_code(
    db: Session,
    code: str,
    user_id: str,
    fingerprint_hash: str,
) -> LicenseCode:
    """激活授权码并绑定设备。

    Raises:
        ValueError: 授权码不存在/已激活/已过期
    """
    lic = (
        db.query(LicenseCode)
        .filter(LicenseCode.code == code)
        .with_for_update()  # 行锁，防止并发激活
        .first()
    )
    if not lic:
        raise ValueError("授权码不存在")
    if lic.status == "activated":
        raise ValueError("授权码已激活")
    if lic.status in ("expired", "revoked"):
        raise ValueError(f"授权码已{lic.status}")

    # 获取或创建设备
    device = get_or_create_device(db, user_id, fingerprint_hash)
    # 激活
    now = datetime.now(timezone.utc)
    duration = PLAN_DURATIONS.get(lic.plan_type, PLAN_DURATIONS["half_year"])
    lic.user_id = user_id
    lic.device_fingerprint_id = str(device.id)
    lic.activated_at = now
    lic.expires_at = now + duration
    lic.status = "activated"
    db.flush()
    return lic


def check_license_status(db: Session, user_id: str) -> dict:
    """查询当前用户的授权状态（只读，不修改数据库）。"""
    lic = (
        db.query(LicenseCode)
        .filter(LicenseCode.user_id == user_id, LicenseCode.status == "activated")
        .order_by(LicenseCode.expires_at.desc())
        .first()
    )
    if not lic:
        return {"status": "inactive", "expired": True, "expires_at": None, "plan_type": None}

    now = datetime.now(timezone.utc)
    expired = lic.expires_at is not None and lic.expires_at < now
    # 只在读取时计算状态，不修改数据库（避免查询函数有写入副作用）
    effective_status = "expired" if expired else lic.status
    return {
        "status": effective_status,
        "expired": expired,
        "expires_at": lic.expires_at.isoformat() if lic.expires_at else None,
        "plan_type": lic.plan_type,
        "code": lic.code,
    }


def confirm_order(
    db: Session,
    order_id: str,
    admin_id: str,
) -> LicenseCode:
    """管理员确认订单 → 生成授权码。"""
    order = (
        db.query(LicenseOrder)
        .filter(LicenseOrder.id == order_id)
        .with_for_update()  # 行锁，防止重复确认
        .first()
    )
    if not order:
        raise ValueError("订单不存在")
    if order.status != "pending":
        raise ValueError(f"订单状态为 {order.status}，无法确认")

    # 生成授权码（碰撞重试）
    from sqlalchemy.exc import IntegrityError
    lic = None
    for _ in range(5):
        code = generate_license_code()
        lic = LicenseCode(
            code=code,
            plan_type=order.plan_type,
            status="pending",
        )
        db.add(lic)
        try:
            db.flush()
            break
        except IntegrityError:
            db.rollback()
            lic = None
    if not lic:
        raise ValueError("授权码生成失败，请重试")

    # 关联订单
    order.license_code_id = str(lic.id)
    order.status = "confirmed"
    order.confirmed_by = admin_id
    order.confirmed_at = datetime.now(timezone.utc)
    db.flush()
    return lic
