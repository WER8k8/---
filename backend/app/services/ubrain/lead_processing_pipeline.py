# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""线索处理 Pipeline（责任链模式） — FIX-35

处理流程：
  Raw Lead → 标准化 → 去重 → 验证 → 评分 → 丰富 → 入库

每个处理器（Handler）独立完成一个步骤，链式传递。
支持跳过、中断、异步处理。
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional
import uuid

log = logging.getLogger(__name__)


class PipelineStatus(str, Enum):
    """Pipeline 处理状态。"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    SKIPPED = "skipped"        # 被跳过（重复等）
    FAILED = "failed"
    ENRICHED = "enriched"      # 已丰富但未入库


@dataclass
class LeadContext:
    """线索处理上下文，在 Pipeline 各节点间传递。"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    raw_data: dict[str, Any] = field(default_factory=dict)
    normalized: dict[str, Any] = field(default_factory=dict)
    status: PipelineStatus = PipelineStatus.PENDING
    errors: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    # 各阶段产出
    is_duplicate: bool = False
    duplicate_of: Optional[str] = None
    verification_result: Optional[dict] = None
    score: float = 0.0
    score_breakdown: dict[str, float] = field(default_factory=dict)
    enriched_data: dict[str, Any] = field(default_factory=dict)


# ============================================================
# 责任链基类
# ============================================================

class LeadHandler(ABC):
    """线索处理责任链节点基类。"""
    name: str = "base_handler"
    priority: int = 0  # 越小越先执行
    def __init__(self):
        """__init__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        self._next: Optional[LeadHandler] = None

    def set_next(self, handler: LeadHandler) -> LeadHandler:
        """设置下一个处理器。"""
        self._next = handler
        return handler

    async def handle(self, ctx: LeadContext) -> LeadContext:
        """处理线索，并传递给下一个处理器。"""
        try:
            ctx = await self.process(ctx)
        except Exception as e:
            log.error("[%s] 处理失败: %s", self.name, e)
            ctx.errors.append(f"{self.name}: {str(e)}")
            ctx.status = PipelineStatus.FAILED

        if self._next and ctx.status != PipelineStatus.FAILED:
            ctx = await self._next.handle(ctx)

        return ctx

    @abstractmethod
    async def process(self, ctx: LeadContext) -> LeadContext:
        """子类实现具体处理逻辑。"""
        ...


# ============================================================
# 处理器实现
# ============================================================

class NormalizeHandler(LeadHandler):
    """标准化处理器：将原始数据统一为标准格式。"""
    name = "normalize"
    priority = 1
    async def process(self, ctx: LeadContext) -> LeadContext:
        """process。

        参数说明：
        :param self: 参数 self
        :param ctx: 参数 ctx
        :return: 返回处理结果。
        """
        raw = ctx.raw_data
        ctx.normalized = {
            "email": (raw.get("email") or "").strip().lower(),
            "first_name": (raw.get("first_name") or raw.get("name") or "").strip(),
            "last_name": (raw.get("last_name") or "").strip(),
            "company": (raw.get("company") or raw.get("organization") or "").strip(),
            "title": (raw.get("title") or raw.get("position") or "").strip(),
            "phone": (raw.get("phone") or "").strip(),
            "linkedin_url": (raw.get("linkedin_url") or raw.get("linkedin") or "").strip(),
            "website": (raw.get("website") or raw.get("domain") or "").strip(),
            "country": (raw.get("country") or "").strip().upper()[:2],
            "industry": (raw.get("industry") or "").strip(),
            "source": raw.get("source", "unknown"),
            "source_url": raw.get("source_url", ""),
        }
        ctx.status = PipelineStatus.PROCESSING
        return ctx


class DedupHandler(LeadHandler):
    """去重处理器：检查线索是否已存在。"""
    name = "dedup"
    priority = 2
    async def process(self, ctx: LeadContext) -> LeadContext:
        """process。

        参数说明：
        :param self: 参数 self
        :param ctx: 参数 ctx
        :return: 返回处理结果。
        """
        try:
            from app.db.session import SessionLocal
            from app.services.ubrain.dedup_engine import DedupEngine
            db = SessionLocal()
            try:
                # P0-3: 必须传入 db，否则 DedupEngine 的 self.db 为 None，
                # check_duplicate 恒返回「非重复」，去重彻底失效。
                engine = DedupEngine(db)
                result = await engine.check_duplicate(ctx.normalized)
                if result.get("is_duplicate"):
                    ctx.is_duplicate = True
                    ctx.duplicate_of = result.get("existing_id")
                    ctx.status = PipelineStatus.SKIPPED
                    ctx.metadata["dedup"] = result
                    log.info("[dedup] 重复线索跳过: %s → %s", ctx.normalized.get("email"), ctx.duplicate_of)
                else:
                    ctx.metadata["dedup"] = {"is_duplicate": False}
            finally:
                db.close()
        except Exception as e:
            log.warning("[dedup] 去重检查失败，放行: %s", e)
            ctx.metadata["dedup"] = {"is_duplicate": False, "error": str(e)}

        return ctx


class VerifyHandler(LeadHandler):
    """验证处理器：验证邮箱有效性。"""
    name = "verify"
    priority = 3
    async def process(self, ctx: LeadContext) -> LeadContext:
        """process。

        参数说明：
        :param self: 参数 self
        :param ctx: 参数 ctx
        :return: 返回处理结果。
        """
        email = ctx.normalized.get("email", "")
        if not email:
            ctx.metadata["verify"] = {"verified": False, "reason": "no_email"}
            return ctx

        try:
            from app.services.ubrain.email_verification_service import (
                EmailVerificationService,
            )
            service = EmailVerificationService()
            result = await service.verify(email)
            ctx.verification_result = result
            ctx.metadata["verify"] = result
        except Exception as e:
            log.warning("[verify] 验证失败，标记为未验证: %s", e)
            ctx.metadata["verify"] = {"verified": False, "error": str(e)}

        return ctx


class ScoreHandler(LeadHandler):
    """评分处理器：对线索进行打分。"""
    name = "score"
    priority = 4
    async def process(self, ctx: LeadContext) -> LeadContext:
        """process。

        参数说明：
        :param self: 参数 self
        :param ctx: 参数 ctx
        :return: 返回处理结果。
        """
        try:
            from app.services.ubrain.lead_scoring_engine import LeadScoringEngine
            engine = LeadScoringEngine()
            result = await engine.score(ctx.normalized, ctx.verification_result)
            ctx.score = result.get("score", 0)
            ctx.score_breakdown = result.get("breakdown", {})
            ctx.metadata["score"] = result
        except Exception as e:
            log.warning("[score] 评分失败，使用默认分: %s", e)
            ctx.score = 50.0
            ctx.metadata["score"] = {"score": 50.0, "error": str(e)}

        return ctx


class EnrichHandler(LeadHandler):
    """丰富处理器：补充公司信息、行业标签等。"""
    name = "enrich"
    priority = 5
    async def process(self, ctx: LeadContext) -> LeadContext:
        """process。

        参数说明：
        :param self: 参数 self
        :param ctx: 参数 ctx
        :return: 返回处理结果。
        """
        company = ctx.normalized.get("company", "")
        website = ctx.normalized.get("website", "")
        enriched = {}
        # 从公司名推断行业
        if company:
            enriched["industry_tags"] = _infer_industry(company)
            enriched["company_size_hint"] = _infer_company_size(company)

        # 从网站推断
        if website:
            enriched["website_valid"] = website.startswith("http")
            enriched["has_ssl"] = website.startswith("https")

        ctx.enriched_data = enriched
        ctx.metadata["enrich"] = enriched
        ctx.status = PipelineStatus.ENRICHED
        return ctx


class PersistHandler(LeadHandler):
    """持久化处理器：将线索存入数据库。"""
    name = "persist"
    priority = 6
    async def process(self, ctx: LeadContext) -> LeadContext:
        """process。

        参数说明：
        :param self: 参数 self
        :param ctx: 参数 ctx
        :return: 返回处理结果。
        """
        if ctx.status == PipelineStatus.SKIPPED:
            return ctx

        try:
            from app.db.session import SessionLocal
            from app.models.prospect_lead import ProspectLead
            db = SessionLocal()
            try:
                lead = ProspectLead(
                    id=ctx.id,
                    email=ctx.normalized.get("email"),
                    first_name=ctx.normalized.get("first_name"),
                    last_name=ctx.normalized.get("last_name"),
                    company=ctx.normalized.get("company"),
                    title=ctx.normalized.get("title"),
                    phone=ctx.normalized.get("phone"),
                    linkedin_url=ctx.normalized.get("linkedin_url"),
                    website=ctx.normalized.get("website"),
                    country=ctx.normalized.get("country"),
                    industry=ctx.normalized.get("industry"),
                    source=ctx.normalized.get("source"),
                    score=ctx.score,
                    score_breakdown=ctx.score_breakdown,
                    enriched_data=ctx.enriched_data,
                    status="new",
                )
                db.add(lead)
                db.commit()
                ctx.status = PipelineStatus.COMPLETED
                ctx.metadata["persist"] = {"lead_id": ctx.id}
                log.info("[persist] 线索入库: %s (score=%.1f)", ctx.id, ctx.score)
            finally:
                db.close()
        except Exception as e:
            log.error("[persist] 入库失败: %s", e)
            ctx.errors.append(f"persist: {str(e)}")
            ctx.status = PipelineStatus.FAILED

        return ctx


# ============================================================
# Pipeline 构建器
# ============================================================

class LeadPipeline:
    """线索处理 Pipeline 构建器。

    用法:
        pipeline = LeadPipeline()
        ctx = await pipeline.process(raw_lead_data)
    """
    def __init__(self):
        """__init__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        self._handlers: list[LeadHandler] = []

    def add_handler(self, handler: LeadHandler) -> LeadPipeline:
        """添加处理器。"""
        self._handlers.append(handler)
        return self

    def build(self) -> LeadHandler | None:
        """构建责任链。"""
        if not self._handlers:
            return None

        # 按优先级排序
        self._handlers.sort(key=lambda h: h.priority)
        # 串联
        for i in range(len(self._handlers) - 1):
            self._handlers[i].set_next(self._handlers[i + 1])

        return self._handlers[0]

    @classmethod
    def create_default(cls) -> LeadPipeline:
        """创建默认 Pipeline（标准化→去重→验证→评分→丰富→入库）。"""
        pipeline = cls()
        pipeline.add_handler(NormalizeHandler())
        pipeline.add_handler(DedupHandler())
        pipeline.add_handler(VerifyHandler())
        pipeline.add_handler(ScoreHandler())
        pipeline.add_handler(EnrichHandler())
        pipeline.add_handler(PersistHandler())
        return pipeline

    async def process(self, raw_data: dict[str, Any]) -> LeadContext:
        """处理一条原始线索数据。"""
        ctx = LeadContext(raw_data=raw_data)
        first_handler = self.build()
        if first_handler:
            ctx = await first_handler.handle(ctx)
        return ctx

    async def process_batch(
        self, raw_leads: list[dict[str, Any]], max_concurrent: int = 5
    ) -> list[LeadContext]:
        """批量处理线索（带并发控制）。"""
        import asyncio
        semaphore = asyncio.Semaphore(max_concurrent)
        async def process_one(raw: dict) -> LeadContext:
            """process_one。

            参数说明：
            :param raw: 参数 raw
            :return: 返回处理结果。
            """
            async with semaphore:
                return await self.process(raw)

        tasks = [process_one(raw) for raw in raw_leads]
        return await asyncio.gather(*tasks, return_exceptions=True)


# ============================================================
# 辅助函数
# ============================================================

def _infer_industry(company_name: str) -> list[str]:
    """从公司名推断行业标签。"""
    tags = []
    name_lower = company_name.lower()
    industry_keywords = {
        "construction": "建材",
        "building": "建筑",
        "steel": "钢铁",
        "glass": "玻璃",
        "ceramic": "陶瓷",
        "furniture": "家具",
        "textile": "纺织",
        "chemical": "化工",
        "machinery": "机械",
        "electronics": "电子",
        "plastic": "塑料",
        "rubber": "橡胶",
        "metal": "金属",
        "wood": "木材",
        "stone": "石材",
        "lighting": "照明",
        "hardware": "五金",
        "tool": "工具",
        "pipe": "管材",
        "valve": "阀门",
        "pump": "泵",
        "insulation": "保温",
        "sealing": "密封",
        "roofing": "屋面",
        "flooring": "地板",
        "door": "门窗",
        "window": "门窗",
    }
    for keyword, tag in industry_keywords.items():
        if keyword in name_lower:
            tags.append(tag)
    return tags if tags else ["综合贸易"]


def _infer_company_size(company_name: str) -> str:
    """从公司名推断规模。"""
    name_lower = company_name.lower()
    if any(k in name_lower for k in ["group", "集团", "holding", "international"]):
        return "large"
    if any(k in name_lower for k in ["co.,ltd", "ltd", "limited", "有限公司"]):
        return "medium"
    return "small"