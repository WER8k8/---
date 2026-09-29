# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""租户域名状态服务 —— 修正设计稿 模块1 / Production Gate G2。

在既有绑定入口（routes/domain.py，存 tenant.custom_domains JSON + ssl_certificate_service）
之上补齐**状态真源**（models.TenantDomain）：

- create_tenant_domain：登记 + 签发 DNS TXT 验证令牌（只回明文一次，库存 sha256 hash）
- verify_tenant_domain：首选 TXT 令牌校验，失败回落 CNAME 探测；两路均失败如实 failed
- activate_tenant_domain：未 verified 拒绝激活（409 语义）
- set_primary_domain：verified + active 才可设主域；同租户其余主域自动让位
- delete_tenant_domain：删状态行 + 清 legacy JSON
- resolve_verified_tenant：middleware 用 —— 仅 verified+active 的 Host 解析到租户

红线（G2）：
- 未 verified 的域名不得进入公开解析、不得设主域；
- domain → tenant 单一真源 = normalized_hostname 全局唯一；
- 状态变更一律经本服务，变更后清 TenantMiddleware 缓存。

legacy：tenant.custom_domains JSON 进入只读兼容（存量命中仍可解析，见对照表收敛项）。
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import secrets
from datetime import datetime, timezone
from typing import Callable, Optional

from sqlalchemy.orm import Session

from app.models.tenant import Tenant
from app.models.tenant_domain import TenantDomain

logger = logging.getLogger(__name__)

DOMAIN_REGEX = re.compile(
    r"^(?:(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,})$"
)
RESERVED_DOMAIN_SUFFIXES = ("youding-saas.com", "youding.com")
CNAME_TARGET = "saas.youding.com"


class DomainError(ValueError):
    """携带 HTTP 语义的业务错误（routes 层转 4xx）。"""

    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def normalize_hostname(hostname: str) -> str:
    host = (hostname or "").strip().lower()
    host = re.sub(r":\d+$", "", host).rstrip(".")
    if not DOMAIN_REGEX.match(host):
        raise DomainError(400, "域名格式不正确")
    for r in RESERVED_DOMAIN_SUFFIXES:
        if host == r or host.endswith(f".{r}"):
            raise DomainError(400, f"不能绑定系统保留域名后缀 {r}")
    return host


def _token_hash(token: str) -> str:
    return hashlib.sha256(f"uj-domain-verify:{token}".encode("utf-8")).hexdigest()


def _clear_middleware_cache() -> None:
    try:
        from app.core.tenant_middleware import TenantMiddleware

        TenantMiddleware.clear_cache()
    except Exception:  # noqa: BLE001 —— 缓存清理失败不影响状态变更
        logger.debug("tenant middleware cache clear skipped")


# ── 查询 ─────────────────────────────────────────────────────


def get_by_id(db: Session, domain_id: str) -> Optional[TenantDomain]:
    return db.query(TenantDomain).filter(TenantDomain.id == str(domain_id)).first()


def get_by_hostname(db: Session, hostname: str) -> Optional[TenantDomain]:
    normalized = normalize_hostname(hostname)
    return (
        db.query(TenantDomain)
        .filter(TenantDomain.normalized_hostname == normalized)
        .first()
    )


def list_for_tenant(db: Session, tenant_id: str) -> list[TenantDomain]:
    return (
        db.query(TenantDomain)
        .filter(TenantDomain.tenant_id == str(tenant_id))
        .order_by(TenantDomain.created_at.asc())
        .all()
    )


# ── 创建 / 令牌 ──────────────────────────────────────────────


def create_tenant_domain(
    db: Session,
    *,
    tenant: Tenant,
    hostname: str,
    verification_method: str = "dns_txt",
    domain_type: str = "custom",
) -> tuple[TenantDomain, str]:
    """登记域名并签发验证令牌。返回 (record, token 明文——仅此一次可见)。"""
    normalized = normalize_hostname(hostname)
    if get_by_hostname(db, normalized):
        raise DomainError(409, f"域名 {normalized} 已被绑定")
    if verification_method not in ("dns_txt", "dns_cname"):
        raise DomainError(400, "verification_method 仅支持 dns_txt / dns_cname")

    token = f"uj-verify-{secrets.token_urlsafe(24)}"
    record = TenantDomain(
        tenant_id=str(tenant.id),
        hostname=hostname.strip().lower(),
        normalized_hostname=normalized,
        domain_type=domain_type,
        verification_method=verification_method,
        verification_token_hash=_token_hash(token),
        verification_status="pending",
        ssl_status="pending",
        is_primary=False,
        is_active=False,
    )
    db.add(record)
    db.flush()
    _clear_middleware_cache()
    return record, token


def rotate_verification_token(db: Session, record: TenantDomain) -> str:
    """重发验证令牌（旧令牌立即失效，回到 pending）。"""
    token = f"uj-verify-{secrets.token_urlsafe(24)}"
    record.verification_token_hash = _token_hash(token)
    record.verification_status = "pending"
    record.verification_failed_reason = None
    db.add(record)
    db.commit()
    _clear_middleware_cache()
    return token


# ── 验证 ─────────────────────────────────────────────────────


def _txt_lookup_default(domain: str) -> Optional[str]:
    """真实 DNS TXT 查询：返回命中 uj-verify 前缀的记录值；无/失败返回 None。"""
    try:
        import dns.exception  # noqa: F401
        import dns.resolver

        answers = dns.resolver.resolve(f"_ujverify.{domain}", "TXT")
        for rdata in answers:
            for txt in getattr(rdata, "strings", []):
                value = txt.decode("utf-8", "ignore") if isinstance(txt, bytes) else str(txt)
                if value.startswith("uj-verify-"):
                    return value
        return None
    except ImportError:
        logger.warning("dnspython 未安装，TXT 验证不可用——诚实返回未命中，不伪造通过")
        return None
    except Exception:  # noqa: BLE001 —— NXDOMAIN/超时等一律未命中
        return None


def _cname_probe_default(domain: str) -> bool:
    """复用既有 CNAME 探测（routes/domain.probe_domain_dns），归属指向 saas 即视为通过。"""
    try:
        from app.api.v1.routes.domain import probe_domain_dns

        return bool(probe_domain_dns(domain))
    except Exception:  # noqa: BLE001
        return False


def verify_tenant_domain(
    db: Session,
    record: TenantDomain,
    *,
    txt_lookup: Optional[Callable[[str], Optional[str]]] = None,
    cname_probe: Optional[Callable[[str], bool]] = None,
) -> TenantDomain:
    """执行所有权验证。TXT 令牌优先，失败回落 CNAME 探测；均失败如实 failed。"""
    _txt = txt_lookup or _txt_lookup_default
    _cname = cname_probe or _cname_probe_default
    domain = record.normalized_hostname
    reasons: list[str] = []

    verified = False
    got = _txt(domain)
    if got and record.verification_token_hash and _token_hash(got) == record.verification_token_hash:
        verified = True
    else:
        reasons.append("txt_token_mismatch_or_missing")

    if not verified:
        if _cname(domain):
            verified = True
            reasons.append("cname_probe_fallback_ok")
        else:
            reasons.append("cname_probe_failed")

    record.last_verified_at = _utcnow()
    if verified:
        record.verification_status = "verified"
        record.verification_failed_reason = (
            ";".join(reasons) if "cname_probe_fallback_ok" in reasons else None
        )
    else:
        record.verification_status = "failed"
        record.verification_failed_reason = ";".join(reasons)[:255]
    db.add(record)
    db.commit()
    _clear_middleware_cache()
    return record


# ── 激活 / 主域 / 删除 ───────────────────────────────────────


def activate_tenant_domain(db: Session, record: TenantDomain) -> TenantDomain:
    """激活：未 verified 拒绝（G2 红线）。激活后 middleware 才解析该 Host。"""
    if record.verification_status != "verified":
        raise DomainError(409, "域名未通过所有权验证，禁止激活")
    record.is_active = True
    db.add(record)
    db.commit()
    _clear_middleware_cache()
    return record


def set_primary_domain(db: Session, record: TenantDomain) -> TenantDomain:
    """设主域：verified + active 才可；同租户其余主域自动让位（唯一性服务层保证）。"""
    if record.verification_status != "verified" or not record.is_active:
        raise DomainError(409, "仅已验证且已激活的域名可设为主域")
    others = (
        db.query(TenantDomain)
        .filter(
            TenantDomain.tenant_id == record.tenant_id,
            TenantDomain.id != record.id,
            TenantDomain.is_primary.is_(True),
        )
        .all()
    )
    for other in others:
        other.is_primary = False
        db.add(other)
    record.is_primary = True
    db.add(record)
    db.commit()
    _clear_middleware_cache()
    return record


def delete_tenant_domain(db: Session, record: TenantDomain) -> None:
    """删除状态行；同步清理 legacy JSON，确保旧 Host 不再解析到租户。"""
    tenant = db.query(Tenant).filter(Tenant.id == record.tenant_id).first()
    db.delete(record)
    if tenant and tenant.custom_domains:
        try:
            domains = json.loads(tenant.custom_domains)
            if isinstance(domains, list) and record.normalized_hostname in domains:
                domains.remove(record.normalized_hostname)
                tenant.custom_domains = json.dumps(domains, ensure_ascii=False)
                db.add(tenant)
        except (json.JSONDecodeError, TypeError, ValueError):
            pass
    db.commit()
    _clear_middleware_cache()


# ── middleware 解析 ──────────────────────────────────────────


def resolve_verified_tenant(db: Session, hostname: str) -> Optional[Tenant]:
    """仅 verified + active 的自定义域名解析到租户（G2：未验证禁止公开）。"""
    host = (hostname or "").strip().lower()
    host = re.sub(r":\d+$", "", host).rstrip(".")
    if not host:
        return None
    return (
        db.query(Tenant)
        .join(TenantDomain, TenantDomain.tenant_id == Tenant.id)
        .filter(
            TenantDomain.normalized_hostname == host,
            TenantDomain.verification_status == "verified",
            TenantDomain.is_active.is_(True),
            Tenant.is_active,
        )
        .first()
    )


def record_info(record: TenantDomain) -> dict:
    """API 输出（不回令牌明文；指引文案提示 rotate 重发）。"""
    return {
        "id": str(record.id),
        "tenant_id": str(record.tenant_id),
        "domain": record.hostname,
        "domain_type": record.domain_type,
        "verification_method": record.verification_method,
        "verification_status": record.verification_status,
        "verification_failed_reason": record.verification_failed_reason,
        "ssl_status": record.ssl_status,
        "is_primary": bool(record.is_primary),
        "is_active": bool(record.is_active),
        "cname_target": CNAME_TARGET,
        "txt_host": f"_ujverify.{record.normalized_hostname}",
    }
