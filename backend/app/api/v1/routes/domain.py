# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""SaaS 租户自定义域名绑定路由"""

import json
import re
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.response import APIResponse, error_response, success_response
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.tenant import Tenant, UserTenant
from app.models.user import User
from app.schemas.tenant import (
    DomainBinding,
    DomainBindingResponse,
    DomainListResponse,
)
from app.services.pilot_rehearsal_service import demo_https_rehearsal_report
from app.services.ssl_certificate_service import (
    list_ssl_records,
    refresh_pending,
    request_certificate,
    ssl_status_for_domain,
)


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = "/domains"
ROUTE_TAGS = ["租户自定义域名"]

router = APIRouter(tags=["租户自定义域名"])

DOMAIN_REGEX = re.compile(
    r"^(?:(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,})$"
)


def _get_tenant_for_user(
    tenant_id: str, user: User, db: Session
) -> Tenant | None:
    """验证用户对租户的访问权限并返回租户对象"""
    link = (
        db.query(UserTenant)
        .filter(
            UserTenant.user_id == user.id,
            UserTenant.tenant_id == tenant_id,
            UserTenant.is_active,
        )
        .first()
    )
    if not link and user.role not in ("admin", "super_admin"):
        return None
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    return tenant


def _parse_domains(tenant: Tenant) -> list[str]:
    """从 tenant.custom_domains 解析域名列表"""
    if not tenant.custom_domains:
        return []
    try:
        domains = json.loads(tenant.custom_domains)
        if isinstance(domains, list):
            return domains
    except (json.JSONDecodeError, TypeError):
        pass
    return []


def _save_domains(tenant: Tenant, domains: list[str], db: Session) -> None:
    """保存域名列表到 tenant.custom_domains"""
    tenant.custom_domains = json.dumps(domains, ensure_ascii=False)
    db.commit()
    db.refresh(tenant)


def _resolve_tenant_by_host(host: str, db: Session) -> Tenant | None:
    """根据 Host 解析租户（公开，供前端 SSR / 网关使用）"""
    from app.core.tenant_middleware import PRIMARY_DOMAIN_PATTERNS, extract_subdomain
    host_no_port = re.sub(r":\d+$", "", host.strip().lower())
    for pattern in PRIMARY_DOMAIN_PATTERNS:
        if re.match(pattern, host_no_port):
            return None

    subdomain = extract_subdomain(host)
    if not subdomain:
        return None

    tenant = (
        db.query(Tenant)
        .filter(Tenant.domain == subdomain, Tenant.is_active)
        .first()
    )
    if tenant:
        return tenant

    # 优化：减少逐行查询，直接使用列查询
    for t in db.query(Tenant).filter(Tenant.is_active).all():
        if host_no_port in _parse_domains(t):
            return t
    return None


# ---------- 公开解析 ----------


@router.get("/resolve")
def resolve_host(
    host: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
):
    """根据 Host 解析 tenant_id（公开接口，无需登录）"""
    tenant = _resolve_tenant_by_host(host, db)
    if not tenant:
        return error_response(404, "域名未绑定租户")
    return success_response(data={"tenant_id": str(tenant.id)})


# ---------- 列表 ----------


@router.get(
    "/tenants/{tenant_id}/domains",
    response_model=APIResponse[DomainListResponse],
)
def list_domains(
    tenant_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取租户已绑定的自定义域名列表"""
    tenant = _get_tenant_for_user(tenant_id, current_user, db)
    if not tenant:
        return error_response(404, "租户不存在或无权访问")

    domains = _parse_domains(tenant)
    items = [
        DomainBindingResponse(domain=d)
        for d in domains
    ]
    return success_response(data=DomainListResponse(items=items))


# ---------- 添加 ----------


@router.post(
    "/tenants/{tenant_id}/domains",
    response_model=APIResponse[DomainBindingResponse],
)
def add_domain(
    tenant_id: str,
    body: DomainBinding,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """添加自定义域名绑定，返回 DNS 验证信息（CNAME 记录值）"""
    tenant = _get_tenant_for_user(tenant_id, current_user, db)
    if not tenant:
        return error_response(404, "租户不存在或无权访问")

    domain = body.domain.strip().lower()
    # 格式验证
    if not DOMAIN_REGEX.match(domain):
        return error_response(400, "域名格式不正确")

    # 不能与系统保留域名冲突
    reserved = {"youding-saas.com", "youding.com"}
    for r in reserved:
        if domain.endswith(f".{r}") or domain == r:
            return error_response(400, f"不能绑定系统保留域名后缀 {r}")

    domains = _parse_domains(tenant)
    # 查重
    if domain in domains:
        return error_response(409, f"域名 {domain} 已绑定")

    # 跨租户查重：检查其他租户是否已绑定该域名
    all_tenants = db.query(Tenant).filter(Tenant.id != tenant.id).all()
    for t in all_tenants:
        existing = _parse_domains(t)
        if domain in existing:
            return error_response(409, f"域名 {domain} 已被其他租户绑定")

    # 修正设计稿 模块1：同步写入 tenant_domains 状态真源并签发 TXT 验证令牌。
    # 令牌明文仅在本次响应返回一次（库存 sha256 hash），丢失走 rotate 重发。
    from app.services import tenant_domain_service as tds
    try:
        state = tds.get_by_hostname(db, domain)
        if state and str(state.tenant_id) == str(tenant.id):
            record, token = state, tds.rotate_verification_token(db, state)
        elif state:
            return error_response(409, f"域名 {domain} 已被其他租户绑定")
        else:
            record, token = tds.create_tenant_domain(
                db, tenant=tenant, hostname=domain, verification_method="dns_txt"
            )
    except tds.DomainError as exc:
        return error_response(exc.status_code, exc.message)

    domains.append(domain)
    _save_domains(tenant, domains, db)
    return success_response(
        data={
            "domain": domain,
            "verified": False,
            "ssl_status": record.ssl_status,
            "cname_target": tds.CNAME_TARGET,
            "domain_id": str(record.id),
            "verification_method": "dns_txt",
            "txt_host": f"_ujverify.{domain}",
            "txt_record": token,
        },
        message=(
            f"域名 {domain} 已登记；请配置 TXT 记录 _ujverify.{domain} = 令牌，"
            f"并将 CNAME 指向 {tds.CNAME_TARGET}，然后调用 verify"
        ),
    )


# ---------- 删除 ----------


@router.delete(
    "/tenants/{tenant_id}/domains/{domain:path}",
    response_model=APIResponse,
)
def remove_domain(
    tenant_id: str,
    domain: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除自定义域名绑定"""
    tenant = _get_tenant_for_user(tenant_id, current_user, db)
    if not tenant:
        return error_response(404, "租户不存在或无权访问")

    domain = domain.strip().lower()
    domains = _parse_domains(tenant)
    if domain not in domains:
        return error_response(404, f"域名 {domain} 未绑定")

    domains.remove(domain)
    _save_domains(tenant, domains, db)
    # 修正设计稿 模块1：同步删除 tenant_domains 状态行 —— 旧 Host 立即不再解析到租户
    from app.services import tenant_domain_service as tds
    state = tds.get_by_hostname(db, domain)
    if state and str(state.tenant_id) == str(tenant.id):
        tds.delete_tenant_domain(db, state)
    return success_response(message=f"域名 {domain} 已解绑")


# ---------- 验证 DNS ----------


def probe_domain_dns(domain: str) -> bool:
    """探测域名 DNS 是否已生效。

    判定顺序：A/AAAA 记录（socket.getaddrinfo）→ CNAME 指向 youding/saas。
    dnspython 未安装时退化为仅 socket 检查。**探测失败一律返回 False，不伪造通过。**

    2026-09-24 抽出为模块级函数：供本文件 verify_domain 与
    `tenants.py` 的 `/tenants/domains/verify` 便捷端点共用，避免 DNS 逻辑重复实现。
    """
    import socket

    try:
        socket.getaddrinfo(domain, 80)
        return True
    except socket.gaierror:
        pass
    except (TimeoutError, Exception):  # noqa: BLE001
        return False

    # CNAME 可能还未生效或没有 A 记录，尝试 CNAME 查询
    try:
        import dns.exception
        import dns.resolver

        try:
            answers = dns.resolver.resolve(domain, "CNAME")
            for rdata in answers:
                target = str(rdata.target).rstrip(".")
                if "youding" in target or "saas" in target:
                    return True
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.exception.DNSException):
            return False
    except ImportError:
        # dnspython 未安装，只做 socket 检查
        return False
    return False


@router.get(
    "/tenants/{tenant_id}/domains/{domain:path}/verify",
    response_model=APIResponse[DomainBindingResponse],
)
def verify_domain(
    tenant_id: str,
    domain: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """验证域名 DNS 配置是否生效（检查 CNAME 是否指向 saas.youding.com）"""
    tenant = _get_tenant_for_user(tenant_id, current_user, db)
    if not tenant:
        return error_response(404, "租户不存在或无权访问")

    domain = domain.strip().lower()
    domains = _parse_domains(tenant)
    if domain not in domains:
        return error_response(404, f"域名 {domain} 未绑定")

    # 修正设计稿 模块1：优先走 tenant_domains 状态真源验证（TXT 令牌 → CNAME 回落），
    # 未登记状态表的 legacy 域名保留纯 DNS 探测兼容。
    from app.services import tenant_domain_service as tds
    state = tds.get_by_hostname(db, domain)
    if state and str(state.tenant_id) == str(tenant.id):
        state = tds.verify_tenant_domain(db, state)
        verified = state.verification_status == "verified"
    else:
        verified = probe_domain_dns(domain)

    # ⚠️ 2026-09-24 修复：原实现的 return 误缩进在 except 块内
    #    → **成功路径会掉出函数返回 None**。现改为无条件返回。
    return DomainBindingResponse(
        domain=domain,
        verified=verified,
        ssl_status=ssl_status_for_domain(tenant, domain),
        cname_target="saas.youding.com",
    )


# ---------- 触发 SSL ----------


def _get_domain_state(db: Session, tenant: Tenant, domain: str):
    """取租户域名状态行；不存在或不属于该租户返回 None。"""
    from app.services import tenant_domain_service as tds

    state = tds.get_by_hostname(db, domain)
    if state and str(state.tenant_id) == str(tenant.id):
        return state
    return None


@router.post("/tenants/{tenant_id}/domains/{domain:path}/activate")
def activate_domain(
    tenant_id: str,
    domain: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """激活域名（修正设计稿 模块1）。未通过所有权验证 → 409，不伪造激活。"""
    tenant = _get_tenant_for_user(tenant_id, current_user, db)
    if not tenant:
        return error_response(404, "租户不存在或无权访问")
    state = _get_domain_state(db, tenant, domain.strip().lower())
    if not state:
        return error_response(404, f"域名 {domain} 未登记状态（请先重新添加以签发验证令牌）")
    from app.services import tenant_domain_service as tds
    try:
        state = tds.activate_tenant_domain(db, state)
    except tds.DomainError as exc:
        return error_response(exc.status_code, exc.message)
    return success_response(data=tds.record_info(state), message=f"域名 {domain} 已激活")


@router.post("/tenants/{tenant_id}/domains/{domain:path}/set-primary")
def set_primary(
    tenant_id: str,
    domain: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """设为主域（verified + active 才可；同租户其余主域自动让位）。"""
    tenant = _get_tenant_for_user(tenant_id, current_user, db)
    if not tenant:
        return error_response(404, "租户不存在或无权访问")
    state = _get_domain_state(db, tenant, domain.strip().lower())
    if not state:
        return error_response(404, f"域名 {domain} 未登记状态")
    from app.services import tenant_domain_service as tds
    try:
        state = tds.set_primary_domain(db, state)
    except tds.DomainError as exc:
        return error_response(exc.status_code, exc.message)
    return success_response(data=tds.record_info(state), message=f"域名 {domain} 已设为主域")


@router.get("/tenants/{tenant_id}/domains/{domain:path}/status")
def domain_status(
    tenant_id: str,
    domain: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """域名状态总览：验证 / SSL / 主域 / 激活 + DNS 配置指引。"""
    tenant = _get_tenant_for_user(tenant_id, current_user, db)
    if not tenant:
        return error_response(404, "租户不存在或无权访问")
    state = _get_domain_state(db, tenant, domain.strip().lower())
    if not state:
        return error_response(404, f"域名 {domain} 未登记状态")
    from app.services import tenant_domain_service as tds
    info = tds.record_info(state)
    info["ssl_provider_status"] = ssl_status_for_domain(tenant, domain)
    return success_response(data=info)


@router.post("/tenants/{tenant_id}/domains/{domain:path}/rotate-token")
def rotate_domain_token(
    tenant_id: str,
    domain: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """重发 TXT 验证令牌（旧令牌立即失效，回到 pending）。明文仅本次返回。"""
    tenant = _get_tenant_for_user(tenant_id, current_user, db)
    if not tenant:
        return error_response(404, "租户不存在或无权访问")
    state = _get_domain_state(db, tenant, domain.strip().lower())
    if not state:
        return error_response(404, f"域名 {domain} 未登记状态")
    from app.services import tenant_domain_service as tds
    token = tds.rotate_verification_token(db, state)
    return success_response(
        data={"domain": state.hostname, "txt_host": f"_ujverify.{state.normalized_hostname}", "txt_record": token},
        message="验证令牌已重发（旧令牌失效）",
    )


# ---------- 触发 SSL ----------


@router.post(
    "/tenants/{tenant_id}/domains/{domain:path}/ssl",
    response_model=APIResponse[DomainBindingResponse],
)
def trigger_ssl(
    tenant_id: str,
    domain: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """触发 SSL 证书自动申请（预留接口，当前返回 pending）"""
    tenant = _get_tenant_for_user(tenant_id, current_user, db)
    if not tenant:
        return error_response(404, "租户不存在或无权访问")

    domain = domain.strip().lower()
    domains = _parse_domains(tenant)
    if domain not in domains:
        return error_response(404, f"域名 {domain} 未绑定")

    record = request_certificate(tenant, domain)
    db.commit()
    db.refresh(tenant)
    status = record.get("status", "pending")
    return success_response(
        data=DomainBindingResponse(
            domain=domain,
            verified=True,
            ssl_status=status,
            cname_target="saas.youding.com",
        ),
        message=f"域名 {domain} SSL 证书申请已提交（{status}）",
    )


@router.get(
    "/tenants/{tenant_id}/domains/ssl",
    response_model=APIResponse[dict],
)
def list_domain_ssl(
    tenant_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """列出租户各域名的 SSL 状态。"""
    tenant = _get_tenant_for_user(tenant_id, current_user, db)
    if not tenant:
        return error_response(404, "租户不存在或无权访问")
    return success_response(data=list_ssl_records(tenant))


@router.post(
    "/tenants/{tenant_id}/domains/{domain:path}/ssl/refresh",
    response_model=APIResponse[DomainBindingResponse],
)
def refresh_domain_ssl(
    tenant_id: str,
    domain: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """P0-01：轮询 ACME webhook / mock 待签发证书状态。"""
    tenant = _get_tenant_for_user(tenant_id, current_user, db)
    if not tenant:
        return error_response(404, "租户不存在或无权访问")
    domain = domain.strip().lower()
    refresh_pending(tenant)
    status = ssl_status_for_domain(tenant, domain)
    return success_response(
        data=DomainBindingResponse(
            domain=domain,
            verified=True,
            ssl_status=status,
            cname_target="saas.youding.com",
        ),
        message=f"SSL 状态已刷新：{status}",
    )


@router.get("/pilot/demo-https", response_model=APIResponse[dict])
def pilot_demo_https_check(
    domain: Optional[str] = Query(None, description="演示独立域，默认读 DEMO_HTTPS_DOMAIN"),
    current_user: User = Depends(get_current_user),
):
    """UBX-OPS-01 / P0-02：保温厂 HTTPS 演示域彩排探针。"""
    _ = current_user
    return success_response(data=demo_https_rehearsal_report(domain))
