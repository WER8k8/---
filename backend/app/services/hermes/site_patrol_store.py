# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Hermes 巡站快照持久化（仅单键 SystemSetting）。"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.content import SystemSetting
from app.services.hermes.maintenance_constitution import assert_maintenance_action

SNAPSHOT_KEY = "hermes_site_patrol_snapshot"
TREND_KEY = "hermes_site_patrol_trend_7d"
TREND_MAX = 7


def _now_iso() -> str:
    """_now_iso。
    :return: 返回处理结果。
    """
    return datetime.now(timezone.utc).isoformat()


def load_patrol_snapshot(db: Session) -> dict[str, Any] | None:
    """load_patrol_snapshot。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    assert_maintenance_action("read_probe")
    row = db.query(SystemSetting).filter(SystemSetting.setting_key == SNAPSHOT_KEY).first()
    if not row or not row.setting_value:
        return None
    try:
        data = json.loads(row.setting_value)
        return data if isinstance(data, dict) else None
    except (json.JSONDecodeError, TypeError):
        return None


def save_patrol_snapshot(db: Session, payload: dict[str, Any]) -> dict[str, Any]:
    """save_patrol_snapshot。

    参数说明：
    :param db: 参数 db
    :param payload: 参数 payload
    :return: 返回处理结果。
    """
    assert_maintenance_action("write_patrol_snapshot")
    body = {**payload, "saved_at": _now_iso()}
    serialized = json.dumps(body, ensure_ascii=False)
    row = db.query(SystemSetting).filter(SystemSetting.setting_key == SNAPSHOT_KEY).first()
    if row is None:
        row = SystemSetting(
            id=str(uuid.uuid4()),
            setting_key=SNAPSHOT_KEY,
            setting_value=serialized,
            setting_type="json",
            description="Hermes 7×24 巡站维护快照（只读探测）",
        )
        db.add(row)
    else:
        row.setting_value = serialized
        row.setting_type = "json"
    db.commit()
    append_patrol_trend(db, body)
    return body


def append_patrol_trend(db: Session, snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    """保留最近 7 次巡站 pass/warn/fail 计数（HERM-10）。"""
    assert_maintenance_action("write_patrol_snapshot")
    probes = snapshot.get("probes") or []
    counts = {"pass": 0, "warn": 0, "fail": 0}
    for p in probes:
        st = p.get("status") or "warn"
        if st in counts:
            counts[st] += 1
    entry = {
        "at": snapshot.get("saved_at") or _now_iso(),
        "overall": snapshot.get("overall_status"),
        **counts,
    }
    row = db.query(SystemSetting).filter(SystemSetting.setting_key == TREND_KEY).first()
    trend: list[dict[str, Any]] = []
    if row and row.setting_value:
        try:
            trend = json.loads(row.setting_value)
            if not isinstance(trend, list):
                trend = []
        except json.JSONDecodeError:
            trend = []
    trend.append(entry)
    trend = trend[-TREND_MAX:]
    serialized = json.dumps(trend, ensure_ascii=False)
    if row is None:
        db.add(
            SystemSetting(
                id=str(uuid.uuid4()),
                setting_key=TREND_KEY,
                setting_value=serialized,
                setting_type="json",
                description="Hermes 巡站 7 日趋势",
            )
        )
    else:
        row.setting_value = serialized
    db.commit()
    return trend


def load_patrol_trend(db: Session) -> list[dict[str, Any]]:
    """load_patrol_trend。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    assert_maintenance_action("read_probe")
    row = db.query(SystemSetting).filter(SystemSetting.setting_key == TREND_KEY).first()
    if not row or not row.setting_value:
        return []
    try:
        data = json.loads(row.setting_value)
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []
