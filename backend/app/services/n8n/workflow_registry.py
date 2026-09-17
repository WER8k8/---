# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""n8n 工作流注册表。

管理 n8n 工作流的注册、查询、启用/禁用，存储 workflow_id、endpoint、auth_config。
支持内存缓存 + 数据库持久化（通过 HermesPluginInstall 模型）。
"""

from __future__ import annotations

import logging
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

log = logging.getLogger(__name__)


@dataclass
class WorkflowRecord:
    """工作流注册记录。"""
    workflow_id: str
    name: str
    endpoint: str                    # n8n webhook URL，如 https://n8n.example.com/webhook/xxx
    auth_config: dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    description: str = ""
    tags: list[str] = field(default_factory=list)
    # 触发场景标识：product_create / content_publish / lead_created / custom
    trigger_scene: str = "custom"
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_triggered_at: Optional[datetime] = None
    trigger_count: int = 0
    success_count: int = 0
    fail_count: int = 0


class WorkflowRegistry:
    """n8n 工作流注册表。

    内存缓存实现，后续可扩展为数据库持久化。
    线程安全（GIL 保护 dict 操作）。

    用法:
        registry = get_workflow_registry()
        registry.register(WorkflowRecord(
            workflow_id="wf_001",
            name="自动建站",
            endpoint="https://n8n.example.com/webhook/build-site",
            trigger_scene="product_create",
        ))
        record = registry.get("wf_001")
        enabled_workflows = registry.list_enabled()
    """
    _instance: Optional[WorkflowRegistry] = None
    def __init__(self) -> None:
        """__init__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        self._workflows: dict[str, WorkflowRecord] = {}

    @classmethod
    def get_instance(cls) -> WorkflowRegistry:
        """获取单例实例。"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register(self, record: WorkflowRecord) -> WorkflowRecord:
        """注册工作流。

        Args:
            record: 工作流注册记录。

        Returns:
            注册后的记录（含生成的 id）。

        Raises:
            ValueError: workflow_id 已存在。
        """
        if record.workflow_id in self._workflows:
            raise ValueError(f"工作流 {record.workflow_id} 已存在，请先注销或更新")
        self._workflows[record.workflow_id] = record
        log.info("n8n 工作流注册成功: %s (%s)", record.workflow_id, record.name)
        return record

    def update(self, workflow_id: str, **kwargs: Any) -> Optional[WorkflowRecord]:
        """更新工作流配置。

        Args:
            workflow_id: 工作流 ID。
            **kwargs: 要更新的字段。

        Returns:
            更新后的记录，不存在则返回 None。
        """
        record = self._workflows.get(workflow_id)
        if record is None:
            return None
        for key, value in kwargs.items():
            if hasattr(record, key):
                setattr(record, key, value)
        record.updated_at = datetime.now(timezone.utc)
        log.info("n8n 工作流更新: %s", workflow_id)
        return record

    def unregister(self, workflow_id: str) -> bool:
        """注销工作流。

        Args:
            workflow_id: 工作流 ID。

        Returns:
            是否成功注销。
        """
        if workflow_id in self._workflows:
            del self._workflows[workflow_id]
            log.info("n8n 工作流注销: %s", workflow_id)
            return True
        return False

    def get(self, workflow_id: str) -> Optional[WorkflowRecord]:
        """获取工作流记录。

        Args:
            workflow_id: 工作流 ID。

        Returns:
            工作流记录，不存在则返回 None。
        """
        return self._workflows.get(workflow_id)

    def list_all(self) -> list[WorkflowRecord]:
        """列出所有工作流。"""
        return list(self._workflows.values())

    def list_enabled(self) -> list[WorkflowRecord]:
        """列出所有启用的工作流。"""
        return [wf for wf in self._workflows.values() if wf.enabled]

    def list_by_scene(self, trigger_scene: str) -> list[WorkflowRecord]:
        """按触发场景列出工作流。

        Args:
            trigger_scene: 触发场景标识。

        Returns:
            匹配场景的工作流列表。
        """
        return [
            wf for wf in self._workflows.values()
            if wf.trigger_scene == trigger_scene and wf.enabled
        ]

    def set_enabled(self, workflow_id: str, enabled: bool) -> Optional[WorkflowRecord]:
        """启用/禁用工作流。

        Args:
            workflow_id: 工作流 ID。
            enabled: 是否启用。

        Returns:
            更新后的记录，不存在则返回 None。
        """
        record = self._workflows.get(workflow_id)
        if record is None:
            return None
        record.enabled = enabled
        record.updated_at = datetime.now(timezone.utc)
        status = "启用" if enabled else "禁用"
        log.info("n8n 工作流 %s: %s", status, workflow_id)
        return record

    def record_trigger(self, workflow_id: str, success: bool) -> None:
        """记录触发结果。

        Args:
            workflow_id: 工作流 ID。
            success: 是否成功。
        """
        record = self._workflows.get(workflow_id)
        if record is None:
            return
        record.last_triggered_at = datetime.now(timezone.utc)
        record.trigger_count += 1
        if success:
            record.success_count += 1
        else:
            record.fail_count += 1

    def get_stats(self) -> dict[str, Any]:
        """获取注册表统计信息。"""
        total = len(self._workflows)
        enabled = sum(1 for wf in self._workflows.values() if wf.enabled)
        total_triggers = sum(wf.trigger_count for wf in self._workflows.values())
        total_success = sum(wf.success_count for wf in self._workflows.values())
        return {
            "total": total,
            "enabled": enabled,
            "disabled": total - enabled,
            "total_triggers": total_triggers,
            "total_success": total_success,
            "total_fail": total_triggers - total_success,
        }


def get_workflow_registry() -> WorkflowRegistry:
    """获取 WorkflowRegistry 单例。"""
    return WorkflowRegistry.get_instance()


# ──────────────────────────────────────────────
# 内建（built-in）工作流种子
# ──────────────────────────────────────────────
# 打通"建站完成 → n8n 出站通知"链路：hermes_task_bridge._notify_site_built 会
# trigger_n8n_workflow.delay("site_built_notify", payload)。此前该工作流从未注册，
# 触发必抛 ValueError("未注册") 被桥 except 静默吞掉 —— 出站通知实际永不发生。
# 这里幂等注册，使 web 与 Celery worker 进程都能解析到该工作流。
#
# 配置（env，均可覆盖）：
#   N8N_SITE_BUILT_WEBHOOK_URL  : n8n webhook 地址；留空则 endpoint=""（禁用态下不触发）
#   N8N_SITE_BUILT_ENABLED      : "true"/"false"（默认 false —— 不误触不存在的端点）
#   N8N_SITE_BUILT_AUTH_HEADER  : 可选，形如 "X-Api-Key: xxx"（按第一个冒号拆 header/value）
def _ensure_one_workflow(
    registry: "WorkflowRegistry",
    *,
    workflow_id: str,
    name: str,
    trigger_scene: str,
    url_env: str,
    enabled_env: str,
    auth_env: str,
    description: str,
    tags: list[str],
) -> None:
    """注册单个内建工作流（幂等：已存在则跳过，不覆盖运维运行时改动）。

    注意：每个工作流**独立判断**是否已存在。早期实现用"site_built_notify 存在就
    return"的单一提前返回，会导致后续新增的内建工作流永远注册不上。
    """
    if registry.get(workflow_id) is not None:
        return

    endpoint = (os.environ.get(url_env) or "").strip()
    raw_enabled = os.environ.get(enabled_env)
    # §12 激活：dev/test 环境下，只要配置了 webhook URL 且未显式禁用，就默认启用，
    # 避免内建工作流被静默跳过（此前默认 false 导致出站通知永不发生）。生产仍须显式 opt-in。
    if raw_enabled is None:
        import os as _os
        _env = _os.environ.get("ENVIRONMENT", "development").lower()
        enabled = bool(endpoint) and _env in ("development", "test", "dev")
    else:
        enabled = raw_enabled.strip().lower() == "true"
    auth_raw = (os.environ.get(auth_env) or "").strip()
    auth_config: dict[str, Any] = {}
    if auth_raw and ":" in auth_raw:
        hname, _, hval = auth_raw.partition(":")
        auth_config = {
            "auth_type": "header",
            "header_name": hname.strip(),
            "header_value": hval.strip(),
        }

    registry.register(
        WorkflowRecord(
            workflow_id=workflow_id,
            name=name,
            endpoint=endpoint,
            auth_config=auth_config,
            enabled=enabled,
            trigger_scene=trigger_scene,
            description=description,
            tags=tags,
        )
    )
    log.info(
        "n8n 内建工作流 %s 已注册 (enabled=%s, endpoint_set=%s)",
        workflow_id, enabled, bool(endpoint),
    )


def ensure_builtin_workflows() -> None:
    """幂等注册内建工作流（web / worker 进程各自首次触发时调用一次）。"""
    registry = get_workflow_registry()

    _ensure_one_workflow(
        registry,
        workflow_id="site_built_notify",
        name="站点建成出站通知",
        trigger_scene="site_built",
        url_env="N8N_SITE_BUILT_WEBHOOK_URL",
        enabled_env="N8N_SITE_BUILT_ENABLED",
        auth_env="N8N_SITE_BUILT_AUTH_HEADER",
        description=(
            "建站任务完成（ai_site_build/site_build）后由 hermes_task_bridge 触发的出站通知："
            "通知 n8n 分发到用户渠道。"
        ),
        tags=["builtin", "site_build", "outbound"],
    )

    _ensure_one_workflow(
        registry,
        workflow_id="content_publish_dispatch",
        name="内容发布多渠道路由",
        trigger_scene="content_publish",
        url_env="N8N_CONTENT_PUBLISH_WEBHOOK_URL",
        enabled_env="N8N_CONTENT_PUBLISH_ENABLED",
        auth_env="N8N_CONTENT_PUBLISH_AUTH_HEADER",
        description=(
            "DeerFlow seo_publish / multi_channel_publish 真实发布成功后触发："
            "把已发布内容经 n8n 分发到外部渠道，打通『发布→分发』末段。"
        ),
        tags=["builtin", "publish", "multi_channel", "outbound"],
    )
