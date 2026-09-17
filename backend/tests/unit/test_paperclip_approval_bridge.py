from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.services.tasks import paperclip_approval_bridge as bridge


def _task(node_id: str = "n1", status: str = "wait_human") -> SimpleNamespace:
    return SimpleNamespace(
        id="task-1",
        tenant_id="tenant-1",
        parent_task_id="plan-1",
        status=status,
        input_json=json.dumps(
            {
                "node_id": node_id,
                "executor": "publish",
                "capability": "publish.multi",
                "blocked_reason": "approval_required: capability=publish.multi",
            },
            ensure_ascii=False,
        ),
    )


def _approval(task_id: str = "task-1", status: str = "pending") -> SimpleNamespace:
    return SimpleNamespace(
        id="approval-1",
        status=status,
        action_type=bridge.ACTION_TYPE,
        action_payload_json=json.dumps({"task_id": task_id}, ensure_ascii=False),
    )


def test_create_task_approval_is_idempotent_by_payload_task_id():
    db = MagicMock()
    existing = _approval()

    with patch.object(bridge, "_find_existing_approval", return_value=existing):
        result = bridge.create_task_approval(db, _task(), "blocked")

    assert result is existing
    db.add.assert_not_called()


def test_create_task_approval_persists_new_record():
    db = MagicMock()
    created = MagicMock()
    created.id = "approval-2"

    with (
        patch.object(bridge, "_find_existing_approval", return_value=None),
        patch.object(bridge, "_company_id_for_tenant", return_value="company-1"),
        patch.object(bridge, "PaperclipApproval", return_value=created) as mock_model,
    ):
        result = bridge.create_task_approval(db, _task(), "blocked")

    assert result is created
    db.add.assert_called_once_with(created)
    db.flush.assert_called_once()
    _, kwargs = mock_model.call_args
    assert kwargs["company_id"] == "company-1"
    assert kwargs["action_type"] == bridge.ACTION_TYPE
    payload = json.loads(kwargs["action_payload_json"])
    assert payload["task_id"] == "task-1"
    assert payload["tenant_id"] == "tenant-1"
    assert payload["blocked_reason"] == "blocked"


def test_resume_approved_task_resumes_and_redispatches_wait_human_task():
    db = MagicMock()
    ctl = MagicMock()
    task = _task()
    ctl.get_task.return_value = task

    with (
        patch.object(bridge, "TaskControlService", return_value=ctl),
        patch("app.tasks.orchestration_tasks.process_ai_task") as mock_task,
    ):
        result = bridge.resume_approved_task(db, _approval())

    assert result == {"status": "resumed", "task_id": "task-1"}
    ctl.resume_task.assert_called_once_with("task-1", tenant_id="tenant-1")
    mock_task.delay.assert_called_once_with("task-1")
    assert "blocked_reason" not in json.loads(task.input_json)


def test_cancel_rejected_task_cancels_active_task():
    db = MagicMock()
    ctl = MagicMock()
    task = _task()
    ctl.get_task.return_value = task

    with patch.object(bridge, "TaskControlService", return_value=ctl):
        result = bridge.cancel_rejected_task(db, _approval(), "not now")

    assert result == {"status": "cancelled", "task_id": "task-1"}
    ctl.cancel_task.assert_called_once_with("task-1", tenant_id="tenant-1")
