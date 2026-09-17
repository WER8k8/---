# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Stripe 支付集成骨架 — 轻量 httpx 直调 REST API，不强依赖 stripe SDK。

功能：
- create_checkout_session  创建 Stripe Checkout Session
- verify_webhook_signature  验证 Webhook 签名
- parse_webhook_event  解析事件 payload

安全设计：
- FF_STRIPE_ENABLED 关闭或 STRIPE_SECRET_KEY 缺失时返回 mock / 明确错误，不硬失败启动。
- 日志中绝不泄露完整 key / secret（仅打印前 8 位用于排查）。
- 结构化日志 logger name: uj-admin.payment.stripe
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import time
from typing import Any
from urllib.parse import urlencode

import httpx

from app.core.config import settings
import os

def _is_feature_enabled(name: str) -> bool:
    """检查功能开关是否开启（兼容 settings、环境变量及默认值）。"""
    env_val = os.getenv(name)
    if env_val is not None:
        return env_val.lower() in ("true", "1", "yes", "on")
    return bool(getattr(settings, name, False))

logger = logging.getLogger("uj-admin.payment.stripe")

# Stripe API 基础地址
_STRIPE_API_BASE = "https://api.stripe.com/v1"

# Webhook 签名时间容差（秒），防止重放攻击
_WEBHOOK_TOLERANCE_SEC = 300


# ---------------------------------------------------------------------------
# 内部工具
# ---------------------------------------------------------------------------


def _get_secret_key() -> str:
    """从 settings 读取 STRIPE_SECRET_KEY，不存在返回空字符串。"""
    return getattr(settings, "STRIPE_SECRET_KEY", "") or ""


def _get_webhook_secret() -> str:
    """从 settings 读取 STRIPE_WEBHOOK_SECRET，不存在返回空字符串。"""
    return getattr(settings, "STRIPE_WEBHOOK_SECRET", "") or ""


def _masked_key(key: str) -> str:
    """返回密钥的掩码形式，用于安全日志（仅保留前 8 位）。"""
    if len(key) <= 8:
        return "****"
    return key[:8] + "****"


def is_stripe_ready() -> bool:
    """判断 Stripe 支付是否就绪：开关已开启 且 密钥已配置。"""
    if not _is_feature_enabled("FF_STRIPE_ENABLED"):
        return False
    secret_key = _get_secret_key()
    return bool(secret_key and secret_key.startswith(("sk_live_", "sk_test_")))


def _build_headers() -> dict[str, str]:
    """构造 Stripe REST API 请求头。"""
    return {
        "Authorization": f"Bearer {_get_secret_key()}",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
    }


# ---------------------------------------------------------------------------
# 公开 API
# ---------------------------------------------------------------------------


def _mock_checkout_session(tenant_id: str) -> dict[str, Any]:
    """返回 Stripe 未就绪时的 mock session（生产环境则抛错）。"""
    from app.core.no_fake_delivery import is_production_environment
    if is_production_environment():
        raise RuntimeError("STRIPE_NOT_CONFIGURED")
    logger.info(
        "Stripe 未就绪（开关关闭或密钥缺失），返回 mock session | tenant=%s",
        tenant_id or "-",
    )
    from app.core.no_fake_delivery import stamp_mock
    return stamp_mock({
        "id": "cs_mock_" + str(int(time.time())),
        "url": "",
    }, reason="stripe_not_configured_dev")


def _validate_checkout_args(
    *,
    line_items: list[dict[str, Any]],
    success_url: str,
    cancel_url: str,
) -> None:
    """校验 Checkout Session 基础参数，非法时抛 ValueError。"""
    if not line_items:
        raise ValueError("line_items 不能为空")
    if not success_url:
        raise ValueError("success_url 不能为空")
    if not cancel_url:
        raise ValueError("cancel_url 不能为空")


def _build_checkout_form_params(
    line_items: list[dict[str, Any]],
    *,
    mode: str,
    success_url: str,
    cancel_url: str,
    locale: str,
    customer_email: str,
    metadata: dict[str, str] | None,
    currency: str,
) -> dict[str, str]:
    """构造 Stripe Checkout 表单参数（含 line_items / metadata 扁平展开）。"""
    params: dict[str, str] = {
        "mode": mode,
        "success_url": success_url,
        "cancel_url": cancel_url,
        "locale": locale,
    }
    if customer_email:
        params["customer_email"] = customer_email

    for idx, item in enumerate(line_items):
        prefix = f"line_items[{idx}]"
        params[f"{prefix}[quantity]"] = str(item.get("quantity", 1))
        if "price" in item:
            params[f"{prefix}[price]"] = item["price"]
        elif "price_data" in item:
            pd = item["price_data"]
            pd_prefix = f"{prefix}[price_data]"
            params[f"{pd_prefix}[currency]"] = pd.get("currency", currency)
            product_data = pd.get("product_data", {})
            params[f"{pd_prefix}[product_data][name]"] = product_data.get("name", "")
            if product_data.get("description"):
                params[f"{pd_prefix}[product_data][description]"] = product_data["description"]
            params[f"{pd_prefix}[unit_amount]"] = str(pd.get("unit_amount", 0))

    if metadata:
        for k, v in metadata.items():
            params[f"metadata[{k}]"] = v
    return params


def _call_stripe_checkout_api(
    params: dict[str, str],
    *,
    mode: str,
    line_items: list[dict[str, Any]],
    tenant_id: str,
) -> dict[str, Any]:
    """调用 Stripe Checkout API 并返回会话字典，失败抛 RuntimeError。"""
    logger.info(
        "创建 Checkout Session | mode=%s | items=%d | tenant=%s | key=%s",
        mode,
        len(line_items),
        tenant_id or "-",
        _masked_key(_get_secret_key()),
    )
    url = f"{_STRIPE_API_BASE}/checkout/sessions"
    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, content=urlencode(params).encode("utf-8"), headers=_build_headers())
    except httpx.HTTPError as exc:
        logger.error("Stripe API 请求异常: %s", exc)
        raise RuntimeError(f"Stripe API 请求失败: {exc}") from exc

    if resp.status_code >= 400:
        error_body = resp.text[:200]
        logger.error("Stripe 创建 Session 失败: HTTP %s | %s", resp.status_code, error_body)
        raise RuntimeError(f"Stripe 创建 Session 失败 HTTP {resp.status_code}")

    data = resp.json()
    logger.info(
        "Checkout Session 创建成功 | id=%s | tenant=%s",
        data.get("id", "?"),
        tenant_id or "-",
    )
    return {
        "id": data.get("id", ""),
        "url": data.get("url", ""),
        "mock": False,
    }


def create_checkout_session(
    *,
    line_items: list[dict[str, Any]],
    mode: str = "payment",
    success_url: str,
    cancel_url: str,
    customer_email: str = "",
    metadata: dict[str, str] | None = None,
    currency: str = "usd",
    locale: str = "auto",
    tenant_id: str = "",
) -> dict[str, Any]:
    """创建 Stripe Checkout Session；未就绪返回 mock，参数非法抛 ValueError。

    返回 {"id", "url", "mock"}；已配置但请求出错抛 RuntimeError。
    """
    if not is_stripe_ready():
        return _mock_checkout_session(tenant_id)
    _validate_checkout_args(line_items=line_items, success_url=success_url, cancel_url=cancel_url)

    params = _build_checkout_form_params(
        line_items,
        mode=mode,
        success_url=success_url,
        cancel_url=cancel_url,
        locale=locale,
        customer_email=customer_email,
        metadata=metadata,
        currency=currency,
    )
    return _call_stripe_checkout_api(
        params,
        mode=mode,
        line_items=line_items,
        tenant_id=tenant_id,
    )


def verify_webhook_signature(
    *,
    payload: bytes,
    sig_header: str,
    webhook_secret: str = "",
) -> bool:
    """验证 Stripe Webhook 签名。

    Stripe-Signature 格式：t=<timestamp>,v1=<signature>
    验证逻辑：HMAC-SHA256(secret, "{timestamp}.{payload}") 与 v1 值进行恒定时间比较。

    参数:
        payload: 原始请求体（bytes）
        sig_header: Stripe-Signature 头的值
        webhook_secret: webhook 密钥，为空时自动从 settings 读取

    返回:
        bool: 签名有效返回 True，否则 False
    """
    secret = webhook_secret or _get_webhook_secret()
    if not secret:
        logger.warning("Stripe Webhook 密钥未配置，无法验签")
        return False

    if not sig_header:
        logger.warning("Stripe-Signature 头缺失")
        return False

    # 解析签名头
    sig_parts: dict[str, str] = {}
    for part in sig_header.split(","):
        kv = part.split("=", 1)
        if len(kv) == 2:
            sig_parts[kv[0].strip()] = kv[1].strip()

    timestamp = sig_parts.get("t", "")
    signature = sig_parts.get("v1", "")
    if not timestamp or not signature:
        logger.warning("Stripe-Signature 格式异常: 缺少 t 或 v1")
        return False

    # 时间容差检查
    try:
        ts_int = int(timestamp)
    except (ValueError, TypeError):
        logger.warning("Stripe-Signature 时间戳格式异常: %s", timestamp)
        return False

    drift = abs(time.time() - ts_int)
    if drift > _WEBHOOK_TOLERANCE_SEC:
        logger.warning("Stripe Webhook 签名过期: drift=%.1fs > %ds", drift, _WEBHOOK_TOLERANCE_SEC)
        return False

    # 计算期望签名
    signed_payload = f"{timestamp}.{payload.decode('utf-8')}"
    expected = hmac.new(
        secret.encode("utf-8"),
        signed_payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    # 恒定时间比较，防止时序攻击
    is_valid = hmac.compare_digest(expected, signature)
    if not is_valid:
        logger.warning("Stripe Webhook 签名验证失败")
    return is_valid


def parse_webhook_event(
    *,
    payload: bytes | str,
) -> dict[str, Any]:
    """解析 Stripe Webhook 事件 payload。

    参数:
        payload: 原始请求体（bytes 或 str）

    返回:
        dict: 标准化事件信息：
            {
                "event_id": "evt_xxx",
                "event_type": "checkout.session.completed",
                "api_version": "2024-06-20",
                "data": {...},          # 事件关联的对象
                "raw_type": "...",      # 原始 type 字段
            }

    抛出:
        ValueError: payload 不是有效 JSON
    """
    if isinstance(payload, bytes):
        payload = payload.decode("utf-8")

    try:
        event = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Stripe Webhook payload 不是有效 JSON: {exc}") from exc

    event_type = event.get("type", "")
    data_obj = event.get("data", {})
    object_data = data_obj.get("object", {}) if isinstance(data_obj, dict) else {}
    logger.info(
        "Stripe Webhook 事件解析 | event_id=%s | type=%s",
        event.get("id", "?"),
        event_type,
    )
    return {
        "event_id": event.get("id", ""),
        "event_type": event_type,
        "api_version": event.get("api_version", ""),
        "data": object_data,
        "raw_type": event_type,
    }
