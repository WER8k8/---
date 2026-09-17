from __future__ import annotations

import json

import pytest

from app.services.tasks.hermes_task_bridge import (
    ROUTERS,
    _run_commercial_loop,
    _run_video_publish,
    _run_workflow_canvas,
)
from app.services.tasks.task_control import TaskControlError


class _Task:
    id = "task-1"
    tenant_id = "tenant-1"

    def __init__(self, input_data: dict):
        self.input_json = json.dumps(input_data, ensure_ascii=False)


def test_new_service_routes_are_registered():
    assert {"commercial_loop", "video_publish", "workflow_canvas"}.issubset(ROUTERS)


def test_commercial_loop_requires_product_identity():
    with pytest.raises(TaskControlError, match="product_data"):
        _run_commercial_loop(None, _Task({"target_market": "us"}))


def test_video_publish_requires_media_fields():
    with pytest.raises(TaskControlError, match="video_url"):
        _run_video_publish(None, _Task({"platform_names": ["bilibili"]}))


def test_workflow_canvas_runs_service_and_returns_trace():
    task = _Task(
        {
            "nodes": [
                {"id": "n1", "type": "start", "data": {}},
                {"id": "n2", "type": "end", "data": {}},
            ],
            "edges": [{"source": "n1", "target": "n2"}],
        }
    )

    result = _run_workflow_canvas(None, task)

    assert result["status"] == "success"
    assert result["execution_trace"] == ["n1", "n2"]
