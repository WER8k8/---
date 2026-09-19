# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""EXECUTOR 插槽 · 优丁 CRM 原生直驱（goodjob_crm，无外桥）。

主理人裁定：GoodJob CRM = 本项目能力域；调度主权在 Hermes（D3）。
本适配器 **进程内直驱** `app.services.goodjob.native_fulfillment`，
不发起任何 GOODJOB_BASE_URL / uj-bridge HTTP。

契约（五字段铁律）：submit 校验 TaskPackage 后同步执行原生能力并缓存结果；
poll 按 idempotency_key 返回 ExecutionResult（幂等）。
"""
from __future__ import annotations

import logging
from typing import Any, Mapping

from app.orchestration.interfaces import (
    ExecutionResult,
    ExecutorAdapter,
    SlotArchetype,
    TaskPackage,
)

logger = logging.getLogger(__name__)

_HANDLE_CACHE_LIMIT = 2000

# task_type → native 能力
_TASK_TYPE_MAP = {
    "customer_pool.sync": "crm.sync_lead",
    "trade_document.generate": "document.generate",
    "crm.sync_stage": "crm.sync_stage",
    "document.generate_pi": "document.generate_pi",
}


class NativeCrmExecutor(ExecutorAdapter):
    """优丁 CRM 原生执行器（Hermes 直驱，无外桥）。"""

    archetype = SlotArchetype.EXECUTOR

    def __init__(self) -> None:
        self._results: dict[str, ExecutionResult] = {}

    @property
    def enabled(self) -> bool:
        """原生路径始终启用（本项目 CRM）。"""
        return True

    @staticmethod
    def _validate_package(package: TaskPackage) -> None:
        if not str(package.tenant_id or "").strip():
            raise ValueError("任务包缺 tenant_id（五字段铁律）")
        if not str(package.idempotency_key or "").strip():
            raise ValueError("任务包缺 idempotency_key（五字段铁律）")
        if int(package.lease_ttl) <= 0:
            raise ValueError("任务包 lease_ttl 必须为正整数（五字段铁律）")
        if not str(package.checkpoint or "").strip():
            raise ValueError("任务包缺 checkpoint（五字段铁律）")

    def submit(
        self,
        package: TaskPackage,
        *,
        task_type: str = "trade_document.generate",
        payload: Mapping[str, Any] | None = None,
        db: Any = None,
    ) -> str:
        """接受任务包并**同步**执行优丁原生 CRM；返回句柄（=幂等键）。"""
        self._validate_package(package)
        handle = package.idempotency_key
        if handle in self._results:
            return handle

        from app.services.goodjob import native_fulfillment as native

        payload = dict(payload or {})
        ttype = (task_type or "").strip()
        # 从 payload 推断能力
        cap = str(payload.get("capability") or "").strip()
        if not cap:
            cap = _TASK_TYPE_MAP.get(ttype, "document.generate")

        session = db
        close_after = False
        if session is None:
            try:
                from app.core.database import SessionLocal

                session = SessionLocal()
                close_after = True
            except Exception as exc:  # noqa: BLE001
                self._results[handle] = ExecutionResult(
                    ok=False,
                    idempotency_key=handle,
                    error=f"db_session_failed:{exc}",
                )
                return handle

        try:
            if cap in ("crm.sync_stage", "sync_stage"):
                out = native.sync_fulfillment_stage(
                    tenant_id=package.tenant_id,
                    order_id=str(payload.get("order_id") or payload.get("inquiry_id") or ""),
                    stage=str(payload.get("stage") or "deposit_received"),
                    step_number=int(payload.get("step_number") or 1),
                    params=payload,
                    db=session,
                )
            elif cap in ("crm.sync_lead", "sync_lead"):
                out = native.sync_lead(
                    tenant_id=package.tenant_id,
                    lead_data=payload,
                    db=session,
                )
            elif cap in ("crm.update_opportunity", "update_opportunity"):
                out = native.update_opportunity(
                    opportunity_id=str(payload.get("opportunity_id") or ""),
                    status=str(payload.get("status") or ""),
                    tenant_id=package.tenant_id,
                    db=session,
                )
            else:
                doc_type = str(
                    payload.get("doc_type")
                    or ("PI" if "pi" in cap else "CI" if "ci" in cap else "PI")
                ).upper()
                out = native.generate_trade_document(
                    doc_type=doc_type,
                    tenant_id=package.tenant_id,
                    params=payload,
                    db=session,
                    order_id=str(payload.get("order_id") or "") or None,
                    inquiry_id=str(payload.get("inquiry_id") or "") or None,
                )

            ok = bool(out.get("success"))
            self._results[handle] = ExecutionResult(
                ok=ok,
                idempotency_key=handle,
                result_ref=str(out.get("doc_no") or out.get("lead_id") or out.get("opportunity_id") or handle),
                metrics={"native": True, "capability": cap},
                error=None if ok else str(out.get("error") or "native_failed"),
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("NativeCrmExecutor submit failed cap=%s", cap)
            self._results[handle] = ExecutionResult(
                ok=False,
                idempotency_key=handle,
                error=f"{type(exc).__name__}: {exc}",
            )
        finally:
            if close_after and session is not None:
                try:
                    session.close()
                except Exception:  # noqa: BLE001
                    pass
        if len(self._results) > _HANDLE_CACHE_LIMIT:
            self._results.pop(next(iter(self._results)))
        return handle

    def poll(self, idempotency_key: str) -> ExecutionResult | None:
        return self._results.get(idempotency_key)


# 历史别名：SlotRegistry/测试仍可能 import GoodJobExecutor
GoodJobExecutor = NativeCrmExecutor


def build_goodjob_executor() -> NativeCrmExecutor | None:
    """兼容工厂：原生 CRM 始终可用。"""
    return NativeCrmExecutor()


def build_native_crm_executor() -> NativeCrmExecutor:
    return NativeCrmExecutor()
