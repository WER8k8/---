# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""超级管理员 RBAC 模型"""

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import (Boolean, Column, DateTime, ForeignKey, Integer,
                        String, Text, UniqueConstraint)
from sqlalchemy.orm import relationship

from app.core.database import UUID_TYPE, Base
logger = logging.getLogger(__name__)


class AdminRole(Base):
    """管理员角色"""
    __tablename__ = "admin_roles"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(200))
    is_system = Column(Boolean, default=False, nullable=False)
    sort_order = Column(Integer, default=0)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    permissions = relationship(
        "AdminPermission",
        secondary="role_permissions",
        back_populates="roles",
        lazy="selectin",
    )
    users = relationship("User", back_populates="role_rel", foreign_keys="User.role_id")


class AdminPermission(Base):
    """权限码"""
    __tablename__ = "admin_permissions"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    code = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    group_name = Column(String(50), index=True)
    description = Column(String(200))
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    roles = relationship(
        "AdminRole",
        secondary="role_permissions",
        back_populates="permissions",
        lazy="selectin",
    )


class RolePermission(Base):
    """角色-权限关联表"""
    __tablename__ = "role_permissions"
    __table_args__ = (
        UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),
    )
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    role_id = Column(
        UUID_TYPE,
        ForeignKey("admin_roles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    permission_id = Column(
        UUID_TYPE,
        ForeignKey("admin_permissions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )


class AdminMenu(Base):
    """后台菜单树"""
    __tablename__ = "admin_menus"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    parent_id = Column(UUID_TYPE, ForeignKey("admin_menus.id"), nullable=True, index=True)
    title = Column(String(50), nullable=False)
    icon = Column(String(50))
    path = Column(String(200))
    permission_code = Column(String(100), index=True)
    sort_order = Column(Integer, default=0)
    visible = Column(Boolean, default=True, nullable=False)
    component_path = Column(String(300))
    meta_json = Column(Text)  # JSON: { badge, target, external }
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    children = relationship("AdminMenu", backref="parent", remote_side=[id])


class LoginLog(Base):
    """超管登录日志

    FIX-B4: 清理策略见下方 cleanup_login_logs() 函数。
    Celery 定时任务应每 90 天调用一次该函数，避免表无限增长。
    """
    __tablename__ = "super_admin_login_logs"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(UUID_TYPE, ForeignKey("users.id"), nullable=True, index=True)
    username = Column(String(50), nullable=False)
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    success = Column(Boolean, default=True, nullable=False)
    fail_reason = Column(String(200))
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )


# ── FIX-B4: 日志清理工具 ──

def cleanup_login_logs(
    db_session,
    retention_days: int = 90,
) -> int:
    """清理超管登录日志中超过 retention_days 的旧记录。

    Args:
        db_session: SQLAlchemy Session
        retention_days: 保留天数，默认 90 天

    Returns:
        删除的记录数

    Usage:
        # 在 Celery 定时任务中调用：
        from app.models.admin import cleanup_login_logs
        from app.db.session import SessionLocal
        db = SessionLocal()
        try:
            deleted = cleanup_login_logs(db, retention_days=90)
            logger.info(f"清理了 {deleted} 条过期登录日志")
        finally:
            db.close()
    """
    from datetime import timedelta
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    deleted = (
        db_session.query(LoginLog)
        .filter(LoginLog.created_at < cutoff)
        .delete(synchronize_session=False)
    )
    db_session.commit()
    return deleted
