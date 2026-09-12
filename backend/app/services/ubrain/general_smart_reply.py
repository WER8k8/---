"""无 LLM 时的卖货助手智能回复：并列多种策略，结合经营快照给出可执行建议。"""

from __future__ import annotations

import re
from typing import Any

from app.services.ubrain.chat_context_service import is_strategic_question

_METRIC_PATTERNS: tuple[tuple[str, str], ...] = (
    ("inquiries", r"询盘\s*(\d+)"),
    ("leads", r"线索\s*(\d+)"),
    ("deals", r"成交\s*(\d+)"),
    ("orders", r"订单\s*(\d+)"),
    ("calls", r"电话\s*(\d+)"),
)

_STRATEGY_LABELS = ("A", "B", "C")


def parse_business_metrics(message: str) -> dict[str, int]:
    """parse_business_metrics。

    参数说明：
    :param message: 参数 message
    :return: 返回处理结果。
    """
    metrics: dict[str, int] = {}
    for key, pattern in _METRIC_PATTERNS:
        match = re.search(pattern, message)
        if match:
            metrics[key] = int(match.group(1))
    return metrics


def _company_name(memory: dict[str, Any]) -> str:
    """_company_name。

    参数说明：
    :param memory: 参数 memory
    :return: 返回处理结果。
    """
    return str(memory.get("company_name") or memory.get("brand_name") or "贵司").strip()


def _product_category(memory: dict[str, Any]) -> str:
    """_product_category。

    参数说明：
    :param memory: 参数 memory
    :return: 返回处理结果。
    """
    return str(memory.get("product_category") or "建材").strip()


def _preferred_regions(memory: dict[str, Any]) -> str:
    """_preferred_regions。

    参数说明：
    :param memory: 参数 memory
    :return: 返回处理结果。
    """
    regions = memory.get("preferred_regions") or []
    if regions:
        return "、".join(str(r) for r in regions[:4])
    return "中东、东南亚"


def _ops_lines(ops: dict[str, Any] | None) -> list[str]:
    """_ops_lines。

    参数说明：
    :param ops: 参数 ops
    :return: 返回处理结果。
    """
    if not ops or not ops.get("available", True):
        return []
    lines: list[str] = []
    pending = int(ops.get("pending_inquiries") or 0)
    with_phone = int(ops.get("pending_with_phone") or 0)
    if pending:
        lines.append(f"待处理询盘 {pending} 条（带手机 {with_phone} 条）")
    draft = int(ops.get("prospects_draft_ready") or 0)
    if draft:
        lines.append(f"待发送开发信 {draft} 条")
    for hint in (ops.get("hints") or [])[:2]:
        lines.append(str(hint))
    return lines


def _conversion_summary(metrics: dict[str, int]) -> str | None:
    """_conversion_summary。

    参数说明：
    :param metrics: 参数 metrics
    :return: 返回处理结果。
    """
    inquiries = metrics.get("inquiries") or metrics.get("leads")
    deals = metrics.get("deals") if metrics.get("deals") is not None else metrics.get("orders")
    if not inquiries or deals is None or inquiries <= 0:
        return None
    rate = deals / inquiries * 100
    verdict = (
        "低于建材 B2B 常见 20–25%，跟进节奏和报价闭环是主要缺口。"
        if rate < 20
        else "在合理区间，可把高意向线索尽快推到报价/样品。"
    )
    return f"转化率约 {rate:.1f}%（{deals}/{inquiries}），{verdict}"


def _strategy_options_export(cat, regions):
    """_strategy_options_export。

    参数说明：
    :param cat: 参数 cat
    :param regions: 参数 regions
    :return: 返回处理结果。
    """
    return [
        {
            "id": "A",
            "name": "单国深潜",
            "fit": "已锁定 1–2 个目的国",
            "actions": [
                f"说「{cat}出口越南可行性」做认证/关税/竞争度研判",
                "确认 HS 编码与本地认证清单后再报价",
            ],
            "command": f"{cat}出口越南可行性",
        },
        {
            "id": "B",
            "name": "多国比选",
            "fit": "还在选市场、想比 ROI",
            "actions": [
                f"说「{cat}蓝海市场推荐」按 {regions} 给优先级",
                "先选 2 国做小批量试单，再放大投入",
            ],
            "command": f"{cat}蓝海市场推荐",
        },
        {
            "id": "C",
            "name": "线索带出口",
            "fit": "已有询盘但不确定能不能发",
            "actions": [
                "说「最新询盘回复草稿」结合目的国写跟进",
                "在回复里明确 MOQ、交期与合规说明",
            ],
            "command": "最新询盘回复草稿",
        },
    ]


def _strategy_options_outreach(cat, regions, draft):
    """_strategy_options_outreach。

    参数说明：
    :param cat: 参数 cat
    :param regions: 参数 regions
    :param draft: 参数 draft
    :return: 返回处理结果。
    """
    return [
        {
            "id": "A",
            "name": "区域批量拓新",
            "fit": "缺新线索、要快速补池",
            "actions": [
                f"说「找{regions} 10 家{cat}采购商」生成候选",
                "再说「生成 5 封英文开发信」出草稿",
            ],
            "command": f"找{regions} 10 家{cat}采购商",
        },
        {
            "id": "B",
            "name": "存量二次触达",
            "fit": f"有 {draft or '若干'} 条草稿待发",
            "actions": [
                "优先发出已审核开发信，今日目标 5–10 封",
                "48h 无回复的做 WhatsApp/电话二次触达",
            ],
            "command": "生成 5 封英文开发信",
        },
        {
            "id": "C",
            "name": "内容引流",
            "fit": "想降低 cold email 依赖",
            "actions": [
                f"说「今晚生成 10 篇{cat}长尾 FAQ」补 SEO/GEO",
                "把高阅读文章导流到独立域表单",
            ],
            "command": f"今晚生成 10 篇{cat}长尾 FAQ",
        },
    ]


def _strategy_options_negotiation():
    """_strategy_options_negotiation。
    :return: 返回处理结果。
    """
    return [
        {
            "id": "A",
            "name": "守价换条件",
            "fit": "客户压价但仍有采购意向",
            "actions": [
                "说「客户压价 10% 怎么回」拿话术模板",
                "用更长交期/更大 MOQ 换单价，不轻易裸降",
            ],
            "command": "客户压价 10% 怎么回",
        },
        {
            "id": "B",
            "name": "样品锁单",
            "fit": "还在比价的早期阶段",
            "actions": [
                "推小批量样品单锁定规格与测试周期",
                "样品确认后再给正式批量报价",
            ],
            "command": "最新询盘回复草稿",
        },
        {
            "id": "C",
            "name": "价值加固",
            "fit": "客户只比价格、不看参数",
            "actions": [
                "补发防火/导热/认证对比一页纸",
                "强调全检、交期稳定与售后响应",
            ],
            "command": "客户要更低 MOQ 怎么谈",
        },
    ]


def build_strategy_options(
    memory: dict[str, Any],
    metrics: dict[str, int],
    ops: dict[str, Any] | None,
    *,
    topic: str = "general",
) -> list[dict[str, Any]]:
    """生成 A/B/C 三条并列策略。"""
    cat = _product_category(memory)
    regions = _preferred_regions(memory)
    pending = int((ops or {}).get("pending_inquiries") or 0)
    with_phone = int((ops or {}).get("pending_with_phone") or 0)
    draft = int((ops or {}).get("prospects_draft_ready") or 0)
    inquiries = metrics.get("inquiries") or metrics.get("leads")
    deals = metrics.get("deals") if metrics.get("deals") is not None else metrics.get("orders")
    gap = (inquiries - deals) if inquiries and deals is not None else None
    if topic == "export":
        return _strategy_options_export(cat, regions)

    if topic == "outreach":
        return _strategy_options_outreach(cat, regions, draft)

    if topic == "negotiation":
        return _strategy_options_negotiation()

    # general / conversion strategies
    strategy_a_actions: list[str] = []
    if with_phone:
        strategy_a_actions.append(
            f"今日电话回访 {with_phone} 条带手机询盘，确认规格/目的港/交期",
        )
    elif pending:
        strategy_a_actions.append(f"24h 内回复 {pending} 条待处理询盘，避免线索冷却")
    else:
        strategy_a_actions.append("说「最新询盘回复草稿」激活存量线索")
    if gap and gap > 0:
        strategy_a_actions.append(f"对未成交约 {gap} 条补正式报价单（含 MOQ/交期）")
    else:
        strategy_a_actions.append("对高意向客户今日发出口头+书面报价区间")

    strategy_b_actions = [
        f"说「找{regions} 10 家{cat}采购商」补新客候选",
        "再说「生成 5 封英文开发信」做首轮触达",
    ]
    if draft:
        strategy_b_actions.insert(0, f"先发 {draft} 条已备开发信草稿，今日目标 5 封")

    strategy_c_actions = [
        "说「本周线索复盘」看来源渠道 ROI",
        "砍掉低效渠道，把人力集中到带手机/有规格线索",
        f"必要时说「{cat}蓝海市场推荐」调整主攻市场",
    ]
    return [
        {
            "id": "A",
            "name": "存量促成交",
            "fit": "转化偏弱" if (gap and gap > 0) or with_phone else "有积压询盘",
            "actions": strategy_a_actions,
            "command": "最新询盘回复草稿",
        },
        {
            "id": "B",
            "name": "精准拓新",
            "fit": "需要补线索池、稳 pipeline",
            "actions": strategy_b_actions,
            "command": f"找{regions} 10 家{cat}采购商",
        },
        {
            "id": "C",
            "name": "渠道复盘",
            "fit": "想搞清投入产出、少做无效动作",
            "actions": strategy_c_actions,
            "command": "本周线索复盘",
        },
    ]


def format_strategy_reply(
    intro_lines: list[str],
    strategies: list[dict[str, Any]],
    *,
    footer: str | None = None,
) -> str:
    """format_strategy_reply。

    参数说明：
    :param intro_lines: 参数 intro_lines
    :param strategies: 参数 strategies
    :param footer: 参数 footer
    :return: 返回处理结果。
    """
    lines = list(intro_lines)
    lines.append("")
    lines.append("给您三条并列策略，可按资源选一条主攻（回复 A/B/C 我帮您展开）：")
    lines.append("")
    for item in strategies:
        label = item["id"]
        lines.append(f"策略 {label} · {item['name']}（适合：{item['fit']}）")
        for action in item["actions"]:
            lines.append(f"  · {action}")
        if item.get("command"):
            lines.append(f"  → 指令：「{item['command']}」")
        lines.append("")
    if footer:
        lines.append(footer)
    return "\n".join(lines).rstrip()


def _strategic_reply(
    message: str,
    memory: dict[str, Any],
    metrics: dict[str, int],
    ops: dict[str, Any] | None,
) -> tuple[str, dict[str, Any]]:
    """_strategic_reply。

    参数说明：
    :param message: 参数 message
    :param memory: 参数 memory
    :param metrics: 参数 metrics
    :param ops: 参数 ops
    :return: 返回处理结果。
    """
    company = _company_name(memory)
    intro = [f"我是{company}的卖货智能助手，先帮您拆一下："]
    summary = _conversion_summary(metrics)
    if summary:
        intro.append(f"• {summary}")
    elif metrics.get("inquiries") or metrics.get("leads"):
        n = metrics.get("inquiries") or metrics.get("leads")
        intro.append(f"• 您提到线索/询盘 {n} 条，建议按「带手机 > 有规格 > 仅留言」排序。")

    strategies = build_strategy_options(memory, metrics, ops, topic="general")
    ops_lines = _ops_lines(ops)
    footer = None
    if ops_lines:
        footer = "当前店铺快照：" + "；".join(ops_lines)
    reply = format_strategy_reply(intro, strategies, footer=footer)
    return reply, {
        "mode": "smart_strategic",
        "metrics": metrics,
        "strategies": strategies,
    }


def _capability_reply(
    memory: dict[str, Any],
    ops: dict[str, Any] | None,
    *,
    message: str = "",
) -> tuple[str, dict[str, Any]]:
    """_capability_reply。

    参数说明：
    :param memory: 参数 memory
    :param ops: 参数 ops
    :param message: 参数 message
    :return: 返回处理结果。
    """
    from app.services.ubrain.llm_assist_reply import (
        reply_with_template_and_llm,
        resolve_template_for_message,
    )
    from app.services.ubrain.reply_templates import (
        capability_plain_reply,
        greeting_plain_reply,
    )
    msg = (message or "你会干什么").strip()
    is_greeting = bool(
        re.match(r"^(你好|您好|嗨|hello|hi|在吗|在不在)[\?？!！。呀啊\s]*$", msg, re.I)
    )
    fallback = greeting_plain_reply(memory, ops) if is_greeting else capability_plain_reply(memory, ops)
    template_body, mode = resolve_template_for_message(
        msg,
        memory,
        ops,
        is_capability=True,
    )
    return reply_with_template_and_llm(
        msg,
        memory,
        template_body=template_body,
        mode=mode,
        situational="",
        ops=ops,
        fallback_reply=fallback,
        fallback_meta={
            "mode": "smart_capability",
            "capabilities": [
                "export_feasibility",
                "blue_ocean",
                "find_buyers",
                "outreach_letter_pack",
                "negotiation_draft",
                "inquiry_draft",
                "lead_content_pack",
            ],
        },
    )


def _contextual_reply(
    message: str,
    memory: dict[str, Any],
    situational: str,
    ops: dict[str, Any] | None,
) -> tuple[str, dict[str, Any]]:
    """_contextual_reply。

    参数说明：
    :param message: 参数 message
    :param memory: 参数 memory
    :param situational: 参数 situational
    :param ops: 参数 ops
    :return: 返回处理结果。
    """
    company = _company_name(memory)
    msg = message.strip()
    if re.search(r"(出口|外销|出海|越南|沙特|中东|美国)", msg):
        strategies = build_strategy_options(memory, {}, ops, topic="export")
        reply = format_strategy_reply(
            [f"我是{company}的卖货智能助手，关于{ _product_category(memory) }出口，有三种打法："],
            strategies,
            footer="仅供参考，签约前请报关或律师确认。",
        )
        return reply, {"mode": "smart_contextual", "strategies": strategies, "topic": "export"}

    if re.search(r"(开发信|邮件|触达|cold)", msg, re.I):
        strategies = build_strategy_options(memory, {}, ops, topic="outreach")
        reply = format_strategy_reply(
            ["开发信触达可以并行推进三条线，按您今天的资源选一条："],
            strategies,
            footer="发送前请在邮箱/WhatsApp 人工确认后再发出。",
        )
        return reply, {"mode": "smart_contextual", "strategies": strategies, "topic": "outreach"}

    if re.search(r"(压价|砍价|议价|报价)", msg):
        strategies = build_strategy_options(memory, {}, ops, topic="negotiation")
        reply = format_strategy_reply(
            ["谈单不必只有一种回法，给您三种策略："],
            strategies,
        )
        return reply, {"mode": "smart_contextual", "strategies": strategies, "topic": "negotiation"}

    strategies = build_strategy_options(memory, {}, ops, topic="general")
    ops_lines = _ops_lines(ops)
    intro = [f"我是{company}的卖货智能助手。"]
    if ops_lines:
        intro.append("当前：" + "；".join(ops_lines))
    intro.append(f"针对「{msg[:40]}{'…' if len(msg) > 40 else ''}」，建议从下面选一条主线：")
    reply = format_strategy_reply(
        intro,
        strategies,
        footer="补充具体目标（如本周要成交几单），我可以帮您排序 A/B/C。",
    )
    return reply, {"mode": "smart_contextual", "strategies": strategies}


def expand_strategy_choice(
    message: str,
    memory: dict[str, Any],
    *,
    ops: dict[str, Any] | None = None,
    last_strategies: list[dict[str, Any]] | None = None,
) -> tuple[str, dict[str, Any]] | None:
    """用户回复 A/B/C 时展开对应策略。"""
    choice = message.strip().upper()
    if not re.fullmatch(r"[ABC]", choice):
        if not re.search(r"^(选|我选|走|用)?\s*[ABC]\s*(策略|方案)?$", message, re.I):
            return None
        match = re.search(r"[ABC]", message.upper())
        if not match:
            return None
        choice = match.group(0)

    strategies = last_strategies or build_strategy_options(memory, {}, ops, topic="general")
    picked = next((s for s in strategies if s.get("id") == choice), None)
    if not picked:
        return None

    lines = [
        f"好的，展开策略 {choice} · {picked['name']}：",
        "",
        f"适用：{picked['fit']}",
        "",
        "建议按顺序执行：",
    ]
    for i, action in enumerate(picked["actions"], 1):
        lines.append(f"{i}. {action}")
    if picked.get("command"):
        lines.append("")
        lines.append(f"可直接发送：「{picked['command']}」")
    return "\n".join(lines), {
        "mode": "smart_strategy_expand",
        "strategy_id": choice,
        "strategy": picked,
    }


def build_smart_general_reply(
    message: str,
    memory: dict[str, Any],
    *,
    situational: str = "",
    ops: dict[str, Any] | None = None,
    is_capability_question: bool = False,
    last_strategies: list[dict[str, Any]] | None = None,
) -> tuple[str, dict[str, Any]]:
    """build_smart_general_reply。

    参数说明：
    :param message: 参数 message
    :param memory: 参数 memory
    :param situational: 参数 situational
    :param ops: 参数 ops
    :param is_capability_question: 参数 is_capability_question
    :param last_strategies: 参数 last_strategies
    :return: 返回处理结果。
    """
    expanded = expand_strategy_choice(
        message,
        memory,
        ops=ops,
        last_strategies=last_strategies,
    )
    if expanded:
        return expanded

    metrics = parse_business_metrics(message)
    if is_capability_question:
        return _capability_reply(memory, ops, message=message)

    if is_strategic_question(message) or metrics:
        return _strategic_reply(message, memory, metrics, ops)

    return _contextual_reply(message, memory, situational, ops)
