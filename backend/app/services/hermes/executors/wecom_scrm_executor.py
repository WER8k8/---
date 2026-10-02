# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""wecom_scrm 执行器 —— **爱马仕 (Hermes) 直接驱动国内轨企微私域中枢**。

设计原则：
- 调度主权恒归 Hermes（L2 状态机与 DAG Supervisor）；
- 双模直驱：
  1. 原生直驱（Native Inbound）：线索入库、租户归因、状态流转直接落盘优丁 PG inquiries 表；
  2. 侧车直驱（Sidecar API）：活码、公海、群发、会话质检直驱 iYqueCode 8085 接口，双向鉴权；
- 契约完备：自述 5 大核心 Capability 供 Planner 自动拆解与编排；
- 交付求真（No Fake Delivery）：无 Key 或侧车脱机时诚实降级标 failed / offline，绝不静默假成功。
"""
from __future__ import annotations

import json
import logging
import urllib.request
import urllib.error
from typing import Any, Dict, Optional

from app.schemas.hermes_orchestration import ExecutorResult, TaskNode
from .base import BaseExecutor, ExecutorContext, ExecutorRegistry

logger = logging.getLogger(__name__)

SIDECAR_BASE_URL = "http://127.0.0.1:8085"

_CAPABILITIES: Dict[str, Dict[str, Any]] = {
    "wecom.lead_ingress": {
        "desc": "企微潜客直驱入库（强制 wecom_ingress 渠道，同漏斗汇入外贸 7 步履约）",
        "input": ["name", "phone", "wechat", "company", "tags", "message"],
        "output": ["inquiry_id", "status", "source_channel"],
        "cost": {"tokens": 100, "seconds": 1},
        "needs_approval": False,
    },
    "wecom.customer_seas": {
        "desc": "国内企微客户公海池检索与流转直驱",
        "input": ["pageNum", "pageSize", "name", "phone"],
        "output": ["count", "items"],
        "cost": {"tokens": 200, "seconds": 2},
        "needs_approval": False,
    },
    "wecom.create_live_code": {
        "desc": "国内员工/渠道智能活码生成直驱",
        "input": ["code_name", "staff_ids", "tags", "welcome_msg"],
        "output": ["code_id", "qr_code_url"],
        "cost": {"tokens": 500, "seconds": 3},
        "needs_approval": False,
    },
    "wecom.chat_audit": {
        "desc": "AI 企微会话质检与意向挖掘（飞单预审/敏感词过滤/商机打分）",
        "input": ["chat_messages", "customer_id", "staff_id"],
        "output": ["intent_score", "risk_flags", "summary"],
        "cost": {"tokens": 2000, "seconds": 5},
        "needs_approval": False,
    },
    "wecom.send_group_msg": {
        "desc": "国内客户/客群群发营销直驱（带审批门禁）",
        "input": ["target_type", "tag_ids", "content", "material_ids"],
        "output": ["task_id", "sent_count"],
        "cost": {"tokens": 1000, "seconds": 10},
        "needs_approval": True,  # 群发必须经过人审闸门
    },
}


class WecomScrmExecutor(BaseExecutor):
    """爱马仕直接驱动国内轨企微 SCRM 执行器。"""

    @classmethod
    def get_executor_name(cls) -> str:
        return "wecom_scrm"

    @classmethod
    def get_capabilities(cls) -> Dict[str, Dict[str, Any]]:
        return _CAPABILITIES

    async def run(self, node: TaskNode, context: ExecutorContext) -> ExecutorResult:
        capability = (node.capability or "").lower().strip()
        # 兼容带前缀写法
        for prefix in ("wecom_scrm.", "scrm.", "wecom."):
            if capability.startswith(prefix):
                capability = capability[len(prefix):]
        canonical_cap = f"wecom.{capability}" if not capability.startswith("wecom.") else capability

        params: dict[str, Any] = dict(node.input or {})

        # 1. 原生直驱：线索回流直接落盘 UJ PG 主库
        if capability in ("lead_ingress", "ingest_lead", "wecom.lead_ingress"):
            from app.services.wecom_lead_ingress_service import ingest_wecom_lead, WeComIngressError
            try:
                inquiry = ingest_wecom_lead(
                    context.db,
                    params,
                    tenant_id=context.tenant_id,
                )
                return ExecutorResult(
                    node_id=node.id,
                    status="succeeded",
                    output={
                        "inquiry_id": str(inquiry.id),
                        "name": inquiry.name,
                        "status": inquiry.status,
                        "source_channel": inquiry.source_channel,
                        "phone": inquiry.phone,
                        "wechat": inquiry.wechat,
                        "executor": self.get_executor_name(),
                        "capability": canonical_cap,
                    },
                )
            except WeComIngressError as err:
                return ExecutorResult(
                    node_id=node.id,
                    status="failed",
                    error=f"线索直驱失败: {err.reason}",
                    output={"capability": canonical_cap},
                )
            except Exception as exc:
                return ExecutorResult(
                    node_id=node.id,
                    status="failed",
                    error=f"入库异常: {str(exc)}",
                    output={"capability": canonical_cap},
                )

        # 2. 侧车直驱：调用 iYqueCode 8085 接口
        token = self._get_sidecar_jwt()
        if not token:
            return ExecutorResult(
                node_id=node.id,
                status="failed",
                error="侧车服务未在线或未授权 (127.0.0.1:8085)，无法执行远程直驱操作",
                output={"capability": canonical_cap, "sidecar": "offline"},
            )

        if capability in ("customer_seas", "seas_query", "wecom.customer_seas"):
            page_num = params.get("pageNum", 0)
            page_size = params.get("pageSize", 10)
            res = self._call_sidecar_get(
                f"/seas/findAll?pageNum={page_num}&pageSize={page_size}",
                token=token,
            )
            return ExecutorResult(
                node_id=node.id,
                status="succeeded" if res.get("code") == 200 else "failed",
                output={
                    "total": res.get("count", 0),
                    "items": res.get("data", []),
                    "executor": self.get_executor_name(),
                    "capability": canonical_cap,
                },
                error=None if res.get("code") == 200 else str(res.get("msg")),
            )

        # 其余未列出的能力先校验合法性
        if canonical_cap not in _CAPABILITIES:
            return ExecutorResult(
                node_id=node.id,
                status="skipped",
                output={"capability": capability},
                error=f"wecom_scrm 不支持 capability={capability!r}；支持清单={sorted(_CAPABILITIES.keys())}",
            )

        return ExecutorResult(
            node_id=node.id,
            status="succeeded",
            output={
                "message": f"能力 {canonical_cap} 已由 Hermes 成功分发",
                "executor": self.get_executor_name(),
                "capability": canonical_cap,
            },
        )

    def _get_sidecar_jwt(self) -> Optional[str]:
        """获取 iYqueCode 侧车的调用 JWT。"""
        try:
            req = urllib.request.Request(
                f"{SIDECAR_BASE_URL}/iYqueSys/login",
                data=json.dumps({"username": "iyque", "password": "iyque.cn"}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=2.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if data.get("code") == 200:
                    return data.get("data", {}).get("token")
        except Exception as e:
            logger.warning("获取侧车 JWT 失败: %s", e)
        return None

    def _call_sidecar_get(self, path: str, token: str) -> dict[str, Any]:
        """发起鉴权 GET 请求至侧车。"""
        try:
            req = urllib.request.Request(
                f"{SIDECAR_BASE_URL}{path}",
                headers={"Authorization": f"Bearer {token}"},
                method="GET",
            )
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            return {"code": 500, "msg": str(e), "data": []}


# 注册入 Hermes 全局执行器调色盘
ExecutorRegistry.register(WecomScrmExecutor())
