# -*- coding: utf-8 -*-
"""分发结果回写编排链的回归测试（不连真库，全部假 DB）。

钉住 2026-09-10 实测的两个"看得见但查不清"问题：

1. 执行器返回 failed 时，桥里抛的是 ``TaskControlError("executor_failed", msg)``。
   两个位置参数会让 ``str(exc)`` 变成 ``"('executor_failed', '...')"`` 元组字面量，
   直接落进 ai_tasks.error_message，人在库里读到的是 Python  repr，不是人话。
2. fail_task 不写 output_json，于是失败节点的逐项明细（哪个渠道、缺什么凭证）
   整块丢失 —— 库里只留下一句"所有平台发布均失败"，等于没排障依据。

顺带钉住 skipped 语义：全渠道未配置属"环境未完成"，必须走 complete_task 落 done，
并把原因写进 output_json，绝不能再被当成业务失败把整条 DAG 判死。
"""
from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from app.schemas.hermes_orchestration import ExecutorResult
from app.services.tasks import hermes_task_bridge as bridge


def _stub_registry(result):
    """把执行器注册表整体换成替身。

    桥里是函数内 import（``from app.services.hermes.executors import ExecutorRegistry``），
    所以必须 patch 真实类的 get 方法，patch 桥模块属性是打不中的。
    """
    from app.services.hermes.executors import ExecutorRegistry

    return patch.object(
        ExecutorRegistry,
        "get",
        classmethod(lambda cls, name: _StubExecutor(result)),
    )


class _StubExecutor:
    """替身执行器：按预设的 ExecutorResult 返回，不碰任何真实服务。"""

    def __init__(self, result):
        self._result = result

    async def run(self, node, context):
        return self._result


def _mk_task(**over):
    data = {
        "id": "task-1",
        "status": "created",
        "task_type": "hermes_node:publish",
        "tenant_id": "tenant-1",
        "parent_task_id": "plan-1",
        "input_json": json.dumps(
            {"node_id": "n4", "capability": "publish.multi", "effective_input": {}},
            ensure_ascii=False,
        ),
    }
    data.update(over)
    return SimpleNamespace(**data)


def _run_node(result):
    """用替身执行器跑一次 _run_hermes_node，返回 (返回值, 异常)。"""
    db = object()
    task = _mk_task()
    with _stub_registry(result):
        exc = None
        out = None
        try:
            out = bridge._run_hermes_node(db, task)
        except Exception as e:  # noqa: BLE001 — 断言交给调用方
            exc = e
    return out, exc


def test_failure_message_is_plain_text_not_tuple_repr():
    """error 必须是执行器给的人话，不许带 Python 元组字面量。"""
    detail = {
        "not_configured": 1,
        "not_configured_detail": {"wechat": {"error_message": "缺 appid"}},
    }
    _out, exc = _run_node(
        ExecutorResult(
            node_id="n4",
            status="failed",
            output=detail,
            error="1 个渠道真发失败 ｜ linkedin：401 token 过期",
        )
    )

    assert isinstance(exc, bridge.HermesNodeExecutionError)
    assert str(exc) == "1 个渠道真发失败 ｜ linkedin：401 token 过期"
    assert "(" not in str(exc).split("｜")[0].replace("（", "").replace("）", "")
    assert exc.code == "executor_failed"
    assert exc.output == detail


def test_success_and_skipped_both_return_output_dict():
    """succeeded / skipped 都正常返回 output，交由上层落 done。"""
    out, exc = _run_node(
        ExecutorResult(
            node_id="n4",
            status="skipped",
            output={"summary": "2/2 个渠道未配置，未发起真实请求"},
            error=None,
        )
    )

    assert exc is None
    assert out["summary"].startswith("2/2")


def _dispatch(result, *, task=None):
    """跑一次 dispatch_ai_task（执行器整段打桩），返回 (db, ctl, task, 异常)。"""
    task = task or _mk_task()
    db = MagicMock_db()
    ctl = SimpleNamespace(
        get_task=lambda tid, tenant_id=None: task,
        start_task=lambda *a, **k: None,
        complete_task=SimpleNamespace(call_args=None),
        fail_task=SimpleNamespace(call_args=None),
        review_task=lambda *a, **k: None,
    )
    calls = {"complete": [], "fail": []}

    def complete(tid, **kw):
        calls["complete"].append(kw)
        task.status = "done"
        if kw.get("output_data") is not None:
            task.output_json = json.dumps(kw["output_data"], ensure_ascii=False)

    def fail(tid, **kw):
        calls["fail"].append(kw)
        task.status = "failed"

    ctl.complete_task = complete
    ctl.fail_task = fail

    with patch.object(bridge, "TaskControlService", lambda d: ctl), patch.object(
        bridge, "TaskControlService", lambda d: ctl
    ), _stub_registry(result), patch.object(bridge, "_notify_site_built"), patch(
        "app.services.hermes.task_control_supervisor.advance_plan", lambda *a, **k: None
    ):
        exc = None
        try:
            bridge.dispatch_ai_task(db, task.id, tenant_id=task.tenant_id)
        except Exception as e:  # noqa: BLE001
            exc = e
    return db, ctl, task, calls, exc


def MagicMock_db():
    """轻量假 DB：只记录 commit/rollback 次数，不做任何真实 IO。"""
    return SimpleNamespace(commit=lambda: None, rollback=lambda: None, refresh=lambda: None)


def test_failed_node_still_persists_detail_to_output_json():
    """失败也要把执行器明细写进 output_json，库里不能只剩一句话。"""
    detail = {
        "summary": "全部 2 个渠道发布失败，成功 0",
        "failed": 2,
        "not_configured_detail": {"zhihu": {"missing_credentials": ["cookies"]}},
    }
    _db, _ctl, task, calls, exc = _dispatch(
        ExecutorResult(node_id="n4", status="failed", output=detail, error="2 个渠道真发失败")
    )

    assert exc is not None, "失败仍要向上抛，保留 Celery 重试语义"
    assert len(calls["fail"]) == 1
    assert "2 个渠道真发失败" in calls["fail"][0]["error_message"]
    assert not calls["complete"], "失败任务绝不能被标成 done"
    stored = json.loads(task.output_json)
    assert stored["not_configured_detail"]["zhihu"]["missing_credentials"] == ["cookies"]


def test_skipped_node_lands_done_with_reason():
    """全渠道未配置 → done + 原因在 output_json，不把整条 DAG 判死。"""
    detail = {"summary": "2/2 个渠道未配置或未接入，未发起任何真实请求", "not_configured": 2}
    _db, _ctl, task, calls, exc = _dispatch(
        ExecutorResult(node_id="n4", status="skipped", output=detail, error=None)
    )

    assert exc is None
    assert not calls["fail"]
    assert len(calls["complete"]) == 1
    assert task.status == "done"
    assert json.loads(task.output_json)["not_configured"] == 2


def test_output_summary_prefers_human_summary():
    """列表页摘要优先取执行器的 summary，而不是空串。"""
    detail = {"summary": "1/3 个渠道真发成功，1 个失败，1 个未配置", "succeeded": 1}
    _db, _ctl, _task, calls, exc = _dispatch(
        ExecutorResult(node_id="n4", status="succeeded", output=detail, error=None)
    )

    assert exc is None
    assert calls["complete"][0]["output_summary"] == detail["summary"]


def test_real_failure_from_publish_executor_is_not_generic_text():
    """分发执行器真失败时，桥里的 error_message 要能看出是哪个平台为什么失败。"""
    from app.services.hermes.executors.publish_executor import PublishExecutor

    result = PublishExecutor._failure_message(
        {
            "linkedin": {"status": "failed", "error_code": "API_ERROR", "error_message": "401 过期"},
            "wechat": {
                "status": "failed",
                "error_code": "PLATFORM_NOT_CONFIGURED",
                "error_message": "缺 appid",
            },
        },
        failed=1,
        not_configured=1,
    )

    assert "linkedin" in result and "401" in result
    assert "wechat" not in result  # 未配置的单列，不混进真发失败原因
    assert "另有 1 个未配置" in result
