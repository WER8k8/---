# -*- coding: utf-8 -*-
"""编排链桥的失败落态回归测试（不连真库，全部用假 DB）。

钉住 2026-09-10 端到端真跑发现的两个 P0：

1. 执行器按契约返回 status="failed" 时，_run_hermes_node 抛 TaskControlError，
   而 dispatch_ai_task 旧代码把 TaskControlError 单独 raise 掉 —— 节点永远停在
   executing，既不落终态也不触发 advance_plan，整条 DAG 僵死。
2. 人工放行（resume 把 wait_human 切成 executing 后重投）以及 Celery 重投时，
   任务已是 EXECUTING；状态机里 EXECUTING→EXECUTING 是非法转移，
   旧代码无条件 start_task 会抛 InvalidTaskTransition 让节点白死一次。
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch


def _mk_task(status: str = "created", task_type: str = "hermes_node:deerflow",
             parent=None):
    task = MagicMock()
    task.id = "task-1"
    task.status = status
    task.task_type = task_type
    task.tenant_id = "tenant-1"
    task.parent_task_id = parent
    return task


def _call_bridge(*, executor_exc=None, executor_result=None, task_status="created",
                 task_type="hermes_node:deerflow", parent="plan-1"):
    """跑一次 dispatch_ai_task，返回 (db, ctl, task, runner, advance, 抛出的异常)。

    按 task_type 打对应路由的桩：hermes_node:* 走 _run_hermes_node，
    ai_site_build / site_build 走 _run_site_build（ROUTERS 里真实存在的两条路）。
    """
    from app.services.tasks import hermes_task_bridge as bridge

    db = MagicMock()
    task = _mk_task(status=task_status, task_type=task_type, parent=parent)
    ctl = MagicMock()
    ctl.get_task.return_value = task

    runner = MagicMock()
    if executor_exc is not None:
        runner.side_effect = executor_exc
    else:
        runner.return_value = executor_result if executor_result is not None else {"reply": "ok"}

    advance = MagicMock()
    # ROUTERS 在模块导入时就绑定了函数对象，只 patch 模块属性没用，得换表项
    if task_type.startswith("hermes_node:"):
        executor_patch = patch.object(bridge, "_run_hermes_node", runner)
    else:
        executor_patch = patch.dict(bridge.ROUTERS, {task_type: runner})
    with patch.object(bridge, "TaskControlService", return_value=ctl), \
            executor_patch, \
            patch.object(bridge, "_notify_site_built"), \
            patch("app.services.hermes.task_control_supervisor.advance_plan", advance):
        exc = None
        try:
            bridge.dispatch_ai_task(db, "task-1", tenant_id="tenant-1")
        except Exception as e:  # noqa: BLE001 — 失败分支会向上抛，交给断言
            exc = e
    return db, ctl, task, runner, advance, exc


def test_executor_failure_lands_terminal_state():
    """执行器失败 → 必须 rollback + fail_task + advance_plan，不许卡 executing。"""
    from app.services.tasks.task_control import TaskControlError

    db, ctl, _task, _runner, advance, exc = _call_bridge(
        executor_exc=TaskControlError("executor_failed", "boom")
    )

    assert exc is not None, "失败仍要向上抛给 Celery（保留重试语义）"
    assert not ctl.complete_task.called, "失败任务绝不能被标成 done"
    db.rollback.assert_called_once()
    ctl.fail_task.assert_called_once()
    assert "boom" in (ctl.fail_task.call_args.kwargs.get("error_message") or "")
    # 失败也必须推进计划，否则 on_fail / Saga 补偿策略永远不会生效
    advance.assert_called_once_with(db, "plan-1")


def test_non_state_error_also_lands_terminal():
    """普通异常（例如外键炸掉）同样要落 failed + advance_plan。"""
    db, ctl, _task, _runner, advance, exc = _call_bridge(
        executor_exc=RuntimeError("constraint blew up")
    )

    assert exc is not None
    ctl.fail_task.assert_called_once()
    assert ctl.fail_task.call_args.kwargs.get("error_code") == "EXECUTION_FAILED"
    advance.assert_called_once()
    db.rollback.assert_called_once()


def test_executing_task_skips_start_task():
    """已是 executing（人工放行或重投）时不得再调 start_task（非法状态转移）。"""
    from app.services.tasks.hermes_task_bridge import EXECUTING

    _db, ctl, _task, runner, _advance, exc = _call_bridge(
        task_status=EXECUTING, executor_result={"reply": "放行后续跑"}
    )

    assert exc is None
    ctl.start_task.assert_not_called()
    runner.assert_called_once()
    ctl.complete_task.assert_called_once()


def test_fresh_task_starts_then_completes():
    """正常路径：created → start_task → complete_task → advance_plan。"""
    _db, ctl, _task, _runner, advance, exc = _call_bridge(
        task_status="created", executor_result={"reply": "真产出"}
    )

    assert exc is None
    ctl.start_task.assert_called_once()
    ctl.complete_task.assert_called_once()
    assert ctl.complete_task.call_args.kwargs.get("output_data") == {"reply": "真产出"}
    advance.assert_called_once_with(_db, "plan-1")


def test_non_dag_task_does_not_advance_plan():
    """非 hermes_node 任务（如 ai_site_build）不该误触 DAG 推进。"""
    _db, ctl, _task, _runner, advance, exc = _call_bridge(
        task_type="ai_site_build", parent=None, executor_result={"reply": "x"}
    )

    assert exc is None
    advance.assert_not_called()
    assert ctl.start_task.call_count == 1


def test_terminal_task_returns_early():
    """已结任务直接返回，避免重试风暴把 done 改写成 failed。"""
    from app.services.tasks import hermes_task_bridge as bridge

    db = MagicMock()
    task = _mk_task(status="done")
    ctl = MagicMock()
    ctl.get_task.return_value = task

    with patch.object(bridge, "TaskControlService", return_value=ctl):
        got = bridge.dispatch_ai_task(db, "task-1", tenant_id="tenant-1")

    assert got is task
    ctl.start_task.assert_not_called()
    ctl.fail_task.assert_not_called()
    ctl.complete_task.assert_not_called()
