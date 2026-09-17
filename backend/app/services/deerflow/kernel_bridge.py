# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""DeerFlow 内核桥接 — 内容产出时抽取事实层为 FactKernel。

对应缺口 #8：DeerFlow 出 9 意图内容时，把「事实层」抽成内核 JSON，
供统一发布台按平台形态投影（A 搜索 / B 社媒 / C B2B / D 知识系），
替代同一篇长文端给 40 家。

只从子任务 output 里读、不写 DB、不发网络；可离线单测。
事实层来源优先级：output.fact_kernel（上游已给）> output.product（产品快照）
> output 顶层硬字段（moq/lead_time/certifications）。
"""

from __future__ import annotations

from typing import Any, Optional

from app.services.geo.content_kernel import FactKernel

# 触发内核抽取的 DeerFlow intent（内容/建站/SEO 类才需要事实层）
_KERNEL_INTENTS = {
    "content_creation",
    "page_creation",
    "seo_publish",
    "seo_metadata",
    "keyword_research",
}


def extract_kernel_from_subtask(intent: str, output: Optional[dict[str, Any]]) -> Optional[FactKernel]:
    """从子任务 intent + output 抽取事实内核。

    返回 None 表示该意图不产生事实层（非内容类），调用方据此跳过投影。
    绝不编造：output 里没有的字段内核会如实降级。
    """
    if intent not in _KERNEL_INTENTS:
        return None
    out = dict(output or {})

    raw: dict[str, Any] = {
        "entity_name": out.get("entity_name") or out.get("title") or out.get("name"),
        "entity_type": out.get("entity_type", "product"),
        "attrs": dict(out.get("attrs") or {}),
        "trade": out.get("trade") or {},
        "evidence": out.get("evidence") or [],
        "copy": out.get("copy") or {},
        "source_url": out.get("source_url") or out.get("url"),
    }
    # 若上游已在 output 里给了现成内核，直接优先采用
    if out.get("fact_kernel"):
        raw = dict(out["fact_kernel"])
    elif out.get("product"):
        # 产品快照作为事实层来源
        snap = dict(out["product"])
        snap.setdefault("entity_name", raw.get("entity_name"))
        snap.setdefault("entity_type", raw.get("entity_type"))
        snap.setdefault("attrs", raw["attrs"])
        snap.setdefault("copy", raw["copy"])
        raw = snap

    kernel = FactKernel.from_dict(raw)
    return kernel


def project_deerflow_output(
    intent: str,
    output: Optional[dict[str, Any]],
    group: str,
    region: str = "cn",
    platform: str = "generic",
) -> dict[str, Any]:
    """一核多形：DeerFlow 产出 → 事实内核 → 目标平台形态投影。

    非内容类意图或无事实层时返回 skipped 标记，不假成功。
    """
    kernel = extract_kernel_from_subtask(intent, output)
    if kernel is None:
        return {"skipped": True, "reason": f"intent {intent} 不产生事实层"}
    from app.services.geo.platform_content_router import route as _route

    return _route(kernel, group, region=region, platform=platform)


__all__ = [
    "extract_kernel_from_subtask",
    "project_deerflow_output",
]
