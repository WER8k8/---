# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Pydantic schemas for SSLCertificate."""
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class SSLCertificateBase(BaseModel):
    """Base schema for SSLCertificate."""
    tenant_id: UUID
    domain: str = Field(..., max_length=255)
    challenge_type: Optional[str] = Field(default="dns-01", max_length=20)


class SSLCertificateCreate(SSLCertificateBase):
    """Schema for creating a new SSLCertificate."""
    pass


class SSLCertificateUpdate(BaseModel):
    """Schema for updating an SSLCertificate (partial)."""
    is_active: Optional[str] = None
    auto_renew: Optional[str] = None
    challenge_type: Optional[str] = Field(default=None, max_length=20)


class SSLCertificateResponse(SSLCertificateBase):
    """Schema for SSLCertificate response."""
    id: UUID
    certificate: Optional[str] = None
    private_key: Optional[str] = None
    chain: Optional[str] = None
    expires_at: Optional[datetime] = None
    issued_at: Optional[datetime] = None
    is_active: str
    auto_renew: str
    last_renewal_attempt: Optional[datetime] = None
    renewal_error: Optional[str] = None
    challenge_token: Optional[str] = None
    challenge_value: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True
