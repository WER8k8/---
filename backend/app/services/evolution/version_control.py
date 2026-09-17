# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Skill/SOP 版本管理 — 语义化版本 + 状态机。

管理 Skill 和 SOP 的版本生命周期：
  draft → evaluation → canary → approved → production → archived

使用语义化版本号 (major.minor.patch)，支持版本血缘追踪。
"""

from __future__ import annotations

import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.evolution import SkillVersion, SOPVersion

logger = logging.getLogger("uj-admin.evolution.version_control")


# 语义化版本正则
_SEMVER_PATTERN = re.compile(r"^(\d+)\.(\d+)\.(\d+)(?:-[a-zA-Z0-9]+)?$")

# Skill 版本状态机合法跃迁
# 总纲 §1.3 第4条：Draft→评估→Canary→人审→Production。
# 人审通过（canary.review_approval 的 _execute_approved_action）后直接 canary→production；
# approved 中间态保留给需要显式占位的流程。
_SKILL_TRANSITIONS = {
    "draft": {"evaluation", "archived"},
    "evaluation": {"canary", "draft", "archived"},
    "canary": {"approved", "production", "draft", "archived"},
    "approved": {"production", "draft", "archived"},
    "production": {"archived"},
    "archived": set(),
}

# SOP 版本状态机合法跃迁
_SOP_TRANSITIONS = {
    "draft": {"evaluation", "archived"},
    "evaluation": {"canary", "draft", "archived"},
    "canary": {"approved", "production", "draft", "archived"},
    "approved": {"production", "draft", "archived"},
    "production": {"archived"},
    "archived": set(),
}


def _parse_semver(version: str) -> tuple[int, int, int]:
    """解析语义化版本号。"""
    m = _SEMVER_PATTERN.match(version.strip())
    if not m:
        raise ValueError(f"无效的语义化版本号: {version}，期望格式: major.minor.patch")
    return int(m.group(1)), int(m.group(2)), int(m.group(3))


def _bump_major(version: str) -> str:
    """实现 bumpmajor 的功能。
    
    :param version: 参数 version（类型: str）
    :return: 返回 str 结果
    """
    major, _, _ = _parse_semver(version)
    return f"{major + 1}.0.0"


def _bump_minor(version: str) -> str:
    """实现 bumpminor 的功能。
    
    :param version: 参数 version（类型: str）
    :return: 返回 str 结果
    """
    major, minor, _ = _parse_semver(version)
    return f"{major}.{minor + 1}.0"


def _bump_patch(version: str) -> str:
    """实现 bumppatch 的功能。
    
    :param version: 参数 version（类型: str）
    :return: 返回 str 结果
    """
    major, minor, patch = _parse_semver(version)
    return f"{major}.{minor}.{patch + 1}"


class VersionControl:
    """版本管理服务 — 管理 Skill/SOP 版本的生命周期。"""
    def __init__(self, db: Session):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param db: 参数 db
        :return: 返回处理结果。
        """
        self.db = db

    # ──────────────────────────────────────────────
    # Skill 版本管理
    # ──────────────────────────────────────────────
    def create_skill_version(
        self,
        *,
        skill_id: str,
        skill_name: str,
        bump: str = "patch",
        parent_version_id: Optional[str] = None,
        prompt_template: Optional[str] = None,
        parameters: Optional[dict[str, Any]] = None,
        changelog: Optional[str] = None,
        based_on_experience_ids: Optional[list[str]] = None,
    ) -> SkillVersion:
        """创建新的 Skill 版本。

        Args:
            skill_id: Skill 标识
            skill_name: Skill 名称
            bump: 版本升级类型 — major / minor / patch
            parent_version_id: 父版本 ID
            prompt_template: Prompt 模板
            parameters: 运行参数
            changelog: 变更说明
            based_on_experience_ids: 关联的经验条目 ID 列表

        Returns:
            新创建的 SkillVersion 实例
        """
        # 确定新版本号
        latest = self._get_latest_skill_version(skill_id)
        if latest:
            if bump == "major":
                new_version = _bump_major(latest.version)
            elif bump == "minor":
                new_version = _bump_minor(latest.version)
            else:
                new_version = _bump_patch(latest.version)
            parent_version_id = parent_version_id or str(latest.id)
        else:
            new_version = "0.1.0"

        major, minor, patch = _parse_semver(new_version)
        entry = SkillVersion(
            id=str(uuid.uuid4()),
            skill_id=skill_id,
            skill_name=skill_name,
            version=new_version,
            major=major,
            minor=minor,
            patch=patch,
            status="draft",
            prompt_template=prompt_template,
            parameters=parameters or {},
            changelog=changelog,
            based_on_experience_ids=based_on_experience_ids or [],
            parent_version_id=parent_version_id,
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        logger.info(
            "Skill version created: skill=%s version=%s parent=%s",
            skill_id, new_version, parent_version_id,
        )
        return entry

    def transition_skill(
        self,
        version_id: str,
        new_status: str,
        *,
        canary_percentage: Optional[float] = None,
        canary_tenant_ids: Optional[list[str]] = None,
    ) -> SkillVersion:
        """执行 Skill 版本状态跃迁。

        Args:
            version_id: 版本 ID
            new_status: 目标状态
            canary_percentage: 灰度百分比（进入 canary 时设置）
            canary_tenant_ids: 灰度租户列表

        Returns:
            更新后的 SkillVersion

        Raises:
            ValueError: 状态跃迁不合法
        """
        entry = (
            self.db.query(SkillVersion)
            .filter(SkillVersion.id == version_id)
            .first()
        )
        if not entry:
            raise ValueError(f"Skill 版本不存在: {version_id}")

        allowed = _SKILL_TRANSITIONS.get(entry.status, set())
        if new_status not in allowed:
            raise ValueError(
                f"非法状态跃迁: {entry.status} → {new_status}，"
                f"允许的目标: {allowed}"
            )

        entry.status = new_status
        if canary_percentage is not None:
            entry.canary_percentage = max(0.0, min(100.0, canary_percentage))
        if canary_tenant_ids is not None:
            entry.canary_tenant_ids = canary_tenant_ids

        self.db.commit()
        self.db.refresh(entry)
        logger.info(
            "Skill version transitioned: id=%s %s → %s",
            version_id, entry.status, new_status,
        )
        return entry

    def get_skill_versions(
        self,
        skill_id: str,
        *,
        status: Optional[str] = None,
        limit: int = 20,
    ) -> list[SkillVersion]:
        """获取 Skill 的版本列表。"""
        q = self.db.query(SkillVersion).filter(SkillVersion.skill_id == skill_id)
        if status:
            q = q.filter(SkillVersion.status == status)
        return q.order_by(SkillVersion.created_at.desc()).limit(limit).all()

    def get_production_version(self, skill_id: str) -> Optional[SkillVersion]:
        """获取当前生产版本的 Skill。"""
        return (
            self.db.query(SkillVersion)
            .filter(
                SkillVersion.skill_id == skill_id,
                SkillVersion.status == "production",
            )
            .first()
        )

    def get_canary_version(self, skill_id: str) -> Optional[SkillVersion]:
        """获取当前灰度版本的 Skill。"""
        return (
            self.db.query(SkillVersion)
            .filter(
                SkillVersion.skill_id == skill_id,
                SkillVersion.status == "canary",
            )
            .first()
        )

    def _get_latest_skill_version(self, skill_id: str) -> Optional[SkillVersion]:
        """获取最新版本的 Skill（按语义化版本排序）。"""
        return (
            self.db.query(SkillVersion)
            .filter(SkillVersion.skill_id == skill_id)
            .filter(SkillVersion.status != "archived")
            .order_by(
                SkillVersion.major.desc(),
                SkillVersion.minor.desc(),
                SkillVersion.patch.desc(),
            )
            .first()
        )

    # ──────────────────────────────────────────────
    # SOP 版本管理
    # ──────────────────────────────────────────────
    def create_sop_version(
        self,
        *,
        sop_id: str,
        sop_name: str,
        bump: str = "patch",
        parent_version_id: Optional[str] = None,
        steps: Optional[list[dict[str, Any]]] = None,
        decision_tree: Optional[dict[str, Any]] = None,
        exception_handling: Optional[dict[str, Any]] = None,
        changelog: Optional[str] = None,
        based_on_experience_ids: Optional[list[str]] = None,
        linked_skill_version_ids: Optional[list[str]] = None,
    ) -> SOPVersion:
        """创建新的 SOP 版本。"""
        latest = self._get_latest_sop_version(sop_id)
        if latest:
            if bump == "major":
                new_version = _bump_major(latest.version)
            elif bump == "minor":
                new_version = _bump_minor(latest.version)
            else:
                new_version = _bump_patch(latest.version)
            parent_version_id = parent_version_id or str(latest.id)
        else:
            new_version = "0.1.0"

        major, minor, patch = _parse_semver(new_version)
        entry = SOPVersion(
            id=str(uuid.uuid4()),
            sop_id=sop_id,
            sop_name=sop_name,
            version=new_version,
            major=major,
            minor=minor,
            patch=patch,
            status="draft",
            steps=steps or [],
            decision_tree=decision_tree or {},
            exception_handling=exception_handling or {},
            changelog=changelog,
            based_on_experience_ids=based_on_experience_ids or [],
            linked_skill_version_ids=linked_skill_version_ids or [],
            parent_version_id=parent_version_id,
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        logger.info(
            "SOP version created: sop=%s version=%s", sop_id, new_version
        )
        return entry

    def transition_sop(
        self,
        version_id: str,
        new_status: str,
    ) -> SOPVersion:
        """执行 SOP 版本状态跃迁。"""
        entry = (
            self.db.query(SOPVersion)
            .filter(SOPVersion.id == version_id)
            .first()
        )
        if not entry:
            raise ValueError(f"SOP 版本不存在: {version_id}")

        allowed = _SOP_TRANSITIONS.get(entry.status, set())
        if new_status not in allowed:
            raise ValueError(
                f"非法状态跃迁: {entry.status} → {new_status}，"
                f"允许的目标: {allowed}"
            )

        entry.status = new_status
        self.db.commit()
        self.db.refresh(entry)
        logger.info("SOP version transitioned: id=%s → %s", version_id, new_status)
        return entry

    def get_sop_versions(
        self,
        sop_id: str,
        *,
        status: Optional[str] = None,
        limit: int = 20,
    ) -> list[SOPVersion]:
        """获取 SOP 版本列表。"""
        q = self.db.query(SOPVersion).filter(SOPVersion.sop_id == sop_id)
        if status:
            q = q.filter(SOPVersion.status == status)
        return q.order_by(SOPVersion.created_at.desc()).limit(limit).all()

    def get_production_sop_version(self, sop_id: str) -> Optional[SOPVersion]:
        """获取当前生产版本的 SOP。"""
        return (
            self.db.query(SOPVersion)
            .filter(
                SOPVersion.sop_id == sop_id,
                SOPVersion.status == "production",
            )
            .first()
        )

    def _get_latest_sop_version(self, sop_id: str) -> Optional[SOPVersion]:
        """获取最新版本的 SOP。"""
        return (
            self.db.query(SOPVersion)
            .filter(SOPVersion.sop_id == sop_id)
            .filter(SOPVersion.status != "archived")
            .order_by(
                SOPVersion.major.desc(),
                SOPVersion.minor.desc(),
                SOPVersion.patch.desc(),
            )
            .first()
        )

    # ──────────────────────────────────────────────
    # 版本工具
    # ──────────────────────────────────────────────
    @staticmethod
    def parse_version(version: str) -> dict[str, int]:
        """解析版本号为结构化数据。"""
        major, minor, patch = _parse_semver(version)
        return {"major": major, "minor": minor, "patch": patch}

    @staticmethod
    def bump_version(current: str, bump_type: str = "patch") -> str:
        """计算升级后的版本号。"""
        if bump_type == "major":
            return _bump_major(current)
        elif bump_type == "minor":
            return _bump_minor(current)
        return _bump_patch(current)

    @staticmethod
    def compare_versions(a: str, b: str) -> int:
        """比较两个版本号。

        Returns:
            -1 如果 a < b, 0 如果相等, 1 如果 a > b
        """
        a_parts = _parse_semver(a)
        b_parts = _parse_semver(b)
        if a_parts < b_parts:
            return -1
        elif a_parts > b_parts:
            return 1
        return 0
