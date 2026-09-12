"""增长工具 — 专属词库条目（行业/品牌/竞品/需求）+ Agent 跑盘记录。"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text

from app.core.database import UUID_TYPE, Base

WORD_CLASSES = ("industry", "brand", "competitor", "demand")


class GrowthKeywordEntry(Base):
    __tablename__ = "growth_keyword_entries"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(UUID_TYPE, nullable=True, index=True)
    keyword = Column(String(500), nullable=False, index=True)
    word_class = Column(String(32), nullable=False, index=True)
    search_volume = Column(Integer, default=0)
    competition = Column(Integer, default=0)
    source = Column(String(100), default="manual")
    notes = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class GrowthAgentRun(Base):
    """智能跑盘任务持久化（全状态 JSON + 索引字段）。"""
    __tablename__ = "growth_agent_runs"
    id = Column(UUID_TYPE, primary_key=True)
    tenant_id = Column(UUID_TYPE, nullable=True, index=True)
    user_id = Column(String(64), nullable=True, index=True)
    workflow = Column(String(64), nullable=False, default="growth_autopilot")
    goal = Column(String(500), nullable=False, default="")
    status = Column(String(32), nullable=False, default="pending", index=True)
    progress = Column(Integer, nullable=False, default=0)
    payload = Column(Text)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    finished_at = Column(DateTime(timezone=True), nullable=True)
