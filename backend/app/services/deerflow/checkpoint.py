# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""DeerFlow 断点管理器。

负责保存和恢复任务的执行状态（checkpoint）。
Checkpoint 数据保存到 DeerFlowJob.payload_json 的 JSONB 字段中。
支持增量保存和快照回滚。
"""

from __future__ import annotations

import copy
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.deerflow_job import DeerflowJob

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Checkpoint 数据结构
# ---------------------------------------------------------------------------

@dataclass
class Checkpoint:
    """执行断点数据。"""
    job_id: str
    version: int = 1
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    plan: Optional[dict[str, Any]] = None
    subtask_results: dict[str, dict[str, Any]] = field(default_factory=dict)
    review: Optional[dict[str, Any]] = None
    current_batch_index: int = 0
    current_subtask_index: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    def to_dict(self) -> dict[str, Any]:
        """to_dict。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return {
            "job_id": self.job_id,
            "version": self.version,
            "created_at": self.created_at,
            "plan": self.plan,
            "subtask_results": self.subtask_results,
            "review": self.review,
            "current_batch_index": self.current_batch_index,
            "current_subtask_index": self.current_subtask_index,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Checkpoint":
        """from_dict。

        参数说明：
        :param cls: 参数 cls
        :param data: 参数 data
        :return: 返回处理结果。
        """
        return cls(
            job_id=data.get("job_id", ""),
            version=data.get("version", 1),
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
            plan=data.get("plan"),
            subtask_results=data.get("subtask_results", {}),
            review=data.get("review"),
            current_batch_index=data.get("current_batch_index", 0),
            current_subtask_index=data.get("current_subtask_index", 0),
            metadata=data.get("metadata", {}),
        )


# ---------------------------------------------------------------------------
# Checkpoint 快照（用于回滚）
# ---------------------------------------------------------------------------

@dataclass
class CheckpointSnapshot:
    """Checkpoint 快照，用于回滚到历史状态。 """
    checkpoint: Checkpoint
    snapshot_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    reason: str = ""
    def to_dict(self) -> dict[str, Any]:
        """to_dict。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return {
            "checkpoint": self.checkpoint.to_dict(),
            "snapshot_at": self.snapshot_at,
            "reason": self.reason,
        }


# ---------------------------------------------------------------------------
# 断点管理器
# ---------------------------------------------------------------------------

class CheckpointManager:
    """断点管理器。

    管理任务执行过程中的状态保存和恢复。
    Checkpoint 数据存储在 DeerFlowJob.payload_json 中（对应 PostgreSQL JSONB 列）。
    快照历史存储在 metadata.snapshots 中（最多保留 MAX_SNAPSHOTS 个）。
    """
    MAX_SNAPSHOTS = 10
    CHECKPOINT_KEY = "checkpoint"
    SNAPSHOTS_KEY = "snapshots"
    def __init__(self, db: Session, job: DeerflowJob):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param db: 参数 db
        :param job: 参数 job
        :return: 返回处理结果。
        """
        self.db = db
        self.job = job

    # ------------------------------------------------------------------
    # 保存
    # ------------------------------------------------------------------
    def save(self, checkpoint: Checkpoint) -> None:
        """保存 checkpoint 到数据库。

        以 JSON 形式写入 payload_json 的 checkpoint 键下。
        每次保存前创建快照（用于后续回滚）。
        """
        # 1. 创建当前 checkpoint 的快照（增量保存）
        self._create_snapshot(
            checkpoint,
            reason=f"save_v{checkpoint.version}"
        )
        # 2. 更新 checkpoint 版本号
        checkpoint.version += 1
        checkpoint.created_at = datetime.now(timezone.utc).isoformat()
        # 3. 写入数据库
        self._write_checkpoint(checkpoint)
        logger.debug(
            "Checkpoint saved: job=%s version=%d",
            self.job.id, checkpoint.version,
        )

    def save_subtask_progress(
        self,
        subtask_id: str,
        result: dict[str, Any],
        *,
        batch_index: int = -1,
        subtask_index: int = -1,
    ) -> None:
        """保存单个子任务的执行进度（增量更新）。"""
        checkpoint = self.load() or Checkpoint(job_id=str(self.job.id))
        # 更新子任务结果
        checkpoint.subtask_results[subtask_id] = {
            **result,
            "saved_at": datetime.now(timezone.utc).isoformat(),
        }
        # 更新进度索引
        if batch_index >= 0:
            checkpoint.current_batch_index = batch_index
        if subtask_index >= 0:
            checkpoint.current_subtask_index = subtask_index

        # 写入
        self._write_checkpoint(checkpoint)
        logger.debug(
            "Subtask progress saved: job=%s subtask=%s batch=%d index=%d",
            self.job.id, subtask_id, batch_index, subtask_index,
        )

    def save_plan(self, plan_data: dict[str, Any]) -> None:
        """保存执行计划。"""
        checkpoint = self.load() or Checkpoint(job_id=str(self.job.id))
        checkpoint.plan = plan_data
        self._write_checkpoint(checkpoint)
        logger.debug("Plan saved to checkpoint: job=%s", self.job.id)

    def save_review(self, review_data: dict[str, Any]) -> None:
        """保存审核结果。"""
        checkpoint = self.load() or Checkpoint(job_id=str(self.job.id))
        checkpoint.review = review_data
        self._write_checkpoint(checkpoint)
        logger.debug("Review saved to checkpoint: job=%s", self.job.id)

    # ------------------------------------------------------------------
    # 加载
    # ------------------------------------------------------------------
    def load(self) -> Optional[Checkpoint]:
        """加载最新的 checkpoint。"""
        payload = self._read_payload()
        checkpoint_data = payload.get(self.CHECKPOINT_KEY)
        if checkpoint_data:
            return Checkpoint.from_dict(checkpoint_data)
        return None

    def load_latest_subtask_result(self) -> Optional[dict[str, Any]]:
        """加载最新的子任务执行结果。"""
        checkpoint = self.load()
        if not checkpoint or not checkpoint.subtask_results:
            return None
        # 按 saved_at 排序取最新
        results = list(checkpoint.subtask_results.values())
        results.sort(key=lambda r: r.get("saved_at", ""), reverse=True)
        return results[0] if results else None

    # ------------------------------------------------------------------
    # 恢复
    # ------------------------------------------------------------------
    def can_resume(self) -> bool:
        """检查是否可以恢复执行。"""
        checkpoint = self.load()
        if not checkpoint:
            return False
        # 有计划且未全部完成
        if checkpoint.plan and checkpoint.subtask_results:
            total = len(checkpoint.plan.get("subtasks", []))
            completed = len(checkpoint.subtask_results)
            return completed < total
        return checkpoint is not None and checkpoint.plan is not None

    def get_resume_point(self) -> tuple[int, int]:
        """获取恢复点 (batch_index, subtask_index)。"""
        checkpoint = self.load()
        if not checkpoint:
            return (0, 0)
        return (checkpoint.current_batch_index, checkpoint.current_subtask_index)

    def get_pending_subtasks(self) -> list[str]:
        """获取尚未完成的子任务 ID 列表。"""
        checkpoint = self.load()
        if not checkpoint or not checkpoint.plan:
            return []

        all_subtask_ids = [
            st["id"] for st in checkpoint.plan.get("subtasks", [])
        ]
        completed_ids = set(checkpoint.subtask_results.keys())
        return [sid for sid in all_subtask_ids if sid not in completed_ids]

    # ------------------------------------------------------------------
    # 快照与回滚
    # ------------------------------------------------------------------
    def _create_snapshot(self, checkpoint: Checkpoint, reason: str = "") -> None:
        """创建 checkpoint 快照。"""
        payload = self._read_payload()
        snapshots = payload.get(self.SNAPSHOTS_KEY, [])
        snapshot = CheckpointSnapshot(
            checkpoint=copy.deepcopy(checkpoint),
            reason=reason,
        )
        snapshots.append(snapshot.to_dict())
        # 限制快照数量
        if len(snapshots) > self.MAX_SNAPSHOTS:
            snapshots = snapshots[-self.MAX_SNAPSHOTS:]

        payload[self.SNAPSHOTS_KEY] = snapshots
        self._write_payload(payload)

    def rollback(self, steps: int = 1) -> Optional[Checkpoint]:
        """回滚到之前的快照。

        Args:
            steps: 回滚步数（1 = 回滚到上一个快照）

        Returns:
            回滚后的 Checkpoint，如果没有足够快照则返回 None
        """
        payload = self._read_payload()
        snapshots = payload.get(self.SNAPSHOTS_KEY, [])
        if len(snapshots) < steps:
            logger.warning(
                "Not enough snapshots to rollback: job=%s needed=%d available=%d",
                self.job.id, steps, len(snapshots),
            )
            return None

        target_snapshot = snapshots[-steps]
        restored_checkpoint = Checkpoint.from_dict(target_snapshot["checkpoint"])
        # 移除被回滚的快照
        payload[self.SNAPSHOTS_KEY] = snapshots[:-steps]
        self._write_payload(payload)
        # 将恢复后的 checkpoint 写入当前
        self._write_checkpoint(restored_checkpoint)
        logger.info(
            "Checkpoint rolled back: job=%s steps=%d reason=%s",
            self.job.id, steps, target_snapshot.get("reason", ""),
        )
        return restored_checkpoint

    def list_snapshots(self) -> list[dict[str, Any]]:
        """列出所有可用的快照。"""
        payload = self._read_payload()
        snapshots = payload.get(self.SNAPSHOTS_KEY, [])
        return [
            {
                "snapshot_at": s.get("snapshot_at"),
                "reason": s.get("reason", ""),
                "version": s.get("checkpoint", {}).get("version", 0),
                "batch_index": s.get("checkpoint", {}).get("current_batch_index", 0),
                "subtask_index": s.get("checkpoint", {}).get("current_subtask_index", 0),
            }
            for s in snapshots
        ]

    # ------------------------------------------------------------------
    # 清理
    # ------------------------------------------------------------------
    def clear(self) -> None:
        """清除所有 checkpoint 和快照数据。"""
        payload = self._read_payload()
        payload.pop(self.CHECKPOINT_KEY, None)
        payload.pop(self.SNAPSHOTS_KEY, None)
        self._write_payload(payload)
        logger.info("Checkpoint cleared: job=%s", self.job.id)

    def cleanup_old_snapshots(self, keep: int = 3) -> int:
        """清理旧快照，只保留最近 N 个。

        Returns:
            删除的快照数量
        """
        payload = self._read_payload()
        snapshots = payload.get(self.SNAPSHOTS_KEY, [])
        original_count = len(snapshots)
        if original_count > keep:
            payload[self.SNAPSHOTS_KEY] = snapshots[-keep:]
            self._write_payload(payload)
            removed = original_count - keep
            logger.info(
                "Cleaned up old snapshots: job=%s removed=%d kept=%d",
                self.job.id, removed, keep,
            )
            return removed
        return 0

    # ------------------------------------------------------------------
    # 数据库读写辅助
    # ------------------------------------------------------------------
    def _read_payload(self) -> dict[str, Any]:
        """读取 payload_json。"""
        if self.job.payload_json:
            try:
                return json.loads(self.job.payload_json)
            except (json.JSONDecodeError, TypeError):
                logger.warning("Corrupted payload_json: job=%s", self.job.id)
        return {}

    def _write_payload(self, payload: dict[str, Any]) -> None:
        """写入 payload_json 并提交。"""
        self.job.payload_json = json.dumps(payload, ensure_ascii=False)
        self.job.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(self.job)

    def _write_checkpoint(self, checkpoint: Checkpoint) -> None:
        """写入 checkpoint 到 payload。"""
        payload = self._read_payload()
        payload[self.CHECKPOINT_KEY] = checkpoint.to_dict()
        self._write_payload(payload)
