"""SEO 矩阵 admin_users 只读校验：MySQL（生产）与 SQLite（本地）双模式，供统一登录使用。"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Optional, Tuple
from urllib.parse import quote_plus

from sqlalchemy import create_engine, text

from app.core.security import verify_password


def _mysql_engine_url(settings: Any) -> Optional[str]:
    """_mysql_engine_url。

    参数说明：
    :param settings: 参数 settings
    :return: 返回处理结果。
    """
    raw = (getattr(settings, "SEO_MATRIX_DATABASE_URL", None) or "").strip()
    if raw:
        return raw
    host = (getattr(settings, "SEO_MATRIX_DB_HOST", None) or "").strip()
    name = (getattr(settings, "SEO_MATRIX_DB_NAME", None) or "").strip()
    user = getattr(settings, "SEO_MATRIX_DB_USER", None)
    if not host or not name or user is None or str(user).strip() == "":
        return None
    port = int(getattr(settings, "SEO_MATRIX_DB_PORT", None) or 3306)
    pw = quote_plus(str(getattr(settings, "SEO_MATRIX_DB_PASSWORD", "") or ""))
    uq = quote_plus(str(user).strip())
    return f"mysql+pymysql://{uq}:{pw}@{host}:{port}/{name}?charset=utf8mb4"


def matrix_credentials_source_configured(settings: Any) -> bool:
    """是否已配置矩阵库（MySQL 或 SQLite 文件）。"""
    if _mysql_engine_url(settings):
        return True
    p = (getattr(settings, "SEO_MATRIX_SQLITE_PATH", None) or "").strip()
    return bool(p and Path(p).is_file())


def verify_matrix_admin_credentials_sqlite(
        sqlite_path: str, username: str, password: str) -> Optional[Tuple[int, str]]:
    """verify_matrix_admin_credentials_sqlite。

    参数说明：
    :param sqlite_path: 参数 sqlite_path
    :param username: 参数 username
    :param password: 参数 password
    :return: 返回处理结果。
    """
    path = Path(sqlite_path)
    if not path.is_file():
        return None
    conn = sqlite3.connect(str(path.resolve()), check_same_thread=False)
    try:
        try:
            cur = conn.execute(
                """
                SELECT id, username, password_hash, status
                FROM admin_users
                WHERE lower(username) = lower(?)
                LIMIT 1
                """,
                (username.strip(),),
            )
            row = cur.fetchone()
        except sqlite3.OperationalError:
            return None
        if not row:
            return None
        return _row_to_result(row[0], row[1], row[2], row[3], password)
    finally:
        conn.close()


def _row_to_result(admin_id, uname, pwd_hash, status,
                   password: str) -> Optional[Tuple[int, str]]:
    """_row_to_result。

    参数说明：
    :param admin_id: 参数 admin_id
    :param uname: 参数 uname
    :param pwd_hash: 参数 pwd_hash
    :param status: 参数 status
    :param password: 参数 password
    :return: 返回处理结果。
    """
    try:
        st = int(status)
    except (TypeError, ValueError):
        st = status
    if st not in (1, "1", True):
        return None
    if not pwd_hash or not verify_password(password, str(pwd_hash)):
        return None
    return (int(admin_id), str(uname))


def _verify_matrix_mysql(url: str, username: str,
                         password: str) -> Optional[Tuple[int, str]]:
    """_verify_matrix_mysql。

    参数说明：
    :param url: 参数 url
    :param username: 参数 username
    :param password: 参数 password
    :return: 返回处理结果。
    """
    engine = create_engine(url, pool_pre_ping=True, pool_recycle=3600)
    try:
        with engine.connect() as conn:
            row = (
                conn.execute(
                    text(
                        "SELECT id, username, password_hash, status "
                        "FROM admin_users WHERE LOWER(username) = LOWER(:u) LIMIT 1"), {
                        "u": username.strip()}, ) .mappings() .first())
        if not row:
            return None
        return _row_to_result(
            row["id"],
            row["username"],
            row["password_hash"],
            row["status"],
            password)
    finally:
        engine.dispose()


def verify_matrix_admin(settings: Any, username: str,
                        password: str) -> Optional[Tuple[int, str]]:
    """
    优先 MySQL（SEO_MATRIX_DATABASE_URL 或 SEO_MATRIX_DB_*），否则 SQLite 文件。
    与 Node 矩阵库表结构一致：admin_users。
    """
    raw_user = (username or "").strip()
    if not raw_user or not password:
        return None

    mysql_url = _mysql_engine_url(settings)
    if mysql_url:
        return _verify_matrix_mysql(mysql_url, raw_user, password)

    sqlite_path = (
        getattr(
            settings,
            "SEO_MATRIX_SQLITE_PATH",
            None) or "").strip()
    if sqlite_path:
        return verify_matrix_admin_credentials_sqlite(
            sqlite_path, raw_user, password)
    return None


# 兼容旧调用名（仅 SQLite）
def verify_matrix_admin_credentials(
    sqlite_path: Optional[str], username: str, password: str
) -> Optional[Tuple[int, str]]:
    """verify_matrix_admin_credentials。

    参数说明：
    :param sqlite_path: 参数 sqlite_path
    :param username: 参数 username
    :param password: 参数 password
    :return: 返回处理结果。
    """
    if not sqlite_path:
        return None
    return verify_matrix_admin_credentials_sqlite(
        sqlite_path, username, password)
