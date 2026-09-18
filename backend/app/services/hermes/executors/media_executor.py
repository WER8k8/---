# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Media Executor Plugin for Hermes Orchestration.

把既有 Media Factory / Video Edit services 包成 ExecutorRegistry 插件，
使业务链媒体生产环节可被任务图调度。

契约（对齐 inquiry_executor 模式）：
    node.executor   = "media"
    node.capability = "media.render" | "media.video" | "default"
    node.input      = { content_type?, prompt?, article_text?, duration? }

设计纪律：
    · 失败一律返回 status="failed" 并带 error，不抛异常给调用方
    · 若引擎未配置，degraded=True 不假成功
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from app.schemas.hermes_orchestration import ExecutorResult, TaskNode

from .base import BaseExecutor, ExecutorContext, ExecutorRegistry

logger = logging.getLogger(__name__)

_SUPPORTED_CAPABILITIES = frozenset({"media.render", "media.video", "default"})


def _media_mock_render() -> bool:
    """如实反映媒体引擎是否处于 mock 渲染态（有真实外部引擎依赖但未配置真源）。"""
    try:
        from app.core.config import settings  # type: ignore

        return bool(getattr(settings, "MEDIA_FACTORY_MOCK_RENDER", False))
    except Exception:  # noqa: BLE001
        return True


class MediaExecutor(BaseExecutor):
    """媒体渲染执行器：图文/视频素材生成。

    复用既有 media_factory_service（render task 创建），
    不做二次实现，只做契约适配。
    """

    @classmethod
    def get_executor_name(cls) -> str:
        return "media"

    async def run(self, node: TaskNode, context: ExecutorContext) -> ExecutorResult:
        capability = (node.capability or "default").strip()
        if capability not in _SUPPORTED_CAPABILITIES:
            return ExecutorResult(
                node_id=node.id,
                status="skipped",
                output={},
                error=f"media 不支持 capability={capability!r}",
            )

        params: dict[str, Any] = dict(node.input or {})

        if capability in ("media.render", "default"):
            return self._exec_media_render(node, params, context)
        elif capability == "media.video":
            return self._exec_media_video(node, params, context)

        return ExecutorResult(node_id=node.id, status="failed", output={}, error=f"unreachable capability={capability!r}")

    def _exec_media_render(
        self, node: TaskNode, params: dict[str, Any], context: ExecutorContext
    ) -> ExecutorResult:
        """Create a media render task (image or short video)."""
        content_type = str(params.get("content_type") or params.get("media_type") or "image").strip()
        prompt = str(params.get("prompt") or params.get("description") or "").strip()

        if not prompt:
            return ExecutorResult(
                node_id=node.id,
                status="failed",
                output={},
                error="missing_prompt: media.render 节点需提供 prompt/description",
            )

        try:
            from app.services.media_factory_service import create_render_task

            payload = {
                "content_type": content_type,
                "prompt": prompt,
                "article_text": str(params.get("article_text") or params.get("source_text") or ""),
                "tenant_id": str(context.tenant_id) if context.tenant_id else None,
                "source": "hermes_orchestration",
            }
            task = create_render_task(context.db, payload)
        except Exception as exc:  # noqa: BLE001
            logger.exception("MediaExecutor media.render 执行失败 node=%s", node.id)
            return ExecutorResult(
                node_id=node.id,
                status="failed",
                output={},
                error=f"{type(exc).__name__}: {exc}",
            )

        output = {
            "executor": "media",
            "capability": "media.render",
            "render_task_id": str(task.id),
            "content_type": content_type,
            "status": task.status,
            "degraded": _media_mock_render(),
        }
        return ExecutorResult(
            node_id=node.id,
            status="degraded" if _media_mock_render() else "succeeded",
            output=output,
        )

    def _exec_media_video(
        self, node: TaskNode, params: dict[str, Any], context: ExecutorContext
    ) -> ExecutorResult:
        """Create a video render task from article/text."""
        article = str(params.get("article_text") or params.get("text") or "").strip()
        if not article:
            return ExecutorResult(
                node_id=node.id,
                status="failed",
                output={},
                error="missing_article_text: media.video 节点需提供 article_text/text",
            )

        try:
            from app.services.media_factory_service import create_render_task, build_article_to_video_script_prompt

            script_prompt = build_article_to_video_script_prompt(article)
            payload = {
                "content_type": "video",
                "prompt": script_prompt,
                "article_text": article,
                "tenant_id": str(context.tenant_id) if context.tenant_id else None,
                "source": "hermes_orchestration",
                "duration": int(params.get("duration") or 30),
            }
            task = create_render_task(context.db, payload)
        except Exception as exc:  # noqa: BLE001
            logger.exception("MediaExecutor media.video 执行失败 node=%s", node.id)
            return ExecutorResult(
                node_id=node.id,
                status="failed",
                output={},
                error=f"{type(exc).__name__}: {exc}",
            )

        output = {
            "executor": "media",
            "capability": "media.video",
            "render_task_id": str(task.id),
            "content_type": "video",
            "status": task.status,
            "duration": int(params.get("duration") or 30),
            "degraded": _media_mock_render(),
        }
        return ExecutorResult(
            node_id=node.id,
            status="degraded" if _media_mock_render() else "succeeded",
            output=output,
        )

    @classmethod
    def get_capabilities(cls) -> Dict[str, Dict[str, Any]]:
        return {
            "media.render": {
                "desc": "媒体素材渲染（图文/短视频生成任务入队）",
                "input": ["content_type", "prompt", "article_text", "tenant_id"],
                "output": ["render_task_id", "content_type", "status"],
                "cost": {"tokens": 0, "seconds": 5},
                "needs_approval": False,
            },
            "media.video": {
                "desc": "文章转视频（article to script to video render task）",
                "input": ["article_text", "duration", "tenant_id"],
                "output": ["render_task_id", "status", "duration"],
                "cost": {"tokens": 500, "seconds": 30},
                "needs_approval": False,
            },
        }


ExecutorRegistry.register(MediaExecutor())
