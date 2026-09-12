"""创建测试用户脚本 - 用于开发和测试"""

import os
import logging

logger = logging.getLogger(__name__)

import sys

sys.path.insert(0, os.path.dirname(__file__))

# 设置环境变量
os.environ["ENVIRONMENT"] = "development"
os.environ["SECRET_KEY"] = "dev-secret-key-for-development-only-keep-it-safe-123456"
os.environ["JWT_SECRET_KEY"] = "dev-secret-key-for-development-only-keep-it-safe-123456"

from app.db.session import SessionLocal, init_db
from app.models.user import User
from app.core.security import get_password_hash
from datetime import datetime, timezone
import uuid


def create_test_users():
    """创建测试用户"""
    init_db()
    db = SessionLocal()

    try:
        # 检查是否已存在测试用户
        test_users = [
            {
                "username": "admin",
                "email": "admin@example.com",
                "password": "admin123",
                "role": "super_admin",
                "is_active": True,
            },
            {
                "username": "province_agent_demo",
                "email": "province_agent@example.com",
                "password": "ProvinceAgent@2026!",
                "role": "l2",
                "is_active": True,
            },
            {
                "username": "city_agent_demo",
                "email": "city_agent@example.com",
                "password": "CityAgent@2026!",
                "role": "l3",
                "is_active": True,
            },
            {
                "username": "tenant_demo",
                "email": "tenant_demo@example.com",
                "password": "TenantDemo@2026!",
                "role": "tenant_admin",
                "is_active": True,
            },
            {
                "username": "editor",
                "email": "editor@example.com",
                "password": "editor123",
                "role": "editor",
                "is_active": True,
            },
            {
                "username": "sales",
                "email": "sales@example.com",
                "password": "sales123",
                "role": "sales",
                "is_active": True,
            },
            {
                "username": "viewer",
                "email": "viewer@example.com",
                "password": "viewer123",
                "role": "viewer",
                "is_active": True,
            },
        ]

        created_count = 0
        for user_data in test_users:
            existing = db.query(User).filter(User.username == user_data["username"]).first()
            if existing:
                logger.info("用户 {user_data['username']} 已存在，跳过", user_data['username'])
                continue

            user = User(
                id=str(uuid.uuid4()),
                username=user_data["username"],
                email=user_data["email"],
                hashed_password=get_password_hash(user_data["password"]),
                role=user_data["role"],
                is_active=user_data["is_active"],
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            db.add(user)
            created_count += 1
            logger.info("创建用户: {user_data['username']} (角色: {user_data['role']})", user_data['username'], user_data['role'])

        db.commit()
        logger.info('\\n成功创建 {created_count} 个测试用户', created_count)

        # 显示所有用户
        logger.info('\\n当前所有用户:')
        users = db.query(User).all()
        for u in users:
            logger.info("  - {u.username} (角色: {u.role}, 状态: {'激活' if u.is_active else '禁用'})", u.username, u.role, '激活' if u.is_active else '禁用')

    except Exception as e:
        logger.info('错误: {e}', e)
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    create_test_users()
