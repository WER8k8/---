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
    # 优先级 1：os.environ 显式注入（测试/mock 可在运行时覆盖）。真实运行时环境变量
    # 无此键 → 走优先级 2。注意：env_file 不注入 os.environ，仅读 os.getenv 恒为
    # False（原实现缺陷）→ 真实运行硬拦从未生效，故需回退到 Settings 字段。
    for flag in ("ACQ_HARD_BLOCK_TOKEN", "TOKEN_WALLET_HARD_BLOCK"):
        v = os.getenv(flag)
        if v is not None and v.strip() != "":
            return str(v).strip().lower() in ("1", "true", "yes", "on")
    # 优先级 2：Settings 字段（pydantic 从 env_file 解析，真实运行真相源）
    try:
        from app.core.config import settings  # noqa: PLC0415
    except Exception:  # noqa: BLE001
        return False
    for flag in ("ACQ_HARD_BLOCK_TOKEN", "TOKEN_WALLET_HARD_BLOCK"):
        v = getattr(settings, flag, None)
        if v is not None and v != "" and str(v).strip().lower() not in ("0", "false", "no", "off", ""):
            return str(v).strip().lower() in ("1", "true", "yes", "on")
    return False


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


class WalletBlockedError(Exception):
    """租户 Token 余额耗尽且硬拦开启时抛出，用于在 AI/派发任务执行前硬拦。"""


def enforce_wallet_gate(tenant_id: str, db: Any = None) -> None:
    """AI/派发任务执行前的真实硬拦：不开库则诚实放行。

    - 硬拦未开启 → 放行（影子态，零回归）
    - 无真实账本余额 / 未知 → 放行（不误拦，不编造余额）
    - 真实余额 <= 0 且硬拦开启 → 抛 WalletBlockedError 阻止任务执行
    这是 check_wallet_status（仅报告）的强制版；把「影子计量」变成「真硬拦」。
    """
    tenant_id = (tenant_id or "").strip()
    if not tenant_id:
        return
    if not _hard_block_enabled():
        return
    session, owned = _resolve_or_open_db(db)
    if session is None:
        return  # 无法读取账本：诚实放行
    try:
        balance = _read_latest_balance(session, tenant_id)
    finally:
        if owned:
            session.close()
    if balance is None:
        return  # 未知：不误拦
    if balance <= 0:
        raise WalletBlockedError(
            f"租户 {tenant_id} Token 余额为 {balance}，硬拦已开启：请先充值再执行 AI/派发任务。"
        )


def _resolve_or_open_db(db: Any = None) -> tuple[Optional[Any], bool]:
    """优先复用传入 session；否则最佳努力开一个 SessionLocal（owned=True 需调用方关闭）。

    返回 (session, owned)。任一环节失败返回 (None, False)，不做假。
    """
    if _resolve_db(db) is not None:
        return _resolve_db(db), False
    try:
        from app.core.database import SessionLocal  # noqa: PLC0415

        return SessionLocal(), True
    except Exception:  # noqa: BLE001
        return None, False


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
