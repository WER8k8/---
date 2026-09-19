# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""销售任务状态契约：模型 open/done/cancelled + 别名归一。"""
from __future__ import annotations

from app.api.v1.routes.sales_task import _normalize_task_status


def test_canonical_status_pass_through():
    assert _normalize_task_status("open") == "open"
    assert _normalize_task_status("done") == "done"
    assert _normalize_task_status("cancelled") == "cancelled"
    assert _normalize_task_status("DONE") == "done"


def test_status_aliases_normalize_to_model_truth():
    assert _normalize_task_status("pending") == "open"
    assert _normalize_task_status("in_progress") == "open"
    assert _normalize_task_status("completed") == "done"
    assert _normalize_task_status("archived") == "cancelled"


def test_invalid_status_rejected():
    assert _normalize_task_status("") is None
    assert _normalize_task_status("  ") is None
    assert _normalize_task_status("bogus") is None
