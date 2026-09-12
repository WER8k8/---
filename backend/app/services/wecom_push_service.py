"""Lane P · 企业微信推送（租户自有凭证 + 群机器人）。"""

from __future__ import annotations

import logging
import uuid
from typing import Any, Optional, TYPE_CHECKING

import httpx

from app.core.config import settings

if TYPE_CHECKING:
    from app.services.tenant_wecom_config_service import TenantWecomCredentials

logger = logging.getLogger(__name__)

_token_cache: dict[str, dict[str, Any]] = {}


def get_access_token_for(*, corp_id: str, agent_secret: str, cache_key: str, force_refresh: bool = False) -> str:
    """get_access_token_for。

    参数说明：
    :param corp_id: 参数 corp_id
    :param agent_secret: 参数 agent_secret
    :param cache_key: 参数 cache_key
    :param force_refresh: 参数 force_refresh
    :return: 返回处理结果。
    """
    import time
    if not corp_id or not agent_secret:
        raise RuntimeError("WECOM_NOT_CONFIGURED")

    now = time.time()
    cached = _token_cache.get(cache_key) or {}
    if not force_refresh and cached.get("token") and cached.get("expires_at", 0) > now + 60:
        return str(cached["token"])

    url = "https://qyapi.weixin.qq.com/cgi-bin/gettoken"
    params = {"corpid": corp_id, "corpsecret": agent_secret}
    with httpx.Client(timeout=12.0) as client:
        resp = client.get(url, params=params)
        data = resp.json()

    if data.get("errcode", 0) != 0:
        raise RuntimeError(f"WECOM_TOKEN_FAILED:{data.get('errcode')}:{data.get('errmsg')}")

    token = str(data.get("access_token") or "")
    if not token:
        raise RuntimeError("WECOM_TOKEN_EMPTY")

    _token_cache[cache_key] = {
        "token": token,
        "expires_at": now + int(data.get("expires_in") or 7200),
    }
    return token


def send_app_text_message_with_credentials(
    cred: "TenantWecomCredentials",
    *,
    userids: list[str],
    content: str,
    duplicate_check: bool = True,
) -> dict[str, Any]:
    """使用租户自有企微应用发消息；成功须返回 msgid。"""
    if not userids:
        return {
            "sent": False,
            "error_code": "NO_RECIPIENT",
            "error_message": "请在本租户后台配置企微销售 UserID",
        }
    if not cred.agent_id:
        return {"sent": False, "error_code": "NO_AGENT_ID", "error_message": "企微 AgentId 无效"}

    cache_key = f"tenant:{cred.tenant_id}:{cred.corp_id}"
    try:
        token = get_access_token_for(
            corp_id=cred.corp_id,
            agent_secret=cred.agent_secret,
            cache_key=cache_key,
        )
    except RuntimeError as exc:
        return {"sent": False, "error_code": "WECOM_TOKEN", "error_message": str(exc)}

    payload: dict[str, Any] = {
        "touser": "|".join(userids),
        "msgtype": "text",
        "agentid": cred.agent_id,
        "text": {"content": content[:3500]},
        "enable_duplicate_check": 1 if duplicate_check else 0,
        "duplicate_check_interval": 1800,
    }
    url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={token}"
    with httpx.Client(timeout=15.0) as client:
        resp = client.post(url, json=payload)
        data = resp.json()

    errcode = int(data.get("errcode", -1))
    if errcode != 0:
        return {
            "sent": False,
            "error_code": f"WECOM_{errcode}",
            "error_message": str(data.get("errmsg") or "send_failed"),
            "upstream_receipt": data,
        }

    msgid = str(data.get("msgid") or "").strip()
    if not msgid:
        return {
            "sent": False,
            "error_code": "WECOM_NO_MSGID",
            "error_message": "企微返回成功但无 msgid",
            "upstream_receipt": data,
        }

    return {
        "sent": True,
        "channel": "wecom_app",
        "upstream_msgid": msgid,
        "upstream_receipt": data,
        "recipient": payload["touser"],
    }


def send_webhook_markdown_to_url(*, webhook_url: str, title: str, body_md: str) -> dict[str, Any]:
    """租户自有群机器人 Webhook。"""
    url = (webhook_url or "").strip()
    if not url:
        return {"sent": False, "error_code": "NO_WEBHOOK", "error_message": "未配置租户群机器人 Webhook"}

    content = f"## {title[:80]}\n{body_md[:3500]}"
    payload = {"msgtype": "markdown", "markdown": {"content": content}}
    with httpx.Client(timeout=12.0) as client:
        resp = client.post(url, json=payload)
        try:
            data = resp.json()
        except Exception:
            data = {"raw": resp.text[:300], "status_code": resp.status_code}

    errcode = int(data.get("errcode", -1)) if isinstance(data, dict) else -1
    if resp.status_code >= 400 or (isinstance(data, dict) and errcode not in (0,)):
        return {
            "sent": False,
            "error_code": f"WEBHOOK_{errcode if errcode >= 0 else resp.status_code}",
            "error_message": str(data.get("errmsg") if isinstance(data, dict) else resp.text[:200]),
            "upstream_receipt": data,
        }

    receipt_id = f"webhook-{uuid.uuid4().hex[:12]}"
    return {
        "sent": True,
        "channel": "wecom_webhook",
        "upstream_msgid": receipt_id,
        "upstream_receipt": data,
        "recipient": "tenant_group_webhook",
    }


# ── 平台运维通道（Hermes 告警专用，非客户推送） ──

def send_platform_ops_webhook(*, title: str, body_md: str) -> dict[str, Any]:
    """send_platform_ops_webhook。

    参数说明：
    :param title: 参数 title
    :param body_md: 参数 body_md
    :return: 返回处理结果。
    """
    import os
    url = (os.getenv("HERMES_WECHAT_WEBHOOK_URL", "") or settings.HERMES_WECHAT_WEBHOOK_URL or "").strip()
    return send_webhook_markdown_to_url(webhook_url=url, title=title, body_md=body_md)
