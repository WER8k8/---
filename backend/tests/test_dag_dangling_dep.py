"""DAG Governor 悬空依赖校验测试（P1-1 缺口修复验证）。

背景：修复前 depends_on 引用不存在的节点会被静默忽略，导致
advance_plan 中 deps_satisfied 永远为 False、节点永久挂起且无错误。
修复后 _validate_dag_topology 对悬空依赖直接 raise。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
for _f in ("config/dev/.env", ".env"):
    if os.path.isfile(_f):
        load_dotenv(_f)

import pytest

from app.schemas.hermes_orchestration import TaskGraph, TaskNode
from app.services.hermes.task_control_supervisor import _validate_dag_topology


def _graph(nodes: list[TaskNode]) -> TaskGraph:
    return TaskGraph(plan_id="p_test", event_id="e_test", nodes=nodes)


def _node(nid: str, depends_on: list[str] | None = None) -> TaskNode:
    return TaskNode(
        id=nid,
        executor="fake",
        capability="default",
        depends_on=depends_on or [],
    )


def test_dangling_dependency_raises():
    """依赖引用不存在的节点必须报错，而不是静默挂起。"""
    graph = _graph([_node("n1"), _node("n2", depends_on=["ghost_node"])])
    with pytest.raises(ValueError, match="悬空依赖"):
        _validate_dag_topology(graph.nodes)


def test_valid_dag_passes():
    """合法链式依赖不应报错。"""
    graph = _graph([_node("n1"), _node("n2", depends_on=["n1"])])
    _validate_dag_topology(graph.nodes)


def test_cycle_still_detected():
    """环路检测回归：修复悬空依赖校验不得破坏环路检测。"""
    graph = _graph([_node("n1", depends_on=["n2"]), _node("n2", depends_on=["n1"])])
    with pytest.raises(ValueError, match="环路"):
        _validate_dag_topology(graph.nodes)
