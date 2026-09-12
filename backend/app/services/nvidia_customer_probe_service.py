"""英伟达客户侧可用模型探测（卖货副驾 / 旺财插件场景）。"""

from __future__ import annotations

import re
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import settings
from app.services.nvidia_customer_probe_store import load_probe_snapshot, save_probe_snapshot
from app.services.nvidia_scenario_health_service import probe_all_scenario_health

DEFAULT_PROBE_SLOTS = ((1, 0), (12, 0), (20, 0))


def parse_probe_slots(raw: str | None = None) -> list[tuple[int, int]]:
    """解析 '1:00,12:00,20:00' → [(1,0),(12,0),(20,0)]。"""
    text = (raw or getattr(settings, "NVIDIA_CUSTOMER_PROBE_SLOTS", "") or "1:00,12:00,20:00").strip()
    slots: list[tuple[int, int]] = []
    for part in text.split(","):
        piece = part.strip()
        if not piece:
            continue
        m = re.match(r"^(\d{1,2})\s*:\s*(\d{2})$", piece)
        if not m:
            continue
        hour, minute = int(m.group(1)), int(m.group(2))
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            slots.append((hour, minute))
    return slots or list(DEFAULT_PROBE_SLOTS)


def run_nvidia_customer_model_probe(
    db: Session,
    *,
    trigger: str = "manual",
) -> dict[str, Any]:
    """探测各产品场景绑定的英伟达模型，写入快照供客户侧展示。"""
    report = probe_all_scenario_health(db)
    scenarios = report.get("scenarios") or []
    available = [s for s in scenarios if s.get("healthy")]
    unavailable = [s for s in scenarios if not s.get("healthy")]
    body: dict[str, Any] = {
        **report,
        "trigger": trigger,
        "probe_slots": [f"{h:02d}:{m:02d}" for h, m in parse_probe_slots()],
        "probe_timezone": getattr(settings, "NVIDIA_CUSTOMER_PROBE_TZ", "Asia/Shanghai"),
        "available_scenarios": [
            {
                "id": s.get("scenario"),
                "label": s.get("label"),
                "model": s.get("model"),
                "latency_ms": s.get("latency_ms"),
            }
            for s in available
        ],
        "unavailable_scenarios": [
            {
                "id": s.get("scenario"),
                "label": s.get("label"),
                "model": s.get("model"),
                "error": (s.get("error") or "")[:200],
            }
            for s in unavailable
        ],
    }
    return save_probe_snapshot(db, body)


def build_probe_public_summary(db: Session) -> dict[str, Any]:
    """租户可见摘要（不含内部错误堆栈）。"""
    snap = load_probe_snapshot(db)
    if not snap:
        return {
            "last_probe_at": None,
            "available_count": 0,
            "total_count": 0,
            "available_scenarios": [],
            "probe_schedule": "每日 1:00、12:00、20:00（北京时间）",
        }
    return {
        "last_probe_at": snap.get("saved_at") or snap.get("checked_at"),
        "available_count": snap.get("healthy_count", 0),
        "total_count": snap.get("total", 0),
        "available_scenarios": snap.get("available_scenarios") or [],
        "probe_schedule": "每日 "
        + "、".join(snap.get("probe_slots") or ["1:00", "12:00", "20:00"])
        + f"（{snap.get('probe_timezone', 'Asia/Shanghai')}）",
    }
