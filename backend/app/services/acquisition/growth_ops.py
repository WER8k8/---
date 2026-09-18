# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""内容获客归因（P1-7）+ IP/指纹槽位只读状态（P1-8）。

原则：
    · 归因可查：文章/视频 → 询盘
    · 槽位诚实：无账单数据时 status=unknown，不编造余额
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ContentTouch:
    content_id: str
    content_title: str = ""
    content_type: str = "article"  # article/video/post/landing
    channel: str = ""
    tenant_id: str = ""
    published_at: str = ""
    inquiry_ids: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=_now_iso)


class ContentAttributionStore:
    def __init__(self) -> None:
        self._by_content: dict[str, ContentTouch] = {}
        self._by_inquiry: dict[str, list[str]] = {}  # inquiry_id -> content_ids

    def upsert_content(
        self,
        *,
        content_id: str = "",
        content_title: str = "",
        content_type: str = "article",
        channel: str = "",
        tenant_id: str = "",
        published_at: str = "",
    ) -> ContentTouch:
        cid = content_id or f"cnt-{uuid4().hex[:10]}"
        item = self._by_content.get(cid)
        if item is None:
            item = ContentTouch(content_id=cid, tenant_id=tenant_id)
            self._by_content[cid] = item
        item.content_title = content_title or item.content_title
        item.content_type = content_type or item.content_type
        item.channel = channel or item.channel
        item.tenant_id = tenant_id or item.tenant_id
        item.published_at = published_at or item.published_at
        return item

    def link_inquiry(self, *, content_id: str, inquiry_id: str, tenant_id: str = "") -> dict[str, Any]:
        if not content_id or not inquiry_id:
            return {"linked": False, "reason": "content_id/inquiry_id required"}
        item = self.upsert_content(content_id=content_id, tenant_id=tenant_id)
        if inquiry_id not in item.inquiry_ids:
            item.inquiry_ids.append(inquiry_id)
        ids = self._by_inquiry.setdefault(inquiry_id, [])
        if item.content_id not in ids:
            ids.append(item.content_id)
        return {
            "linked": True,
            "content_id": item.content_id,
            "inquiry_id": inquiry_id,
            "inquiry_count": len(item.inquiry_ids),
        }

    def list_contents(self, tenant_id: str = "") -> list[dict[str, Any]]:
        out = []
        for item in self._by_content.values():
            if tenant_id and item.tenant_id and item.tenant_id != tenant_id:
                continue
            out.append({
                "content_id": item.content_id,
                "content_title": item.content_title,
                "content_type": item.content_type,
                "channel": item.channel,
                "published_at": item.published_at,
                "inquiry_count": len(item.inquiry_ids),
                "inquiry_ids": list(item.inquiry_ids),
                "tenant_id": item.tenant_id,
            })
        out.sort(key=lambda x: x["inquiry_count"], reverse=True)
        return out

    def inquiry_sources(self, inquiry_id: str) -> list[str]:
        return list(self._by_inquiry.get(inquiry_id, []))

    def report(self, tenant_id: str = "") -> dict[str, Any]:
        items = self.list_contents(tenant_id=tenant_id)
        total_inq = sum(i["inquiry_count"] for i in items)
        plain = (
            f"共 {len(items)} 条内容，带来 {total_inq} 条询盘关联。"
            if items
            else "暂无内容归因数据。发布内容时登记 content_id，询盘进线可挂来源。"
        )
        return {
            "tenant_id": tenant_id,
            "content_count": len(items),
            "total_attributed_inquiries": total_inq,
            "items": items,
            "plain_summary": plain,
            "hint": "归因按「询盘挂 content_id」统计；未挂来源的内容记 0，不编造转化。",
        }


@dataclass
class IpSlot:
    slot_id: str = field(default_factory=lambda: f"ip-{uuid4().hex[:8]}")
    label: str = ""
    region: str = ""
    status: str = "unknown"  # active/idle/blocked/unknown
    fingerprint_profile: str = ""
    bound_account: str = ""
    plan: str = ""
    note: str = ""


class IpSlotCatalog:
    """IP/指纹槽位只读目录（P1-8）。无账本时诚实 unknown。"""

    def __init__(self) -> None:
        self._items: list[IpSlot] = [
            IpSlot(label="静态IP-中东-01", region="ME", status="unknown", note="待接计费账本后显示真实状态"),
            IpSlot(label="静态IP-东南亚-01", region="SEA", status="unknown", note="待接计费账本后显示真实状态"),
            IpSlot(label="指纹槽位-浏览器-01", region="", status="unknown", fingerprint_profile="chrome-stable", note="Browser Runtime 绑定后激活"),
        ]

    def list_view(self, tenant_id: str = "") -> dict[str, Any]:
        items = [
            {
                "slot_id": s.slot_id,
                "label": s.label,
                "region": s.region,
                "status": s.status,
                "status_label": {
                    "active": "使用中",
                    "idle": "空闲",
                    "blocked": "不可用",
                    "unknown": "未知（未接账本）",
                }.get(s.status, s.status),
                "fingerprint_profile": s.fingerprint_profile,
                "bound_account": s.bound_account,
                "plan": s.plan,
                "note": s.note,
            }
            for s in self._items
        ]
        known = sum(1 for i in items if i["status"] != "unknown")
        return {
            "tenant_id": tenant_id,
            "slots": items,
            "total": len(items),
            "known_count": known,
            "billing_ready": known > 0,
            "hint": "轨道三（IP/指纹）先只读；未接入计费时不显示假余额、不开放购买。",
            "plain_summary": (
                f"槽位 {len(items)} 个，其中 {known} 个状态已知。"
                if known
                else f"槽位 {len(items)} 个，状态待计费账本接入后展示。"
            ),
        }


content_attr_store = ContentAttributionStore()
ip_slot_catalog = IpSlotCatalog()
