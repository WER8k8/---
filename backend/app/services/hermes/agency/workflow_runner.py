# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""agency-orchestrator YAML 工作流执行 — Hermes 驱动的 Python DAG 引擎。"""

from __future__ import annotations

import asyncio
import logging
import re
from collections import deque
from pathlib import Path
from typing import Any

import yaml

from app.services.hermes.agency.role_loader import load_role

logger = logging.getLogger(__name__)

_DATA_ROOT = Path(__file__).resolve().parents[3] / "data"
_DEFAULT_WORKFLOWS_DIR = _DATA_ROOT / "agency_workflows"

_VAR_RE = re.compile(r"\{\{([^}]+)\}\}")


def resolve_workflows_dir() -> Path:
    """resolve_workflows_dir。
    :return: 返回处理结果。
    """
    try:
        from app.core.config import settings
        custom = getattr(settings, "AGENCY_WORKFLOWS_DIR", None)
        if custom:
            p = Path(str(custom))
            if p.is_dir():
                return p
    except Exception:
        pass
    return _DEFAULT_WORKFLOWS_DIR


def list_workflow_files() -> list[Path]:
    """list_workflow_files。
    :return: 返回处理结果。
    """
    root = resolve_workflows_dir()
    if not root.is_dir():
        return []
    return sorted(root.rglob("*.yaml"))


def workflow_id_from_path(path: Path) -> str:
    """workflow_id_from_path。

    参数说明：
    :param path: 参数 path
    :return: 返回处理结果。
    """
    root = resolve_workflows_dir()
    rel = path.relative_to(root).with_suffix("")
    return rel.as_posix()


def _resolve_workflow_path(workflow_id: str) -> Path:
    """_resolve_workflow_path。

    参数说明：
    :param workflow_id: 参数 workflow_id
    :return: 返回处理结果。
    """
    root = resolve_workflows_dir()
    wid = workflow_id.replace("\\", "/").strip().strip("/")
    if wid.endswith(".yaml"):
        wid = wid[:-5]
    direct = root / f"{wid}.yaml"
    if direct.is_file():
        return direct
    stem = Path(wid).name
    matches = [p for p in root.rglob("*.yaml") if p.stem == stem]
    if len(matches) == 1:
        return matches[0]
    for p in root.rglob("*.yaml"):
        if workflow_id_from_path(p) == wid:
            return p
    raise FileNotFoundError(f"workflow_not_found:{wid}")


def load_workflow_yaml(workflow_id: str) -> dict[str, Any]:
    """load_workflow_yaml。

    参数说明：
    :param workflow_id: 参数 workflow_id
    :return: 返回处理结果。
    """
    path = _resolve_workflow_path(workflow_id)
    wid = workflow_id_from_path(path)
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    data["_file"] = str(path)
    data["_id"] = wid
    return data


def list_workflows() -> list[dict[str, Any]]:
    """list_workflows。
    :return: 返回处理结果。
    """
    rows: list[dict[str, Any]] = []
    for p in list_workflow_files():
        wid = workflow_id_from_path(p)
        try:
            with open(p, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        except Exception:
            data = {}
        category = wid.split("/")[0] if "/" in wid else "root"
        rows.append(
            {
                "workflow_id": wid,
                "name": data.get("name") or p.stem,
                "description": data.get("description") or "",
                "step_count": len(data.get("steps") or []),
                "category": category,
            }
        )
    return rows


def _substitute(template: str, ctx: dict[str, Any]) -> str:
    """_substitute。

    参数说明：
    :param template: 参数 template
    :param ctx: 参数 ctx
    :return: 返回处理结果。
    """
    def repl(m: re.Match[str]) -> str:
        """repl。

        参数说明：
        :param m: 参数 m
        :return: 返回处理结果。
        """
        key = m.group(1).strip()
        return str(ctx.get(key, m.group(0)))

    return _VAR_RE.sub(repl, template or "")


def _topo_order(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """_topo_order。

    参数说明：
    :param steps: 参数 steps
    :return: 返回处理结果。
    """
    by_id = {str(s["id"]): s for s in steps if s.get("id")}
    indeg = {sid: 0 for sid in by_id}
    graph: dict[str, list[str]] = {sid: [] for sid in by_id}
    for sid, step in by_id.items():
        for dep in step.get("depends_on") or []:
            dep = str(dep)
            if dep in by_id:
                graph[dep].append(sid)
                indeg[sid] += 1
    q = deque([sid for sid, d in indeg.items() if d == 0])
    ordered: list[str] = []
    while q:
        sid = q.popleft()
        ordered.append(sid)
        for nxt in graph.get(sid, []):
            indeg[nxt] -= 1
            if indeg[nxt] == 0:
                q.append(nxt)
    if len(ordered) != len(by_id):
        raise ValueError("workflow_cycle_detected")
    return [by_id[sid] for sid in ordered]


async def _invoke_step_llm(
    db: Any,
    *,
    role_id: str,
    task: str,
    tenant_id: str | None,
    task_type: str,
    max_tokens: int = 2048,
    llm_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """_invoke_step_llm。

    参数说明：
    :param db: 参数 db
    :param role_id: 参数 role_id
    :param task: 参数 task
    :param tenant_id: 参数 tenant_id
    :param task_type: 参数 task_type
    :param max_tokens: 参数 max_tokens
    :param llm_config: 参数 llm_config
    :return: 返回处理结果。
    """
    from app.services.hermes.agency.llm_router import invoke_agency_llm
    role = load_role(role_id)
    system = (role or {}).get("system_prompt") or f"你是专家角色 {role_id}。"
    llm = dict(llm_config or {})
    if max_tokens and not llm.get("max_tokens"):
        llm["max_tokens"] = max_tokens
    return await invoke_agency_llm(
        db,
        system_prompt=system,
        user_message=task,
        llm=llm or None,
        tenant_id=tenant_id,
        task_type=task_type,
        lane="customer",
    )


def _ai_available(db: Any) -> bool:
    """_ai_available。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    try:
        from app.services.hermes.agency.llm_router import list_providers
        if getattr(_settings(), "HERMES_AGENCY_LLM_ENABLED", True):
            if any(p.get("available") for p in list_providers(probe=True)):
                return True
    except Exception:
        pass
    try:
        from app.services.ai_key_probe import ai_key_status
        if db is None:
            return False
        return bool(ai_key_status(db).get("has_real_key"))
    except Exception:
        return False


def _settings():
    """_settings。
    :return: 返回处理结果。
    """
    from app.core.config import settings
    return settings


async def run_workflow_async(
    db: Any,
    *,
    workflow_id: str,
    inputs: dict[str, Any],
    tenant_id: str | None = None,
    max_steps: int | None = None,
) -> dict[str, Any]:
    """run_workflow_async。

    参数说明：
    :param db: 参数 db
    :param workflow_id: 参数 workflow_id
    :param inputs: 参数 inputs
    :param tenant_id: 参数 tenant_id
    :param max_steps: 参数 max_steps
    :return: 返回处理结果。
    """
    wf = load_workflow_yaml(workflow_id)
    steps_def = wf.get("steps") or []
    if not steps_def:
        raise ValueError("workflow_empty")

    ctx: dict[str, Any] = dict(inputs or {})
    for inp in wf.get("inputs") or []:
        if not isinstance(inp, dict):
            continue
        name = inp.get("name")
        if name and name not in ctx and inp.get("default") is not None:
            ctx[name] = inp["default"]

    ordered = _topo_order(steps_def)
    if max_steps is not None:
        ordered = ordered[: max(1, max_steps)]

    use_ai = _ai_available(db)
    step_records: list[dict[str, Any]] = []
    outputs: dict[str, str] = {}
    llm_block = wf.get("llm") if isinstance(wf.get("llm"), dict) else {}
    for step in ordered:
        sid = str(step.get("id") or "")
        role_id = str(step.get("role") or "")
        task_tpl = str(step.get("task") or "")
        task = _substitute(task_tpl, {**ctx, **outputs})
        record: dict[str, Any] = {
            "id": sid,
            "role": role_id,
            "title": sid,
            "status": "pending",
        }
        if not use_ai:
            placeholder = f"[模板] {sid} — 角色 {role_id}\n{task[:180]}…"
            out_key = step.get("output")
            if out_key:
                outputs[str(out_key)] = placeholder
                ctx[str(out_key)] = placeholder
            record.update({"status": "degraded", "summary": "无 AI Key，规则占位"})
            step_records.append(record)
            continue

        try:
            llm_out = await _invoke_step_llm(
                db,
                role_id=role_id,
                task=task,
                tenant_id=tenant_id,
                task_type=f"agency_wf_{workflow_id}_{sid}"[:64],
                max_tokens=int(llm_block.get("max_tokens") or 2048),
                llm_config=llm_block,
            )
            text = str(llm_out.get("content") or "").strip()
        except Exception as exc:
            logger.warning("agency step llm failed wf=%s step=%s: %s", workflow_id, sid, exc)
            record.update({"status": "failed", "summary": str(exc)[:160]})
            step_records.append(record)
            raise

        out_key = step.get("output")
        if out_key:
            outputs[str(out_key)] = text
            ctx[str(out_key)] = text
        record.update(
            {
                "status": "success",
                "summary": text[:200].replace("\n", " "),
                "role_name": (load_role(role_id) or {}).get("name"),
                "llm_provider": llm_out.get("provider_used"),
                "llm_routing": llm_out.get("routing"),
            }
        )
        step_records.append(record)

    return {
        "workflow_id": workflow_id,
        "workflow_name": wf.get("name") or workflow_id,
        "source": "agency_orchestrator" if use_ai else "template",
        "llm": {
            "provider": llm_block.get("provider"),
            "model": llm_block.get("model"),
        },
        "steps": step_records,
        "outputs": outputs,
        "context": {k: v for k, v in ctx.items() if not str(k).startswith("_")},
    }


def run_workflow(
    db: Any,
    *,
    workflow_id: str,
    inputs: dict[str, Any],
    tenant_id: str | None = None,
    max_steps: int | None = None,
) -> dict[str, Any]:
    """run_workflow。

    参数说明：
    :param db: 参数 db
    :param workflow_id: 参数 workflow_id
    :param inputs: 参数 inputs
    :param tenant_id: 参数 tenant_id
    :param max_steps: 参数 max_steps
    :return: 返回处理结果。
    """
    return asyncio.run(
        run_workflow_async(
            db,
            workflow_id=workflow_id,
            inputs=inputs,
            tenant_id=tenant_id,
            max_steps=max_steps,
        )
    )
