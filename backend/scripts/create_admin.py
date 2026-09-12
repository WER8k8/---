from app.models.user import User
import logging

logger = logging.getLogger(__name__)

from app.core.database import SessionLocal
from app.db.session import init_db
from passlib.context import CryptContext
from datetime import datetime, timezone
import getpass
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_admin_password():
    password = os.getenv("ADMIN_PASSWORD")
    if password:
        return password
    try:
        password = getpass.getpass("请输入管理员密码: ")
        confirm = getpass.getpass("请确认密码: ")
        if password != confirm:
            logger.info('错误: 两次输入的密码不一致')
            sys.exit(1)
        return password
    except (EOFError, KeyboardInterrupt):
        logger.info('\\n错误: 未提供密码')
        sys.exit(1)


def create_super_admin():
    init_db()
    db = SessionLocal()
    try:
        from app.db.seed import seed_super_admin
        logger.info('初始化种子数据...')
        seed_super_admin(db)
        db.commit()

        admin_password = get_admin_password()
        role = os.getenv("ADMIN_ROLE", "super_admin")
        username = os.getenv("ADMIN_USERNAME", "admin")

        existing = db.query(User).filter(User.username == username).first()
        if existing:
            logger.info('用户 {username} 已存在，更新密码和角色...', username)
            existing.hashed_password = pwd_context.hash(admin_password)
            existing.role = role
            existing.is_active = True
            db.commit()
            logger.info('密码已更新，角色已设置为 {role}', role)
        else:
            admin = User(
                username=username,
                email=os.getenv("ADMIN_EMAIL", f"{username}@youding.com"),
                hashed_password=pwd_context.hash(admin_password),
                display_name=os.getenv("ADMIN_DISPLAY_NAME", "超级管理员"),
                role=role,
                is_active=True,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            db.add(admin)
            db.commit()
            logger.info('{role} 用户创建成功!', role)
            logger.info('用户名: {username}', username)

        # 同时确保有 admin 角色的默认账号
        if role != "admin" and not db.query(User).filter(User.username == "admin").first():
            default_admin = User(
                username="admin",
                email="admin@youding.com",
                hashed_password=pwd_context.hash(admin_password),
                display_name="管理员",
                role="admin",
                is_active=True,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            db.add(default_admin)
            db.commit()
            logger.info('默认管理员账号 (admin) 也已创建')

    except Exception as e:
        db.rollback()
        logger.info('错误: {e}', e)
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    create_super_admin()
