# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Token 钱包 / 三轨闸 — 读真实账本（有库则读，无库诚实 unknown）。

契约：
    · 有 TokenLedger：取该租户最新 balance_after
    · 余额为 0 且 ACQ_HARD_BLOCK_TOKEN=true → hard_block_enabled=true
    · 无账本/异常：unknown + 不误拦 + 不编造余额
"""
from __future__ import annotations

import logging
import os
from typing import Any, Optional

logger = logging.getLogger(__name__)


def _hard_block_enabled() -> bool:
    v = (os.getenv("ACQ_HARD_BLOCK_TOKEN") or os.getenv("TOKEN_WALLET_HARD_BLOCK") or "").strip().lower()
    return v in ("1", "true", "yes", "on")


def _read_latest_balance(db: Any, tenant_id: str) -> Optional[int]:
    if db is None or not hasattr(db, "query"):
        return None
    try:
        from app.models.token_ledger import TokenLedgerEntry
        from app.services.acquisition.repo import resolve_tenant_uuid

        # PG 下 tenant_id 是 UUID 列：业务串（demo）先解析
        tid = resolve_tenant_uuid(db, tenant_id) or tenant_id
        q = db.query(TokenLedgerEntry).filter(TokenLedgerEntry.tenant_id == tid)
        # 兼容 mock/真实 session：优先 all() 后排序，避免 desc 绑定失败
        try:
            rows = list(q.all())
        except Exception:
            try:
                rows = [q.order_by(TokenLedgerEntry.created_at.desc()).first()]
            except Exception:
                rows = [q.first()]
        rows = [r for r in rows if r is not None]
        if not rows:
            return None
        def _ts(r: Any):
            return getattr(r, "created_at", None) or ""
        rows.sort(key=lambda r: str(_ts(r)))
        bal = getattr(rows[-1], "balance_after", None)
        return None if bal is None else int(bal)
    except Exception as exc:  # noqa: BLE001
        logger.warning("token ledger 读取失败: %s", exc)
        return None


def _resolve_db(db: Any = None) -> Any:
    if db is None or type(db).__name__ == "Depends" or not hasattr(db, "query"):
        return None
    return db


def check_wallet_status(tenant_id: str, db: Any = None) -> dict[str, Any]:
    """查询租户 Token 状态。优先真实 ledger；否则诚实 unknown。"""
    tenant_id = (tenant_id or "").strip() or "unknown"
    session = _resolve_db(db)
    balance = _read_latest_balance(session, tenant_id) if session else None
    hard = _hard_block_enabled()

    if balance is None:
        return {
            "tenant_id": tenant_id,
            "token_balance": None,
            "plan": None,
            "hard_block_enabled": False,
            "status": "unknown",
            "message": "计费账本尚未接入或该租户无流水；不会误拦任务，也不会显示虚假余额。",
            "next_step": "配置 PG 并写入 token_ledger 后显示真实余额",
            "source": "none",
        }

    if balance <= 0 and hard:
        return {
            "tenant_id": tenant_id,
            "token_balance": balance,
            "plan": None,
            "hard_block_enabled": True,
            "status": "blocked",
            "message": f"Token 余额为 {balance}，已开启硬拦：请先充值再执行 AI/派发任务。",
            "next_step": "前往 /client/tokens 充值",
            "source": "token_ledger",
        }

    return {
        "tenant_id": tenant_id,
        "token_balance": balance,
        "plan": None,
        "hard_block_enabled": False,
        "status": "ok" if balance > 0 else "empty",
        "message": (
            f"Token 余额 {balance}。" + ("余额偏低请注意充值。" if balance <= 100 else "正常。")
            if balance is not None else ""
        ),
        "next_step": "",
        "source": "token_ledger",
    }
