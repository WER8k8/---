# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Hermes 插件运行时 — 统一执行入口。"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from sqlalchemy.orm import Session

from app.services.hermes.brand_guard import sanitize_public_copy, sanitize_public_data
from app.services.hermes.flywheel_workflow import run_closed_loop_flywheel
from app.services.hermes.video_matrix_workflow import run_video_matrix_v1
from app.services.hermes.install_service import is_plugin_enabled
from app.services.hermes.registry import get_plugin
from app.services.ubrain.orchestrator import ubrain_orchestrator

logger = logging.getLogger(__name__)


class HermesPluginError(Exception):
    def __init__(self, code: str, message: str = ""):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param code: 参数 code
        :param message: 参数 message
        :return: 返回处理结果。
        """
        self.code = code
        super().__init__(message or code)


def _wrap_result(
    spec: dict[str, Any],
    *,
    plugin_id: str,
    kind: str,
    handler: str,
    reply: str,
    tool_result: dict[str, Any],
    needs_confirmation: bool,
    intent: str | None = None,
    disclaimer: str | None = None,
) -> dict[str, Any]:
    """_wrap_result。

    参数说明：
    :param spec: 参数 spec
    :param plugin_id: 参数 plugin_id
    :param kind: 参数 kind
    :param handler: 参数 handler
    :param reply: 参数 reply
    :param tool_result: 参数 tool_result
    :param needs_confirmation: 参数 needs_confirmation
    :param intent: 参数 intent
    :param disclaimer: 参数 disclaimer
    :return: 返回处理结果。
    """
    return {
        "plugin_id": plugin_id,
        "handler_kind": kind,
        "handler": handler,
        "intent": intent,
        "reply": sanitize_public_copy(reply),
        "tool_result": sanitize_public_data(tool_result),
        "needs_confirmation": needs_confirmation,
        "disclaimer": disclaimer,
        "public_name": (spec.get("public") or {}).get("name"),
    }


def _customer_ai_disclaimer(db: Session, tenant_id: str) -> str | None:
    """_customer_ai_disclaimer。

    参数说明：
    :param db: 参数 db
    :param tenant_id: 参数 tenant_id
    :return: 返回处理结果。
    """
    from app.models.tenant import Tenant
    from app.services.ai_traffic_connect_service import (
        NVIDIA_USAGE_POLICY_NOTICE,
        build_connect_status,
    )
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        return None
    status = build_connect_status(db, tenant)
    if status.get("free_tier"):
        return NVIDIA_USAGE_POLICY_NOTICE
    return None


def execute_plugin(
    db: Session,
    *,
    tenant_id: str,
    plugin_id: str,
    message: str,
    context: dict[str, Any] | None = None,
    user_id: str | None = None,
) -> dict[str, Any]:
    """execute_plugin。

    参数说明：
    :param db: 参数 db
    :param tenant_id: 参数 tenant_id
    :param plugin_id: 参数 plugin_id
    :param message: 参数 message
    :param context: 参数 context
    :param user_id: 参数 user_id
    :return: 返回处理结果。
    """
    spec = get_plugin(plugin_id)
    if not spec:
        raise HermesPluginError("unknown_plugin", f"未知插件: {plugin_id}")

    if not is_plugin_enabled(db, tenant_id, plugin_id):
        raise HermesPluginError("plugin_disabled", "插件未安装或已禁用")

    try:
        from app.services.ai_traffic_connect_service import ensure_tenant_ai_connectivity
        ensure_tenant_ai_connectivity(db, tenant_id)
    except Exception as exc:
        logger.warning("hermes ai_connect ensure failed tenant=%s: %s", tenant_id, exc)

    internal = spec.get("internal") or {}
    kind = str(internal.get("kind") or "")
    handler = str(internal.get("handler") or plugin_id)
    ctx = dict(context or {})
    ctx.setdefault("tenant_id", tenant_id)
    if user_id:
        ctx.setdefault("user_id", user_id)

    if kind == "agency_workflow":
        return _execute_agency_workflow(
            db, plugin_id, spec, kind, handler, message, tenant_id, ctx, user_id,
        )
    if kind == "workflow":
        return _execute_workflow(
            db, plugin_id, spec, kind, handler, message, tenant_id, user_id, ctx,
        )
    if kind == "site_builder":
        return _execute_site_builder(
            db, plugin_id, spec, kind, handler, message, tenant_id, ctx, user_id,
        )
    if kind == "ubrain_intent":
        return _execute_ubrain_intent(
            db, plugin_id, spec, kind, handler, message, tenant_id, ctx,
        )
    if kind == "gap_handler":
        return _execute_gap_handler(db, plugin_id, spec, kind, handler, tenant_id)
    if kind == "browser_companion":
        return _execute_browser_companion(db, plugin_id, spec, kind, handler, tenant_id)

    raise HermesPluginError("unsupported_kind", kind)


def _execute_agency_workflow(
    db: Session,
    plugin_id: str,
    spec: dict[str, Any],
    kind: str,
    handler: str,
    message: str,
    tenant_id: str,
    ctx: dict[str, Any],
    user_id: str | None,
) -> dict[str, Any]:
    """_execute_agency_workflow。

    参数说明：
    :param db: 参数 db
    :param plugin_id: 参数 plugin_id
    :param spec: 参数 spec
    :param kind: 参数 kind
    :param handler: 参数 handler
    :param message: 参数 message
    :param tenant_id: 参数 tenant_id
    :param ctx: 参数 ctx
    :param user_id: 参数 user_id
    :return: 返回处理结果。
    """
    import asyncio
    from app.services.hermes.agency.orchestrator_bridge import (
        run_geo_matrix_via_agency,
        run_hermes_agency_workflow,
    )
    # 安全执行异步函数：兼容已有事件循环（FastAPI）和无事件循环（Celery）
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    async def _run_agency():
        """_run_agency。
        :return: 返回处理结果。
        """
        if handler == "geo_content_matrix_b2b":
            return await run_geo_matrix_via_agency(
                db,
                message=message,
                tenant_id=tenant_id,
                context=ctx,
                created_by=user_id,
            )
        else:
            return await run_hermes_agency_workflow(
                db,
                workflow_id=handler,
                message=message,
                tenant_id=tenant_id,
                context=ctx,
            )

    if loop and loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            result = pool.submit(asyncio.run, _run_agency()).result()
    else:
        result = asyncio.run(_run_agency())
        intent = str(result.get("intent") or "agency_workflow")
    return _wrap_result(
        spec,
        plugin_id=plugin_id,
        kind=kind,
        handler=handler,
        reply=str(result.get("reply") or ""),
        tool_result=result,
        needs_confirmation=bool(
            spec.get("requires_confirmation") or result.get("human_review_required")
        ),
        intent=intent,
        disclaimer=_customer_ai_disclaimer(db, tenant_id),
    )


def _execute_workflow(
    db: Session,
    plugin_id: str,
    spec: dict[str, Any],
    kind: str,
    handler: str,
    message: str,
    tenant_id: str,
    user_id: str | None,
    ctx: dict[str, Any],
) -> dict[str, Any]:
    """_execute_workflow。

    参数说明：
    :param db: 参数 db
    :param plugin_id: 参数 plugin_id
    :param spec: 参数 spec
    :param kind: 参数 kind
    :param handler: 参数 handler
    :param message: 参数 message
    :param tenant_id: 参数 tenant_id
    :param user_id: 参数 user_id
    :param ctx: 参数 ctx
    :return: 返回处理结果。
    """
    if handler == "closed_loop_v1":
        result = run_closed_loop_flywheel(
            db,
            tenant_id=tenant_id,
            message=message,
            user_id=user_id,
        )
        return _wrap_result(
            spec,
            plugin_id=plugin_id,
            kind=kind,
            handler=handler,
            reply=str(result.get("reply") or ""),
            tool_result=result,
            needs_confirmation=bool(
                spec.get("requires_confirmation") or result.get("needs_confirmation")
            ),
            intent="flywheel_loop",
            disclaimer=_customer_ai_disclaimer(db, tenant_id),
        )
    if handler == "video_matrix_v1":
        result = run_video_matrix_v1(
            db,
            tenant_id=tenant_id,
            message=message,
            user_id=user_id,
            context=ctx,
        )
        return _wrap_result(
            spec,
            plugin_id=plugin_id,
            kind=kind,
            handler=handler,
            reply=str(result.get("reply") or ""),
            tool_result=result,
            needs_confirmation=bool(
                spec.get("requires_confirmation") or result.get("needs_confirmation")
            ),
            intent="video_matrix_publish",
            disclaimer=_customer_ai_disclaimer(db, tenant_id),
        )
    raise HermesPluginError("unknown_workflow", handler)


def _execute_site_builder(
    db: Session,
    plugin_id: str,
    spec: dict[str, Any],
    kind: str,
    handler: str,
    message: str,
    tenant_id: str,
    ctx: dict[str, Any],
    user_id: str | None,
) -> dict[str, Any]:
    """_execute_site_builder。

    参数说明：
    :param db: 参数 db
    :param plugin_id: 参数 plugin_id
    :param spec: 参数 spec
    :param kind: 参数 kind
    :param handler: 参数 handler
    :param message: 参数 message
    :param tenant_id: 参数 tenant_id
    :param ctx: 参数 ctx
    :param user_id: 参数 user_id
    :return: 返回处理结果。
    """
    if handler != "ai_site_builder_v1":
        raise HermesPluginError("unknown_site_builder", handler)
    from app.models.tenant import Tenant
    from app.services.hermes.site_build_workflow import run_ai_site_builder_v1
    product_name = str(ctx.get("product_name") or message or "").strip()
    if not product_name:
        raise HermesPluginError("missing_product", "请提供 product_name 或消息中的产品名")
    auto_save = bool(ctx.get("auto_save"))
    use_ai = ctx.get("use_ai", True)
    if isinstance(use_ai, str):
        use_ai = use_ai.lower() not in ("0", "false", "no")
    raw_images = ctx.get("product_images") or ctx.get("productImages") or []
    product_images = raw_images if isinstance(raw_images, list) else []
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    company_name = tenant.name if tenant else ""
    persist_fn = None
    if auto_save:
        from app.services.tenant_site_persistence import persist_tenant_site_content
        persist_fn = persist_tenant_site_content

    result = asyncio.run(
        run_ai_site_builder_v1(
            db,
            tenant_id=tenant_id,
            product_name=product_name,
            company_name=company_name or "",
            auto_save=auto_save,
            use_ai=bool(use_ai),
            persist_fn=persist_fn,
            product_images=product_images,
        )
    )
    pub_name = (spec.get("public") or {}).get("name") or plugin_id
    return _wrap_result(
        spec,
        plugin_id=plugin_id,
        kind=kind,
        handler=handler,
        reply=str(result.get("reply") or f"【{pub_name}】已完成"),
        tool_result=result,
        needs_confirmation=bool(result.get("needs_confirmation")),
        intent="ai_site_builder",
        disclaimer=_customer_ai_disclaimer(db, tenant_id),
    )


def _execute_ubrain_intent(
    db: Session,
    plugin_id: str,
    spec: dict[str, Any],
    kind: str,
    handler: str,
    message: str,
    tenant_id: str,
    ctx: dict[str, Any],
) -> dict[str, Any]:
    """_execute_ubrain_intent。

    参数说明：
    :param db: 参数 db
    :param plugin_id: 参数 plugin_id
    :param spec: 参数 spec
    :param kind: 参数 kind
    :param handler: 参数 handler
    :param message: 参数 message
    :param tenant_id: 参数 tenant_id
    :param ctx: 参数 ctx
    :return: 返回处理结果。
    """
    intent = handler
    if intent == "commercial_os_pipeline":
        from app.services.hermes.flywheel_workflow import public_flywheel_status
        result = {"status": public_flywheel_status(db, tenant_id), "mode": "pipeline_status"}
        reply = "编排管线状态已刷新。"
        chat = {"intent": intent, "reply": reply, "tool_result": result}
    else:
        chat = ubrain_orchestrator.chat(
            message,
            db=db,
            tenant_id=tenant_id,
            context=ctx,
        )
    return _wrap_result(
        spec,
        plugin_id=plugin_id,
        kind=kind,
        handler=handler,
        reply=str(chat.get("reply") or ""),
        tool_result=chat.get("tool_result") or {},
        needs_confirmation=bool(
            spec.get("requires_confirmation") or chat.get("needs_confirmation")
        ),
        intent=str(chat.get("intent") or intent),
        disclaimer=chat.get("disclaimer") or _customer_ai_disclaimer(db, tenant_id),
    )


def _execute_gap_handler(
    db: Session,
    plugin_id: str,
    spec: dict[str, Any],
    kind: str,
    handler: str,
    tenant_id: str,
) -> dict[str, Any]:
    """_execute_gap_handler。

    参数说明：
    :param db: 参数 db
    :param plugin_id: 参数 plugin_id
    :param spec: 参数 spec
    :param kind: 参数 kind
    :param handler: 参数 handler
    :param tenant_id: 参数 tenant_id
    :return: 返回处理结果。
    """
    from app.services.ubrain.accio_gap_handlers import execute_gap_mvp
    gap = execute_gap_mvp(handler)
    if not gap:
        raise HermesPluginError("gap_not_ready", "插件仍在建设中")
    pub_name = (spec.get("public") or {}).get("name") or plugin_id
    return _wrap_result(
        spec,
        plugin_id=plugin_id,
        kind=kind,
        handler=handler,
        reply=f"【{pub_name}】试点结果已生成，请查看详情并人工确认下一步。",
        tool_result=gap if isinstance(gap, dict) else {"data": gap},
        needs_confirmation=bool(spec.get("requires_confirmation")),
        intent=handler,
        disclaimer=_customer_ai_disclaimer(db, tenant_id),
    )


def _execute_browser_companion(
    db: Session,
    plugin_id: str,
    spec: dict[str, Any],
    kind: str,
    handler: str,
    tenant_id: str,
) -> dict[str, Any]:
    """_execute_browser_companion。

    参数说明：
    :param db: 参数 db
    :param plugin_id: 参数 plugin_id
    :param spec: 参数 spec
    :param kind: 参数 kind
    :param handler: 参数 handler
    :param tenant_id: 参数 tenant_id
    :return: 返回处理结果。
    """
    pub = spec.get("public") or {}
    companion = pub.get("companion") or {}
    install = companion.get("install") or {}
    pub_name = pub.get("name") or plugin_id
    guide = (install.get("guide") or "").strip()
    reply_lines = [
        f"【{pub_name}】为优丁平台专属浏览器伴侣，不能脱离优丁单独使用。",
        "请从优丁「视频引流发布」或插件市场点击「在优丁工作台使用」进入。",
    ]
    if guide:
        reply_lines.append(guide)
    return _wrap_result(
        spec,
        plugin_id=plugin_id,
        kind=kind,
        handler=handler,
        reply="\n".join(reply_lines),
        tool_result={
            "install_kind": "local_browser",
            "install": install,
            "disclaimer": companion.get("disclaimer"),
            "platforms": companion.get("platforms") or [],
        },
        needs_confirmation=False,
        intent="browser_companion",
        disclaimer=companion.get("disclaimer") or _customer_ai_disclaimer(db, tenant_id),
    )
