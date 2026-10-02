# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""网站线索 HMAC 接入（GJ-U4 · GoodJob 上游 v1.9.1 同构，UJ 多租户化）。

上游参照：``_external/goodjob-crm/backend/src/server.ts`` 的 website-lead ingress 验签段
（canonical = v1\\nkeyId\\nMETHOD\\npath\\ntimestamp\\nnonce\\nsha256(body)）。
与上游差异（UJ 化）：
- 密钥**按租户**存 CredentialVault（AES-GCM + AAD 四元绑定），非单主体加密文件；
- 线索落 UJ ``inquiries``：tenant_id 来自**密钥属主**（不信任请求体）、
  source_channel 服务端强制 "website_ingress"（反欺骗：忽略客户端渠道声明）；
- 防重放：进程内 (key_id, nonce) 缓存 + ±600s 时效窗 + timingSecure 比对。
红线：任何一步不过即拒绝且**零落库**；密钥明文仅签发响应返回一次（vault 之外不落任何明文）。
"""
from __future__ import annotations

import hashlib
import hmac
import re
import secrets
import threading
import time
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.inquiry import Inquiry
from app.services.vault.credential_service import (
    CredentialVaultService,
    make_vault_ref,
)

_KEY_ID_RE = re.compile(r"[A-Za-z0-9_-]{2,80}")
_TIMESTAMP_RE = re.compile(r"\d{10}")
_NONCE_RE = re.compile(r"[A-Za-z0-9_-]{20,64}")
_SIGNATURE_RE = re.compile(r"v1=[a-f0-9]{64}")
_SECRET_MIN, _SECRET_MAX = 32, 512
_WINDOW_SECONDS = 600
_REPLAY_LIMIT = 10000
_CONNECTION_ID = "website-lead-ingress"
_ARTIFACT_TYPE = "webhook_secret"
_FORCED_CHANNEL = "website_ingress"

_replay_lock = threading.Lock()
_replay_cache: dict[str, int] = {}


class IngressError(Exception):
    """HMAC 接入拒绝（status ∈ unconfigured/invalid/expired/replay）。"""

    def __init__(self, status: str):
        self.status = status
        super().__init__(status)


# ---------------------------------------------------------------- 密钥管理（vault）


def issue_key(db: Session, *, tenant_id: str, label: str | None = None) -> dict[str, Any]:
    """签发接入密钥：key_id + secret（明文仅本次响应返回一次，vault 外零落盘）。"""
    key_id = f"wl-{secrets.token_urlsafe(6)}"
    secret = secrets.token_urlsafe(48)
    vault = CredentialVaultService(db)
    cred = vault.store_credential(
        secret=secret,
        tenant_id=str(tenant_id),
        owner_type="tenant",
        owner_id=str(tenant_id),
        connection_type="platform",
        connection_id=_CONNECTION_ID,
        artifact_type=_ARTIFACT_TYPE,
        name=key_id,
    )
    return {
        "key_id": key_id,
        "secret": secret,
        "vault_ref": make_vault_ref(str(cred.id)),
        "label": label or "",
        "tenant_id": str(tenant_id),
    }


def list_keys(db: Session, *, tenant_id: str) -> list[dict[str, Any]]:
    """本租户接入密钥列表（零明文：只给 key_id/状态/时间）。"""
    vault = CredentialVaultService(db)
    out = []
    for item in vault.list_credentials(tenant_id=str(tenant_id), status="active"):
        if item["connection_id"] != _CONNECTION_ID or item["artifact_type"] != _ARTIFACT_TYPE:
            continue
        out.append(
            {
                "key_id": item["name"],
                "vault_ref": item["vault_ref"],
                "created_at": item["created_at"],
                "last_used_at": item["last_used_at"],
            }
        )
    return out


def revoke_key(db: Session, *, tenant_id: str, key_id: str) -> bool:
    """吊销：vault 置 revoked（验签侧随 list 过滤自然失效）。幂等。"""
    vault = CredentialVaultService(db)
    for item in vault.list_credentials(tenant_id=str(tenant_id), status="active"):
        if item["connection_id"] == _CONNECTION_ID and item["name"] == key_id:
            vault.revoke_credential(item["vault_ref"])
            return True
    return False


def _candidate_secrets(db: Session, *, key_id: str) -> list[tuple[str, str]]:
    """跨租户按 key_id 解析候选密钥明文（key_id 含随机 token，跨租户碰撞可忽略）。

    返回 [(tenant_id, secret), ...]；vault AAD 四元绑定按各自属主校验。
    """
    vault = CredentialVaultService(db)
    out: list[tuple[str, str]] = []
    for item in vault.list_credentials(status="active"):
        if item["connection_id"] != _CONNECTION_ID or item["name"] != key_id:
            continue
        tid = str(item["tenant_id"] or "")
        if not tid:
            continue
        try:
            out.append(
                (
                    tid,
                    vault.resolve_credential(
                        item["vault_ref"],
                        tenant_id=tid,
                        owner_type="tenant",
                        owner_id=tid,
                        connection_type="platform",
                        connection_id=_CONNECTION_ID,
                        artifact_type=_ARTIFACT_TYPE,
                    ),
                )
            )
        except Exception:  # noqa: BLE001 —— 单个凭据解析失败跳过（吊销/轮换中间态）
            continue
    return out


# ---------------------------------------------------------------- 验签（上游同构）


def _prune_replay(now: int) -> None:
    for key, expires_at in list(_replay_cache.items()):
        if expires_at <= now:
            _replay_cache.pop(key, None)
    while len(_replay_cache) >= _REPLAY_LIMIT:
        _replay_cache.pop(next(iter(_replay_cache)), None)


def verify_signature(
    db: Session,
    *,
    method: str,
    path: str,
    headers: dict[str, str],
    raw_body: bytes,
) -> dict[str, Any]:
    """验签 + 防重放。返回 {"key_id", "tenant_id"}（ok，租户由密钥属主决定）；
    否则抛 IngressError（unconfigured/invalid/expired/replay）。

    headers 取值需为小写键名。canonical 与上游逐字段一致：
    ["v1", key_id, METHOD, path, timestamp, nonce, sha256(raw_body).hex()]。
    """
    key_id = (headers.get("x-goodjob-key-id") or "").strip()
    timestamp_text = (headers.get("x-goodjob-timestamp") or "").strip()
    nonce = (headers.get("x-goodjob-nonce") or "").strip()
    signature_header = (headers.get("x-goodjob-signature") or "").strip()

    if (
        not _KEY_ID_RE.fullmatch(key_id)
        or not _TIMESTAMP_RE.fullmatch(timestamp_text)
        or not _NONCE_RE.fullmatch(nonce)
        or not _SIGNATURE_RE.fullmatch(signature_header)
    ):
        raise IngressError("invalid")

    candidates = _candidate_secrets(db, key_id=key_id)
    if not candidates:
        raise IngressError("unconfigured")

    now = int(time.time())
    timestamp = int(timestamp_text)
    if abs(now - timestamp) > _WINDOW_SECONDS:
        raise IngressError("expired")

    body_hash = hashlib.sha256(raw_body).hexdigest()
    canonical = "\n".join(
        ["v1", key_id, method.upper(), path, timestamp_text, nonce, body_hash]
    )
    supplied = bytes.fromhex(signature_header[len("v1="):])
    matched_tenant: Optional[str] = None
    for tenant_id, secret in candidates:
        expected = hmac.new(secret.encode("utf-8"), canonical.encode("utf-8"), hashlib.sha256).digest()
        if hmac.compare_digest(expected, supplied):
            matched_tenant = tenant_id
            break
    if matched_tenant is None:
        raise IngressError("invalid")

    with _replay_lock:
        _prune_replay(now)
        replay_key = f"{key_id}:{nonce}"
        if _replay_cache.get(replay_key, 0) > now:
            raise IngressError("replay")
        _replay_cache[replay_key] = now + _WINDOW_SECONDS
    return {"key_id": key_id, "tenant_id": matched_tenant}


# ---------------------------------------------------------------- 线索落库


def create_inquiry(
    db: Session,
    *,
    tenant_id: str,
    payload: dict[str, Any],
    key_meta: dict[str, Any],
    external_id: str | None = None,
) -> Inquiry:
    """HMAC 已验证后的线索落库。反欺骗：渠道/来源服务端强制，忽略客户端声明。"""
    company = str(payload.get("company") or "").strip()
    contact = str(payload.get("contact") or "").strip()
    email = str(payload.get("email") or "").strip().lower()
    phone = str(payload.get("phone") or "").strip()
    content = str(payload.get("inquiryContent") or "").strip()
    if not company:
        raise ValueError("company_required")
    if not email and not phone:
        raise ValueError("contact_channel_required")
    if len(content) < 5 or len(content) > 5000:
        raise ValueError("inquiry_content_invalid")

    inquiry = Inquiry(
        name=(contact or company)[:100],
        email=email or None,
        phone=phone or None,
        message=content,
        status="pending",
        is_active=True,
        source_channel=_FORCED_CHANNEL,  # 服务端强制（反欺骗）
        tenant_id=str(tenant_id),
        session_id=(external_id or "")[:64] or None,
        provenance_metadata={
            "ingress": {
                "provider": "website_hmac",
                "key_id": key_meta.get("key_id", ""),
                "external_id": external_id or "",
                "declared_company": company[:200],
                "declared_contact": contact[:200],
            }
        },
    )
    db.add(inquiry)
    db.commit()
    db.refresh(inquiry)
    return inquiry
