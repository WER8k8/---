# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""禁止假交付 — 出站响应扫描（生产路径硬拒绝）。"""

from __future__ import annotations

import json
import re
from typing import Any

from app.core.no_fake_delivery import FakeDeliveryViolation, is_production_environment

_MAX_DEPTH = 12
_MAX_NODES = 4000

# 响应 message 含下列文案却未标 mode=mock → 生产阻断
_FAKE_MESSAGE_HINTS = re.compile(
    r"模拟数据|演示数据|以下为演示|暂时返回模拟|模拟模式",
    re.I,
)

_SKIP_PATH_PREFIXES: tuple[str, ...] = (
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/static/",
    "/uploads/",
)

_SKIP_API_PREFIXES: tuple[str, ...] = (
    "/api/v1/health",
    "/api/v1/auth/login",
    "/api/v1/auth/refresh",
    "/api/v1/feishu/webhook",
)


def should_scan_path(path: str) -> bool:
    """should_scan_path。

    参数说明：
    :param path: 参数 path
    :return: 返回处理结果。
    """
    if not path.startswith("/api/"):
        return False
    if path in ("/", "/health", "/health/ready"):
        return False
    for prefix in _SKIP_PATH_PREFIXES:
        if path.startswith(prefix):
            return False
    for prefix in _SKIP_API_PREFIXES:
        if path.startswith(prefix):
            return False
    return True


def _walk(obj: Any, *, path: str, out: list[str], budget: list[int]) -> None:
    """_walk。

    参数说明：
    :param obj: 参数 obj
    :param path: 参数 path
    :param out: 参数 out
    :param budget: 参数 budget
    :return: 返回处理结果。
    """
    if budget[0] <= 0:
        return
    budget[0] -= 1
    if not isinstance(obj, dict):
        if isinstance(obj, list):
            for i, item in enumerate(obj[:50]):
                _walk(item, path=f"{path}[{i}]", out=out, budget=budget)
        return

    if obj.get("mock") is True and obj.get("mode") != "mock":
        out.append(f"{path or '$'}: mock=true 但未标记 mode=mock")

    if obj.get("data_source") == "mock":
        out.append(f"{path or '$'}: data_source=mock")

    if obj.get("probe_mode") in ("stub", "mock", "demo") and obj.get("included") is True:
        out.append(f"{path or '$'}: stub 探测 included=true")

    msg = obj.get("message")
    if isinstance(msg, str) and _FAKE_MESSAGE_HINTS.search(msg):
        if obj.get("mode") != "mock" and not _subtree_marked_mock(obj):
            out.append(f"{path or '$'}: message 含模拟/演示文案但未标 mode=mock")

    if obj.get("success") is True and obj.get("data") is None:
        code = str(obj.get("error_code") or "")
        if code not in ("", "0") and "NOT_CONFIGURED" not in code:
            pass
        elif isinstance(msg, str) and _FAKE_MESSAGE_HINTS.search(msg):
            out.append(f"{path or '$'}: success=true 且 message 含模拟文案")

    for key, value in obj.items():
        if key in ("data", "results", "stats", "summary", "payload", "items"):
            _walk(value, path=f"{path}.{key}" if path else key, out=out, budget=budget)
        elif isinstance(value, (dict, list)):
            _walk(value, path=f"{path}.{key}" if path else key, out=out, budget=budget)


def _subtree_marked_mock(obj: dict[str, Any]) -> bool:
    """_subtree_marked_mock。

    参数说明：
    :param obj: 参数 obj
    :return: 返回处理结果。
    """
    data = obj.get("data")
    if isinstance(data, dict) and data.get("mode") == "mock":
        return True
    return obj.get("mode") == "mock"


def find_payload_violations(payload: Any) -> list[str]:
    """扫描 JSON 载荷中的假交付信号（生产路径）。"""
    out: list[str] = []
    _walk(payload, path="", out=out, budget=[_MAX_NODES])
    return out[:20]


def enforce_honest_json_payload(payload: Any, *, request_path: str) -> None:
    """生产环境：检出违规则抛 FakeDeliveryViolation。"""
    if not is_production_environment():
        return
    if not should_scan_path(request_path):
        return
    violations = find_payload_violations(payload)
    if violations:
        raise FakeDeliveryViolation(
            "FAKE_DELIVERY_BLOCKED",
            "响应含未门控的 mock/演示数据，生产路径已拒绝",
            violations=violations,
        )


def scan_response_bytes(body: bytes, *, request_path: str) -> list[str]:
    """scan_response_bytes。

    参数说明：
    :param body: 参数 body
    :param request_path: 参数 request_path
    :return: 返回处理结果。
    """
    if not body or not is_production_environment():
        return []
    if not should_scan_path(request_path):
        return []
    try:
        payload = json.loads(body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return []
    return find_payload_violations(payload)
