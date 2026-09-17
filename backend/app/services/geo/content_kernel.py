# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""内容事实内核（Fact Kernel）— 全平台分发的单一事实真源。

设计定位（对应 AGENTS.md「一核多形」缺口）：
- 一份结构化事实内核只生产一次，质量最高；各平台只是把内核按自身
  形态重新包装（搜索引擎吃 Schema、B2B 吃商品 feed、社媒吃短视频脚本）。
- 内核 = 实体 / 属性 / 资质 / 贸易条款 / 证据 / 多语言文案 六段。
- 所有字段可选、全量容忍缺数据；缺什么就标什么，绝不编造（交付求真，
  无 Key 降级而非假成功——见 AGENTS.md §4 铁律）。

本模块只做「内核建模 + 校验」，不碰 DB、不碰网络，保证可离线单测。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Literal

# 平台形态分类：A 搜索引擎 / B 社媒多模态 / C 垂直 B2B / D 知识背书
# 与 services/geo/platform_rank_registry.py 的 region/content_type 口径对齐，
# 但不依赖它（避免内核层反向依赖排名层）。
class PlatformGroup:
    SEARCH = "search"          # A：谷歌/Bing/百度/搜狗/360
    SOCIAL = "social"          # B：LinkedIn/YouTube/FB/X/Instagram/TikTok
    B2B = "b2b"                # C：Alibaba/Made-in-China/GlobalSources/1688
    KNOWLEDGE = "knowledge"    # D：知乎/B站/小红书/行业媒体


# 证据等级：strong=官方检测报告/认证证书原件；verified=第三方可查证；
# self_reported=卖家自述（未经验证）；none=无证据。
EvidenceLevel = Literal["strong", "verified", "self_reported", "none"]


def _clean_str(value: Any, max_len: int = 500) -> str:
    """清洗文本：去首尾空白、压缩连续换行，并截断到 max_len。纯函数。"""
    if value is None:
        return ""
    text = str(value)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_len]


@dataclass(frozen=True)
class Evidence:
    """一条证据（检测报告 / 认证 / 客户引语 / 实拍）。"""

    label: str
    level: EvidenceLevel = "self_reported"
    source: str = ""
    verifiable: bool = False

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "Evidence":
        level = raw.get("level", "self_reported")
        if level not in ("strong", "verified", "self_reported", "none"):
            level = "self_reported"
        return cls(
            label=_clean_str(raw.get("label"), 200),
            level=level,
            source=_clean_str(raw.get("source"), 300),
            verifiable=bool(raw.get("verifiable", False)),
        )


@dataclass(frozen=True)
class TradeTerms:
    """外贸 7 步闭环里内核要落的硬条款（询盘→成交→物流可查）。"""

    moq: str = ""                 # 最小起订量
    lead_time: str = ""           # 交期
    payment_terms: str = ""       # 付款方式（T/T、L/C …）
    incoterms: str = ""           # 贸易条款（FOB/CIF/EXW …）
    sample_policy: str = ""       # 打样政策
    certifications: tuple[str, ...] = ()   # 认证（ISO/CE/SGS …）

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "TradeTerms":
        certs = raw.get("certifications") or []
        if isinstance(certs, str):
            certs = [c.strip() for c in certs.split(",") if c.strip()]
        certs = tuple(_clean_str(c, 100) for c in certs)
        return cls(
            moq=_clean_str(raw.get("moq"), 120),
            lead_time=_clean_str(raw.get("lead_time"), 120),
            payment_terms=_clean_str(raw.get("payment_terms"), 200),
            incoterms=_clean_str(raw.get("incoterms"), 120),
            sample_policy=_clean_str(raw.get("sample_policy"), 200),
            certifications=certs,
        )


@dataclass
class FactKernel:
    """单一事实内核：全平台分发的唯一真源。

    字段分组：
      实体   entity_*   —— 被搜索引擎/GEO 识别的「谁」
      属性   attrs      —— 可被 LLM 摘为答案的键值事实
      资质   trade      —— 外贸硬条款（可信度来源）
      证据   evidence   —— 支撑每条资质的可查证材料
      多语   copy       —— zh/en 等语言的事实性短文案（非营销腔）
    """

    entity_name: str
    entity_type: str = "product"        # product | organization | facility | service
    entity_aliases: tuple[str, ...] = ()  # 别名/同义（提升实体识别与 GEO 锚定）
    attrs: dict[str, Any] = field(default_factory=dict)
    trade: TradeTerms = field(default_factory=TradeTerms)
    evidence: tuple[Evidence, ...] = ()
    copy: dict[str, str] = field(default_factory=dict)  # lang -> short fact copy
    source_url: str = ""
    source_tenant: str = ""
    schema_ready: bool = True            # 关键字段是否齐到能出 Schema

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "FactKernel":
        """从松散 dict（如 ProductDocument/ContentMaster 快照）构建内核。

        容忍缺数据：只取存在的键，缺失字段留空并如实标记 schema_ready。
        """
        raw = raw or {}
        entity_type = _clean_str(raw.get("entity_type"), 50) or "product"
        aliases = raw.get("entity_aliases") or raw.get("aliases") or []
        if isinstance(aliases, str):
            aliases = [a.strip() for a in aliases.split(",") if a.strip()]
        attrs = dict(raw.get("attrs") or {})
        # 常见贸易条款可能平铺在 raw 顶层，兼容收编进 TradeTerms
        trade = TradeTerms.from_dict(raw.get("trade") or {})
        if not trade.moq and raw.get("moq"):
            trade = TradeTerms.from_dict({**raw, "moq": raw.get("moq")})
        ev_raw = raw.get("evidence") or []
        evidence = tuple(Evidence.from_dict(e) for e in ev_raw)
        copy = {
            _clean_str(k, 10): _clean_str(v, 600)
            for k, v in (raw.get("copy") or {}).items()
        }
        name = _clean_str(raw.get("entity_name") or raw.get("name"), 200)
        kernel = cls(
            entity_name=name,
            entity_type=entity_type,
            entity_aliases=tuple(_clean_str(a, 100) for a in aliases),
            attrs={str(k): v for k, v in attrs.items()},
            trade=trade,
            evidence=evidence,
            copy=copy,
            source_url=_clean_str(raw.get("source_url"), 300),
            source_tenant=_clean_str(raw.get("source_tenant"), 100),
        )
        kernel.schema_ready = kernel._completeness() >= 0.6
        return kernel

    # ------------------------------------------------------------------
    # 完备度与降级
    # ------------------------------------------------------------------
    def _completeness(self) -> float:
        """事实完备度（0~1）：事实内核能否支撑下游形态生成的比例。

        只算「硬事实」维度，营销文案不计入——避免用辞藻冒充可信度。
        """
        checks = [
            bool(self.entity_name.strip()),
            bool(self.attrs),
            bool(self.trade.moq or self.trade.lead_time or self.trade.incoterms),
            bool(self.evidence),
            any(lang.strip() for lang in self.copy),
        ]
        hit = sum(1 for c in checks if c)
        return hit / len(checks)

    def completeness(self) -> float:
        return self._completeness()

    def degraded(self) -> bool:
        """True 表示关键字段缺失，下游必须走降级（不假装已配置/已收录）。"""
        return not self.schema_ready

    def to_dict(self) -> dict[str, Any]:
        return {
            "entity_name": self.entity_name,
            "entity_type": self.entity_type,
            "entity_aliases": list(self.entity_aliases),
            "attrs": dict(self.attrs),
            "trade": {
                "moq": self.trade.moq,
                "lead_time": self.trade.lead_time,
                "payment_terms": self.trade.payment_terms,
                "incoterms": self.trade.incoterms,
                "sample_policy": self.trade.sample_policy,
                "certifications": list(self.trade.certifications),
            },
            "evidence": [
                {
                    "label": e.label,
                    "level": e.level,
                    "source": e.source,
                    "verifiable": e.verifiable,
                }
                for e in self.evidence
            ],
            "copy": dict(self.copy),
            "source_url": self.source_url,
            "source_tenant": self.source_tenant,
            "schema_ready": self.schema_ready,
            "completeness": round(self.completeness(), 4),
        }


__all__ = [
    "PlatformGroup",
    "Evidence",
    "TradeTerms",
    "FactKernel",
    "EvidenceLevel",
]
