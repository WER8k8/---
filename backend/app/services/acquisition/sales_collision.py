# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""P2-7 销售团队撞单规则 — 同一询盘归属与交接审计。

规则（傻子都行）：
    1. 空卡可认领：claim 成功即 owner
    2. 已有人跟：必须 confirm=true 才强制交接，并写 handoff_history
    3. 冲突一律告警 + 留痕，禁止静默抢走
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def claim_inquiry(
    ops_store: Any,
    *,
    inquiry_id: str,
    user_id: str,
    tenant_id: str = "",
    confirm_force: bool = False,
    note: str = "",
) -> dict[str, Any]:
    """认领/交接询盘。返回撞单审计结果。"""
    if not (inquiry_id or "").strip() or not (user_id or "").strip():
        return {
            "ok": False,
            "code": "invalid_args",
            "message": "询盘编号与业务员不能为空",
        }
    card = ops_store.get_by_inquiry(inquiry_id)
    if card is None:
        card = ops_store.materialize(
            tenant_id=tenant_id or "demo",
            inquiry_id=inquiry_id,
            owner_user_id=user_id,
        )
        return {
            "ok": True,
            "code": "claimed_new",
            "message": f"新建跟单卡并认领给 {user_id}",
            "owner_user_id": user_id,
            "card": card.to_dict(),
            "audit": [{
                "type": "claim_new",
                "from": "",
                "to": user_id,
                "at": _now(),
                "note": note or "新建认领",
            }],
        }

    current = (card.owner_user_id or "").strip()
    if not current:
        card = ops_store.set_owner(inquiry_id, user_id, note=note or "认领无主询盘")
        return {
            "ok": True,
            "code": "claimed_empty",
            "message": f"询盘原无负责人，已认领给 {user_id}",
            "owner_user_id": user_id,
            "card": card.to_dict(),
            "audit": card.handoff_history[-1:],
        }

    if current == user_id:
        return {
            "ok": True,
            "code": "already_owner",
            "message": "你已经是该询盘负责人",
            "owner_user_id": current,
            "card": card.to_dict(),
            "audit": [],
        }

    # 撞单
    if not confirm_force:
        return {
            "ok": False,
            "code": "collision",
            "message": f"该询盘已由 {current} 跟进。确认交接请带 confirm=true（会写审计）。",
            "owner_user_id": current,
            "attempted_by": user_id,
            "card": card.to_dict(),
            "hint": "禁止静默抢客；确认后写入交接历史。",
        }

    card = ops_store.set_owner(inquiry_id, user_id, note=note or f"强制交接 from {current}")
    audit = card.handoff_history[-1:] if card.handoff_history else [{
        "from": current,
        "to": user_id,
        "at": _now(),
        "note": note or "force handoff",
    }]
    return {
        "ok": True,
        "code": "handed_off",
        "message": f"已从 {current} 交接给 {user_id}（已留痕）",
        "owner_user_id": user_id,
        "card": card.to_dict(),
        "audit": audit,
    }


def collision_report(ops_store: Any, tenant_id: str = "") -> dict[str, Any]:
    """团队撞单/交接汇总（只读）。"""
    items = []
    for card in getattr(ops_store, "_by_inquiry", {}).values():
        if tenant_id and getattr(card, "tenant_id", "") not in ("", tenant_id):
            continue
        history = list(getattr(card, "handoff_history", None) or [])
        if not history:
            continue
        items.append({
            "inquiry_id": card.inquiry_id,
            "owner_user_id": card.owner_user_id,
            "handoff_count": len(history),
            "last_handoff": history[-1] if history else None,
            "buyer_display": getattr(card, "buyer_display", "") or "",
        })
    plain = f"发生过交接的询盘 {len(items)} 条。" if items else "暂无交接/撞单记录。"
    return {
        "tenant_id": tenant_id,
        "items": items,
        "total": len(items),
        "plain_summary": plain,
        "rule": "无主可直接认领；有主须 confirm 交接并写审计，禁止静默抢客。",
    }
