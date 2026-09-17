# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""核心进化引擎 — 编排完整闭环。

流程：
  数据收集 → 经验沉淀 → Skill优化 → SOP优化 → 灰度发布 → 效果验证

每个阶段通过流水线编排，支持单步执行和全闭环运行。
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.evolution import (
    EvolutionTaskRecord,
    ExperienceEntry,
    SkillVersion,
)
from app.services.evolution.canary import CanaryRelease
from app.services.evolution.experience_store import ExperienceStore
from app.services.evolution.version_control import VersionControl

logger = logging.getLogger("uj-admin.evolution.engine")


class EvolutionEngine:
    """进化引擎 — 编排数据收集到效果验证的完整闭环。"""
    def __init__(self, db: Session):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param db: 参数 db
        :return: 返回处理结果。
        """
        self.db = db
        self.experience_store = ExperienceStore(db)
        self.version_control = VersionControl(db)
        self.canary = CanaryRelease(db)

    # ──────────────────────────────────────────────
    # Stage 1: 数据收集
    # ──────────────────────────────────────────────
    def record_task_execution(
        self,
        *,
        task_type: str,
        executor_type: str = "skill",
        executor_id: str,
        success: bool,
        duration_ms: int = 0,
        cost: float = 0.0,
        tokens_used: int = 0,
        tenant_id: Optional[str] = None,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
        input_summary: Optional[str] = None,
        output_summary: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> EvolutionTaskRecord:
        """记录一次任务执行结果。

        这是进化引擎的数据入口，每次 AI 任务执行后调用。

        Args:
            task_type: 任务类型（如 content_generation, seo_analysis）
            executor_type: 执行器类型（skill / agent / workflow）
            executor_id: 执行器标识
            success: 是否成功
            duration_ms: 执行耗时（毫秒）
            cost: 成本（元）
            tokens_used: Token 消耗数
            tenant_id: 租户 ID
            error_code: 错误码
            error_message: 错误信息
            input_summary: 输入摘要
            output_summary: 输出摘要
            metadata: 扩展元数据

        Returns:
            创建的任务执行记录
        """
        record = EvolutionTaskRecord(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            task_type=task_type,
            executor_type=executor_type,
            executor_id=executor_id,
            success=success,
            duration_ms=duration_ms,
            cost=cost,
            tokens_used=tokens_used,
            error_code=error_code,
            error_message=error_message,
            input_summary=input_summary,
            output_summary=output_summary,
            metadata_json=metadata or {},
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        logger.info(
            "Task recorded: type=%s executor=%s/%s success=%s cost=%.4f",
            task_type, executor_type, executor_id, success, cost,
        )
        return record

    # ──────────────────────────────────────────────
    # Stage 2: 经验沉淀
    # ──────────────────────────────────────────────
    def run_experience_extraction(
        self,
        task_type: str,
        *,
        lookback_hours: int = 24,
        min_samples: int = 5,
    ) -> dict[str, Any]:
        """执行经验沉淀阶段。

        从近期任务记录中提取可复用模式，存入经验库。

        Args:
            task_type: 要分析的任务类型
            lookback_hours: 数据回溯窗口
            min_samples: 最小样本数

        Returns:
            提取结果摘要
        """
        experiences = self.experience_store.extract_from_records(
            task_type,
            lookback_hours=lookback_hours,
            min_samples=min_samples,
        )
        created = sum(1 for e in experiences if e.get("action") == "created")
        merged = sum(1 for e in experiences if e.get("action") == "merged")
        result = {
            "stage": "experience_extraction",
            "task_type": task_type,
            "total_extracted": len(experiences),
            "created": created,
            "merged": merged,
            "details": experiences,
        }
        logger.info(
            "Experience extraction complete: task_type=%s, %d created, %d merged",
            task_type, created, merged,
        )
        return result

    # ──────────────────────────────────────────────
    # Stage 3: Skill 优化
    # ──────────────────────────────────────────────
    def run_skill_optimization(
        self,
        *,
        skill_id: str,
        skill_name: str,
        task_type: str,
        bump: str = "patch",
        prompt_template: Optional[str] = None,
        parameters: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """执行 Skill 优化阶段。

        基于经验库自动调整 Prompt/参数，生成新版本。

        Args:
            skill_id: Skill 标识
            skill_name: Skill 名称
            task_type: 关联的任务类型
            bump: 版本升级级别（major/minor/prompt）
            prompt_template: 新 Prompt 模板（可选，自动基于经验生成）
            parameters: 新参数（可选）

        Returns:
            优化结果摘要
        """
        # 获取适用经验
        experiences = self.experience_store.find_applicable(
            task_type,
            unapplied_only=True,
            limit=10,
        )
        if not experiences:
            return {
                "stage": "skill_optimization",
                "status": "skipped",
                "reason": "no_applicable_experiences",
            }

        # 构建变更说明
        exp_ids = [str(e.id) for e in experiences]
        changelog_parts = [f"基于 {len(experiences)} 条经验自动优化："]
        for exp in experiences[:5]:
            changelog_parts.append(f"  - [{exp.pattern_type}] {exp.title} (置信度: {exp.confidence:.2f})")

        # 如果未提供 prompt_template，基于经验构建优化提示
        if prompt_template is None:
            prompt_template = self._build_optimized_prompt(experiences)

        # 创建新版本
        new_version = self.version_control.create_skill_version(
            skill_id=skill_id,
            skill_name=skill_name,
            bump=bump,
            prompt_template=prompt_template,
            parameters=parameters or {},
            changelog="\n".join(changelog_parts),
            based_on_experience_ids=exp_ids,
        )
        # 标记经验为已应用
        for exp in experiences:
            self.experience_store.mark_applied(str(exp.id))

        result = {
            "stage": "skill_optimization",
            "status": "completed",
            "skill_id": skill_id,
            "new_version": new_version.version,
            "version_id": str(new_version.id),
            "experiences_applied": len(exp_ids),
        }
        logger.info(
            "Skill optimized: %s v%s (based on %d experiences)",
            skill_id, new_version.version, len(exp_ids),
        )
        return result

    def _build_optimized_prompt(
        self,
        experiences: list[ExperienceEntry],
    ) -> str:
        """基于经验条目构建优化的 Prompt 模板。

        将成功模式和失败模式转化为 Prompt 优化指令。
        """
        success_patterns = [
            e for e in experiences if e.pattern_type == "success_pattern"
        ]
        failure_patterns = [
            e for e in experiences if e.pattern_type == "failure_pattern"
        ]
        optimization_hints = [
            e for e in experiences if e.pattern_type == "optimization_hint"
        ]
        parts = ["# 进化优化后的 Prompt", ""]
        if success_patterns:
            parts.append("## 坚持的做法（已验证有效）：")
            for p in success_patterns:
                parts.append(f"- {p.description}")
            parts.append("")

        if failure_patterns:
            parts.append("## 需要避免的问题：")
            for p in failure_patterns:
                parts.append(f"- {p.description}")
            parts.append("")

        if optimization_hints:
            parts.append("## 优化建议：")
            for p in optimization_hints:
                parts.append(f"- {p.description}")
            parts.append("")

        return "\n".join(parts)

    # ──────────────────────────────────────────────
    # Stage 4: SOP 优化
    # ──────────────────────────────────────────────
    def run_sop_optimization(
        self,
        *,
        sop_id: str,
        sop_name: str,
        task_type: str,
        bump: str = "patch",
    ) -> dict[str, Any]:
        """执行 SOP 优化阶段。

        基于经验更新标准操作流程。

        Args:
            sop_id: SOP 标识
            sop_name: SOP 名称
            task_type: 关联的任务类型
            bump: 版本升级级别

        Returns:
            优化结果摘要
        """
        experiences = self.experience_store.find_applicable(
            task_type,
            unapplied_only=True,
            limit=10,
        )
        if not experiences:
            return {
                "stage": "sop_optimization",
                "status": "skipped",
                "reason": "no_applicable_experiences",
            }

        # 获取当前生产版本作为基础
        current_sop = self.version_control.get_production_sop_version(sop_id)
        # 基于经验更新步骤
        new_steps = list(current_sop.steps) if current_sop else []
        exp_ids = []
        for exp in experiences:
            exp_ids.append(str(exp.id))
            if exp.pattern_type == "failure_pattern":
                # 为失败模式添加异常处理步骤
                error_codes = exp.pattern_data.get("error_codes", [])
                if error_codes:
                    new_steps.append({
                        "type": "decision",
                        "condition": f"error_code in {error_codes}",
                        "action": f"触发异常处理: {exp.title}",
                        "fallback": "通知人工介入",
                    })
            elif exp.pattern_type == "success_pattern":
                # 为成功模式添加最佳实践步骤
                duration = exp.pattern_data.get("avg_duration_ms", 0)
                new_steps.append({
                    "type": "action",
                    "label": f"最佳实践: {exp.title}",
                    "expected_duration_ms": duration,
                })

        changelog = f"SOP 基于 {len(exp_ids)} 条经验自动优化"
        new_version = self.version_control.create_sop_version(
            sop_id=sop_id,
            sop_name=sop_name,
            bump=bump,
            steps=new_steps,
            changelog=changelog,
            based_on_experience_ids=exp_ids,
        )
        for exp_id in exp_ids:
            self.experience_store.mark_applied(exp_id)

        return {
            "stage": "sop_optimization",
            "status": "completed",
            "sop_id": sop_id,
            "new_version": new_version.version,
            "version_id": str(new_version.id),
            "steps_count": len(new_steps),
        }

    # ──────────────────────────────────────────────
    # Stage 5: 灰度发布
    # ──────────────────────────────────────────────
    def deploy_to_canary(
        self,
        *,
        skill_id: str,
        version_id: str,
        percentage: float = 5.0,
        tenant_ids: Optional[list[str]] = None,
        requester: str = "system",
    ) -> dict[str, Any]:
        """将已批准的版本部署到灰度。

        Args:
            skill_id: Skill 标识
            version_id: 版本 ID
            percentage: 灰度百分比
            tenant_ids: 白名单租户
            requester: 操作人

        Returns:
            部署结果
        """
        # 从 approved → canary
        new_version = self.version_control.transition_skill(
            version_id,
            "canary",
            canary_percentage=percentage,
            canary_tenant_ids=tenant_ids or [],
        )
        return {
            "stage": "canary_deployment",
            "status": "deployed",
            "skill_id": skill_id,
            "version": new_version.version,
            "version_id": version_id,
            "canary_percentage": percentage,
            "canary_tenant_ids": tenant_ids or [],
            "deployed_by": requester,
        }

    def promote_to_production(
        self,
        *,
        skill_id: str,
        version_id: str,
        requester: str = "system",
    ) -> dict[str, Any]:
        """将灰度版本晋升到生产（需审批）。

        自动提交审批请求，等待人工审核。

        Args:
            skill_id: Skill 标识
            version_id: 版本 ID
            requester: 操作人

        Returns:
            审批提交结果
        """
        # 先获取对比数据作为审批依据
        comparison = self.canary.compare_versions(skill_id, lookback_hours=24)
        approval = self.canary.submit_approval(
            target_type="skill_version",
            target_id=version_id,
            action="promote_to_production",
            requester=requester,
            evidence=comparison,
        )
        return {
            "stage": "promotion_request",
            "status": "pending_approval",
            "skill_id": skill_id,
            "version_id": version_id,
            "approval_id": str(approval.id),
            "evidence": comparison,
        }

    # ──────────────────────────────────────────────
    # Stage 6: 效果验证
    # ──────────────────────────────────────────────
    def validate_canary(
        self,
        skill_id: str,
        *,
        lookback_hours: int = 24,
    ) -> dict[str, Any]:
        """验证灰度版本效果 — A/B 对比。

        Args:
            skill_id: Skill 标识
            lookback_hours: 数据回溯窗口

        Returns:
            对比验证结果
        """
        result = self.canary.compare_versions(
            skill_id, lookback_hours=lookback_hours
        )
        # 自动判断是否推荐晋升
        comparison = result.get("comparison", {})
        if comparison:
            result["auto_recommendation"] = {
                "should_promote": comparison.get("success_rate_improved", False)
                and comparison.get("statistically_significant", False),
                "should_rollback": (
                    comparison.get("success_rate_delta", 0) < -0.05
                ),
            }

        return result

    # ──────────────────────────────────────────────
    # 全流程运行
    # ──────────────────────────────────────────────
    def run_full_cycle(
        self,
        *,
        task_type: str,
        skill_id: str,
        skill_name: str,
        lookback_hours: int = 24,
        deploy_canary: bool = False,
        canary_percentage: float = 5.0,
        requester: str = "system",
    ) -> dict[str, Any]:
        """运行完整的进化闭环。

        依次执行：经验沉淀 → Skill优化 → (可选)灰度发布 → 效果验证

        Args:
            task_type: 任务类型
            skill_id: Skill 标识
            skill_name: Skill 名称
            lookback_hours: 数据回溯窗口
            deploy_canary: 是否部署灰度
            canary_percentage: 灰度百分比
            requester: 操作人

        Returns:
            闭环执行结果摘要
        """
        cycle_id = str(uuid.uuid4())[:8]
        started_at = datetime.now(timezone.utc)
        logger.info(
            "[Cycle %s] Starting full evolution cycle: task=%s skill=%s",
            cycle_id, task_type, skill_id,
        )
        results = {
            "cycle_id": cycle_id,
            "task_type": task_type,
            "skill_id": skill_id,
            "started_at": started_at.isoformat(),
            "stages": {},
        }
        # Stage 2: 经验沉淀
        try:
            exp_result = self.run_experience_extraction(
                task_type, lookback_hours=lookback_hours
            )
            results["stages"]["experience_extraction"] = exp_result
            if exp_result["total_extracted"] == 0:
                results["status"] = "completed_no_new_experiences"
                results["ended_at"] = datetime.now(timezone.utc).isoformat()
                return results
        except Exception as exc:
            results["stages"]["experience_extraction"] = {"error": str(exc)}
            results["status"] = "failed_at_experience_extraction"
            results["ended_at"] = datetime.now(timezone.utc).isoformat()
            return results

        # Stage 3: Skill 优化
        try:
            opt_result = self.run_skill_optimization(
                skill_id=skill_id,
                skill_name=skill_name,
                task_type=task_type,
            )
            results["stages"]["skill_optimization"] = opt_result
            if opt_result["status"] == "skipped":
                results["status"] = "completed_no_optimization"
                results["ended_at"] = datetime.now(timezone.utc).isoformat()
                return results

            new_version_id = opt_result["version_id"]
        except Exception as exc:
            results["stages"]["skill_optimization"] = {"error": str(exc)}
            results["status"] = "failed_at_skill_optimization"
            results["ended_at"] = datetime.now(timezone.utc).isoformat()
            return results

        # Stage 5 (optional): 灰度发布
        if deploy_canary:
            try:
                # draft → evaluation → canary
                self.version_control.transition_skill(new_version_id, "evaluation")
                deploy_result = self.deploy_to_canary(
                    skill_id=skill_id,
                    version_id=new_version_id,
                    percentage=canary_percentage,
                    requester=requester,
                )
                results["stages"]["canary_deployment"] = deploy_result
            except Exception as exc:
                results["stages"]["canary_deployment"] = {"error": str(exc)}

        results["status"] = "completed"
        results["ended_at"] = datetime.now(timezone.utc).isoformat()
        logger.info(
            "[Cycle %s] Evolution cycle complete: status=%s",
            cycle_id, results["status"],
        )
        return results

    # ──────────────────────────────────────────────
    # 统计与概览
    # ──────────────────────────────────────────────
    def get_overview(self) -> dict[str, Any]:
        """获取进化引擎整体概览。"""
        total_records = (
            self.db.query(func.count(EvolutionTaskRecord.id)).scalar() or 0
        )
        success_records = (
            self.db.query(func.count(EvolutionTaskRecord.id))
            .filter(EvolutionTaskRecord.success.is_(True))
            .scalar()
            or 0
        )
        total_skills = (
            self.db.query(func.count(func.distinct(SkillVersion.skill_id)))
            .scalar()
            or 0
        )
        production_skills = (
            self.db.query(func.count(func.distinct(SkillVersion.skill_id)))
            .filter(SkillVersion.status == "production")
            .scalar()
            or 0
        )
        canary_skills = (
            self.db.query(func.count(func.distinct(SkillVersion.skill_id)))
            .filter(SkillVersion.status == "canary")
            .scalar()
            or 0
        )
        experience_stats = self.experience_store.get_stats()
        return {
            "data_collection": {
                "total_records": total_records,
                "success_records": success_records,
                "failed_records": total_records - success_records,
                "overall_success_rate": (
                    round(success_records / total_records, 4) if total_records else 0
                ),
            },
            "version_control": {
                "total_skills": total_skills,
                "production_versions": production_skills,
                "canary_versions": canary_skills,
            },
            "experience_store": experience_stats,
            "pipeline_stages": [
                "data_collection",
                "experience_extraction",
                "skill_optimization",
                "sop_optimization",
                "canary_deployment",
                "validation",
            ],
        }
