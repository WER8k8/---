# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""GEO / AI Visibility 数据模型 — AI 搜索可见性监控（Phase 6）"""

from __future__ import annotations

import uuid

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from app.core.database import Base, UUID_TYPE
from app.models.soft_delete import SoftDeleteMixin


class AIQuery(SoftDeleteMixin, Base):
    """AI 搜索目标问题。"""
    __tablename__ = "ai_queries"
    id = Column(UUID_TYPE, primary_key=True, default=uuid.uuid4)
    query = Column(String(500), nullable=False, index=True)
    language = Column(String(10), default="en")
    category = Column(String(100), nullable=True)
    target_entity = Column(String(200), nullable=True)  # 品牌/产品名
    competitor_keywords = Column(Text, nullable=True)  # JSON
    active = Column(String(10), nullable=False, default="1")
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())


class AIQueryRun(SoftDeleteMixin, Base):
    """一次 AI 查询运行结果快照。"""
    __tablename__ = "ai_query_runs"
    id = Column(UUID_TYPE, primary_key=True, default=uuid.uuid4)
    query_id = Column(UUID_TYPE, ForeignKey("ai_queries.id"), nullable=True, index=True)
    engine = Column(String(50), nullable=True)  # chatgpt / gemini / perplexity / deepseek ...
    raw_answer = Column(Text, nullable=True)
    entity_appeared = Column(String(10), nullable=True)  # 0/1
    recommended = Column(String(10), nullable=True)  # 0/1
    position = Column(Integer, nullable=True)
    run_at = Column(DateTime(timezone=True), nullable=False, default=func.now())


class AIMention(SoftDeleteMixin, Base):
    """品牌/产品在 AI 回答中的出现记录。"""
    __tablename__ = "ai_mentions"
    id = Column(UUID_TYPE, primary_key=True, default=uuid.uuid4)
    query_id = Column(UUID_TYPE, ForeignKey("ai_queries.id"), nullable=True, index=True)
    run_id = Column(UUID_TYPE, ForeignKey("ai_query_runs.id"), nullable=True, index=True)
    entity = Column(String(200), nullable=False)
    mentioned = Column(String(10), nullable=False, default="1")
    recommended = Column(String(10), nullable=False, default="0")
    snippet = Column(Text, nullable=True)
    occurred_at = Column(DateTime(timezone=True), nullable=False, default=func.now())


class AICitation(SoftDeleteMixin, Base):
    """引用记录（引用公司页面/文档）。"""
    __tablename__ = "ai_citations"
    id = Column(UUID_TYPE, primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID_TYPE, ForeignKey("ai_query_runs.id"), nullable=True, index=True)
    entity = Column(String(200), nullable=True)
    cited_url = Column(String(1000), nullable=True)
    cited_page = Column(String(300), nullable=True)
    relevance_score = Column(Float, nullable=True)
    occurred_at = Column(DateTime(timezone=True), nullable=False, default=func.now())


class CompetitorMention(SoftDeleteMixin, Base):
    """竞争对手出现记录。"""
    __tablename__ = "competitor_mentions"
    id = Column(UUID_TYPE, primary_key=True, default=uuid.uuid4)
    query_id = Column(UUID_TYPE, ForeignKey("ai_queries.id"), nullable=True, index=True)
    run_id = Column(UUID_TYPE, ForeignKey("ai_query_runs.id"), nullable=True, index=True)
    competitor = Column(String(200), nullable=False)
    mentioned = Column(String(10), nullable=False, default="1")
    recommended = Column(String(10), nullable=False, default="0")
    snippet = Column(Text, nullable=True)
    occurred_at = Column(DateTime(timezone=True), nullable=False, default=func.now())


class VisibilityScore(SoftDeleteMixin, Base):
    """GEO 可见性总分。"""
    __tablename__ = "visibility_scores"
    id = Column(UUID_TYPE, primary_key=True, default=uuid.uuid4)
    entity = Column(String(200), nullable=False, index=True)
    score = Column(Integer, nullable=False, default=0)
    mention_count = Column(Integer, nullable=False, default=0)
    recommendation_count = Column(Integer, nullable=False, default=0)
    citation_count = Column(Integer, nullable=False, default=0)
    query_coverage = Column(Integer, nullable=False, default=0)
    competitor_count = Column(Integer, nullable=False, default=0)
    computed_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
