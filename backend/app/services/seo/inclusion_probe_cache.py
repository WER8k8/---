# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""收录探测 probe_mode 侧车缓存（无 schema 迁移）。"""

from __future__ import annotations

import json
import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models.content import SystemSetting

CACHE_KEY = "inclusion_last_probe_modes"
_MAX = 500


def _load_map(db: Session) -> dict[str, str]:
    """实现 加载映射 的功能。
    
    :param db: 参数 db（类型: Session）
    :return: 返回 dict[str, str] 结果
    """
    row = db.query(SystemSetting).filter(SystemSetting.setting_key == CACHE_KEY).first()
    if not row or not row.setting_value:
        return {}
    try:
        data = json.loads(row.setting_value)
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}


def set_probe_mode(db: Session, task_id: str, probe_mode: str) -> None:
    """实现 设置探测模式 的功能。
    
    :param db: 参数 db（类型: Session）
    :param task_id: 参数 task_id（类型: str）
    :param probe_mode: 参数 probe_mode（类型: str）
    :return: 返回 None 结果
    """
    m = _load_map(db)
    m[str(task_id)] = probe_mode
    if len(m) > _MAX:
        keys = list(m.keys())[-_MAX:]
        m = {k: m[k] for k in keys}
    serialized = json.dumps(m, ensure_ascii=False)
    row = db.query(SystemSetting).filter(SystemSetting.setting_key == CACHE_KEY).first()
    if row is None:
        db.add(
            SystemSetting(
                id=str(uuid.uuid4()),
                setting_key=CACHE_KEY,
                setting_value=serialized,
                setting_type="json",
                description="收录复检 probe_mode 缓存",
            )
        )
    else:
        row.setting_value = serialized
    db.commit()


def get_probe_mode(db: Session, task_id: str) -> str | None:
    """实现 获取探测模式 的功能。
    
    :param db: 参数 db（类型: Session）
    :param task_id: 参数 task_id（类型: str）
    :return: 返回 str | None 结果
    """
    return _load_map(db).get(str(task_id))
