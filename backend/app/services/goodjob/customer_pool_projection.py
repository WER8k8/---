# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""customer_pool 投影同步 · UJ 真相 → GoodJob 工作副本.

设计出处：uj-annex-integration-design §10.5 / §10.19；批次 B。

铁律：
- GoodJob 的 customer_pool 是投影副本（master=uj），询盘/线索真相永远在
  UJ（inquiries / unified_leads）；投影单向 UJ→GoodJob，GoodJob 侧禁止回写；
- 无 tenant_id 的询盘不投影（多租户隔离红线，宁缺勿串）；
- 幂等键确定性派生（询盘ID+状态+更新时间），重复同步在桥两端自动去重；
- 同步失败不得阻断询盘主流程（调用方 fail-safe 静默）。
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.orchestration.executors.goodjob_executor import (
    GoodJobExecutor,
    TASK_TYPE_CUSTOMER_POOL,
)
from app.orchestration.interfaces import TaskPackage

PROJECTION_KIND = "customer_pool"
MASTER_MARK = "uj"
SOURCE_OF_TRUTH = "inquiries"
_LEASE_TTL_SECONDS = 900
_MESSAGE_EXCERPT_LIMIT = 200
_KEY_MAX_LEN = 128


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _attr_str(row: Any, name: str) -> str:
    return str(getattr(row, name, "") or "")


def _attr_iso(row: Any, name: str) -> str:
    value = getattr(row, name, None)
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.isoformat(timespec="seconds")
    return str(value)


def _excerpt(text: Any, limit: int = _MESSAGE_EXCERPT_LIMIT) -> str:
    return str(text or "").strip()[:limit]


def build_projection(row: Any) -> dict[str, Any]:
    """从询盘行构造投影载荷（鸭子类型取值，不依赖 SQLAlchemy，可测）。"""
    tenant_id = _attr_str(row, "tenant_id").strip()
    if not tenant_id:
        raise ValueError("询盘缺 tenant_id，拒绝投影（多租户隔离红线）")
    return {
        "master": MASTER_MARK,
        "source_of_truth": SOURCE_OF_TRUTH,
        "projection_kind": PROJECTION_KIND,
        "tenant_id": tenant_id,
        "entity": {
            "inquiry_id": _attr_str(row, "id"),
            "updated_at": _attr_iso(row, "updated_at"),
        },
        "customer": {
            "name": _attr_str(row, "name"),
            "email": _attr_str(row, "email"),
            "phone": _attr_str(row, "phone"),
            "product": _attr_str(row, "product"),
            "message_excerpt": _excerpt(getattr(row, "message", "")),
            "status": _attr_str(row, "status"),
            "source_channel": _attr_str(row, "source_channel"),
            "attribution_channel": _attr_str(row, "attribution_channel"),
        },
        "synced_at": _now_iso(),
    }


def projection_idempotency_key(row: Any) -> str:
    """确定性幂等键：同询盘同状态同更新时间重放自动去重。"""
    key = (
        f"gj-pool:{_attr_str(row, 'id')}:{_attr_str(row, 'status')}:"
        f"{_attr_iso(row, 'updated_at') or _attr_iso(row, 'created_at')}"
    )
    return key[:_KEY_MAX_LEN]


def sync_inquiry_to_pool(executor: GoodJobExecutor, row: Any) -> str | None:
    """把询盘投影推送到 GoodJob 客户池；桥禁用时返回 None 静默跳过。"""
    if not executor.enabled:
        return None
    projection = build_projection(row)
    package = TaskPackage(
        tenant_id=projection["tenant_id"],
        idempotency_key=projection_idempotency_key(row),
        lease_ttl=_LEASE_TTL_SECONDS,
        checkpoint="v1",
        budget={"max_retries": 2},
    )
    return executor.submit(
        package, task_type=TASK_TYPE_CUSTOMER_POOL, payload=projection
    )
