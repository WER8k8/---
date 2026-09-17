# -*- coding: utf-8 -*-
"""UbrainExecutor and unified chat task entry tests."""

from __future__ import annotations

import asyncio
import json
from unittest.mock import MagicMock, patch

import pytest

from app.schemas.hermes_orchestration import TaskNode
from app.services.hermes.executors.base import ExecutorContext, ExecutorRegistry
from app.services.hermes.executors.ubrain_executor import UbrainExecutor
from app.services.ubrain.chat_task_service import (
    UBrainChatTaskError,
    run_chat_task,
)


def _ctx() -> ExecutorContext:
    return ExecutorContext(db=MagicMock(), tenant_id="tenant-1", plan_id="plan-1")


def _node(**input_data) -> TaskNode:
    return TaskNode(
        id="ubrain-1",
        executor="ubrain",
        capability="ubrain.chat",
        depends_on=[],
        input=input_data,
    )


def test_executor_is_registered_with_declared_capability():
    assert ExecutorRegistry.has("ubrain")
    assert "ubrain.chat" in UbrainExecutor.capability_names()


def test_executor_success_passes_orchestrator_output():
    expected = {"intent": "find_buyers", "reply": "ok", "tool_result": {}}
    with patch("app.services.ubrain.orchestrator.ubrain_orchestrator") as mock_orch:
        mock_orch.chat.return_value = expected
        result = asyncio.run(
            UbrainExecutor().run(_node(message="找德国买家"), _ctx())
        )

    assert result.status == "succeeded"
    assert result.output == expected
    mock_orch.chat.assert_called_once()


def test_executor_missing_message_returns_failed():
    result = asyncio.run(UbrainExecutor().run(_node(), _ctx()))
    assert result.status == "failed"
    assert "missing_message" in (result.error or "")


def test_executor_exception_returns_failed_not_raise():
    with patch("app.services.ubrain.orchestrator.ubrain_orchestrator") as mock_orch:
        mock_orch.chat.side_effect = RuntimeError("db down")
        result = asyncio.run(
            UbrainExecutor().run(_node(message="找德国买家"), _ctx())
        )

    assert result.status == "failed"
    assert "RuntimeError" in (result.error or "")


def test_chat_task_service_creates_dispatches_and_returns_output():
    created = MagicMock()
    created.id = "task-1"
    refreshed = MagicMock()
    refreshed.status = "done"
    refreshed.output_json = json.dumps({"intent": "find_buyers", "reply": "ok"})

    db = MagicMock()
    ctl = MagicMock()
    ctl.create_task.return_value = created
    ctl.get_task.return_value = refreshed

    celery_task = MagicMock()
    with (
        patch("app.services.ubrain.chat_task_service.TaskControlService", return_value=ctl),
        patch("app.tasks.orchestration_tasks.process_ai_task") as mock_task,
    ):
        mock_task.delay.return_value = celery_task
        task, output = run_chat_task(
            db,
            tenant_id="tenant-1",
            message="找德国买家",
            context={"country": "DE"},
            user_id="user-1",
        )

    assert task is refreshed
    assert output["intent"] == "find_buyers"
    ctl.create_task.assert_called_once()
    mock_task.delay.assert_called_once_with("task-1")
    celery_task.get.assert_called_once()


def test_chat_task_service_maps_failed_task_to_error():
    created = MagicMock()
    created.id = "task-1"
    refreshed = MagicMock()
    refreshed.status = "failed"
    refreshed.error_message = "orchestrator exploded"

    db = MagicMock()
    ctl = MagicMock()
    ctl.create_task.return_value = created
    ctl.get_task.return_value = refreshed

    with (
        patch("app.services.ubrain.chat_task_service.TaskControlService", return_value=ctl),
        patch("app.tasks.orchestration_tasks.process_ai_task") as mock_task,
    ):
        mock_task.delay.return_value = MagicMock()
        with pytest.raises(UBrainChatTaskError, match="orchestrator exploded"):
            run_chat_task(
                db,
                tenant_id="tenant-1",
                message="找德国买家",
            )
