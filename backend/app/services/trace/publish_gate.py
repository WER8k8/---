# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Canary 发布门禁（总纲 §1.3 第4条 / §6.6 P3 / E14）。

发布流程：Draft → 评估(Evaluation) → Canary(5/25/50/100% 阶梯，按租户百分比分流)
→ 人审(Approval) → Production。
复用 version_control 状态机 + canary 分流/审批 + engine 效果验证，不另起炉灶。
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.evolution import ApprovalRecord, SkillVersion
from app.services.evolution.canary import CanaryRelease
from app.services.evolution.engine import EvolutionEngine
from app.services.evolution.version_control import VersionControl

logger = logging.getLogger("uj-admin.trace.publish_gate")

# §1.3/§6.6：Canary 阶梯百分比（逐级放量，不得跳级）
CANARY_STEPS = (5.0, 25.0, 50.0, 100.0)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PublishGate:
    """Skill 版本发布门禁 — 编排灰度放量、效果评估、人审晋升。"""
    def __init__(self, db: Session):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param db: 参数 db
        :return: 返回处理结果。
        """
        self.db = db
        self.vc = VersionControl(db)
        self.canary = CanaryRelease(db)
        self.engine = EvolutionEngine(db)

    # ──────────────────────────────────────────────
    # 门禁编排
    # ──────────────────────────────────────────────
    def start_release(
        self,
        *,
        skill_id: str,
        version_id: str,
        canary_percentage: float = CANARY_STEPS[0],
        tenant_ids: Optional[list[str]] = None,
        requester: str = "system",
    ) -> dict[str, Any]:
        """Draft → 评估 → Canary 阶梯第一步。

        校验：canary_percentage 必须在 CANARY_STEPS 阶梯内（不允许任意百分比越级）。
        """
        if canary_percentage not in CANARY_STEPS:
            raise ValueError(
                f"非法灰度百分比: {canary_percentage}，允许阶梯: {list(CANARY_STEPS)}"
            )
        # draft → evaluation → canary
        self.vc.transition_skill(version_id, "evaluation")
        self.vc.transition_skill(
            version_id, "canary",
            canary_percentage=canary_percentage,
            canary_tenant_ids=tenant_ids or [],
        )
        logger.info(
            "release started: skill=%s version=%s canary=%.0f%% by %s",
            skill_id, version_id, canary_percentage, requester,
        )
        return {
            "stage": "canary",
            "skill_id": skill_id,
            "version_id": version_id,
            "canary_percentage": canary_percentage,
            "canary_tenant_ids": tenant_ids or [],
            "requester": requester,
        }

    def route_release(
        self,
        *,
        skill_id: str,
        tenant_id: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """按租户百分比分流（E14：对接 evolution/canary.py 按租户百分比）。"""
        return self.canary.route(
            skill_id=skill_id,
            tenant_id=tenant_id,
            request_id=request_id,
        )

    def scale_canary(
        self,
        *,
        skill_id: str,
        version_id: str,
        next_percentage: float,
        requester: str = "system",
    ) -> dict[str, Any]:
        """Canary 阶梯放量：5 → 25 → 50 → 100（逐级，不得跳级）。"""
        if next_percentage not in CANARY_STEPS:
            raise ValueError(
                f"非法灰度百分比: {next_percentage}，允许阶梯: {list(CANARY_STEPS)}"
            )
        entry = self._get_version(version_id)
        current = float(entry.canary_percentage or 0)
        cur_idx = CANARY_STEPS.index(current) if current in CANARY_STEPS else -1
        next_idx = CANARY_STEPS.index(next_percentage)
        if next_idx <= cur_idx:
            raise ValueError(
                f"Canary 阶梯不得回退/原地: {current}% → {next_percentage}%"
            )
        if next_idx > cur_idx + 1:
            raise ValueError(
                f"Canary 阶梯不得跳级: {current}% → {next_percentage}%（须逐级 5/25/50/100）"
            )
        # 放量只调整灰度百分比，状态仍为 canary（canary→canary 非状态跃迁）
        entry.canary_percentage = next_percentage
        entry.updated_at = _utcnow()
        self.db.commit()
        self.db.refresh(entry)
        logger.info(
            "canary scaled: skill=%s version=%s %.0f%% → %.0f%% by %s",
            skill_id, version_id, current, next_percentage, requester,
        )
        return {
            "stage": "canary",
            "skill_id": skill_id,
            "version_id": version_id,
            "canary_percentage": next_percentage,
            "requester": requester,
        }

    def evaluate(
        self,
        *,
        skill_id: str,
        lookback_hours: int = 24,
    ) -> dict[str, Any]:
        """评估当前灰度效果 → 返回推荐动作（promote / rollback / continue）。"""
        result = self.engine.validate_canary(skill_id, lookback_hours=lookback_hours)
        comparison = result.get("comparison") or {}
        if comparison:
            result["recommendation"] = _recommend(comparison)
        return result

    def request_promotion(
        self,
        *,
        skill_id: str,
        version_id: str,
        requester: str = "system",
        force: bool = False,
    ) -> dict[str, Any]:
        """Canary 满量(100%) 后请求人审晋升 Production。

        force=True 跳过 100% 校验（用于人工介入场景）。
        """
        entry = self._get_version(version_id)
        if entry.status != "canary":
            raise ValueError(f"版本不在 canary 态: {entry.status}")
        if not force and float(entry.canary_percentage or 0) < 100.0:
            raise ValueError(
                f"Canary 未满量（当前 {entry.canary_percentage}%），须 100% 后才能申请晋升"
            )
        comparison = self.canary.compare_versions(skill_id, lookback_hours=24)
        approval = self.canary.submit_approval(
            target_type="skill_version",
            target_id=version_id,
            action="promote_to_production",
            requester=requester,
            evidence=comparison,
        )
        logger.info(
            "promotion requested: skill=%s version=%s approval=%s by %s",
            skill_id, version_id, approval.id, requester,
        )
        return {
            "stage": "approval",
            "skill_id": skill_id,
            "version_id": version_id,
            "approval_id": str(approval.id),
            "status": "pending_approval",
            "evidence": comparison,
        }

    def review_promotion(
        self,
        approval_id: str,
        *,
        reviewer: str,
        approved: bool,
        comment: Optional[str] = None,
    ) -> ApprovalRecord:
        """人审晋升审批。"""
        return self.canary.review_approval(
            approval_id,
            reviewer=reviewer,
            approved=approved,
            comment=comment,
            version_control=self.vc,
        )

    # ──────────────────────────────────────────────
    # 内部
    # ──────────────────────────────────────────────
    def _get_version(self, version_id: str) -> SkillVersion:
        entry = (
            self.db.query(SkillVersion)
            .filter(SkillVersion.id == version_id)
            .first()
        )
        if not entry:
            raise ValueError(f"Skill 版本不存在: {version_id}")
        return entry


def _recommend(comparison: dict[str, Any]) -> str:
    """基于对比数据给出门禁推荐。"""
    if comparison.get("statistically_significant"):
        if comparison.get("success_rate_improved"):
            return "promote: 灰度显著优于生产，建议晋升"
        if comparison.get("success_rate_delta", 0) < -0.05:
            return "rollback: 灰度明显劣化，建议回滚"
    return "continue_canary: 样本不足或差异不显著，继续灰度观察"
