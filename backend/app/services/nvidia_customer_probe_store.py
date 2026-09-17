# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""英伟达客户可用模型探测快照（system_settings）。"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.content import SystemSetting

SNAPSHOT_KEY = "nvidia_customer_model_probe_snapshot"


def _now_iso() -> str:
    """_now_iso。
    :return: 返回处理结果。
    """
    return datetime.now(timezone.utc).isoformat()


def load_probe_snapshot(db: Session) -> dict[str, Any] | None:
    """load_probe_snapshot。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    row = db.query(SystemSetting).filter(SystemSetting.setting_key == SNAPSHOT_KEY).first()
    if not row or not row.setting_value:
        return None
    try:
        data = json.loads(row.setting_value)
        return data if isinstance(data, dict) else None
    except (json.JSONDecodeError, TypeError):
        return None


def save_probe_snapshot(db: Session, payload: dict[str, Any]) -> dict[str, Any]:
    """save_probe_snapshot。

    参数说明：
    :param db: 参数 db
    :param payload: 参数 payload
    :return: 返回处理结果。
    """
    body = {**payload, "saved_at": _now_iso()}
    serialized = json.dumps(body, ensure_ascii=False)
    row = db.query(SystemSetting).filter(SystemSetting.setting_key == SNAPSHOT_KEY).first()
    if row is None:
        row = SystemSetting(
            id=str(uuid.uuid4()),
            setting_key=SNAPSHOT_KEY,
            setting_value=serialized,
            setting_type="json",
            description="英伟达客户可用模型定时探测快照（1:00/12:00/20:00）",
        )
        db.add(row)
    else:
        row.setting_value = serialized
        row.setting_type = "json"
    db.commit()
    return body
