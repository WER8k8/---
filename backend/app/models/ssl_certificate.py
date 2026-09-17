# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""SSL Certificate model for independent domain SSL auto-issuance."""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, String, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import UUID_TYPE, Base


class SSLCertificate(Base):
    __tablename__ = "ssl_certificates"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(UUID_TYPE, ForeignKey("tenants.id"), nullable=False, index=True)
    domain = Column(String(255), nullable=False, index=True)
    certificate = Column(Text, nullable=True)  # PEM certificate
    private_key = Column(Text, nullable=True)  # PEM private key
    chain = Column(Text, nullable=True)  # PEM chain
    expires_at = Column(DateTime(timezone=True), nullable=True)
    issued_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(String(10), default="true")
    auto_renew = Column(String(10), default="true")
    last_renewal_attempt = Column(DateTime(timezone=True), nullable=True)
    renewal_error = Column(Text, nullable=True)
    # ACME challenge info
    challenge_type = Column(String(20), default="dns-01")  # dns-01 or http-01
    challenge_token = Column(String(255), nullable=True)
    challenge_value = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    # Relationships
    tenant = relationship("Tenant", back_populates="ssl_certificates")
