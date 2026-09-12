#!/usr/bin/env python3
"""
简单密码修复脚本
直接将管理员密码设置为123456，跳过所有验证
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.core.database import SessionLocal
from app.models import User
from passlib.context import CryptContext

def fix_password():
    db = SessionLocal()
    try:
        print("正在查找管理员用户...")
        
        # 查找管理员用户
        admin_user = db.query(User).filter(User.username == 'admin').first()
        
        if not admin_user:
            print("未找到管理员用户 'admin'")
            print("正在创建管理员用户...")
            
            from datetime import datetime, timezone
            import uuid
            
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            
            admin = User(
                id=str(uuid.uuid4()),
                username='admin',
                email='admin@youding.com',
                hashed_password=pwd_context.hash('123456'),
                display_name='管理员',
                role='admin',
                is_active=True,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            db.add(admin)
            db.commit()
            print("✓ 管理员用户创建成功！")
        else:
            print("找到管理员用户，正在更新密码...")
            
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            admin_user.hashed_password = pwd_context.hash('123456')
            db.commit()
            print("✓ 密码更新成功！")
        
        print("\n========================================")
        print("超级管理员登录信息：")
        print("  用户名: admin")
        print("  密码: 123456")
        print("========================================")
        print("\n现在可以使用这个简单密码登录了！")
        
        return True
        
    except Exception as e:
        db.rollback()
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    fix_password()
