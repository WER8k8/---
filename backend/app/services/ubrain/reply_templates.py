# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""财旺/UBrain 预制回复模板 — 事实与指令骨架；口语润色由 LLM assist 完成。"""

from __future__ import annotations

from typing import Any


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


def capability_template(
    memory: dict[str, Any],
    ops: dict[str, Any] | None = None,
) -> str:
    """能力介绍 / 你会干什么 — 预制要点（不含 A/B/C 编号）。"""
    company = _company_name(memory)
    cat = _product_category(memory)
    regions = _preferred_regions(memory)
    lines = [
        f"身份：财旺，{company}工作台卖货助手",
        "语气：口语、同事聊天，2–5 段，不要策略 A/B/C 编号",
        "",
        "必须覆盖的能力（各用一句口语说明即可）：",
        f"· 出口能不能做 — 示例：「{cat}能出口沙特吗」",
        f"· 选市场 — 示例：「{cat}蓝海市场推荐」",
        f"· 找买家 — 示例：「找{regions} 10 家{cat}采购商」",
        "· 开发信/谈单 — 示例：「生成 5 封英文开发信」「客户压价 10% 怎么回」",
        "· 询盘跟进 — 示例：「最新询盘回复草稿」",
        "· 内容引流 — 示例：「今晚生成 10 篇长尾 FAQ」",
    ]
    ops_lines = _ops_lines(ops)
    if ops_lines:
        lines.extend(["", "可顺带提一句当前店铺（勿编造数字）：", *ops_lines])
    lines.extend(
        [
            "",
            "结尾：问用户今天想先推获客还是跟询盘，邀请直接说一句话即可",
        ]
    )
    return "\n".join(lines)


def capability_plain_reply(
    memory: dict[str, Any],
    ops: dict[str, Any] | None = None,
) -> str:
    """无 LLM 时的用户可见纯文本（与 capability_template 同内容，已排版）。"""
    company = _company_name(memory)
    cat = _product_category(memory)
    regions = _preferred_regions(memory)
    lines = [
        f"嗨，我是财旺，{company}工作台里的卖货助手～",
        "",
        "您直接说想干嘛就行，不用记命令。我常帮这几类事：",
        "",
        f"· 出口能不能做：比如「{cat}能出口沙特吗」",
        f"· 选市场：「{cat}蓝海市场推荐」",
        f"· 找买家：「找{regions} 10 家{cat}采购商」",
        "· 开发信 / 谈单：「生成 5 封英文开发信」「客户压价 10% 怎么回」",
        "· 询盘跟进：「最新询盘回复草稿」",
        "· 内容引流：「今晚生成 10 篇长尾 FAQ」",
    ]
    ops_lines = _ops_lines(ops)
    if ops_lines:
        lines.extend(["", "刚看了眼您这边：" + "；".join(ops_lines)])
    lines.extend(["", "今天想先推获客，还是把手头询盘跟一圈？跟我说一句就行。"])
    return "\n".join(lines)


def greeting_plain_reply(memory: dict[str, Any], ops: dict[str, Any] | None = None) -> str:
    """greeting_plain_reply。

    参数说明：
    :param memory: 参数 memory
    :param ops: 参数 ops
    :return: 返回处理结果。
    """
    company = _company_name(memory)
    lines = [
        f"您好，我是财旺，{company}的卖货助手～",
        "出口研判、找买家、开发信和询盘回复我都能帮。",
    ]
    ops_lines = _ops_lines(ops)
    if ops_lines:
        lines.append("刚看了眼：" + "；".join(ops_lines))
    lines.append("今天想先推获客，还是跟询盘？")
    return "\n".join(lines)


def greeting_template(
    memory: dict[str, Any],
    ops: dict[str, Any] | None = None,
) -> str:
    """greeting_template。

    参数说明：
    :param memory: 参数 memory
    :param ops: 参数 ops
    :return: 返回处理结果。
    """
    company = _company_name(memory)
    lines = [
        f"身份：财旺，{company}卖货助手",
        "用户只是在打招呼，简短回应即可（1–3 句）",
        "可轻点一句：出口研判、找买家、询盘回复都能帮",
        "结尾问：今天想推进获客还是询盘",
    ]
    ops_lines = _ops_lines(ops)
    if ops_lines:
        lines.append("若有数据可提一句：" + "；".join(ops_lines))
    return "\n".join(lines)


def polish_scaffold_from_smart_reply(smart_reply: str, *, mode: str) -> str:
    """将规则/smart 回复包装为 LLM 润色用的预制骨架。"""
    return (
        f"回复模式：{mode}\n"
        "以下是要点骨架，请改写成自然口语，保留全部事实与数字，不要添加 A/B/C 编号：\n\n"
        f"{smart_reply.strip()}"
    )
