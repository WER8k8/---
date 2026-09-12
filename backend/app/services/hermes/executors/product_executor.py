"""Product Create Executor Plugin for Hermes Orchestration.

把既有 `ProductService.create_product` 包成 ExecutorRegistry 插件，
使产品创建可被任务图调度。

契约（见 docs/串联驱动设计-2026-09-10.md §3）：
    node.executor   = "product"
    node.capability = "product.create" | "default"
    node.input      = { title/name, slug?, category_id?, images[] }

设计纪律（对齐项目"不假交付"铁律）：
    · 失败一律返回 status="failed" 并带 error，不抛异常给调用方
    · 不静默吞异常（记录完整堆栈）
"""
from __future__ import annotations

import logging
import re
import uuid
from typing import Any, Dict

from app.schemas.hermes_orchestration import ExecutorResult, TaskNode

from .base import BaseExecutor, ExecutorContext, ExecutorRegistry

logger = logging.getLogger(__name__)

_SUPPORTED_CAPABILITIES = frozenset({"product.create", "default"})


def _slugify(text: str) -> str:
    """简易 slug 化：中文保留 / 空格与非法字符换 - / 小写。"""
    text = text.strip().lower()
    text = re.sub(r"[^\w\u4e00-\u9fff]+", "-", text)
    return text.strip("-") or uuid.uuid4().hex[:12]


class ProductExecutor(BaseExecutor):
    """产品创建执行器：真实调 ProductRepository 入库。"""

    @classmethod
    def get_executor_name(cls) -> str:
        return "product"

    async def run(self, node: TaskNode, context: ExecutorContext) -> ExecutorResult:
        capability = (node.capability or "default").strip()
        if capability not in _SUPPORTED_CAPABILITIES:
            return ExecutorResult(
                node_id=node.id,
                status="skipped",
                output={},
                error=f"product 不支持 capability={capability!r}",
            )

        params: dict[str, Any] = dict(node.input or {})
        title = str(params.get("title") or params.get("name") or "").strip()
        if not title:
            return ExecutorResult(
                node_id=node.id,
                status="failed",
                output={},
                error="missing_title: 产品节点需提供 title（或 name）",
            )

        slug = str(params.get("slug") or "").strip() or _slugify(title)
        category_id = str(params.get("category_id") or "").strip()
        if not category_id:
            category_id = self._first_category_id(context)

        images = params.get("images") or params.get("product_images") or []
        if isinstance(images, str):
            images = [images] if images else []
        image_url = images[0] if isinstance(images, list) and images else None

        try:
            from app.schemas.product import ProductCreate
            from app.services.product_service import ProductService

            data = ProductCreate(
                name=title,
                slug=slug,
                category_id=category_id,
                description=params.get("description") or None,
                image_url=image_url,
            )
            svc = ProductService(context.db)
            product = svc.create_product(
                data=data,
                created_by=str(context.tenant_id) if context.tenant_id else None,
            )
        except ValueError as exc:
            # slug 冲突等业务校验错误 → 明确 failed
            return ExecutorResult(
                node_id=node.id,
                status="failed",
                output={},
                error=f"slug_conflict: {exc}",
            )
        except Exception as exc:  # noqa: BLE001 — 契约要求失败返回而非抛出
            logger.exception("ProductExecutor 执行失败 node=%s", node.id)
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
                "product_id": str(product.id),
                "slug": product.slug,
                "name": product.name,
                "status": "created",
            },
        )

    @staticmethod
    def _first_category_id(context: ExecutorContext) -> str:
        """未显式给分类时取首个可用分类。取不到返回空（由业务层决定报错）。"""
        try:
            from app.models.product import Category

            cat = (
                context.db.query(Category)
                .filter(Category.is_active.is_(True))
                .first()
            )
            return str(cat.id) if cat else ""
        except Exception:  # noqa: BLE001
            return ""

    @classmethod
    def get_capabilities(cls) -> Dict[str, Dict[str, Any]]:
        return {
            "product.create": {
                "desc": "产品创建 → 真实入库（slug 唯一校验）",
                "input": ["title", "slug", "category_id", "images"],
                "output": ["product_id", "slug", "status"],
                "cost": {"tokens": 200, "seconds": 3},
                "needs_approval": False,
            },
        }


ExecutorRegistry.register(ProductExecutor())
