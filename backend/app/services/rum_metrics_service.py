"""浏览器 RUM 采集与 Rank Guard 快照联动。"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.core.cache import redis_client
from app.core.config import settings
from app.models.content import SystemSetting

SNAPSHOT_KEY = "rum:metrics:latest"
SETTING_KEY = "rum_metrics_latest"
SNAPSHOT_TTL = 86400 * 3


def ingest_rum_sample(
    db: Session,
    *,
    lcp_ms: float | None = None,
    inp_ms: float | None = None,
    cls: float | None = None,
    error_rate: float | None = None,
    page_path: str | None = None,
    tenant_id: str | None = None,
) -> dict[str, Any]:
    """接收前端 RUM 信标；滚动平均写入快照。"""
    prev = load_rum_snapshot(db) or {}
    n = int(prev.get("sample_count") or 0) + 1
    def _blend(key: str, new_val: float | None, old_val: float | None) -> float | None:
        """_blend。

        参数说明：
        :param key: 参数 key
        :param new_val: 参数 new_val
        :param old_val: 参数 old_val
        :return: 返回处理结果。
        """
        if new_val is None:
            return old_val
        if old_val is None:
            return float(new_val)
        return round((old_val * (n - 1) + float(new_val)) / n, 3)

    body: dict[str, Any] = {
        "lcp_ms": int(_blend("lcp_ms", lcp_ms, prev.get("lcp_ms")) or 0),
        "inp_ms": int(_blend("inp_ms", inp_ms, prev.get("inp_ms")) or 0),
        "cls": _blend("cls", cls, prev.get("cls")),
        "error_rate": _blend("error_rate", error_rate, prev.get("error_rate")),
        "sample_count": n,
        "last_page_path": page_path or prev.get("last_page_path"),
        "tenant_id": tenant_id or prev.get("tenant_id"),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    save_rum_snapshot(db, body)
    return body


def save_rum_snapshot(db: Session, payload: dict[str, Any]) -> dict[str, Any]:
    """save_rum_snapshot。

    参数说明：
    :param db: 参数 db
    :param payload: 参数 payload
    :return: 返回处理结果。
    """
    serialized = json.dumps(payload, ensure_ascii=False)
    if redis_client:
        redis_client.set(SNAPSHOT_KEY, serialized, ex=SNAPSHOT_TTL)
    row = db.query(SystemSetting).filter(SystemSetting.setting_key == SETTING_KEY).first()
    if row is None:
        row = SystemSetting(
            id=str(uuid.uuid4()),
            setting_key=SETTING_KEY,
            setting_value=serialized,
            setting_type="json",
            description="浏览器 RUM 滚动快照",
        )
        db.add(row)
    else:
        row.setting_value = serialized
    db.commit()
    return payload


def load_rum_snapshot(db: Session | None = None) -> dict[str, Any] | None:
    """load_rum_snapshot。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    from app.core.cache import redis_available
    if redis_available():
        try:
            raw = redis_client.get(SNAPSHOT_KEY)
        except Exception:
            raw = None
        if raw:
            try:
                data = json.loads(raw)
                return data if isinstance(data, dict) else None
            except json.JSONDecodeError:
                pass
    if db is None:
        return None
    row = db.query(SystemSetting).filter(SystemSetting.setting_key == SETTING_KEY).first()
    if not row or not row.setting_value:
        return None
    try:
        data = json.loads(row.setting_value)
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        return None


def rum_for_rank_guard(db: Session | None = None) -> dict[str, Any]:
    """Rank Guard 优先用真实 RUM，否则 env 默认。"""
    snap = load_rum_snapshot(db)
    if snap and int(snap.get("sample_count") or 0) >= 3:
        return {
            "lcp_ms": int(snap.get("lcp_ms") or getattr(settings, "RUM_LCP_MS", None) or 2000),
            "inp_ms": int(snap.get("inp_ms") or getattr(settings, "RUM_INP_MS", None) or 150),
            "error_rate": float(
                snap.get("error_rate")
                if snap.get("error_rate") is not None
                else getattr(settings, "RUM_ERROR_RATE", None) or 0.005
            ),
            "source": "rum_beacon",
            "sample_count": snap.get("sample_count"),
        }
    return {
        "lcp_ms": int(getattr(settings, "RUM_LCP_MS", None) or 2000),
        "inp_ms": int(getattr(settings, "RUM_INP_MS", None) or 150),
        "error_rate": float(getattr(settings, "RUM_ERROR_RATE", None) or 0.005),
        "source": "env_default",
        "sample_count": 0,
    }
