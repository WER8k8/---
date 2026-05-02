import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.core.database import SessionLocal
from app.models.user import User
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def update_admin_password():
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            print("错误: 未找到admin用户")
            return False
        
        new_password = "Admin@123456"
        admin.hashed_password = pwd_context.hash(new_password)
        db.commit()
        
        print(f"成功更新admin用户密码为: {new_password}")
        return True
    except Exception as e:
        db.rollback()
        print(f"错误: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    update_admin_password()
