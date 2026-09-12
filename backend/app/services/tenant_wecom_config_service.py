"""租户企微推送配置 — 客户填写自己的 Corp / Agent / 销售 UserID。"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.no_fake_delivery import is_production_environment
from app.models.tenant_wecom_push import TenantWecomPushConfig


@dataclass
class TenantWecomCredentials:
    tenant_id: str
    enabled: bool
    corp_id: str
    agent_id: int
    agent_secret: str
    push_userids: list[str]
    webhook_url: str
    @property
    def app_ready(self) -> bool:
        """app_ready。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return bool(self.corp_id and self.agent_secret and self.agent_id > 0 and self.push_userids)

    @property
    def webhook_ready(self) -> bool:
        """webhook_ready。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return bool(self.webhook_url.strip())


def _parse_userids(raw: Optional[str]) -> list[str]:
    """_parse_userids。

    参数说明：
    :param raw: 参数 raw
    :return: 返回处理结果。
    """
    if not raw:
        return []
    parts = re.split(r"[|,;,\s]+", raw.strip())
    return [p for p in parts if p]


def get_or_create_row(db: Session, tenant_id: str) -> TenantWecomPushConfig:
    """get_or_create_row。

    参数说明：
    :param db: 参数 db
    :param tenant_id: 参数 tenant_id
    :return: 返回处理结果。
    """
    row = (
        db.query(TenantWecomPushConfig)
        .filter(TenantWecomPushConfig.tenant_id == tenant_id)
        .first()
    )
    if row:
        return row
    row = TenantWecomPushConfig(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        enabled=False,
    )
    db.add(row)
    db.flush()
    return row


def serialize_for_api(row: TenantWecomPushConfig) -> dict[str, Any]:
    """serialize_for_api。

    参数说明：
    :param row: 参数 row
    :return: 返回处理结果。
    """
    userids = _parse_userids(row.push_userids)
    return {
        "tenant_id": row.tenant_id,
        "enabled": bool(row.enabled),
        "corp_id": row.corp_id or "",
        "agent_id": row.agent_id or "",
        "agent_secret_set": bool((row.agent_secret or "").strip()),
        "push_userids": userids,
        "push_userids_text": row.push_userids or "",
        "webhook_url": row.webhook_url or "",
        "app_ready": bool(
            row.enabled
            and row.corp_id
            and row.agent_secret
            and row.agent_id
            and userids
        ),
        "webhook_ready": bool(row.enabled and (row.webhook_url or "").strip()),
        "note": "推送接收人为本租户企微成员 UserID，由客户在后台自行配置",
    }


def upsert_config(
    db: Session,
    tenant_id: str,
    *,
    enabled: Optional[bool] = None,
    corp_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    agent_secret: Optional[str] = None,
    push_userids: Optional[str] = None,
    webhook_url: Optional[str] = None,
) -> dict[str, Any]:
    """upsert_config。

    参数说明：
    :param db: 参数 db
    :param tenant_id: 参数 tenant_id
    :param enabled: 参数 enabled
    :param corp_id: 参数 corp_id
    :param agent_id: 参数 agent_id
    :param agent_secret: 参数 agent_secret
    :param push_userids: 参数 push_userids
    :param webhook_url: 参数 webhook_url
    :return: 返回处理结果。
    """
    row = get_or_create_row(db, tenant_id)
    if enabled is not None:
        row.enabled = bool(enabled)
    if corp_id is not None:
        row.corp_id = corp_id.strip()[:64] or None
    if agent_id is not None:
        row.agent_id = agent_id.strip()[:32] or None
    if agent_secret is not None and agent_secret.strip():
        row.agent_secret = agent_secret.strip()[:200]
    if push_userids is not None:
        row.push_userids = push_userids.strip() or None
    if webhook_url is not None:
        row.webhook_url = webhook_url.strip()[:500] or None
    db.commit()
    db.refresh(row)
    payload = serialize_for_api(row)
    if payload.get("app_ready") or payload.get("webhook_ready"):
        try:
            from app.services.onboarding_progress_service import mark_sales_channel_flag
            mark_sales_channel_flag(db, tenant_id, "wecom_push_configured")
            db.commit()
        except Exception:
            db.rollback()
    return payload


def resolve_tenant_credentials(db: Session, tenant_id: Optional[str]) -> Optional[TenantWecomCredentials]:
    """resolve_tenant_credentials。

    参数说明：
    :param db: 参数 db
    :param tenant_id: 参数 tenant_id
    :return: 返回处理结果。
    """
    if not tenant_id:
        return None
    row = (
        db.query(TenantWecomPushConfig)
        .filter(TenantWecomPushConfig.tenant_id == tenant_id)
        .first()
    )
    if not row or not row.enabled:
        return None
    try:
        agent_id = int((row.agent_id or "").strip())
    except ValueError:
        agent_id = 0
    return TenantWecomCredentials(
        tenant_id=str(tenant_id),
        enabled=True,
        corp_id=(row.corp_id or "").strip(),
        agent_id=agent_id,
        agent_secret=(row.agent_secret or "").strip(),
        push_userids=_parse_userids(row.push_userids),
        webhook_url=(row.webhook_url or "").strip(),
    )


def platform_dev_fallback_userids() -> list[str]:
    """仅开发环境：平台 .env 兜底，生产禁止用于客户推送。"""
    if is_production_environment():
        return []
    import os
    raw = (os.getenv("WECOM_PUSH_TO_USERIDS", "") or settings.WECOM_PUSH_TO_USERIDS or "").strip()
    return _parse_userids(raw)


def platform_dev_credentials(tenant_id: str) -> Optional[TenantWecomCredentials]:
    """开发环境：租户未配全时，用平台 .env 企微凭证 + UserID 兜底跑通 5b 彩排。"""
    if is_production_environment():
        return None
    import os
    corp_id = (os.getenv("WECOM_CORP_ID", "") or settings.WECOM_CORP_ID or "").strip()
    agent_secret = (os.getenv("WECOM_AGENT_SECRET", "") or settings.WECOM_AGENT_SECRET or "").strip()
    agent_raw = (os.getenv("WECOM_AGENT_ID", "") or settings.WECOM_AGENT_ID or "").strip()
    userids = platform_dev_fallback_userids()
    if not (corp_id and agent_secret and agent_raw and userids):
        return None
    try:
        agent_id = int(agent_raw)
    except ValueError:
        return None
    if agent_id <= 0:
        return None
    return TenantWecomCredentials(
        tenant_id=str(tenant_id),
        enabled=True,
        corp_id=corp_id,
        agent_id=agent_id,
        agent_secret=agent_secret,
        push_userids=userids,
        webhook_url="",
    )


def resolve_push_credentials(
    db: Session,
    tenant_id: Optional[str],
) -> tuple[Optional[TenantWecomCredentials], list[str], str]:
    """推送用凭证：优先租户配置，开发环境可回落平台 .env。"""
    if not tenant_id:
        return None, [], "none"
    cred = resolve_tenant_credentials(db, tenant_id)
    recipients = (cred.push_userids if cred else []) or platform_dev_fallback_userids()
    if cred and (cred.app_ready or cred.webhook_ready):
        if not recipients and cred.push_userids:
            recipients = cred.push_userids
        return cred, recipients, "tenant"
    if cred and cred.webhook_ready:
        return cred, recipients or cred.push_userids, "tenant_webhook"
    platform_cred = platform_dev_credentials(tenant_id)
    if platform_cred:
        return platform_cred, platform_cred.push_userids, "platform_dev"
    return cred, recipients, "tenant_partial" if cred else "none"
