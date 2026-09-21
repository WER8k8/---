# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""P1-7 跟进 SLA 超时主动告警：每日扫描跟单卡，对逾期未跟进的卡片自动建任务 + 通知。

背景（真实取证）：
    · acquisition/services/sla.py 的 evaluate_sla/card_sla 已实现，且被调用 4 处
      （routes/acquisition.py:41/87/100/1603、acquisition/__init__.py:728）
    · 但这 4 处全是「请求时才算」的**被动计算**——没人主动巡检，逾期卡片只会静静躺着。
    · 本任务把被动计算升级为主动告警闭环：扫 PG 全量跟单卡 → overdue → 建 SalesTask
      + 飞书/邮件通知 → 按 (租户, 卡片, 日期) 幂等去重，避免每日重复轰炸。

幂等：独立表 acquisition_sla_alerts，主键 (tenant_id, inquiry_id, alert_date)，
      同一张卡同一天只告警一次；跨天仍逾期则次日再提醒（持续逾期不会被静音）。
"""
from __future__ import annotations

import json
import logging
from datetime import date, datetime, timedelta, timezone

import httpx
from celery import shared_task
from sqlalchemy import text

logger = logging.getLogger(__name__)

_ALERT_DDL = """
CREATE TABLE IF NOT EXISTS acquisition_sla_alerts (
    tenant_id TEXT NOT NULL,
    inquiry_id TEXT NOT NULL,
    alert_date DATE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (tenant_id, inquiry_id, alert_date)
);
"""


def _send_feishu(title: str, content: str) -> bool:
    """飞书通知（橙模板，匹配 SLA 逾期语义）。"""
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
        logger.warning("飞书 SLA 告警通知失败: %s", exc)
        return False


def _send_email(to_email: str, buyer: str, detail: str) -> bool:
    """邮件通知负责人/客户成功。"""
    from app.core.config import settings

    if not to_email or not settings.SMTP_SERVER:
        return False
    try:
        from app.services.email_service import EmailService

        svc = EmailService()
        subject = f"【优丁 SaaS】跟进 SLA 逾期 · {buyer}"
        html = (
            f"<p>您好，</p>"
            f"<p>客户 <strong>{buyer}</strong> 的跟进已逾期：</p>"
            f"<p>{detail}</p>"
            f"<p>请登录处理：<a href=\"{settings.FRONTEND_URL}/client/inquiries\">立即跟进</a></p>"
            f"<p>— 优丁建材 SaaS</p>"
        )
        return svc._send_email(to_email, subject, html)
    except Exception as exc:  # noqa: BLE001
        logger.warning("邮件 SLA 告警通知失败: %s", exc)
        return False


def _iter_card_payloads(db):
    """从 PG 全量读跟单卡 payload（不依赖内存单例，避免进程重启后状态丢失）。

    表不存在（尚未产生跟单卡）时优雅降级为空迭代，不抛异常。
    """
    try:
        rows = db.execute(
            text("SELECT inquiry_id, tenant_id, payload FROM acquisition_ops_cards")
        ).fetchall()
    except Exception as exc:  # noqa: BLE001
        logger.info("acquisition_ops_cards 不可读（可能尚未建表）: %s", exc)
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


def _already_alerted(db, tenant_id: str, inquiry_id: str, day: date) -> bool:
    try:
        row = db.execute(
            text(
                "SELECT 1 FROM acquisition_sla_alerts "
                "WHERE tenant_id = :t AND inquiry_id = :i AND alert_date = :d"
            ),
            {"t": tenant_id, "i": inquiry_id, "d": day},
        ).first()
        return row is not None
    except Exception:  # noqa: BLE001
        return False


def _mark_alerted(db, tenant_id: str, inquiry_id: str, day: date) -> None:
    db.execute(
        text(
            "INSERT INTO acquisition_sla_alerts (tenant_id, inquiry_id, alert_date) "
            "VALUES (:t, :i, :d) ON CONFLICT DO NOTHING"
        ),
        {"t": tenant_id, "i": inquiry_id, "d": day},
    )


def _fetch_tenant(db, tenant_id: str):
    """查租户；tenant_id 非合法 UUID（如历史脏数据 "demo"）会触发 PG DataError，
    这里吞掉并按「无租户」处理——不能让一张脏卡中断整轮巡检。"""
    try:
        from app.models.tenant import Tenant

        return db.query(Tenant).filter(Tenant.id == tenant_id).first()
    except Exception:  # noqa: BLE001
        try:
            db.rollback()
        except Exception:
            pass
        return None


def _handle_card(db, summary, inquiry_id, tenant_id, data, now, today, dry_run) -> None:
    """处理单张逾期卡：建任务 + 通知 + 幂等标记。"""
    from app.models.sales_task import SalesTask
    from app.services.acquisition.sla import evaluate_sla

    sla = evaluate_sla(
        stage=str(data.get("stage") or ""),
        next_action=str(data.get("next_action") or ""),
        next_action_at=str(data.get("next_action_at") or ""),
        last_touch_at=str(data.get("last_touch_at") or ""),
        now=now,
    )
    if sla.get("sla") != "overdue":
        return
    summary["overdue"] += 1
    if not tenant_id or not inquiry_id:
        return
    if _already_alerted(db, tenant_id, inquiry_id, today):
        summary["skipped"] += 1
        return

    buyer = str(data.get("buyer_display") or inquiry_id)
    detail = sla.get("display") or "跟进已逾期"
    if dry_run:
        summary["items"].append(
            {
                "tenant_id": tenant_id,
                "inquiry_id": inquiry_id,
                "buyer": buyer,
                "dry_run": True,
            }
        )
        summary["alerted"] += 1
        return

    tenant = _fetch_tenant(db, tenant_id)
    feishu_ok = _send_feishu(
        f"SLA 逾期 · {buyer}",
        f"**客户**：{buyer}\n**状态**：{detail}\n"
        f"**下一步**：{data.get('next_action') or '（未填写）'}\n请立即跟进。",
    )
    email_ok = False
    if tenant is not None:
        email_ok = _send_email(getattr(tenant, "contact_email", "") or "", buyer, detail)
    owner = str(data.get("owner_user_id") or "") or None
    task = SalesTask(
        title=f"SLA 逾期跟进 · {buyer}",
        description=(
            f"{detail}；下一步：{data.get('next_action') or '（未填写）'}；询盘ID：{inquiry_id}"
        ),
        task_type="followup",
        priority="high",
        status="open",
        tenant_id=tenant_id,
        assigned_to=owner,
        due_at=now + timedelta(days=1),
        created_by="system:sla-auto",
    )
    db.add(task)
    _mark_alerted(db, tenant_id, inquiry_id, today)
    db.commit()
    summary["alerted"] += 1
    summary["tasks_created"] += 1
    summary["notified"] += 1 if (feishu_ok or email_ok) else 0
    summary["items"].append(
        {
            "tenant_id": tenant_id,
            "inquiry_id": inquiry_id,
            "buyer": buyer,
            "feishu": feishu_ok,
            "email": email_ok,
            "task_id": str(task.id),
        }
    )


@shared_task(name="app.tasks.sla_tasks.sla_overdue_alert_daily", ignore_result=False)
def sla_overdue_alert_daily(dry_run: bool = False) -> dict:
    """每日 SLA 逾期巡检（P1-7）。

    dry_run=True 时只统计不落库/不通知，便于上线前验证。
    """
    from app.core.database import SessionLocal

    now = datetime.now(timezone.utc)
    today = now.date()
    summary: dict = {
        "scanned": 0,
        "overdue": 0,
        "alerted": 0,
        "tasks_created": 0,
        "notified": 0,
        "skipped": 0,
        "errors": 0,
        "items": [],
        "error": False,
    }
    try:
        with SessionLocal() as db:
            db.execute(text(_ALERT_DDL))
            db.commit()

            for inquiry_id, tenant_id, data in _iter_card_payloads(db):
                summary["scanned"] += 1
                try:
                    _handle_card(db, summary, inquiry_id, tenant_id, data, now, today, dry_run)
                except Exception as exc:  # noqa: BLE001
                    # 单卡失败绝不能拖垮整轮巡检：PG 报错后事务处于 aborted 状态，
                    # 不回滚后续所有语句都会失败（这正是首轮实测 55 张逾期只推进 1 张的原因）。
                    summary["errors"] += 1
                    logger.warning("SLA 告警单卡失败 tenant=%s inquiry=%s: %s", tenant_id, inquiry_id, exc)
                    try:
                        db.rollback()
                    except Exception:
                        pass
    except Exception:  # noqa: BLE001
        logger.exception("sla_overdue_alert_daily failed")
        summary["error"] = True
    return summary
