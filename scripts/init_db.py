#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# 设置环境变量（用于开发环境）
os.environ.setdefault("SECRET_KEY", "dev-secret-key-for-init-db-only-12345678901234567890")
os.environ.setdefault("ENVIRONMENT", "development")

from app.core.database import Base, engine
from app.core.database import SessionLocal
from app.models.user import User
from datetime import datetime, timezone
from passlib.context import CryptContext
import uuid

def init_db():
    print('正在创建数据库表...')
    Base.metadata.create_all(bind=engine)
    print('数据库表创建完成!')
    
    # 检查是否已有管理员用户
    db = SessionLocal()
    try:
        existing_admin = db.query(User).filter(User.username == 'admin').first()
        if existing_admin:
            print('管理员用户已存在，跳过创建。')
            return
        
        # 创建管理员用户
        print('正在创建管理员用户...')
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        admin_password = os.getenv("SEED_ADMIN_PASSWORD", "123456")
        admin = User(
            id=str(uuid.uuid4()),
            username="admin",
            email="admin@youding.com",
            hashed_password=pwd_context.hash(admin_password),
            display_name="管理员",
            role="admin",
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(admin)
        db.commit()
        print(f'管理员用户创建成功!')
        print(f'  用户名: admin')
        print(f'  密码: {admin_password}')
        print(f'现在可以使用这个账户登录了!')
    except Exception as e:
        db.rollback()
        print(f'错误: {e}')
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
