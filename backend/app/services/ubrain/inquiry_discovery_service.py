# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Discovery 教练 — 新询盘结构化追问（MOQ / 目的港 / 规格）。"""

from __future__ import annotations

from typing import Any


def build_discovery_questions(
    *,
    product: str | None = None,
    message: str = "",
) -> list[dict[str, str]]:
    """build_discovery_questions。

    参数说明：
    :param product: 参数 product
    :param message: 参数 message
    :return: 返回处理结果。
    """
    prod = (product or "建材").strip() or "建材"
    text = message or ""
    qty_hint = "批量" if any(k in text for k in ("吨", "平", "立方", "柜", "MOQ", "批量")) else "预计采购量/MOQ"
    return [
        {
            "id": "moq",
            "label": "数量与 MOQ",
            "question": f"请确认{prod}的{qty_hint}（是否接受分批交货）。",
        },
        {
            "id": "port",
            "label": "目的港",
            "question": "请提供目的港或交货城市，以便核算 FOB/CIF 与交期。",
        },
        {
            "id": "spec",
            "label": "规格",
            "question": f"请确认{prod}规格（厚度/密度/防火等级或适用标准）。",
        },
    ]


def format_discovery_note(questions: list[dict[str, str]]) -> str:
    """format_discovery_note。

    参数说明：
    :param questions: 参数 questions
    :return: 返回处理结果。
    """
    lines = [f"{i + 1}. {q['question']}" for i, q in enumerate(questions)]
    return "【待追问】\n" + "\n".join(lines)


def attach_discovery_to_message(message: str, questions: list[dict[str, str]]) -> str:
    """attach_discovery_to_message。

    参数说明：
    :param message: 参数 message
    :param questions: 参数 questions
    :return: 返回处理结果。
    """
    base = (message or "").rstrip()
    note = format_discovery_note(questions)
    if note in base:
        return base
    return f"{base}\n\n---\n{note}"
