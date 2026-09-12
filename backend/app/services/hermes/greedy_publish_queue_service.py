"""L4 发布队列人工审核 — 通过/驳回 + 审核历史。"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Literal

from sqlalchemy.orm import Session

from app.core.cache import redis_client
from app.services.hermes.greedy_avatar_constitution import assert_greedy_action, legal_gate_check
from app.services.hermes.greedy_revenue_loop_service import _PUBLISH_QUEUE_KEY

logger = logging.getLogger("uj-admin.greedy_publish_queue")

_REVIEW_HISTORY_KEY = "hermes:greedy:publish_review_history"
_fallback_queue: list[str] = []
_fallback_history: list[dict[str, Any]] = []


def _read_queue_raw() -> list[str]:
    """_read_queue_raw。
    :return: 返回处理结果。
    """
    if redis_client:
        try:
            return list(redis_client.lrange(_PUBLISH_QUEUE_KEY, 0, -1) or [])
        except Exception as exc:
            logger.debug("queue lrange failed: %s", exc)
    return list(_fallback_queue)


def _write_queue_raw(items: list[str]) -> None:
    """_write_queue_raw。

    参数说明：
    :param items: 参数 items
    :return: 返回处理结果。
    """
    if redis_client:
        try:
            pipe = redis_client.pipeline()
            pipe.delete(_PUBLISH_QUEUE_KEY)
            if items:
                pipe.rpush(_PUBLISH_QUEUE_KEY, *items)
            pipe.execute()
            return
        except Exception as exc:
            logger.debug("queue rewrite failed: %s", exc)
    _fallback_queue.clear()
    _fallback_queue.extend(items)


def _parse_item(raw: str, index: int) -> dict[str, Any]:
    """_parse_item。

    参数说明：
    :param raw: 参数 raw
    :param index: 参数 index
    :return: 返回处理结果。
    """
    try:
        payload = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        payload = {"raw": str(raw)[:200]}
    if isinstance(payload, dict):
        payload.setdefault("queue_index", index)
    return payload if isinstance(payload, dict) else {"raw": str(raw)[:200], "queue_index": index}


def _append_history(entry: dict[str, Any]) -> None:
    """_append_history。

    参数说明：
    :param entry: 参数 entry
    :return: 返回处理结果。
    """
    entry = dict(entry)
    entry.setdefault("reviewed_at", datetime.now(timezone.utc).isoformat())
    if redis_client:
        try:
            redis_client.lpush(_REVIEW_HISTORY_KEY, json.dumps(entry, ensure_ascii=False))
            redis_client.ltrim(_REVIEW_HISTORY_KEY, 0, 99)
            return
        except Exception as exc:
            logger.debug("review history write failed: %s", exc)
    _fallback_history.insert(0, entry)
    del _fallback_history[100:]


def get_publish_review_history(*, limit: int = 30) -> list[dict[str, Any]]:
    """get_publish_review_history。

    参数说明：
    :param limit: 参数 limit
    :return: 返回处理结果。
    """
    assert_greedy_action("read_probe")
    cap = max(1, min(int(limit), 100))
    rows: list[dict[str, Any]] = []
    if redis_client:
        try:
            for raw in redis_client.lrange(_REVIEW_HISTORY_KEY, 0, cap - 1) or []:
                try:
                    rows.append(json.loads(raw))
                except (json.JSONDecodeError, TypeError):
                    rows.append({"raw": str(raw)[:200]})
        except Exception:
            pass
    if not rows:
        rows = list(_fallback_history[:cap])
    return rows


def _build_publish_plan(
    db: Session | None,
    item: dict[str, Any],
    *,
    reviewer: str | None,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    """构建/执行发布计划，返回 (plan, publish_exec)。"""
    if db is not None:
        try:
            from app.services.hermes.greedy_survival_publish_service import execute_survival_l4_publish
            publish_exec = execute_survival_l4_publish(db, item, user_id=reviewer)
            plan = {
                "mode": "publish_tasks_created" if publish_exec.get("status") == "queued" else "publish_attempt",
                "execution": publish_exec,
                "platforms": publish_exec.get("platform_names"),
                "task_ids": publish_exec.get("task_ids"),
                "count": publish_exec.get("count"),
            }
            return plan, publish_exec
        except Exception as exc:
            logger.exception("survival l4 publish failed")
            return {"mode": "publish_execute_failed", "error": str(exc)[:200]}, None

    try:
        from app.services.ubrain.matrix_publish_service import build_matrix_publish_plan
        plan = build_matrix_publish_plan(
            {
                "locale": item.get("locale") or "global",
                "content_source": "greedy_l4_manual_approve",
                "cta": item.get("cta") or "B2B inquiry / digital product",
                "skus": [item.get("sku")],
                "title": item.get("title"),
                "body": item.get("body"),
            }
        )
        plan["manual_review"] = True
        plan["item_sku"] = item.get("sku")
        plan["note"] = "无 DB 会话，仅生成计划未创建 PublishTask"
        return plan, None
    except Exception as exc:
        return {"mode": "plan_build_failed", "error": str(exc)[:160]}, None


def _record_publish_credits(item: dict[str, Any]) -> dict[str, Any] | None:
    """为参与角色记录发布战功，失败静默跳过。"""
    role_ids = list(item.get("primary_roles") or [])
    if not role_ids:
        return None
    try:
        from app.services.hermes.greedy_contest_memory_service import record_publish_credits
        record_publish_credits(role_ids, skus=[item.get("sku") or "unknown"])
        return {"roles": role_ids, "sku": item.get("sku")}
    except Exception as exc:
        logger.debug("publish credits skipped: %s", exc)
        return None


def _build_approve_history(
    item: dict[str, Any],
    *,
    plan: dict[str, Any],
    publish_exec: dict[str, Any] | None,
    reviewer: str | None,
    reason: str | None,
) -> dict[str, Any]:
    """组装审核通过的历史记录。"""
    return {
        "action": "approved",
        "sku": item.get("sku"),
        "locale": item.get("locale"),
        "publish_plan": plan,
        "publish_status": (publish_exec or {}).get("status"),
        "task_ids": (publish_exec or {}).get("task_ids"),
        "task_count": (publish_exec or {}).get("count"),
        "content_master_id": (publish_exec or {}).get("content_master_id"),
        "channels": item.get("publish_channels"),
        "reviewer": reviewer,
        "note": (reason or "")[:500] or None,
    }


def review_publish_queue_item(
    *,
    queue_index: int,
    action: Literal["approve", "reject"],
    reviewer: str | None = None,
    reason: str | None = None,
    db: Session | None = None,
) -> dict[str, Any]:
    """按 queue_index（与 GET publish-queue 一致）审核单条。"""
    idx = int(queue_index)
    if idx < 0:
        return {"ok": False, "error": "invalid_queue_index"}

    raw_items = _read_queue_raw()
    if idx >= len(raw_items):
        return {"ok": False, "error": "queue_index_out_of_range", "depth": len(raw_items)}

    item = _parse_item(raw_items[idx], idx)
    removed_raw = raw_items.pop(idx)
    _write_queue_raw(raw_items)
    result: dict[str, Any] = {
        "ok": True,
        "action": action,
        "queue_index": idx,
        "item": item,
        "remaining_depth": len(raw_items),
        "reviewer": reviewer,
    }
    if action == "reject":
        assert_greedy_action("stage_publish")
        history = {
            "action": "rejected",
            "sku": item.get("sku"),
            "locale": item.get("locale"),
            "reason": (reason or "人工驳回")[:500],
            "reviewer": reviewer,
        }
        _append_history(history)
        result["history"] = history
        return result

    assert_greedy_action("publish_survival_marketing")
    gate = legal_gate_check(action="publish_survival_marketing", meta=item)
    if not gate.get("ok"):
        raw_items.insert(idx, removed_raw)
        _write_queue_raw(raw_items)
        return {"ok": False, "error": "legal_gate_blocked", "legal_gate": gate}

    plan, publish_exec = _build_publish_plan(db, item, reviewer=reviewer)
    credits = _record_publish_credits(item)
    if credits is not None:
        result["contest_credits"] = credits

    history = _build_approve_history(
        item,
        plan=plan,
        publish_exec=publish_exec,
        reviewer=reviewer,
        reason=reason,
    )
    _append_history(history)
    result["publish_plan"] = plan
    result["publish_execution"] = publish_exec
    result["history"] = history
    return result
