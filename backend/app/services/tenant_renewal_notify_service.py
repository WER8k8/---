# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""租户到期续费提醒 — 飞书 + 邮件，幂等按到期日去重。"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.tenant import Tenant
from app.services.email_service import EmailService
from app.services.tenant_lifecycle_service import TenantLifecycleService

logger = logging.getLogger(__name__)

_NOTIFY_KEY = "renewal_notify_map"


def _load_settings(tenant: Tenant) -> dict[str, Any]:
    """_load_settings。

    参数说明：
    :param tenant: 参数 tenant
    :return: 返回处理结果。
    """
    if not tenant.settings:
        return {}
    try:
        data = json.loads(tenant.settings)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, TypeError):
        return {}


def _save_settings(tenant: Tenant, data: dict[str, Any]) -> None:
    """_save_settings。

    参数说明：
    :param tenant: 参数 tenant
    :param data: 参数 data
    :return: 返回处理结果。
    """
    tenant.settings = json.dumps(data, ensure_ascii=False)


def _notify_key(expires_at: str | None) -> str:
    """_notify_key。

    参数说明：
    :param expires_at: 参数 expires_at
    :return: 返回处理结果。
    """
    return (expires_at or "")[:10]


def _already_notified(tenant: Tenant, expires_at: str | None) -> bool:
    """_already_notified。

    参数说明：
    :param tenant: 参数 tenant
    :param expires_at: 参数 expires_at
    :return: 返回处理结果。
    """
    cfg = _load_settings(tenant)
    mapping = cfg.get(_NOTIFY_KEY) or {}
    return mapping.get(_notify_key(expires_at)) is not None


def _mark_notified(db: Session, tenant: Tenant, expires_at: str | None) -> None:
    """_mark_notified。

    参数说明：
    :param db: 参数 db
    :param tenant: 参数 tenant
    :param expires_at: 参数 expires_at
    :return: 返回处理结果。
    """
    cfg = _load_settings(tenant)
    mapping = cfg.get(_NOTIFY_KEY) or {}
    mapping[_notify_key(expires_at)] = datetime.now(timezone.utc).isoformat()
    cfg[_NOTIFY_KEY] = mapping
    _save_settings(tenant, cfg)
    db.commit()


def _send_feishu(title: str, content: str) -> bool:
    """_send_feishu。

    参数说明：
    :param title: 参数 title
    :param content: 参数 content
    :return: 返回处理结果。
    """
    webhook = (settings.FEISHU_WEBHOOK_URL or "").strip()
    if not webhook:
        return False
    payload = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": title},
                "template": "orange",
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
    except Exception as exc:
        logger.warning("飞书续费提醒失败: %s", exc)
        return False


def _send_email(to_email: str, tenant_name: str, expires_at: str) -> bool:
    """_send_email。

    参数说明：
    :param to_email: 参数 to_email
    :param tenant_name: 参数 tenant_name
    :param expires_at: 参数 expires_at
    :return: 返回处理结果。
    """
    if not to_email or not settings.SMTP_SERVER:
        return False
    try:
        svc = EmailService()
        subject = f"【优丁 SaaS】{tenant_name} 订阅即将到期"
        html = (
            f"<p>您好，</p>"
            f"<p>您的租户 <strong>{tenant_name}</strong> 将于 <strong>{expires_at[:10]}</strong> 到期。</p>"
            f"<p>请登录客户后台续费，避免服务中断：<a href=\"{settings.FRONTEND_URL}/client/billing\">立即续费</a></p>"
            f"<p>— 优丁建材 SaaS</p>"
        )
        return svc._send_email(to_email, subject, html)
    except Exception as exc:
        logger.warning("邮件续费提醒失败: %s", exc)
        return False


class TenantRenewalNotifyService:
    def __init__(self, db: Session):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param db: 参数 db
        :return: 返回处理结果。
        """
        self.db = db

    def notify_expiring(
        self,
        *,
        within_days: int = 7,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """notify_expiring。

        参数说明：
        :param self: 参数 self
        :param within_days: 参数 within_days
        :param dry_run: 参数 dry_run
        :return: 返回处理结果。
        """
        preview = TenantLifecycleService(self.db).preview_expiring(within_days=within_days)
        sent: list[dict[str, Any]] = []
        skipped = 0
        for row in preview.get("tenants") or []:
            tenant = self.db.query(Tenant).filter(Tenant.id == row["id"]).first()
            if not tenant:
                continue
            exp = row.get("expires_at")
            if _already_notified(tenant, exp):
                skipped += 1
                continue

            title = f"续费提醒 · {tenant.name}"
            md = (
                f"**租户**：{tenant.name}\n"
                f"**到期**：{exp}\n"
                f"**状态**：{tenant.status}\n"
                f"请引导客户前往 `/client/billing` 续费。"
            )
            if dry_run:
                sent.append({"tenant_id": str(tenant.id), "dry_run": True, "expires_at": exp})
                continue

            feishu_ok = _send_feishu(title, md)
            email_ok = _send_email(tenant.contact_email or "", tenant.name, exp or "")
            _mark_notified(self.db, tenant, exp)
            sent.append(
                {
                    "tenant_id": str(tenant.id),
                    "feishu": feishu_ok,
                    "email": email_ok,
                    "expires_at": exp,
                }
            )

        return {
            "within_days": within_days,
            "dry_run": dry_run,
            "sent_count": len(sent),
            "skipped_count": skipped,
            "items": sent,
        }
