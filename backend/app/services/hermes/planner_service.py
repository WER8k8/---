# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Hermes 拆解器（Planner）—— 意图 → 任务图（智慧调度串联版）。

这是整条编排链的「大脑」入口：把一句自然语言需求拆成可执行的 TaskGraph。

三级降级 + Hybrid：
    L1 模板匹配  —— 已知意图走确定性模板（只用已注册执行器）
    L1+Skill     —— 模板参数槽被 payload/技能召回填充（Hybrid）
    L2 LLM 出图  —— 未命中模板时，ModelGateway + 技能包 top-k 上下文
    L3 最小兜底  —— 单节点直答，绝不出假图

三道安全阀：
    ① 执行器白名单  ② 拓扑治理  ③ 能力白名单

获客全链模板（对齐第二大脑 08/18/细胞总谱）：
    · 智能拓客 acquisition_smart：找客→背调→评分→千人千面信→计量
    · 社媒WA拓客 social_outreach：抓取→背调→WA触达(人审)→意图分类
    · 履约闭环 fulfillment：询盘→订单→PI→定金→CRM→单证→物流→尾款
    · 询盘转化 inquiry_convert：捕获→背调评分→报价节点(人审)
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

# ── ③ 能力白名单（注册表不可用时兜底）────────────────────────
FALLBACK_CAPABILITIES: frozenset[str] = frozenset({
    "site.generate", "site.build", "content.create",
    "research.deep_run", "seo.optimize",
    "outreach.letter", "prospect.enrich", "prospect.match",
    "negotiation.draft", "prospect.scrape", "outreach.whatsapp", "outreach.email",
    "inbox.classify",
    "lead.search", "lead.score",
    "inquiry.capture",
    "order.create", "order.sync",
    "billing.meter", "billing.invoice",
    "trade.docs", "document.generate_pi", "document.generate_trade_docs",
    "crm.sync_stage", "order.fulfill", "logistics.track", "dispatch.notify",
    "publish.multi", "publish.single",
    "nurture.create", "nurture.advance",
    "egress.assign", "egress.provision",
    "default",
})


def known_capabilities() -> frozenset[str]:
    """当前可用能力集合：优先执行器真实声明，失败回落硬编码。"""
    try:
        from app.services.hermes.executors import ExecutorRegistry
        declared = set(ExecutorRegistry.capability_names())
        if declared:
            return frozenset(declared | {"default"})
    except Exception:  # noqa: BLE001
        logger.exception("planner: 读取执行器能力声明失败，回落硬编码白名单")
    return FALLBACK_CAPABILITIES


KNOWN_CAPABILITIES = FALLBACK_CAPABILITIES

IntentBuilder = Callable[[str, str, dict[str, Any]], Optional[TaskGraph]]


# ═══════════════════════════════════════════════════════════
# L1 模板：获客莫比乌斯标准航道（只用已注册执行器）
# ═══════════════════════════════════════════════════════════

def _site_launch_graph(plan_id: str, event_id: str, payload: dict[str, Any]) -> TaskGraph:
    """建站 → 内容 → SEO → 分发(人审) → 养号 → IP → 开发信。"""
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
            approval_required=["publish.multi", "outreach.letter"],
            degradation="skip",
        ),
        nodes=[
            TaskNode(
                id="n1", executor="site_builder", capability="site.generate",
                depends_on=[],
                input={"product_name": product, "product_images": images, "auto_save": True},
                on_fail="abort", compensation_action="site.draft.delete",
            ),
            TaskNode(
                id="n2", executor="content", capability="content.create",
                depends_on=["n1"],
                input={"title": product, "page_type": "product", "status": "draft"},
                on_fail="skip",
            ),
            TaskNode(
                id="n3", executor="deerflow", capability="seo.optimize",
                depends_on=["n1"],
                input_from={"site_url": "n1.output.url", "product_name": "n1.output.product_name"},
                sop_ref="ecc://ai-seo/optimize", on_fail="skip",
            ),
            TaskNode(
                id="n4", executor="publish", capability="publish.multi",
                depends_on=["n2", "n3"],
                input={"channels": channels},
                input_from={"title": "n2.output.title", "url": "n1.output.url"},
                on_fail="skip",
            ),
            TaskNode(
                id="n5", executor="nurture", capability="nurture.create",
                depends_on=["n4"],
                input={"platform": (markets[0] if markets else "wechat"), "account_label": "主号"},
                on_fail="skip",
            ),
            TaskNode(
                id="n6", executor="egress", capability="egress.assign",
                depends_on=["n5"], input={"count": 1}, on_fail="skip",
            ),
            TaskNode(
                id="n7", executor="accio", capability="outreach.letter",
                depends_on=["n3"],
                input_from={"site_url": "n1.output.url"},
                on_fail="skip", budget={"max_tokens": 20000},
            ),
        ],
    )


def _research_graph(plan_id: str, event_id: str, payload: dict[str, Any]) -> TaskGraph:
    """深度研究（DeerFlow）。"""
    topic = str(payload.get("topic") or payload.get("message") or "").strip()
    return TaskGraph(
        plan_id=plan_id, event_id=event_id, strategy="deep",
        policies=GraphPolicies(max_parallel=1),
        nodes=[
            TaskNode(
                id="n1", executor="deerflow", capability="research.deep_run",
                depends_on=[],
                input={"topic": topic, "depth": payload.get("depth") or "standard"},
                on_fail="abort",
            ),
        ],
    )


def _outreach_graph(plan_id: str, event_id: str, payload: dict[str, Any]) -> TaskGraph:
    """智能拓客全链（获客莫比乌斯主航道）。

    找客 → 背调富化 → 评分 → 千人千面开发信(人审) → Token 计量
    对齐第二大脑 08 §8 必选节点；执行器均为已注册真实插座。
    """
    keyword = str(payload.get("keyword") or payload.get("message") or "").strip()
    country = str(payload.get("country") or "Global").strip()
    playbook_hints = payload.get("_experience_hints") or []
    skill_refs = payload.get("_skill_refs") or []

    return TaskGraph(
        plan_id=plan_id,
        event_id=event_id,
        strategy=str(payload.get("strategy") or "standard"),
        policies=GraphPolicies(
            max_parallel=2,
            budget_cap={"max_tokens_total": 80000},
            # 外发信件必须人审（compliance cell C-05）
            approval_required=["outreach.letter"],
            degradation="skip",
        ),
        nodes=[
            # ① 找客：Geo/多渠道线索
            TaskNode(
                id="n1", executor="lead", capability="lead.search",
                depends_on=[],
                input={
                    "keyword": keyword,
                    "country": country,
                    "industry": payload.get("industry") or "building_materials",
                    "limit": int(payload.get("limit") or 20),
                },
                on_fail="abort",
            ),
            # ② 背调富化：画像/公司信息（诚实失败，不造假数据）
            TaskNode(
                id="n2", executor="accio", capability="prospect.enrich",
                depends_on=["n1"],
                input_from={"prospects": "n1.output.leads", "keyword": "n1.output.keyword"},
                input={
                    "country": country,
                    "research_depth": payload.get("research_depth") or "standard",
                    "persona_lock": True,
                },
                sop_ref="ecc://osint/company-dd",
                on_fail="skip",
            ),
            # ③ 评分：证据分（无证据不默认假分）
            TaskNode(
                id="n3", executor="lead", capability="lead.score",
                depends_on=["n2"],
                input_from={"prospects": "n2.output.prospects"},
                input={"min_score": int(payload.get("min_score") or 40)},
                on_fail="skip",
            ),
            # ④ 千人千面开发信（必须人审）
            TaskNode(
                id="n4", executor="accio", capability="outreach.letter",
                depends_on=["n3"],
                input_from={
                    "prospects": "n3.output.prospects",
                    "leads": "n3.output.qualified",
                },
                input={
                    "keyword": keyword,
                    "country": country,
                    "locale": payload.get("locale") or "en",
                    "playbook_hints": playbook_hints[:3] if isinstance(playbook_hints, list) else [],
                    "skill_refs": skill_refs[:3] if isinstance(skill_refs, list) else [],
                    "human_send_required": True,
                },
                persona_ref=payload.get("persona_ref") or "agency://trade_outreach_officer",
                sop_ref=payload.get("sop_ref") or "ecc://cold-email/best-practice",
                on_fail="skip",
                budget={"max_tokens": 30000},
            ),
            # ⑤ 计量：Token/获客动作记账（三轨计费轨2）
            TaskNode(
                id="n5", executor="billing", capability="billing.meter",
                depends_on=["n4"],
                input={
                    "event_type": "lead_generated",
                    "scene": "acquisition_smart",
                    "keyword": keyword,
                    "country": country,
                },
                on_fail="skip",
            ),
        ],
    )


def _social_outreach_graph(plan_id: str, event_id: str, payload: dict[str, Any]) -> TaskGraph:
    """社媒/WhatsApp 拓客：抓取 → 背调 → WA触达(人审) → 意图分类。"""
    keyword = str(payload.get("keyword") or payload.get("message") or "").strip()
    country = str(payload.get("country") or "Global").strip()

    return TaskGraph(
        plan_id=plan_id, event_id=event_id,
        strategy="standard",
        policies=GraphPolicies(
            max_parallel=2,
            approval_required=["outreach.whatsapp", "outreach.letter"],
            degradation="skip",
        ),
        nodes=[
            TaskNode(
                id="n1", executor="trade_ai_agent", capability="prospect.scrape",
                depends_on=[],
                input={"keyword": keyword, "country": country, "channel": "social"},
                on_fail="abort",
            ),
            TaskNode(
                id="n2", executor="accio", capability="prospect.enrich",
                depends_on=["n1"],
                input_from={"prospects": "n1.output.prospects"},
                input={"country": country, "research_depth": "standard"},
                on_fail="skip",
            ),
            TaskNode(
                id="n3", executor="trade_ai_agent", capability="outreach.whatsapp",
                depends_on=["n2"],
                input_from={"prospects": "n2.output.prospects"},
                input={
                    "country": country,
                    "locale": payload.get("locale") or "en",
                    "human_send_required": True,
                },
                on_fail="skip",
                budget={"max_tokens": 20000},
            ),
            TaskNode(
                id="n4", executor="trade_ai_agent", capability="inbox.classify",
                depends_on=["n3"],
                input_from={"message": "n3.output.last_outbound"},
                input={"purpose": "acquisition_reply_triage"},
                on_fail="skip",
            ),
        ],
    )


def _fulfillment_graph(plan_id: str, event_id: str, payload: dict[str, Any]) -> TaskGraph:
    """外贸履约闭环：询盘→订单→PI→定金→CRM→单证→物流→尾款。

    对齐第二大脑 07 七步 + 细胞 N-ACQ 履约；billing 两次计量（定金/尾款）。
    """
    inquiry_ref = str(payload.get("inquiry_id") or payload.get("message") or "").strip()
    order_id = payload.get("order_id") or ""
    deposit_ratio = float(payload.get("deposit_ratio") or 0.3)

    return TaskGraph(
        plan_id=plan_id, event_id=event_id,
        strategy="standard",
        policies=GraphPolicies(
            max_parallel=2,
            approval_required=["document.generate_pi", "order.create"],
            degradation="skip",
        ),
        nodes=[
            # ① 询盘捕获/建档
            TaskNode(
                id="n1", executor="inquiry", capability="inquiry.capture",
                depends_on=[],
                input={
                    "source": payload.get("source") or "manual",
                    "raw_text": payload.get("message") or inquiry_ref,
                    "country": payload.get("country") or "",
                    "product": payload.get("product") or "",
                },
                on_fail="abort",
            ),
            # ② 订单创建（人审闸）
            TaskNode(
                id="n2", executor="order", capability="order.create",
                depends_on=["n1"],
                input_from={"inquiry_id": "n1.output.inquiry_id"},
                input={
                    "product": payload.get("product") or "",
                    "qty": payload.get("qty") or 0,
                    "incoterms": payload.get("incoterms") or "FOB",
                    "currency": payload.get("currency") or "USD",
                },
                on_fail="abort",
            ),
            # ③ PI 形式发票（人审闸）
            TaskNode(
                id="n3", executor="goodjob_crm", capability="document.generate_pi",
                depends_on=["n2"],
                input_from={"order_id": "n2.output.order_id"},
                input={
                    "incoterms": payload.get("incoterms") or "FOB",
                    "payment_terms": payload.get("payment_terms") or "T/T 30% deposit, balance before shipment",
                },
                sop_ref="ecc://pi_terms",
                on_fail="skip",
            ),
            # ④ 定金计量
            TaskNode(
                id="n4", executor="billing", capability="billing.meter",
                depends_on=["n3"],
                input_from={"order_id": "n2.output.order_id"},
                input={
                    "event_type": "deposit_received",
                    "scene": "fulfillment",
                    "ratio": deposit_ratio,
                },
                on_fail="skip",
            ),
            # ⑤ CRM 阶段推进
            TaskNode(
                id="n5", executor="goodjob_crm", capability="crm.sync_stage",
                depends_on=["n4"],
                input_from={"order_id": "n2.output.order_id"},
                input={"stage": "in_production"},
                on_fail="skip",
            ),
            # ⑥ 发运单证 CI/PL
            TaskNode(
                id="n6", executor="goodjob_crm", capability="document.generate_trade_docs",
                depends_on=["n5"],
                input_from={"order_id": "n2.output.order_id"},
                input={"docs": ["CI", "PL"]},
                on_fail="skip",
            ),
            # ⑦ 物流轨迹
            TaskNode(
                id="n7", executor="logistics", capability="logistics.track",
                depends_on=["n6"],
                input_from={"order_id": "n2.output.order_id"},
                input={"mode": payload.get("shipping_mode") or "sea"},
                on_fail="skip",
            ),
            # ⑧ 尾款计量
            TaskNode(
                id="n8", executor="billing", capability="billing.meter",
                depends_on=["n7"],
                input_from={"order_id": "n2.output.order_id"},
                input={"event_type": "final_payment_received", "scene": "fulfillment"},
                on_fail="skip",
            ),
        ],
    )


def _inquiry_convert_graph(plan_id: str, event_id: str, payload: dict[str, Any]) -> TaskGraph:
    """询盘转化轻量图：捕获 → 背调评分 → 开发/报价信草稿(人审)。"""
    raw = str(payload.get("message") or payload.get("raw_text") or "").strip()
    return TaskGraph(
        plan_id=plan_id, event_id=event_id,
        strategy="standard",
        policies=GraphPolicies(
            max_parallel=2,
            approval_required=["outreach.letter"],
            degradation="skip",
        ),
        nodes=[
            TaskNode(
                id="n1", executor="inquiry", capability="inquiry.capture",
                depends_on=[],
                input={
                    "source": payload.get("source") or "manual",
                    "raw_text": raw,
                    "country": payload.get("country") or "",
                },
                on_fail="abort",
            ),
            TaskNode(
                id="n2", executor="accio", capability="prospect.enrich",
                depends_on=["n1"],
                input_from={"prospects": "n1.output.inquiry_id"},
                input={"research_depth": "standard", "from_inquiry": True},
                on_fail="skip",
            ),
            TaskNode(
                id="n3", executor="accio", capability="outreach.letter",
                depends_on=["n2"],
                input_from={"prospects": "n2.output.prospects"},
                input={
                    "mode": "inquiry_reply_draft",
                    "locale": payload.get("locale") or "en",
                    "human_send_required": True,
                },
                on_fail="skip",
                budget={"max_tokens": 12000},
            ),
        ],
    )


# 意图关键词 → 构建器（按序匹配；具体意图优先于泛词）
_TEMPLATES: list[tuple[tuple[str, ...], IntentBuilder]] = [
    # 履约 / 订单 / PI（具体意图先匹配，避免被泛词劫持）
    (("fulfillment", "履约", "形式发票", "出运", "发货跟单", "generate_pi", "order_fulfill"),
     _fulfillment_graph),
    (("inquiry_reply", "询盘转化", "回复询盘", "询盘跟进"),
     _inquiry_convert_graph),
    # 社媒 / WhatsApp
    (("whatsapp", "社媒拓客", "社媒获客", "wa触达", "social_outreach", "私域"),
     _social_outreach_graph),
    # 建站
    (("generate_site", "site", "建站", "建官网", "落地页"),
     _site_launch_graph),
    # 研究
    (("deep_research", "research", "调研", "研报", "市场研究", "market_research"),
     _research_graph),
    # 智能拓客（泛拓客词放最后）
    (("find_leads", "outreach", "开发信", "找客户", "拓客", "获客", "acquisition", "lead_gen"),
     _outreach_graph),
]


def _minimal_graph(plan_id: str, event_id: str, payload: dict[str, Any]) -> TaskGraph:
    """L3 最小兜底：单节点直答（绝不出假图）。"""
    return TaskGraph(
        plan_id=plan_id, event_id=event_id, strategy="fast",
        policies=GraphPolicies(max_parallel=1, degradation="skip"),
        nodes=[
            TaskNode(
                id="n1", executor="deerflow", capability="default",
                depends_on=[],
                input={"message": str(payload.get("message") or ""), "fallback": True},
                on_fail="skip",
            ),
        ],
    )


# ── 安全阀 ──────────────────────────────────────────────────
def _registered_executors() -> set[str]:
    try:
        from app.services.hermes.executors import ExecutorRegistry
        return set(ExecutorRegistry.list_executors())
    except Exception:  # noqa: BLE001
        logger.exception("planner: 读取执行器注册表失败")
        return set()


def validate_graph(graph: TaskGraph) -> list[str]:
    """三道安全阀。返回违规清单（空 = 通过）。"""
    problems: list[str] = []
    registered = _registered_executors()

    for node in graph.nodes:
        if node.executor not in registered:
            problems.append(
                f"节点 {node.id}: 执行器 {node.executor!r} 未注册（已注册: {sorted(registered)}）"
            )

    allowed = known_capabilities()
    for node in graph.nodes:
        if node.capability not in allowed:
            problems.append(f"节点 {node.id}: 能力 {node.capability!r} 不在白名单")

    try:
        from app.services.hermes.task_control_supervisor import _validate_dag_topology
        _validate_dag_topology(graph.nodes)
    except Exception as exc:  # noqa: BLE001
        problems.append(f"拓扑校验失败: {exc}")

    return problems


# ── 技能包召回（DSH 外层 · 万能皆可插）──────────────────────
def _recall_skills(query: str, top_k: int = 3) -> list[dict[str, Any]]:
    """从磁盘技能包召回 top-k，供 L2 Prompt / Hybrid 使用。失败返回空。"""
    try:
        from app.services.registry.skill_pack_loader import match_skill_pack
        hits = match_skill_pack(query or "", top_k=top_k)
        out = []
        for entry, score in hits:
            out.append({
                "name": getattr(entry, "name", ""),
                "version": getattr(entry, "version", "") or "",
                "score": int(score),
                "description": (getattr(entry, "description", "") or "")[:200],
            })
        return out
    except Exception:  # noqa: BLE001
        logger.debug("planner: 技能召回失败（忽略）")
        return []


def _match_template(intent_event: IntentEvent) -> Optional[IntentBuilder]:
    """只按结构化 intent 字段优先，其次 payload 关键词（防 payload 劫持）。"""
    intent = (intent_event.intent or "").strip().lower()
    # 1) 结构化 intent 精确/前缀命中
    for keywords, builder in _TEMPLATES:
        for k in keywords:
            if intent == k.lower() or intent.startswith(k.lower()):
                return builder
    # 2) 落到 payload 文本（intent=raw_text 时）
    hay = f"{intent_event.intent} {json.dumps(intent_event.payload or {}, ensure_ascii=False)}".lower()
    for keywords, builder in _TEMPLATES:
        if any(k.lower() in hay for k in keywords):
            return builder
    return None


# ── L2：技能增强的 LLM 出图 ─────────────────────────────────
async def _llm_decompose(intent_event: IntentEvent, db: Session) -> Optional[TaskGraph]:
    """L2：ModelGateway 出图 + 技能包 top-k 上下文。失败返回 None。"""
    try:
        from app.services.model_gateway import ModelGateway
    except Exception:  # noqa: BLE001
        logger.warning("planner: ModelGateway 不可用，跳过 L2")
        return None

    registered = sorted(_registered_executors())
    query = f"{intent_event.intent} {json.dumps(intent_event.payload or {}, ensure_ascii=False)}"
    skills = _recall_skills(query, top_k=3)
    skill_block = ""
    if skills:
        skill_block = "可选技能包（仅供理解业务，节点 executor 仍必须用上表）:\n" + "\n".join(
            f"- {s['name']}: {s['description']}" for s in skills
        )

    prompt = (
        "你是任务编排拆解器。把用户需求拆成一张任务图，只输出 JSON，不要解释。\n"
        f"可用执行器（只能用这些）: {registered}\n"
        f"可用能力（只能用这些）: {sorted(known_capabilities())}\n"
        "获客/外贸需求时优先参考：找客 lead.search → 背调 accio.prospect.enrich → "
        "评分 lead.score → 开发信 accio.outreach.letter（外发需 approval）。\n"
        '输出格式: {"nodes":[{"id":"n1","executor":"...","capability":"...",'
        '"depends_on":[],"input":{},"input_from":{},"on_fail":"abort|skip"}]}\n'
        f"{skill_block}\n"
        f"用户需求: {intent_event.intent} / {json.dumps(intent_event.payload or {}, ensure_ascii=False)}"
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
        graph = TaskGraph(
            plan_id=str(uuid.uuid4()),
            event_id=intent_event.event_id,
            strategy=str(raw.get("strategy") or "standard"),
            policies=GraphPolicies(**(raw.get("policies") or {})),
            nodes=nodes,
        )
        # 外发能力强制人审（无论 LLM 是否写了 approval）
        for cap in ("outreach.letter", "outreach.whatsapp", "publish.multi"):
            if any(n.capability.startswith(cap) for n in graph.nodes):
                if cap not in graph.policies.approval_required:
                    graph.policies.approval_required.append(cap)
        return graph
    except Exception:  # noqa: BLE001
        logger.exception("planner: L2 LLM 出图失败，降级")
        return None


def _extract_json(text: str) -> Optional[dict[str, Any]]:
    if not text:
        return None
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        return json.loads(text[start:end + 1])
    except Exception:  # noqa: BLE001
        return None


def _enrich_with_experience(intent_event: IntentEvent, db: Session) -> dict:
    """经验注入 + 技能包召回 → payload._experience_hints / _skill_refs。"""
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
    except Exception:  # noqa: BLE001
        pass
    # DSH 技能召回进 payload，供 L1 Hybrid / L2 使用
    try:
        query = f"{intent_event.intent} {json.dumps(payload, ensure_ascii=False)}"
        skills = _recall_skills(query, top_k=3)
        if skills:
            payload["_skill_refs"] = skills
    except Exception:  # noqa: BLE001
        pass
    return payload


async def decompose(intent_event: IntentEvent, db: Session) -> tuple[TaskGraph, str]:
    """意图 → 任务图。

    :return: (graph, source) —— source ∈
             {"L1_template", "L1_hybrid", "L2_llm", "L3_minimal"}
    """
    intent_event.payload = _enrich_with_experience(intent_event, db)
    plan_id = str(uuid.uuid4())

    # L1 / Hybrid：命中模板且过安全阀
    builder = _match_template(intent_event)
    if builder:
        graph = builder(plan_id, intent_event.event_id, dict(intent_event.payload or {}))
        problems = validate_graph(graph)
        if not problems:
            # 有技能召回则标 hybrid（同一模板，外层已注入 skill 经验）
            has_skills = bool((intent_event.payload or {}).get("_skill_refs"))
            return graph, ("L1_hybrid" if has_skills else "L1_template")
        logger.warning("planner: L1 模板未过安全阀 %s，降级", problems)

    # L2：技能增强 LLM
    graph = await _llm_decompose(intent_event, db)
    if graph is not None:
        graph.plan_id = plan_id
        problems = validate_graph(graph)
        if not problems:
            return graph, "L2_llm"
        logger.warning("planner: L2 出图未过安全阀 %s，降级", problems)

    # L3
    graph = _minimal_graph(plan_id, intent_event.event_id, dict(intent_event.payload or {}))
    problems = validate_graph(graph)
    if problems:
        raise RuntimeError(f"planner: 最小兜底图未过安全阀 {problems}")
    return graph, "L3_minimal"
