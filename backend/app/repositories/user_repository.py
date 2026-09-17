# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""用户数据访问层

PII 字段加密说明：
    - email 列在数据库中以 AES-256-GCM 加密存储。
    - create / update 时自动加密；读取时自动解密。
    - 通过 set_committed_value 设置解密值，避免 dirty tracking 导致明文回写。
    - 搜索方法（search_users）对加密字段仅能精确匹配，不支持模糊搜索。
    - try/except 包裹解密操作，兼容历史未加密数据。
"""

from typing import List, Optional

from sqlalchemy import or_, select
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import set_committed_value

from app.core.field_crypto import decrypt_field, encrypt_field
from app.models.user import OperationLog, User
from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    """用户Repository（email 字段自动加解密）"""
    def __init__(self, db: Session):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param db: 参数 db
        :return: 返回处理结果。
        """
        super().__init__(db, User)

    # ------------------------------------------------------------------
    # 内部辅助
    # ------------------------------------------------------------------
    def _decrypt_user_email(self, user: User) -> None:
        """原地解密 user.email，不触发 ORM dirty tracking。兼容历史明文数据。"""
        if not user.email:
            return
        try:
            set_committed_value(user, "email", decrypt_field(user.email))
        except Exception:
            pass  # 历史明文数据或解密失败，保持原值

    def _decrypt_user_list(self, users: List[User]) -> List[User]:
        """_decrypt_user_list。

        参数说明：
        :param self: 参数 self
        :param users: 参数 users
        :return: 返回处理结果。
        """
        for u in users:
            self._decrypt_user_email(u)
        return users

    # ------------------------------------------------------------------
    # 写操作：加密存储
    # ------------------------------------------------------------------
    def create(self, **kwargs) -> User:
        """create。

        参数说明：
        :param self: 参数 self
        :param **kwargs: 参数 **kwargs
        :return: 返回处理结果。
        """
        if "email" in kwargs and kwargs["email"]:
            kwargs["email"] = encrypt_field(kwargs["email"])
        return super().create(**kwargs)

    def update(self, id: str, **kwargs) -> Optional[User]:
        """update。

        参数说明：
        :param self: 参数 self
        :param id: 参数 id
        :param **kwargs: 参数 **kwargs
        :return: 返回处理结果。
        """
        if "email" in kwargs and kwargs["email"]:
            kwargs["email"] = encrypt_field(kwargs["email"])
        return super().update(id, **kwargs)

    # ------------------------------------------------------------------
    # 读操作：解密 + 搜索加密
    # ------------------------------------------------------------------
    def get_by_id(self, id: str) -> Optional[User]:
        """get_by_id。

        参数说明：
        :param self: 参数 self
        :param id: 参数 id
        :return: 返回处理结果。
        """
        user = super().get_by_id(id)
        if user:
            self._decrypt_user_email(user)
        return user

    def get_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        user = self.db.execute(
            select(User).filter(User.username == username, User.is_active)
        ).scalar_one_or_none()
        if user:
            self._decrypt_user_email(user)
        return user

    def get_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户（加密精确匹配）"""
        encrypted = encrypt_field(email)
        user = self.db.execute(
            select(User).filter(
                User.email == encrypted,
                User.is_active,
            )
        ).scalar_one_or_none()
        if user:
            self._decrypt_user_email(user)
        return user

    def get_by_username_or_email(
            self, username_or_email: str) -> Optional[User]:
        """根据用户名或邮箱获取用户"""
        encrypted = encrypt_field(username_or_email)
        user = self.db.execute(
            select(User).filter(
                or_(
                    User.username == username_or_email,
                    User.email == encrypted,
                ),
                User.is_active,
            )
        ).scalar_one_or_none()
        if user:
            self._decrypt_user_email(user)
        return user

    def get_by_role(self, role: str) -> List[User]:
        """根据角色获取用户列表"""
        users = self.db.execute(
            select(User).filter(
                User.role == role,
                User.is_active,
            )
        ).scalars().all()
        return self._decrypt_user_list(users)

    def search_users(self, keyword: str) -> List[User]:
        """搜索用户（用户名、邮箱、显示名）

        注意：加密后 email ILIKE 无法工作，仅能匹配用户名和显示名。
        如需按邮箱搜索，请使用 get_by_email 精确匹配。
        """
        users = (
            self.db.execute(
                select(User).filter(
                    User.is_active,
                    or_(
                        User.username.ilike(f"%{keyword}%"),
                        User.email.ilike(f"%{keyword}%"),
                        User.display_name.ilike(f"%{keyword}%"),
                    ),
                )
            )
            .scalars()
            .all()
        )
        return self._decrypt_user_list(users)

    def exists_by_username(self, username: str) -> bool:
        """检查用户名是否存在"""
        return self.db.execute(
            select(User).filter(
                User.username == username)).scalar() is not None

    def exists_by_email(self, email: str) -> bool:
        """检查邮箱是否存在（加密精确匹配）"""
        encrypted = encrypt_field(email)
        return self.db.execute(
            select(User).filter(
                User.email == encrypted)).scalar() is not None


class OperationLogRepository(BaseRepository[OperationLog]):
    """操作日志Repository"""
    def __init__(self, db: Session):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param db: 参数 db
        :return: 返回处理结果。
        """
        super().__init__(db, OperationLog)

    def get_by_user_id(
            self,
            user_id: str,
            limit: int = 100) -> List[OperationLog]:
        """获取用户操作日志"""
        return (
            self.db.execute(
                select(OperationLog)
                .filter(OperationLog.user_id == user_id)
                .order_by(OperationLog.created_at.desc())
                .limit(limit)
            )
            .scalars()
            .all()
        )

    def get_recent_logs(self, limit: int = 50) -> List[OperationLog]:
        """获取最近操作日志"""
        return (
            self.db.execute(
                select(OperationLog).order_by(
                    OperationLog.created_at.desc()).limit(limit)).scalars().all())

    def create_log(
        self,
        user_id: str,
        action: str,
        resource_type: str,
        resource_id: str = None,
        detail: str = None,
        ip_address: str = None,
    ):
        """创建操作日志"""
        log = OperationLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            detail=detail,
            ip_address=ip_address,
        )
        self.db.add(log)
        self.db.commit()
        return log
