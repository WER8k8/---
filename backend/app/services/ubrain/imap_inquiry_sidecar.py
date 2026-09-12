"""只读 IMAP 询盘收取 Sidecar — mymailclaw 对标，禁止 SMTP 自动发信。"""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_TIMEOUT = 90.0


def sidecar_base_url() -> str:
    """sidecar_base_url。
    :return: 返回处理结果。
    """
    return (os.getenv("IMAP_INQUIRY_URL") or "").strip().rstrip("/")


def sidecar_token() -> str:
    """sidecar_token。
    :return: 返回处理结果。
    """
    return (os.getenv("IMAP_INQUIRY_TOKEN") or "").strip()


def imap_inquiry_sidecar_status() -> dict[str, Any]:
    """imap_inquiry_sidecar_status。
    :return: 返回处理结果。
    """
    base = sidecar_base_url()
    out: dict[str, Any] = {
        "configured": bool(base),
        "url": base or None,
        "healthy": None,
        "detail": None,
        "github_ref": "mymailclaw",
        "contract_paths": ["/v1/poll-inbox"],
        "compliance": "read_only_imap",
        "smtp_disabled": True,
    }
    if not base:
        out["fallback"] = "not_configured"
        return out
    headers = _auth_headers()
    for path in ("/health", "/v1/health"):
        try:
            with httpx.Client(timeout=5.0) as client:
                resp = client.get(f"{base}{path}", headers=headers)
            if resp.status_code < 300:
                out["healthy"] = True
                out["health_path"] = path
                return out
            out["detail"] = f"{path}: HTTP {resp.status_code}"
        except Exception as exc:
            out["detail"] = str(exc)[:200]
    out["healthy"] = False
    return out


def _auth_headers() -> dict[str, str]:
    """_auth_headers。
    :return: 返回处理结果。
    """
    headers: dict[str, str] = {"Content-Type": "application/json"}
    token = sidecar_token()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def poll_imap_inbox(
    *,
    tenant_id: str | None = None,
    mailbox: str | None = None,
    max_messages: int = 10,
) -> dict[str, Any] | None:
    """poll_imap_inbox。

    参数说明：
    :param tenant_id: 参数 tenant_id
    :param mailbox: 参数 mailbox
    :param max_messages: 参数 max_messages
    :return: 返回处理结果。
    """
    base = sidecar_base_url()
    if not base:
        return None
    payload: dict[str, Any] = {
        "tenant_id": tenant_id,
        "max_messages": max(1, min(int(max_messages), 50)),
    }
    if mailbox:
        payload["mailbox"] = mailbox.strip()
    headers = _auth_headers()
    for path in ("/v1/poll-inbox", "/api/poll-inbox"):
        try:
            with httpx.Client(timeout=_TIMEOUT) as client:
                resp = client.post(f"{base}{path}", json=payload, headers=headers)
            if resp.status_code >= 300:
                continue
            data = resp.json()
            if isinstance(data, dict) and "data" in data:
                data = data["data"]
            if not isinstance(data, dict):
                continue
            messages = data.get("messages") or data.get("items") or []
            valid: list[dict[str, Any]] = []
            for row in messages:
                if not isinstance(row, dict):
                    continue
                message_id = str(row.get("message_id") or row.get("id") or "").strip()
                body = str(row.get("body") or row.get("text") or row.get("snippet") or "").strip()
                from_email = str(row.get("from_email") or row.get("email") or "").strip()
                if not message_id or not body or not from_email:
                    continue
                valid.append(
                    {
                        "message_id": message_id[:200],
                        "from_email": from_email[:200],
                        "from_name": str(row.get("from_name") or row.get("name") or "")[:120],
                        "subject": str(row.get("subject") or "")[:300],
                        "body": body[:8000],
                        "received_at": row.get("received_at"),
                        "evidence_url": str(
                            row.get("evidence_url") or row.get("imap_uid_url") or ""
                        )[:500]
                        or None,
                    }
                )
            if not valid and not data.get("ok"):
                return None
            out: dict[str, Any] = {
                "messages": valid,
                "count": len(valid),
                "mailbox": data.get("mailbox"),
                "human_verify_required": True,
            }
            if str(data.get("mode") or "").lower() == "mock":
                out["probe_mode"] = "stub"
            elif data.get("probe_mode"):
                out["probe_mode"] = data.get("probe_mode")
            return out
        except Exception as exc:
            logger.info("imap sidecar %s failed: %s", path, exc)
    return None
