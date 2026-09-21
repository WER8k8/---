# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""P1-3 客户健康度+流失预警自动动作：每日扫描高风险租户，自动建销售跟进任务 + 飞书/邮件通知。

复用既有 ChurnService.get_at_risk_tenants 计算风险，对 high（或 medium）风险租户
自动：① 创建 SalesTask 跟进任务；② 飞书+邮件通知客户成功；③ 写入幂等标记
（7 天内同一租户不重复动作）。与 P1-1 续费提醒同构，纯接线、零新增数据模型。
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone

import httpx
from celery import shared_task

logger = logging.getLogger(__name__)

_CHURN_AUTO_KEY = "churn_auto_action_at"
_AUTO_RENOTIFY_DAYS = 7


def _load_settings(tenant) -> dict:
    """读取 tenant.settings JSON（缺省空 dict）。"""
    if not tenant.settings:
        return {}
    try:
        data = json.loads(tenant.settings)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, TypeError):
        return {}


def _save_settings(tenant, data) -> None:
    """写回 tenant.settings JSON。"""
    tenant.settings = json.dumps(data, ensure_ascii=False)


def _already_auto_actioned(tenant) -> bool:
    """7 天内已自动动作的租户跳过，避免每日重复打扰（持续高风险则每周再提醒）。"""
    cfg = _load_settings(tenant)
    ts = cfg.get(_CHURN_AUTO_KEY)
    if not ts:
        return False
    try:
        last = datetime.fromisoformat(ts)
    except (ValueError, TypeError):
        return False
    return (datetime.now(timezone.utc) - last) < timedelta(days=_AUTO_RENOTIFY_DAYS)


def _mark_auto_actioned(db, tenant) -> None:
    """标记本次自动动作时间（同时 flush 同会话内待提交的 SalesTask）。"""
    cfg = _load_settings(tenant)
    cfg[_CHURN_AUTO_KEY] = datetime.now(timezone.utc).isoformat()
    _save_settings(tenant, cfg)
    db.commit()


def _send_feishu(title: str, content: str) -> bool:
    """飞书通知（红模板，匹配流失预警语义）。"""
    from app.core.config import settings

    webhook = (settings.FEISHU_WEBHOOK_URL or "").strip()
    if not webhook:
        return False
    payload = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": title},
                "template": "red",
            },
            "elements": [
                {"tag": "div", "text": {"tag": "lark_md", "content": content}},
            ],
        },
    }
    try:
        with httpx.Client(timeout=10) as client:
            resp = client.post(webhook, json=payload)
            return resp.status_code < 300
    except Exception as exc:  # noqa: BLE001
        logger.warning("飞书流失预警通知失败: %s", exc)
        return False


def _send_email(to_email: str, tenant_name: str, reasons: str) -> bool:
    """邮件通知客户成功团队。"""
    from app.core.config import settings

    if not to_email or not settings.SMTP_SERVER:
        return False
    try:
        from app.services.email_service import EmailService

        svc = EmailService()
        subject = f"【优丁 SaaS】流失风险预警 · {tenant_name}"
        html = (
            f"<p>您好，</p>"
            f"<p>租户 <strong>{tenant_name}</strong> 出现流失风险信号：</p>"
            f"<p>{reasons}</p>"
            f"<p>请登录客户后台跟进：<a href=\"{settings.FRONTEND_URL}/client/churn\">立即处理</a></p>"
            f"<p>— 优丁建材 SaaS</p>"
        )
        return svc._send_email(to_email, subject, html)
    except Exception as exc:  # noqa: BLE001
        logger.warning("邮件流失预警通知失败: %s", exc)
        return False


@shared_task(name="app.tasks.churn_tasks.churn_auto_action_daily", ignore_result=False)
def churn_auto_action_daily(min_risk: str = "high", dry_run: bool = False) -> dict:
    """每日流失预警自动动作（P1-3）。

    扫描 high（min_risk=high）或全部 high+medium 风险租户，对每个未动作过的租户
    自动建 SalesTask 跟进任务并飞书/邮件通知；幂等按 7 天去重。
    """
    from app.core.database import SessionLocal
    from app.models.sales_task import SalesTask
    from app.models.tenant import Tenant
    from app.services.churn_service import ChurnService

    levels = {"high"} if min_risk == "high" else {"high", "medium"}
    summary: dict = {
        "scanned": 0,
        "actions": 0,
        "tasks_created": 0,
        "notified": 0,
        "skipped": 0,
        "items": [],
        "error": False,
    }
    try:
        with SessionLocal() as db:
            at_risk = ChurnService.get_at_risk_tenants(db)
            summary["scanned"] = len(at_risk)
            for t in at_risk:
                if t["risk_level"] not in levels:
                    continue
                tid = str(t["id"])
                tenant = db.query(Tenant).filter(Tenant.id == tid).first()
                if not tenant:
                    continue
                if _already_auto_actioned(tenant):
                    summary["skipped"] += 1
                    continue
                reasons = "；".join(t.get("reasons") or []) or "流失风险"
                priority = "high" if t["risk_level"] == "high" else "normal"
                if dry_run:
                    summary["items"].append(
                        {
                            "tenant_id": tid,
                            "name": t["name"],
                            "risk_level": t["risk_level"],
                            "dry_run": True,
                        }
                    )
                    summary["actions"] += 1
                    continue
                feishu_ok = _send_feishu(
                    f"流失预警 · {tenant.name}",
                    f"**租户**：{tenant.name}\n**风险等级**：{t['risk_level']}\n"
                    f"**信号**：{reasons}\n请安排客户成功跟进。",
                )
                email_ok = _send_email(tenant.contact_email or "", tenant.name, reasons)
                task = SalesTask(
                    title=f"流失预警跟进 · {tenant.name}",
                    description=f"风险等级：{t['risk_level']}；信号：{reasons}",
                    task_type="followup",
                    priority=priority,
                    status="open",
                    tenant_id=tid,
                    due_at=datetime.now(timezone.utc) + timedelta(days=3),
                    created_by="system:churn-auto",
                )
                db.add(task)
                _mark_auto_actioned(db, tenant)  # 提交 tenant.settings 同时 flush task
                summary["actions"] += 1
                summary["tasks_created"] += 1
                summary["notified"] += 1 if (feishu_ok or email_ok) else 0
                summary["items"].append(
                    {
                        "tenant_id": tid,
                        "name": tenant.name,
                        "risk_level": t["risk_level"],
                        "feishu": feishu_ok,
                        "email": email_ok,
                        "task_id": str(task.id),
                    }
                )
    except Exception:  # noqa: BLE001
        logger.exception("churn_auto_action_daily failed")
        summary["error"] = True
    return summary
