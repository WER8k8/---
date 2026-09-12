"""Hermes 拆解器（Planner）—— 意图 → 任务图。

这是整条编排链的「大脑」入口：把一句自然语言需求拆成可执行的 TaskGraph。
补齐的是设计文档 `docs/架构设计-智能编排内核-任务图驱动-2026-09-06.md` 的 P3 阶段。

三级降级（对齐设计文档 §4 智能化爬坡）：
    L1 模板匹配  —— 已知意图走确定性模板（复用 templates/，但只产出**已注册执行器**的节点）
    L2 LLM 出图  —— 未命中模板时，走 ModelGateway 让模型生成 TaskGraph
    L3 最小兜底  —— 两者都失败时，退化为单节点直答，绝不出假图

三道安全阀（对齐设计文档 §8 风险对策）：
    ① 执行器白名单 —— node.executor 必须在 ExecutorRegistry 里真实存在
    ② 拓扑治理     —— 复用 task_control_supervisor._validate_dag_topology（节点≤100 + 环路检测）
    ③ 能力白名单   —— node.capability 必须在本模块声明的已知能力内

设计纪律：
    · 绝不产出引用不存在执行器的图（旧 templates/ 就是栽在这里）
    · LLM 输出必须过 schema 校验，失败即降级，不硬跑假图
    · 只依赖已注册执行器，不假设未实现的能力
"""
from __future__ import annotations

import json
import logging
import uuid
from typing import Any, Callable, Optional

from sqlalchemy.orm import Session

from app.schemas.hermes_orchestration import (
    GraphPolicies,
    IntentEvent,
    TaskGraph,
    TaskNode,
)

logger = logging.getLogger(__name__)

# ── ③ 能力白名单 ────────────────────────────────────────────
# ⚠️ 现已改为**从执行器注册表动态读取**（Executor Contract）：执行器自己声明
#    `get_capabilities()`，此处硬编码仅作为**注册表不可用时的兜底**。
#    加执行器只需写文件 + 声明能力，**本模块零改动**。
FALLBACK_CAPABILITIES: frozenset[str] = frozenset({
    # 建站 / 内容 / 媒体
    "site.generate", "site.build", "content.create",
    # 研究与 SEO
    "research.deep_run", "seo.optimize",
    # 触达
    "outreach.letter", "prospect.enrich", "prospect.match",
    "negotiation.draft", "prospect.scrape", "outreach.whatsapp", "outreach.email",
    "inbox.classify",
    # 分发（真发布器）
    "publish.multi", "publish.single",
    # 养号 + 静态IP/指纹环境（业务链第 7 环）
    "nurture.create", "nurture.advance",
    "egress.assign", "egress.provision",
    # 履约与出站
    "trade.docs", "order.fulfill", "logistics.track", "dispatch.notify",
    # 兜底
    "default",
})


def known_capabilities() -> frozenset[str]:
    """当前可用能力集合。

    优先取执行器注册表的**真实声明**（Executor Contract）；
    注册表不可用或声明为空时，回落到 FALLBACK_CAPABILITIES。
    始终并入 "default"（兜底能力）。
    """
    try:
        from app.services.hermes.executors import ExecutorRegistry

        declared = set(ExecutorRegistry.capability_names())
        if declared:
            return frozenset(declared | {"default"})
    except Exception:  # noqa: BLE001 — 注册表异常不阻断，回落硬编码
        logger.exception("planner: 读取执行器能力声明失败，回落到硬编码白名单")
    return FALLBACK_CAPABILITIES


# 兼容旧引用（供外部 import）——运行时请用 known_capabilities()
KNOWN_CAPABILITIES = FALLBACK_CAPABILITIES

# ── 意图 → 模板构建器（L1）────────────────────────────────────
# 每个构建器只使用**已注册执行器**；未注册的不写进来。
IntentBuilder = Callable[[str, str, dict[str, Any]], Optional[TaskGraph]]


def _site_launch_graph(plan_id: str, event_id: str, payload: dict[str, Any]) -> TaskGraph:
    """建站 → 内容 → 分发 → 养号+IP分配 → 出站通知。

    覆盖业务链主干：路都用**已注册执行器**（site_builder / deerflow / content /
    publish / nurture / egress / accio），承载真实服务。
    """
    product = str(payload.get("product_name") or payload.get("message") or "").strip()
    images = payload.get("product_images") or []
    channels = payload.get("channels") or ["wechat", "zhihu"]
    markets = payload.get("platforms") or channels

    return TaskGraph(
        plan_id=plan_id,
        event_id=event_id,
        strategy=str(payload.get("strategy") or "standard"),
        policies=GraphPolicies(
            max_parallel=3,
            budget_cap={"max_tokens_total": 200000},
            # 分发类需人工审批（对齐设计文档 §8：publish.* 命中即挂起）
            approval_required=["publish.multi"],
            degradation="skip",
        ),
        nodes=[
            # ① 建站
            TaskNode(
                id="n1",
                executor="site_builder",
                capability="site.generate",
                depends_on=[],
                input={"product_name": product, "product_images": images, "auto_save": True},
                on_fail="abort",
                compensation_action="site.draft.delete",
            ),
            # ② 内容页（依赖建站产出）
            TaskNode(
                id="n2",
                executor="content",
                capability="content.create",
                depends_on=["n1"],
                input={"title": product, "page_type": "product", "status": "draft"},
                on_fail="skip",
            ),
            # ③ SEO 优化（DeerFlow）
            TaskNode(
                id="n3",
                executor="deerflow",
                capability="seo.optimize",
                depends_on=["n1"],
                input_from={"site_url": "n1.output.url", "product_name": "n1.output.product_name"},
                sop_ref="ecc://ai-seo/optimize",
                on_fail="skip",
            ),
            # ④ 多平台分发（真发布器；命中 approval_required 会挂起等人审）
            TaskNode(
                id="n4",
                executor="publish",
                capability="publish.multi",
                depends_on=["n2", "n3"],
                input={"channels": channels},
                input_from={"title": "n2.output.title", "url": "n1.output.url"},
                on_fail="skip",
            ),
            # ⑤ 为分发出去的账号养号（业务链第 7 环）
            TaskNode(
                id="n5",
                executor="nurture",
                capability="nurture.create",
                depends_on=["n4"],
                input={"platform": (markets[0] if markets else "wechat"), "account_label": "主号"},
                on_fail="skip",
            ),
            # ⑥ 分配独立静态 IP / 指纹环境（防多账号关联）
            TaskNode(
                id="n6",
                executor="egress",
                capability="egress.assign",
                depends_on=["n5"],
                input={"count": 1},
                on_fail="skip",
            ),
            # ⑦ 开发信触达（Accio）
            TaskNode(
                id="n7",
                executor="accio",
                capability="outreach.letter",
                depends_on=["n3"],
                input_from={"site_url": "n1.output.url"},
                on_fail="skip",
                budget={"max_tokens": 20000},
            ),
        ],
    )


def _research_graph(plan_id: str, event_id: str, payload: dict[str, Any]) -> TaskGraph:
    """深度研究（DeerFlow 单节点）。"""
    topic = str(payload.get("topic") or payload.get("message") or "").strip()
    return TaskGraph(
        plan_id=plan_id,
        event_id=event_id,
        strategy="deep",
        policies=GraphPolicies(max_parallel=1),
        nodes=[
            TaskNode(
                id="n1",
                executor="deerflow",
                capability="research.deep_run",
                depends_on=[],
                input={"topic": topic, "depth": payload.get("depth") or "standard"},
                on_fail="abort",
            ),
        ],
    )


def _outreach_graph(plan_id: str, event_id: str, payload: dict[str, Any]) -> TaskGraph:
    """拓客 + 开发信（Accio 两节点）。"""
    keyword = str(payload.get("keyword") or payload.get("message") or "").strip()
    return TaskGraph(
        plan_id=plan_id,
        event_id=event_id,
        strategy="standard",
        policies=GraphPolicies(max_parallel=2, approval_required=["outreach.letter"]),
        nodes=[
            TaskNode(
                id="n1",
                executor="accio",
                capability="prospect.enrich",
                depends_on=[],
                input={"keyword": keyword, "country": payload.get("country") or "Global"},
                on_fail="abort",
            ),
            TaskNode(
                id="n2",
                executor="accio",
                capability="outreach.letter",
                depends_on=["n1"],
                input_from={"prospects": "n1.output.leads"},
                on_fail="skip",
            ),
        ],
    )


# 意图关键词 → 构建器（按序匹配，先命中先用）
_TEMPLATES: list[tuple[tuple[str, ...], IntentBuilder]] = [
    (("generate_site", "site", "建站", "建官网", "落地页"), _site_launch_graph),
    (("deep_research", "research", "调研", "研报", "市场研究"), _research_graph),
    (("find_leads", "outreach", "开发信", "找客户", "拓客"), _outreach_graph),
]

# 最小兜底：单节点直答（绝不出假图）
def _minimal_graph(plan_id: str, event_id: str, payload: dict[str, Any]) -> TaskGraph:
    return TaskGraph(
        plan_id=plan_id,
        event_id=event_id,
        strategy="fast",
        policies=GraphPolicies(max_parallel=1, degradation="skip"),
        nodes=[
            TaskNode(
                id="n1",
                executor="deerflow",
                capability="default",
                depends_on=[],
                input={"message": str(payload.get("message") or ""), "fallback": True},
                on_fail="skip",
            ),
        ],
    )


# ── 安全阀 ──────────────────────────────────────────────────
def _registered_executors() -> set[str]:
    """运行时真实注册的执行器名集合。"""
    try:
        from app.services.hermes.executors import ExecutorRegistry

        return set(ExecutorRegistry.list_executors())
    except Exception:  # noqa: BLE001 — 注册表导入失败时不阻断，退化为空集（会被安全阀拦下）
        logger.exception("planner: 读取执行器注册表失败")
        return set()


def validate_graph(graph: TaskGraph) -> list[str]:
    """三道安全阀。返回违规清单（空 = 通过）。"""
    problems: list[str] = []
    registered = _registered_executors()

    # ① 执行器白名单
    for node in graph.nodes:
        if node.executor not in registered:
            problems.append(
                f"节点 {node.id}: 执行器 {node.executor!r} 未注册（已注册: {sorted(registered)}）"
            )

    # ③ 能力白名单（从执行器真实声明读取）
    allowed = known_capabilities()
    for node in graph.nodes:
        if node.capability not in allowed:
            problems.append(f"节点 {node.id}: 能力 {node.capability!r} 不在白名单")

    # ② 拓扑治理（复用既有实现）
    try:
        from app.services.hermes.task_control_supervisor import _validate_dag_topology

        _validate_dag_topology(graph.nodes)
    except Exception as exc:  # noqa: BLE001
        problems.append(f"拓扑校验失败: {exc}")

    return problems


# ── 主入口 ──────────────────────────────────────────────────
def _match_template(intent_event: IntentEvent) -> Optional[IntentBuilder]:
    hay = f"{intent_event.intent} {json.dumps(intent_event.payload, ensure_ascii=False)}".lower()
    for keywords, builder in _TEMPLATES:
        if any(k.lower() in hay for k in keywords):
            return builder
    return None


async def _llm_decompose(intent_event: IntentEvent, db: Session) -> Optional[TaskGraph]:
    """L2：让模型出图。走 ModelGateway（成本记账 + 合规闸门）。失败返回 None。"""
    try:
        from app.services.model_gateway import ModelGateway
    except Exception:  # noqa: BLE001
        logger.warning("planner: ModelGateway 不可用，跳过 L2")
        return None

    registered = sorted(_registered_executors())
    prompt = (
        "你是任务编排拆解器。把用户需求拆成一张任务图，只输出 JSON，不要解释。\n"
        f"可用执行器（只能用这些）: {registered}\n"
        f"可用能力（只能用这些）: {sorted(known_capabilities())}\n"
        '输出格式: {"nodes":[{"id":"n1","executor":"...","capability":"...",'
        '"depends_on":[],"input":{},"input_from":{},"on_fail":"abort|skip"}]}\n'
        f"用户需求: {intent_event.intent} / {json.dumps(intent_event.payload, ensure_ascii=False)}"
    )

    try:
        gw = ModelGateway()
        result = await gw.generate(
            prompt,
            required_capabilities=["reasoning"],
            quality="medium",
            budget=0.02,
            max_tokens=1500,
            tenant_id=intent_event.tenant_id,
        )
        content = (result or {}).get("content") or ""
        raw = _extract_json(content)
        if not raw or "nodes" not in raw:
            logger.warning("planner: L2 未产出合法 nodes")
            return None
        nodes = [TaskNode(**n) for n in raw["nodes"]]
        return TaskGraph(
            plan_id=str(uuid.uuid4()),
            event_id=intent_event.event_id,
            strategy=str(raw.get("strategy") or "standard"),
            policies=GraphPolicies(**(raw.get("policies") or {})),
            nodes=nodes,
        )
    except Exception:  # noqa: BLE001 — L2 失败必须能降级，不能炸主链
        logger.exception("planner: L2 LLM 出图失败，降级")
        return None


def _extract_json(text: str) -> Optional[dict[str, Any]]:
    """从模型输出里抠出第一个 JSON 对象。"""
    if not text:
        return None
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        return json.loads(text[start : end + 1])
    except Exception:  # noqa: BLE001
        return None



def _enrich_with_experience(intent_event: IntentEvent, db: Session) -> dict:
    """J.4: 将 experience_store 的适用经验注入 intent payload，供 L1/L2 参考。"""
    payload = dict(intent_event.payload or {})
    try:
        from app.services.evolution.experience_store import ExperienceStore
        store = ExperienceStore(db)
        scene = intent_event.scene_type or intent_event.intent or ""
        experiences = store.find_applicable(
            tenant_id=str(payload.get("tenant_id") or ""),
            scene_type=scene,
            limit=3,
        )
        if experiences:
            payload["_experience_hints"] = [
                {
                    "id": e.get("id"),
                    "type": e.get("experience_type"),
                    "summary": e.get("summary") or e.get("description") or "",
                    "score": e.get("success_score", 0),
                }
                for e in experiences[:3]
            ]
    except Exception:
        # best-effort: 体验注入失败不阻断拆解
        pass
    return payload

async def decompose(intent_event: IntentEvent, db: Session) -> tuple[TaskGraph, str]:
    """意图 → 任务图。

    :return: (graph, source) —— source ∈ {"L1_template", "L2_llm", "L3_minimal"}
    流程：L1 模板 → L2 LLM → 逐级安全阀校验 → L3 兜底。
    """
    # J.4: L4 体验引擎注入 - 从 experience_store 取相关经验辅助拆解
    intent_event.payload = _enrich_with_experience(intent_event, db)

    plan_id = str(uuid.uuid4())

    # L1
    builder = _match_template(intent_event)
    if builder:
        graph = builder(plan_id, intent_event.event_id, dict(intent_event.payload or {}))
        problems = validate_graph(graph)
        if not problems:
            return graph, "L1_template"
        logger.warning("planner: L1 模板未过安全阀 %s，降级", problems)

    # L2
    graph = await _llm_decompose(intent_event, db)
    if graph is not None:
        graph.plan_id = plan_id  # 统一 plan_id
        problems = validate_graph(graph)
        if not problems:
            return graph, "L2_llm"
        logger.warning("planner: L2 出图未过安全阀 %s，降级", problems)

    # L3
    graph = _minimal_graph(plan_id, intent_event.event_id, dict(intent_event.payload or {}))
    problems = validate_graph(graph)
    if problems:
        # 连最小图都不过，说明注册表本身有问题——如实抛，不硬跑
        raise RuntimeError(f"planner: 最小兜底图未过安全阀 {problems}")
    return graph, "L3_minimal"
