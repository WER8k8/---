# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""B2B 商品 feed 生成器 — 从事实内核产出结构化商品 feed。

对应缺口第 4 条：垂直 B2B（Alibaba/GlobalSources/Made-in-China/1688）
要的是「结构化商品 feed」，不是网页长文。本模块把 FactKernel 转成
平台无关的规范 feed 记录（JSON），再投影为各平台可接收的形态：

- alibaba_offer   : 阿里国际站 offer 字段
- made_in_china   : MIC 产品字段
- generic_xml_item: 通用 XML item（可序列化）

设计铁律（AGENTS.md §4 交付求真）：
- 内核 degraded（关键字段缺失）时，相关字段留空并在 feed 里打
  ``incomplete=true``，绝不用占位值冒充已就绪。
- 不编造价格/认证；认证只透传内核 evidence，无则不写。
"""

from __future__ import annotations

from typing import Any, Optional

from app.services.geo.content_kernel import FactKernel, PlatformGroup


# 各 B2B 平台对「必填硬字段」的最低要求（用于判断 incomplete）
_REQUIRED_FOR_PLATFORM: dict[str, tuple[str, ...]] = {
    "alibaba_offer": ("moq", "name", "image"),
    "made_in_china": ("name", "description"),
    "generic": ("name",),
}


def _pick(attrs: dict[str, Any], *keys: str) -> Any:
    for k in keys:
        if attrs.get(k) not in (None, "", []):
            return attrs[k]
    return None


def build_feed_record(kernel: FactKernel, platform: str = "alibaba_offer") -> dict[str, Any]:
    """把事实内核投影为某 B2B 平台的一条商品 feed 记录。

    参数：
      kernel   : 已构建的 FactKernel
      platform : alibaba_offer | made_in_china | generic
    返回：
      规范 feed 记录；缺数据处留空并置 incomplete=true。
    """
    trade = kernel.trade
    name = kernel.entity_name
    desc = kernel.copy.get("en") or kernel.attrs.get("description") or ""

    moq = trade.moq or _pick(kernel.attrs, "moq", "min_order")
    image = _pick(kernel.attrs, "image_url", "main_image")
    price = _pick(kernel.attrs, "price", "unit_price", "price_range")
    specs = kernel.attrs.get("specifications") or kernel.attrs.get("specifications_text")

    certs = list(trade.certifications)
    if not certs:
        # 退而求其次：从强/已验证证据里抽认证标签，避免漏掉真实资质
        certs = [
            e.label for e in kernel.evidence
            if e.level in ("strong", "verified") and "cert" in e.label.lower()
        ]

    base: dict[str, Any] = {
        "platform": platform,
        "group": PlatformGroup.B2B,
        "name": name,
        "description": desc,
        "moq": moq,
        "unit": _pick(kernel.attrs, "unit") or "piece",
        "price": price,
        "image": image,
        "lead_time": trade.lead_time,
        "incoterms": trade.incoterms,
        "payment_terms": trade.payment_terms,
        "certifications": certs,
        "specifications": specs,
        "entity_type": kernel.entity_type,
        "attrs": dict(kernel.attrs),
        "source_url": kernel.source_url,
    }

    required = _REQUIRED_FOR_PLATFORM.get(platform, _REQUIRED_FOR_PLATFORM["generic"])
    missing: list[str] = []
    for field in required:
        val = base.get(field)
        if val in (None, "", [], {}):
            missing.append(field)

    base["incomplete"] = bool(missing) or kernel.degraded()
    base["missing_fields"] = missing
    base["schema_ready"] = kernel.schema_ready
    return base


def build_product_feed(
    kernels: list[FactKernel], platform: str = "alibaba_offer"
) -> dict[str, Any]:
    """一次产出多条商品 feed（一租户多产品），并汇总完备度。"""
    items = [build_feed_record(k, platform) for k in kernels]
    complete = sum(1 for it in items if not it["incomplete"])
    return {
        "platform": platform,
        "count": len(items),
        "complete": complete,
        "incomplete": len(items) - complete,
        "complete_ratio": round(complete / len(items), 4) if items else 0.0,
        "items": items,
    }


def to_generic_xml_item(record: dict[str, Any]) -> str:
    """把一条 feed 记录序列化为通用 XML item（供无官方 feed 的平台）。

    仅输出存在且非空的字段；incomplete 标记为属性透传，绝不填充假值。
    """
    def _esc(v: Any) -> str:
        s = str(v)
        return (
            s.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )

    fields = [
        "name", "description", "moq", "unit", "price",
        "lead_time", "incoterms", "payment_terms",
    ]
    parts = [f'<item incomplete="{str(record["incomplete"]).lower()}">']
    for f in fields:
        val = record.get(f)
        if val not in (None, "", []):
            parts.append(f"  <{f}>{_esc(val)}</{f}>")
    certs = record.get("certifications") or []
    if certs:
        parts.append("  <certifications>")
        parts.extend(f"    <cert>{_esc(c)}</cert>" for c in certs)
        parts.append("  </certifications>")
    parts.append("</item>")
    return "\n".join(parts)


__all__ = [
    "build_feed_record",
    "build_product_feed",
    "to_generic_xml_item",
]
