# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""禁止假交付 — 生产路径门控助手。"""

from __future__ import annotations

import os
from typing import Any, Callable

from app.core.config import settings


class NotConfiguredError(RuntimeError):
    """上游/能力未配置，不得伪装成功。"""
    def __init__(self, code: str, message: str):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param code: 参数 code
        :param message: 参数 message
        :return: 返回处理结果。
        """
        self.code = code
        super().__init__(message)


class FakeDeliveryViolation(RuntimeError):
    """出站响应或业务结果违反禁止假交付宪章。"""
    def __init__(
        self,
        code: str,
        message: str,
        *,
        violations: list[str] | None = None,
    ):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param code: 参数 code
        :param message: 参数 message
        :param violations: 参数 violations
        :return: 返回处理结果。
        """
        self.code = code
        self.violations = violations or []
        super().__init__(message)


def is_production_environment() -> bool:
    """is_production_environment。
    :return: 返回处理结果。
    """
    return (settings.ENVIRONMENT or "").strip().lower() == "production"


def mock_allowed(env_flag: str | None = None) -> bool:
    """是否允许显式 Mock（开发或 env 显式开启）。"""
    if not is_production_environment():
        return True
    if env_flag:
        return os.getenv(env_flag, "").strip().lower() in ("1", "true", "yes")
    return False


def require_configured(
    condition: bool,
    *,
    code: str,
    message: str,
) -> None:
    """require_configured。

    参数说明：
    :param condition: 参数 condition
    :param code: 参数 code
    :param message: 参数 message
    :return: 返回处理结果。
    """
    if not condition:
        raise NotConfiguredError(code, message)


def is_mock_payload(payload: dict[str, Any]) -> bool:
    """响应是否为显式 mock（兼容旧 mock 字段）。"""
    return payload.get("mode") == "mock" or payload.get("mock") is True


def stamp_mock(payload: dict[str, Any], *, reason: str) -> dict[str, Any]:
    """开发 Mock 响应必须带 mode 标记。"""
    out = dict(payload)
    out["mode"] = "mock"
    out["mock_reason"] = reason
    return out


def assert_not_fake_success(
    *,
    ok: bool,
    evidence: Any,
    code: str,
    message: str,
) -> None:
    """assert_not_fake_success。

    参数说明：
    :param ok: 参数 ok
    :param evidence: 参数 evidence
    :param code: 参数 code
    :param message: 参数 message
    :return: 返回处理结果。
    """
    if ok and not evidence:
        raise NotConfiguredError(code, message)


def dev_mock_or_raise(
    *,
    env_flag: str | None,
    mock_builder: Callable[[], dict[str, Any]],
    error_code: str,
    message: str,
) -> dict[str, Any]:
    """开发：stamp_mock；生产：NotConfiguredError。"""
    if mock_allowed(env_flag):
        return stamp_mock(mock_builder(), reason=error_code.lower())
    raise NotConfiguredError(error_code, message)


def reject_production_mock_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """生产路径禁止未标记 mock 载荷透出。"""
    if is_production_environment() and payload.get("mock") is True and payload.get("mode") != "mock":
        raise FakeDeliveryViolation(
            "UNMARKED_MOCK_PAYLOAD",
            "生产路径禁止 mock:true 且无 mode=mock",
        )
    return payload
