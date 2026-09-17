# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""trade-documents 桥 · 单证生成委派 GoodJob（批次 B）.

设计出处：uj-annex-integration-design §10.18（六件套缺口扫描）/ §10.19。
分工：报价真相在 UJ（quote 表），合同/CI/PL/COO/CUSTOMS 等 8 类单证
生成委派 GoodJob（其 advanced-document-templates 已有全套模板）；
生成的单据引用（result_ref）回传 UJ，由调用方挂到询盘/商机上。

铁律：
- 委派 ≠ 裁剪：doc_type 白名单与 GoodJob 模板体系一一对应；
- 幂等键按内容哈希派生——同一询盘同一单证同一内容重复提交自动去重；
- 条目数上限 200（对齐清单端点默认分页上限铁律）；
- 无 tenant_id 拒绝派单。
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Mapping

from app.orchestration.executors.goodjob_executor import (
    ExecutionResult,
    GoodJobExecutor,
    TASK_TYPE_TRADE_DOCUMENT,
)
from app.orchestration.interfaces import TaskPackage

DOC_TYPES = frozenset(
    {"PI", "CI", "PL", "CONTRACT", "QUOTATION", "CUSTOMS", "COO", "SHIPPING"}
)
MAX_ITEMS = 200
_LEASE_TTL_SECONDS = 1800
_KEY_MAX_LEN = 128


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _content_hash(items: Any, options: Mapping[str, Any]) -> str:
    canonical = json.dumps(
        {"items": items, "options": dict(options)}, ensure_ascii=False, sort_keys=True
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


def document_idempotency_key(
    tenant_id: str, inquiry_id: str, doc_type: str, items: Any, options: Mapping[str, Any]
) -> str:
    return (
        f"gj-doc:{tenant_id}:{inquiry_id}:{doc_type}:{_content_hash(items, options)}"
    )[:_KEY_MAX_LEN]


def submit_document_task(
    executor: GoodJobExecutor,
    *,
    tenant_id: str,
    inquiry_id: str,
    doc_type: str,
    items: Any,
    options: Mapping[str, Any] | None = None,
) -> str | None:
    """向 GoodJob 提交单证生成任务；桥禁用时返回 None 静默跳过。"""
    if not executor.enabled:
        return None
    tenant_id = str(tenant_id or "").strip()
    if not tenant_id:
        raise ValueError("单证任务缺 tenant_id，拒绝派单（多租户隔离红线）")
    inquiry_id = str(inquiry_id or "").strip()
    if not inquiry_id:
        raise ValueError("单证任务缺 inquiry_id，拒绝派单（结果无法回挂）")
    doc_type = str(doc_type or "").strip().upper()
    if doc_type not in DOC_TYPES:
        raise ValueError(f"非法单证类型 {doc_type!r}，白名单: {sorted(DOC_TYPES)}")
    items_list = list(items or [])
    if len(items_list) > MAX_ITEMS:
        raise ValueError(f"单证条目超上限 {MAX_ITEMS}（清单端点分页铁律）")
    opts = dict(options or {})
    payload = {
        "inquiry_id": inquiry_id,
        "doc_type": doc_type,
        "items": items_list,
        "options": opts,
        "issued_at": _now_iso(),
    }
    package = TaskPackage(
        tenant_id=tenant_id,
        idempotency_key=document_idempotency_key(tenant_id, inquiry_id, doc_type, items_list, opts),
        lease_ttl=_LEASE_TTL_SECONDS,
        checkpoint="v1",
        budget={"max_retries": 1},
    )
    return executor.submit(
        package, task_type=TASK_TYPE_TRADE_DOCUMENT, payload=payload
    )


def poll_document_task(
    executor: GoodJobExecutor, idempotency_key: str
) -> ExecutionResult | None:
    """查询单证任务结果；result_ref 指向 GoodJob 侧单据/请求引用。"""
    return executor.poll(idempotency_key)


def submit_stage_sync_task(
    executor: GoodJobExecutor,
    *,
    tenant_id: str,
    order_id: str,
    stage: str,
    step_number: int = 1,
    status: str = "in_progress",
    payload: Mapping[str, Any] | None = None,
) -> str | None:
    """向 GoodJob 提交外贸7步履约生命周期状态同步任务。"""
    if not executor.enabled:
        return None
    tenant_id = str(tenant_id or "").strip()
    if not tenant_id:
        raise ValueError("履约阶段同步缺 tenant_id（多租户隔离红线）")
    order_id = str(order_id or "").strip()
    if not order_id:
        raise ValueError("履约阶段同步缺 order_id")
    stage = str(stage or "").strip()
    sync_payload = {
        "order_id": order_id,
        "stage": stage,
        "step_number": int(step_number),
        "status": status,
        "details": dict(payload or {}),
        "synced_at": _now_iso(),
    }
    idempotency_key = f"gj-stage:{tenant_id}:{order_id}:{stage}:{step_number}"[:_KEY_MAX_LEN]
    package = TaskPackage(
        tenant_id=tenant_id,
        idempotency_key=idempotency_key,
        lease_ttl=_LEASE_TTL_SECONDS,
        checkpoint="v1",
        budget={"max_retries": 1},
    )
    from app.orchestration.executors.goodjob_executor import TASK_TYPE_STAGE_SYNC
    return executor.submit(
        package, task_type=TASK_TYPE_STAGE_SYNC, payload=sync_payload
    )

