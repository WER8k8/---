# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""P3-5 退订 / 抑制名单 — 同邮箱不重复骚扰。

红线：
    · 抑制中的联系人禁止再进个性化外发队列
    · 抑制只增不减（人工解除必须显式 confirm）
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
        key = (tenant_id or "demo", email_n)
        if key in self._by_key:
            e = self._by_key[key]
            return {
                "ok": True,
                "code": "already_suppressed",
                "message": f"{email_n} 已在抑制名单（{e.reason}）",
                "entry": e.__dict__,
            }
        e = SuppressionEntry(
            email=email_n,
            tenant_id=tenant_id or "demo",
            reason=reason or "unsubscribe",
            source=source,
            created_by=created_by,
        )
        self._by_key[key] = e
        return {"ok": True, "code": "suppressed", "message": f"{email_n} 已加入抑制名单", "entry": e.__dict__}

    def remove(
        self,
        *,
        email: str,
        tenant_id: str = "demo",
        confirm: bool = False,
        note: str = "",
    ) -> dict[str, Any]:
        email_n = self._norm(email)
        key = (tenant_id or "demo", email_n)
        if key not in self._by_key:
            return {"ok": False, "code": "not_found", "message": "不在抑制名单"}
        if not confirm:
            return {
                "ok": False,
                "code": "need_confirm",
                "message": "解除抑制必须 confirm=true（避免误放骚扰）",
            }
        old = self._by_key.pop(key)
        return {
            "ok": True,
            "code": "released",
            "message": f"{email_n} 已解除抑制",
            "previous": old.__dict__,
            "note": note,
        }

    def is_suppressed(self, email: str, tenant_id: str = "demo") -> bool:
        return (tenant_id or "demo", self._norm(email)) in self._by_key

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
        if not email_n:
            return {
                "allowed": False,
                "code": "missing_email",
                "message": "无邮箱，无法外发",
                "channel": channel,
                "mode": mode,
            }
        if self.is_suppressed(email_n, tenant_id):
            e = self._by_key[(tenant_id or "demo", email_n)]
            return {
                "allowed": False,
                "code": "suppressed",
                "message": f"{email_n} 已退订/抑制（{e.reason}），禁止再发",
                "reason": e.reason,
                "since": e.created_at,
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
        out = []
        for (tid, email), e in self._by_key.items():
            if tenant_id and tid != tenant_id:
                continue
            out.append(e.__dict__)
        out.sort(key=lambda x: x.get("created_at") or "", reverse=True)
        return out

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


# 全局单例（生产可换 DB 表）
suppression_store = SuppressionStore()
