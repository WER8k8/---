"""Paperclip 审批闸口与 Hermes 等人任务桥。

Hermes 的 `wait_human` 节点原本只能靠任务控制面手动放行；这里把它同步成
Paperclip 审批记录，使审批通过/拒绝能反向驱动 ai_task 生命周期。
"""

from __future__ import annotations

import json
import logging
from typing import Any

from sqlalchemy.orm import Session

from app.models.paperclip import PaperclipApproval, PaperclipCompany
from app.models.ai_task import TERMINAL_TASK_STATUSES
from app.services.tasks.task_control import TaskControlService

logger = logging.getLogger(__name__)

ACTION_TYPE = "hermes_node_approval"


def _load_json(raw: str | None) -> dict[str, Any]:
    """解析 JSON，失败时返回空对象，避免桥接层拖垮主流程。"""
    try:
        value = json.loads(raw or "{}")
        return value if isinstance(value, dict) else {}
    except (TypeError, json.JSONDecodeError):
        return {}


def _payload_of(approval: PaperclipApproval) -> dict[str, Any]:
    return _load_json(getattr(approval, "action_payload_json", None))


def _company_id_for_tenant(db: Session, tenant_id: str) -> str:
    """取租户对应 Paperclip 公司；没有则建立最小公司记录。"""
    company = (
        db.query(PaperclipCompany)
        .filter(PaperclipCompany.tenant_id == tenant_id)
        .first()
    )
    if company:
        return str(company.id)

    company = PaperclipCompany(
        tenant_id=tenant_id,
        name=f"Tenant {tenant_id[:8]}",
        mission="Hermes 关键节点人工审批",
        status="active",
    )
    db.add(company)
    db.flush()
    return str(company.id)


def _find_existing_approval(
    db: Session, task_id: str
) -> PaperclipApproval | None:
    """按 action_type + payload.task_id 找幂等审批。"""
    rows = (
        db.query(PaperclipApproval)
        .filter(PaperclipApproval.action_type == ACTION_TYPE)
        .order_by(PaperclipApproval.created_at.desc())
        .all()
    )
    for row in rows:
        if str(_payload_of(row).get("task_id") or "") == str(task_id):
            return row
    return None


def create_task_approval(
    db: Session,
    task: Any,
    blocked_reason: str | None = None,
) -> PaperclipApproval | None:
    """把 Hermes wait_human 节点登记成 Paperclip 待审批项。"""
    if not getattr(task, "id", None):
        return None

    task_id = str(task.id)
    existing = _find_existing_approval(db, task_id)
    if existing:
        return existing

    tenant_id = str(getattr(task, "tenant_id", "") or "")
    if not tenant_id:
        logger.warning("paperclip_approval_bridge: task %s 缺少 tenant_id", task_id)
        return None

    cfg = _load_json(getattr(task, "input_json", None))
    payload = {
        "task_id": task_id,
        "tenant_id": tenant_id,
        "plan_task_id": str(getattr(task, "parent_task_id", "") or "") or None,
        "node_id": cfg.get("node_id"),
        "executor": cfg.get("executor"),
        "capability": cfg.get("capability"),
        "blocked_reason": blocked_reason,
    }
    approval = PaperclipApproval(
        company_id=_company_id_for_tenant(db, tenant_id),
        agent_id=None,
        action_type=ACTION_TYPE,
        action_payload_json=json.dumps(payload, ensure_ascii=False),
        status="pending",
    )
    db.add(approval)
    db.flush()
    logger.info(
        "paperclip_approval_bridge: task %s 已登记审批 %s", task_id, approval.id
    )
    return approval


def resume_approved_task(db: Session, approval: PaperclipApproval) -> dict[str, Any]:
    """Paperclip 审批通过后放行 Hermes 节点。"""
    payload = _payload_of(approval)
    task_id = str(payload.get("task_id") or "")
    if not task_id:
        return {"status": "failed", "reason": "missing_task_id"}

    ctl = TaskControlService(db)
    task = ctl.get_task(task_id)
    if not task:
        return {"status": "failed", "reason": "task_not_found"}
    if task.status != "wait_human":
        return {"status": "skipped", "reason": f"task_status={task.status}"}

    cfg = _load_json(task.input_json)
    cfg.pop("blocked_reason", None)
    task.input_json = json.dumps(cfg, ensure_ascii=False)
    db.add(task)
    db.commit()

    try:
        ctl.resume_task(task_id, tenant_id=str(task.tenant_id))
        from app.tasks.orchestration_tasks import process_ai_task

        process_ai_task.delay(task_id)
    except Exception as exc:  # noqa: BLE001 — 放行失败要可观察，但不能炸审批接口
        logger.exception("paperclip_approval_bridge: task %s 放行失败", task_id)
        return {"status": "failed", "reason": str(exc), "task_id": task_id}

    return {"status": "resumed", "task_id": task_id}


def cancel_rejected_task(
    db: Session,
    approval: PaperclipApproval,
    comment: str | None = None,
) -> dict[str, Any]:
    """Paperclip 审批拒绝后取消 Hermes 节点。"""
    payload = _payload_of(approval)
    task_id = str(payload.get("task_id") or "")
    if not task_id:
        return {"status": "failed", "reason": "missing_task_id"}

    ctl = TaskControlService(db)
    task = ctl.get_task(task_id)
    if not task:
        return {"status": "failed", "reason": "task_not_found"}
    if task.status in TERMINAL_TASK_STATUSES:
        return {"status": "skipped", "reason": f"task_status={task.status}"}

    try:
        ctl.cancel_task(task_id, tenant_id=str(task.tenant_id))
    except Exception as exc:  # noqa: BLE001 — 拒绝结果不因取消失败而反向翻转
        logger.exception("paperclip_approval_bridge: task %s 取消失败", task_id)
        return {"status": "failed", "reason": str(exc), "task_id": task_id}

    logger.info(
        "paperclip_approval_bridge: task %s 已取消，comment=%s", task_id, comment
    )
    return {"status": "cancelled", "task_id": task_id}
