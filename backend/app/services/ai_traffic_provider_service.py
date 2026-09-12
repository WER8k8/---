"""客户自选 AI 大模型平台（AI 流量充值与租户偏好）。"""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from app.models.tenant import Tenant

SETTINGS_KEY = "ai_traffic_provider"

# 客户可见平台（与超管 provider-setup 口径对齐，id 用于下单与场景配置）
AI_TRAFFIC_PROVIDERS: dict[str, dict[str, str]] = {
    "deepseek": {
        "label": "DeepSeek",
        "tagline": "性价比高，适合日常文案与对话",
    },
    "nvidia": {
        "label": "NVIDIA NIM",
        "tagline": "多模型聚合，适合视频与复杂任务",
    },
    "openai": {
        "label": "OpenAI",
        "tagline": "GPT 系列，综合能力强",
    },
    "anthropic": {
        "label": "Claude",
        "tagline": "长文与推理表现好",
    },
    "google": {
        "label": "Google Gemini",
        "tagline": "多模态与海外业务",
    },
    "zhipu": {
        "label": "智谱 GLM",
        "tagline": "国内合规，中文友好",
    },
    "aliyun": {
        "label": "通义千问",
        "tagline": "阿里云生态",
    },
    "byte": {
        "label": "字节豆包",
        "tagline": "短视频与营销文案",
    },
}


def list_providers_for_client() -> list[dict[str, Any]]:
    """list_providers_for_client。
    :return: 返回处理结果。
    """
    return [
        {
            "provider_id": pid,
            "label": spec["label"],
            "tagline": spec["tagline"],
        }
        for pid, spec in AI_TRAFFIC_PROVIDERS.items()
    ]


def resolve_provider_id(provider_id: str | None) -> str:
    """resolve_provider_id。

    参数说明：
    :param provider_id: 参数 provider_id
    :return: 返回处理结果。
    """
    pid = (provider_id or "").strip().lower()
    if pid not in AI_TRAFFIC_PROVIDERS:
        raise ValueError(f"不支持的大模型平台: {provider_id}")
    return pid


def provider_label(provider_id: str) -> str:
    """provider_label。

    参数说明：
    :param provider_id: 参数 provider_id
    :return: 返回处理结果。
    """
    return AI_TRAFFIC_PROVIDERS.get(provider_id, {}).get("label", provider_id)


def _read_settings(tenant: Tenant) -> dict[str, Any]:
    """_read_settings。

    参数说明：
    :param tenant: 参数 tenant
    :return: 返回处理结果。
    """
    raw = tenant.settings or "{}"
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}


def get_tenant_ai_traffic_provider(tenant: Tenant) -> str | None:
    """get_tenant_ai_traffic_provider。

    参数说明：
    :param tenant: 参数 tenant
    :return: 返回处理结果。
    """
    pid = (_read_settings(tenant).get(SETTINGS_KEY) or "").strip().lower()
    if pid in AI_TRAFFIC_PROVIDERS:
        return pid
    return None


def set_tenant_ai_traffic_provider(db: Session, tenant: Tenant, provider_id: str) -> str:
    """set_tenant_ai_traffic_provider。

    参数说明：
    :param db: 参数 db
    :param tenant: 参数 tenant
    :param provider_id: 参数 provider_id
    :return: 返回处理结果。
    """
    pid = resolve_provider_id(provider_id)
    cfg = _read_settings(tenant)
    cfg[SETTINGS_KEY] = pid
    tenant.settings = json.dumps(cfg, ensure_ascii=False)
    db.add(tenant)
    return pid
