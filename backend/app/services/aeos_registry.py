# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""AEOS 八大子系统注册表（Desktop Hermes 蓝图落地 · 可调度/可业务调用）。

SYSTEM-LOCK-02：法定不可裁减 8 大子系统。
每个子系统：代码探针 + 运行时探针 + invoke_path（可被 biz_bot/desktop_hermes 调用）。
不编造：缺配置 ≠ 缺代码，但生产必须接通才可称已上线。
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable, Optional

# aeos_registry.py → services → app（路由/服务均在 app 下）
REPO_APP = Path(__file__).resolve().parents[1]


def _exists(*parts: str) -> bool:
    return (REPO_APP.joinpath(*parts)).exists()


def _probe_deepseek() -> dict[str, Any]:
    ok = _exists("services", "hermes", "planner_service.py") and _exists("services", "hermes", "harness_gateway.py")
    return {
        "ok": ok,
        "detail": "planner/harness 存在" if ok else "harness 缺失",
        "invoke": {"executor": "desktop_hermes", "capability": "desktop_hermes.assemble", "intent": "find_leads"},
    }


def _probe_hermes() -> dict[str, Any]:
    ok = _exists("services", "hermes", "executors") and _exists("services", "hermes", "task_control_supervisor.py")
    n = 0
    if _exists("services", "hermes", "executors"):
        n = len(list((REPO_APP / "services" / "hermes" / "executors").glob("*_executor.py")))
    return {
        "ok": ok,
        "detail": f"executor 注册 + DAG 调度（执行器文件≈{n}）" if ok else "hermes 内核缺失",
        "invoke": {"executor": "biz_bot", "capability": "biz_bot.run", "module": "orchestration"},
    }


def _probe_site_calc() -> dict[str, Any]:
    ok = _exists("services", "site_ai") or _exists("api", "v1", "routes", "site_ai_generator.py")
    return {
        "ok": ok,
        "detail": "建站/BOQ 相关路由或服务存在",
        "invoke": {"executor": "platform_ops", "capability": "platform_ops.product_catalog"},
    }


def _probe_deerflow() -> dict[str, Any]:
    ok = _exists("services", "hermes", "executors", "deerflow_executor.py")
    return {
        "ok": ok,
        "detail": "DeerFlow 执行器已注册",
        "invoke": {"executor": "content_deep", "capability": "content_deep.knowledge"},
    }


def _probe_tradeai() -> dict[str, Any]:
    """TradeAI = 本项目拓客能力域：探优丁原生模块，不探外挂 URL。"""
    native = _exists("services", "tradeai", "native_acquisition.py")
    executor = _exists("services", "hermes", "executors", "trade_ai_agent_executor.py")
    return {
        "ok": bool(native or executor),
        "detail": f"native_acquisition={'有' if native else '无'} hermes_executor={'有' if executor else '无'}（爱马仕原生直驱）",
        "runtime": "native_hermes",
        "invoke": {"executor": "trade_ai_agent", "capability": "prospect.scrape"},
    }


def _probe_goodjob() -> dict[str, Any]:
    """goodjob_crm = 本项目 CRM：探优丁原生模块，不探外挂桥。"""
    native = _exists("services", "goodjob", "native_fulfillment.py")
    slot = _exists("orchestration", "executors", "native_crm_executor.py")
    executor = _exists("services", "hermes", "executors", "goodjob_crm_executor.py")
    return {
        "ok": bool(native and executor),
        "detail": f"native_fulfillment={'有' if native else '无'} slot_adapter={'有' if slot else '无'} hermes_executor={'有' if executor else '无'}（无外桥）",
        "runtime": "native_hermes",
        "invoke": {"executor": "goodjob_crm", "capability": "document.generate_pi"},
    }


def _probe_assets() -> dict[str, Any]:
    worktree_skills = Path(__file__).resolve().parents[3] / "skills"
    skills_alt = Path(r"C:\Users\Administrator\Documents\上线网站开发完成\技能包")
    n = 0
    for cand in (worktree_skills, skills_alt):
        if cand.exists():
            n = max(n, len(list(cand.rglob("SKILL.md"))))
    ok = n > 0 or _exists("services", "registry", "skill_pack_loader.py")
    return {
        "ok": ok,
        "detail": f"技能包 SKILL.md≈{n} loader={'有' if _exists('services','registry','skill_pack_loader.py') else '无'}",
        "invoke": {"executor": "biz_bot", "capability": "biz_bot.run", "module": "skill_store"},
    }


def _probe_browser_n8n() -> dict[str, Any]:
    ok = _exists("services", "hermes", "executors", "browser_executor.py")
    n8n = (os.getenv("N8N_HOST") or os.getenv("N8N_BASE_URL") or "").strip()
    return {
        "ok": ok,
        "detail": f"browser执行器={'有' if ok else '无'} n8n_url={'有' if n8n else '未配'}",
        "runtime": "configured" if n8n else "not_configured",
        "invoke": {"executor": "growth_probe", "capability": "growth_probe.mcp_health"},
    }


SUBSYSTEMS = [
    {"id": "deepseek_harness", "name": "DeepSeek Harness 认知沙箱", "probe": _probe_deepseek},
    {"id": "hermes_inner", "name": "对内 Hermes 智慧调度", "probe": _probe_hermes},
    {"id": "site_calc_boq", "name": "Site/Calc/BOQ 入站工具", "probe": _probe_site_calc},
    {"id": "deerflow", "name": "DeerFlow 研报与内容", "probe": _probe_deerflow},
    {"id": "trade_ai", "name": "Trade AI Agent 拓客中枢", "probe": _probe_tradeai},
    {"id": "goodjob_crm", "name": "GoodJob CRM 履约单证", "probe": _probe_goodjob},
    {"id": "assets_350", "name": "350+ 智能资产/技能", "probe": _probe_assets},
    {"id": "browser_n8n", "name": "Browser Runtime / n8n 出站", "probe": _probe_browser_n8n},
]


def aeos_registry_report() -> dict[str, Any]:
    items = []
    ready = 0
    for s in SUBSYSTEMS:
        try:
            r = s["probe"]()
        except Exception as exc:  # noqa: BLE001
            r = {"ok": False, "detail": str(exc)[:120]}
        item = {
            "id": s["id"],
            "name": s["name"],
            "ok": bool(r.get("ok")),
            "detail": r.get("detail"),
            "runtime": r.get("runtime", "n/a"),
            "invoke": r.get("invoke") or {},
        }
        if r.get("ok"):
            ready += 1
        items.append(item)
    return {
        "lock": "SYSTEM-LOCK-02",
        "required": 8,
        "ready_count": ready,
        "subsystems": items,
        "all_code_present": ready >= 8,
        "plain_summary": f"AEOS 八大子系统：代码面 {ready}/8 可用；运行时以配置探针为准。",
        "hint": "法定 8 子系统不可裁减；缺配置≠缺代码，但生产必须接通才可称已上线。",
        "blueprint": "docs/AEOS_MASTER_ARCHITECTURE_SPEC.md + DesktopHermes 总案",
    }


def aeos_invoke_map() -> dict[str, dict[str, Any]]:
    """子系统 id → 可调度业务路径。"""
    out: dict[str, dict[str, Any]] = {}
    for s in SUBSYSTEMS:
        try:
            r = s["probe"]()
        except Exception:
            r = {}
        inv = r.get("invoke") or {}
        out[s["id"]] = {
            "name": s["name"],
            "code_ok": bool(r.get("ok")),
            "runtime": r.get("runtime", "n/a"),
            **inv,
        }
    return out


async def aeos_invoke_subsystem(
    subsystem_id: str,
    *,
    db: Any = None,
    tenant_id: str = "demo",
    payload: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """真调用八大子系统之一的业务路径（经已注册执行器）。"""
    amap = aeos_invoke_map()
    spec = amap.get(subsystem_id)
    if not spec:
        return {"ok": False, "subsystem_id": subsystem_id, "error": "unknown subsystem"}
    executor = spec.get("executor")
    capability = spec.get("capability")
    if not executor or not capability:
        return {
            "ok": False,
            "subsystem_id": subsystem_id,
            "code_ok": spec.get("code_ok"),
            "error": "no invoke path declared",
        }
    try:
        from app.schemas.hermes_orchestration import TaskNode
        from app.services.hermes.executors import ExecutorRegistry
        from app.services.hermes.executors.base import ExecutorContext

        ex = ExecutorRegistry.get(executor)
        node_input: dict[str, Any] = {
            "tenant_id": tenant_id,
            **(payload or {}),
        }
        if spec.get("module"):
            node_input["module"] = spec["module"]
        if spec.get("intent"):
            node_input["intent"] = spec["intent"]
        node = TaskNode(
            id=f"aeos-{subsystem_id}",
            executor=executor,
            capability=capability,
            input=node_input,
        )
        ctx = ExecutorContext(db=db, tenant_id=tenant_id, plan_id=f"aeos-{subsystem_id}")
        res = await ex.run(node, ctx)
        return {
            "ok": res.status == "succeeded",
            "subsystem_id": subsystem_id,
            "name": spec.get("name"),
            "executor": executor,
            "capability": capability,
            "status": res.status,
            "output": res.output,
            "error": res.error,
            "code_ok": spec.get("code_ok"),
            "runtime": spec.get("runtime"),
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "subsystem_id": subsystem_id,
            "executor": executor,
            "capability": capability,
            "error": str(exc)[:200],
        }


async def aeos_full_invoke(
    *,
    db: Any = None,
    tenant_id: str = "demo",
) -> dict[str, Any]:
    """八大子系统全部业务路径各跑一遍（诚实汇总）。"""
    results = []
    ok_n = 0
    for sid in [s["id"] for s in SUBSYSTEMS]:
        r = await aeos_invoke_subsystem(sid, db=db, tenant_id=tenant_id)
        results.append(r)
        if r.get("ok"):
            ok_n += 1
    report = aeos_registry_report()
    return {
        "lock": "SYSTEM-LOCK-02",
        "required": 8,
        "code_ready": report.get("ready_count"),
        "invoke_ok": ok_n,
        "invoke_total": 8,
        "results": results,
        "plain_summary": f"AEOS 代码面 {report.get('ready_count')}/8；业务调用成功 {ok_n}/8（失败项如实标注，不假成功）。",
        "all_invoke_ok": ok_n >= 8,
    }
