import sys
import os
import re
import argparse
sys.path.insert(0, os.path.dirname(__file__))

from app.core.database import SessionLocal
from app.models.user import User
from passlib.context import CryptContext
from dotenv import load_dotenv

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def validate_password_strength(password: str) -> tuple[bool, list[str]]:
    """
    验证密码强度
    返回 (是否符合要求, 错误信息列表)
    """
    errors = []
    
    # 至少8个字符
    if len(password) < 8:
        errors.append("密码长度至少为8个字符")
    
    # 包含大写字母
    if not re.search(r'[A-Z]', password):
        errors.append("密码需包含至少一个大写字母")
    
    # 包含小写字母
    if not re.search(r'[a-z]', password):
        errors.append("密码需包含至少一个小写字母")
    
    # 包含数字
    if not re.search(r'\d', password):
        errors.append("密码需包含至少一个数字")
    
    # 包含特殊字符
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append("密码需包含至少一个特殊字符(!@#$%^&*(),.?\":{}|<>)")
    
    return len(errors) == 0, errors


def update_admin_password():
    # 加载环境变量
    load_dotenv()
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="更新 admin 用户密码")
    parser.add_argument("--password", help="新密码（如果未提供，将从环境变量 ADMIN_PASSWORD 读取）")
    parser.add_argument("--interactive", action="store_true", help="交互式输入密码")
    
    args = parser.parse_args()
    
    # 获取密码
    new_password = None
    
    # 优先级: 命令行参数 > 交互式输入 > 环境变量
    if args.password:
        new_password = args.password
    elif args.interactive:
        import getpass
        new_password = getpass.getpass("请输入新密码: ")
    else:
        new_password = os.getenv("ADMIN_PASSWORD")
    
    if not new_password:
        print("错误: 未提供密码。请使用 --password 参数、--interactive 参数或设置 ADMIN_PASSWORD 环境变量")
        return False
    
    # 验证密码强度
    is_valid, errors = validate_password_strength(new_password)
    if not is_valid:
        print("密码强度不符合要求:")
        for error in errors:
            print(f"  - {error}")
        return False
    
    # 更新密码
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            print("错误: 未找到admin用户")
            return False
        
        admin.hashed_password = pwd_context.hash(new_password)
        db.commit()
        
        print("成功更新admin用户密码")
        return True
    except Exception as e:
        db.rollback()
        print(f"错误: {e}")
        return False
    finally:
        db.close()


if __name__ == "__main__":
    success = update_admin_password()
    sys.exit(0 if success else 1)
