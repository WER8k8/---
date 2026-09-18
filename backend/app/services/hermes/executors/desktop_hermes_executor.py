# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Desktop Hermes 外层执行器 — DSH 组装进任务图 + AEOS 全域蓝图落地。

capability:
    desktop_hermes.assemble   意图 → 技能召回 → 真 planner 出图
    desktop_hermes.aeos       八大子系统状态（代码面 + invoke 路径）
    desktop_hermes.aeos_invoke 子系统真业务调用 / 全量体检
    desktop_hermes.feedback   莫比乌斯经验环标记
    desktop_hermes.scenes     四航道场景库
    desktop_hermes.status     DSH/蓝图里程碑状态
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from app.schemas.hermes_orchestration import ExecutorResult, TaskNode

from .base import BaseExecutor, ExecutorContext, ExecutorRegistry

logger = logging.getLogger(__name__)

_CAPS = {
    "desktop_hermes.assemble": {
        "desc": "DSH 外层组装：意图+技能 → Hermes 任务图",
        "input": ["intent", "payload?", "tenant_id?"],
        "output": ["plan_id", "nodes", "skill_refs"],
        "needs_approval": False,
    },
    "desktop_hermes.aeos": {
        "desc": "AEOS 八大子系统状态",
        "input": [],
        "output": ["ready_count", "subsystems"],
    },
    "desktop_hermes.aeos_invoke": {
        "desc": "AEOS 子系统业务调用（全量或单系统）",
        "input": ["subsystem_id?", "tenant_id?"],
        "output": ["ok", "invoke_ok", "results"],
        "needs_approval": False,
    },
    "desktop_hermes.feedback": {
        "desc": "莫比乌斯经验环标记",
        "input": ["intent", "success", "note?"],
        "output": ["ok", "skills"],
        "needs_approval": False,
    },
    "desktop_hermes.scenes": {
        "desc": "四航道 + AEOS/机器人场景库",
        "input": [],
        "output": ["scenes", "skills"],
    },
    "desktop_hermes.status": {
        "desc": "DSH 与蓝图里程碑状态",
        "input": [],
        "output": ["name", "milestones", "l1_templates"],
    },
}


class DesktopHermesExecutor(BaseExecutor):
    @classmethod
    def get_executor_name(cls) -> str:
        return "desktop_hermes"

    @classmethod
    def get_capabilities(cls) -> Dict[str, Dict[str, Any]]:
        return dict(_CAPS)

    async def run(self, node: TaskNode, context: ExecutorContext) -> ExecutorResult:
        cap = (node.capability or "").strip()
        p = dict(node.input or {})
        try:
            from app.services.desktop_hermes import desktop_hermes
            from app.services.aeos_registry import (
                aeos_full_invoke,
                aeos_invoke_map,
                aeos_invoke_subsystem,
                aeos_registry_report,
            )

            if cap in ("desktop_hermes.aeos",):
                rep = aeos_registry_report()
                return ExecutorResult(
                    node_id=node.id,
                    status="succeeded",
                    output={
                        **rep,
                        "invoke_map": aeos_invoke_map(),
                        "executor": self.get_executor_name(),
                    },
                )
            if cap == "desktop_hermes.aeos_invoke":
                sid = str(p.get("subsystem_id") or "").strip()
                tid = str(p.get("tenant_id") or context.tenant_id or "demo")
                if sid:
                    out = await aeos_invoke_subsystem(sid, db=context.db, tenant_id=tid)
                else:
                    out = await aeos_full_invoke(db=context.db, tenant_id=tid)
                status = "succeeded" if out.get("ok") or out.get("invoke_ok", 0) > 0 else "failed"
                # 全量体检即使部分失败也 succeeded（结果里如实标注），避免把部分真结果当整体失败
                if not sid:
                    status = "succeeded"
                return ExecutorResult(
                    node_id=node.id,
                    status=status,
                    output={**out, "executor": self.get_executor_name()},
                    error=None if status == "succeeded" else str(out.get("error") or "aeos invoke failed"),
                )
            if cap == "desktop_hermes.scenes":
                return ExecutorResult(
                    node_id=node.id,
                    status="succeeded",
                    output={
                        "scenes": desktop_hermes.list_scenes(),
                        "skills": desktop_hermes.list_skills(),
                        "invoke_map": aeos_invoke_map(),
                        "executor": self.get_executor_name(),
                    },
                )
            if cap == "desktop_hermes.status":
                return ExecutorResult(
                    node_id=node.id,
                    status="succeeded",
                    output={**desktop_hermes.status(), "executor": self.get_executor_name()},
                )
            if cap == "desktop_hermes.feedback":
                out = desktop_hermes.mobius_feedback(
                    intent=str(p.get("intent") or ""),
                    success=bool(p.get("success")),
                    note=str(p.get("note") or ""),
                )
                return ExecutorResult(
                    node_id=node.id,
                    status="succeeded",
                    output={**out, "executor": self.get_executor_name()},
                )
            if cap in ("desktop_hermes.assemble", "default"):
                intent = str(p.get("intent") or p.get("message") or "").strip()
                if not intent:
                    return ExecutorResult(node_id=node.id, status="failed", output={}, error="missing intent")
                out = await desktop_hermes.assemble_plan(
                    intent,
                    payload=dict(p.get("payload") or {}),
                    db=context.db,
                    tenant_id=str(p.get("tenant_id") or context.tenant_id or "demo"),
                )
                status = "succeeded" if out.get("ok") else "failed"
                return ExecutorResult(
                    node_id=node.id,
                    status=status,
                    output={**out, "executor": self.get_executor_name()},
                    error=None if out.get("ok") else str(out.get("error") or "assemble failed"),
                )
            return ExecutorResult(node_id=node.id, status="skipped", output={}, error=f"unsupported {cap}")
        except Exception as exc:  # noqa: BLE001
            logger.exception("desktop_hermes failed %s", cap)
            return ExecutorResult(node_id=node.id, status="failed", output={}, error=str(exc)[:300])


ExecutorRegistry.register(DesktopHermesExecutor())
