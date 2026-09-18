# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""履约节点进跟单卡 + 到期提醒（P1-2）。

节点：报价 quote → 形式发票 pi → 定金 deposit → 尾款 balance
状态：pending / active / done / overdue / skipped
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from app.services.acquisition.sla import _parse_ts

NODE_ORDER = ("quote", "pi", "deposit", "balance")

NODE_LABELS = {
    "quote": "报价",
    "pi": "形式发票PI",
    "deposit": "定金",
    "balance": "尾款",
}

STATUS_LABELS = {
    "pending": "未开始",
    "active": "进行中",
    "done": "已完成",
    "overdue": "已逾期",
    "skipped": "已跳过",
}

REMINDER_TEXT = {
    "quote": "报价未出：先补齐数量/港口/认证再报",
    "pi": "PI 未出：定金条款写清，新客勿空口承诺",
    "deposit": "定金未到：到账前勿排产",
    "balance": "尾款未清：发货前核对收款节点",
}


def fulfillment_view(card: Any, now: Optional[datetime] = None) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    raw_nodes = list(getattr(card, "fulfillment_nodes", None) or [])
    by_key = {getattr(n, "key", ""): n for n in raw_nodes}
    nodes_out: list[dict[str, Any]] = []
    reminders: list[dict[str, Any]] = []

    # 从 payment 字段诚实推断状态（避免假完成）
    payment = getattr(card, "payment", None)
    pi_no = getattr(payment, "pi_no", "") if payment else ""
    deposit_paid = bool(getattr(payment, "deposit_paid_at", "") if payment else "")
    balance_status = (getattr(payment, "balance_status", "") if payment else "") or ""
    stage = (getattr(card, "stage", "") or "").lower()

    for key in NODE_ORDER:
        n = by_key.get(key)
        label = NODE_LABELS.get(key, key)
        status = getattr(n, "status", "") if n else ""
        due_at = getattr(n, "due_at", "") if n else ""
        done_at = getattr(n, "done_at", "") if n else ""
        note = getattr(n, "note", "") if n else ""
        ref = getattr(n, "ref", "") if n else ""

        # payment 联动（不覆盖人工 done/skipped）
        if status not in ("done", "skipped"):
            if key == "pi" and pi_no:
                status = "done" if not status or status == "pending" else status
                ref = ref or pi_no
            elif key == "deposit" and deposit_paid:
                status = "done" if not status or status in ("pending", "active") else status
            elif key == "balance" and balance_status == "paid":
                status = "done" if not status or status in ("pending", "active") else status
            elif key == "balance" and balance_status == "overdue":
                status = "overdue"
            elif key == "quote" and stage in ("quoted", "sampling", "pi", "negotiating", "won"):
                if status in ("", "pending"):
                    status = "done"

        if not status:
            status = "pending"

        # 到期 → overdue（未完成且 due 过期）
        due_dt = _parse_ts(due_at)
        if status in ("pending", "active") and due_dt is not None and now >= due_dt:
            status = "overdue"

        nodes_out.append({
            "key": key,
            "label": label,
            "status": status,
            "status_label": STATUS_LABELS.get(status, status),
            "due_at": due_at,
            "done_at": done_at,
            "note": note,
            "ref": ref,
        })

        if status == "overdue" or (status in ("pending", "active") and key in ("pi", "deposit") and pi_no is not None):
            if status == "overdue":
                reminders.append({
                    "node": key,
                    "label": label,
                    "status": status,
                    "display": f"{label}已逾期，请优先处理" + (f"（{due_at}）" if due_at else ""),
                    "priority": 0,
                })
            elif status in ("pending", "active") and key in ("deposit", "balance", "pi") and (
                (key == "deposit" and pi_no and not deposit_paid)
                or (key == "balance" and deposit_paid and balance_status not in ("paid",))
                or (key == "pi" and not pi_no and stage not in ("new", "lost"))
            ):
                reminders.append({
                    "node": key,
                    "label": label,
                    "status": status,
                    "display": REMINDER_TEXT.get(key, f"请推进{label}"),
                    "priority": 1,
                })

    reminders.sort(key=lambda r: r.get("priority", 9))
    marks = {"done": "✓", "active": "…", "overdue": "!", "skipped": "-", "pending": "·"}
    summary = " ".join(f"{n['label']}{marks.get(n['status'], '·')}" for n in nodes_out)

    return {
        "nodes": nodes_out,
        "reminders": reminders,
        "summary": summary,
        "hint": "节点状态会随收款/PI 自动联动；到期未完成会进今日待办提醒。",
    }
