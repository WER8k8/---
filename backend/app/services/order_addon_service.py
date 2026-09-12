"""Token 加购 — 支付成功后充值 Token（幂等按 order_no）。"""

from __future__ import annotations

import re

from sqlalchemy.orm import Session

from app.models.payment import PaymentOrder
from app.models.tenant import Tenant
from app.models.token_ledger import TokenLedgerEntry
from app.services.token_service import TokenService

TOKEN_SUBJECT_RE = re.compile(r"\[addon:token:(\d+)(?::([a-z0-9_]+))?\]", re.I)

# 标准 Token 包（pack_id → 规格）
TOKEN_PACK_CATALOG: dict[str, dict] = {
    "pack_10k": {"tokens": 10_000, "price_cents": 9900, "label": "1万 Token 包"},
    "pack_50k": {"tokens": 50_000, "price_cents": 39900, "label": "5万 Token 包"},
    "pack_100k": {"tokens": 100_000, "price_cents": 69900, "label": "10万 Token 包"},
}

# 自定义充值：按「1万点 / ¥99」折算（与 pack_10k 一致）
CUSTOM_RECHARGE_MIN_YUAN = 10.0
CUSTOM_RECHARGE_MAX_YUAN = 50_000.0
CUSTOM_RECHARGE_MIN_TOKENS = 100
_CUSTOM_BASE_TOKENS = 10_000
_CUSTOM_BASE_CENTS = 9900


def custom_recharge_config_for_client() -> dict:
    """custom_recharge_config_for_client。
    :return: 返回处理结果。
    """
    yuan_per_pack = _CUSTOM_BASE_CENTS / 100
    return {
        "enabled": True,
        "min_yuan": CUSTOM_RECHARGE_MIN_YUAN,
        "max_yuan": CUSTOM_RECHARGE_MAX_YUAN,
        "min_tokens": CUSTOM_RECHARGE_MIN_TOKENS,
        "rate_description": f"¥{yuan_per_pack:g} 约到账 {_CUSTOM_BASE_TOKENS:,} 点 AI 流量",
        "tokens_per_yuan": round(_CUSTOM_BASE_TOKENS / yuan_per_pack, 2),
    }


def quote_custom_token_recharge(amount_yuan: float) -> dict:
    """按支付金额（元）估算到账流量与分。"""
    try:
        yuan = float(amount_yuan)
    except (TypeError, ValueError) as exc:
        raise ValueError("充值金额无效") from exc
    if yuan < CUSTOM_RECHARGE_MIN_YUAN:
        raise ValueError(f"自定义充值不能低于 ¥{CUSTOM_RECHARGE_MIN_YUAN:g}")
    if yuan > CUSTOM_RECHARGE_MAX_YUAN:
        raise ValueError(f"自定义充值不能超过 ¥{CUSTOM_RECHARGE_MAX_YUAN:g}")
    price_cents = max(1, int(round(yuan * 100)))
    tokens = int(price_cents * _CUSTOM_BASE_TOKENS / _CUSTOM_BASE_CENTS)
    if tokens < CUSTOM_RECHARGE_MIN_TOKENS:
        raise ValueError(
            f"金额过小，至少需到账 {CUSTOM_RECHARGE_MIN_TOKENS} 点流量，请提高金额或选择固定流量包"
        )
    return {
        "amount_yuan": round(yuan, 2),
        "price_cents": price_cents,
        "price_yuan": round(price_cents / 100, 2),
        "tokens": tokens,
        "label": f"自定义 ¥{round(yuan, 2):g}",
    }


def resolve_custom_token_recharge(amount_yuan: float) -> dict:
    """resolve_custom_token_recharge。

    参数说明：
    :param amount_yuan: 参数 amount_yuan
    :return: 返回处理结果。
    """
    return quote_custom_token_recharge(amount_yuan)


def parse_token_addon(subject: str) -> tuple[int | None, str | None]:
    """parse_token_addon。

    参数说明：
    :param subject: 参数 subject
    :return: 返回处理结果。
    """
    m = TOKEN_SUBJECT_RE.search(subject or "")
    if not m:
        return None, None
    amount = max(1, min(1_000_000, int(m.group(1))))
    provider = (m.group(2) or "").strip().lower() or None
    return amount, provider


def parse_token_amount(subject: str) -> int | None:
    """parse_token_amount。

    参数说明：
    :param subject: 参数 subject
    :return: 返回处理结果。
    """
    amount, _ = parse_token_addon(subject)
    return amount


def token_addon_subject(tokens: int, provider_id: str | None = None) -> str:
    """token_addon_subject。

    参数说明：
    :param tokens: 参数 tokens
    :param provider_id: 参数 provider_id
    :return: 返回处理结果。
    """
    from app.services.ai_traffic_provider_service import provider_label, resolve_provider_id
    if provider_id:
        pid = resolve_provider_id(provider_id)
        label = provider_label(pid)
        return f"[addon:token:{tokens}:{pid}] {label} AI流量 x{tokens:,}"
    return f"[addon:token:{tokens}] AI流量充值 x{tokens:,}"


def resolve_pack(pack_id: str) -> dict:
    """resolve_pack。

    参数说明：
    :param pack_id: 参数 pack_id
    :return: 返回处理结果。
    """
    pack = TOKEN_PACK_CATALOG.get(pack_id)
    if not pack:
        raise ValueError(f"未知 Token 包: {pack_id}")
    return pack


def apply_token_addon(db: Session, order: PaymentOrder) -> dict | None:
    """apply_token_addon。

    参数说明：
    :param db: 参数 db
    :param order: 参数 order
    :return: 返回处理结果。
    """
    tokens, provider_id = parse_token_addon(order.subject)
    if not tokens:
        return None

    tenant = db.query(Tenant).filter(Tenant.id == order.tenant_id).first()
    if not tenant:
        return {"ok": False, "reason": "tenant_not_found"}

    if provider_id:
        from app.services.ai_traffic_provider_service import set_tenant_ai_traffic_provider
        try:
            set_tenant_ai_traffic_provider(db, tenant, provider_id)
        except ValueError:
            pass

    dup = (
        db.query(TokenLedgerEntry)
        .filter(
            TokenLedgerEntry.tenant_id == order.tenant_id,
            TokenLedgerEntry.reference_id == order.order_no,
        )
        .first()
    )
    if dup:
        return {"ok": True, "addon": "token", "tokens": tokens, "skipped": True}

    balance = TokenService(db).credit(
        order.tenant_id,
        tokens,
        "token_pack_purchase",
        reference_id=order.order_no,
    )
    db.commit()
    return {
        "ok": True,
        "addon": "token",
        "tokens": tokens,
        "balance_after": balance,
        "provider_id": provider_id,
    }


def apply_egress_addon(db: Session, order: PaymentOrder) -> dict | None:
    """apply_egress_addon。

    参数说明：
    :param db: 参数 db
    :param order: 参数 order
    :return: 返回处理结果。
    """
    from app.services.egress_addon_service import parse_addon_slots, bump_egress_quota
    slots = parse_addon_slots(order.subject)
    if not slots:
        return None
    tenant = db.query(Tenant).filter(Tenant.id == order.tenant_id).first()
    if not tenant:
        return {"ok": False, "reason": "tenant_not_found"}
    result = bump_egress_quota(db, tenant, slots)
    return {"ok": True, "addon": "egress_ip", "slots": slots, **result}


def apply_order_addon(db: Session, order: PaymentOrder) -> dict | None:
    """解析订单 subject，分发至 Token / IP 槽位加购（互斥）。"""
    token_result = apply_token_addon(db, order)
    if token_result is not None:
        return token_result
    return apply_egress_addon(db, order)


def is_addon_order(order: PaymentOrder) -> bool:
    """is_addon_order。

    参数说明：
    :param order: 参数 order
    :return: 返回处理结果。
    """
    subj = order.subject or ""
    return "[addon:" in subj
