# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""NVIDIA 按业务场景选择/切换模型（持久化到 ai_model_configs）。"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.ai_config import AIModelConfig, AIModelProvider
from app.services.nvidia_catalog_service import build_nvidia_catalog

# 产品内可切换的核心场景（与 AI 功能页面对齐）
PRODUCT_SCENARIOS: list[dict[str, str]] = [
    {
        "id": "inference",
        "label": "AI 推理 / 对话",
        "description": "智能问答、摘要、结构化输出、通用助手",
        "group": "content",
    },
    {
        "id": "article",
        "label": "文章 / 长文生成",
        "description": "SEO 文章、营销文案、新闻稿、产品详情",
        "group": "content",
    },
    {
        "id": "code",
        "label": "代码生成",
        "description": "代码补全、审查、技术文档",
        "group": "dev",
    },
    {
        "id": "vision",
        "label": "图像理解",
        "description": "读图问答、图表/OCR 分析",
        "group": "multimodal",
    },
    {
        "id": "text_to_video",
        "label": "文生视频",
        "description": "文本描述直接生成短视频",
        "group": "video",
    },
    {
        "id": "image_to_video",
        "label": "图生视频",
        "description": "以图片为起点生成后续镜头",
        "group": "video",
    },
    {
        "id": "video_transfer",
        "label": "视频风格转换",
        "description": "光照、环境、风格迁移",
        "group": "video",
    },
    {
        "id": "article_to_video_script",
        "label": "文章 → 分镜脚本",
        "description": "将长文拆分为镜头脚本与画面描述",
        "group": "video",
    },
    {
        "id": "article_to_video_render",
        "label": "脚本 → 视频",
        "description": "根据分镜脚本调用 Cosmos 渲染视频",
        "group": "video",
    },
    {
        "id": "video_understanding",
        "label": "视频理解",
        "description": "视频内容理解、质检与结构化提取",
        "group": "multimodal",
    },
]

SCENARIO_GROUP_LABELS = {
    "content": "内容创作",
    "video": "视频创作",
    "multimodal": "多模态",
    "dev": "开发辅助",
}

# 场景 id → 目录分类 id（article_to_video_* 走 article / text_to_video 候选）
SCENARIO_CATALOG_MAP = {
    "inference": "inference",
    "article": "article",
    "code": "code",
    "vision": "vision",
    "text_to_video": "text_to_video",
    "image_to_video": "image_to_video",
    "video_transfer": "video_transfer",
    "video_understanding": "video_understanding",
    "article_to_video_script": "article",
    "article_to_video_render": "text_to_video",
}


def _get_nvidia_provider(db: Session) -> AIModelProvider | None:
    """_get_nvidia_provider。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    return (
        db.query(AIModelProvider)
        .filter(AIModelProvider.provider_type == "nvidia", AIModelProvider.is_active)
        .order_by(AIModelProvider.is_default.desc())
        .first()
    )


def _catalog_index(catalog: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """_catalog_index。

    参数说明：
    :param catalog: 参数 catalog
    :return: 返回处理结果。
    """
    idx: dict[str, dict[str, Any]] = {}
    for cat in catalog.get("categories", []):
        idx[cat["id"]] = cat
    return idx


def _default_for_scenario(scenario_id: str, defaults: dict[str, str]) -> str:
    """_default_for_scenario。

    参数说明：
    :param scenario_id: 参数 scenario_id
    :param defaults: 参数 defaults
    :return: 返回处理结果。
    """
    if scenario_id in defaults:
        return defaults[scenario_id]
    mapped = SCENARIO_CATALOG_MAP.get(scenario_id, scenario_id)
    return defaults.get(mapped, defaults.get("inference", "meta/llama-3.1-8b-instruct"))


def get_platform_scenario_mappings(db: Session) -> dict[str, str]:
    """get_platform_scenario_mappings。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    provider = _get_nvidia_provider(db)
    if not provider:
        return dict(settings.AI_NVIDIA_MODELS)

    rows = (
        db.query(AIModelConfig)
        .filter(
            AIModelConfig.provider_id == provider.id,
            AIModelConfig.is_active,
        )
        .all()
    )
    mapping = {row.model_type: row.model_name for row in rows}
    defaults = settings.AI_NVIDIA_MODELS
    result: dict[str, str] = {}
    for sc in PRODUCT_SCENARIOS:
        sid = sc["id"]
        result[sid] = mapping.get(sid) or _default_for_scenario(sid, defaults)
    return result


def get_scenario_mappings(db: Session, tenant_id: str | None = None) -> dict[str, str]:
    """get_scenario_mappings。

    参数说明：
    :param db: 参数 db
    :param tenant_id: 参数 tenant_id
    :return: 返回处理结果。
    """
    platform = get_platform_scenario_mappings(db)
    if not tenant_id:
        return platform
    from app.services.tenant_scenario_service import merge_tenant_scenario_mappings
    return merge_tenant_scenario_mappings(db, tenant_id, platform)


def build_scenario_switch_payload(db: Session) -> dict[str, Any]:
    """build_scenario_switch_payload。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    catalog = build_nvidia_catalog()
    cat_idx = _catalog_index(catalog)
    defaults = catalog.get("defaults", {})
    current = get_platform_scenario_mappings(db)
    groups: dict[str, list[dict[str, Any]]] = {}
    for sc in PRODUCT_SCENARIOS:
        sid = sc["id"]
        cat_id = SCENARIO_CATALOG_MAP.get(sid, sid)
        cat = cat_idx.get(cat_id, {})
        candidates = cat.get("models", [])
        current_model = current.get(sid) or _default_for_scenario(sid, defaults)
        picked = next((m for m in candidates if m.get("id") == current_model), None)
        item = {
            **sc,
            "group_label": SCENARIO_GROUP_LABELS.get(sc["group"], sc["group"]),
            "current_model": current_model,
            "endpoint": (picked or {}).get("endpoint", "/v1/chat/completions"),
            "candidates": candidates,
        }
        groups.setdefault(sc["group"], []).append(item)

    ordered_groups = []
    for gid in ("content", "video", "multimodal", "dev"):
        if gid in groups:
            ordered_groups.append(
                {
                    "id": gid,
                    "label": SCENARIO_GROUP_LABELS[gid],
                    "scenarios": groups[gid],
                }
            )

    return {
        "provider": "nvidia",
        "note": catalog.get("note", ""),
        "groups": ordered_groups,
        "mappings": current,
    }


def save_scenario_mappings(db: Session, mappings: dict[str, str]) -> dict[str, str]:
    """save_scenario_mappings。

    参数说明：
    :param db: 参数 db
    :param mappings: 参数 mappings
    :return: 返回处理结果。
    """
    provider = _get_nvidia_provider(db)
    if not provider:
        raise ValueError("请先在模型配置中接入 NVIDIA NIM")

    allowed = {sc["id"] for sc in PRODUCT_SCENARIOS}
    saved: dict[str, str] = {}
    for scenario_id, model_name in mappings.items():
        if scenario_id not in allowed:
            continue
        model_name = (model_name or "").strip()
        if not model_name:
            continue

        row = (
            db.query(AIModelConfig)
            .filter(
                AIModelConfig.provider_id == provider.id,
                AIModelConfig.model_type == scenario_id,
            )
            .first()
        )
        if row is None:
            import uuid
            row = AIModelConfig(
                id=str(uuid.uuid4()),
                provider_id=provider.id,
                model_name=model_name,
                model_type=scenario_id,
                temperature="0.3",
                max_tokens="4096",
                is_active=True,
                is_default=True,
            )
            db.add(row)
        else:
            row.model_name = model_name
            row.is_active = True
            row.is_default = True
        saved[scenario_id] = model_name

    db.commit()
    try:
        from app.services.ai_engine import get_ai_engine
        engine = get_ai_engine()
        for scenario_id, model_name in saved.items():
            if hasattr(engine, "update_nvidia_scenario"):
                engine.update_nvidia_scenario(scenario_id, model_name)
    except Exception:
        pass

    return get_platform_scenario_mappings(db)


def resolve_scenario_model(db: Session | None, scenario_or_model: str) -> str:
    """解析场景 ID 为 ai_engine 可用的 model key（与 llms 字典键一致）。"""
    key = (scenario_or_model or "general").strip()
    if db is not None:
        mappings = get_scenario_mappings(db)
        if key in mappings:
            return key
    if key in settings.AI_NVIDIA_MODELS:
        return key
    return key if key else "general"
