# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""UBrain-X / Accio 卖货：租户记忆与采购商候选线索。"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text

from app.core.database import UUID_TYPE, Base


class UbrainTenantMemory(Base):
    """租户副驾记忆 — 品类、市场、语气；工具调用越多越贴近偏好。"""
    __tablename__ = "ubrain_tenant_memory"
    tenant_id = Column(UUID_TYPE, ForeignKey("tenants.id"), primary_key=True)
    memory_json = Column(Text, nullable=False, default="{}")
    tool_use_count = Column(Integer, nullable=False, default=0)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class BuyerProspectLead(Base):
    """采购商候选（画像级，需人工核实后联系）。"""
    __tablename__ = "buyer_prospect_leads"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(UUID_TYPE, ForeignKey("tenants.id"), nullable=False, index=True)
    region_label = Column(String(80), nullable=False)
    country_code = Column(String(8), nullable=True)
    buyer_type = Column(String(40), nullable=False)  # distributor / contractor / epc / importer
    title = Column(String(200), nullable=False)
    fit_score = Column(Integer, nullable=False, default=50)
    suggested_channel = Column(String(40), default="email")
    notes = Column(Text)
    outreach_draft = Column(Text)
    status = Column(String(20), nullable=False, default="discovered", index=True)
    source_tool = Column(String(64), default="find_buyers")
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
