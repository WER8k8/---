# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""WangcaiRouter 总编排（实施指南 §0.1 链路；阶段 1 收口，不依赖 LLM 可上线）。

流程（指南 0.1）：
  N1 意图 → 新意图：N3 上下文 → N2 知识检索 → 规则回复（带引用）
           旧意图（海关/蓝海/出口可行性/帮助）：委托旧引擎降级路径（零回归）
           unclear：澄清式追问（指南 1.1，禁止硬猜）
           human_handoff：转人工话术
红线：
  - 访客输入=不可信（R9）：回复出站前经 sanitizer 净化（默认挂
    hermes/brand_guard.sanitize_public_copy，故障时退化为透传并标记）；
  - 知识未命中禁止冒充（指南 2.1）：路由到转人工话术；
  - 租户作用域：检索器无 hint 即空（knowledge.py 红线）。
输出形状与旧引擎 ask_wangcai 完全兼容：{intent, reply, disclaimer, language, ...}，
并附 router 元数据（route/citations/session_id）。
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Callable, Dict, List, Optional

from app.services.wangcai.intent import detect_intent
from app.services.wangcai.knowledge import KnowledgeRetriever, RetrievalResult
from app.services.wangcai.memory import (
    InMemorySessionStore,
    SessionStore,
    Turn,
    build_context,
    resolve_coreference_hint,
)

logger = logging.getLogger(__name__)

# 新意图（走租户知识管线）；旧意图委托旧引擎（零回归，指南 0.2 事实基线）
NEW_INTENTS = frozenset({
    "product_spec", "certification", "price_inquiry",
    "logistics", "company_info", "case_reference",
})
LEGACY_DELEGATED = frozenset({
    "hs_lookup", "customs_data", "blue_ocean", "export_feasibility", "help",
})

_CLARIFY = {
    "zh": "抱歉，我没有完全理解您的问题。请更具体地描述您的产品与问题，例如：「岩棉板的密度是多少？」「有 CE 认证吗？」",
    "en": "Sorry, I didn't fully understand. Please describe your product and question more specifically, e.g. 'What is the density of the rock wool board?'",
}
_HANDOFF = {
    "zh": "这个问题已为您转接人工顾问，将尽快与您联系。您也可以直接通过页面询盘入口提交需求。",
    "en": "Your question has been forwarded to a human advisor who will contact you shortly. You can also submit your request via the inquiry form.",
}
_HANDOFF_EXPLICIT = {
    "zh": "正在为您转接人工顾问，请稍候。",
    "en": "Connecting you to a human advisor, please wait.",
}


def _pick_lang(language: Optional[str]) -> str:
    """_pick_lang。

    参数说明：
    :param language: 参数 language
    :return: 返回处理结果。
    """
    return "zh" if (language or "").lower().startswith("zh") else "en"


def llm_enabled() -> bool:
    """旺财 LLM 回复开关（默认关，零回归；规则回复为降级路径）。"""
    return os.environ.get("WANGCAI_LLM_ENABLED", "0") == "1"


def try_llm_reply(
    *,
    intent: str,
    knowledge_hits: List[Any],
    history: List[Any],
    question: str,
    language: Optional[str] = None,
) -> Any:
    """尝试 LLM 回复（N4）；开关关/运行中事件循环/任何异常 → None（回退规则回复）。

    同步上下文用 asyncio.run；已在运行事件循环（FastAPI 异步链路）时不嵌套，
    降级规则回复（异步全链路接线为后续阶段）。
    """
    if not llm_enabled():
        return None
    try:
        asyncio.get_running_loop()
        return None  # 已有事件循环：不嵌套，降级规则回复
    except RuntimeError:
        pass
    try:
        from app.services.wangcai.llm import WangcaiLLM  # noqa: PLC0415
        return asyncio.run(
            WangcaiLLM().answer(
                intent=intent,
                knowledge_hits=knowledge_hits,
                history=history,
                question=question,
                lang=language or "zh",
            )
        )
    except Exception:  # noqa: BLE001 — LLM 故障不得阻断回复（降级规则回复）
        logger.warning("wangcai llm reply 异常，降级规则回复")
        return None


class WangcaiRouter:
    """阶段 1 编排器：纯规则可上线；N4 LLM 层为阶段 2 插槽（不在本层实现）。"""
    def __init__(
        self,
        retriever: Optional[KnowledgeRetriever] = None,
        store: Optional[SessionStore] = None,
        sanitizer: Optional[Callable[[str], str]] = None,
        disclaimer_provider: Optional[Callable[[Optional[str]], str]] = None,
    ):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param retriever: 参数 retriever
        :param store: 参数 store
        :param sanitizer: 参数 sanitizer
        :param disclaimer_provider: 参数 disclaimer_provider
        :return: 返回处理结果。
        """
        self.retriever = retriever
        self.store: SessionStore = store or InMemorySessionStore()
        self._sanitizer = sanitizer if sanitizer is not None else _default_sanitizer()
        self._disclaimer_provider = disclaimer_provider

    # ------------------------------------------------------------------
    def handle(
        self,
        message: str,
        *,
        tenant_id: str,
        visitor_ref: str,
        tenant_hint: str,
        language: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """返回与旧引擎兼容的 dict；返回 None = 委托旧引擎（调用方降级）。"""
        text = (message or "").strip()
        lang_code = _pick_lang(language)
        result = detect_intent(text)
        intent = result.intent
        # 旧意图 / 空输入：委托旧引擎（零回归）
        if not text or intent in LEGACY_DELEGATED:
            return None

        # 会话（租户+访客隔离）
        session = self.store.get_or_create(visitor_ref, tenant_id)
        ctx = build_context(self.store, session.session_id)
        self.store.append_turn(session.session_id, Turn(role="user", content=text, intent=intent))
        # 转人工显式请求
        if intent == "human_handoff":
            reply_raw = _HANDOFF_EXPLICIT[lang_code]
            out = self._pack(intent, reply_raw, language, route="handoff")
            self._log_assistant(session.session_id, out["reply"], intent)
            return out

        # 低置信/未识别：澄清式追问（禁止硬猜，指南 1.1）
        if intent == "unclear" or result.needs_llm:
            reply_raw = _CLARIFY[lang_code]
            out = self._pack("unclear", reply_raw, language, route="clarify")
            self._log_assistant(session.session_id, out["reply"], "unclear")
            return out

        # 新意图：知识检索（含指代上下文补充）
        if self.retriever is None:
            # 检索器未接线（DB 不可用等）：转人工，不冒充
            out = self._pack(intent, _HANDOFF[lang_code], language, route="retriever_unavailable")
            self._log_assistant(session.session_id, out["reply"], intent)
            return out

        coref = resolve_coreference_hint(ctx.turns)
        query = f"{coref} {text}" if coref else text
        retrieval: RetrievalResult = self.retriever.search(tenant_hint, query, intent=intent)
        if retrieval.missed:
            reply_raw = _HANDOFF[lang_code]
            out = self._pack(intent, reply_raw, language, route="knowledge_miss")
            self._log_assistant(session.session_id, out["reply"], intent)
            return out

        top = retrieval.top
        citations = [h.citation for h in retrieval.hits[:3] if h.citation]
        # ---- N4 LLM 回复（开关默认关；失败/关闭→规则回复降级，零回归）----
        llm_draft = try_llm_reply(
            intent=intent,
            knowledge_hits=retrieval.hits[:5],
            history=self.store.turns(session.session_id)[-6:],
            question=text,
            language=language,
        )
        if llm_draft is not None and getattr(llm_draft, "text", ""):
            reply_raw = llm_draft.text
            out = self._pack(
                intent, reply_raw, language,
                route="knowledge_llm",
                citations=citations,
                knowledge_score=top.score,
                llm={
                    "model": getattr(llm_draft, "model", ""),
                    "tokens": getattr(llm_draft, "tokens", 0),
                    "mock": getattr(llm_draft, "mock", False),
                    "degraded": getattr(llm_draft, "degraded", False),
                },
            )
            self._log_assistant(
                session.session_id, out["reply"], intent,
                meta={
                    "model": getattr(llm_draft, "model", ""),
                    "tokens": getattr(llm_draft, "tokens", 0),
                    "citation_refs": citations,
                },
            )
            return out

        # ---- 规则回复（降级路径）----
        reply_raw = top.text
        if citations:
            sep = "来源：" if lang_code == "zh" else "Source: "
            reply_raw = f"{top.text}\n{sep}" + " | ".join(citations)
        out = self._pack(
            intent, reply_raw, language,
            route="knowledge",
            citations=citations,
            knowledge_score=top.score,
        )
        self._log_assistant(
            session.session_id, out["reply"], intent,
            meta={"citation_refs": citations},
        )
        return out

    # ------------------------------------------------------------------
    def _pack(self, intent: str, reply_raw: str, language: Optional[str], **extra) -> Dict[str, Any]:
        """_pack。

        参数说明：
        :param self: 参数 self
        :param intent: 参数 intent
        :param reply_raw: 参数 reply_raw
        :param language: 参数 language
        :param **extra: 参数 **extra
        :return: 返回处理结果。
        """
        sanitized, sanitize_ok = self._sanitize(reply_raw)
        disclaimer = ""
        if self._disclaimer_provider is not None:
            try:
                disclaimer = self._disclaimer_provider(language) or ""
            except Exception:
                disclaimer = ""
        payload: Dict[str, Any] = {
            "intent": intent,
            "reply": sanitized,
            "disclaimer": disclaimer,
            "language": _pick_lang(language),
            "wangcai_router": True,
            **extra,
        }
        if not sanitize_ok:
            payload["sanitize_degraded"] = True
        return payload

    def _sanitize(self, text: str):
        """_sanitize。

        参数说明：
        :param self: 参数 self
        :param text: 参数 text
        :return: 返回处理结果。
        """
        try:
            return self._sanitizer(text), True
        except Exception:
            logger.warning("wangcai router: sanitizer 故障，退化为透传（已标记）")
            return text, False

    def _log_assistant(
        self,
        session_id: str,
        reply: str,
        intent: str,
        meta: Optional[Dict[str, Any]] = None,
    ) -> None:
        """assistant 轮写入；meta（model/tokens/citation_refs）随轮落 qa_log（N8 计量/N7 证据）。"""
        try:
            m = meta or {}
            self.store.append_turn(session_id, Turn(
                role="assistant", content=reply, intent=intent,
                model=m.get("model"), tokens=m.get("tokens"),
                citation_refs=m.get("citation_refs"),
            ))
        except Exception:
            logger.warning("wangcai router: assistant 轮写入失败（不影响回复）")


def _default_sanitizer() -> Callable[[str], str]:
    """默认净化器：挂 hermes/brand_guard（指南 N5 直接挂接，不新造）。"""
    try:
        from app.services.hermes.brand_guard import sanitize_public_copy
        return sanitize_public_copy
    except Exception:  # 挂接失败：透传（调用侧可见降级标记）
        return lambda s: s


# ---------------------------------------------------------------------------
# DB 接线工厂（供 tenant_wangcai_service 使用；纯逻辑测试不经过这里）
# ---------------------------------------------------------------------------

_default_router: Optional[WangcaiRouter] = None


def build_db_retriever(db) -> KnowledgeRetriever:
    """阶段一：hint 作用域的三源 fetcher（无 hint → 空，租户红线）。"""
    from app.models.case_study import CaseStudy
    from app.models.product import Product, ProductFaq
    def _products(hint: str) -> List[dict]:
        """_products。

        参数说明：
        :param hint: 参数 hint
        :return: 返回处理结果。
        """
        if not hint:
            return []
        like = f"%{hint}%"
        q = db.query(Product).filter(
            (Product.name.ilike(like)) | (Product.slug.ilike(like))
        ).limit(20)
        return [
            {
                "id": str(p.id),
                "text": " ".join(x for x in (p.name, getattr(p, "description", "") or "") if x)[:600],
                "citation": f"产品:{p.name}",
            }
            for p in q.all()
        ]

    def _faqs(hint: str) -> List[dict]:
        """_faqs。

        参数说明：
        :param hint: 参数 hint
        :return: 返回处理结果。
        """
        if not hint:
            return []
        like = f"%{hint}%"
        rows = (
            db.query(ProductFaq, Product)
            .join(Product, ProductFaq.product_id == Product.id)
            .filter((Product.name.ilike(like)) | (Product.slug.ilike(like)))
            .filter(ProductFaq.is_active.is_(True))
            .limit(30)
            .all()
        )
        out = []
        for faq, prod in rows:
            text = " ".join(
                x for x in (faq.question_zh, faq.answer_zh, faq.question_en or "", faq.answer_en or "") if x
            )
            out.append({"id": str(faq.id), "text": text[:600], "citation": f"FAQ:{prod.name}"})
        return out

    def _cases(hint: str) -> List[dict]:
        """_cases。

        参数说明：
        :param hint: 参数 hint
        :return: 返回处理结果。
        """
        if not hint:
            return []
        like = f"%{hint}%"
        q = db.query(CaseStudy).filter(
            (CaseStudy.project_name.ilike(like)) | ((CaseStudy.materials_used or "").ilike(like))
        ).limit(10)
        return [
            {
                "id": str(c.id),
                "text": " ".join(
                    x for x in (c.project_name, c.client_name or "", c.materials_used or "") if x
                )[:600],
                "citation": f"案例:{c.project_name}",
            }
            for c in q.all()
        ]

    return KnowledgeRetriever(_products, _faqs, _cases)


def get_router(db=None) -> WangcaiRouter:
    """全局 Router（进程级）。db 提供时挂真实检索器，否则检索降级为转人工。
    qa_log 落库开关开（`WANGCAI_QA_PERSIST_ENABLED=1`）且 db 可用时挂 DbSessionStore。"""
    global _default_router
    retriever = build_db_retriever(db) if db is not None else None
    if _default_router is None:
        _default_router = WangcaiRouter(retriever=retriever, store=_build_db_store(db))
        return _default_router
    # db 可用性变化时更新检索器
    _default_router.retriever = retriever
    return _default_router


def _build_db_store(db):
    """qa_log 落库 store（开关默认关→None→Router 用内存 store，零回归）。"""
    if db is None:
        return None
    try:
        from app.services.wangcai.persistence import DbSessionStore, qa_persist_enabled  # noqa: PLC0415
        if qa_persist_enabled():
            return DbSessionStore(db)
    except Exception:  # noqa: BLE001 — 持久化层故障不影响路由（内存 store 兜底）
        logger.warning("wangcai qa_log 落库层挂载失败，回退内存 store")
    return None
