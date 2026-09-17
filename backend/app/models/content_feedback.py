# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Content Feedback Loop — DB models for feedback checks and industry patterns.

Tables:
  - content_feedback_checks: tracks pending/checked/expired rank probes per published URL
  - industry_patterns: records success/failure/boost patterns to inform future tactics
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Integer, JSON, String, Text

from app.core.database import UUID_TYPE, Base


class ContentFeedbackCheck(Base):
    """Scheduled GEO/SEO probe for a published content piece.

    Lifecycle: pending -> checked (or expired if not picked up in time).
    Stores rank probe results and flags content that needs refresh.
    """
    __tablename__ = "content_feedback_checks"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    content_id = Column(UUID_TYPE, nullable=False, index=True)
    publish_url = Column(String(1000), nullable=False)
    platform = Column(String(100), default="")
    tenant_id = Column(String(36), nullable=True, index=True)
    keyword = Column(String(500), default="")
    tactics_version = Column(String(50), default="")
    # Scheduling
    status = Column(
        String(20), default="pending", nullable=False, index=True
    )  # pending | checked | expired
    check_at = Column(
        DateTime(timezone=True), nullable=False, index=True
    )
    # Probe results (populated after check)
    is_indexed = Column(Boolean, nullable=True)
    rank_position = Column(Integer, nullable=True)
    rank_change = Column(Integer, nullable=True)  # positive = improved
    probe_error = Column(Text, nullable=True)
    check_meta = Column(JSON, nullable=True)
    # Refresh flags
    refresh_suggested = Column(Boolean, default=False)
    refresh_reason = Column(String(200), nullable=True)
    checked_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class IndustryPattern(Base):
    """Records content success/failure/boost patterns for tactic reinforcement.

    pattern_type values:
      - success: content was indexed or rank improved
      - failure: content was not indexed or rank declined
      - boost: tactic version proven effective (rank improved)
    """
    __tablename__ = "industry_patterns"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), nullable=True, index=True)
    content_id = Column(UUID_TYPE, nullable=False, index=True)
    publish_url = Column(String(1000), nullable=False)
    platform = Column(String(100), default="")
    pattern_type = Column(
        String(20), nullable=False, index=True
    )  # success | failure | boost
    tactics_version = Column(String(50), default="")
    rank_position = Column(Integer, nullable=True)
    rank_change = Column(Integer, nullable=True)
    details = Column(JSON, nullable=True)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
