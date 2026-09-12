"""Headless 排名探针 — 外置 Sidecar（Playwright/Browser Use）或显式 dev stub。

未配置 Sidecar 时返回 skipped/503，禁止伪造排名。
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.content import SystemSetting
from app.services.geo.multi_engine_rank_registry import (
    all_traffic_engines,
    exploration_engines,
)

logger = logging.getLogger(__name__)

SNAPSHOT_KEY = "headless_rank_probe_snapshot"
_SETTING_KEY = "headless_rank_probe_latest"
_TIMEOUT = 60.0


def sidecar_base_url() -> str:
    """实现 sidecarbaseURL 的功能。
    
    :return: 返回 str 结果
    """
    return (os.getenv("HEADLESS_PROBE_SIDECAR_URL") or "").strip().rstrip("/")


def sidecar_token() -> str:
    """实现 sidecar令牌 的功能。
    
    :return: 返回 str 结果
    """
    return (os.getenv("HEADLESS_PROBE_SIDECAR_TOKEN") or "").strip()


def headless_probe_sidecar_status() -> dict[str, Any]:
    """实现 headless探测sidecar状态 的功能。
    
    :return: 返回 dict[str, Any] 结果
    """
    base = sidecar_base_url()
    out: dict[str, Any] = {
        "configured": bool(base),
        "url": base or None,
        "healthy": None,
        "exploration_engine_count": len(
            [e for e in all_traffic_engines() if e.probe_via == "headless_exploration"]
        ),
    }
    if not base:
        allow = _dev_stub_allowed()
        out["fallback"] = "dev_stub" if allow else "not_configured"
        out["dev_stub_allowed"] = allow
        return out
    headers = _auth_headers()
    for path in ("/health", "/api/health", "/v1/health"):
        try:
            with httpx.Client(timeout=5.0) as client:
                resp = client.get(f"{base}{path}", headers=headers)
            if resp.status_code < 300:
                out["healthy"] = True
                out["health_path"] = path
                return out
            out["detail"] = f"{path}: HTTP {resp.status_code}"
        except Exception as exc:
            out["detail"] = str(exc)[:200]
    out["healthy"] = False
    return out


def _auth_headers() -> dict[str, str]:
    """实现 认证headers 的功能。
    
    :return: 返回 dict[str, str] 结果
    """
    headers: dict[str, str] = {"Content-Type": "application/json"}
    token = sidecar_token()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _dev_stub_allowed() -> bool:
    """实现 devstuballowed 的功能。
    
    :return: 返回 bool 结果
    """
    env = (getattr(settings, "ENVIRONMENT", "") or "").lower()
    flag = (os.getenv("HEADLESS_PROBE_ALLOW_STUB") or "").strip().lower()
    return env == "development" or flag in ("1", "true", "yes")


def probe_single_engine(
    *,
    engine_id: str,
    keyword: str,
    target_url: str,
) -> dict[str, Any]:
    """单引擎探针；Sidecar 优先，dev stub 仅 development。"""
    base = sidecar_base_url()
    if base:
        return _probe_via_sidecar(engine_id=engine_id, keyword=keyword, target_url=target_url)
    if _dev_stub_allowed():
        return {
            "engine_id": engine_id,
            "keyword": keyword,
            "target_url": target_url,
            "probe_mode": "stub",
            "skipped": True,
            "found": None,
            "rank_hint": None,
            "note": "HEADLESS_PROBE_SIDECAR_URL 未配置；dev stub 不写入生产终态",
        }
    return {
        "engine_id": engine_id,
        "keyword": keyword,
        "target_url": target_url,
        "probe_mode": "unconfigured",
        "skipped": True,
        "error_code": "HEADLESS_PROBE_NOT_CONFIGURED",
        "note": "请配置 HEADLESS_PROBE_SIDECAR_URL（Playwright/Browser Use Worker）",
    }


def _probe_via_sidecar(*, engine_id: str, keyword: str, target_url: str) -> dict[str, Any]:
    """实现 探测viasidecar 的功能。
    
    :param engine_id: 参数 engine_id（类型: str）
    :param keyword: 参数 keyword（类型: str）
    :param target_url: 参数 target_url（类型: str）
    :return: 返回 dict[str, Any] 结果
    """
    base = sidecar_base_url()
    payload = {
        "engine_id": engine_id,
        "keyword": keyword,
        "target_url": target_url,
    }
    paths = ("/v1/headless-probe", "/api/headless-probe", "/headless-probe")
    headers = _auth_headers()
    for path in paths:
        try:
            with httpx.Client(timeout=_TIMEOUT) as client:
                resp = client.post(f"{base}{path}", json=payload, headers=headers)
            if resp.status_code >= 300:
                continue
            data = resp.json()
            if isinstance(data, dict) and "data" in data:
                data = data["data"]
            if not isinstance(data, dict):
                continue
            data.setdefault("probe_mode", "headless")
            data.setdefault("engine_id", engine_id)
            return data
        except Exception as exc:
            logger.warning("headless sidecar %s failed: %s", path, exc)
    return {
        "engine_id": engine_id,
        "keyword": keyword,
        "target_url": target_url,
        "probe_mode": "headless",
        "skipped": True,
        "error_code": "HEADLESS_PROBE_SIDECAR_ERROR",
        "note": "Sidecar 调用失败",
    }


def run_headless_probe_batch(
    db: Session,
    *,
    keyword: str,
    target_url: str,
    engine_ids: list[str] | None = None,
    limit: int = 5,
) -> dict[str, Any]:
    """对 headless_exploration 通道批量探针（限量，防超时）。"""
    engines = exploration_engines()
    headless = [e for e in engines if e.probe_via == "headless_exploration"]
    if engine_ids:
        wanted = set(engine_ids)
        headless = [e for e in headless if e.id in wanted]
    headless = headless[: max(1, min(limit, 8))]
    results: list[dict[str, Any]] = []
    for eng in headless:
        row = probe_single_engine(
            engine_id=eng.id,
            keyword=keyword,
            target_url=target_url,
        )
        row["display_name"] = eng.display_name
        results.append(row)

    body = {
        "saved_at": datetime.now(timezone.utc).isoformat(),
        "keyword": keyword,
        "target_url": target_url,
        "results": results,
        "configured": bool(sidecar_base_url()),
        "dev_stub": _dev_stub_allowed() and not sidecar_base_url(),
    }
    _save_snapshot(db, body)
    return body


def load_headless_probe_snapshot(db: Session | None = None) -> dict[str, Any] | None:
    """实现 加载headless探测snapshot 的功能。
    
    :param db: 参数 db（类型: Session | None）
    :return: 返回 dict[str, Any] | None 结果
    """
    if db is None:
        return None
    row = db.query(SystemSetting).filter(SystemSetting.setting_key == _SETTING_KEY).first()
    if not row or not row.setting_value:
        return None
    try:
        data = json.loads(row.setting_value)
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        return None


def _save_snapshot(db: Session, payload: dict[str, Any]) -> dict[str, Any]:
    """实现 保存snapshot 的功能。
    
    :param db: 参数 db（类型: Session）
    :param payload: 参数 payload（类型: dict[str, Any]）
    :return: 返回 dict[str, Any] 结果
    """
    serialized = json.dumps(payload, ensure_ascii=False)
    row = db.query(SystemSetting).filter(SystemSetting.setting_key == _SETTING_KEY).first()
    if not row:
        row = SystemSetting(
            setting_key=_SETTING_KEY,
            setting_value=serialized,
            setting_type="json",
            description="Headless 排名探针最近快照",
        )
        db.add(row)
    else:
        row.setting_value = serialized
    db.commit()
    return payload


def merge_snapshot_into_traffic_cards(
    cards: list[dict[str, Any]],
    snapshot: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    """将最近 headless 探针结果合并进增长工具 platform_cards。"""
    if not snapshot:
        return cards
    by_engine = {
        (r.get("engine_id") or ""): r
        for r in (snapshot.get("results") or [])
        if isinstance(r, dict)
    }
    out: list[dict[str, Any]] = []
    for card in cards:
        c = dict(card)
        eng_id = c.get("engine_id") or ""
        probe = by_engine.get(eng_id)
        if probe:
            c["headless_probe"] = {
                "probe_mode": probe.get("probe_mode"),
                "skipped": probe.get("skipped"),
                "found": probe.get("found"),
                "rank_hint": probe.get("rank_hint"),
                "evidence_snippet": (probe.get("evidence_snippet") or "")[:200],
                "saved_at": snapshot.get("saved_at"),
            }
            if probe.get("probe_mode") == "headless" and probe.get("found") is True:
                c["probe_status_label"] = "Headless 已探测"
            elif probe.get("probe_mode") == "stub":
                c["probe_status_label"] = "Dev Stub"
        out.append(c)
    return out
