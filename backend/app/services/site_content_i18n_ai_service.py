# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Hermes · 按租户 site_content 正文 AI 翻译为多语种 i18n。"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from sqlalchemy.orm import Session

from app.services.ai_invocation_service import invoke_llm
from app.services.im_locale_service import SUPPORTED_LANGUAGES
from app.services.site_content_i18n_service import (
    EXPORT_SITE_I18N_LANGS,
    apply_i18n_translations,
    ensure_site_content_i18n,
    extract_i18n_source_texts,
    infer_product_context,
)

logger = logging.getLogger(__name__)

# 分批调用 LLM，避免单次 JSON 过长
# 覆盖 Tier1（11 语）+ Tier2（12 语）= 23 种非英语语种
_I18N_LANG_BATCHES: tuple[tuple[str, ...], ...] = (
    ("zh", "ar", "es", "ru"),
    ("pt", "th", "vi", "id"),
    ("ms", "ja", "ko"),
    ("fr", "de", "it", "nl"),
    ("pl", "tr", "hi", "bn"),
    ("fa", "he", "uk", "fil"),
)


def _extract_json_object(text: str) -> dict[str, Any] | None:
    """_extract_json_object。

    参数说明：
    :param text: 参数 text
    :return: 返回处理结果。
    """
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


def _normalize_ai_translations(raw: dict[str, Any]) -> dict[str, dict[str, dict[str, str]]]:
    """解析 LLM 输出 → { lang: { section: { field: value } } }。"""
    root = raw.get("translations") if isinstance(raw.get("translations"), dict) else raw
    if not isinstance(root, dict):
        return {}
    out: dict[str, dict[str, dict[str, str]]] = {}
    for lang, sections in root.items():
        code = str(lang).strip().lower()[:5]
        if code not in SUPPORTED_LANGUAGES or code == "en":
            continue
        if not isinstance(sections, dict):
            continue
        lang_out: dict[str, dict[str, str]] = {}
        for section, fields in sections.items():
            if not isinstance(fields, dict):
                continue
            cleaned = {
                str(k): str(v).strip()
                for k, v in fields.items()
                if isinstance(v, (str, int, float)) and str(v).strip()
            }
            if cleaned:
                lang_out[str(section)] = cleaned
        if lang_out:
            out[code] = lang_out
    return out


def _build_translation_prompt(
    source: dict[str, dict[str, str]],
    target_langs: tuple[str, ...],
) -> str:
    """_build_translation_prompt。

    参数说明：
    :param source: 参数 source
    :param target_langs: 参数 target_langs
    :return: 返回处理结果。
    """
    lang_labels = ", ".join(f"{code}({SUPPORTED_LANGUAGES.get(code, code)})" for code in target_langs)
    source_json = json.dumps(source, ensure_ascii=False, indent=2)
    return (
        "你是 B2B 外贸官网本地化专家（Hermes 建站 Agent）。\n"
        "根据以下站点 canonical 文案，翻译为专业、面向海外采购商的官网用语。\n"
        "要求：\n"
        "1. 只输出一个 JSON 对象，不要 markdown 说明\n"
        "2. 结构必须为 {\"translations\": { \"语言代码\": { \"brand\"|\"home\"|\"about\"|\"products\": {字段: 译文} } } }\n"
        "3. 字段名必须与原文完全一致，不要增删字段\n"
        "4. 保留公司名/产品名原文或合理音译，CTA 按钮要短而有力\n"
        "5. 阿拉伯语/泰语等 RTL 语言仅翻译 value，键保持英文\n"
        f"6. 目标语言：{lang_labels}\n\n"
        f"原文：\n{source_json}\n"
    )


async def _translate_batch(
    db: Session | None,
    *,
    source: dict[str, dict[str, str]],
    target_langs: tuple[str, ...],
    tenant_id: str | None,
) -> dict[str, dict[str, dict[str, str]]]:
    """_translate_batch。

    参数说明：
    :param db: 参数 db
    :param source: 参数 source
    :param target_langs: 参数 target_langs
    :param tenant_id: 参数 tenant_id
    :return: 返回处理结果。
    """
    if not target_langs or not source:
        return {}
    prompt = _build_translation_prompt(source, target_langs)
    result = await invoke_llm(
        db,
        prompt=prompt,
        scenario="article",
        max_tokens=3500,
        task_type="hermes_site_i18n",
        tenant_id=tenant_id,
        lane="customer",
    )
    parsed = _extract_json_object(str(result.get("content") or ""))
    if not parsed:
        return {}
    return _normalize_ai_translations(parsed)


async def translate_site_content_i18n_ai(
    db: Session | None,
    site_content: dict[str, Any],
    *,
    tenant_id: str | None = None,
    langs: tuple[str, ...] | None = None,
    overwrite: bool = False,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """
    AI 按租户正文生成 i18n；失败时不改 site_content。
    返回 (site_content, stats)。
    """
    source = extract_i18n_source_texts(site_content)
    if not source:
        return site_content, {"ai_fields_added": 0, "ai_langs": 0, "ai_ok": False, "reason": "no_source"}

    target = langs or EXPORT_SITE_I18N_LANGS
    merged_translations: dict[str, dict[str, dict[str, str]]] = {}
    batches_run = 0
    try:
        pending = [code for code in target if code in EXPORT_SITE_I18N_LANGS]
        for batch in _I18N_LANG_BATCHES:
            batch_langs = tuple(code for code in batch if code in pending)
            if not batch_langs:
                continue
            part = await _translate_batch(
                db,
                source=source,
                target_langs=batch_langs,
                tenant_id=tenant_id,
            )
            batches_run += 1
            for lang, sections in part.items():
                merged_translations.setdefault(lang, {})
                for section, fields in sections.items():
                    merged_translations[lang].setdefault(section, {}).update(fields)
    except Exception as exc:
        logger.warning("site i18n AI translate failed: %s", exc)
        return site_content, {
            "ai_fields_added": 0,
            "ai_langs": 0,
            "ai_ok": False,
            "reason": str(exc),
            "batches_run": batches_run,
        }

    if not merged_translations:
        return site_content, {
            "ai_fields_added": 0,
            "ai_langs": 0,
            "ai_ok": False,
            "reason": "empty_response",
            "batches_run": batches_run,
        }

    updated, stats = apply_i18n_translations(site_content, merged_translations, overwrite=overwrite)
    return updated, {
        "ai_fields_added": stats.get("fields_added", 0),
        "ai_langs": stats.get("langs_touched", 0),
        "ai_ok": True,
        "batches_run": batches_run,
    }


async def enrich_site_content_i18n(
    db: Session | None,
    site_content: dict[str, Any],
    *,
    tenant_id: str | None = None,
    use_ai: bool = True,
    overwrite_ai: bool = True,
    product_name: str | None = None,
    company_name: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """
    AI 翻译（可选）+ 模板补全缺口。
    建站主路径：AI 成功后调用；模板路径仅 ensure。
    """
    stats: dict[str, Any] = {"i18n_source": "template"}
    current = site_content
    if use_ai and db is not None:
        current, ai_stats = await translate_site_content_i18n_ai(
            db,
            current,
            tenant_id=tenant_id,
            overwrite=overwrite_ai,
        )
        stats.update(ai_stats)
        if ai_stats.get("ai_ok"):
            stats["i18n_source"] = "ai"

    current, tpl_stats = ensure_site_content_i18n(
        current,
        product_name=product_name,
        company_name=company_name,
        overwrite=False,
    )
    stats["template_fields_added"] = tpl_stats.get("fields_added", 0)
    stats["template_langs"] = tpl_stats.get("langs_touched", 0)
    return current, stats


async def backfill_tenant_site_content_i18n_async(
    db: Session,
    *,
    dry_run: bool = False,
    overwrite: bool = False,
    use_ai: bool = False,
) -> dict[str, Any]:
    """扫描租户：可选 AI 翻译 + 模板补全。"""
    from app.models.tenant import Tenant
    from app.services.onboarding_im_contacts_service import _safe_settings
    from app.services.site_content_bridge import sync_site_content_to_brand
    tenants = db.query(Tenant).all()
    tenants_scanned = 0
    tenants_updated = 0
    fields_added_total = 0
    ai_tenants = 0
    skipped_no_site = 0
    samples: list[dict[str, str]] = []
    for tenant in tenants:
        tenants_scanned += 1
        settings = _safe_settings(tenant.settings)
        brand = settings.get("brand") if isinstance(settings.get("brand"), dict) else {}
        site = brand.get("site_content") if isinstance(brand.get("site_content"), dict) else None
        if not site:
            skipped_no_site += 1
            continue

        name, company, _ = infer_product_context(site)
        updated = site
        added = 0
        ai_ok = False
        if use_ai and not dry_run:
            updated, ai_stats = await translate_site_content_i18n_ai(
                db,
                updated,
                tenant_id=str(tenant.id),
                overwrite=overwrite,
            )
            added += int(ai_stats.get("ai_fields_added") or 0)
            ai_ok = bool(ai_stats.get("ai_ok"))

        updated, tpl_stats = ensure_site_content_i18n(
            updated,
            product_name=name,
            company_name=company,
            overwrite=overwrite if not use_ai else False,
        )
        added += int(tpl_stats.get("fields_added") or 0)
        if added <= 0 and not (use_ai and ai_ok):
            continue

        tenants_updated += 1
        fields_added_total += added
        if ai_ok:
            ai_tenants += 1
        if len(samples) < 5:
            samples.append(
                {
                    "domain": tenant.domain,
                    "fields_added": str(added),
                    "ai": "yes" if ai_ok else "no",
                }
            )

        if dry_run:
            continue

        brand = {**brand, "site_content": updated}
        settings["brand"] = sync_site_content_to_brand(brand, updated)
        tenant.settings = json.dumps(settings, ensure_ascii=False)

    if not dry_run and tenants_updated:
        db.commit()

    return {
        "tenants_scanned": tenants_scanned,
        "tenants_updated": tenants_updated,
        "fields_added_total": fields_added_total,
        "ai_tenants": ai_tenants,
        "skipped_no_site": skipped_no_site,
        "dry_run": dry_run,
        "overwrite": overwrite,
        "use_ai": use_ai,
        "langs": list(EXPORT_SITE_I18N_LANGS),
        "samples": samples,
    }
