# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""AI 模型能力解析与健康探测（供超管配置页展示）。"""

from __future__ import annotations

import time
from typing import Any

from sqlalchemy.orm import Session

from app.models.ai_config import AIModelConfig, AIModelProvider
from app.services.nvidia_catalog_service import CATEGORY_META, VIDEO_NIM_MODELS, classify_chat_model
from app.services.nvidia_scenario_health_service import (
    VIDEO_SCENARIOS,
    probe_chat_model,
    probe_cosmos_scenario,
)
from app.services.nvidia_scenario_service import PRODUCT_SCENARIOS
from app.services.scenario_health_store import load_health_snapshot

# 通用 model_type → 中文能力（非 NVIDIA 场景 seed 时兜底）
GENERIC_TYPE_LABELS: dict[str, str] = {
    "chat": "纯文本推理 / 对话",
    "embedding": "向量嵌入 / RAG",
    "image": "图像生成",
    "general": "通用推理",
}

VIDEO_MODEL_IDS = frozenset(vm["id"] for vm in VIDEO_NIM_MODELS)


def _category_label(cat_id: str) -> str:
    """_category_label。

    参数说明：
    :param cat_id: 参数 cat_id
    :return: 返回处理结果。
    """
    for meta in CATEGORY_META:
        if meta["id"] == cat_id:
            return meta["label"]
    for sc in PRODUCT_SCENARIOS:
        if sc["id"] == cat_id:
            return sc["label"]
    return GENERIC_TYPE_LABELS.get(cat_id, cat_id)


def _category_description(cat_id: str) -> str:
    """_category_description。

    参数说明：
    :param cat_id: 参数 cat_id
    :return: 返回处理结果。
    """
    for meta in CATEGORY_META:
        if meta["id"] == cat_id:
            return meta["description"]
    for sc in PRODUCT_SCENARIOS:
        if sc["id"] == cat_id:
            return sc["description"]
    return ""


def _video_catalog_entry(model_name: str) -> dict[str, Any] | None:
    """_video_catalog_entry。

    参数说明：
    :param model_name: 参数 model_name
    :return: 返回处理结果。
    """
    for vm in VIDEO_NIM_MODELS:
        if vm["id"] == model_name:
            return vm
    return None


def resolve_model_capability(model_name: str, model_type: str) -> dict[str, Any]:
    """解析模型能力与接口类型（不发起外网请求）。"""
    model_name = (model_name or "").strip()
    model_type = (model_type or "chat").strip()
    video_meta = _video_catalog_entry(model_name)
    if video_meta or model_name.startswith("nvidia/cosmos-"):
        vm = video_meta or {}
        input_mode = vm.get("input", "text")
        if input_mode == "text":
            cap_id = "text_to_video"
        elif input_mode == "image":
            cap_id = "image_to_video"
        elif "transfer" in model_name:
            cap_id = "video_transfer"
        else:
            cap_id = model_type if model_type in {c["id"] for c in CATEGORY_META} else "video_to_video"
        return {
            "capability_id": cap_id,
            "capability_label": _category_label(cap_id),
            "capability_desc": vm.get("description") or _category_description(cap_id),
            "endpoint": "/v1/infer",
            "input_modes": [input_mode] if input_mode else ["text"],
            "modality": "video",
        }

    cats = classify_chat_model(model_name) if model_name else set()
    cap_id = model_type if model_type in {c["id"] for c in CATEGORY_META} else None
    if not cap_id and cats:
        priority = ("vision", "code", "article", "embedding", "guardrail", "video_understanding", "inference")
        for pid in priority:
            if pid in cats:
                cap_id = pid
                break
    if not cap_id:
        cap_id = model_type if model_type else "inference"

    input_modes = ["text"]
    if cap_id == "vision" or "vision" in cats:
        input_modes = ["text", "image"]

    return {
        "capability_id": cap_id,
        "capability_label": _category_label(cap_id),
        "capability_desc": _category_description(cap_id),
        "endpoint": "/v1/chat/completions",
        "input_modes": input_modes,
        "modality": "chat",
    }


def _has_valid_key(key: str | None) -> bool:
    """_has_valid_key。

    参数说明：
    :param key: 参数 key
    :return: 返回处理结果。
    """
    text = (key or "").strip()
    return bool(text) and text not in {"your_", "change-me", "sk-your-key-here"}


def probe_single_model(
    model_name: str,
    model_type: str,
    *,
    api_key: str | None,
    base_url: str | None,
) -> dict[str, Any]:
    """探测单个模型可用性（使用提供商 DB 中的 Key）。"""
    cap = resolve_model_capability(model_name, model_type)
    if not _has_valid_key(api_key):
        return {
            **cap,
            "status": "no_key",
            "status_label": "未配置 Key",
            "healthy": False,
            "latency_ms": 0,
            "error": "请先配置有效的 API Key",
        }

    is_video = (
        model_name in VIDEO_MODEL_IDS
        or model_name.startswith("nvidia/cosmos-")
        or model_type in VIDEO_SCENARIOS
        or cap["endpoint"] == "/v1/infer"
    )
    integrate_base = (base_url or "https://integrate.api.nvidia.com/v1").rstrip("/")
    if is_video and "/v1/infer" not in integrate_base:
        return {
            **cap,
            "status": "key_ok",
            "status_label": "Key 有效",
            "healthy": True,
            "latency_ms": 0,
            "note": "视频类模型走 /v1/infer；托管 Key 已就绪，渲染需 Cosmos 端点或工作流调用",
            "skipped_infer_probe": True,
        }

    if is_video:
        probe = probe_cosmos_scenario(model_name)
        status = "available" if probe.get("healthy") else "unavailable"
        return {
            **cap,
            "status": status,
            "status_label": "可用" if probe.get("healthy") else "不可用",
            "healthy": bool(probe.get("healthy")),
            "latency_ms": probe.get("latency_ms", 0),
            "error": probe.get("error"),
            "note": probe.get("note"),
        }

    probe = probe_chat_model(
        model_name,
        api_key=api_key,
        base_url=base_url,
    )
    status = "available" if probe.get("healthy") else "unavailable"
    return {
        **cap,
        "status": status,
        "status_label": "可用" if probe.get("healthy") else "不可用",
        "healthy": bool(probe.get("healthy")),
        "latency_ms": probe.get("latency_ms", 0),
        "error": probe.get("error"),
    }


def enrich_model_row(
    model: AIModelConfig,
    provider: AIModelProvider | None,
    provider_name: str | None = None,
    *,
    health_by_scenario: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """enrich_model_row。

    参数说明：
    :param model: 参数 model
    :param provider: 参数 provider
    :param provider_name: 参数 provider_name
    :param health_by_scenario: 参数 health_by_scenario
    :return: 返回处理结果。
    """
    cap = resolve_model_capability(model.model_name, model.model_type)
    row: dict[str, Any] = {
        "id": str(model.id),
        "provider_id": str(model.provider_id),
        "provider_name": provider_name,
        "model_name": model.model_name,
        "model_type": model.model_type,
        "temperature": model.temperature,
        "max_tokens": model.max_tokens,
        "is_active": bool(model.is_active),
        "active": bool(model.is_active),
        "is_default": bool(model.is_default),
        "sort_order": int(model.sort_order or 0),
        **cap,
        "status": "unknown",
        "status_label": "未检测",
        "healthy": None,
        "latency_ms": None,
    }
    if not model.is_active:
        row["status"] = "disabled"
        row["status_label"] = "已禁用"
        return row

    if provider and not _has_valid_key(provider.api_key):
        row["status"] = "no_key"
        row["status_label"] = "未配置 Key"
        return row

    if health_by_scenario and model.model_type in health_by_scenario:
        snap = health_by_scenario[model.model_type]
        if snap.get("model") == model.model_name:
            healthy = bool(snap.get("healthy"))
            row["healthy"] = healthy
            row["latency_ms"] = snap.get("latency_ms")
            if healthy:
                row["status"] = "available"
                row["status_label"] = "可用"
            elif snap.get("mode") == "mock":
                row["status"] = "key_ok"
                row["status_label"] = "Mock 模式"
            else:
                row["status"] = "unavailable"
                row["status_label"] = "不可用"
            row["error"] = snap.get("error")
            row["checked_at"] = snap.get("checked_at")

    return row


def build_models_enriched_list(db: Session, provider_id: str | None = None) -> list[dict[str, Any]]:
    """build_models_enriched_list。

    参数说明：
    :param db: 参数 db
    :param provider_id: 参数 provider_id
    :return: 返回处理结果。
    """
    query = db.query(AIModelConfig)
    if provider_id:
        query = query.filter(AIModelConfig.provider_id == provider_id)
    models = (
        query.order_by(
            AIModelConfig.provider_id.asc(),
            AIModelConfig.sort_order.asc(),
            AIModelConfig.is_default.desc(),
        ).all()
    )
    providers = {str(p.id): p for p in db.query(AIModelProvider).all()}
    provider_names = {str(p.id): p.name for p in providers.values()}
    snapshot = load_health_snapshot(db)
    health_by_scenario: dict[str, dict[str, Any]] = {}
    if snapshot:
        checked_at = snapshot.get("saved_at") or snapshot.get("checked_at")
        for sc in snapshot.get("scenarios") or []:
            sid = sc.get("scenario")
            if sid:
                health_by_scenario[sid] = {**sc, "checked_at": checked_at}

    return [
        enrich_model_row(
            m,
            providers.get(str(m.provider_id)),
            provider_names.get(str(m.provider_id)),
            health_by_scenario=health_by_scenario,
        )
        for m in models
    ]


def probe_all_configured_models(db: Session, provider_id: str | None = None) -> dict[str, Any]:
    """probe_all_configured_models。

    参数说明：
    :param db: 参数 db
    :param provider_id: 参数 provider_id
    :return: 返回处理结果。
    """
    query = db.query(AIModelConfig)
    if provider_id:
        query = query.filter(AIModelConfig.provider_id == provider_id)
    models = query.filter(AIModelConfig.is_active.is_(True)).all()
    providers = {str(p.id): p for p in db.query(AIModelProvider).all()}
    rows: list[dict[str, Any]] = []
    for m in models:
        provider = providers.get(str(m.provider_id))
        probe = probe_single_model(
            m.model_name,
            m.model_type,
            api_key=provider.api_key if provider else None,
            base_url=provider.base_url if provider else None,
        )
        rows.append(
            {
                "id": str(m.id),
                "model_name": m.model_name,
                "model_type": m.model_type,
                "provider_name": provider.name if provider else None,
                **probe,
            }
        )

    available = sum(1 for r in rows if r.get("status") in ("available", "key_ok"))
    return {
        "total": len(rows),
        "available_count": available,
        "unavailable_count": sum(1 for r in rows if r.get("status") == "unavailable"),
        "no_key_count": sum(1 for r in rows if r.get("status") == "no_key"),
        "models": rows,
        "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
