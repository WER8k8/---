# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""P1-6 报价未回访唤醒：报价发出后石沉大海，系统主动把卡片捞回来。

为什么需要：
    外贸 B2B 报价后最常见的死法是「发完就没下文」——销售人员忙起来就忘了追，
    报价悄无声息过期。既有 quote_guard.quote_validity_view 能**判定**报价是否过期，
    但只是被动视图（前端打开才看到），没人主动巡检 → P1-6 缺口。

规则：
    命中任一条件即唤醒（且卡片未成交/未流失）：
      A. 报价后 ≥ idle_days 天仍无任何跟进记录（last_touch_at 为空或早于报价日）
      B. 报价已过有效期（quote_validity_view.status == "expired"）→ 高优先级重报
    动作：建 SalesTask（指派给卡片负责人）+ 飞书通知 + 按 (租户,卡片,日期) 幂等。

与 P1-7 的关系：P1-7 管「排期逾期」，本任务管「压根没排期/报价过期」，互补不重叠。
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone

import httpx
from celery import shared_task
from sqlalchemy import text

logger = logging.getLogger(__name__)

_WAKE_DDL = """
CREATE TABLE IF NOT EXISTS acquisition_quote_wake (
    tenant_id TEXT NOT NULL,
    inquiry_id TEXT NOT NULL,
    alert_date DATE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (tenant_id, inquiry_id, alert_date)
);
"""

_CLOSED_STAGES = {"won", "lost"}


def _send_feishu(title: str, content: str) -> bool:
    from app.core.config import settings

    webhook = (settings.FEISHU_WEBHOOK_URL or "").strip()
    if not webhook:
        return False
    payload = {
        "msg_type": "interactive",
        "card": {
            "header": {"title": {"tag": "plain_text", "content": title}, "template": "orange"},
            "elements": [{"tag": "div", "text": {"tag": "lark_md", "content": content}}],
        },
    }
    try:
        with httpx.Client(timeout=10) as client:
            resp = client.post(webhook, json=payload)
            return resp.status_code < 300
    except Exception as exc:  # noqa: BLE001
        logger.warning("飞书报价唤醒通知失败: %s", exc)
        return False


def _iter_card_payloads(db):
    """全量读跟单卡 payload（与 P1-7 同数据源；表不存在则优雅降级为空）。"""
    try:
        rows = db.execute(
            text("SELECT inquiry_id, tenant_id, payload FROM acquisition_ops_cards")
        ).fetchall()
    except Exception as exc:  # noqa: BLE001
        logger.info("acquisition_ops_cards 不可读: %s", exc)
        return
    for inquiry_id, tenant_id, payload in rows:
        data = payload
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except (json.JSONDecodeError, TypeError):
                continue
        if not isinstance(data, dict):
            continue
        yield str(inquiry_id or ""), str(tenant_id or ""), data


def _already_woken(db, tenant_id: str, inquiry_id: str, day) -> bool:
    try:
        return (
            db.execute(
                text(
                    "SELECT 1 FROM acquisition_quote_wake "
                    "WHERE tenant_id = :t AND inquiry_id = :i AND alert_date = :d"
                ),
                {"t": tenant_id, "i": inquiry_id, "d": day},
            ).first()
            is not None
        )
    except Exception:  # noqa: BLE001
        return False


@shared_task(name="app.tasks.quote_wake_tasks.quote_followup_wake_daily", ignore_result=False)
def quote_followup_wake_daily(idle_days: int = 3, dry_run: bool = False) -> dict:
    """每日报价未回访唤醒（P1-6）。"""
    from app.core.database import SessionLocal
    from app.models.sales_task import SalesTask
    from app.services.acquisition.quote_guard import quote_validity_view
    from app.services.acquisition.sla import _parse_ts

    now = datetime.now(timezone.utc)
    today = now.date()
    summary: dict = {
        "scanned": 0,
        "wake": 0,
        "idle_wake": 0,
        "expired_wake": 0,
        "tasks_created": 0,
        "notified": 0,
        "skipped": 0,
        "errors": 0,
        "items": [],
        "error": False,
    }

    def _handle(db, inquiry_id, tenant_id, data):
        quote_at = str(data.get("quote_at") or "")
        stage = str(data.get("stage") or "").lower()
        if not quote_at or stage in _CLOSED_STAGES:
            return
        started = _parse_ts(quote_at)
        if started is None:
            return
        touch = _parse_ts(str(data.get("last_touch_at") or ""))
        idle = (touch is None) or (touch <= started)
        since_days = (now - started).days
        validity = quote_validity_view(
            quote_at=quote_at,
            valid_days=data.get("quote_valid_days") or 14,
            fx_locked=bool(data.get("quote_fx_locked")),
            now=now,
        )
        expired = bool(validity.get("expired"))
        if not (idle and since_days >= idle_days) and not expired:
            return
        summary["wake"] += 1
        if expired:
            summary["expired_wake"] += 1
        else:
            summary["idle_wake"] += 1
        if not tenant_id or not inquiry_id:
            return
        if _already_woken(db, tenant_id, inquiry_id, today):
            summary["skipped"] += 1
            return

        buyer = str(data.get("buyer_display") or inquiry_id)
        reason = (
            f"报价已于 {validity.get('valid_until', '')[:10]} 过期，需重新核价"
            if expired
            else f"报价已 {since_days} 天，报价后无任何跟进记录"
        )
        if dry_run:
            summary["items"].append(
                {"tenant_id": tenant_id, "inquiry_id": inquiry_id, "buyer": buyer, "reason": reason}
            )
            return

        feishu_ok = _send_feishu(
            f"报价待唤醒 · {buyer}",
            f"**客户**：{buyer}\n**原因**：{reason}\n**下一步**：{validity.get('next_action') or '联系客户确认意向'}\n请尽快跟进。",
        )
        task = SalesTask(
            title=f"报价跟进唤醒 · {buyer}",
            description=f"{reason}；{validity.get('next_action') or ''}；询盘ID：{inquiry_id}",
            task_type="followup",
            priority="high" if expired else "normal",
            status="open",
            tenant_id=tenant_id,
            assigned_to=str(data.get("owner_user_id") or "") or None,
            due_at=now + timedelta(days=1),
            created_by="system:quote-wake",
        )
        db.add(task)
        db.execute(
            text(
                "INSERT INTO acquisition_quote_wake (tenant_id, inquiry_id, alert_date) "
                "VALUES (:t, :i, :d) ON CONFLICT DO NOTHING"
            ),
            {"t": tenant_id, "i": inquiry_id, "d": today},
        )
        db.commit()
        summary["tasks_created"] += 1
        summary["notified"] += 1 if feishu_ok else 0
        summary["items"].append(
            {"tenant_id": tenant_id, "inquiry_id": inquiry_id, "buyer": buyer, "reason": reason}
        )

    try:
        with SessionLocal() as db:
            db.execute(text(_WAKE_DDL))
            db.commit()
            for inquiry_id, tenant_id, data in _iter_card_payloads(db):
                summary["scanned"] += 1
                try:
                    _handle(db, inquiry_id, tenant_id, data)
                except Exception as exc:  # noqa: BLE001
                    # 单卡失败不拖垮整轮（PG 报错后事务 aborted，必须回滚）
                    summary["errors"] += 1
                    logger.warning("报价唤醒单卡失败 %s/%s: %s", tenant_id, inquiry_id, exc)
                    try:
                        db.rollback()
                    except Exception:
                        pass
    except Exception:  # noqa: BLE001
        logger.exception("quote_followup_wake_daily failed")
        summary["error"] = True
    return summary
