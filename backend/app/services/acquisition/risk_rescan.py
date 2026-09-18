# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""P3-4 制裁/风险名单重扫提醒。

原则：
    · 有 last_scan_at 且超期 → 待重扫
    · 无名单源/未扫描 → 诚实 unknown，不假装已合规
    · 可标记「已重扫」；不自动调外部名单 API（未接入时）
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from app.services.acquisition.sla import _parse_ts


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


DEFAULT_RESCAN_DAYS = 90


@dataclass
class RiskScanRecord:
    inquiry_id: str
    buyer_display: str = ""
    country: str = ""
    risk_flags: list[str] = field(default_factory=list)
    last_scan_at: str = ""
    last_scan_result: str = "unknown"  # clear/watch/blocked/unknown
    last_scan_source: str = ""  # manual/playbook/external_list
    rescan_count: int = 0
    note: str = ""
    updated_at: str = field(default_factory=_now)


class RiskRescanStore:
    def __init__(self) -> None:
        self._by_inquiry: dict[str, RiskScanRecord] = {}

    def upsert_from_card(self, card: Any) -> RiskScanRecord:
        iid = getattr(card, "inquiry_id", "") or ""
        if not iid:
            return RiskScanRecord(inquiry_id="")
        rec = self._by_inquiry.get(iid)
        if rec is None:
            rec = RiskScanRecord(inquiry_id=iid)
            self._by_inquiry[iid] = rec
        rec.buyer_display = getattr(card, "buyer_display", "") or rec.buyer_display
        rec.risk_flags = list(getattr(card, "risk_flags", None) or rec.risk_flags or [])
        rec.updated_at = _now()
        return rec

    def mark_scanned(
        self,
        inquiry_id: str,
        *,
        result: str = "unknown",
        source: str = "manual",
        note: str = "",
        country: str = "",
        risk_flags: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        rec = self._by_inquiry.get(inquiry_id)
        if rec is None:
            rec = RiskScanRecord(inquiry_id=inquiry_id)
            self._by_inquiry[inquiry_id] = rec
        rec.last_scan_at = _now()
        rec.last_scan_result = result if result in ("clear", "watch", "blocked", "unknown") else "unknown"
        rec.last_scan_source = source or "manual"
        rec.rescan_count += 1
        rec.note = note or rec.note
        if country:
            rec.country = country
        if risk_flags is not None:
            rec.risk_flags = list(risk_flags)
        rec.updated_at = _now()
        return {
            "ok": True,
            "code": "scanned",
            "message": f"{inquiry_id} 已记录重扫（{rec.last_scan_result}）",
            "record": rec.__dict__,
        }

    def evaluate_one(self, rec: RiskScanRecord, *, rescan_days: int = DEFAULT_RESCAN_DAYS, now: Optional[datetime] = None) -> dict[str, Any]:
        now = now or datetime.now(timezone.utc)
        last = _parse_ts(rec.last_scan_at) if rec.last_scan_at else None
        if last is None:
            return {
                "inquiry_id": rec.inquiry_id,
                "buyer_display": rec.buyer_display,
                "country": rec.country,
                "status": "never_scanned",
                "status_label": "从未扫描",
                "due": True,
                "days_overdue": None,
                "last_scan_at": "",
                "last_scan_result": "unknown",
                "plain": f"{rec.buyer_display or rec.inquiry_id}：未做过名单扫描 — 建议至少人工核对一次。",
                "next_action": "查目的国/公司是否在限制名单；结果点「已重扫」。",
            }
        due_dt = last
        # 超期
        from datetime import timedelta
        cutoff = last + timedelta(days=int(rescan_days))
        if now >= cutoff:
            days_over = int((now - cutoff).days)
            return {
                "inquiry_id": rec.inquiry_id,
                "buyer_display": rec.buyer_display,
                "country": rec.country,
                "status": "overdue",
                "status_label": "待重扫",
                "due": True,
                "days_overdue": days_over,
                "last_scan_at": rec.last_scan_at,
                "last_scan_result": rec.last_scan_result,
                "plain": f"{rec.buyer_display or rec.inquiry_id}：上次扫描已超过 {rescan_days} 天（逾期约 {days_over} 天），请重扫。",
                "next_action": "更新名单扫描结果；高风险勿自动 PI。",
            }
        days_left = int((cutoff - now).days)
        return {
            "inquiry_id": rec.inquiry_id,
            "buyer_display": rec.buyer_display,
            "country": rec.country,
            "status": "ok",
            "status_label": "扫描有效",
            "due": False,
            "days_overdue": None,
            "days_left": days_left,
            "last_scan_at": rec.last_scan_at,
            "last_scan_result": rec.last_scan_result,
            "plain": f"{rec.buyer_display or rec.inquiry_id}：扫描有效，约 {days_left} 天后需重扫。",
            "next_action": "到期前复扫；风险标记变化立即复扫。",
        }

    def report(
        self,
        *,
        ops_store: Any = None,
        tenant_id: str = "",
        rescan_days: int = DEFAULT_RESCAN_DAYS,
        external_list_configured: bool = False,
    ) -> dict[str, Any]:
        # 从跟单卡同步
        if ops_store is not None:
            try:
                for card in getattr(ops_store, "_by_inquiry", {}).values():
                    if tenant_id and getattr(card, "tenant_id", "") not in ("", tenant_id):
                        continue
                    if getattr(card, "stage", "") == "lost":
                        continue
                    self.upsert_from_card(card)
            except Exception:
                pass
        items = [self.evaluate_one(r, rescan_days=rescan_days) for r in self._by_inquiry.values()]
        # 未接外部名单源时统一提示
        due_list = [i for i in items if i.get("due")]
        never = sum(1 for i in items if i.get("status") == "never_scanned")
        overdue = sum(1 for i in items if i.get("status") == "overdue")
        if not external_list_configured:
            source_plain = "外部制裁名单源未接入 — 结果以人工/Playbook 核对为准，系统不编造「已合规」。"
        else:
            source_plain = "已配置外部名单源（以引擎返回为准）。"
        plain = (
            f"跟踪 {len(items)} 个在跟客户：待重扫 {len(due_list)}（从未扫 {never} / 逾期 {overdue}）。{source_plain}"
        )
        return {
            "tenant_id": tenant_id,
            "rescan_days": rescan_days,
            "total_tracked": len(items),
            "due_count": len(due_list),
            "never_scanned": never,
            "overdue": overdue,
            "external_list_configured": external_list_configured,
            "source_plain": source_plain,
            "items": sorted(items, key=lambda x: (not x.get("due"), x.get("days_overdue") is None, -(x.get("days_overdue") or 0))),
            "plain_summary": plain,
            "hint": "重扫只更新记录；未接名单 API 时不自动判定 clear/blocked。",
        }


risk_rescan_store = RiskRescanStore()
