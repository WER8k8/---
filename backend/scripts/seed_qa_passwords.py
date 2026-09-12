"""重置 QA 三壳账号密码（dev sqlite）— 截图/E2E 前执行"""

import os
import logging

logger = logging.getLogger(__name__)

import sys

sys.path.insert(0, os.path.dirname(__file__))

os.environ.setdefault("DATABASE_URL", "sqlite:///./youding_dev.db")

from app.core.security import get_password_hash
from app.db.session import SessionLocal, init_db
from app.models.user import User

QA = [("admin", "admin123"), ("editor", "editor123"), ("sales", "sales123")]


def main() -> None:
    init_db()
    db = SessionLocal()
    try:
        for username, password in QA:
            user = db.query(User).filter(User.username == username).first()
            if not user:
                logger.info('skip missing: {username}', username)
                continue
            user.hashed_password = get_password_hash(password)
            logger.info('reset {username}', username)
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    main()
