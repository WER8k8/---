# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""GEO/SEO 内容矩阵 — 借鉴 agency-orchestrator seo-content-matrix + content-pipeline DAG。

上游：关键词 → 策略 → 母版成稿 → SEO 审 → 多平台变体
下游：写入 ContentMaster 草稿，人审后走统一发布母版 / publish_worker。
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import json
import logging
import re
from typing import Any

from sqlalchemy.orm import Session


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

from app.models.content_master import ContentMaster
from app.services.geo.geo_writing_policy import (
    build_geo_write_instructions,
    build_humanize_rewrite_instructions,
    build_platform_variant_instructions,
    content_quality_to_dict,
    score_content_quality,
)
from app.services.geo.platform_rank_registry import publish_order_for_ranking
from app.services.geo.public_tech_reference_service import (
    build_technical_reference_block,
    public_reference_prompt_suffix,
)
from app.services.hermes.brand_guard import sanitize_public_copy, sanitize_public_data

logger = logging.getLogger(__name__)

DEFAULT_PLATFORMS: tuple[str, ...] = ("LinkedIn", "百家号", "抖音", "小红书")

_STEP_TITLES = {
    "keyword_research": "SEO 关键词与选题",
    "content_strategy": "内容矩阵策略",
    "write_article": "GEO 母版成稿",
    "seo_review": "SEO/GEO 审核",
    "platform_variants": "多平台变体",
}


def _ai_available(db: Session | None) -> bool:
    """_ai_available。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    try:
        from app.services.ai_key_probe import ai_key_status
        if db is None:
            return False
        return bool(ai_key_status(db).get("has_real_key"))
    except Exception:
        return False


async def _llm_text(
    db: Session | None,
    *,
    prompt: str,
    tenant_id: str | None,
    task_type: str,
    max_tokens: int = 2048,
) -> str:
    """_llm_text。

    参数说明：
    :param db: 参数 db
    :param prompt: 参数 prompt
    :param tenant_id: 参数 tenant_id
    :param task_type: 参数 task_type
    :param max_tokens: 参数 max_tokens
    :return: 返回处理结果。
    """
    from app.services.ai_invocation_service import invoke_llm
    result = await invoke_llm(
        db,
        prompt=prompt,
        scenario="article",
        max_tokens=max_tokens,
        task_type=task_type,
        tenant_id=tenant_id,
        lane="customer",
    )
    return str(result.get("content") or "").strip()


def _parse_keywords(message: str, ctx: dict[str, Any]) -> str:
    """_parse_keywords。

    参数说明：
    :param message: 参数 message
    :param ctx: 参数 ctx
    :return: 返回处理结果。
    """
    if ctx.get("target_keywords"):
        return str(ctx["target_keywords"]).strip()
    m = re.search(r"关键词[:：]\s*([^\n；;]+)", message)
    if m:
        return m.group(1).strip()
    m = re.search(r"([\u4e00-\u9fffA-Za-z0-9,\s/-]{4,120})", message)
    return (m.group(1).strip() if m else "rock wool insulation, fire rating, B2B export")[:200]


def _parse_domain(message: str, ctx: dict[str, Any]) -> str:
    """_parse_domain。

    参数说明：
    :param message: 参数 message
    :param ctx: 参数 ctx
    :return: 返回处理结果。
    """
    if ctx.get("domain"):
        return str(ctx["domain"]).strip()
    m = re.search(r"([\u4e00-\u9fffA-Za-z0-9]{2,40}(?:保温|建材|材料|insulation|building))", message, re.I)
    if m:
        return m.group(1).strip()
    category = str(ctx.get("category") or "建材出口")
    return category


def _parse_article_count(ctx: dict[str, Any]) -> int:
    """_parse_article_count。

    参数说明：
    :param ctx: 参数 ctx
    :return: 返回处理结果。
    """
    raw = ctx.get("article_count", 1)
    try:
        n = int(raw)
    except (TypeError, ValueError):
        n = 1
    return max(1, min(n, 3))


def _parse_platforms(ctx: dict[str, Any]) -> list[str]:
    """_parse_platforms。

    参数说明：
    :param ctx: 参数 ctx
    :return: 返回处理结果。
    """
    raw = ctx.get("platforms")
    if isinstance(raw, list) and raw:
        return [str(p).strip() for p in raw if str(p).strip()][:8]
    if isinstance(raw, str) and raw.strip():
        return [p.strip() for p in re.split(r"[,，、|]", raw) if p.strip()][:8]
    region = str(ctx.get("region") or "cn").lower()
    rank_first = ctx.get("rank_first", True)
    if rank_first:
        ordered = publish_order_for_ranking(
            region=region if region in ("cn", "global") else None,
            live_only=bool(ctx.get("live_platforms_only")),
            limit=8,
        )
        if ordered:
            return ordered
    return list(DEFAULT_PLATFORMS)


def _parse_tech_reference_block(ctx: dict[str, Any], *, domain: str) -> str:
    """公开专利/国标摘要等 — 脱敏后注入成稿 Prompt。"""
    refs: list[str] = []
    for key in ("tech_references", "patent_snippets", "standard_snippets"):
        raw = ctx.get(key)
        if isinstance(raw, list):
            refs.extend(str(x).strip() for x in raw if str(x).strip())
        elif isinstance(raw, str) and raw.strip():
            refs.append(raw.strip())
    if not refs:
        return ""
    return build_technical_reference_block(refs, category=domain)


def _step_record(step_id: str, status: str, *, summary: str = "", tokens: int = 0) -> dict[str, Any]:
    """_step_record。

    参数说明：
    :param step_id: 参数 step_id
    :param status: 参数 status
    :param summary: 参数 summary
    :param tokens: 参数 tokens
    :return: 返回处理结果。
    """
    return {
        "id": step_id,
        "title": _STEP_TITLES.get(step_id, step_id),
        "status": status,
        "summary": summary[:280],
        "tokens": tokens,
    }


def _fallback_keyword_plan(domain: str, keywords: str, article_count: int) -> str:
    """_fallback_keyword_plan。

    参数说明：
    :param domain: 参数 domain
    :param keywords: 参数 keywords
    :param article_count: 参数 article_count
    :return: 返回处理结果。
    """
    return (
        f"业务领域：{domain}\n核心关键词：{keywords}\n"
        f"推荐选题（{article_count} 篇）：\n"
        f"1. {domain} 采购指南：密度、防火等级与验收\n"
        f"2. {keywords.split(',')[0].strip()} 出口常见问题 FAQ\n"
        f"3. 工厂直供 vs 贸易商：B2B 询价要点\n"
    )


def _fallback_article(domain: str, keywords: str, title: str) -> dict[str, str]:
    """_fallback_article。

    参数说明：
    :param domain: 参数 domain
    :param keywords: 参数 keywords
    :param title: 参数 title
    :return: 返回处理结果。
    """
    body = (
        f"# {title}\n\n"
        f"> 品类：{domain} · GEO 内容矩阵生成 · **草稿，需人审后发布**\n\n"
        f"## 为什么采购方会搜「{keywords.split(',')[0].strip()}」\n\n"
        "工程与贸易采购在对比规格、防火等级、交付周期与 MOQ 时需要可引用的专业说明。"
        "本文面向 B2B 买家与 AI 搜索引擎可抓取的结构化说明。\n\n"
        "## 选型要点\n\n"
        "- 密度与导热系数如何影响节能与厚度\n"
        "- 防火等级（如 A1）与项目验收文件\n"
        "- 包装、柜量与目的港清关配合\n\n"
        "## 行动号召\n\n"
        "请访问**独立域官网**提交询盘表单或拨打页面电话，获取规格书与报价。"
        "勿只堆文章不带转化入口。\n"
    )
    return {
        "title": title,
        "meta_title": title[:60],
        "meta_description": f"{domain} B2B 出口选型与询价指南。"[:155],
        "body": body,
    }


def _fallback_variant(platform: str, master: dict[str, str]) -> dict[str, str]:
    """_fallback_variant。

    参数说明：
    :param platform: 参数 platform
    :param master: 参数 master
    :return: 返回处理结果。
    """
    title = master["title"]
    intro = {
        "LinkedIn": "Professional B2B note for engineers and procurement:",
        "百家号": "【建材出口】",
        "抖音": "【60秒讲清楚】",
        "小红书": "【工程采购笔记】",
    }.get(platform, f"【{platform}】")
    body = (
        f"{intro}\n\n{master['body'][:1200]}\n\n"
        f"— 发布平台适配：{platform} · 请人审后从统一发布台分发。\n"
    )
    return {
        "platform": platform,
        "title": f"[{platform}] {title}"[:500],
        "body": body,
    }


async def _run_keyword_plan(
    db: Session | None,
    *,
    domain: str,
    keywords: str,
    article_count: int,
    tenant_id: str | None,
    use_ai: bool,
) -> tuple[str, dict[str, Any]]:
    """_run_keyword_plan。

    参数说明：
    :param db: 参数 db
    :param domain: 参数 domain
    :param keywords: 参数 keywords
    :param article_count: 参数 article_count
    :param tenant_id: 参数 tenant_id
    :param use_ai: 参数 use_ai
    :return: 返回处理结果。
    """
    if not use_ai:
        text = _fallback_keyword_plan(domain, keywords, article_count)
        return text, _step_record("keyword_research", "success", summary="规则模板选题")

    prompt = (
        f"你是 B2B 建材外贸 SEO 专家。业务领域：{domain}\n"
        f"核心关键词：{keywords}\n目标文章数：{article_count}\n\n"
        "请输出：1) 关键词矩阵（意图/难度） 2) 长尾词扩展 3) "
        f"{article_count} 篇 GEO 友好文章选题（含建议标题）。用中文，面向出口采购与 AI 引用。"
    )
    try:
        text = await _llm_text(
            db,
            prompt=prompt,
            tenant_id=tenant_id,
            task_type="geo_content_matrix_keyword",
            max_tokens=1200,
        )
        return text, _step_record("keyword_research", "success", summary="LLM 关键词矩阵")
    except Exception as exc:
        logger.warning("geo keyword LLM failed: %s", exc)
        text = _fallback_keyword_plan(domain, keywords, article_count)
        return text, _step_record("keyword_research", "degraded", summary=str(exc)[:120])


async def _run_write_article(
    db: Session | None,
    *,
    domain: str,
    keywords: str,
    keyword_plan: str,
    tenant_id: str | None,
    use_ai: bool,
    tech_reference_block: str = "",
) -> tuple[dict[str, str], dict[str, Any]]:
    """_run_write_article。

    参数说明：
    :param db: 参数 db
    :param domain: 参数 domain
    :param keywords: 参数 keywords
    :param keyword_plan: 参数 keyword_plan
    :param tenant_id: 参数 tenant_id
    :param use_ai: 参数 use_ai
    :param tech_reference_block: 参数 tech_reference_block
    :return: 返回处理结果。
    """
    default_title = f"{domain} 出口采购与 {keywords.split(',')[0].strip()} 选型指南"
    if not use_ai:
        art = _fallback_article(domain, keywords, default_title)
        return art, _step_record("write_article", "success", summary="规则模板成稿")

    prompt = (
        build_geo_write_instructions(domain=domain, keywords=keywords)
        + public_reference_prompt_suffix(tech_reference_block)
        + f"\n\n关键词计划摘要：\n{keyword_plan[:1500]}\n"
    )
    try:
        raw = await _llm_text(
            db,
            prompt=prompt,
            tenant_id=tenant_id,
            task_type="geo_content_matrix_write",
            max_tokens=2500,
        )
        meta_title = default_title[:60]
        meta_desc = f"{domain} B2B 出口指南"[:155]
        mt = re.search(r"META_TITLE:\s*(.+)", raw)
        md = re.search(r"META_DESC:\s*(.+)", raw)
        if mt:
            meta_title = mt.group(1).strip()[:60]
        if md:
            meta_desc = md.group(1).strip()[:155]
        body = re.sub(r"META_TITLE:.*|META_DESC:.*", "", raw, flags=re.M).strip()
        title = meta_title if meta_title else default_title
        art = {"title": title, "meta_title": meta_title, "meta_description": meta_desc, "body": body}
        quality = score_content_quality(body, intent=keywords)
        if quality.ai_taste_score >= 0.35 and use_ai:
            try:
                rewrite_prompt = (
                    build_humanize_rewrite_instructions(ai_taste_score=quality.ai_taste_score)
                    + f"\n\n---\n\n{body[:3500]}"
                )
                body = await _llm_text(
                    db,
                    prompt=rewrite_prompt,
                    tenant_id=tenant_id,
                    task_type="geo_content_humanize",
                    max_tokens=2800,
                )
                body = re.sub(r"META_TITLE:.*|META_DESC:.*", "", body, flags=re.M).strip()
                art["body"] = body
                quality = score_content_quality(body, intent=keywords)
            except Exception as exc:
                logger.warning("geo humanize pass failed: %s", exc)
        art["quality"] = content_quality_to_dict(quality)
        summary = f"LLM 母版 · GEO分 {quality.geo_citation_score:.2f} · AI味 {quality.ai_taste_score:.2f}"
        return art, _step_record("write_article", "success", summary=summary)
    except Exception as exc:
        logger.warning("geo write LLM failed: %s", exc)
        art = _fallback_article(domain, keywords, default_title)
        return art, _step_record("write_article", "degraded", summary=str(exc)[:120])


async def _run_platform_variant(
    db: Session | None,
    *,
    platform: str,
    master: dict[str, str],
    tenant_id: str | None,
    use_ai: bool,
) -> dict[str, str]:
    """_run_platform_variant。

    参数说明：
    :param db: 参数 db
    :param platform: 参数 platform
    :param master: 参数 master
    :param tenant_id: 参数 tenant_id
    :param use_ai: 参数 use_ai
    :return: 返回处理结果。
    """
    if not use_ai:
        return _fallback_variant(platform, master)
    prompt = (
        build_platform_variant_instructions(platform)
        + f"\n\n标题：{master['title']}\n\n{master['body'][:2000]}\n\n输出 Markdown，第一行用 # 标题。"
    )
    try:
        raw = await _llm_text(
            db,
            prompt=prompt,
            tenant_id=tenant_id,
            task_type="geo_content_matrix_variant",
            max_tokens=1500,
        )
        title = master["title"]
        m = re.match(r"^#\s+(.+)$", raw.strip().splitlines()[0] if raw.strip() else "")
        if m:
            title = m.group(1).strip()[:500]
        return {"platform": platform, "title": f"[{platform}] {title}"[:500], "body": raw.strip()}
    except Exception as exc:
        logger.warning("geo variant LLM failed platform=%s: %s", platform, exc)
        return _fallback_variant(platform, master)


def _persist_masters(
    db: Session,
    *,
    tenant_id: str,
    master: dict[str, str],
    variants: list[dict[str, str]],
    created_by: str | None,
    geo_checklist: list[dict[str, str]],
) -> list[dict[str, Any]]:
    """_persist_masters。

    参数说明：
    :param db: 参数 db
    :param tenant_id: 参数 tenant_id
    :param master: 参数 master
    :param variants: 参数 variants
    :param created_by: 参数 created_by
    :param geo_checklist: 参数 geo_checklist
    :return: 返回处理结果。
    """
    created: list[dict[str, Any]] = []
    def _add_row(title: str, body: str, *, kind: str, platform: str | None = None) -> None:
        """_add_row。

        参数说明：
        :param title: 参数 title
        :param body: 参数 body
        :param kind: 参数 kind
        :param platform: 参数 platform
        :return: 返回处理结果。
        """
        safe_title = sanitize_public_copy(title)[:500]
        safe_body = sanitize_public_copy(body)
        row = ContentMaster(
            tenant_id=tenant_id,
            title=safe_title,
            body=safe_body,
            content_type="article",
            hub_summary=(master.get("meta_description") or safe_title)[:200],
            show_on_hub=False,
            status="draft",
            created_by=created_by,
        )
        db.add(row)
        created.append(
            {
                "kind": kind,
                "platform": platform,
                "title": safe_title,
                "status": "draft",
            }
        )

    meta_block = (
        f"\n\n---\n\n**Meta Title**: {master.get('meta_title', '')}\n\n"
        f"**Meta Description**: {master.get('meta_description', '')}\n"
    )
    _add_row(master["title"], master["body"] + meta_block, kind="master")
    for v in variants:
        _add_row(v["title"], v["body"], kind="variant", platform=v.get("platform"))

    if geo_checklist:
        checklist_md = "## GEO 执行清单（人审后落地到独立域）\n\n" + "\n".join(
            f"- [{item['id']}] {item['label']}" for item in geo_checklist
        )
        _add_row(
            f"[GEO清单] {master['title'][:80]}",
            checklist_md,
            kind="geo_checklist",
        )

    if created:
        db.commit()
        rows = (
            db.query(ContentMaster)
            .filter(
                ContentMaster.tenant_id == tenant_id,
                ContentMaster.status == "draft",
                ContentMaster.title.in_([c["title"] for c in created]),
            )
            .order_by(ContentMaster.created_at.desc())
            .limit(len(created))
            .all()
        )
        by_title = {r.title: r for r in rows}
        for item in created:
            row = by_title.get(item["title"])
            if row:
                item["id"] = row.id
                item["admin_path"] = "/client/content-masters"

    return created


def _content_strategy_step(platforms: list[str]) -> dict[str, Any]:
    """生成内容策略步骤记录（母版 + 平台变体计划）。"""
    return _step_record(
        "content_strategy",
        "success",
        summary=(
            f"排名优先 · 母版 1 篇 + 平台变体 {len(platforms)} 个 · "
            f"顺序: {', '.join(platforms[:4])}{'…' if len(platforms) > 4 else ''}"
        ),
    )


async def _run_platform_variant_steps(
    db: Session | None,
    *,
    platforms: list[str],
    master: dict[str, str],
    tenant_id: str | None,
    use_ai: bool,
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    """生成各平台变体并返回（variants, 步骤记录）。"""
    variants: list[dict[str, str]] = []
    for platform in platforms:
        variants.append(
            await _run_platform_variant(
                db,
                platform=platform,
                master=master,
                tenant_id=tenant_id,
                use_ai=use_ai,
            )
        )
    step = _step_record(
        "platform_variants",
        "success",
        summary=f"已生成 {len(variants)} 个平台变体",
    )
    return variants, step


def _build_pipeline_result(
    *,
    domain: str,
    keywords: str,
    platforms: list[str],
    ctx: dict[str, Any],
    tech_reference_block: str,
    use_ai: bool,
    steps: list[dict[str, Any]],
    keyword_plan: str,
    master: dict[str, str],
    variants: list[dict[str, str]],
) -> dict[str, Any]:
    """组装 GEO 内容矩阵流水线的最终返回结果。"""
    from app.services.ubrain.orchestrator import UBrainOrchestrator
    geo_pack = UBrainOrchestrator()._geo_submit_pack({"domain": ctx.get("domain") or domain})
    checklist = geo_pack.get("checklist") or []
    return {
        "workflow": "geo_content_matrix_v1",
        "domain": domain,
        "target_keywords": keywords,
        "platforms": platforms,
        "rank_first": ctx.get("rank_first", True),
        "tech_reference_applied": bool(tech_reference_block),
        "source": "ai" if use_ai else "template",
        "steps": steps,
        "keyword_plan_preview": keyword_plan[:800],
        "master_preview": {
            "title": master["title"],
            "meta_title": master.get("meta_title"),
            "meta_description": master.get("meta_description"),
            "quality": master.get("quality"),
        },
        "variants": [{"platform": v["platform"], "title": v["title"]} for v in variants],
        "geo_checklist": checklist,
        "human_review_required": True,
        "north_star": "人审后从统一发布母版矩阵分发，CTA 指向独立域询盘/电话。",
        "_master": master,
        "_variants_full": variants,
        "_checklist_rows": checklist,
    }


async def _run_pipeline_async(
    db: Session | None,
    *,
    message: str,
    ctx: dict[str, Any],
    tenant_id: str | None,
) -> dict[str, Any]:
    """执行 GEO 内容矩阵流水线：关键词计划 → 母版 → 变体。"""
    domain = _parse_domain(message, ctx)
    keywords = _parse_keywords(message, ctx)
    article_count = _parse_article_count(ctx)
    platforms = _parse_platforms(ctx)
    tech_reference_block = _parse_tech_reference_block(ctx, domain=domain)
    use_ai = _ai_available(db)
    steps: list[dict[str, Any]] = []
    keyword_plan, s1 = await _run_keyword_plan(
        db,
        domain=domain,
        keywords=keywords,
        article_count=article_count,
        tenant_id=tenant_id,
        use_ai=use_ai,
    )
    steps.append(s1)
    steps.append(_content_strategy_step(platforms))
    master, s3 = await _run_write_article(
        db,
        domain=domain,
        keywords=keywords,
        keyword_plan=keyword_plan,
        tenant_id=tenant_id,
        use_ai=use_ai,
        tech_reference_block=tech_reference_block,
    )
    steps.append(s3)
    seo_notes = (
        "检查：标题/H2 含目标词；FAQ Schema；内链产品页；独立域 canonical；/llms.txt。"
    )
    quality = master.get("quality") or content_quality_to_dict(
        score_content_quality(master.get("body") or "", intent=keywords)
    )
    seo_status = "success" if quality.get("passed") else "warning"
    seo_summary = (
        f"GEO引用 {quality.get('geo_citation_score')} · AI味 {quality.get('ai_taste_score')} · "
        + ("通过" if quality.get("passed") else "建议人审改稿")
    )
    steps.append(_step_record("seo_review", seo_status, summary=seo_summary[:200]))
    variants, variant_step = await _run_platform_variant_steps(
        db,
        platforms=platforms,
        master=master,
        tenant_id=tenant_id,
        use_ai=use_ai,
    )
    steps.append(variant_step)
    return _build_pipeline_result(
        domain=domain,
        keywords=keywords,
        platforms=platforms,
        ctx=ctx,
        tech_reference_block=tech_reference_block,
        use_ai=use_ai,
        steps=steps,
        keyword_plan=keyword_plan,
        master=master,
        variants=variants,
    )


def run_geo_content_matrix_job(
    db: Session,
    *,
    tenant_id: str,
    message: str,
    context: dict[str, Any] | None = None,
    created_by: str | None = None,
) -> dict[str, Any]:
    """DeerFlow intent=geo_content_matrix 执行体。"""
    ctx = dict(context or {})
    pack = _safe_asyncio_run(
        _run_pipeline_async(
            db,
            message=message,
            ctx=ctx,
            tenant_id=tenant_id,
        )
    )
    master = pack.pop("_master")
    variants = pack.pop("_variants_full")
    checklist = pack.pop("_checklist_rows")
    masters = _persist_masters(
        db,
        tenant_id=tenant_id,
        master=master,
        variants=variants,
        created_by=created_by,
        geo_checklist=checklist,
    )
    pack["masters"] = masters
    pack["cms_draft_count"] = len(masters)
    pack["write_back"] = "content_masters"
    return sanitize_public_data(pack)
