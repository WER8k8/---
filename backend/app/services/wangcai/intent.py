# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""旺财 N1 意图识别层（实施指南 §1，总纲 §7A 阶段 1）。

设计（指南 1.4）：
- IntentRegistry 注册表式：新增意图不改核心代码（对齐 Skill 版本化思想）；
- 旧 5 意图（hs_lookup/customs_data/blue_ocean/export_feasibility/help）正则
  从 wangcai_trade_service.detect_wangcai_intent 原样移植，零回归；
- 新增 7 意图：product_spec / certification / price_inquiry / logistics /
  company_info / case_reference / human_handoff；
- 置信度 < LLM_FALLBACK_THRESHOLD(0.6) → 标记 source='need_llm'
  （阶段 2 接 N4 cost_optimized 档；阶段 1 由 Router 走澄清追问）；
- **废除旧假兜底**（未命中一律 customs_data）：未命中返回 'unclear'（指南 2.1）。
- 实体抽取随意图返回：国家/产品词/数量/时间（供 N6 转化信号）。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Pattern

LLM_FALLBACK_THRESHOLD = 0.6  # 指南 1.4-3

# ---------------------------------------------------------------------------
# 结果结构
# ---------------------------------------------------------------------------


@dataclass
class IntentResult:
    intent: str
    confidence: float
    entities: Dict[str, str] = field(default_factory=dict)
    source: str = "rule"  # rule | legacy | need_llm
    @property
    def needs_llm(self) -> bool:
        """needs_llm。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return self.source == "need_llm" or self.confidence < LLM_FALLBACK_THRESHOLD


@dataclass
class IntentDef:
    name: str
    patterns: List[Pattern]
    confidence: float = 0.85
    origin: str = "rule"  # rule | legacy


_REGISTRY: Dict[str, IntentDef] = {}
_ORDER: List[str] = []  # 匹配优先级顺序


def register_intent(
    name: str,
    patterns: List[str],
    *,
    confidence: float = 0.85,
    origin: str = "rule",
    priority: Optional[int] = None,
) -> None:
    """注册意图（可扩展入口：新增意图不改核心代码）。"""
    _REGISTRY[name] = IntentDef(
        name=name,
        patterns=[re.compile(p, re.I) for p in patterns],
        confidence=confidence,
        origin=origin,
    )
    if priority is None:
        _ORDER.append(name)
    else:
        _ORDER.insert(min(priority, len(_ORDER)), name)


# ---------------------------------------------------------------------------
# 意图清单：新增 7 个在前（更具体），旧 5 个在后（零回归移植）
# ---------------------------------------------------------------------------

# 转人工（最高优先，显式请求）
register_intent(
    "human_handoff",
    [r"转人工", r"人工客服", r"真人", r"(talk|speak)\s+(to|with)\s+(a\s+)?"
     r"(human|person|agent|sales)", r"customer\s+service", r"live\s+agent"],
    confidence=0.95, priority=0,
)
# 认证
register_intent(
    "certification",
    [r"认证", r"证书", r"检测报告", r"\bCE\b", r"\bISO\b", r"SGS", r"UL\b",
     r"certificat\w*", r"test\s+report", r"compliance\s+certificate", r"防火等级"],
    confidence=0.9, priority=1,
)
# 价格咨询
register_intent(
    "price_inquiry",
    [r"价格", r"报价", r"多少钱", r"单价", r"批发价", r"\bprice\b", r"\bquote\b",
     r"quotation", r"how\s+much", r"cost\s+per", r"per\s+(m2|m²|sqm|ton)"],
    confidence=0.9, priority=2,
)
# 产品规格
register_intent(
    "product_spec",
    [r"规格", r"参数", r"密度", r"厚度", r"导热系数", r"尺寸", r"spec\w*",
     r"dimension", r"density", r"thickness", r"thermal\s+conductivity",
     r"r[\s-]?value", r"data\s*sheet", r"技术参数"],
    confidence=0.88, priority=3,
)
# 运费交期
register_intent(
    "logistics",
    [r"运费", r"交期", r"货期", r"发货", r"运输", r"到港", r"shipping",
     r"freight", r"delivery\s+time", r"lead\s+time", r"shipment", r"FOB", r"CIF"],
    confidence=0.88, priority=4,
)
# 案例
register_intent(
    "case_reference",
    [r"案例", r"项目案例", r"工程案例", r"成功案例", r"应用案例", r"case\s+stud\w*",
     r"project\s+reference", r"reference\s+project", r"portfolio"],
    confidence=0.88, priority=5,
)
# 公司介绍
register_intent(
    "company_info",
    [r"公司介绍", r"关于我们", r"工厂", r"产能", r"公司规模", r"你们公司",
     r"about\s+(you|us|the\s+company)", r"company\s+profile", r"factory",
     r"production\s+capacity", r"manufacturer\??"],
    confidence=0.85, priority=6,
)

# ---- 旧 5 意图：原样移植（零回归），优先级在后 ----
register_intent(
    "hs_lookup",
    [r"(海关|hs|编码|税号|harmonized|tariff code)"],
    confidence=0.75, origin="legacy",
)
register_intent(
    "customs_data",
    [r"(全部品类|all categor|list all|top export market|海关数据|贸易数据|出口指数|"
     r"export index|trade data|customs data|statistics|统计)"],
    confidence=0.75, origin="legacy",
)
register_intent(
    "blue_ocean",
    [r"(蓝海|哪个国家|哪国|哪些国家|好卖|best market|where to sell|top market|export to where)"],
    confidence=0.75, origin="legacy",
)
register_intent(
    "export_feasibility",
    [r"(出口|export|ship to|send to|sell to|能发|能不能|can i|can we|feasible|compliance)"],
    confidence=0.72, origin="legacy",
)
register_intent(
    "help",
    [r"(help|what can|how|你好|您好|hi\b|hello)"],
    confidence=0.5, origin="legacy",
)

# ---------------------------------------------------------------------------
# 实体抽取（供 N6 转化信号）
# ---------------------------------------------------------------------------

_COUNTRY_WORDS = [
    "美国", "沙特", "阿联酋", "迪拜", "卡塔尔", "印度", "越南", "泰国", "印尼",
    "马来西亚", "菲律宾", "澳大利亚", "英国", "德国", "法国", "俄罗斯", "巴西",
    "墨西哥", "南非", "尼日利亚", "埃及",
]
_COUNTRY_EN = [
    r"united states", r"\busa?\b", r"saudi arabia", r"\buae\b", r"dubai",
    r"qatar", r"india", r"vietnam", r"thailand", r"indonesia", r"malaysia",
    r"philippines", r"australia", r"united kingdom", r"\buk\b", r"germany",
    r"france", r"russia", r"brazil", r"mexico", r"south africa", r"nigeria",
    r"egypt",
]
_QTY_RE = re.compile(
    r"(\d[\d,\.]*)\s*(m2|m²|sqm|平方米|tons?|吨|containers?|柜|pcs|件)", re.I
)
_TIME_RE = re.compile(
    r"(within\s+\d+\s*(days?|weeks?|months?)|[0-9一两三四五六七八九十]+\s*(天后|天内|周内|个月内))", re.I
)


def _extract_entities(text: str) -> Dict[str, str]:
    """_extract_entities。

    参数说明：
    :param text: 参数 text
    :return: 返回处理结果。
    """
    ent: Dict[str, str] = {}
    low = text.lower()
    for c in _COUNTRY_WORDS:
        if c in text:
            ent["country"] = c
            break
    if "country" not in ent:
        for p in _COUNTRY_EN:
            if re.search(p, low):
                ent["country"] = p.strip(r"\b").replace(r"\s+", " ")
                break
    qty = _QTY_RE.search(text)
    if qty:
        ent["quantity"] = qty.group(0).strip()
    tm = _TIME_RE.search(text)
    if tm:
        ent["timeline"] = tm.group(0).strip()
    return ent


# ---------------------------------------------------------------------------
# 主入口
# ---------------------------------------------------------------------------


def detect_intent(message: str) -> IntentResult:
    """规则层意图识别；低置信返回 unclear+need_llm（废除旧假兜底）。"""
    text = (message or "").strip()
    if not text:
        return IntentResult(intent="unclear", confidence=0.0, source="need_llm")

    for name in _ORDER:
        idef = _REGISTRY[name]
        for pat in idef.patterns:
            if pat.search(text):
                return IntentResult(
                    intent=name,
                    confidence=idef.confidence,
                    entities=_extract_entities(text),
                    source=idef.origin,
                )
    # 未命中：不硬猜（指南 1.1/2.1）
    return IntentResult(
        intent="unclear",
        confidence=0.2,
        entities=_extract_entities(text),
        source="need_llm",
    )


def list_intents() -> List[str]:
    """当前注册表（供管理端展示/测试一致性校验）。"""
    return list(_ORDER)
