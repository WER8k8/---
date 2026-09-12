"""跨租户行业模式学习服务 — 行业匿名聚合 + 战术推荐。

功能：
- aggregate_successful_patterns  — 聚合同行业成功模式
- get_industry_benchmarks        — 返回行业平均指标
- share_anonymized_insight       — 匿名存储行业洞察
- get_recommended_tactics        — 返回相似租户的有效战术

数据存储：industry_insights 表（Alembic 迁移 055_industry_insights）。
隐私：所有 insight 存储前脱敏 tenant_id（SHA-256 哈希前 12 位）。
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import Column, DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Session

from app.core.database import Base

logger = logging.getLogger("uj-admin.industry_pattern")

# ═══════════════════════════════════════════════════════════════════════════
# ORM Model
# ═══════════════════════════════════════════════════════════════════════════


class IndustryInsight(Base):
    """行业洞察表 — 存储聚合后的匿名行业洞察。"""
    __tablename__ = "industry_insights"
    id = Column(Integer, primary_key=True, autoincrement=True)
    industry = Column(String(100), nullable=False, index=True, comment="行业分类")
    pattern_type = Column(String(50), nullable=False, index=True, comment="模式类型: tactic / benchmark / content_style / keyword_cluster")
    pattern_data = Column(Text, nullable=False, comment="模式详情 JSON")
    success_score = Column(Float, nullable=False, default=0.0, comment="成功评分 0~1")
    sample_count = Column(Integer, nullable=False, default=0, comment="样本租户数")
    source_tenant_hash = Column(String(64), nullable=True, comment="来源租户 SHA-256 匿名哈希")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


# ═══════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════

def _anonymize_tenant_id(tenant_id: str) -> str:
    """SHA-256 哈希前 12 位 — 不可逆，足够区分但无法反查。"""
    return hashlib.sha256(tenant_id.encode("utf-8")).hexdigest()[:12]


def _now_utc() -> datetime:
    """_now_utc。
    :return: 返回处理结果。
    """
    return datetime.now(timezone.utc)


# ═══════════════════════════════════════════════════════════════════════════
# Service
# ═══════════════════════════════════════════════════════════════════════════


class IndustryInsightService:
    """跨租户行业模式学习服务。"""
    def __init__(self, db: Session):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param db: 参数 db
        :return: 返回处理结果。
        """
        self.db = db

    # ─────────────────────────────────────────
    # 聚合同行业成功模式
    # ─────────────────────────────────────────
    def aggregate_successful_patterns(self, industry: str) -> dict[str, Any]:
        """查询同行业所有模式，按成功评分聚合，返回 Top N 策略。

        Args:
            industry: 行业标识（如 "insulation", "building_materials"）

        Returns:
            {
                "industry": str,
                "patterns": list[dict],  # Top 20 按 success_score DESC
                "total_patterns": int,
                "avg_success_score": float,
            }
        """
        rows = (
            self.db.query(IndustryInsight)
            .filter(IndustryInsight.industry == industry)
            .order_by(IndustryInsight.success_score.desc())
            .limit(50)
            .all()
        )
        patterns: list[dict[str, Any]] = []
        for row in rows:
            try:
                data = json.loads(row.pattern_data) if isinstance(row.pattern_data, str) else row.pattern_data
            except (json.JSONDecodeError, TypeError):
                data = {}
            patterns.append({
                "id": row.id,
                "pattern_type": row.pattern_type,
                "pattern_data": data,
                "success_score": row.success_score,
                "sample_count": row.sample_count,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            })

        avg_score = (
            sum(p["success_score"] for p in patterns) / len(patterns)
            if patterns else 0.0
        )
        return {
            "industry": industry,
            "patterns": patterns[:20],
            "total_patterns": len(patterns),
            "avg_success_score": round(avg_score, 4),
        }

    # ─────────────────────────────────────────
    # 行业基准指标
    # ─────────────────────────────────────────
    def get_industry_benchmarks(self, industry: str) -> dict[str, Any]:
        """返回行业平均指标（从 benchmark 类型模式中聚合）。

        Returns:
            {
                "industry": str,
                "benchmarks": {
                    "avg_inquiry_count": float,
                    "avg_conversion_rate": float,
                    "avg_geo_pass_rate": float,
                    "avg_content_quality_score": float,
                    "top_keyword_categories": list[str],
                    "sample_size": int,
                }
            }
        """
        rows = (
            self.db.query(IndustryInsight)
            .filter(
                IndustryInsight.industry == industry,
                IndustryInsight.pattern_type == "benchmark",
            )
            .all()
        )
        if not rows:
            return {
                "industry": industry,
                "benchmarks": {
                    "avg_inquiry_count": 0.0,
                    "avg_conversion_rate": 0.0,
                    "avg_geo_pass_rate": 0.0,
                    "avg_content_quality_score": 0.0,
                    "top_keyword_categories": [],
                    "sample_size": 0,
                },
                "message": "no_benchmark_data",
            }

        # 聚合所有 benchmark 行的指标
        total_samples = 0
        sum_inquiries = 0.0
        sum_conversion = 0.0
        sum_geo = 0.0
        sum_quality = 0.0
        keyword_cats: dict[str, int] = {}
        for row in rows:
            try:
                data = json.loads(row.pattern_data) if isinstance(row.pattern_data, str) else row.pattern_data
            except (json.JSONDecodeError, TypeError):
                continue
            total_samples += row.sample_count or 0
            sum_inquiries += float(data.get("avg_inquiry_count", 0)) * (row.sample_count or 1)
            sum_conversion += float(data.get("avg_conversion_rate", 0)) * (row.sample_count or 1)
            sum_geo += float(data.get("avg_geo_pass_rate", 0)) * (row.sample_count or 1)
            sum_quality += float(data.get("avg_content_quality_score", 0)) * (row.sample_count or 1)
            for cat in (data.get("top_keyword_categories") or []):
                keyword_cats[cat] = keyword_cats.get(cat, 0) + 1

        n = max(total_samples, 1)
        top_kw = sorted(keyword_cats.items(), key=lambda x: x[1], reverse=True)[:10]
        return {
            "industry": industry,
            "benchmarks": {
                "avg_inquiry_count": round(sum_inquiries / n, 2),
                "avg_conversion_rate": round(sum_conversion / n, 4),
                "avg_geo_pass_rate": round(sum_geo / n, 4),
                "avg_content_quality_score": round(sum_quality / n, 2),
                "top_keyword_categories": [k for k, _ in top_kw],
                "sample_size": total_samples,
            },
        }

    # ─────────────────────────────────────────
    # 匿名分享洞察
    # ─────────────────────────────────────────
    def share_anonymized_insight(
        self,
        tenant_id: str,
        insight: dict[str, Any],
    ) -> dict[str, Any]:
        """存储一条行业洞察，tenant_id 匿名化后存储。

        Args:
            tenant_id: 原始租户 ID（不会存储原始值）
            insight: {
                "industry": str,
                "pattern_type": str,
                "pattern_data": dict,
                "success_score": float,
                "sample_count": int (optional, default 1),
            }

        Returns:
            {"stored": True, "pattern_id": int, "tenant_hash": str}
        """
        industry = insight.get("industry") or ""
        pattern_type = insight.get("pattern_type") or "tactic"
        pattern_data = insight.get("pattern_data") or {}
        success_score = float(insight.get("success_score") or 0)
        sample_count = int(insight.get("sample_count") or 1)
        if not industry:
            return {"stored": False, "error": "missing_industry"}

        tenant_hash = _anonymize_tenant_id(tenant_id)
        # 检查是否已有相同哈希+行业的类似模式（去重）
        existing = (
            self.db.query(IndustryInsight)
            .filter(
                IndustryInsight.industry == industry,
                IndustryInsight.source_tenant_hash == tenant_hash,
                IndustryInsight.pattern_type == pattern_type,
            )
            .first()
        )
        if existing:
            # 更新已有记录（取更高的 success_score）
            if success_score > existing.success_score:
                existing.success_score = success_score
                existing.pattern_data = json.dumps(pattern_data, ensure_ascii=False)
                existing.sample_count = max(existing.sample_count, sample_count)
                existing.updated_at = _now_utc()
                self.db.flush()
            return {"stored": True, "pattern_id": existing.id, "tenant_hash": tenant_hash, "action": "updated"}

        pattern = IndustryInsight(
            industry=industry,
            pattern_type=pattern_type,
            pattern_data=json.dumps(pattern_data, ensure_ascii=False),
            success_score=success_score,
            sample_count=sample_count,
            source_tenant_hash=tenant_hash,
        )
        self.db.add(pattern)
        self.db.flush()
        logger.info(
            "Industry insight stored: industry=%s type=%s score=%.2f hash=%s",
            industry, pattern_type, success_score, tenant_hash,
        )
        return {"stored": True, "pattern_id": pattern.id, "tenant_hash": tenant_hash, "action": "created"}

    # ─────────────────────────────────────────
    # 推荐战术
    # ─────────────────────────────────────────
    def get_recommended_tactics(self, tenant_id: str) -> dict[str, Any]:
        """返回适合该租户的推荐战术。

        策略：
        1. 查找 tenant 所属行业
        2. 查询同行业成功模式（success_score >= 0.6）
        3. 排除 tenant 自己贡献的模式（避免回音壁）
        4. 按 success_score DESC 排序，返回 Top 10

        Returns:
            {
                "tenant_id": str (anonymized),
                "industry": str,
                "tactics": list[dict],
                "total_available": int,
            }
        """
        tenant_hash = _anonymize_tenant_id(tenant_id)
        # 查找 tenant 行业：优先从已有 insight 推断
        tenant_insight = (
            self.db.query(IndustryInsight)
            .filter(IndustryInsight.source_tenant_hash == tenant_hash)
            .first()
        )
        # 尝试从租户表推断行业
        industry = ""
        if tenant_insight:
            industry = tenant_insight.industry

        if not industry:
            try:
                from app.models.tenant import Tenant
                tenant = self.db.query(Tenant).filter(Tenant.id == tenant_id).first()
                if tenant:
                    industry = getattr(tenant, "industry", "") or ""
            except Exception:
                pass

        if not industry:
            return {
                "tenant_id": tenant_hash,
                "industry": "",
                "tactics": [],
                "total_available": 0,
                "message": "industry_not_determined",
            }

        # 查询同行业高分模式（排除自身贡献）
        rows = (
            self.db.query(IndustryInsight)
            .filter(
                IndustryInsight.industry == industry,
                IndustryInsight.success_score >= 0.6,
                IndustryInsight.source_tenant_hash != tenant_hash,
            )
            .order_by(IndustryInsight.success_score.desc())
            .limit(20)
            .all()
        )
        tactics: list[dict[str, Any]] = []
        for row in rows:
            try:
                data = json.loads(row.pattern_data) if isinstance(row.pattern_data, str) else row.pattern_data
            except (json.JSONDecodeError, TypeError):
                data = {}
            tactics.append({
                "pattern_type": row.pattern_type,
                "tactic": data,
                "success_score": row.success_score,
                "sample_count": row.sample_count,
            })

        return {
            "tenant_id": tenant_hash,
            "industry": industry,
            "tactics": tactics[:10],
            "total_available": len(tactics),
        }
