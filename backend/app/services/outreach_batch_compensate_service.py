# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""批量外联补偿服务 —— ORCH-19 修复

处理批量发信场景下的事务补偿：
- 批量发送失败时，支持部分成功状态的恢复
- 提供重试已完成发送的幂等保护
- 提供批量状态聚合统计
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session

from app.models.email_outreach import EmailOutreach, EmailStatus
from app.services.acquisition_outreach_service import send_outreach_step

logger = logging.getLogger(__name__)


def compensate_batch_outreach(
    db: Session,
    *,
    sequence_id: str | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    """补偿批量外联发送失败的任务。

    ORCH-19: 批量发信补偿服务
    - 查询 failed/queued 状态的外联记录
    - 跳过已成功的记录（幂等保护）
    - 重试最多3次
    """
    rows = _query_compensatable_rows(db, sequence_id=sequence_id, limit=limit)
    if not rows:
        return {"compensated": 0, "skipped": 0, "failed": 0, "details": []}

    result = {"compensated": 0, "skipped": 0, "failed": 0, "details": []}
    for row in rows:
        _compensate_single_row(db, row, result)
    _commit_compensate_changes(db)
    return result


def _query_compensatable_rows(
    db: Session,
    *,
    sequence_id: str | None,
    limit: int,
) -> list[Any]:
    """查询待补偿记录：failed/queued/draft 状态，按创建时间升序截断。"""
    query = db.query(EmailOutreach)
    if sequence_id:
        query = query.filter(EmailOutreach.sequence_id == sequence_id)
    return (
        query
        .filter(
            EmailOutreach.status.in_(
                [EmailStatus.FAILED, EmailStatus.QUEUED, EmailStatus.DRAFT]
            )
        )
        .order_by(EmailOutreach.created_at.asc())
        .limit(limit)
        .all()
    )


def _compensate_single_row(db: Session, row: Any, result: dict[str, Any]) -> None:
    """补偿单条外联记录：幂等跳过→重试次数校验→执行发送→回写统计。"""
    try:
        status = row.status.value if hasattr(row.status, "value") else str(row.status)
        if status in ("sent", "delivered", "opened", "clicked"):
            result["skipped"] += 1
            return

        meta = row.outreach_metadata or {}
        retry_count = meta.get("retry_count", 0)
        if retry_count >= 3:
            result["failed"] += 1
            # 超过 3 次重试：推入死信队列 (DLQ)
            push_to_dlq({
                "id": str(row.id),
                "sequence_id": str(row.sequence_id) if row.sequence_id else None,
                "tenant_id": str(row.tenant_id) if hasattr(row, "tenant_id") else None,
                "status": "max_retries_exceeded",
                "retry_count": retry_count,
                "failed_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
            })
            result["details"].append({
                "id": str(row.id),
                "status": "pushed_to_dlq",
                "retry_count": retry_count,
            })
            return

        step_result = send_outreach_step(db, outreach_id=str(row.id))
        if step_result.get("ok"):
            result["compensated"] += 1
            result["details"].append({
                "id": str(row.id),
                "status": "compensated",
                "new_status": step_result.get("status"),
            })
        else:
            result["failed"] += 1
            meta["retry_count"] = retry_count + 1
            meta["last_retry_at"] = str(row.updated_at) if row.updated_at else None
            row.outreach_metadata = meta
            db.add(row)
            result["details"].append({
                "id": str(row.id),
                "status": "retry_failed",
                "error": step_result.get("error", "unknown"),
            })

    except Exception as exc:
        logger.warning("Compensate failed for outreach %s: %s", row.id, exc)
        result["failed"] += 1
        result["details"].append({
            "id": str(row.id),
            "status": "exception",
            "error": str(exc)[:200],
        })


def _commit_compensate_changes(db: Session) -> None:
    """提交补偿期间所有变更，失败则回滚并向上抛出。"""
    try:
        db.commit()
    except Exception as exc:
        logger.error("Batch compensate commit failed: %s", exc)
        db.rollback()
        raise


def get_outreach_batch_stats(db: Session) -> dict[str, Any]:
    """获取外联批量统计。"""
    stats = {}
    for status in EmailStatus:
        count = (
            db.query(EmailOutreach)
            .filter(EmailOutreach.status == status)
            .count()
        )
        stats[status.value] = count
    return stats


# ── 死信队列 (DLQ) 基础设施 ──────────────────────────────────────
_DLQ_KEY = "youding:trade_outreach_dlq"
_IN_MEMORY_DLQ: list[dict[str, Any]] = []


def _get_redis_client():
    try:
        from app.core.redis import get_redis
        return get_redis()
    except Exception:
        return None


def push_to_dlq(payload: dict[str, Any]) -> bool:
    """将失败外联推入 Redis / 内存死信队列 (DLQ)。"""
    import json
    r = _get_redis_client()
    if r:
        try:
            r.lpush(_DLQ_KEY, json.dumps(payload, ensure_ascii=False))
            r.expire(_DLQ_KEY, 7 * 24 * 3600)  # 保留 7 天
            return True
        except Exception as exc:
            logger.warning("Redis DLQ push failed: %s, falling back to in-memory DLQ", exc)
    _IN_MEMORY_DLQ.append(payload)
    return True


def get_dlq_items(limit: int = 50) -> list[dict[str, Any]]:
    """查询死信队列中的异常任务列表。"""
    import json
    r = _get_redis_client()
    items = []
    if r:
        try:
            raw = r.lrange(_DLQ_KEY, 0, limit - 1)
            for it in raw:
                try:
                    items.append(json.loads(it))
                except Exception:
                    pass
            if items:
                return items
        except Exception:
            pass
    return _IN_MEMORY_DLQ[:limit]


def retry_dlq_item(db: Session, outreach_id: str) -> dict[str, Any]:
    """从死信队列中人工/自动重试单条外联任务。"""
    row = db.query(EmailOutreach).filter(EmailOutreach.id == outreach_id).first()
    if not row:
        return {"success": False, "reason": "outreach_not_found"}

    # 重置重试计数器并再次尝试投递
    meta = row.outreach_metadata or {}
    meta["retry_count"] = 0
    row.outreach_metadata = meta
    row.status = EmailStatus.QUEUED
    db.commit()
    db.refresh(row)

    step_result = send_outreach_step(db, outreach_id=str(row.id))
    return {
        "success": bool(step_result.get("ok")),
        "outreach_id": str(row.id),
        "status": step_result.get("status"),
        "error": step_result.get("error"),
    }

