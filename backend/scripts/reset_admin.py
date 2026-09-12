/**
import logging

logger = logging.getLogger(__name__)

 * FIX-B1: 重置 admin 密码脚本
 *
 * 安全变更：
 * - 移除硬编码密码 "admin123"，改为强制交互输入（getpass）
 * - 移除硬编码 SECRET_KEY，改为从 .env 加载或环境变量
 * - 密码强度校验：长度 >= 8
 */

import os
import sys

# 优先从 .env 加载配置，不硬编码
from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
if os.path.exists(env_path):
    load_dotenv(env_path)

os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")

# 如果 SECRET_KEY 未设置，给出明确错误而非使用弱密钥
if not os.environ.get("SECRET_KEY"):
    logger.info('ERROR: SECRET_KEY 未设置。请设置环境变量或在 .env 中配置。')
    logger.info('生成方式: python -c \\"import secrets; print(secrets.token_hex(32))\\"')
    sys.exit(1)

from app.core.database import get_db
from app.models.user import User
from app.core.security import get_password_hash


def _prompt_password() -> str:
    """强制交互输入密码，禁止硬编码。"""
    try:
        import getpass
        pwd = getpass.getpass("请输入新的 admin 密码（至少 8 位）: ")
        confirm = getpass.getpass("请再次输入确认: ")
    except Exception:
        # 非交互环境（如 CI）fallback 到 stdin
        import sys
        logger.info('"请输入新的 admin 密码（至少 8 位）: ", end="", flush=True')
        pwd = sys.stdin.readline().strip()
        logger.info('"请再次输入确认: ", end="", flush=True')
        confirm = sys.stdin.readline().strip()

    if pwd != confirm:
        logger.info('ERROR: 两次输入不一致')
        sys.exit(1)
    if len(pwd) < 8:
        logger.info('ERROR: 密码长度至少 8 位')
        sys.exit(1)
    return pwd


def main():
    db = next(get_db())
    admin = db.query(User).filter(User.username == "admin").first()

    if not admin:
        logger.info('Admin user not found!')
        sys.exit(1)

    new_password = _prompt_password()
    admin.hashed_password = get_password_hash(new_password)
    db.commit()
    logger.info('Admin password reset successfully.')


if __name__ == "__main__":
    main()
