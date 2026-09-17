"""轻量 AST 断言：hermes_task_bridge 编排执行点存在业务 Span 埋点。

不改业务逻辑，仅验证"埋点调用存在"这一契约，防止后续重构把它删掉。
不依赖外部服务（不连库/不改 provider）。
"""
import ast
from pathlib import Path


def _module_path():
    return Path(__file__).resolve().parents[2] / "app" / "services" / "tasks" / "hermes_task_bridge.py"


def test_exec_with_trace_uses_start_as_current_span():
    """核心执行调度必须经 _exec_with_trace（opentelemetry 缺失时降级直调）。"""
    tree = ast.parse(_module_path().read_text(encoding="utf-8"))

    fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "_exec_with_trace")
    src = ast.get_source_segment(_module_path().read_text(encoding="utf-8"), fn)
    assert "start_as_current_span" in src
    # 必须挂业务语义属性
    assert "task_id" in src and "tenant_id" in src and "executor" in src
    # 必须不吞异常（返回值即 executor 返回）
    assert "return executor(db, task)" in src


def test_dispatch_invokes_tracing_helper():
    """dispatch_ai_task 的执行点必须调用 _exec_with_trace，埋点落在最外层执行体上。"""
    src = _module_path().read_text(encoding="utf-8")
    tree = ast.parse(src)
    fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "dispatch_ai_task")
    dsrc = ast.get_source_segment(src, fn)
    assert "_exec_with_trace(" in dsrc
    assert "get_tracer(" in dsrc