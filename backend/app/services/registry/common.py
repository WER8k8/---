"""注册表公共工具：JSON 安全解析、状态校验、唯一性帮助。"""

from __future__ import annotations

import json
import re
from typing import Any

from sqlalchemy.orm import Session

_ID_PATTERN = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9\-_.]{0,119}$")


def parse_json(value: str | None, default: Any = None) -> Any:
    """JSON 文本安全解析；非法或空返回 default。"""
    if not value:
        return default
    try:
        return json.loads(value)
    except (ValueError, TypeError):
        return default


def into_json(value: Any) -> str | None:
    """对象 → JSON 文本；None 返回 None。"""
    if value is None:
        return None
    return json.dumps(value, ensure_ascii=False)


def valid_name(name: str) -> bool:
    """注册名合法性：非空、≤120 字符、仅字母数字下划线连字符点。"""
    if not name or not name.strip():
        return False
    return bool(_ID_PATTERN.match(name.strip()))


def ensure_in(value: Any, allowed: set[str] | tuple[str, ...], field: str) -> None:
    """枚举校验，非法抛出 ValueError。"""
    if value not in allowed:
        raise ValueError(f"{field} 取值非法: {value!r}（允许: {sorted(allowed)}）")


def commit_or_rollback(db: Session) -> None:
    """提交会话；失败回滚并重抛。"""
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise