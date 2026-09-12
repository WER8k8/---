"""Hermes × agency-orchestrator — 专家角色库编排桥接。"""

from __future__ import annotations

import asyncio
import concurrent.futures
import logging
import re
from typing import Any

from sqlalchemy.orm import Session

from app.services.hermes.agency.role_loader import list_roles, roles_meta
from app.services.hermes.agency.llm_router import provider_catalog_meta
from app.services.hermes.agency.workflow_runner import list_workflows, run_workflow_async
from app.services.hermes.brand_guard import sanitize_public_data

logger = logging.getLogger(__name__)


def _safe_asyncio_run(coro):
    """安全执行异步协程：兼容已有事件循环（FastAPI）和无事件循环（Celery）。"""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, coro).result()
    return asyncio.run(coro)

WORKFLOW_PUBLIC: dict[str, dict[str, str]] = {
    "geo-content-matrix-b2b": {
        "intent": "geo_content_matrix",
        "label": "GEO 内容矩阵（专家编排）",
        "platforms_hint": "LinkedIn,百家号,抖音,小红书",
    },
    "marketing/seo-content-matrix": {
        "intent": "lead_content_pack",
        "label": "SEO 内容矩阵",
        "platforms_hint": "独立站/博客",
    },
    "seo-content-matrix": {
        "intent": "lead_content_pack",
        "label": "SEO 内容矩阵",
        "platforms_hint": "独立站/博客",
    },
    "marketing/xiaohongshu-content": {
        "intent": "china_platform_content",
        "label": "小红书种草笔记",
        "platforms_hint": "小红书",
    },
    "xiaohongshu-content": {
        "intent": "china_platform_content",
        "label": "小红书种草笔记",
        "platforms_hint": "小红书",
    },
    "department-collab/content-publish": {
        "intent": "china_platform_content",
        "label": "国内平台发布流程",
        "platforms_hint": "公众号,小红书,抖音,百家号",
    },
    "content-publish": {
        "intent": "china_platform_content",
        "label": "国内平台发布流程",
        "platforms_hint": "公众号,小红书,抖音,百家号",
    },
    "douyin-script": {
        "intent": "china_platform_content",
        "label": "抖音脚本",
        "platforms_hint": "抖音",
    },
}


def agency_catalog(*, include_roles: bool = True) -> dict[str, Any]:
    """agency_catalog。

    参数说明：
    :param include_roles: 参数 include_roles
    :return: 返回处理结果。
    """
    wfs = list_workflows()
    for row in wfs:
        pub = WORKFLOW_PUBLIC.get(row["workflow_id"], {})
        if not pub and "/" in row["workflow_id"]:
            pub = WORKFLOW_PUBLIC.get(row["workflow_id"].split("/")[-1], {})
        row["public_label"] = pub.get("label") or row.get("name")
        row["platforms_hint"] = pub.get("platforms_hint", "")
    meta = roles_meta()
    payload: dict[str, Any] = {
        "meta": meta,
        "workflows": wfs,
        "driver": "hermes_agency_orchestrator",
        "llm": provider_catalog_meta(),
    }
    if include_roles:
        payload["roles"] = list_roles()
    else:
        payload["roles"] = []
        payload["roles_summary"] = meta.get("categories") or {}
    return payload


def _parse_message_inputs(message: str, ctx: dict[str, Any]) -> dict[str, Any]:
    """_parse_message_inputs。

    参数说明：
    :param message: 参数 message
    :param ctx: 参数 ctx
    :return: 返回处理结果。
    """
    out = dict(ctx or {})
    m = re.search(r"([\u4e00-\u9fffA-Za-z0-9,\s/-]{4,80})", message or "")
    topic = (m.group(1).strip() if m else "建材出口")[:80]
    out.setdefault("domain", topic)
    out.setdefault("target_keywords", topic)
    out.setdefault("topic", topic)
    out.setdefault("product", topic)
    out.setdefault("category", str(ctx.get("category") or "建材"))
    out.setdefault("platform", str(ctx.get("platform") or "小红书"))
    return out


async def run_hermes_agency_workflow(
    db: Session,
    *,
    workflow_id: str,
    message: str,
    tenant_id: str,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """run_hermes_agency_workflow。

    参数说明：
    :param db: 参数 db
    :param workflow_id: 参数 workflow_id
    :param message: 参数 message
    :param tenant_id: 参数 tenant_id
    :param context: 参数 context
    :return: 返回处理结果。
    """
    inputs = _parse_message_inputs(message, dict(context or {}))
    result = await run_workflow_async(
        db,
        workflow_id=workflow_id,
        inputs=inputs,
        tenant_id=tenant_id,
    )
    pub = WORKFLOW_PUBLIC.get(workflow_id, {})
    result["intent"] = pub.get("intent") or "agency_workflow"
    result["human_review_required"] = True
    result["reply"] = (
        f"已完成「{result.get('workflow_name') or workflow_id}」专家编排"
        f"（{len(result.get('steps') or [])} 步）。请人工审阅后发布。"
    )
    return sanitize_public_data(result)


def _extract_geo_master(*, master_raw: Any, domain: str) -> dict[str, str]:
    """从工作流产出中解析主稿标题、meta 与正文。"""
    title = domain + " 出口采购指南"
    meta_title = title[:60]
    meta_desc = f"{domain} B2B 选型与询价"[:155]
    body = master_raw if isinstance(master_raw, str) else str(master_raw)
    mt = re.search(r"META_TITLE:\s*(.+)", body)
    md = re.search(r"META_DESC:\s*(.+)", body)
    if mt:
        meta_title = mt.group(1).strip()[:60]
        title = meta_title
    if md:
        meta_desc = md.group(1).strip()[:155]
    h1 = re.search(r"^#\s+(.+)$", body, re.M)
    if h1:
        title = h1.group(1).strip()[:500]

    return {
        "title": title,
        "meta_title": meta_title,
        "meta_description": meta_desc,
        "body": body,
    }


def _build_geo_variants(
    *,
    variants_raw: Any,
    platforms: list[str],
    master: dict[str, str],
) -> list[dict[str, str]]:
    """按平台生成分发变体，无原始变体内容时回退到模板变体。"""
    from app.services.ubrain.geo_content_matrix_service import _fallback_variant
    variants: list[dict[str, str]] = []
    if isinstance(variants_raw, str) and variants_raw.strip():
        for platform in platforms:
            variants.append(
                {
                    "platform": platform,
                    "title": f"[{platform}] {master['title']}"[:500],
                    "body": variants_raw[:4000],
                }
            )
    else:
        for platform in platforms:
            variants.append(_fallback_variant(platform, master))
    return variants


def _build_geo_matrix_result(
    *,
    domain: str,
    keywords: Any,
    platforms: list[str],
    wf_result: dict[str, Any],
    keyword_plan: Any,
    master: dict[str, str],
    variants: list[dict[str, str]],
    checklist: Any,
    masters: Any,
) -> dict[str, Any]:
    """组装 GEO 内容矩阵的对外返回结构。"""
    return {
        "workflow": "geo_content_matrix_agency_v1",
        "domain": domain,
        "target_keywords": keywords,
        "platforms": platforms,
        "source": wf_result.get("source") or "agency_orchestrator",
        "agency_steps": wf_result.get("steps") or [],
        "steps": wf_result.get("steps") or [],
        "keyword_plan_preview": (keyword_plan or "")[:800],
        "master_preview": {
            "title": master["title"],
            "meta_title": master.get("meta_title"),
            "meta_description": master.get("meta_description"),
        },
        "variants": [{"platform": v["platform"], "title": v["title"]} for v in variants],
        "geo_checklist": checklist,
        "masters": masters,
        "cms_draft_count": len(masters),
        "write_back": "content_masters",
        "human_review_required": True,
        "north_star": "Hermes 驱动 agency 专家角色编排 → 人审 → 统一发布台",
        "reply": f"GEO 内容矩阵已生成（{len(masters)} 篇草稿），请打开统一发布台审阅。",
    }


async def run_geo_matrix_via_agency(
    db: Session,
    *,
    message: str,
    tenant_id: str,
    context: dict[str, Any] | None = None,
    created_by: str | None = None,
) -> dict[str, Any]:
    """run_geo_matrix_via_agency。

    参数说明：
    :param db: 参数 db
    :param message: 参数 message
    :param tenant_id: 参数 tenant_id
    :param context: 参数 context
    :param created_by: 参数 created_by
    :return: 返回处理结果。
    """
    from app.services.ubrain.geo_content_matrix_service import (
        _parse_domain,
        _parse_keywords,
        _parse_platforms,
        _persist_masters,
    )
    from app.services.ubrain.orchestrator import UBrainOrchestrator
    ctx = dict(context or {})
    domain = _parse_domain(message, ctx)
    keywords = _parse_keywords(message, ctx)
    platforms = _parse_platforms(ctx)
    wf_result = await run_workflow_async(
        db,
        workflow_id="geo-content-matrix-b2b",
        inputs={
            "domain": domain,
            "target_keywords": keywords,
            "platforms": ",".join(platforms),
        },
        tenant_id=tenant_id,
    )
    outputs = wf_result.get("outputs") or {}
    keyword_plan = outputs.get("keyword_plan") or ""
    master_raw = outputs.get("master_article") or outputs.get("articles") or keyword_plan
    variants_raw = outputs.get("variants") or outputs.get("notes") or ""
    master = _extract_geo_master(master_raw=master_raw, domain=domain)
    variants = _build_geo_variants(
        variants_raw=variants_raw,
        platforms=platforms,
        master=master,
    )
    geo_pack = UBrainOrchestrator()._geo_submit_pack({"domain": domain})
    checklist = geo_pack.get("checklist") or []
    masters = _persist_masters(
        db,
        tenant_id=tenant_id,
        master=master,
        variants=variants,
        created_by=created_by,
        geo_checklist=checklist,
    )
    return sanitize_public_data(
        _build_geo_matrix_result(
            domain=domain,
            keywords=keywords,
            platforms=platforms,
            wf_result=wf_result,
            keyword_plan=keyword_plan,
            master=master,
            variants=variants,
            checklist=checklist,
            masters=masters,
        )
    )


def run_geo_matrix_via_agency_sync(
    db: Session,
    *,
    message: str,
    tenant_id: str,
    context: dict[str, Any] | None = None,
    created_by: str | None = None,
) -> dict[str, Any]:
    """run_geo_matrix_via_agency_sync。

    参数说明：
    :param db: 参数 db
    :param message: 参数 message
    :param tenant_id: 参数 tenant_id
    :param context: 参数 context
    :param created_by: 参数 created_by
    :return: 返回处理结果。
    """
    from app.services.ubrain.geo_content_matrix_service import (
        run_geo_content_matrix_job,
        _ai_available,
    )
    try:
        from app.core.config import settings
        if not getattr(settings, "HERMES_AGENCY_ORCHESTRATOR_ENABLED", True):
            raise RuntimeError("agency_disabled")
    except RuntimeError:
        return run_geo_content_matrix_job(
            db,
            tenant_id=tenant_id,
            message=message,
            context=context,
            created_by=created_by,
        )
    except Exception:
        pass

    if not _ai_available(db):
        return run_geo_content_matrix_job(
            db,
            tenant_id=tenant_id,
            message=message,
            context=context,
            created_by=created_by,
        )

    try:
        return _safe_asyncio_run(
            run_geo_matrix_via_agency(
                db,
                message=message,
                tenant_id=tenant_id,
                context=context,
                created_by=created_by,
            )
        )
    except Exception as exc:
        logger.warning("agency geo matrix failed, fallback legacy: %s", exc)
        return run_geo_content_matrix_job(
            db,
            tenant_id=tenant_id,
            message=message,
            context=context,
            created_by=created_by,
        )
