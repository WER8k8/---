# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""灰度发布 — Draft → Evaluation → Canary → Approved → Production。

支持按租户/百分比分流，所有进化操作需人工审批才能进入 Production。
"""

from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.evolution import (
    ApprovalRecord,
    CanaryRouteRecord,
    EvolutionTaskRecord,
    SkillVersion,
)

logger = logging.getLogger("uj-admin.evolution.canary")


class CanaryRelease:
    """灰度发布服务 — 管理版本的分流、对比、晋升。"""
    def __init__(self, db: Session):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param db: 参数 db
        :return: 返回处理结果。
        """
        self.db = db

    # ──────────────────────────────────────────────
    # 灰度路由决策
    # ──────────────────────────────────────────────
    def route(
        self,
        *,
        skill_id: str,
        tenant_id: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """决定请求应路由到生产版本还是灰度版本。

        分流优先级：
        1. 租户白名单（canary_tenant_ids）优先命中灰度
        2. 百分比分流（基于 request_id 或 tenant_id 的一致性哈希）

        Args:
            skill_id: Skill 标识
            tenant_id: 租户 ID
            request_id: 请求标识（用于一致性哈希）

        Returns:
            {
                "use_canary": bool,
                "production_version": SkillVersion | None,
                "canary_version": SkillVersion | None,
                "route_reason": str,
            }
        """
        production = (
            self.db.query(SkillVersion)
            .filter(
                SkillVersion.skill_id == skill_id,
                SkillVersion.status == "production",
            )
            .first()
        )
        canary = (
            self.db.query(SkillVersion)
            .filter(
                SkillVersion.skill_id == skill_id,
                SkillVersion.status == "canary",
            )
            .first()
        )
        if not canary:
            return {
                "use_canary": False,
                "production_version": production,
                "canary_version": None,
                "route_reason": "no_active_canary",
            }

        # 1. 租户白名单优先
        canary_tenants = canary.canary_tenant_ids or []
        if tenant_id and tenant_id in canary_tenants:
            self._record_route(skill_id, tenant_id, canary, True, request_id)
            return {
                "use_canary": True,
                "production_version": production,
                "canary_version": canary,
                "route_reason": "tenant_whitelist",
            }

        # 2. 百分比分流
        percentage = canary.canary_percentage or 0.0
        if percentage >= 100.0:
            self._record_route(skill_id, tenant_id, canary, True, request_id)
            return {
                "use_canary": True,
                "production_version": production,
                "canary_version": canary,
                "route_reason": "full_percentage",
            }

        if percentage <= 0.0:
            self._record_route(skill_id, tenant_id, production, False, request_id)
            return {
                "use_canary": False,
                "production_version": production,
                "canary_version": canary,
                "route_reason": "zero_percentage",
            }

        # 一致性哈希：根据 tenant_id 或 request_id 决定
        hash_key = tenant_id or request_id or str(uuid.uuid4())
        hash_value = int(hashlib.md5(hash_key.encode()).hexdigest(), 16)
        bucket = hash_value % 10000  # 0-9999
        threshold = int(percentage * 100)  # 例如 10% → 1000
        use_canary = bucket < threshold
        self._record_route(
            skill_id,
            tenant_id,
            canary if use_canary else production,
            use_canary,
            request_id,
        )
        return {
            "use_canary": use_canary,
            "production_version": production,
            "canary_version": canary,
            "route_reason": f"percentage_{percentage}%",
        }

    def _record_route(
        self,
        skill_id: str,
        tenant_id: Optional[str],
        version: Optional[SkillVersion],
        is_canary: bool,
        request_id: Optional[str],
    ) -> None:
        """记录路由决策（用于效果对比分析）。"""
        record = CanaryRouteRecord(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            skill_id=skill_id,
            routed_version=version.version if version else None,
            routed_version_id=version.id if version else None,
            is_canary=is_canary,
            request_hash=hashlib.sha256(
                (request_id or str(uuid.uuid4())).encode()
            ).hexdigest()[:16] if request_id else None,
        )
        self.db.add(record)
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()

    # ──────────────────────────────────────────────
    # 灰度效果对比
    # ──────────────────────────────────────────────
    def compare_versions(
        self,
        skill_id: str,
        *,
        lookback_hours: int = 24,
    ) -> dict[str, Any]:
        """A/B 对比灰度版本与生产版本的效果。

        对比维度：成功率、平均耗时、平均成本。

        Args:
            skill_id: Skill 标识
            lookback_hours: 数据回溯窗口

        Returns:
            对比结果字典
        """
        from datetime import timedelta
        cutoff = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
        canary = (
            self.db.query(SkillVersion)
            .filter(
                SkillVersion.skill_id == skill_id,
                SkillVersion.status.in_(("canary", "approved")),
            )
            .first()
        )
        production = (
            self.db.query(SkillVersion)
            .filter(
                SkillVersion.skill_id == skill_id,
                SkillVersion.status == "production",
            )
            .first()
        )
        result = {
            "skill_id": skill_id,
            "lookback_hours": lookback_hours,
            "production": None,
            "canary": None,
            "comparison": None,
        }
        # 生产版本指标
        if production:
            result["production"] = self._compute_version_metrics(
                skill_id, production.version, cutoff
            )

        # 灰度版本指标
        if canary:
            result["canary"] = self._compute_version_metrics(
                skill_id, canary.version, cutoff
            )

        # 对比
        if result["production"] and result["canary"]:
            p_succ = result["production"]["success_rate"] or 0
            c_succ = result["canary"]["success_rate"] or 0
            p_dur = result["production"]["avg_duration_ms"] or 0
            c_dur = result["canary"]["avg_duration_ms"] or 0
            result["comparison"] = {
                "success_rate_delta": round(c_succ - p_succ, 4),
                "success_rate_improved": c_succ > p_succ,
                "duration_delta_ms": int(c_dur - p_dur),
                "duration_improved": c_dur < p_dur if c_dur and p_dur else None,
                # 灰度版本样本数需足够才有统计意义
                "statistically_significant": (
                    (result["canary"]["total_invocations"] or 0) >= 20
                ),
                "recommendation": _recommend_action(p_succ, c_succ, result["canary"]),
            }

        return result

    def _compute_version_metrics(
        self,
        skill_id: str,
        version: str,
        cutoff: datetime,
    ) -> dict[str, Any]:
        """计算指定版本的运行指标。"""
        rows = (
            self.db.query(EvolutionTaskRecord)
            .filter(
                EvolutionTaskRecord.executor_id == skill_id,
                EvolutionTaskRecord.created_at >= cutoff,
            )
            .all()
        )
        if not rows:
            return {
                "version": version,
                "total_invocations": 0,
                "success_rate": None,
                "avg_duration_ms": None,
                "avg_cost": None,
            }

        total = len(rows)
        successes = sum(1 for r in rows if r.success)
        avg_duration = sum(r.duration_ms for r in rows) / total
        avg_cost = sum(r.cost for r in rows) / total
        return {
            "version": version,
            "total_invocations": total,
            "success_rate": round(successes / total, 4),
            "avg_duration_ms": round(avg_duration),
            "avg_cost": round(avg_cost, 6),
        }

    # ──────────────────────────────────────────────
    # 审批流程
    # ──────────────────────────────────────────────
    def submit_approval(
        self,
        *,
        target_type: str,
        target_id: str,
        action: str,
        requester: str,
        evidence: Optional[dict[str, Any]] = None,
    ) -> ApprovalRecord:
        """提交审批请求。

        Args:
            target_type: skill_version / sop_version
            target_id: 目标版本 ID
            action: promote_to_production / abort_canary
            requester: 提交人
            evidence: 审批依据数据

        Returns:
            创建的审批记录
        """
        record = ApprovalRecord(
            id=str(uuid.uuid4()),
            target_type=target_type,
            target_id=target_id,
            action=action,
            status="pending",
            requester=requester,
            evidence=evidence or {},
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        logger.info(
            "Approval submitted: %s %s by %s",
            target_type, action, requester,
        )
        return record

    def review_approval(
        self,
        approval_id: str,
        *,
        reviewer: str,
        approved: bool,
        comment: Optional[str] = None,
        version_control: Any = None,
    ) -> ApprovalRecord:
        """审批审批请求。

        Args:
            approval_id: 审批记录 ID
            reviewer: 审批人
            approved: 是否批准
            comment: 审批意见
            version_control: VersionControl 实例（用于执行状态跃迁）

        Returns:
            更新后的审批记录
        """
        record = (
            self.db.query(ApprovalRecord)
            .filter(ApprovalRecord.id == approval_id)
            .first()
        )
        if not record:
            raise ValueError(f"审批记录不存在: {approval_id}")

        if record.status != "pending":
            raise ValueError(f"审批已处理，当前状态: {record.status}")

        record.reviewer = reviewer
        record.review_comment = comment
        record.reviewed_at = datetime.now(timezone.utc)
        if approved:
            record.status = "approved"
            # 执行状态跃迁
            if version_control:
                self._execute_approved_action(record, version_control)
        else:
            record.status = "rejected"
            # 驳回时回退版本状态
            if version_control:
                self._execute_rejection(record, version_control)

        self.db.commit()
        self.db.refresh(record)
        logger.info(
            "Approval reviewed: id=%s by %s → %s",
            approval_id, reviewer, record.status,
        )
        return record

    def _execute_approved_action(
        self,
        record: ApprovalRecord,
        vc: Any,
    ) -> None:
        """执行审批通过后的动作。"""
        if record.action == "promote_to_production":
            if record.target_type == "skill_version":
                # 先将当前生产版本归档
                old_prod = vc.get_production_version(
                    vc.db.query(SkillVersion)
                    .filter(SkillVersion.id == record.target_id)
                    .first()
                    .skill_id
                )
                if old_prod and old_prod.id != record.target_id:
                    vc.transition_skill(old_prod.id, "archived")
                vc.transition_skill(record.target_id, "production")
                logger.info("Skill %s promoted to production", record.target_id)
            elif record.target_type == "sop_version":
                vc.transition_sop(record.target_id, "production")
                logger.info("SOP %s promoted to production", record.target_id)

        elif record.action == "abort_canary":
            if record.target_type == "skill_version":
                vc.transition_skill(record.target_id, "draft")
                logger.info("Skill %s canary aborted → draft", record.target_id)
            elif record.target_type == "sop_version":
                vc.transition_sop(record.target_id, "draft")
                logger.info("SOP %s canary aborted → draft", record.target_id)

    def _execute_rejection(
        self,
        record: ApprovalRecord,
        vc: Any,
    ) -> None:
        """执行审批驳回后的回退。"""
        if record.action == "promote_to_production":
            # 驳回晋升：回到 canary/approved 状态
            if record.target_type == "skill_version":
                vc.transition_skill(record.target_id, "canary")
            elif record.target_type == "sop_version":
                vc.transition_sop(record.target_id, "canary")

    def get_pending_approvals(
        self,
        target_type: Optional[str] = None,
        limit: int = 20,
    ) -> list[ApprovalRecord]:
        """获取待审批列表。"""
        q = self.db.query(ApprovalRecord).filter(
            ApprovalRecord.status == "pending"
        )
        if target_type:
            q = q.filter(ApprovalRecord.target_type == target_type)
        return q.order_by(ApprovalRecord.submitted_at.asc()).limit(limit).all()


def _recommend_action(
    production_success_rate: float,
    canary_success_rate: float,
    canary_metrics: dict[str, Any],
) -> str:
    """基于对比数据给出推荐动作。"""
    canary_invocations = canary_metrics.get("total_invocations", 0)
    if canary_invocations < 20:
        return "continue_canary: 样本数不足，继续灰度收集数据"

    if canary_success_rate > production_success_rate + 0.02:
        return "promote: 灰度版本成功率显著优于生产版本，建议晋升"

    if canary_success_rate < production_success_rate - 0.05:
        return "rollback: 灰度版本成功率明显劣化，建议回滚"

    return "continue_canary: 效果差异不显著，建议继续观察"
