import io, os

PATH = r"C:/Users/Administrator.WIN-36O2UQRI3U1/Desktop/上线网站开发完成/上线网站.worktrees/agents-install-vscode-cline-deploy-strix/backend/app/services/hermes/runtime.py"

with open(PATH, "r", encoding="utf-8") as f:
    lines = f.readlines()

# function execute_plugin spans lines 97..364 (1-indexed)
# branch blocks occupy lines 139..362 (1-indexed). Replace them with dispatch calls.
assert lines[138].startswith("    if kind == \"agency_workflow\":")
assert lines[361].rstrip() == "        )"  # closing of browser_companion return

dispatch = '''    if kind == "agency_workflow":
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
'''

# replace lines[138..362] (0-indexed 138..361 inclusive)
new_lines = lines[:138] + [dispatch] + lines[362:]

helpers = '''

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
        reply="\\n".join(reply_lines),
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
'''

new_lines = new_lines + [helpers]

with open(PATH, "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print("done, total lines:", len(new_lines))
