"""DeerFlow 任务规划器。

将复杂任务拆解为可独立执行的子任务，生成执行计划。
规划结果保存到 DeerFlowJob 的 checkpoint 中。
"""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.deerflow_job import DeerflowJob

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 子任务定义
# ---------------------------------------------------------------------------

@dataclass
class SubTask:
    """子任务定义。"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    intent: str = ""  # 对应 Hermes plugin kind 或 Paperclip intent
    agent_ref: str = ""  # 指定执行的 Agent 角色引用
    priority: int = 0  # 数字越小优先级越高
    depends_on: list[str] = field(default_factory=list)  # 依赖的子任务 ID
    parameters: dict[str, Any] = field(default_factory=dict)
    timeout_seconds: int = 300  # 默认 5 分钟超时
    max_retries: int = 2
    def to_dict(self) -> dict[str, Any]:
        """to_dict。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "intent": self.intent,
            "agent_ref": self.agent_ref,
            "priority": self.priority,
            "depends_on": self.depends_on,
            "parameters": self.parameters,
            "timeout_seconds": self.timeout_seconds,
            "max_retries": self.max_retries,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SubTask:
        """from_dict。

        参数说明：
        :param cls: 参数 cls
        :param data: 参数 data
        :return: 返回处理结果。
        """
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# ---------------------------------------------------------------------------
# 执行计划
# ---------------------------------------------------------------------------

@dataclass
class ExecutionPlan:
    """执行计划。"""
    job_id: str
    subtasks: list[SubTask] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    strategy: str = "sequential"  # sequential | parallel | dag
    def to_dict(self) -> dict[str, Any]:
        """to_dict。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return {
            "job_id": self.job_id,
            "subtasks": [st.to_dict() for st in self.subtasks],
            "created_at": self.created_at,
            "strategy": self.strategy,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExecutionPlan":
        """from_dict。

        参数说明：
        :param cls: 参数 cls
        :param data: 参数 data
        :return: 返回处理结果。
        """
        subtasks = [SubTask.from_dict(st) for st in data.get("subtasks", [])]
        return cls(
            job_id=data["job_id"],
            subtasks=subtasks,
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
            strategy=data.get("strategy", "sequential"),
        )

    def get_execution_order(self) -> list[list[SubTask]]:
        """根据依赖关系计算执行批次。

        返回分批次的子任务列表，同一批次内的任务可以并行执行。
        """
        if self.strategy == "sequential":
            return [[st] for st in sorted(self.subtasks, key=lambda s: s.priority)]

        # DAG 拓扑排序
        subtask_map = {st.id: st for st in self.subtasks}
        executed: set[str] = set()
        batches: list[list[SubTask]] = []
        while len(executed) < len(self.subtasks):
            # 找出所有依赖已满足的任务
            ready = [
                st for st in self.subtasks
                if st.id not in executed
                and all(dep in executed for dep in st.depends_on)
            ]
            if not ready:
                # 存在循环依赖，将剩余任务作为最后一批
                remaining = [st for st in self.subtasks if st.id not in executed]
                logger.warning(
                    "Circular dependency detected in plan for job=%s, forcing remaining: %s",
                    self.job_id, [st.id for st in remaining],
                )
                batches.append(remaining)
                break

            batches.append(sorted(ready, key=lambda s: s.priority))
            executed.update(st.id for st in ready)

        return batches


# ---------------------------------------------------------------------------
# 任务规划器
# ---------------------------------------------------------------------------

class TaskPlanner:
    """任务规划器。

    根据任务 intent 和 payload 生成执行计划。
    支持基于规则的任务拆解和基于模板的快速规划。
    """
    # intent -> 子任务模板映射
    _TEMPLATES: dict[str, list[dict[str, Any]]] = {
        "content_marketing": [
            {
                "title": "关键词研究与内容策划",
                "description": "分析目标关键词，制定内容策略",
                "intent": "keyword_research",
                "agent_ref": "marketing/seo-specialist",
                "priority": 0,
            },
            {
                "title": "内容创作",
                "description": "基于关键词研究结果创作内容",
                "intent": "content_creation",
                "agent_ref": "content/writer",
                "priority": 1,
            },
            {
                "title": "SEO 优化与发布",
                "description": "对内容进行 SEO 优化并发布",
                "intent": "seo_publish",
                "agent_ref": "marketing/seo-specialist",
                "priority": 2,
            },
        ],
        "product_launch": [
            {
                "title": "产品页面创建",
                "description": "创建产品详情页",
                "intent": "page_creation",
                "agent_ref": "tech/web-developer",
                "priority": 0,
            },
            {
                "title": "SEO 元数据优化",
                "description": "优化产品页 title/meta/结构化数据",
                "intent": "seo_metadata",
                "agent_ref": "marketing/seo-specialist",
                "priority": 1,
            },
            {
                "title": "多渠道分发",
                "description": "将产品信息分发到各平台",
                "intent": "multi_channel_publish",
                "agent_ref": "marketing/social-media",
                "priority": 2,
            },
        ],
        "outreach_campaign": [
            {
                "title": "目标买家筛选",
                "description": "筛选目标市场潜在买家",
                "intent": "buyer_research",
                "agent_ref": "sales/research-analyst",
                "priority": 0,
            },
            {
                "title": "开发信生成",
                "description": "为每个买家生成个性化开发信",
                "intent": "outreach_letter",
                "agent_ref": "sales/outreach-specialist",
                "priority": 1,
            },
            {
                "title": "发送与跟踪",
                "description": "发送开发信并设置跟踪",
                "intent": "email_dispatch",
                "agent_ref": "sales/outreach-specialist",
                "priority": 2,
            },
        ],
    }
    def __init__(self, db: Session):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param db: 参数 db
        :return: 返回处理结果。
        """
        self.db = db

    def create_plan(
        self,
        job: DeerflowJob,
        *,
        strategy: str = "sequential",
        custom_subtasks: Optional[list[dict[str, Any]]] = None,
    ) -> ExecutionPlan:
        """为任务创建执行计划。

        优先使用 custom_subtasks，否则根据 intent 查找模板。
        如果都没有，生成一个默认的单子任务计划。

        Args:
            job: DeerFlow 任务记录
            strategy: 执行策略 (sequential | parallel | dag)
            custom_subtasks: 自定义子任务列表

        Returns:
            ExecutionPlan 执行计划
        """
        subtask_defs = custom_subtasks or self._TEMPLATES.get(job.intent)
        if subtask_defs:
            subtasks = []
            for i, defn in enumerate(subtask_defs):
                st = SubTask(
                    title=defn.get("title", f"子任务 {i + 1}"),
                    description=defn.get("description", ""),
                    intent=defn.get("intent", job.intent),
                    agent_ref=defn.get("agent_ref", ""),
                    priority=defn.get("priority", i),
                    parameters=defn.get("parameters", {}),
                    timeout_seconds=defn.get("timeout_seconds", 300),
                    max_retries=defn.get("max_retries", 2),
                )
                # 设置依赖关系（DAG 模式）
                if strategy == "dag" and i > 0 and "depends_on" not in defn:
                    st.depends_on = [subtasks[-1].id]
                elif "depends_on" in defn:
                    st.depends_on = defn["depends_on"]
                subtasks.append(st)
        else:
            # 默认单子任务
            subtasks = [
                SubTask(
                    title=f"执行: {job.intent}",
                    description=f"自动生成的默认子任务，intent={job.intent}",
                    intent=job.intent,
                    priority=0,
                )
            ]

        plan = ExecutionPlan(
            job_id=str(job.id),
            subtasks=subtasks,
            strategy=strategy,
        )
        logger.info(
            "Plan created: job=%s subtasks=%d strategy=%s",
            job.id, len(subtasks), strategy,
        )
        return plan

    def save_plan(self, job: DeerflowJob, plan: ExecutionPlan) -> None:
        """将执行计划保存到任务的 checkpoint 中。"""
        checkpoint = self._load_checkpoint(job)
        checkpoint["plan"] = plan.to_dict()
        self._save_checkpoint(job, checkpoint)
        logger.info("Plan saved to checkpoint: job=%s", job.id)

    def load_plan(self, job: DeerflowJob) -> Optional[ExecutionPlan]:
        """从任务 checkpoint 加载执行计划。"""
        checkpoint = self._load_checkpoint(job)
        plan_data = checkpoint.get("plan")
        if plan_data:
            return ExecutionPlan.from_dict(plan_data)
        return None

    # ------------------------------------------------------------------
    # Checkpoint 辅助
    # ------------------------------------------------------------------
    def _load_checkpoint(self, job: DeerflowJob) -> dict[str, Any]:
        """加载任务 checkpoint 数据。"""
        if job.payload_json:
            try:
                data = json.loads(job.payload_json)
                return data.get("checkpoint", {})
            except (json.JSONDecodeError, TypeError):
                pass
        return {}

    def _save_checkpoint(self, job: DeerflowJob, checkpoint: dict[str, Any]) -> None:
        """保存 checkpoint 到任务 payload_json。"""
        payload: dict[str, Any] = {}
        if job.payload_json:
            try:
                payload = json.loads(job.payload_json)
            except (json.JSONDecodeError, TypeError):
                pass
        payload["checkpoint"] = checkpoint
        job.payload_json = json.dumps(payload, ensure_ascii=False)
        self.db.commit()
