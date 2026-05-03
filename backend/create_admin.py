import sys
import os
import getpass
sys.path.insert(0, os.path.dirname(__file__))

from passlib.context import CryptContext
from app.core.database import SessionLocal
from app.models.user import User
from datetime import datetime, timezone

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
db = SessionLocal()

def get_admin_password():
    password = os.getenv('ADMIN_PASSWORD')
    if password:
        return password
    try:
        password = getpass.getpass('请输入管理员密码: ')
        confirm = getpass.getpass('请确认密码: ')
        if password != confirm:
            print('错误: 两次输入的密码不一致')
            sys.exit(1)
        if len(password) < 8:
            print('错误: 密码长度至少8位')
            sys.exit(1)
        return password
    except (EOFError, KeyboardInterrupt):
        print('\n错误: 未提供密码')
        sys.exit(1)

try:
    admin_password = get_admin_password()
    existing = db.query(User).filter(User.username == 'admin').first()
    if existing:
        print('Admin用户已存在，更新密码...')
        existing.hashed_password = pwd_context.hash(admin_password)
        existing.role = 'admin'
        existing.is_active = True
        db.commit()
        print('密码已更新')
    else:
        admin = User(
            username='admin',
            email='admin@youding.com',
            hashed_password=pwd_context.hash(admin_password),
            display_name='管理员',
            role='admin',
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(admin)
        db.commit()
        print('Admin用户创建成功!')
        print('用户名: admin')
except Exception as e:
    db.rollback()
    print(f'错误: {e}')
finally:
    db.close()
