# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""一键建站核心编排器。

串联 Vision 分析、结构生成、多语言内容、SEO 优化、站点组装五个步骤，
输出完整站点数据结构。
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.services.ai_invocation_service import invoke_llm
from app.services.site_builder.prompts import (
    build_content_user_prompt,
    build_seo_user_prompt,
    build_structure_user_prompt,
    build_vision_user_prompt,
    CONTENT_SYSTEM_PROMPT,
    SEO_SYSTEM_PROMPT,
    STRUCTURE_SYSTEM_PROMPT,
    VISION_SYSTEM_PROMPT,
)

logger = logging.getLogger(__name__)


def _extract_json_object(text: str) -> dict[str, Any] | None:
    """从 LLM 输出中提取 JSON 对象（兼容 markdown 包裹）。"""
    raw = (text or "").strip()
    if not raw:
        return None
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw, re.IGNORECASE)
    if fence:
        raw = fence.group(1).strip()
    start = raw.find("{")
    end = raw.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        parsed = json.loads(raw[start : end + 1])
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _extract_json_array(text: str) -> list[Any] | None:
    """从 LLM 输出中提取 JSON 数组。"""
    raw = (text or "").strip()
    if not raw:
        return None
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw, re.IGNORECASE)
    if fence:
        raw = fence.group(1).strip()
    start = raw.find("[")
    end = raw.rfind("]")
    if start < 0 or end <= start:
        return None
    try:
        parsed = json.loads(raw[start : end + 1])
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, list) else None


class SiteBuildError(Exception):
    """建站流程错误，携带步骤信息。"""
    def __init__(self, step: str, message: str, detail: Any = None):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param step: 参数 step
        :param message: 参数 message
        :param detail: 参数 detail
        :return: 返回处理结果。
        """
        self.step = step
        self.detail = detail
        super().__init__(f"[{step}] {message}")


class SiteBuilderOrchestrator:
    """一键建站编排器。

    使用方式：
        orchestrator = SiteBuilderOrchestrator(db, tenant_id=tenant_id)
        result = await orchestrator.build(
            product_images=["url1", "url2"],
            product_description_text="轻集料混凝土...",
            target_market="东南亚",
            language="zh",
        )
    """
    def __init__(
        self,
        db: Session | None,
        *,
        tenant_id: str | None = None,
        max_tokens: int = 2500,
    ):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param db: 参数 db
        :param tenant_id: 参数 tenant_id
        :param max_tokens: 参数 max_tokens
        :return: 返回处理结果。
        """
        self.db = db
        self.tenant_id = tenant_id
        self.max_tokens = max_tokens

    async def build(
        self,
        product_images: list[str],
        product_description_text: str,
        target_market: str,
        language: str,
    ) -> dict[str, Any]:
        """执行完整建站流程。

        Returns:
            {
                "site_id": str,
                "tenant_id": str | None,
                "pages": [{"page_type": "home", "slug": "index", "title": "...", ...}],
                "product_info": dict,
                "status": "success" | "partial",
                "steps_completed": list[str],
                "steps_failed": list[dict],
            }
        """
        steps_completed: list[str] = []
        steps_failed: list[dict[str, Any]] = []

        # ── Step 1: Vision 分析产品图片 ──
        product_info, completed, failed = await self._run_step_vision(
            product_images, product_description_text, steps_completed, steps_failed
        )

        # ── Step 2: 生成网站结构 ──
        site_structure, completed, failed = await self._run_step_structure(
            product_info, target_market, language, completed, failed
        )

        pages = site_structure.get("pages", [])
        if not pages:
            raise SiteBuildError("structure", "未生成任何页面")

        # ── Step 3: 生成多语言内容 ──
        pages_with_content = await self._run_step_content(
            pages, product_info, target_market, language, completed, failed
        )

        # ── Step 4: SEO 优化 ──
        pages_with_seo = await self._run_step_seo(
            pages_with_content, product_info, completed, failed
        )

        # ── Step 5: 组装站点数据 ──
        return self._assemble_result(
            pages_with_seo, product_info, completed, failed
        )

    async def _run_step_vision(
        self,
        product_images: list[str],
        product_description_text: str,
        steps_completed: list[str],
        steps_failed: list[dict[str, Any]],
    ) -> tuple[dict, list, list]:
        """执行 Vision 分析步骤。"""
        try:
            product_info = await self._step_vision_analysis(
                product_images, product_description_text
            )
            steps_completed.append("vision_analysis")
            return product_info, steps_completed, steps_failed
        except Exception as exc:
            logger.warning("Step 1 vision analysis failed: %s", exc)
            steps_failed.append({"step": "vision_analysis", "error": str(exc)})
            product_info = self._fallback_product_info(product_description_text)
            steps_completed.append("vision_analysis_fallback")
            return product_info, steps_completed, steps_failed

    async def _run_step_structure(
        self,
        product_info: dict,
        target_market: str,
        language: str,
        steps_completed: list[str],
        steps_failed: list[dict[str, Any]],
    ) -> tuple[dict, list, list]:
        """执行网站结构生成步骤。"""
        try:
            site_structure = await self._step_generate_structure(
                product_info, target_market, language
            )
            steps_completed.append("structure_generation")
            return site_structure, steps_completed, steps_failed
        except Exception as exc:
            logger.warning("Step 2 structure generation failed: %s", exc)
            steps_failed.append({"step": "structure_generation", "error": str(exc)})
            site_structure = self._fallback_structure(product_info)
            steps_completed.append("structure_generation_fallback")
            return site_structure, steps_completed, steps_failed

    async def _run_step_content(
        self,
        pages: list[dict],
        product_info: dict,
        target_market: str,
        language: str,
        steps_completed: list[str],
        steps_failed: list[dict[str, Any]],
    ) -> list[dict]:
        """执行多语言内容生成步骤。"""
        pages_with_content = []
        for page in pages:
            try:
                content = await self._step_generate_page_content(
                    page, product_info, target_market, language
                )
                page.update(content)
                steps_completed.append(f"content_{page.get('page_type', 'unknown')}")
            except Exception as exc:
                logger.warning(
                    "Step 3 content failed for %s: %s",
                    page.get("page_type"), exc,
                )
                steps_failed.append({
                    "step": "content_generation",
                    "page_type": page.get("page_type"),
                    "error": str(exc),
                })
                page.setdefault("title", page.get("title", ""))
                page.setdefault("meta_description", "")
                page.setdefault("content_markdown", "")
            pages_with_content.append(page)
        return pages_with_content

    async def _run_step_seo(
        self,
        pages_with_content: list[dict],
        product_info: dict,
        steps_completed: list[str],
        steps_failed: list[dict[str, Any]],
    ) -> list[dict]:
        """执行 SEO 优化步骤。"""
        pages_with_seo = []
        for page in pages_with_content:
            try:
                seo = await self._step_seo_optimize(
                    page, page, pages_with_content, product_info
                )
                page.update(seo)
                steps_completed.append(f"seo_{page.get('page_type', 'unknown')}")
            except Exception as exc:
                logger.warning(
                    "Step 4 SEO failed for %s: %s",
                    page.get("page_type"), exc,
                )
                steps_failed.append({
                    "step": "seo_optimization",
                    "page_type": page.get("page_type"),
                    "error": str(exc),
                })
                page.setdefault("seo_title", page.get("title", ""))
                page.setdefault("seo_keywords", [])
                page.setdefault("schema_type", "Article")
                page.setdefault("internal_links", [])
            pages_with_seo.append(page)
        return pages_with_seo

    def _assemble_result(
        self,
        pages_with_seo: list[dict],
        product_info: dict,
        steps_completed: list[str],
        steps_failed: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """组装最终结果。"""
        site_id = str(uuid.uuid4())
        status = "success" if not steps_failed else "partial"
        result = {
            "site_id": site_id,
            "tenant_id": self.tenant_id,
            "pages": pages_with_seo,
            "product_info": product_info,
            "status": status,
            "steps_completed": steps_completed,
            "steps_failed": steps_failed,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        logger.info(
            "Site build completed: site_id=%s, pages=%d, status=%s, steps_failed=%d",
            site_id, len(pages_with_seo), status, len(steps_failed),
        )
        return result

    # ──────────────────────────────────────────────────────────────────
    # Step 1: Vision 分析产品图片
    # ──────────────────────────────────────────────────────────────────
    async def _step_vision_analysis(
        self,
        product_images: list[str],
        product_description_text: str,
    ) -> dict[str, Any]:
        """Vision 分析产品图片，提取特性/参数/应用场景。"""
        if not product_images and not product_description_text.strip():
            raise SiteBuildError(
                "vision_analysis",
                "缺少产品图片和文字描述，无法分析",
            )

        if not product_images:
            # 无图片时退化为纯文本分析
            return self._text_only_product_info(product_description_text)

        prompt = build_vision_user_prompt(
            product_description_text, len(product_images)
        )
        result = await invoke_llm(
            self.db,
            prompt=prompt,
            scenario="vision",
            max_tokens=self.max_tokens,
            task_type="site_builder_vision",
            tenant_id=self.tenant_id,
            lane="customer",
        )
        content = str(result.get("content") or "")
        parsed = _extract_json_object(content)
        if not parsed:
            raise SiteBuildError(
                "vision_analysis",
                "Vision 分析返回格式错误，无法解析 JSON",
                detail=content[:500],
            )

        parsed.setdefault("product_name", "")
        parsed.setdefault("category", "")
        parsed.setdefault("features", [])
        parsed.setdefault("parameters", {})
        parsed.setdefault("application_scenarios", [])
        parsed.setdefault("visual_notes", "")
        return parsed

    def _text_only_product_info(self, text: str) -> dict[str, Any]:
        """无图片时从文字描述提取基础产品信息。"""
        return {
            "product_name": text[:50] if text else "产品",
            "category": "",
            "features": [t.strip() for t in text.split("。") if t.strip()][:5],
            "parameters": {},
            "application_scenarios": [],
            "visual_notes": "基于文字描述，无图片分析",
        }

    def _fallback_product_info(self, text: str) -> dict[str, Any]:
        """Vision 失败时的兜底产品信息。"""
        return {
            "product_name": text[:50] if text else "产品",
            "category": "建筑材料",
            "features": [],
            "parameters": {},
            "application_scenarios": [],
            "visual_notes": "Vision 分析失败，使用兜底数据",
        }

    # ──────────────────────────────────────────────────────────────────
    # Step 2: 生成网站结构
    # ──────────────────────────────────────────────────────────────────
    async def _step_generate_structure(
        self,
        product_info: dict[str, Any],
        target_market: str,
        language: str,
    ) -> dict[str, Any]:
        """生成网站页面结构。"""
        prompt = build_structure_user_prompt(
            product_info, target_market, language
        )
        result = await invoke_llm(
            self.db,
            prompt=prompt,
            scenario="article",
            max_tokens=self.max_tokens,
            task_type="site_builder_structure",
            tenant_id=self.tenant_id,
            lane="customer",
        )
        content = str(result.get("content") or "")
        parsed = _extract_json_object(content)
        if not parsed or not parsed.get("pages"):
            raise SiteBuildError(
                "structure_generation",
                "结构生成返回格式错误或无页面数据",
                detail=content[:500],
            )

        return parsed

    def _fallback_structure(self, product_info: dict[str, Any]) -> dict[str, Any]:
        """结构生成失败时的兜底页面结构。"""
        name = product_info.get("product_name", "产品")
        return {
            "pages": [
                {
                    "page_type": "home",
                    "slug": "index",
                    "title": f"{name} 生产厂家 · 供应商",
                    "sections": ["hero", "features", "products", "contact"],
                },
                {
                    "page_type": "products",
                    "slug": "products",
                    "title": f"{name} 产品中心",
                    "sections": ["product-list", "specs", "inquiry"],
                },
                {
                    "page_type": "about",
                    "slug": "about",
                    "title": "关于我们",
                    "sections": ["company-intro", "milestones", "factory"],
                },
                {
                    "page_type": "contact",
                    "slug": "contact",
                    "title": "联系我们",
                    "sections": ["form", "info", "map"],
                },
            ],
        }

    # ──────────────────────────────────────────────────────────────────
    # Step 3: 生成多语言内容
    # ──────────────────────────────────────────────────────────────────
    async def _step_generate_page_content(
        self,
        page: dict[str, Any],
        product_info: dict[str, Any],
        target_market: str,
        language: str,
    ) -> dict[str, Any]:
        """为单个页面生成内容。"""
        prompt = build_content_user_prompt(
            page, product_info, target_market, language
        )
        result = await invoke_llm(
            self.db,
            prompt=prompt,
            scenario="article",
            max_tokens=self.max_tokens,
            task_type="site_builder_content",
            tenant_id=self.tenant_id,
            lane="customer",
        )
        content = str(result.get("content") or "")
        parsed = _extract_json_object(content)
        if not parsed:
            raise SiteBuildError(
                "content_generation",
                f"页面 {page.get('page_type')} 内容生成格式错误",
                detail=content[:500],
            )

        parsed.setdefault("page_type", page.get("page_type"))
        parsed.setdefault("title", page.get("title", ""))
        parsed.setdefault("meta_description", "")
        parsed.setdefault("content_markdown", "")
        return parsed

    # ──────────────────────────────────────────────────────────────────
    # Step 4: SEO 优化
    # ──────────────────────────────────────────────────────────────────
    async def _step_seo_optimize(
        self,
        page: dict[str, Any],
        page_content: dict[str, Any],
        all_pages: list[dict[str, Any]],
        product_info: dict[str, Any],
    ) -> dict[str, Any]:
        """为单个页面生成 SEO 元数据。"""
        prompt = build_seo_user_prompt(
            page, page_content, all_pages, product_info
        )
        result = await invoke_llm(
            self.db,
            prompt=prompt,
            scenario="article",
            max_tokens=1500,
            task_type="site_builder_seo",
            tenant_id=self.tenant_id,
            lane="customer",
        )
        content = str(result.get("content") or "")
        parsed = _extract_json_object(content)
        if not parsed:
            raise SiteBuildError(
                "seo_optimization",
                f"页面 {page.get('page_type')} SEO 优化格式错误",
                detail=content[:500],
            )

        parsed.setdefault("page_type", page.get("page_type"))
        parsed.setdefault("seo_title", page_content.get("title", ""))
        parsed.setdefault("seo_keywords", [])
        parsed.setdefault("schema_type", "Article")
        parsed.setdefault("internal_links", [])
        return parsed
