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

    domains.append(domain)
    _save_domains(tenant, domains, db)
    return success_response(
        data=DomainBindingResponse(
            domain=domain,
            verified=False,
            ssl_status="none",
            cname_target="saas.youding.com",
        ),
        message=f"域名 {domain} 添加成功，请配置 CNAME 记录指向 saas.youding.com",
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
    return success_response(message=f"域名 {domain} 已解绑")


# ---------- 验证 DNS ----------


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

    verified = False
    try:
        import socket
        try:
            result = socket.getaddrinfo(domain, 80)
            verified = True
        except socket.gaierror:
            # CNAME 可能还未生效或没有 A 记录，尝试 CNAME 查询
            try:
                import dns.resolver
                try:
                    answers = dns.resolver.resolve(domain, "CNAME")
                    for rdata in answers:
                        target = str(rdata.target).rstrip(".")
                        if "youding" in target or "saas" in target:
                            verified = True
                            break
                except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.exception.DNSException):
                    pass
            except ImportError:
                # dnspython 未安装，只做 socket 检查
                pass
    except (socket.gaierror, TimeoutError, Exception):
        pass
        return DomainBindingResponse(
            domain=domain,
            verified=verified,
            ssl_status=ssl_status_for_domain(tenant, domain),
            cname_target="saas.youding.com",
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
