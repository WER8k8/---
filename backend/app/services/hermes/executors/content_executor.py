"""Content Executor Plugin — 内容页创建与发布。

承载实现（已存在）：
    services/content_service.ContentPageService.create_page(data: ContentPageCreate)
    app/schemas/content.ContentPageCreate —— title / slug 必填，slug 全局唯一

能力：
    content.create   —— 创建内容页
输入：
    {"title": "...", "slug": "可选，缺省自动生成", "content": "...", "summary": "...",
     "page_type": "page", "status": "draft"}
"""
from __future__ import annotations

import logging
import re
import uuid
from typing import Any, Dict

from app.schemas.hermes_orchestration import ExecutorResult, TaskNode

from .base import BaseExecutor, ExecutorContext, ExecutorRegistry

logger = logging.getLogger(__name__)

_SUPPORTED_CAPABILITIES = frozenset({"content.create", "default"})


def _slugify(text: str, *, fallback: str) -> str:
    """从标题生成 slug；非 ASCII 标题退化为随机后缀（避免中文 slug 冲突）。"""
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    if len(s) >= 3:
        return s[:180]
    return f"{fallback}-{uuid.uuid4().hex[:8]}"


class ContentExecutor(BaseExecutor):
    """内容页执行器。"""

    @classmethod
    def get_executor_name(cls) -> str:
        return "content"

    async def run(self, node: TaskNode, context: ExecutorContext) -> ExecutorResult:
        capability = (node.capability or "default").strip()
        if capability not in _SUPPORTED_CAPABILITIES:
            return ExecutorResult(
                node_id=node.id,
                status="skipped",
                output={},
                error=f"content 不支持 capability={capability!r}",
            )

        params: dict[str, Any] = dict(node.input or {})
        # input_from 可能从上游把正文送进来
        title = str(params.get("title") or params.get("product_name") or "").strip()
        body = params.get("content") or params.get("body")
        if not title:
            return ExecutorResult(
                node_id=node.id,
                status="failed",
                output={},
                error="missing_title: 内容节点需提供 title（或 product_name）",
            )

        slug = str(params.get("slug") or "").strip() or _slugify(title, fallback="page")

        try:
            from app.schemas.content import ContentPageCreate
            from app.services.content_service import ContentPageService

            data = ContentPageCreate(
                title=title,
                slug=slug,
                content=str(body) if body is not None else None,
                summary=str(params.get("summary")) if params.get("summary") else None,
                page_type=str(params.get("page_type") or "page"),
                status=str(params.get("status") or "draft"),
            )
            page = ContentPageService(context.db).create_page(data)
        except ValueError as exc:
            # slug 冲突是可预期的业务错误，明确区分
            logger.warning("ContentExecutor slug 冲突 node=%s slug=%s", node.id, slug)
            return ExecutorResult(
                node_id=node.id,
                status="failed",
                output={"slug": slug},
                error=f"slug_conflict: {exc}",
            )
        except Exception as exc:  # noqa: BLE001 — 契约要求失败返回而非抛出
            logger.exception("ContentExecutor 执行失败 node=%s", node.id)
            return ExecutorResult(
                node_id=node.id,
                status="failed",
                output={},
                error=f"{type(exc).__name__}: {exc}",
            )

        return ExecutorResult(
            node_id=node.id,
            status="succeeded",
            output={
                "executor": self.get_executor_name(),
                "page_id": str(getattr(page, "id", "")),
                "slug": str(getattr(page, "slug", slug)),
                "title": str(getattr(page, "title", title)),
                # 默认建的是 draft，不是已发布——如实标注，避免上层误判
                "status": str(getattr(page, "status", "draft")),
                "published": str(getattr(page, "status", "draft")) == "published",
            },
        )


    @classmethod
    def get_capabilities(cls) -> Dict[str, Dict[str, Any]]:
        return {
            "content.create": {
                "desc": "创建内容页（title/slug 必填，slug 全局唯一）",
                "input": ["title", "slug", "content", "summary", "page_type", "status"],
                "output": ["page_id", "slug", "title", "status", "published"],
                "cost": {"tokens": 5000, "seconds": 30},
                "needs_approval": False,
            },
        }


ExecutorRegistry.register(ContentExecutor())
