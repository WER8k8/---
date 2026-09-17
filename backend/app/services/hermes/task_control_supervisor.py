# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Hermes Task Control Supervisor.
Responsible for executing the TaskGraph DAG by mapping TaskNodes to AiTasks.
"""
from typing import Dict, Any, List, Optional
import json
import logging
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import asyncio

from app.models.ai_task import AiTask, TASK_STATUSES
from app.schemas.hermes_orchestration import TaskGraph, TaskNode, ExecutorResult
from app.services.hermes.experience_engine import get_engine

logger = logging.getLogger(__name__)

MAX_DAG_NODES = 100


def _validate_dag_topology(nodes: List[TaskNode]) -> None:
    """DAG Governor: 拓扑防爆护栏与死循环检测。"""
    engine = get_engine()
    historical_exp = engine.query("dag_validation", top_k=3)

    if len(nodes) > MAX_DAG_NODES:
        raise ValueError(
            f"DAG Governor: TaskGraph 超过最大节点数限制 (上限 {MAX_DAG_NODES}，当前 {len(nodes)})"
        )

    node_ids = {n.id for n in nodes}
    # 悬空依赖校验：depends_on 引用不存在的节点会导致 advance_plan 中
    # deps_satisfied 永远为 False、节点永久挂起且无任何错误提示。
    for n in nodes:
        for dep in n.depends_on:
            if dep not in node_ids:
                raise ValueError(
                    f"DAG Governor: 节点 '{n.id}' 依赖了不存在的节点 '{dep}'（悬空依赖）"
                )
    # 邻接表：从依赖指向后续节点
    graph_adj: dict[str, list[str]] = {n.id: [] for n in nodes}
    for n in nodes:
        for dep in n.depends_on:
            if dep in node_ids:
                graph_adj[dep].append(n.id)

    # 0 = unvisited, 1 = visiting, 2 = visited
    visited = {n.id: 0 for n in nodes}

    def dfs(u: str) -> None:
        visited[u] = 1
        for v in graph_adj.get(u, []):
            if visited.get(v) == 1:
                raise ValueError(f"DAG Governor: 检测到拓扑死循环环路: '{u}' -> '{v}'")
            if visited.get(v) == 0:
                dfs(v)
        visited[u] = 2

    for n in nodes:
        if visited[n.id] == 0:
            dfs(n.id)


def parse_graph_to_tasks(db: Session, tenant_id: str, graph: TaskGraph) -> List[AiTask]:
    """Convert a TaskGraph to a set of AiTasks in the DB with DAG Governor validation."""
    # 1. 拓扑治理防御检验
    _validate_dag_topology(graph.nodes)

    trace_id = getattr(graph, "event_id", None) or f"trace-{graph.plan_id}"

    # Create the parent plan task
    plan_task = AiTask(
        tenant_id=tenant_id,
        task_type="hermes_plan",
        status="planning",
        input_json=graph.model_dump_json(),
        idempotency_key=f"plan:{graph.plan_id}",
    )
    db.add(plan_task)
    db.flush()

    node_tasks = []
    for node in graph.nodes:
        node_input = {
            "graph_plan_id": graph.plan_id,
            "node_id": node.id,
            "executor": node.executor,
            "capability": node.capability,
            "depends_on": node.depends_on,
            "static_input": node.input,
            "input_from": node.input_from,
            "sop_ref": node.sop_ref,
            "trace_id": trace_id,
        }
        status = "created" if not node.depends_on else "paused"
        
        task = AiTask(
            tenant_id=tenant_id,
            parent_task_id=plan_task.id,
            task_type=f"hermes_node:{node.executor}",
            status=status,
            input_json=json.dumps(node_input),
            idempotency_key=f"node:{graph.plan_id}:{node.id}"
        )
        db.add(task)
        node_tasks.append(task)
    
    db.commit()
    return node_tasks

def _resolve_input_from(
    input_from: dict[str, str],
    node_outputs: dict[str, dict[str, Any]],
    node_tasks: dict[str, AiTask],
) -> dict[str, Any]:
    """JsonPath / 路径表达式解析器：从上游节点 output 提取数据。
    
    支持语法：
    - "node_1.output.leads[0].email" 或 "node_1.leads"
    - 兼容 node_id 或 task_id 索引
    """
    resolved: dict[str, Any] = {}
    for target_key, expr in input_from.items():
        if not expr or not isinstance(expr, str):
            continue
        parts = expr.split(".")
        src_node = parts[0]
        sub_path = parts[1:]
        if sub_path and sub_path[0] == "output":
            sub_path = sub_path[1:]

        # 尝试通过 node_id 或 task_id 匹配上游产物
        src_data = node_outputs.get(src_node)
        if src_data is None and src_node in node_tasks:
            try:
                src_data = json.loads(node_tasks[src_node].output_json or "{}")
            except Exception:
                src_data = {}

        if src_data is None:
            resolved[target_key] = None
            continue

        val = src_data
        for p in sub_path:
            if "[" in p and p.endswith("]"):
                field_name, idx_str = p[:-1].split("[", 1)
                if field_name:
                    val = val.get(field_name) if isinstance(val, dict) else None
                if isinstance(val, list) and idx_str.isdigit():
                    idx = int(idx_str)
                    val = val[idx] if idx < len(val) else None
                else:
                    val = None
                    break
            elif isinstance(val, dict):
                val = val.get(p)
            elif isinstance(val, list) and p.isdigit():
                idx = int(p)
                val = val[idx] if idx < len(val) else None
            else:
                val = None
                break

        resolved[target_key] = val
    return resolved


def _capability_matches(capability: str, patterns: list[str]) -> bool:
    """判断 capability 是否命中审批模式列表。

    支持三种写法（对齐设计文档 §契约二 的 approval_required 语义）：
        精确:  "publish.multi"
        前缀:  "publish.*"     （匹配 publish.multi / publish.single）
        全量:  "*"

    约定：**模式写错（如写成 "publish" 漏了通配）不算命中** —— 宁可漏挂起，
    不可误放行敏感操作。
    """
    cap = (capability or "").strip()
    if not cap:
        return False
    for raw in patterns or []:
        pat = str(raw or "").strip()
        if not pat:
            continue
        if pat == "*":
            return True
        if pat.endswith(".*"):
            if cap.startswith(pat[:-1]):     # "publish.*" → 前缀 "publish."
                return True
        elif cap == pat:
            return True
    return False


def advance_plan(db: Session, plan_task_id: str) -> list[str]:
    """DAG 调度推进引擎（P0 核心）：
    
    1. 读父计划 task，若已终态直接退出。
    2. 遍历子任务构建 DAG 状态拓扑图与输出池。
    3. 若任一依赖节点 failed：依据 on_fail 策略决定 abort（触发 Saga 回滚）或跳过。
    4. 筛选 pending 节点（paused / created）：
       - 当所有 depends_on 均已完成（done / skipped）时，判定为就绪。
       - 通过 _resolve_input_from 解析数据依赖并注入 effective_input。
       - 翻转状态并派发 Celery 任务 (process_ai_task.delay)。
    5. 当所有子节点均完成，将父计划标记为 done。
    """
    plan_task = db.query(AiTask).filter(AiTask.id == plan_task_id).first()
    if not plan_task or plan_task.status in ["done", "failed", "cancelled"]:
        return []

    child_tasks = db.query(AiTask).filter(AiTask.parent_task_id == plan_task.id).all()
    if not child_tasks:
        plan_task.status = "done"
        db.commit()
        return []

    # 1. 建立节点映射
    node_tasks_by_id: dict[str, AiTask] = {}
    node_tasks_by_node_id: dict[str, AiTask] = {}
    node_outputs: dict[str, dict[str, Any]] = {}
    node_status: dict[str, str] = {}
    node_configs: dict[str, dict[str, Any]] = {}

    for task in child_tasks:
        node_tasks_by_id[str(task.id)] = task
        try:
            cfg = json.loads(task.input_json or "{}")
        except Exception:
            cfg = {}
        node_id = str(cfg.get("node_id") or task.id)
        node_tasks_by_node_id[node_id] = task
        node_configs[str(task.id)] = cfg
        node_status[node_id] = task.status
        node_status[str(task.id)] = task.status

        if task.status == "done":
            try:
                node_outputs[node_id] = json.loads(task.output_json or "{}")
                node_outputs[str(task.id)] = node_outputs[node_id]
            except Exception:
                node_outputs[node_id] = {}
                node_outputs[str(task.id)] = {}

    # 2. 检查是否有失败节点导致计划终止
    for task in child_tasks:
        if task.status == "failed":
            cfg = node_configs.get(str(task.id), {})
            on_fail = cfg.get("on_fail", "abort")
            if on_fail == "abort":
                logger.warning(
                    "advance_plan: 节点 %s 失败且策略为 abort，触发 Saga 回滚", task.id
                )
                compensate_plan(db, plan_task_id)
                get_engine().record("advance_plan", False, 0.0, error_type="abort")
                return []

    # 3. 筛选并激活就绪节点（含三重闸门：并发 / 审批 / 预算）
    dispatched_task_ids: list[str] = []
    from app.tasks.orchestration_tasks import process_ai_task

    # ── 读图策略（此前 GraphPolicies 定义了但**从未被读取**，等于空设）──
    policies: dict[str, Any] = {}
    try:
        policies = (json.loads(plan_task.input_json or "{}") or {}).get("policies") or {}
    except Exception:  # noqa: BLE001 — 策略解析失败不阻断调度
        policies = {}

    max_parallel = int(policies.get("max_parallel") or 0)          # 0 = 不限制
    approval_patterns = list(policies.get("approval_required") or [])
    budget_cap = policies.get("budget_cap") or {}
    budget_max = None
    for k in ("max_tokens_total", "max_tokens", "max_seconds"):
        if budget_cap.get(k):
            budget_max = float(budget_cap[k])
            break

    # 当前在跑 / 已消耗（用于并发与预算判定）
    running_now = sum(1 for t in child_tasks if t.status == "running")
    try:
        budget_used = sum(float(t.budget_used or 0) for t in child_tasks)
    except Exception:  # noqa: BLE001
        budget_used = 0.0
    gated_task_ids: list[str] = []   # 被闸门挡下的，需要落库状态

    for task in child_tasks:
        if task.status in ["paused", "created"]:
            cfg = node_configs.get(str(task.id), {})
            deps = cfg.get("depends_on") or []

            # 校验所有依赖是否已完成
            deps_satisfied = True
            for dep in deps:
                dep_st = node_status.get(str(dep))
                if dep_st not in ("done", "skipped"):
                    deps_satisfied = False
                    break

            if deps_satisfied:
                capability = str(cfg.get("capability") or "")

                # 先解析上游数据依赖，再判闸门。原因：命中审批门的节点状态会变成
                # wait_human，而本循环只处理 paused/created，它不会再回到这里；
                # 若此时不写入 effective_input，人工放行后执行器只能拿到 static_input。
                # 2026-09-10 端到端真跑实测：n4 publish.multi 放行后真执行，
                # 因缺 n2 产出的 title 直接报 missing_content 整节点失败，
                # 连带 n5/n6 被 Saga 取消、整条计划判 failed。
                input_from = cfg.get("input_from") or {}
                resolved_inputs = _resolve_input_from(
                    input_from, node_outputs, node_tasks_by_node_id
                )
                base_input = dict(cfg.get("static_input") or cfg.get("input") or {})
                base_input.update(resolved_inputs)
                cfg["effective_input"] = base_input

                # 闸门① 预算熔断（图级）：超预算不再派发后续节点
                if budget_max is not None and budget_used >= budget_max:
                    cfg["blocked_reason"] = (
                        f"budget_exceeded: used={budget_used} cap={budget_max}"
                    )
                    task.input_json = json.dumps(cfg)
                    task.status = "paused"
                    gated_task_ids.append(str(task.id))
                    logger.warning(
                        "advance_plan: 预算熔断，节点 %s 暂停（used=%s cap=%s）",
                        task.id, budget_used, budget_max,
                    )
                    continue

                # 闸门② 人工审批（命中 approval_required 即挂起，等人审）
                if approval_patterns and _capability_matches(capability, approval_patterns):
                    cfg["blocked_reason"] = f"approval_required: capability={capability}"
                    task.input_json = json.dumps(cfg)
                    task.status = "wait_human"
                    gated_task_ids.append(str(task.id))
                    logger.info(
                        "advance_plan: 节点 %s 命中审批闸（cap=%s），挂起待人工",
                        task.id, capability,
                    )

                    # 同步到 Paperclip 审批单（幂等创建），不影响主调度流
                    try:
                        from app.services.tasks.paperclip_approval_bridge import (
                            create_task_approval,
                        )
                        create_task_approval(db, task, cfg["blocked_reason"])
                    except Exception:  # noqa: BLE001 — 桥挂不阻断编排
                        logger.exception("advance_plan: Paperclip 审批登记失败 task=%s", task.id)
                    continue

                # 闸门③ 并发上限（max_parallel）：本轮超出即留到下一轮
                if max_parallel and running_now >= max_parallel:
                    logger.info(
                        "advance_plan: 并发已达上限 %s，节点 %s 留待下一轮",
                        max_parallel, task.id,
                    )
                    continue

                task.input_json = json.dumps(cfg)
                task.status = "created"
                db.add(task)
                dispatched_task_ids.append(str(task.id))
                running_now += 1   # 计入本轮并发

    # 4. 先 Commit 释放行锁，彻底规避并发与 Eager 模式下的死锁
    db.commit()

    # 5. 释放行锁后再派发 Celery / 本地任务
    for tid in dispatched_task_ids:
        try:
            process_ai_task.delay(tid)
        except Exception as exc:
            logger.warning("Celery process_ai_task.delay 失败，尝试本地同步降级: %s", exc)
            from app.services.tasks.hermes_task_bridge import dispatch_ai_task
            try:
                dispatch_ai_task(db, tid)
            except Exception as bridge_exc:
                logger.exception("本地降级执行失败: %s", bridge_exc)

    # 6. 重新检查全计划是否全部完成
    child_tasks = db.query(AiTask).filter(AiTask.parent_task_id == plan_task.id).all()
    all_terminal = True
    all_succeeded = True
    for task in child_tasks:
        if task.status not in ("done", "skipped", "failed", "cancelled"):
            all_terminal = False
            break
        if task.status in ("failed", "cancelled"):
            all_succeeded = False

    if all_terminal:
        plan_task.status = "done" if all_succeeded else "failed"
        db.add(plan_task)
        get_engine().record("advance_plan", all_succeeded, 0.0,
                           error_type=None if all_succeeded else "partial_failure")
    elif plan_task.status != "executing":
        plan_task.status = "executing"
        db.add(plan_task)

    db.commit()
    return dispatched_task_ids


def compensate_plan(db: Session, plan_task_id: str):
    """Saga Pattern Compensation.
    Triggered when a node fails and the plan policies dictate an abort/rollback.
    This safely unwinds completed operations and refunds budgets.
    """
    plan_task = db.query(AiTask).filter(AiTask.id == plan_task_id).first()
    if not plan_task:
        return

    logger.warning(f"Initiating Saga Compensation for Plan: {plan_task_id}")

    # 1. Fetch all child nodes for this plan
    child_tasks = db.query(AiTask).filter(AiTask.parent_task_id == plan_task.id).all()

    for task in child_tasks:
        try:
            node_input = json.loads(task.input_json or "{}")
        except Exception:
            continue

        comp_action = node_input.get("compensation_action")

        # 2. If node was 'done' or 'executing', and has a compensation action, execute it.
        if task.status in ["done", "executing"] and comp_action:
            logger.info(
                f"Executing compensation {comp_action} for node {node_input.get('node_id')}"
            )
            task.status = "cancelled"
            task.error_message = f"Saga Rollback executed: {comp_action}"

        elif task.status in ["created", "paused", "planning"]:
            task.status = "cancelled"

    plan_task.status = "failed"
    plan_task.error_message = "Plan failed, Saga compensation completed."
    db.commit()
    logger.info(f"Saga Compensation Complete for Plan: {plan_task_id}")
