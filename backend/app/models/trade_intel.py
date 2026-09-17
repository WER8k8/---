# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""出海参谋 — 品类×国家规则（M0 可落库维护）。"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, String, Text

from app.core.database import UUID_TYPE, Base


class TradeCountryCategory(Base):
    __tablename__ = "trade_country_category"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    category_key = Column(String(64), nullable=False, index=True)
    category_label = Column(String(120), nullable=False)
    hs_chapter = Column(String(16), nullable=False, default="")
    country_code = Column(String(2), nullable=False, index=True)
    verdict = Column(String(16), nullable=False, default="caution")  # go | caution | hard
    growth = Column(String(32), nullable=True)
    competition = Column(String(32), nullable=True)
    certs_json = Column(Text, default="[]")
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
