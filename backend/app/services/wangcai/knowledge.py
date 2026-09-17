# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""旺财 N2 知识检索层（实施指南 §2，阶段一：SQL 关键词起步）。

设计（指南 2.4）：
- KnowledgeRetriever.search(tenant_hint, query, intent) -> RetrievalResult；
- 三源检索：products / product_faqs / case_studies，词频打分 top-k；
- 命中为空 → KnowledgeMiss（Router 决定转人工/澄清）；
  **禁止回退海关数据冒充答案**（指南 2.1/2.6，当前"智障感"头号来源）。

租户作用域（红线，指南 2.1/2.6）：
- 实测（2026-08-31）：products/product_faqs/case_studies 三表**均无 tenant_id 列**；
- 现状租户↔产品为弱关联：tenant.settings.onboarding.primary_product 文本提示
  （实测 services/tenant_product_context.py resolve_tenant_product_hint）；
- 阶段一方案：以 hint 做作用域匹配（产品名/分类/slug 与 hint 相关才入候选）；
  未来给三表加 tenant_id（需独立迁移+数据回灌，另行立项）后，
  仅需替换 tenant_filter 即可切换，检索逻辑不变。
- 纯逻辑（tokenize/score/rank）不依赖 DB，可独立测试。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

# 三源权重（FAQ 直接问答最相关 > 产品信息 > 案例）
SOURCE_WEIGHTS: Dict[str, float] = {
    "product_faq": 1.0,
    "product": 0.9,
    "case_study": 0.8,
}

TOP_K_DEFAULT = 5
MIN_SCORE = 1.0  # 低于该分值视为未命中
# 阶段一已知局限：纯关键词法不支持跨语言匹配（中文提问命中不了英文语料），
# 阶段二语义检索（pgvector/EmbeddingService）弥补（指南 2.2）。

_WORD_RE = re.compile(r"[a-z0-9][a-z0-9\-\.]*", re.I)
_CJK_RE = re.compile(r"[\u4e00-\u9fff]+")


@dataclass
class KnowledgeHit:
    source_type: str          # product | product_faq | case_study
    source_id: str
    text: str
    score: float
    citation: str             # 来源引用（Evidence 要求，指南 2.1）


@dataclass
class RetrievalResult:
    hits: List[KnowledgeHit] = field(default_factory=list)
    missed: bool = False
    tenant_hint: Optional[str] = None
    @property
    def top(self) -> Optional[KnowledgeHit]:
        """top。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return self.hits[0] if self.hits else None


# ---------------------------------------------------------------------------
# 纯逻辑：分词 / 打分 / 排序（可独立测试）
# ---------------------------------------------------------------------------

def tokenize(text: str) -> List[str]:
    """英文按词（小写），中文按 2-gram；去重保序。"""
    if not text:
        return []
    tokens: List[str] = []
    seen = set()
    for w in _WORD_RE.findall(text.lower()):
        if w not in seen:
            seen.add(w)
            tokens.append(w)
    for run in _CJK_RE.findall(text):
        if len(run) == 1:
            if run not in seen:
                seen.add(run)
                tokens.append(run)
            continue
        for i in range(len(run) - 1):
            bg = run[i:i + 2]
            if bg not in seen:
                seen.add(bg)
                tokens.append(bg)
    return tokens


def score_text(text: str, tokens: List[str]) -> float:
    """词频打分：命中 token 出现次数求和（中文 bigram 计 1.5 倍权重）。"""
    if not text or not tokens:
        return 0.0
    low = text.lower()
    score = 0.0
    for t in tokens:
        cnt = low.count(t)
        if cnt:
            score += cnt * (1.5 if _CJK_RE.fullmatch(t) else 1.0)
    return score


def rank_hits(candidates: List[KnowledgeHit], top_k: int = TOP_K_DEFAULT) -> List[KnowledgeHit]:
    """rank_hits。

    参数说明：
    :param candidates: 参数 candidates
    :param top_k: 参数 top_k
    :return: 返回处理结果。
    """
    ranked = sorted(candidates, key=lambda h: h.score, reverse=True)
    return [h for h in ranked[:top_k] if h.score >= MIN_SCORE]


# ---------------------------------------------------------------------------
# 检索器（数据源以 fetcher 注入，便于测试与后续切换真实租户列）
# ---------------------------------------------------------------------------

# fetcher 签名: (tenant_hint: str) -> List[dict]
# dict 需含: id / text（可检索文本）/ citation（展示用来源名）
Fetcher = Callable[[str], List[dict]]


class KnowledgeRetriever:
    """三源关键词检索（阶段一）。tenant_filter 决定作用域（红线）。"""
    def __init__(
        self,
        products_fetcher: Fetcher,
        faqs_fetcher: Fetcher,
        cases_fetcher: Fetcher,
    ):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param products_fetcher: 参数 products_fetcher
        :param faqs_fetcher: 参数 faqs_fetcher
        :param cases_fetcher: 参数 cases_fetcher
        :return: 返回处理结果。
        """
        self._sources = (
            ("product", products_fetcher),
            ("product_faq", faqs_fetcher),
            ("case_study", cases_fetcher),
        )

    def search(
        self,
        tenant_hint: str,
        query: str,
        intent: Optional[str] = None,
        top_k: int = TOP_K_DEFAULT,
    ) -> RetrievalResult:
        """search。

        参数说明：
        :param self: 参数 self
        :param tenant_hint: 参数 tenant_hint
        :param query: 参数 query
        :param intent: 参数 intent
        :param top_k: 参数 top_k
        :return: 返回处理结果。
        """
        hint = (tenant_hint or "").strip()
        tokens = tokenize(query)
        if not tokens:
            return RetrievalResult(missed=True, tenant_hint=hint)
        # 租户作用域红线：无知识绑定时不得从全局池回答（防跨租户泄漏），
        # 直接返回 miss 由 Router 转人工/澄清（指南 2.1）。
        if not hint:
            return RetrievalResult(missed=True, tenant_hint=hint)

        candidates: List[KnowledgeHit] = []
        for source_type, fetcher in self._sources:
            try:
                rows = fetcher(hint) or []
            except Exception:
                rows = []  # 单源故障不影响其他源；全空则按 miss 处理
            weight = SOURCE_WEIGHTS.get(source_type, 0.8)
            for row in rows:
                text = str(row.get("text") or "")
                s = score_text(text, tokens) * weight
                if s > 0:
                    candidates.append(
                        KnowledgeHit(
                            source_type=source_type,
                            source_id=str(row.get("id") or ""),
                            text=text[:600],
                            score=round(s, 2),
                            citation=str(row.get("citation") or source_type),
                        )
                    )
        hits = rank_hits(candidates, top_k=top_k)
        return RetrievalResult(hits=hits, missed=not hits, tenant_hint=hint)


def miss_reason(result: RetrievalResult) -> str:
    """KnowledgeMiss 的标准话术依据（供 Router：转人工/澄清，禁止冒充）。"""
    if not (result.tenant_hint or "").strip():
        return "tenant_no_knowledge_binding"
    return "knowledge_empty"
