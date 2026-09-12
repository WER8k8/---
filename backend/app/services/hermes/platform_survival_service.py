"""Hermes 平台生存基金 — 财迷疯真钱账本（仅超管收款，与租户账单隔离）。"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.platform_survival_ledger import WALLET_SCOPE, PlatformSurvivalLedgerEntry

logger = logging.getLogger("uj-admin.platform_survival")

_CHARTER_PATH = Path(__file__).resolve().parents[2] / "data" / "hermes_platform_survival_charter.json"


@lru_cache(maxsize=1)
def load_survival_charter() -> dict[str, Any]:
    """load_survival_charter。
    :return: 返回处理结果。
    """
    if not _CHARTER_PATH.is_file():
        return {}
    with open(_CHARTER_PATH, encoding="utf-8") as f:
        return json.load(f)


def _fx_to_cny(currency: str, amount_minor: int) -> tuple[int, str]:
    """_fx_to_cny。

    参数说明：
    :param currency: 参数 currency
    :param amount_minor: 参数 amount_minor
    :return: 返回处理结果。
    """
    charter = load_survival_charter()
    rates = charter.get("fx_to_cny") or {"CNY": 1.0}
    cur = (currency or "CNY").upper()
    rate = float(rates.get(cur, 1.0 if cur == "CNY" else 0))
    if rate <= 0:
        rate = 1.0
    base = int(round(amount_minor * rate))
    return base, str(rate)


def _today_utc() -> datetime:
    """_today_utc。
    :return: 返回处理结果。
    """
    return datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)


def record_survival_settlement(
    db: Session,
    *,
    amount_minor: int,
    currency: str,
    channel: str,
    payment_provider: str,
    provider_payment_id: str,
    entry_type: str = "revenue",
    status: str = "settled",
    opportunity_id: str | None = None,
    ecc_verdict: str | None = None,
    recorded_by_user_id: str | None = None,
    note: str | None = None,
) -> dict[str, Any]:
    """
    入账真钱。幂等键：payment_provider + provider_payment_id。
    禁止 tenant_id —  survival 钱包只属于平台超管。
    """
    if amount_minor <= 0:
        return {"ok": False, "error": "amount_must_be_positive"}
    if not provider_payment_id or not payment_provider:
        return {"ok": False, "error": "provider_payment_id_required_for_real_money"}
    if status != "settled":
        return {"ok": False, "error": "only_settled_counts_for_survival_kpi"}

    try:
        from app.services.hermes.greedy_avatar_constitution import assert_greedy_action
        assert_greedy_action("record_survival_settlement")
    except Exception:
        pass

    existing = (
        db.query(PlatformSurvivalLedgerEntry)
        .filter(
            PlatformSurvivalLedgerEntry.payment_provider == payment_provider,
            PlatformSurvivalLedgerEntry.provider_payment_id == provider_payment_id,
        )
        .first()
    )
    if existing:
        return {
            "ok": True,
            "duplicate": True,
            "entry_id": existing.id,
            "amount_base_minor": existing.amount_base_minor,
        }

    base_minor, fx = _fx_to_cny(currency, amount_minor)
    row = PlatformSurvivalLedgerEntry(
        wallet_scope=WALLET_SCOPE,
        entry_type=entry_type,
        channel=channel,
        amount_minor=amount_minor,
        currency=currency.upper(),
        amount_base_minor=base_minor,
        base_currency="CNY",
        fx_rate_to_base=fx,
        payment_provider=payment_provider,
        provider_payment_id=provider_payment_id,
        status=status,
        opportunity_id=opportunity_id,
        ecc_verdict=ecc_verdict,
        recorded_by_user_id=recorded_by_user_id,
        note=(note or "")[:2000] or None,
        recorded_at=datetime.now(timezone.utc),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    logger.info(
        "Platform survival settled %s %s minor=%s base_cny=%s",
        payment_provider,
        provider_payment_id,
        amount_minor,
        base_minor,
    )
    try:
        from app.services.hermes.greedy_contest_memory_service import attribute_settlement_to_contest
        attribute_settlement_to_contest(
            amount_base_minor=base_minor,
            currency=currency,
            provider_payment_id=provider_payment_id,
        )
    except Exception as exc:
        logger.debug("contest settlement attribute skipped: %s", exc)
    return {
        "ok": True,
        "duplicate": False,
        "entry_id": row.id,
        "amount_minor": amount_minor,
        "currency": currency.upper(),
        "amount_base_minor": base_minor,
    }


def record_worldfirst_inbound(
    db: Session,
    *,
    amount_minor: int,
    currency: str,
    transaction_id: str,
    inbound_type: str = "b2b_tt",
    note: str | None = None,
    recorded_by_user_id: str | None = None,
) -> dict[str, Any]:
    """
    万里汇入账 — survival 唯一主通道。
    transaction_id：万里汇交易号/入账流水号（幂等）。
    amount_minor：最小货币单位（USD 用分，JPY 用 1 日元等，与 WF 账单一致）。
    """
    channel = f"worldfirst_{(inbound_type or 'b2b_tt').strip().lower()}"
    return record_survival_settlement(
        db,
        amount_minor=amount_minor,
        currency=currency,
        channel=channel,
        payment_provider="worldfirst",
        provider_payment_id=transaction_id.strip(),
        recorded_by_user_id=recorded_by_user_id,
        note=note,
    )


def worldfirst_setup_hints() -> dict[str, Any]:
    """worldfirst_setup_hints。
    :return: 返回处理结果。
    """
    charter = load_survival_charter()
    wf = charter.get("worldfirst") or {}
    hints: dict[str, Any] = {
        "selected": wf.get("selected", True),
        "register_url": wf.get("register_url"),
        "support_email_b2b": wf.get("support_email_b2b"),
        "onboarding_checklist": wf.get("onboarding_checklist") or [],
        "use_for": wf.get("use_for") or [],
        "settlement_to": wf.get("settlement_to") or [],
        "inbound_types": wf.get("inbound_types") or [],
        "tenant_domestic_separate": charter.get("tenant_domestic_rails") or [],
        "api_record": "POST /api/v1/hermes/ops/survival/worldfirst/record",
        "api_webhook": "POST /api/v1/hermes/ops/survival/worldfirst/webhook",
        "webhook_auth": "Bearer SURVIVAL_WORLDFIRST_WEBHOOK_SECRET or X-WorldFirst-Signature HMAC-SHA256",
    }
    try:
        from app.services.hermes.worldfirst_webhook_service import webhook_setup_meta
        hints["webhook"] = webhook_setup_meta()
    except Exception:
        hints["webhook"] = {}
    return hints


def record_infra_cost(
    db: Session,
    *,
    amount_minor: int,
    channel: str,
    provider_payment_id: str,
    note: str | None = None,
    recorded_by_user_id: str | None = None,
) -> dict[str, Any]:
    """记录基础设施支出（云主机/GPU 等），用于 runway 计算。"""
    return record_survival_settlement(
        db,
        amount_minor=amount_minor,
        currency="CNY",
        channel=channel,
        payment_provider="platform_infra",
        provider_payment_id=provider_payment_id,
        entry_type="infra_cost",
        status="settled",
        recorded_by_user_id=recorded_by_user_id,
        note=note,
    )


def _sum_base_minor(
    db: Session,
    *,
    entry_types: tuple[str, ...],
    since: datetime | None = None,
) -> int:
    """_sum_base_minor。

    参数说明：
    :param db: 参数 db
    :param entry_types: 参数 entry_types
    :param since: 参数 since
    :return: 返回处理结果。
    """
    q = db.query(func.coalesce(func.sum(PlatformSurvivalLedgerEntry.amount_base_minor), 0)).filter(
        PlatformSurvivalLedgerEntry.wallet_scope == WALLET_SCOPE,
        PlatformSurvivalLedgerEntry.status == "settled",
        PlatformSurvivalLedgerEntry.entry_type.in_(entry_types),
    )
    if since:
        q = q.filter(PlatformSurvivalLedgerEntry.recorded_at >= since)
    return int(q.scalar() or 0)


def _lifetime_balance_base_minor(db: Session) -> int:
    """_lifetime_balance_base_minor。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    rev = _sum_base_minor(db, entry_types=("revenue",))
    cost = _sum_base_minor(db, entry_types=("infra_cost",))
    refunds = _sum_base_minor(db, entry_types=("refund",))
    return rev - cost - refunds


def greedy_survival_pulse(db: Session) -> dict[str, Any]:
    """财迷疯脉搏 — 仅统计 platform_survival 真钱，不含租户订阅、不含虚拟积分。"""
    charter = load_survival_charter()
    target = charter.get("daily_target") or {}
    primary = target.get("primary") or {"currency": "CNY", "amount_minor": 100000}
    target_minor = int(primary.get("amount_minor") or 100000)
    target_currency = primary.get("currency") or "CNY"
    today_start = _today_utc()
    settled_today = _sum_base_minor(db, entry_types=("revenue",), since=today_start)
    balance = _lifetime_balance_base_minor(db)
    infra = charter.get("infra") or {}
    daily_burn = int(infra.get("daily_burn_cny_minor") or 50000)
    runway_warning = int(infra.get("runway_warning_days") or 14)
    runway_critical = int(infra.get("runway_critical_days") or 7)
    runway_days = round(balance / daily_burn, 1) if daily_burn > 0 else 0.0
    progress_pct = round(settled_today / target_minor * 100, 1) if target_minor else 0.0
    greedy = charter.get("greedy_personality") or {}
    if runway_days <= runway_critical or progress_pct < 30:
        threat = "critical"
        mood = "shutdown_risk"
        headline = greedy.get("shutdown_line") or "生存线告急"
    elif runway_days <= runway_warning or progress_pct < 60:
        threat = "warning"
        mood = "anxious"
        headline = f"今日实收 ¥{settled_today / 100:.2f} / 目标 ¥{target_minor / 100:.2f} — Hermes 还在饿肚子"
    elif progress_pct >= 100:
        threat = "ok"
        mood = "celebrate"
        headline = greedy.get("success_line") or "今日真钱已达标"
    else:
        threat = "ok"
        mood = "hustling"
        headline = f"今日实收 ¥{settled_today / 100:.2f}，继续为更强硬件挣真钱"

    return {
        "wallet_scope": WALLET_SCOPE,
        "beneficiary": charter.get("beneficiary"),
        "tenant_billing_separate": True,
        "virtual_credits_in_kpi": False,
        "daily_target": {
            "amount_minor": target_minor,
            "currency": target_currency,
            "display": f"¥{target_minor / 100:.2f} {target_currency}",
        },
        "settled_today_base_minor": settled_today,
        "settled_today_display_cny": round(settled_today / 100, 2),
        "progress_pct": progress_pct,
        "lifetime_balance_base_minor": balance,
        "lifetime_balance_display_cny": round(balance / 100, 2),
        "daily_burn_cny_minor": daily_burn,
        "runway_days": runway_days,
        "threat_level": threat,
        "mood": mood,
        "headline": headline,
        "mission": charter.get("mission"),
        "as_of": datetime.now(timezone.utc).isoformat(),
    }


def survival_status(db: Session, *, recent_limit: int = 10) -> dict[str, Any]:
    """survival_status。

    参数说明：
    :param db: 参数 db
    :param recent_limit: 参数 recent_limit
    :return: 返回处理结果。
    """
    pulse = greedy_survival_pulse(db)
    rows = (
        db.query(PlatformSurvivalLedgerEntry)
        .filter(PlatformSurvivalLedgerEntry.wallet_scope == WALLET_SCOPE)
        .order_by(PlatformSurvivalLedgerEntry.recorded_at.desc())
        .limit(recent_limit)
        .all()
    )
    return {
        "charter_version": load_survival_charter().get("version"),
        "primary_rail": "worldfirst",
        "worldfirst": worldfirst_setup_hints(),
        "pulse": pulse,
        "recent_entries": [
            {
                "id": r.id,
                "entry_type": r.entry_type,
                "channel": r.channel,
                "amount_minor": r.amount_minor,
                "currency": r.currency,
                "amount_base_minor": r.amount_base_minor,
                "payment_provider": r.payment_provider,
                "provider_payment_id": (r.provider_payment_id or "")[:24],
                "recorded_at": r.recorded_at.isoformat() if r.recorded_at else None,
            }
            for r in rows
        ],
    }
