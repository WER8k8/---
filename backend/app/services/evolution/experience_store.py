# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""经验存储 — 经验沉淀阶段。

从任务执行记录中提取可复用模式，存入 PostgreSQL JSONB 经验库。
支持经验检索、置信度更新、合并相似经验。
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy import Integer, and_, func, or_
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Session

from app.models.evolution import ExperienceEntry, EvolutionTaskRecord

logger = logging.getLogger("uj-admin.evolution.experience")


# 经验提取的置信度阈值
_CONFIDENCE_THRESHOLD = 0.3
# 最小样本数才提取经验
_MIN_SAMPLE_COUNT = 5
# 高成功率阈值（超过则视为成功模式）
_HIGH_SUCCESS_RATE = 0.85
# 低成功率阈值（低于则视为失败模式）
_LOW_SUCCESS_RATE = 0.50


class ExperienceStore:
    """经验库存储服务 — 管理可复用模式的提取、存储、检索。"""
    def __init__(self, db: Session):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param db: 参数 db
        :return: 返回处理结果。
        """
        self.db = db

    # ──────────────────────────────────────────────
    # 经验提取
    # ──────────────────────────────────────────────
    def extract_from_records(
        self,
        task_type: str,
        *,
        lookback_hours: int = 24,
        min_samples: int = _MIN_SAMPLE_COUNT,
    ) -> list[dict[str, Any]]:
        """从近期任务记录中提取可复用模式。

        Args:
            task_type: 任务类型
            lookback_hours: 回溯时间窗口（小时）
            min_samples: 最小样本数

        Returns:
            新提取的经验条目列表
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
        # 聚合统计：按执行器分组
        stats = (
            self.db.query(
                EvolutionTaskRecord.executor_id,
                EvolutionTaskRecord.executor_type,
                func.count(EvolutionTaskRecord.id).label("total"),
                func.sum(func.cast(EvolutionTaskRecord.success, Integer)).label("successes"),
                func.avg(EvolutionTaskRecord.duration_ms).label("avg_duration"),
                func.avg(EvolutionTaskRecord.cost).label("avg_cost"),
            )
            .filter(
                EvolutionTaskRecord.task_type == task_type,
                EvolutionTaskRecord.created_at >= cutoff,
            )
            .group_by(
                EvolutionTaskRecord.executor_id,
                EvolutionTaskRecord.executor_type,
            )
            .all()
        )
        if not stats:
            logger.debug("No records found for extraction: task_type=%s", task_type)
            return []

        new_experiences = self._extract_experiences_from_stats(
            cutoff, lookback_hours, min_samples, stats, task_type
        )
        logger.info(
            "Extracted %d experiences for task_type=%s (lookback=%dh)",
            len(new_experiences), task_type, lookback_hours,
        )
        return new_experiences

    def _extract_experiences_from_stats(
        self,
        cutoff: Any,
        lookback_hours: int,
        min_samples: int,
        stats: list[Any],
        task_type: str,
    ) -> list[dict[str, Any]]:
        """依据聚合统计提取成功/失败模式经验。"""
        new_experiences: list[dict[str, Any]] = []
        for row in stats:
            total = int(row.total or 0)
            successes = int(row.successes or 0)
            if total < min_samples:
                continue

            success_rate = successes / total
            executor_id = row.executor_id
            executor_type = row.executor_type
            # 提取成功模式
            if success_rate >= _HIGH_SUCCESS_RATE:
                exp = self._build_success_pattern_experience(
                    task_type=task_type,
                    executor_type=executor_type,
                    executor_id=executor_id,
                    success_rate=success_rate,
                    total=total,
                    row=row,
                    lookback_hours=lookback_hours,
                )
                if exp:
                    new_experiences.append(exp)

            # 提取失败模式
            elif success_rate <= _LOW_SUCCESS_RATE:
                exp = self._build_failure_pattern_experience(
                    cutoff=cutoff,
                    task_type=task_type,
                    executor_type=executor_type,
                    executor_id=executor_id,
                    success_rate=success_rate,
                    total=total,
                    lookback_hours=lookback_hours,
                )
                if exp:
                    new_experiences.append(exp)

        return new_experiences

    def _build_success_pattern_experience(
        self,
        *,
        task_type: str,
        executor_type: str,
        executor_id: str,
        success_rate: float,
        total: int,
        row: Any,
        lookback_hours: int,
    ) -> Optional[dict[str, Any]]:
        """构建「高成功率」经验条目。"""
        return self._create_or_update_experience(
            task_type=task_type,
            pattern_type="success_pattern",
            title=f"高成功率模式: {executor_type}/{executor_id}",
            description=(
                f"任务 {task_type} 由 {executor_type}/{executor_id} 执行，"
                f"成功率 {success_rate:.1%}（{total} 次），"
                f"平均耗时 {int(row.avg_duration or 0)}ms，"
                f"平均成本 {float(row.avg_cost or 0):.4f}"
            ),
            confidence=min(0.95, success_rate),
            pattern_data={
                "executor_id": executor_id,
                "executor_type": executor_type,
                "success_rate": round(success_rate, 4),
                "total_invocations": total,
                "avg_duration_ms": int(row.avg_duration or 0),
                "avg_cost": round(float(row.avg_cost or 0), 6),
                "lookback_hours": lookback_hours,
            },
        )

    def _collect_failure_diagnostics(
        self,
        cutoff: Any,
        task_type: str,
        executor_id: str,
    ) -> tuple[list[str], list[dict[str, Any]]]:
        """收集失败记录的错误码与错误样本。"""
        failure_records = (
            self.db.query(EvolutionTaskRecord)
            .filter(
                EvolutionTaskRecord.task_type == task_type,
                EvolutionTaskRecord.executor_id == executor_id,
                EvolutionTaskRecord.success.is_(False),
                EvolutionTaskRecord.created_at >= cutoff,
            )
            .order_by(EvolutionTaskRecord.created_at.desc())
            .limit(10)
            .all()
        )
        error_codes = list(set(
            r.error_code for r in failure_records if r.error_code
        ))
        error_samples = [
            {"code": r.error_code, "msg": (r.error_message or "")[:200]}
            for r in failure_records[:3]
        ]
        return error_codes, error_samples

    def _build_failure_pattern_experience(
        self,
        *,
        cutoff: Any,
        task_type: str,
        executor_type: str,
        executor_id: str,
        success_rate: float,
        total: int,
        lookback_hours: int,
    ) -> Optional[dict[str, Any]]:
        """构建「失败模式告警」经验条目。"""
        error_codes, error_samples = self._collect_failure_diagnostics(
            cutoff, task_type, executor_id,
        )
        return self._create_or_update_experience(
            task_type=task_type,
            pattern_type="failure_pattern",
            title=f"失败模式告警: {executor_type}/{executor_id}",
            description=(
                f"任务 {task_type} 由 {executor_type}/{executor_id} 执行，"
                f"成功率仅 {success_rate:.1%}（{total} 次），"
                f"需排查改进"
            ),
            confidence=min(0.90, 1.0 - success_rate),
            pattern_data={
                "executor_id": executor_id,
                "executor_type": executor_type,
                "success_rate": round(success_rate, 4),
                "total_invocations": total,
                "error_codes": error_codes,
                "error_samples": error_samples,
                "lookback_hours": lookback_hours,
            },
        )

    def _create_or_update_experience(
        self,
        *,
        task_type: str,
        pattern_type: str,
        title: str,
        description: str,
        confidence: float,
        pattern_data: dict[str, Any],
    ) -> Optional[dict[str, Any]]:
        """创建新经验或合并更新已有相似经验。"""
        executor_id = pattern_data.get("executor_id", "")
        existing = (
            self.db.query(ExperienceEntry)
            .filter(
                ExperienceEntry.task_type == task_type,
                ExperienceEntry.pattern_type == pattern_type,
                ExperienceEntry.pattern_data["executor_id"].as_string() == executor_id,
            )
            .order_by(ExperienceEntry.updated_at.desc())
            .first()
        )
        if existing:
            # 合并更新
            existing.occurrence_count += 1
            existing.confidence = min(0.99, (existing.confidence + confidence) / 2)
            existing.description = description
            existing.pattern_data = {
                **existing.pattern_data,
                **pattern_data,
                "merged_at": datetime.now(timezone.utc).isoformat(),
                "merge_count": existing.occurrence_count,
            }
            existing.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(existing)
            logger.debug("Merged experience: id=%s count=%d", existing.id, existing.occurrence_count)
            return {"id": str(existing.id), "action": "merged"}

        entry = ExperienceEntry(
            id=str(uuid.uuid4()),
            task_type=task_type,
            pattern_type=pattern_type,
            title=title,
            description=description,
            pattern_data=pattern_data,
            confidence=confidence,
            occurrence_count=1,
            applied=False,
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        logger.info("New experience created: id=%s type=%s", entry.id, pattern_type)
        return {"id": str(entry.id), "action": "created"}

    # ──────────────────────────────────────────────
    # 经验检索
    # ──────────────────────────────────────────────
    def find_applicable(
        self,
        task_type: str,
        *,
        pattern_type: Optional[str] = None,
        min_confidence: float = _CONFIDENCE_THRESHOLD,
        unapplied_only: bool = True,
        limit: int = 20,
    ) -> list[ExperienceEntry]:
        """检索适用于指定任务类型的经验。

        Args:
            task_type: 任务类型
            pattern_type: 模式类型过滤（可选）
            min_confidence: 最低置信度
            unapplied_only: 仅返回未应用的经验
            limit: 返回数量上限

        Returns:
            经验条目列表
        """
        q = self.db.query(ExperienceEntry).filter(
            ExperienceEntry.task_type == task_type,
            ExperienceEntry.confidence >= min_confidence,
        )
        if pattern_type:
            q = q.filter(ExperienceEntry.pattern_type == pattern_type)
        if unapplied_only:
            q = q.filter(ExperienceEntry.applied.is_(False))

        return q.order_by(ExperienceEntry.confidence.desc()).limit(limit).all()

    def get_stats(self) -> dict[str, Any]:
        """获取经验库统计信息。"""
        total = self.db.query(func.count(ExperienceEntry.id)).scalar() or 0
        unapplied = (
            self.db.query(func.count(ExperienceEntry.id))
            .filter(ExperienceEntry.applied.is_(False))
            .scalar()
            or 0
        )
        by_pattern = (
            self.db.query(
                ExperienceEntry.pattern_type,
                func.count(ExperienceEntry.id),
                func.avg(ExperienceEntry.confidence),
            )
            .group_by(ExperienceEntry.pattern_type)
            .all()
        )
        return {
            "total_experiences": total,
            "unapplied": unapplied,
            "applied": total - unapplied,
            "by_pattern_type": {
                row[0]: {
                    "count": int(row[1]),
                    "avg_confidence": round(float(row[2] or 0), 4),
                }
                for row in by_pattern
            },
        }

    def mark_applied(self, experience_id: str) -> bool:
        """标记经验为已应用。"""
        entry = (
            self.db.query(ExperienceEntry)
            .filter(ExperienceEntry.id == experience_id)
            .first()
        )
        if not entry:
            return False
        entry.applied = True
        entry.applied_at = datetime.now(timezone.utc)
        self.db.commit()
        return True
