#!/usr/bin/env python3
"""
更新管理员密码脚本
将管理员密码设置为简单的 123456
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.core.database import SessionLocal
from app.models import User
from passlib.context import CryptContext

def update_admin_password():
    db = SessionLocal()
    try:
        # 查找管理员用户
        admin_user = db.query(User).filter(User.username == 'admin').first()
        
        if not admin_user:
            print("未找到管理员用户 'admin'")
            return False
        
        # 使用简单的密码
        new_password = '123456'
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        # 更新密码
        admin_user.hashed_password = pwd_context.hash(new_password)
        db.commit()
        
        print(f"✓ 管理员密码已成功更新！")
        print(f"  用户名: admin")
        print(f"  新密码: {new_password}")
        print(f"\n现在可以使用简单的密码登录了！")
        
        return True
        
    except Exception as e:
        db.rollback()
        print(f"错误: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    update_admin_password()
