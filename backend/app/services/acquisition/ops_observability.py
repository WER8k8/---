# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""E-3 租户配额限流（获客 API）+ E-5 meter vs ledger 日对账。

原则：
    · 限流内存实现（开发/单机）；Redis 可选增强；超限诚实 429
    · 对账只读：meter 与 ledger 误差报告，不自动改账
"""
from __future__ import annotations

import threading
import time
from collections import defaultdict, deque
from datetime import datetime, timezone
from typing import Any, Optional


def _now() -> float:
    return time.time()


class TenantRateLimiter:
    """滑动窗口限流：tenant+action → 次数。"""

    def __init__(self, default_limit: int = 60, window_sec: int = 60) -> None:
        self.default_limit = int(default_limit)
        self.window_sec = int(window_sec)
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, *, tenant_id: str, action: str = "acq_api", limit: Optional[int] = None) -> dict[str, Any]:
        tid = (tenant_id or "unknown").strip() or "unknown"
        key = f"{tid}|{action}"
        lim = int(limit or self.default_limit)
        now = _now()
        cutoff = now - self.window_sec
        with self._lock:
            q = self._hits[key]
            while q and q[0] < cutoff:
                q.popleft()
            used = len(q)
            if used >= lim:
                return {
                    "allowed": False,
                    "code": "rate_limited",
                    "tenant_id": tid,
                    "action": action,
                    "limit": lim,
                    "used": used,
                    "window_sec": self.window_sec,
                    "retry_after_sec": max(1, int(self.window_sec - (now - q[0]))) if q else self.window_sec,
                    "plain": f"租户 {tid} 动作 {action} 超过限流 {lim} 次/{self.window_sec}s，请稍后再试。",
                }
            q.append(now)
            return {
                "allowed": True,
                "code": "ok",
                "tenant_id": tid,
                "action": action,
                "limit": lim,
                "used": used + 1,
                "window_sec": self.window_sec,
                "plain": f"通过限流（{used + 1}/{lim} / {self.window_sec}s）。",
            }

    def stats(self) -> dict[str, Any]:
        now = _now()
        cutoff = now - self.window_sec
        out = {}
        with self._lock:
            for k, q in self._hits.items():
                while q and q[0] < cutoff:
                    q.popleft()
                if q:
                    out[k] = len(q)
        return {"window_sec": self.window_sec, "active": out}


# 全局单例（开发默认 60 次/分钟）
acq_rate_limiter = TenantRateLimiter(default_limit=60, window_sec=60)


def billing_reconcile(
    db: Any,
    *,
    tenant_id: str = "",
    window_hours: int = 24,
) -> dict[str, Any]:
    """E-5：meter_events vs token_ledger 对账（只读，诚实误差）。"""
    if db is None or not hasattr(db, "execute"):
        return {
            "ok": False,
            "code": "db_unavailable",
            "tenant_id": tenant_id,
            "meter_token_delta": None,
            "ledger_token_delta": None,
            "token_diff": None,
            "plain_summary": "无数据库，无法对账（诚实）。",
            "issues": [],
        }
    try:
        from sqlalchemy import text
        from app.services.acquisition.repo import resolve_tenant_uuid

        tid = resolve_tenant_uuid(db, tenant_id) if tenant_id else None
        since = datetime.now(timezone.utc)
        from datetime import timedelta
        since = datetime.now(timezone.utc) - timedelta(hours=max(1, window_hours))
        meter_sql = """
            select coalesce(sum(coalesce(token_delta,0)), 0)
            from meter_events
            where occurred_at >= :since
        """
        ledger_sql = """
            select coalesce(sum(delta), 0)
            from token_ledger_entries
            where created_at >= :since
        """
        params = {"since": since}
        if tid:
            meter_sql += " and tenant_id = :tid"
            ledger_sql += " and tenant_id = :tid"
            params["tid"] = tid
        meter = int(db.execute(text(meter_sql), params).scalar() or 0)
        ledger = int(db.execute(text(ledger_sql), params).scalar() or 0)
        # meter 侧 token_delta 通常为正消耗；ledger 扣减为负 → 对齐时取绝对差
        token_diff = abs(abs(meter) - abs(ledger)) if meter or ledger else 0
        issues: list[dict[str, Any]] = []
        if meter or ledger:
            if token_diff > max(50, int(abs(meter) * 0.2)):
                issues.append({
                    "code": "token_mismatch",
                    "meter": meter,
                    "ledger": ledger,
                    "diff": token_diff,
                    "message": f"Token 误差 {token_diff}（计量 {meter} / 账本 {ledger}）— 请查汇总任务与双记账开关",
                })
        plain = (
            f"近 {window_hours}h：计量 token={meter}，账本 delta={ledger}，误差 {token_diff}。"
            + ("误差在容忍内。" if not issues else "存在误差，请人工核对。")
        )
        return {
            "ok": True,
            "code": "ok",
            "tenant_id": tenant_id,
            "tenant_uuid": tid,
            "window_hours": window_hours,
            "meter_token_delta": meter,
            "ledger_token_delta": ledger,
            "token_diff": token_diff,
            "issues": issues,
            "plain_summary": plain,
            "hint": "对账只读；不自动改账。双记账开关须互斥启用。",
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "code": "error",
            "tenant_id": tenant_id,
            "error": str(exc)[:200],
            "plain_summary": f"对账失败：{str(exc)[:120]}",
            "issues": [],
        }
