"""GoodJob CRM Executor — 接真实 HTTP 桥（不再返回硬编码假单证）。

⚠️ 本文件此前是**危险 mock**：硬编码了假的卖家抬头、**假银行账号与假 SWIFT**、
   假买家名称、以及用字符串前缀拼接伪造的"翻译"，却报 status="succeeded"。
   一张带假银行账号的 PI 若发给客户是真实业务事故。**上述硬编码已全部移除。**

现在的行为：
    经 `services/goodjob/trade_document_bridge` 走**真实 HTTP 桥**
    （`orchestration/executors/goodjob_executor.py` 的 GoodJobExecutor）：
      · 桥已配置（GOODJOB_BASE_URL）→ 提交单证任务，返回受理句柄
      · 桥未配置 → **明确 failed**，说明缺什么配置（绝不编造假单证）

能力：
    trade.docs / document.generate_pi / document.generate_trade_docs / trade_document.generate
        → submit_document_task（doc_type 走白名单：PI / CI / PL …）

真实桥自带的校验（本插件不绕过）：
    · tenant_id 必填（多租户隔离红线）
    · inquiry_id 必填（结果可回挂）
    · doc_type 白名单
    · items 条数上限
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from app.schemas.hermes_orchestration import ExecutorResult, TaskNode

from .base import BaseExecutor, ExecutorContext, ExecutorRegistry

logger = logging.getLogger(__name__)

_DOC_CAPS = frozenset({
    "trade.docs",
    "document.generate_pi", "generate_pi", "pi_generator",
    "document.generate_trade_docs", "trade_document.generate",
    # P3: 7步履约·商机建档同步 + 单证生成（同走真实单证工作室桥，未配置即失败）
    "crm.sync_stage", "sync_stage",
})

# capability → 默认单证类型（真实桥会做白名单校验）
_CAP_DEFAULT_DOCTYPE = {
    "trade.docs": "PI",
    "document.generate_pi": "PI",
    "generate_pi": "PI",
    "pi_generator": "PI",
    "document.generate_trade_docs": "CI",
    "trade_document.generate": "CI",
}


class GoodJobCrmExecutor(BaseExecutor):
    """GoodJob 履约执行器（真实桥；未配置即明确失败）。"""

    @classmethod
    def get_executor_name(cls) -> str:
        return "goodjob_crm"

    async def run(self, node: TaskNode, context: ExecutorContext) -> ExecutorResult:
        capability = (node.capability or "").lower().strip()
        if capability.startswith("goodjob."):
            capability = capability.split(".", 1)[1]
        params: dict[str, Any] = dict(node.input or {})

        if capability not in _DOC_CAPS:
            return ExecutorResult(
                node_id=node.id,
                status="skipped",
                output={"capability": capability},
                error=(
                    f"goodjob_crm 当前仅支持单证类能力 {sorted(_DOC_CAPS)}；"
                    f"capability={capability!r} 未实现（不返回假数据）"
                ),
            )

        # ① 取真桥；未配置即明确失败
        try:
            from app.orchestration.executors.goodjob_executor import build_goodjob_executor

            executor = build_goodjob_executor()
        except Exception as exc:  # noqa: BLE001
            logger.exception("GoodJobCrm: 桥导入失败")
            return ExecutorResult(
                node_id=node.id, status="failed", output={},
                error=f"bridge_import_failed: {type(exc).__name__}: {exc}",
            )

        if executor is None or not getattr(executor, "enabled", False):
            return ExecutorResult(
                node_id=node.id,
                status="failed",
                output={"capability": capability},
                error=(
                    "goodjob_bridge_disabled: 未配置 GOODJOB_BASE_URL，GoodJob 桥已禁用。"
                    "**不返回假单证**。配置后自动生效。"
                ),
            )

        # ② 组装真实参数（缺 tenant_id / inquiry_id 由真桥抛错，本层不兜造）
        doc_type = str(
            params.get("doc_type") or _CAP_DEFAULT_DOCTYPE.get(capability, "PI")
        ).upper()
        items = params.get("items") or []
        if isinstance(items, dict):
            items = [items]
        inquiry_id = str(
            params.get("inquiry_id") or params.get("inquiry") or node.id
        ).strip()
        options = params.get("options") if isinstance(params.get("options"), dict) else None

        try:
            from app.services.goodjob.trade_document_bridge import submit_document_task

            handle = submit_document_task(
                executor,
                tenant_id=context.tenant_id,
                inquiry_id=inquiry_id,
                doc_type=doc_type,
                items=items,
                options=options,
            )
        except ValueError as exc:
            # 真桥的校验失败（缺 tenant/id、doc_type 非法、条目超限）——原样透出
            return ExecutorResult(
                node_id=node.id,
                status="failed",
                output={"doc_type": doc_type, "inquiry_id": inquiry_id},
                error=f"bridge_validation: {exc}",
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("GoodJobCrm: 提交单证任务失败 node=%s", node.id)
            return ExecutorResult(
                node_id=node.id, status="failed", output={},
                error=f"{type(exc).__name__}: {exc}",
            )

        if handle is None:
            return ExecutorResult(
                node_id=node.id,
                status="failed",
                output={"doc_type": doc_type},
                error="bridge_returned_none: 桥未受理（禁用或上游拒绝），不视为成功",
            )

        return ExecutorResult(
            node_id=node.id,
            status="succeeded",
            output={
                "executor": self.get_executor_name(),
                "doc_type": doc_type,
                "inquiry_id": inquiry_id,
                "handle": handle,
                # 受理 ≠ 单证已生成 —— 需 poll 回查，如实标注
                "note": "任务已受理（handle 为幂等键）；单证产出需经 poll_document_task 回查，不代表已生成",
            },
        )


    @classmethod
    def get_capabilities(cls) -> Dict[str, Dict[str, Any]]:
        return {
            "trade.docs": {
                "desc": "外贸单证提交（PI/CI/PL，走真实 HTTP 桥；未配置即失败）",
                "input": ["doc_type", "items", "inquiry_id", "options"],
                "output": ["handle", "doc_type", "inquiry_id"],
                "cost": {"tokens": 0, "seconds": 120},
                "needs_approval": True,
            },
            "document.generate_pi": {
                "desc": "形式发票 PI 生成（走真实 GoodJob 单证工作室桥；未配置即明确失败，不造单证）",
                "input": ["product_name", "quantity", "unit_price", "buyer_name", "country"],
                "output": ["pi_number", "handle", "note"],
                "cost": {"tokens": 0, "seconds": 120},
                "needs_approval": True,
            },
            "crm.sync_stage": {
                "desc": "外贸 7 步履约·商机建档同步（GoodJob 漏斗阶段归档；走真实单证工作室桥校验，未配置即失败）",
                "input": ["stage", "lead_id"],
                "output": ["stage", "lead_id", "synced_at"],
                "cost": {"tokens": 0, "seconds": 60},
                "needs_approval": False,
            },
        }


ExecutorRegistry.register(GoodJobCrmExecutor())
