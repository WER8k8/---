# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""P3-5 退订 / 抑制名单 — 同邮箱不重复骚扰（P1-9：已落库持久化）。

红线：
    · 抑制中的联系人禁止再进个性化外发队列
    · 抑制只增不减（人工解除必须显式 confirm）

落库改造（P1-9）：
    原实现仅存进程内 dict，重启即丢 → 用户退订后仍可能被再次发送（合规事故）。
    现改为 **PG 主存 + 内存缓存**：写先落库，读优先库、miss 回源并回填缓存；
    DB 不可用时降级为纯内存（保持服务可用，行为等价旧实现）。
    对外方法签名与返回结构 **完全不变**，既有 4 处调用方零改动：
      · api/v1/routes/acquisition.py（4 个端点）
      · services/hermes/biz_bot_actions.py
      · services/hermes/executors/outreach_loop_executor.py
      · services/hermes/executors/commerce_ops_executor.py
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class SuppressionEntry:
    email: str
    tenant_id: str = "demo"
    reason: str = ""  # unsubscribe/complaint/manual/bounce_hard
    source: str = ""
    created_at: str = field(default_factory=_now)
    created_by: str = "system"


class SuppressionStore:
    def __init__(self) -> None:
        self._by_key: dict[tuple[str, str], SuppressionEntry] = {}

    @staticmethod
    def _norm(email: str) -> str:
        return (email or "").strip().lower()

    @staticmethod
    def _pg():
        """惰性取 PG 持久层；不可用返回 None（降级内存）。"""
        try:
            from app.services.acquisition import suppression_pg

            return suppression_pg
        except Exception:  # noqa: BLE001
            return None

    def add(
        self,
        *,
        email: str,
        tenant_id: str = "demo",
        reason: str = "unsubscribe",
        source: str = "",
        created_by: str = "system",
    ) -> dict[str, Any]:
        email_n = self._norm(email)
        if not email_n or "@" not in email_n:
            return {"ok": False, "code": "invalid_email", "message": "邮箱格式不合法"}
        tid = tenant_id or "demo"
        key = (tid, email_n)

        # 已在（内存或库）→ 幂等返回，不重复写
        cached = self._by_key.get(key)
        pg = self._pg()
        existing = cached.__dict__ if cached else None
        if existing is None and pg is not None:
            existing = pg.get_entry(tenant_id=tid, email=email_n)
        if existing:
            return {
                "ok": True,
                "code": "already_suppressed",
                "message": f"{email_n} 已在抑制名单（{existing.get('reason')}）",
                "entry": existing,
            }

        if pg is not None:
            if pg.save_entry(
                tenant_id=tid,
                email=email_n,
                reason=reason or "unsubscribe",
                source=source,
                created_by=created_by,
            ):
                saved = pg.get_entry(tenant_id=tid, email=email_n) or {}
                e = SuppressionEntry(
                    email=email_n,
                    tenant_id=tid,
                    reason=saved.get("reason") or reason or "unsubscribe",
                    source=saved.get("source") or source,
                    created_at=saved.get("created_at") or _now(),
                    created_by=saved.get("created_by") or created_by,
                )
                self._by_key[key] = e
                return {
                    "ok": True,
                    "code": "suppressed",
                    "message": f"{email_n} 已加入抑制名单（已落库）",
                    "entry": e.__dict__,
                }
            # 落库失败 → 降级内存，仍保证本次会话内生效

        e = SuppressionEntry(
            email=email_n,
            tenant_id=tid,
            reason=reason or "unsubscribe",
            source=source,
            created_by=created_by,
        )
        self._by_key[key] = e
        return {
            "ok": True,
            "code": "suppressed",
            "message": f"{email_n} 已加入抑制名单（内存态，落库不可用）",
            "entry": e.__dict__,
        }

    def remove(
        self,
        *,
        email: str,
        tenant_id: str = "demo",
        confirm: bool = False,
        note: str = "",
    ) -> dict[str, Any]:
        email_n = self._norm(email)
        tid = tenant_id or "demo"
        key = (tid, email_n)

        cached = self._by_key.get(key)
        pg = self._pg()
        existing = cached.__dict__ if cached else None
        if existing is None and pg is not None:
            existing = pg.get_entry(tenant_id=tid, email=email_n)
        if not existing:
            return {"ok": False, "code": "not_found", "message": "不在抑制名单"}
        if not confirm:
            return {
                "ok": False,
                "code": "need_confirm",
                "message": "解除抑制必须 confirm=true（避免误放骚扰）",
            }

        persisted = False
        if pg is not None:
            persisted = pg.delete_entry(tenant_id=tid, email=email_n)
        self._by_key.pop(key, None)
        return {
            "ok": True,
            "code": "released",
            "message": f"{email_n} 已解除抑制",
            "previous": existing,
            "note": note,
            "persisted": persisted,
        }

    def is_suppressed(self, email: str, tenant_id: str = "demo") -> bool:
        tid = tenant_id or "demo"
        email_n = self._norm(email)
        if (tid, email_n) in self._by_key:
            return True
        pg = self._pg()
        if pg is None:
            return False
        try:
            return pg.get_entry(tenant_id=tid, email=email_n) is not None
        except Exception:  # noqa: BLE001
            return False

    def check_outreach(
        self,
        *,
        email: str,
        tenant_id: str = "demo",
        channel: str = "email",
        mode: str = "personalized",
    ) -> dict[str, Any]:
        """外发前闸门。抑制中 → allowed=False。"""
        email_n = self._norm(email)
        tid = tenant_id or "demo"
        if not email_n:
            return {
                "allowed": False,
                "code": "missing_email",
                "message": "无邮箱，无法外发",
                "channel": channel,
                "mode": mode,
            }
        if self.is_suppressed(email_n, tid):
            entry = self._by_key.get((tid, email_n))
            info = entry.__dict__ if entry else None
            if info is None:
                pg = self._pg()
                if pg is not None:
                    info = pg.get_entry(tenant_id=tid, email=email_n) or {}
            reason = (info or {}).get("reason") or ""
            since = (info or {}).get("created_at") or ""
            return {
                "allowed": False,
                "code": "suppressed",
                "message": f"{email_n} 已退订/抑制（{reason}），禁止再发",
                "reason": reason,
                "since": since,
                "channel": channel,
                "mode": mode,
            }
        return {
            "allowed": True,
            "code": "ok",
            "message": "未在抑制名单",
            "channel": channel,
            "mode": mode,
        }

    def list_all(self, tenant_id: str = "") -> list[dict[str, Any]]:
        """PG 为准，内存补充（DB 不可用则纯内存）。"""
        items: list[dict[str, Any]] = []
        seen: set[tuple[str, str]] = set()
        pg = self._pg()
        if pg is not None:
            for d in pg.list_entries(tenant_id=tenant_id):
                seen.add((str(d.get("tenant_id") or ""), str(d.get("email") or "")))
                items.append(d)
        for (tid, email), e in self._by_key.items():
            if tenant_id and tid != tenant_id:
                continue
            if (tid, email) in seen:
                continue
            items.append(e.__dict__)
        items.sort(key=lambda x: x.get("created_at") or "", reverse=True)
        return items

    def report(self, tenant_id: str = "demo") -> dict[str, Any]:
        items = self.list_all(tenant_id=tenant_id)
        by_reason: dict[str, int] = {}
        for i in items:
            r = i.get("reason") or "unknown"
            by_reason[r] = by_reason.get(r, 0) + 1
        plain = (
            f"抑制名单 {len(items)} 人。"
            + ("；".join(f"{k} {v}" for k, v in by_reason.items()) if by_reason else "")
        ) if items else "抑制名单为空。"
        return {
            "tenant_id": tenant_id,
            "total": len(items),
            "by_reason": by_reason,
            "items": items,
            "plain_summary": plain,
            "hint": "退订/投诉后禁止再发；解除需人工 confirm。",
        }


# 全局单例（P1-9：底层已落库，进程重启不再丢失）
suppression_store = SuppressionStore()
