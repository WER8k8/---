# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""超管轻量 CRUD 公共存储：SystemConfig JSON 数组 + OperationLog 写痕。"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.system_config import SystemConfig
from app.models.user import OperationLog, User


def new_id() -> str:
    """new_id。"""
    return str(uuid.uuid4())


def now_iso() -> str:
    """now_iso。"""
    return datetime.now(timezone.utc).isoformat()


def load_items(db: Session, key: str) -> list[dict[str, Any]]:
    """load_items。"""
    row = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    if not row or not row.value:
        return []
    try:
        data = json.loads(row.value)
    except json.JSONDecodeError:
        return []
    return data if isinstance(data, list) else []


def save_items(
    db: Session,
    key: str,
    items: list[dict[str, Any]],
    description: str,
) -> None:
    """save_items。"""
    payload = json.dumps(items, ensure_ascii=False)
    row = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    if row:
        row.value = payload
        row.value_type = "json"
        row.updated_at = datetime.now(timezone.utc)
    else:
        db.add(
            SystemConfig(
                id=new_id(),
                key=key,
                value=payload,
                value_type="json",
                description=description,
                is_public=False,
            )
        )
    db.commit()


def log_admin_write(
    db: Session,
    *,
    admin: Optional[User],
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    detail: Optional[dict[str, Any]] = None,
) -> None:
    """写操作审计；失败不回滚业务。"""
    try:
        row = OperationLog(
            id=new_id(),
            user_id=str(admin.id) if admin else None,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            detail=json.dumps(detail or {}, ensure_ascii=False)[:4000],
            created_at=datetime.now(timezone.utc),
        )
        db.add(row)
        db.commit()
    except Exception:
        db.rollback()
