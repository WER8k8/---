"""用户服务层"""

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.security import (create_access_token, get_password_hash,
                               verify_password)
from app.models.user import User
from app.repositories.user_repository import (OperationLogRepository,
                                              UserRepository)
from app.schemas.user import UserCreate, UserResponse, UserUpdate


class UserService:
    """用户服务"""
    def __init__(self, db: Session):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param db: 参数 db
        :return: 返回处理结果。
        """
        self.user_repo = UserRepository(db)
        self.log_repo = OperationLogRepository(db)

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """根据ID获取用户"""
        return self.user_repo.get_by_id(user_id)

    def get_user_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        return self.user_repo.get_by_username(username)

    def get_user_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        return self.user_repo.get_by_email(email)

    def authenticate(
            self,
            username_or_email: str,
            password: str) -> Optional[User]:
        """验证用户身份"""
        user = self.user_repo.get_by_username_or_email(username_or_email)
        if user and verify_password(password, user.hashed_password):
            return user
        return None

    def create_user(self, data: UserCreate, created_by: str = None) -> User:
        """创建用户"""
        # 检查用户名是否已存在
        if self.user_repo.exists_by_username(data.username):
            raise ValueError("用户名已存在")

        # 检查邮箱是否已存在
        if self.user_repo.exists_by_email(data.email):
            raise ValueError("邮箱已存在")

        # 创建用户
        user = self.user_repo.create(
            username=data.username,
            email=data.email,
            hashed_password=get_password_hash(data.password),
            display_name=data.display_name,
            role=data.role or "viewer",
            is_active=True,
        )
        # 记录操作日志
        if created_by:
            self.log_repo.create_log(
                user_id=created_by,
                action="create",
                resource_type="user",
                resource_id=user.id,
                detail=f"创建用户: {user.username}",
            )

        return user

    def update_user(self, user_id: str, data: UserUpdate,
                    updated_by: str = None) -> Optional[User]:
        """更新用户"""
        update_data = data.model_dump(exclude_unset=True)
        # 如果包含密码，需要加密
        if "password" in update_data:
            update_data["hashed_password"] = get_password_hash(
                update_data.pop("password"))

        user = self.user_repo.update(user_id, **update_data)
        if user and updated_by:
            self.log_repo.create_log(
                user_id=updated_by,
                action="update",
                resource_type="user",
                resource_id=user.id,
                detail=f"更新用户: {user.username}",
            )

        return user

    def delete_user(self, user_id: str, deleted_by: str = None) -> bool:
        """删除用户（软删除）"""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return False

        # 软删除
        self.user_repo.update(user_id, is_active=False)
        if deleted_by:
            self.log_repo.create_log(
                user_id=deleted_by,
                action="delete",
                resource_type="user",
                resource_id=user_id,
                detail=f"删除用户: {user.username}",
            )

        return True

    def list_users(self,
                   page: int = 1,
                   page_size: int = 20,
                   role: str = None,
                   search: str = None) -> tuple[List[User],
                                                int]:
        """分页获取用户列表"""
        if search:
            users = self.user_repo.search_users(search)
            if role:
                users = [u for u in users if u.role == role]
            return users, len(users)
        if role:
            users = self.user_repo.get_by_role(role)
            return users, len(users)
        return self.user_repo.get_paginated(page=page, page_size=page_size)

    def get_users_by_role(self, role: str) -> List[User]:
        """根据角色获取用户"""
        return self.user_repo.get_by_role(role)

    def create_access_token(self, user: User) -> str:
        """创建访问令牌"""
        return create_access_token(
            data={
                "sub": str(
                    user.id),
                "role": user.role})

    def record_login(self, user: User):
        """记录登录时间"""
        self.user_repo.update(user.id, last_login=datetime.now(timezone.utc))

    def get_operation_logs(self, user_id: str = None, limit: int = 50) -> List:
        """获取操作日志"""
        if user_id:
            return self.log_repo.get_by_user_id(user_id, limit)
        return self.log_repo.get_recent_logs(limit)

    def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        """修改用户密码"""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return False
        if not verify_password(old_password, user.hashed_password):
            return False
        self.user_repo.update(user_id, hashed_password=get_password_hash(new_password), is_default_password=False)
        return True

    def record_operation(
        self,
        user_id: str,
        action: str,
        resource_type: str,
        resource_id: str = None,
        detail: str = None,
        ip_address: str = None,
    ):
        """记录操作日志"""
        self.log_repo.create_log(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            detail=detail,
            ip_address=ip_address,
        )
