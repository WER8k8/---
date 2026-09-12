"""万里汇 WorldFirst Webhook → 财迷疯 survival 台账（摸金校尉 L6 自动收款）。"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import settings
from app.services.hermes.greedy_avatar_constitution import assert_greedy_action
from app.services.hermes.platform_survival_service import record_worldfirst_inbound

logger = logging.getLogger("uj-admin.worldfirst_webhook")

# 常见 JPY 等零小数货币
_ZERO_DECIMAL_CURRENCIES = frozenset({"JPY", "KRW", "VND"})


def _webhook_secret() -> str:
    """_webhook_secret。
    :return: 返回处理结果。
    """
    return (getattr(settings, "SURVIVAL_WORLDFIRST_WEBHOOK_SECRET", None) or "").strip()


def verify_worldfirst_webhook(
    raw_body: bytes,
    *,
    signature_header: str | None = None,
    authorization_header: str | None = None,
) -> str | None:
    """校验 webhook；通过返回 None，失败返回原因。"""
    secret = _webhook_secret()
    if not secret:
        return "webhook_secret_not_configured"

    auth = (authorization_header or "").strip()
    if auth == f"Bearer {secret}" or auth == secret:
        return None

    sig = (signature_header or "").strip()
    if sig.startswith("sha256="):
        sig = sig[7:]
    if sig:
        expected = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
        if hmac.compare_digest(expected.lower(), sig.lower()):
            return None
        return "invalid_signature"

    return "missing_auth_or_signature"


def _pick_str(data: dict[str, Any], *keys: str) -> str:
    """_pick_str。

    参数说明：
    :param data: 参数 data
    :param *keys: 参数 *keys
    :return: 返回处理结果。
    """
    for k in keys:
        v = data.get(k)
        if v is not None and str(v).strip():
            return str(v).strip()
    return ""


def _parse_amount_minor(data: dict[str, Any], currency: str) -> int | None:
    """_parse_amount_minor。

    参数说明：
    :param data: 参数 data
    :param currency: 参数 currency
    :return: 返回处理结果。
    """
    if data.get("amount_minor") is not None:
        try:
            return int(data["amount_minor"])
        except (TypeError, ValueError):
            return None
    raw = data.get("amount") or data.get("payment_amount") or data.get("receive_amount")
    if raw is None:
        return None
    try:
        val = float(raw)
    except (TypeError, ValueError):
        return None
    cur = (currency or "USD").upper()
    if cur in _ZERO_DECIMAL_CURRENCIES:
        return int(round(val))
    return int(round(val * 100))


def _is_settled_status(data: dict[str, Any]) -> bool:
    """_is_settled_status。

    参数说明：
    :param data: 参数 data
    :return: 返回处理结果。
    """
    status = _pick_str(data, "status", "payment_status", "transaction_status").lower()
    if not status:
        return True
    return status in (
        "settled",
        "success",
        "completed",
        "paid",
        "received",
        "credit",
        "succeeded",
    )


def parse_worldfirst_webhook_payload(raw_body: bytes) -> dict[str, Any]:
    """解析万里汇/兼容入账 JSON。"""
    try:
        data = json.loads(raw_body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        return {"ok": False, "error": f"invalid_json:{exc}"}

    if isinstance(data.get("data"), dict):
        inner = data["data"]
        merged = {**data, **inner}
    else:
        merged = data

    tx_id = _pick_str(
        merged,
        "transaction_id",
        "transactionId",
        "payment_id",
        "paymentId",
        "id",
        "order_id",
        "orderId",
    )
    currency = _pick_str(merged, "currency", "payment_currency", "receive_currency") or "USD"
    amount_minor = _parse_amount_minor(merged, currency)
    inbound_type = _pick_str(merged, "inbound_type", "type", "payment_type", "biz_type") or "b2b_tt"
    if not tx_id:
        return {"ok": False, "error": "missing_transaction_id", "raw_keys": list(merged.keys())[:20]}
    if amount_minor is None or amount_minor <= 0:
        return {"ok": False, "error": "missing_or_invalid_amount", "transaction_id": tx_id}
    if not _is_settled_status(merged):
        return {
            "ok": False,
            "error": "status_not_settled",
            "transaction_id": tx_id,
            "status": merged.get("status"),
        }

    return {
        "ok": True,
        "transaction_id": tx_id,
        "amount_minor": amount_minor,
        "currency": currency.upper(),
        "inbound_type": inbound_type.lower().replace("-", "_")[:40],
        "note": _pick_str(merged, "note", "remark", "description")[:500] or "worldfirst_webhook",
    }


def handle_worldfirst_webhook(
    db: Session,
    raw_body: bytes,
    *,
    signature_header: str | None = None,
    authorization_header: str | None = None,
) -> dict[str, Any]:
    """Webhook 入口：验签 → 解析 → survival 入账（幂等）。"""
    assert_greedy_action("record_survival_settlement")
    auth_err = verify_worldfirst_webhook(
        raw_body,
        signature_header=signature_header,
        authorization_header=authorization_header,
    )
    if auth_err:
        return {"ok": False, "error": auth_err}

    parsed = parse_worldfirst_webhook_payload(raw_body)
    if not parsed.get("ok"):
        return parsed

    result = record_worldfirst_inbound(
        db,
        amount_minor=int(parsed["amount_minor"]),
        currency=str(parsed["currency"]),
        transaction_id=str(parsed["transaction_id"]),
        inbound_type=str(parsed.get("inbound_type") or "b2b_tt"),
        note=str(parsed.get("note") or "worldfirst_webhook"),
        recorded_by_user_id="worldfirst_webhook",
    )
    assert_greedy_action("emit_greedy_alert")
    logger.info(
        "WorldFirst webhook survival recorded tx=%s duplicate=%s",
        parsed["transaction_id"],
        result.get("duplicate"),
    )
    return {
        "ok": result.get("ok", False),
        "duplicate": result.get("duplicate"),
        "entry_id": result.get("entry_id"),
        "transaction_id": parsed["transaction_id"],
        "amount_minor": parsed["amount_minor"],
        "currency": parsed["currency"],
        "source": "worldfirst_webhook",
    }


def webhook_setup_meta() -> dict[str, Any]:
    """webhook_setup_meta。
    :return: 返回处理结果。
    """
    secret_set = bool(_webhook_secret())
    return {
        "webhook_path": "/api/v1/hermes/ops/survival/worldfirst/webhook",
        "auth": "Bearer SURVIVAL_WORLDFIRST_WEBHOOK_SECRET or HMAC-SHA256 header X-WorldFirst-Signature",
        "secret_configured": secret_set,
        "payload_fields": {
            "transaction_id": "required (or transactionId/id)",
            "amount_minor": "preferred",
            "amount": "major units if amount_minor omitted",
            "currency": "USD/EUR/CNY/...",
            "status": "settled|success|completed (optional)",
            "inbound_type": "b2b_tt|pi_payment|...",
        },
    }
