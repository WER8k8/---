# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""ai_tasks → Hermes 编排桥（打通中央断点；总纲 §4.6 / 轮24 后续）。

背景：ai_tasks 是一张"被动影子表"——状态机/checkpoint 真实，但此前没有任何代码
从 ai_tasks 读取任务去调 Hermes，导致"外部请求 → ai_tasks → Hermes 编排 → 执行 → 回结果"
整条链路在此断裂。本桥补上这块胶水：

- 读 AiTask → 按 task_type 路由到真实执行器（Hermes 内的 run_ai_site_builder_v1 等）
  → 经 TaskControlService 状态机写回 output_json / status。
- 站点建好 → 触发 n8n 出站通知（best-effort，不阻断主链路）。
- 调度主权归 Control Plane（本桥）：不反向让 n8n 编排 Hermes。
- 加场景 = 在 ROUTERS 注册一个 (task_type → 执行函数)，Hermes 主循环不动。
- 红线：任何异常都落 fail_task 并 best-effort 忽略副作用，绝不静默吞掉核心状态。

设计原则"每个环节做正确的事"：桥只负责"接 + 派 + 回写"，业务语义下沉到各执行器。
"""

from __future__ import annotations

import asyncio
import json
import logging
import concurrent.futures
from typing import Any, Callable, Optional

from sqlalchemy.orm import Session

from app.services.tasks.task_control import (
    CREATED,
    DONE,
    FAILED,
    CANCELLED,
    TIMEOUT,
    EXECUTING,
    TaskControlError,
    TaskControlService,
    TaskNotFound,
)

logger = logging.getLogger("uj-admin.tasks.hermes_bridge")

# 复用全局 OpenTelemetry tracer（复用 core/opentelemetry_config 已设的 provider，
# 不重复初始化；opentelemetry 未装/异常时静默降级，不引入硬依赖）
try:
    from opentelemetry import trace as _otel_trace
except Exception:  # noqa: BLE001
    _otel_trace = None

# 终态集合（已结任务直接跳过，避免重试风暴）
TERMINAL_STATUSES = frozenset({DONE, FAILED, CANCELLED, TIMEOUT})

# 执行器签名：db, task -> dict 结果
TaskExecutor = Callable[[Session, Any], dict[str, Any]]


def _exec_with_trace(tracer, span_name: str, executor: TaskExecutor, db: Session, task: Any) -> dict[str, Any]:
    """极简业务 Span 埋点：包裹最外层执行体，不改返回值、不吞异常。

    opentelemetry 未装时走直调（零开销），保证任何环境都不破坏主链路。
    """
    if tracer is None:
        return executor(db, task)
    with tracer.start_as_current_span(
        span_name,
        attributes={
            "task_id": str(task.id),
            "tenant_id": str(task.tenant_id or ""),
            "executor": getattr(task, "task_type", ""),
        },
    ):
        return executor(db, task)


def _run_async(coro):
    """在 Celery / FastAPI 两种宿主里都能安全执行桥内协程。"""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    if loop.is_running():
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, coro).result()
    return loop.run_until_complete(coro)


class HermesNodeExecutionError(TaskControlError):
    """执行器按契约返回 status=failed 时抛出的受控异常。

    为什么要单独一个类：TaskControlError 若用两个位置参数构造，str(exc) 会变成
    "('executor_failed', '所有平台发布均失败')" 这种元组字面量，直接污染
    ai_tasks.error_message（2026-09-10 实测）。这里保证消息是单串人话，
    同时把执行器返回的逐平台明细 output 带出来，让失败节点也能落库可查。
    """

    def __init__(
        self, code: str, message: str, output: Optional[dict[str, Any]] = None
    ):
        self.code = code
        self.output = output or {}
        super().__init__(message or code)


# ──────────────────────────────────────────────
# 执行器（直接调 Hermes 内的真实实现，绕过插件目录启用态检查）
# ──────────────────────────────────────────────
def _load_input(task: Any) -> dict[str, Any]:
    try:
        return json.loads(task.input_json or "{}")
    except (json.JSONDecodeError, TypeError):
        return {}


def _run_site_build(db: Session, task: Any) -> dict[str, Any]:
    """建站场景：自行车图片 → 多语独立站。直接调 Hermes 同款真实实现。"""
    from app.services.hermes.site_build_workflow import run_ai_site_builder_v1

    data = _load_input(task)
    product_name = str(data.get("product_name") or data.get("message") or "").strip()
    if not product_name:
        raise TaskControlError("missing_product", "建站任务需提供 product_name")

    company_name = ""
    try:
        from app.models.tenant import Tenant

        tenant = db.query(Tenant).filter(Tenant.id == task.tenant_id).first()
        company_name = tenant.name if tenant else ""
    except Exception:  # noqa: BLE001
        pass

    auto_save = bool(data.get("auto_save", True))
    use_ai = data.get("use_ai", True)
    if isinstance(use_ai, str):
        use_ai = use_ai.lower() not in ("0", "false", "no")
    raw_images = data.get("product_images") or data.get("productImages") or []
    product_images = raw_images if isinstance(raw_images, list) else []

    persist_fn = None
    if auto_save:
        try:
            from app.services.tenant_site_persistence import persist_tenant_site_content

            persist_fn = persist_tenant_site_content
        except Exception:  # noqa: BLE001
            persist_fn = None

    return asyncio.run(
        run_ai_site_builder_v1(
            db,
            tenant_id=str(task.tenant_id),
            product_name=product_name,
            company_name=company_name,
            auto_save=auto_save,
            use_ai=bool(use_ai),
            persist_fn=persist_fn,
            product_images=product_images,
        )
    )


def _run_growth_loop(db: Session, task: Any) -> dict[str, Any]:
    """增长工具 Agent：热词 → 成稿 → 质检 → 引流监测 → 汇总。"""
    from app.services.agent_loop.growth_workflow import (
        create_growth_run,
        execute_growth_run,
        get_growth_run,
    )

    data = _load_input(task)
    tenant_id = str(task.tenant_id)
    goal = str(data.get("goal") or "").strip()
    if not goal:
        raise TaskControlError("missing_goal", "growth_loop 任务需提供 goal")
    run_id = str(data.get("run_id") or "").strip()

    try:
        if not run_id:
            run = create_growth_run(
                goal=goal,
                tenant_id=tenant_id,
                user_id=str(data.get("user_id") or "") or None,
                context=data.get("context") or {},
                preset_id=data.get("preset_id"),
            )
            run_id = str(run["id"])
        execute_growth_run(db, run_id, tenant_id=tenant_id)
        result = get_growth_run(db, run_id)
        if not result:
            raise TaskControlError("growth_run_missing", f"growth run 不存在: {run_id}")
        return result
    except Exception as exc:  # noqa: BLE001
        logger.exception("growth_loop 执行失败 tenant=%s run_id=%s", tenant_id, run_id)
        raise TaskControlError("growth_loop_failed", f"{type(exc).__name__}: {exc}")


def _run_commercial_loop(db: Session, task: Any) -> dict[str, Any]:
    """商业闭环：产品数据 → 全链路商业执行。"""
    from app.services.orchestrator.commercial_loop import CommercialLoopOrchestrator

    data = _load_input(task)
    raw_product = data.get("product_data")
    if raw_product is not None and not isinstance(raw_product, dict):
        raise HermesNodeExecutionError(
            "invalid_product_data", "commercial_loop 的 product_data 必须是对象"
        )

    product_data = dict(raw_product or {})
    name = str(
        product_data.get("name") or data.get("product_name") or data.get("name") or ""
    ).strip()
    description = str(
        product_data.get("description")
        or data.get("product_description")
        or data.get("description")
        or ""
    ).strip()
    if not name or not description:
        raise HermesNodeExecutionError(
            "missing_product",
            "commercial_loop 任务需提供 product_data.name 与 product_data.description",
        )
    product_data["name"] = name
    product_data["description"] = description

    try:
        product_data["images_count"] = int(
            data.get("images_count", product_data.get("images_count", 0)) or 0
        )
    except (TypeError, ValueError):
        raise HermesNodeExecutionError(
            "invalid_images_count", "commercial_loop 的 images_count 必须是整数"
        )
    product_data["industry"] = str(data.get("industry") or product_data.get("industry") or "")

    skip_to = str(data.get("skip_to") or "").strip() or None
    try:
        result = _run_async(
            CommercialLoopOrchestrator(db).execute(
                tenant_id=str(task.tenant_id),
                product_data=product_data,
                target_market=str(data.get("target_market") or "global"),
                language=str(data.get("language") or "en"),
                skip_to=skip_to,
            )
        )
    except Exception as exc:  # noqa: BLE001 — 统一落终态，不把原始栈暴露给任务面
        logger.exception("commercial_loop 执行失败 tenant=%s", task.tenant_id)
        raise HermesNodeExecutionError(
            "commercial_loop_failed",
            f"{type(exc).__name__}: {exc}",
            output={"trace_hint": str(task.id)},
        )

    if str(result.get("status") or "") != "completed":
        raise HermesNodeExecutionError(
            "commercial_loop_failed",
            f"商业闭环未完成: status={result.get('status')}, failed_at={result.get('failed_at')}",
            output=result,
        )
    return result


def _run_video_publish(db: Session, task: Any) -> dict[str, Any]:
    """视频真发：平台列表 → 逐平台 Worker 链 + 验真。"""
    from app.services.video_publish_orchestrator import publish_platforms_batch

    data = _load_input(task)
    raw_platforms = data.get("platform_names", data.get("platforms"))
    if isinstance(raw_platforms, str):
        raw_platforms = raw_platforms.split(",")
    if not isinstance(raw_platforms, list):
        raise HermesNodeExecutionError(
            "missing_platforms", "video_publish 任务需提供 platform_names 列表"
        )
    platform_names = list(
        dict.fromkeys(str(name).strip() for name in raw_platforms if str(name).strip())
    )
    if not platform_names:
        raise HermesNodeExecutionError(
            "missing_platforms", "video_publish 任务需至少一个 platform_names"
        )

    video_url = str(data.get("video_url") or "").strip()
    cover_url = str(data.get("cover_url") or "").strip()
    title = str(data.get("title") or "").strip()
    if not video_url or not cover_url or not title:
        raise HermesNodeExecutionError(
            "missing_media", "video_publish 任务需提供 video_url / cover_url / title"
        )

    raw_tags = data.get("tags")
    if isinstance(raw_tags, str):
        tags = [tag.strip() for tag in raw_tags.split(",") if tag.strip()]
    elif isinstance(raw_tags, list):
        tags = [str(tag).strip() for tag in raw_tags if str(tag).strip()]
    else:
        tags = []

    scheduled_at = data.get("scheduled_at")
    if scheduled_at is not None:
        try:
            scheduled_at = int(scheduled_at)
        except (TypeError, ValueError):
            raise HermesNodeExecutionError(
                "invalid_scheduled_at", "video_publish 的 scheduled_at 必须是 Unix 毫秒整数"
            )

    nurture_cycle_ids = data.get("nurture_cycle_ids")
    if nurture_cycle_ids is not None and not isinstance(nurture_cycle_ids, dict):
        raise HermesNodeExecutionError(
            "invalid_nurture_cycle_ids",
            "video_publish 的 nurture_cycle_ids 必须是 {platform_name: cycle_id}",
        )

    try:
        results = _run_async(
            publish_platforms_batch(
                db,
                platform_names=platform_names,
                video_url=video_url,
                cover_url=cover_url,
                title=title,
                body=str(data.get("body") or ""),
                tags=tags,
                tenant_id=str(task.tenant_id) if task.tenant_id else None,
                scheduled_at=scheduled_at,
                nurture_cycle_ids=nurture_cycle_ids,
            )
        )
    except Exception as exc:  # noqa: BLE001 — 外部通道异常也要落终态
        logger.exception("video_publish 执行失败 tenant=%s", task.tenant_id)
        raise HermesNodeExecutionError(
            "video_publish_failed", f"{type(exc).__name__}: {exc}"
        )

    succeeded = sum(
        1 for row in results if isinstance(row, dict) and row.get("success") is True
    )
    failed = len(results) - succeeded
    output = {
        "summary": f"{succeeded}/{len(results)} 个平台验证发布成功，{failed} 个失败",
        "results": results,
        "succeeded": succeeded,
        "failed": failed,
        "partial": 0 < succeeded < len(results),
    }
    if succeeded == 0:
        raise HermesNodeExecutionError(
            "video_publish_failed",
            "所有平台发布均未通过验证",
            output=output,
        )
    return output


def _run_workflow_canvas(db: Session, task: Any) -> dict[str, Any]:
    """可视化工作流画布：nodes / edges → 服务层执行轨迹。"""
    from app.services.workflow_canvas_service import WorkflowCanvasService

    del db  # 当前画布执行器是纯内存执行，不使用数据库会话
    data = _load_input(task)
    nodes = data.get("nodes")
    edges = data.get("edges")
    if not isinstance(nodes, list) or not nodes:
        raise HermesNodeExecutionError(
            "missing_workflow_nodes", "workflow_canvas 任务需提供非空 nodes 列表"
        )
    if not isinstance(edges, list):
        raise HermesNodeExecutionError(
            "invalid_workflow_edges", "workflow_canvas 的 edges 必须是列表"
        )

    try:
        result = _run_async(
            WorkflowCanvasService().execute_workflow(
                {"nodes": nodes, "edges": edges}
            )
        )
    except Exception as exc:  # noqa: BLE001 — 画布输入错误/执行错误统一落终态
        logger.exception("workflow_canvas 执行失败 tenant=%s", task.tenant_id)
        code = "invalid_workflow" if isinstance(exc, ValueError) else "workflow_canvas_failed"
        raise HermesNodeExecutionError(code, f"{type(exc).__name__}: {exc}")

    if str(result.get("status") or "") != "success":
        raise HermesNodeExecutionError(
            "workflow_canvas_failed",
            f"画布执行未成功: status={result.get('status')}",
            output=result,
        )
    return result


def _run_ubrain_intent(db: Session, task: Any) -> dict[str, Any]:
    """U-Brain 意图编排场景：自然语言 → ubrain_orchestrator 拆解执行。"""
    from app.services.ubrain.orchestrator import ubrain_orchestrator

    data = _load_input(task)
    message = str(data.get("message") or data.get("prompt") or "").strip()
    if not message:
        raise TaskControlError("missing_message", "ubrain_intent 任务需提供 message")
    return ubrain_orchestrator.chat(
        message,
        db=db,
        tenant_id=str(task.tenant_id),
        context=data.get("context") or {},
    )


def _run_wangcai_intent(db: Session, task: Any) -> dict[str, Any]:
    """旺财贸易问答场景：自然语言 → ask_wangcai_for_tenant 统一入口。

    H.5：把旺财变成 Hermes 执行器。桥只负责「接 + 派 + 回写」，业务语义
    下沉到 tenant_wangcai_service 统一入口（router v1 知识管线 + 旧引擎降级）。"""
    from app.models.tenant import Tenant
    from app.services.tenant_wangcai_service import ask_wangcai_for_tenant

    data = _load_input(task)
    message = str(data.get("message") or data.get("prompt") or "").strip()
    if not message:
        raise TaskControlError("missing_message", "wangcai_intent 任务需提供 message")

    tenant = db.query(Tenant).filter(Tenant.id == task.tenant_id).first()
    if tenant is None:
        raise TaskControlError("tenant_missing", f"wangcai_intent 未找到租户 {task.tenant_id}")

    return ask_wangcai_for_tenant(
        db,
        tenant,
        message,
        source=str(data.get("source") or "hermes"),
        product_hint_override=data.get("product_hint"),
        language=data.get("language"),
    )


def _run_deepseek_harness(db: Session, task: Any) -> dict[str, Any]:
    """外层 DeepSeek Harness 编排场景：自然语言/任务 → dsh 外层智能体执行。

    这是"外层 DeepSeek Harness → 内层 Hermes"拓扑的对外入口之一：
    统一任务面收到 task_type=deepseek_harness 时，由本桥直接驱动 dsh 外层运行时，
    其产物/结论可再经 Hermes 内层进一步编排。dsh SDK 在此函数内懒加载，
    未安装时桥会抛出清晰错误（由 dispatch 落 fail_task，不静默吞）。
    """
    from app.services.deepseek_harness.client import run_turn

    data = _load_input(task)
    prompt = str(
        data.get("prompt") or data.get("message") or data.get("input") or ""
    ).strip()
    if not prompt:
        raise TaskControlError("missing_prompt", "deepseek_harness 任务需提供 prompt/message")

    result = run_turn(
        prompt,
        session_id=str(task.id),
        profile=data.get("profile"),
        provider=data.get("provider"),
        model=data.get("model"),
    )
    return {
        "reply": result.get("final_response"),
        "finish_reason": result.get("finish_reason"),
        "provider": result.get("provider"),
        "model": result.get("model"),
        "profile": result.get("profile"),
    }


def _run_hermes_node(db: Session, task: Any) -> dict[str, Any]:
    """执行器契约路由：hermes_node:<executor_name> 委托到 ExecutorRegistry"""
    from app.services.hermes.executors import ExecutorRegistry, ExecutorContext
    from app.schemas.hermes_orchestration import TaskNode

    parts = task.task_type.split(":", 1)
    executor_name = parts[1] if len(parts) > 1 else task.task_type
    executor = ExecutorRegistry.get(executor_name)
    data = _load_input(task)

    # 动态组装 TaskNode 契约
    node = TaskNode(
        id=str(data.get("node_id") or task.id),
        executor=executor_name,
        capability=str(data.get("capability") or "default"),
        input=data.get("effective_input") or data.get("input") or data.get("static_input") or {},
        input_from=data.get("input_from") or {},
        sop_ref=data.get("sop_ref"),
        persona_ref=data.get("persona_ref"),
    )

    # ECC SOP 注入（J.2）：sop_ref 解析为技能内容后随 node.input 传给执行器，供 LLM 遵循作业标准
    if node.sop_ref:
        from app.services.hermes.sop_resolver import resolve_sop_ref
        sop = resolve_sop_ref(node.sop_ref, db=db)
        if sop.get("content"):
            node.input = {**dict(node.input or {}), "sop": sop}

    context = ExecutorContext(
        db=db,
        tenant_id=str(task.tenant_id),
        plan_id=str(task.parent_task_id or "")
    )

    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                res = pool.submit(asyncio.run, executor.run(node, context)).result()
        else:
            res = loop.run_until_complete(executor.run(node, context))
    except RuntimeError:
        res = asyncio.run(executor.run(node, context))

    if getattr(res, "status", "") == "failed":
        # 执行器返回 failed 时，error 里通常已经带了逐项原因（如逐平台发布原因），
        # output 里还带了可用的结构化明细（如 not_configured_detail）。
        # 两者都要往下传，否则库里只剩一句"Node execution failed"，谁都查不到为什么。
        raise HermesNodeExecutionError(
            "executor_failed",
            getattr(res, "error", "") or "Node execution failed",
            output=getattr(res, "output", None),
        )

    return getattr(res, "output", {}) or {}


# task_type → 执行器（加场景只改这里，不动 Hermes 主循环）
ROUTERS: dict[str, TaskExecutor] = {
    "ai_site_build": _run_site_build,
    "site_build": _run_site_build,
    "ubrain_intent": _run_ubrain_intent,
    "wangcai_intent": _run_wangcai_intent,
    "deepseek_harness": _run_deepseek_harness,
    "growth_loop": _run_growth_loop,
    "commercial_loop": _run_commercial_loop,
    "video_publish": _run_video_publish,
    "workflow_canvas": _run_workflow_canvas,
}


# ──────────────────────────────────────────────
# 出站（best-effort）
# ──────────────────────────────────────────────
def _notify_site_built(db: Session, task: Any, result: dict[str, Any]) -> None:
    """站点建好 → n8n 出站通知用户（仅当已注册对应工作流才触发，未注册静默跳过）。"""
    try:
        from app.services.n8n.trigger import trigger_n8n_workflow

        payload = {
            "tenant_id": str(task.tenant_id),
            "task_id": str(task.id),
            "event": "site_built",
            "product": (result or {}).get("product_name"),
            "url": (result or {}).get("url") or (result or {}).get("site_url"),
        }
        trigger_n8n_workflow.delay("site_built_notify", payload)
    except Exception as exc:  # noqa: BLE001
        logger.warning("hermes_bridge: n8n 出站通知失败（已忽略）: %s", exc)


# ──────────────────────────────────────────────
# 桥入口
# ──────────────────────────────────────────────

def _fire_terminal_hooks(
    db: Session, task: Any, *, success: bool, result: Optional[dict[str, Any]] = None,
    error_code: Optional[str] = None, error_message: Optional[str] = None,
) -> None:
    """H.7：D 类机制层钩子（Evolution 经验回流 + Pipeline 关卡标记），best-effort。"""
    try:
        from app.services.hermes.node_terminal_hooks import fire_node_terminal_hooks

        report = fire_node_terminal_hooks(
            db, task, success=success, result=result,
            error_code=error_code, error_message=error_message,
        )
        logger.info("hermes_bridge: terminal hooks task=%s %s", task.id, report.summary())
    except Exception as hook_exc:  # noqa: BLE001 — 钩子失败不得翻转已落定的终态
        logger.warning("hermes_bridge: terminal hooks 未生效（已忽略）: %s", hook_exc)
def dispatch_ai_task(
    db: Session, task_id: str, *, tenant_id: Optional[str] = None
) -> Any:
    """读 AiTask → 路由到执行器 → 写回 output/status。

    这是 ai_tasks 与 Hermes 之间的桥：此前链路在此断裂（无人从 ai_tasks 调 Hermes）。
    """
    ctl = TaskControlService(db)
    task = ctl.get_task(task_id, tenant_id=tenant_id)
    if not task:
        raise TaskNotFound(task_id, tenant_id)
    if task.status in TERMINAL_STATUSES:
        return task  # 已结任务直接返回，避免重试风暴

    executor = ROUTERS.get(task.task_type)
    if not executor and task.task_type.startswith("hermes_node:"):
        executor = _run_hermes_node

    if not executor:
        logger.warning(
            "hermes_bridge: 无路由 task_type=%s，转 review 待人工/补注册", task.task_type
        )
        ctl.review_task(task.id, tenant_id=tenant_id)
        raise TaskControlError(
            "unsupported_task_type", f"未注册执行器: {task.task_type}"
        )

    # 已在 executing 的情况有两种：人工放行（resume 合法地把 wait_human 切成
    # executing 后重新入队）、以及 Celery 重投。状态机里 EXECUTING→EXECUTING 是
    # 非法转移，硬调 start_task 会抛 InvalidTaskTransition 让节点白死一次，
    # 所以这里幂等跳过——执行本身仍照常进行，终态仍由 complete/fail 落定。
    if task.status != EXECUTING:
        ctl.start_task(task.id, tenant_id=tenant_id, executor_type="hermes")
    else:
        logger.info(
            "hermes_bridge: 任务已处于 executing（人工放行或重投），幂等跳过状态切换 task=%s",
            task_id,
        )
    try:
        tracer = _otel_trace.get_tracer("youding-hermes-bridge") if _otel_trace is not None else None
        result = _exec_with_trace(
            tracer,
            f"hermes_bridge.dispatch.{task.task_type}",
            executor,
            db,
            task,
        )
        ctl.complete_task(
            task.id,
            tenant_id=tenant_id,
            output_data=result,
            # 摘要优先级：执行器自述的中文 summary → 对话回复 → 业务主名 → 报错原因
            # （分发节点没有 reply/product_name，不补 summary 这一档就永远空着）
            output_summary=str(
                (result or {}).get("summary")
                or (result or {}).get("reply")
                or (result or {}).get("product_name")
                or ""
            )[:500]
            or None,
            executor_type="hermes",
        )
        if task.task_type in ("ai_site_build", "site_build"):
            _notify_site_built(db, task, result)
        if task.task_type.startswith("hermes_node:") and task.parent_task_id:
            try:
                from app.services.hermes.task_control_supervisor import advance_plan
                advance_plan(db, str(task.parent_task_id))
            except Exception as exc:  # noqa: BLE001
                logger.warning("hermes_bridge: advance_plan 触发失败 (parent=%s): %s", task.parent_task_id, exc)
        # H.7：节点终态钩子（经验回流 + 管线关卡），best-effort 不影响主链
        _fire_terminal_hooks(db, task, success=True, result=result)
        return task
    except Exception as exc:  # noqa: BLE001
        # 含 TaskControlError：执行器按契约返回 status="failed" 时，_run_hermes_node
        # 会抛 TaskControlError。此前该分支被单独 `raise` 掉，节点状态永远停在
        # executing，既不落终态也不推进计划 —— 整条 DAG 就此僵死（2026-09-10 实测）。
        # 失败必须落终态 + 触发 advance_plan，让 on_fail/Saga 策略真正生效。
        logger.exception("hermes_bridge: 执行失败 task=%s", task_id)
        try:
            db.rollback()
        except Exception:  # noqa: BLE001 — 回滚失败不影响落终态
            pass
        ctl.fail_task(
            task.id,
            tenant_id=tenant_id,
            error_code=getattr(exc, "code", None) or "EXECUTION_FAILED",
            error_message=str(exc)[:2000],
            executor_type="hermes",
        )
        # fail_task 不写 output_json，失败节点的执行器明细（逐项原因）会整块丢失。
        # 这里补一次回写：失败不吞明细，done 和 failed 在库里同样可查。
        failure_output = getattr(exc, "output", None)
        if isinstance(failure_output, dict) and failure_output:
            try:
                task.output_json = json.dumps(failure_output, ensure_ascii=False)
                db.commit()
            except Exception:  # noqa: BLE001 — 明细回写失败不得掩盖原始异常
                logger.warning(
                    "hermes_bridge: 失败明细回写 output_json 未成功 task=%s", task_id
                )
                db.rollback()
        if task.task_type.startswith("hermes_node:") and task.parent_task_id:
            try:
                from app.services.hermes.task_control_supervisor import advance_plan
                advance_plan(db, str(task.parent_task_id))
            except Exception as notify_exc:  # noqa: BLE001
                logger.warning("hermes_bridge: advance_plan on_fail 触发失败: %s", notify_exc)
        # H.7：失败节点同样走终态钩子（失败经验是沉淀的主食）
        _fire_terminal_hooks(
            db, task, success=False, result=failure_output,
            error_code=getattr(exc, "code", None) or "EXECUTION_FAILED",
            error_message=str(exc)[:500],
        )
        raise
