# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""SSL Certificate API Routes - Auto-issuance via Let's Encrypt."""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging import get_logger
from app.models.ssl_certificate import SSLCertificate
from app.schemas.ssl_certificate import (
    SSLCertificateCreate,
    SSLCertificateResponse,
    SSLCertificateUpdate,
)
from app.core.security import require_admin
from app.models.user import User
from app.services.acme_service import SSLCertificateService

logger = get_logger(__name__)
ROUTE_PREFIX = ""
router = APIRouter(prefix="/ssl-certificates", tags=["SSL证书管理"])


@router.post("", response_model=SSLCertificateResponse, status_code=status.HTTP_201_CREATED)
async def create_ssl_certificate(
    cert_data: SSLCertificateCreate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> SSLCertificate:
    """Request SSL certificate issuance for a domain.

    Args:
        cert_data: SSL certificate creation data.
        db: Database session.

    Returns:
        SSLCertificate: Created certificate record.
    """
    # Check if certificate already exists for this domain
    result = await db.execute(
        select(SSLCertificate).where(
            SSLCertificate.domain == cert_data.domain,
            SSLCertificate.tenant_id == cert_data.tenant_id,
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Certificate already exists for this domain")

    # Create certificate record
    cert = SSLCertificate(
        tenant_id=cert_data.tenant_id,
        domain=cert_data.domain,
        challenge_type=cert_data.challenge_type or "dns-01",
    )
    db.add(cert)
    await db.commit()
    await db.refresh(cert)
    # Trigger issuance (async - would normally enqueue to worker)
    try:
        service = SSLCertificateService()
        issued = await service.issue_certificate(
            tenant_id=str(cert.tenant_id),
            domain=cert.domain,
            challenge_type=cert.challenge_type,
        )
        # Update certificate with issued data
        cert.certificate = issued["certificate"]
        cert.chain = issued["chain"]
        cert.expires_at = issued["expires_at"]
        cert.issued_at = issued["issued_at"]
        cert.is_active = "true"
        await db.commit()
        await db.refresh(cert)

    except Exception as e:
        logger.error(f"Failed to issue certificate for {cert.domain}: {e}")
        cert.renewal_error = str(e)
        await db.commit()

    logger.info(f"Created SSL certificate for {cert.domain}")
    return cert


@router.get("", response_model=List[SSLCertificateResponse])
async def list_ssl_certificates(
    tenant_id: UUID = Query(...),
    _admin: User = Depends(require_admin),
    is_active: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> List[SSLCertificate]:
    """List SSL certificates for a tenant.

    Args:
        tenant_id: Tenant ID.
        is_active: Filter by active status.
        skip: Pagination offset.
        limit: Pagination limit.
        db: Database session.

    Returns:
        List[SSLCertificate]: List of certificates.
    """
    query = select(SSLCertificate).where(SSLCertificate.tenant_id == tenant_id)
    if is_active:
        query = query.where(SSLCertificate.is_active == is_active)

    query = query.order_by(SSLCertificate.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    certs = result.scalars().all()
    return certs


@router.get("/{cert_id}", response_model=SSLCertificateResponse)
async def get_ssl_certificate(
    cert_id: UUID,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> SSLCertificate:
    """Get SSL certificate by ID.

    Args:
        cert_id: Certificate ID.
        db: Database session.

    Returns:
        SSLCertificate: Certificate record.

    Raises:
        HTTPException: If certificate not found.
    """
    result = await db.execute(select(SSLCertificate).where(SSLCertificate.id == str(cert_id)))
    cert = result.scalar_one_or_none()
    if not cert:
        raise HTTPException(status_code=404, detail="SSL certificate not found")

    return cert


@router.post("/{cert_id}/renew", response_model=Dict[str, Any])
async def renew_ssl_certificate(
    cert_id: UUID,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> Dict[str, Any]:
    """手动触发证书续期。

    参数:
        cert_id: 证书 ID。
        db: 数据库会话。

    返回:
        dict: 续期结果。

    异常:
        HTTPException: 证书不存在时抛出。
    """
    result = await db.execute(select(SSLCertificate).where(SSLCertificate.id == str(cert_id)))
    cert = result.scalar_one_or_none()
    if not cert:
        raise HTTPException(status_code=404, detail="SSL certificate not found")

    try:
        service = SSLCertificateService()
        renewed = await service.renew_certificate(
            domain=cert.domain,
            certificate=cert.certificate,
            private_key=cert.private_key,
        )
        # Update certificate
        cert.certificate = renewed["certificate"]
        cert.chain = renewed["chain"]
        cert.expires_at = renewed["expires_at"]
        cert.issued_at = renewed["issued_at"]
        cert.last_renewal_attempt = datetime.now(timezone.utc)
        cert.renewal_error = None
        await db.commit()
        logger.info(f"Renewed SSL certificate for {cert.domain}")
        return {"status": "success", "expires_at": renewed["expires_at"]}

    except Exception as e:
        logger.error(f"Failed to renew certificate for {cert.domain}: {e}")
        cert.last_renewal_attempt = datetime.now(timezone.utc)
        cert.renewal_error = str(e)
        await db.commit()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/auto-renew", response_model=Dict[str, Any])
async def trigger_auto_renewal(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> Dict[str, Any]:
    """Trigger auto-renewal check for all certificates.

    Returns:
        dict: Renewal summary.
    """
    from app.services.acme_service import auto_renew_certificates
    await auto_renew_certificates()
    return {"status": "auto_renewal_triggered"}
