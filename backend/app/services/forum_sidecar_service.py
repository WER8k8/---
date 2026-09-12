"""Apache Answer 论坛 Sidecar — 健康检查、租户嵌入配置。"""

from __future__ import annotations

import json
import os
import secrets
from typing import Any

import httpx

from app.models.tenant import Tenant


def sidecar_base_url() -> str:
    """sidecar_base_url。
    :return: 返回处理结果。
    """
    return (os.getenv("FORUM_SIDECAR_URL") or "http://127.0.0.1:9080").strip().rstrip("/")


def webhook_secret() -> str:
    """webhook_secret。
    :return: 返回处理结果。
    """
    return (os.getenv("FORUM_WEBHOOK_SECRET") or "").strip()


def forum_sidecar_status() -> dict[str, Any]:
    """forum_sidecar_status。
    :return: 返回处理结果。
    """
    base = sidecar_base_url()
    out: dict[str, Any] = {
        "configured": bool(base),
        "url": base,
        "healthy": None,
        "detail": None,
        "product": "apache_answer",
    }
    if not base:
        out["detail"] = "未配置 FORUM_SIDECAR_URL"
        return out
    for path in ("/health", "/healthz", "/"):
        try:
            with httpx.Client(timeout=5.0, follow_redirects=True) as client:
                resp = client.get(f"{base}{path}")
            if resp.status_code < 500:
                out["healthy"] = True
                out["health_path"] = path
                out["http_status"] = resp.status_code
                return out
            out["detail"] = f"{path}: HTTP {resp.status_code}"
        except Exception as exc:
            out["detail"] = str(exc)[:200]
    out["healthy"] = False
    return out


def _safe_settings(raw: str | None) -> dict[str, Any]:
    """_safe_settings。

    参数说明：
    :param raw: 参数 raw
    :return: 返回处理结果。
    """
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, TypeError):
        return {}


def get_tenant_forum_config(tenant: Tenant, *, api_base: str = "/api/v1") -> dict[str, Any]:
    """get_tenant_forum_config。

    参数说明：
    :param tenant: 参数 tenant
    :param api_base: 参数 api_base
    :return: 返回处理结果。
    """
    settings = _safe_settings(tenant.settings)
    forum = settings.get("forum") if isinstance(settings.get("forum"), dict) else {}
    enabled = bool(forum.get("enabled"))
    embed_url = str(forum.get("embed_url") or sidecar_base_url()).rstrip("/")
    public_path = str(forum.get("public_path") or "/questions").strip()
    if not public_path.startswith("/"):
        public_path = f"/{public_path}"
    iframe_src = f"{embed_url}{public_path}" if enabled and embed_url else None
    secret = str(forum.get("webhook_secret") or webhook_secret() or "")
    tid = str(tenant.id)
    webhook_url = f"{api_base.rstrip('/')}/forum/webhook"
    return {
        "enabled": enabled,
        "embed_url": embed_url,
        "public_path": public_path,
        "iframe_src": iframe_src,
        "tenant_id": tid,
        "tenant_domain": tenant.domain,
        "webhook_url": webhook_url,
        "webhook_secret": secret or None,
        "webhook_headers": {
            "X-Forum-Webhook-Secret": secret,
            "X-Tenant-Id": tid,
            "Content-Type": "application/json",
        },
        "honest_note": "买家问答来自 Sidecar；新问题先入 SEO 候选，不自动冒充活跃社区。",
        "sidecar": forum_sidecar_status(),
    }


def update_tenant_forum_config(
    tenant: Tenant,
    *,
    enabled: bool | None = None,
    embed_url: str | None = None,
    public_path: str | None = None,
    rotate_webhook_secret: bool = False,
) -> dict[str, Any]:
    """update_tenant_forum_config。

    参数说明：
    :param tenant: 参数 tenant
    :param enabled: 参数 enabled
    :param embed_url: 参数 embed_url
    :param public_path: 参数 public_path
    :param rotate_webhook_secret: 参数 rotate_webhook_secret
    :return: 返回处理结果。
    """
    settings = _safe_settings(tenant.settings)
    forum = settings.get("forum") if isinstance(settings.get("forum"), dict) else {}
    if enabled is not None:
        forum["enabled"] = bool(enabled)
    if embed_url is not None:
        forum["embed_url"] = embed_url.strip().rstrip("/") or sidecar_base_url()
    if public_path is not None:
        forum["public_path"] = public_path.strip() or "/questions"
    if rotate_webhook_secret or not forum.get("webhook_secret"):
        forum["webhook_secret"] = secrets.token_urlsafe(24)
    settings["forum"] = forum
    tenant.settings = json.dumps(settings, ensure_ascii=False)
    return forum
