"""物流轨迹第三方适配（快递100 / 沙箱）。"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from app.core.config import settings

_KUAIDI100_POLL_URL = "https://poll.kuaidi100.com/poll/maptrack.do"

# 常见承运商编码（快递100 com 参数）
_CARRIER_ALIASES: dict[str, str] = {
    "auto": "auto",
    "sf": "shunfeng",
    "shunfeng": "shunfeng",
    "yt": "yuantong",
    "yuantong": "yuantong",
    "zt": "zhongtong",
    "zhongtong": "zhongtong",
    "yd": "yunda",
    "yunda": "yunda",
    "sto": "shentong",
    "shentong": "shentong",
}


def _demo_payload(tracking_number: str, carrier: str | None) -> dict[str, Any]:
    """_demo_payload。

    参数说明：
    :param tracking_number: 参数 tracking_number
    :param carrier: 参数 carrier
    :return: 返回处理结果。
    """
    now = datetime.now(timezone.utc)
    return {
        "tracking_number": tracking_number.strip(),
        "carrier": carrier or "auto",
        "status": "in_transit",
        "origin": "发货仓",
        "destination": "收货城市",
        "estimated_delivery": (now + timedelta(days=2)).isoformat(),
        "last_update": now.isoformat(),
        "events": [
            {
                "description": "快件已揽收",
                "timestamp": (now - timedelta(days=1)).isoformat(),
                "location": "始发网点",
            },
            {
                "description": "运输中",
                "timestamp": now.isoformat(),
                "location": "中转中心",
            },
        ],
        "demo": True,
        "provider": "demo",
    }


def _map_kuaidi_status(state: str | None) -> str:
    """快递100 state → 统一状态。"""
    if not state:
        return "in_transit"
    if state in ("3", "301", "302", "303", "304"):
        return "delivered"
    if state in ("0", "1001", "1002", "1003"):
        return "picked_up"
    if state in ("4", "401", "14"):
        return "exception"
    return "in_transit"


def fetch_via_kuaidi100(tracking_number: str, carrier: str | None) -> dict[str, Any]:
    """fetch_via_kuaidi100。

    参数说明：
    :param tracking_number: 参数 tracking_number
    :param carrier: 参数 carrier
    :return: 返回处理结果。
    """
    customer = getattr(settings, "KUAIDI100_CUSTOMER", None) or os.getenv("KUAIDI100_CUSTOMER", "")
    key = getattr(settings, "KUAIDI100_API_KEY", None) or os.getenv("KUAIDI100_API_KEY", "")
    if not customer or not key:
        raise ValueError("kuaidi100_not_configured")

    com = _CARRIER_ALIASES.get((carrier or "auto").lower(), carrier or "auto")
    param = json.dumps({"com": com, "num": tracking_number.strip()}, ensure_ascii=False)
    sign = hashlib.md5(f"{param}{key}{customer}".encode()).hexdigest().upper()
    data = {"customer": customer, "sign": sign, "param": param}
    with httpx.Client(timeout=15.0) as client:
        resp = client.post(_KUAIDI100_POLL_URL, data=data)
        resp.raise_for_status()
        body = resp.json()

    if body.get("status") != "200" and body.get("returnCode") not in ("200", "408"):
        raise ValueError(body.get("message") or "kuaidi100_error")

    result = body.get("data") or []
    events = []
    for item in result:
        events.append(
            {
                "description": item.get("context") or item.get("status"),
                "timestamp": item.get("time") or item.get("ftime"),
                "location": item.get("location") or item.get("areaName"),
            }
        )
    last_state = result[-1].get("status") if result else None
    status = _map_kuaidi_status(str(last_state) if last_state is not None else None)
    now = datetime.now(timezone.utc).isoformat()
    return {
        "tracking_number": tracking_number.strip(),
        "carrier": com,
        "status": status,
        "origin": result[0].get("location") if result else None,
        "destination": result[-1].get("location") if result else None,
        "estimated_delivery": None,
        "last_update": now,
        "events": events or [{"description": "暂无轨迹", "timestamp": now}],
        "demo": False,
        "provider": "kuaidi100",
    }


def fetch_tracking(tracking_number: str, carrier: str | None = None) -> dict[str, Any]:
    """统一物流查询入口。"""
    provider = (
        getattr(settings, "LOGISTICS_PROVIDER", None)
        or os.getenv("LOGISTICS_PROVIDER", "demo")
    ).lower()
    number = tracking_number.strip()
    if not number:
        raise ValueError("运单号不能为空")

    if provider == "kuaidi100":
        try:
            return fetch_via_kuaidi100(number, carrier)
        except Exception:
            # 生产可改为直接抛出；开发/演示降级沙箱
            if os.getenv("LOGISTICS_FALLBACK_DEMO", "true").lower() in ("1", "true", "yes"):
                payload = _demo_payload(number, carrier)
                payload["provider"] = "demo_fallback"
                payload["warning"] = "kuaidi100_unavailable"
                return payload
            raise

    return _demo_payload(number, carrier)
