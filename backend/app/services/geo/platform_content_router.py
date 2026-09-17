# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""平台形态路由 — 把事实内核分发到四类平台形态。

对应缺口第 2、3 条：ContentMaster 只发「同一篇长文」，本模块按
平台形态（A 搜索 / B 社媒 / C B2B / D 知识背书）生成各自的形态变体，
而不是同一篇内容端给 40 家。

- A 搜索   ：产出 Schema.org 标记 + 事实密度段落（GEO 引用友好）
- B 社媒   ：产出短视频脚本 + 图文 hook
- C B2B    ：委托 product_feed.build_feed_record
- D 知识系 ：产出降 AI 味的长文（事实加厚，供知乎/百家号/头条）

国内系（D 组 cn）额外走「降 AI 味」策略：加厚可查证事实、弱化辞藻，
与 services/geo/geo_writing_policy.py 的去 AI 味战术口径一致。

纯函数、无 DB/网络依赖，可离线单测。
"""

from __future__ import annotations

from typing import Any

from app.services.geo.content_kernel import FactKernel, PlatformGroup
from app.services.geo.product_feed import build_feed_record


def _facts_sentence(kernel: FactKernel) -> str:
    """把内核属性压成一句事实密度短句（GEO 首段 60 词内给结论）。"""
    t = kernel.trade
    bits: list[str] = []
    if t.moq:
        bits.append(f"MOQ {t.moq}")
    if t.lead_time:
        bits.append(f"lead time {t.lead_time}")
    if t.incoterms:
        bits.append(t.incoterms)
    if t.certifications:
        bits.append("certified " + "/".join(t.certifications[:4]))
    suffix = (" | " + " | ".join(bits)) if bits else ""
    return f"{kernel.entity_name}: {kernel.copy.get('en') or kernel.attrs.get('description') or ''}{suffix}".strip()


def _schema_markup(kernel: FactKernel) -> dict[str, Any]:
    """生成 Schema.org 标记（product/organization 二选一 + FAQ 可选）。"""
    t = kernel.trade
    item: dict[str, Any]
    if kernel.entity_type in ("organization", "facility"):
        item = {"@type": "Organization", "name": kernel.entity_name}
    else:
        item = {"@type": "Product", "name": kernel.entity_name}
        desc = kernel.copy.get("en") or kernel.attrs.get("description")
        if desc:
            item["description"] = desc
        img = kernel.attrs.get("image_url")
        if img:
            item["image"] = img
        if t.certifications:
            item["brand"] = {"@type": "Brand", "name": kernel.entity_name}
    if t.payment_terms or t.incoterms:
        item["additionalProperty"] = []
        for label, val in (("incoterms", t.incoterms), ("paymentTerms", t.payment_terms)):
            if val:
                item["additionalProperty"].append(
                    {"@type": "PropertyValue", "name": label, "value": val}
                )
    return {"@context": "https://schema.org", **item}


def render_search(kernel: FactKernel) -> dict[str, Any]:
    """A 组：搜索引擎 / GEO 形态。"""
    return {
        "group": PlatformGroup.SEARCH,
        "facts_sentence": _facts_sentence(kernel),
        "schema": _schema_markup(kernel),
        "completeness": round(kernel.completeness(), 4),
        "incomplete": kernel.degraded(),
    }


def render_social(kernel: FactKernel) -> dict[str, Any]:
    """B 组：社媒多模态形态（短视频脚本 + hook）。"""
    hook = kernel.copy.get("en") or kernel.copy.get("zh") or kernel.entity_name
    script = [
        f"hook: {hook}",
        _facts_sentence(kernel),
        "cta: request a quote / MOQ & lead time in comments",
    ]
    return {
        "group": PlatformGroup.SOCIAL,
        "hook": hook,
        "short_video_script": script,
        "incomplete": kernel.degraded(),
    }


def render_b2b(kernel: FactKernel, platform: str = "alibaba_offer") -> dict[str, Any]:
    """C 组：垂直 B2B 商品 feed 形态。"""
    record = build_feed_record(kernel, platform)
    record["group"] = PlatformGroup.B2B
    return record


def render_knowledge(kernel: FactKernel, region: str = "cn") -> dict[str, Any]:
    """D 组：知识背书长文。region=cn 时加厚事实、压辞藻（降 AI 味）。"""
    t = kernel.trade
    evidence_lines = [f"- {e.label}" for e in kernel.evidence] or ["- 证据待补"]
    body: list[str] = [kernel.entity_name]
    if region == "cn":
        # 国内系：先摆可查证事实，弱化形容词，避免被原创度判定打低分
        body.append("事实与资质（可查证）：")
        body.extend(evidence_lines)
        if t.moq or t.lead_time:
            body.append(
                f"供货条款：MOQ {t.moq or '见详情页'}；交期 {t.lead_time or '面议'}；"
                f"贸易方式 {t.incoterms or 'EXW/FOB'}。"
            )
    else:
        body.append(kernel.copy.get("en") or kernel.attrs.get("description") or "")
        body.extend(evidence_lines)
    return {
        "group": PlatformGroup.KNOWLEDGE,
        "region": region,
        "body": "\n".join(body),
        "de_ai_tuned": region == "cn",
        "incomplete": kernel.degraded(),
    }


def route(kernel: FactKernel, group: str, **kw: Any) -> dict[str, Any]:
    """统一入口：按形态组渲染内核。未知组返回 incomplete 标记，不假成功。"""
    if group == PlatformGroup.SEARCH:
        return render_search(kernel)
    if group == PlatformGroup.SOCIAL:
        return render_social(kernel)
    if group == PlatformGroup.B2B:
        return render_b2b(kernel, kw.get("platform", "alibaba_offer"))
    if group == PlatformGroup.KNOWLEDGE:
        return render_knowledge(kernel, kw.get("region", "cn"))
    return {
        "group": group,
        "incomplete": True,
        "missing_fields": ["group not recognized"],
        "note": "unknown platform group; no content generated",
    }


__all__ = [
    "route",
    "render_search",
    "render_social",
    "render_b2b",
    "render_knowledge",
]
