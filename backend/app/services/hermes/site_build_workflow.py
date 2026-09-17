# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Hermes 智能建站工作流 — ECC 专家流水线 + 设计技能约束。"""



from __future__ import annotations



from typing import Any



from sqlalchemy.orm import Session



from app.models.tenant import Tenant

from app.services.hermes.site_builder_ecc_pipeline import (

    load_site_builder_pipeline,

    run_ecc_site_builder_pipeline,

)

from app.services.hermes.site_design_guard import apply_design_guard, load_design_manifest



__all__ = [

    "apply_design_guard",

    "load_design_manifest",

    "design_skills_summary",

    "run_ai_site_builder_v1",

]





def design_skills_summary() -> list[dict[str, str]]:
    """design_skills_summary。
    :return: 返回处理结果。
    """
    manifest = load_design_manifest()
    return [

        {"id": s.get("id", ""), "title": s.get("title", "")}
        for s in (manifest.get("design_skills") or [])
        if isinstance(s, dict)

    ]





def _persist_site_if_needed(
    db: Session,
    *,
    tenant_id: str,
    site_content: Any,
    name: str,
    auto_save: bool,
    persist_fn,
) -> bool:
    """按需将生成的站点内容落库，返回是否已保存。"""
    if not (auto_save and persist_fn is not None):
        return False
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        return False
    persist_fn(db, tenant, site_content, name)
    return True


def _build_site_builder_reply(
    *,
    name: str,
    skills_count: int,
    expert_count: int,
    source: str,
    saved: bool,
) -> str:
    """拼装 ai_site_builder 的回复文案。"""
    if source == "template":
        return (
            f"AI 额度不足或未启用，已走 ECC 智能模板流水线生成「{name}」官网"
            + ("，并已保存。" if saved else "。")
        )
    return (
        f"Hermes 已驱动 ECC 专家流水线（{expert_count} 位专家、{skills_count} 项设计技能）"
        f"为「{name}」生成官网"
        + ("，并已保存。" if saved else "，请预览后保存。")
    )


def _build_site_builder_result(
    *,
    reply: str,
    site_content: Any,
    source: str,
    saved: bool,
    skills: list[dict[str, str]],
    pipeline: dict[str, Any],
    pipe_result: dict[str, Any],
) -> dict[str, Any]:
    """组装 ai_site_builder 的返回结构。"""
    return {
        "reply": reply,
        "site_content": site_content,
        "source": source,
        "saved": saved,
        "design_skills_applied": [s["id"] for s in skills],
        "design_skills": skills,
        "ecc_pipeline_version": pipeline.get("pipeline_version"),
        "ecc_experts_applied": pipe_result.get("ecc_experts_applied") or [],
        "pipeline_trace": pipe_result.get("pipeline_trace") or [],
        "plugin_handler": "ai_site_builder_v1",
        "needs_confirmation": not saved,
        "l_pro_publish_gate": pipe_result.get("l_pro_publish_gate") or {},
    }




async def run_ai_site_builder_v1(

    db: Session,

    *,

    tenant_id: str,

    product_name: str,

    company_name: str = "",

    auto_save: bool = False,

    use_ai: bool = True,

    persist_fn=None,

    product_images: list[Any] | None = None,

    skip_i18n_ai: bool = False,

) -> dict[str, Any]:

    """Hermes 插件 ai_site_builder — 驱动 ECC 美工/文案/视觉营销/美学 UI 流水线。"""
    name = (product_name or "").strip()
    if not name:

        raise ValueError("请填写产品名称")



    pipe_result = await run_ecc_site_builder_pipeline(

        db,
        product_name=name,
        company_name=company_name,
        tenant_id=tenant_id,
        use_ai=use_ai,
        product_images=product_images,
        skip_i18n_ai=skip_i18n_ai,

    )
    site_content = pipe_result["site_content"]
    source = pipe_result.get("source") or "template"
    skills = design_skills_summary()
    pipeline = load_site_builder_pipeline()
    saved = _persist_site_if_needed(
        db,
        tenant_id=tenant_id,
        site_content=site_content,
        name=name,
        auto_save=auto_save,
        persist_fn=persist_fn,
    )
    reply = _build_site_builder_reply(
        name=name,
        skills_count=len(skills),
        expert_count=len(pipe_result.get("ecc_experts_applied") or []),
        source=source,
        saved=saved,
    )
    return _build_site_builder_result(
        reply=reply,
        site_content=site_content,
        source=source,
        saved=saved,
        skills=skills,
        pipeline=pipeline,
        pipe_result=pipe_result,
    )


