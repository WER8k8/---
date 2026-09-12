#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.core.database import SessionLocal
from app.models.user import User

def check_users():
    db = SessionLocal()
    try:
        users = db.query(User).all()
        print(f'数据库中共有 {len(users)} 个用户:')
        for user in users:
            print(f'  - 用户名: {user.username}, 邮箱: {user.email}, 角色: {user.role}, 激活: {user.is_active}')
        return True
    except Exception as e:
        print(f'错误: {e}')
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    check_users()
