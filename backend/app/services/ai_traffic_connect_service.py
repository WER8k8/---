"""租户 AI 通道自动对接：充值后接通所选平台 Key；无 Key 时无缝降级免费 NVIDIA。"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.ai_config import AIModelProvider
from app.models.tenant import Tenant
from app.services.ai_traffic_provider_service import (
    AI_TRAFFIC_PROVIDERS,
    get_tenant_ai_traffic_provider,
    provider_label,
    set_tenant_ai_traffic_provider,
)

SETTINGS_CONNECT_KEY = "ai_connect"

FREE_NVIDIA_ALERT_TITLE = "英伟达免费体验（哪些模型能用以实时为准）"

FREE_NVIDIA_NOTICE = (
    "英伟达（NVIDIA）目前有免费额度可供体验，但我们无法保证每一个模型都能用——"
    "哪些能用、哪些暂时不能用，以平台实时情况为准，速度也偏慢。"
    "要想获得更好的体验，请充值 AI 流量。"
)

FREE_NVIDIA_PROVIDER_HINT = (
    "英伟达现提供免费额度，但哪些模型能用随时会变、速度偏慢。"
    "要想获得更好的体验，请充值。"
)

RECHARGE_CTA_SHORT = "要想获得更好的体验，请充值 AI 流量。"

NVIDIA_USAGE_POLICY_NOTICE = (
    "【客户须知】英伟达免费通道受官方限速与用量额度约束，规则可能随时调整；"
    "高峰时段可能排队、变慢或个别模型暂时不可用。"
    "系统于每日 1:00、12:00、20:00 自动检测可用模型，仍以您实际调用时为准。"
    "要想获得更稳定、更快的服务，请充值 AI 流量。"
)

PAID_CONNECT_NOTICE = "已为您接通「{label}」AI 通道，卖货副驾与旺财插件将按该通道扣减流量。"

# provider_id（租户侧）→ settings 环境变量 / DB provider_type
_PROVIDER_ENV_KEYS: dict[str, str] = {
    "nvidia": "AI_NVIDIA_API_KEY",
    "deepseek": "AI_DEEPSEEK_API_KEY",
    "openai": "AI_OPENAI_API_KEY",
    "anthropic": "AI_ANTHROPIC_API_KEY",
    "google": "AI_GEMINI_API_KEY",
    "gemini": "AI_GEMINI_API_KEY",
    "zhipu": "AI_ZHIPU_API_KEY",
    "aliyun": "AI_ALIYUN_API_KEY",
    "byte": "AI_BYTE_API_KEY",
}


def _utcnow() -> datetime:
    """_utcnow。
    :return: 返回处理结果。
    """
    return datetime.now(timezone.utc)


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


def _write_settings(tenant: Tenant, data: dict[str, Any]) -> None:
    """_write_settings。

    参数说明：
    :param tenant: 参数 tenant
    :param data: 参数 data
    :return: 返回处理结果。
    """
    tenant.settings = json.dumps(data, ensure_ascii=False)


def platform_provider_has_key(db: Session, provider_id: str) -> bool:
    """平台是否已为该大模型配置可用 Key（DB 或环境变量）。"""
    pid = (provider_id or "").strip().lower()
    if pid not in AI_TRAFFIC_PROVIDERS:
        return False

    env_name = _PROVIDER_ENV_KEYS.get(pid)
    if env_name and bool(getattr(settings, env_name, None)):
        return True

    row = (
        db.query(AIModelProvider)
        .filter(
            AIModelProvider.provider_type == pid,
            AIModelProvider.is_active.is_(True),
        )
        .first()
    )
    if row and (row.api_key or "").strip():
        return True
    return False


def nvidia_free_available(db: Session) -> bool:
    """nvidia_free_available。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    return platform_provider_has_key(db, "nvidia")


def get_tenant_ai_connect(tenant: Tenant) -> dict[str, Any]:
    """get_tenant_ai_connect。

    参数说明：
    :param tenant: 参数 tenant
    :return: 返回处理结果。
    """
    block = _read_settings(tenant).get(SETTINGS_CONNECT_KEY)
    return block if isinstance(block, dict) else {}


def build_connect_status(db: Session, tenant: Tenant) -> dict[str, Any]:
    """供前端展示：是否已对接、是否免费档、用户提示文案。"""
    connect = get_tenant_ai_connect(tenant)
    pid = connect.get("effective_provider_id") or get_tenant_ai_traffic_provider(tenant)
    mode = connect.get("mode") or "unknown"
    free_tier = bool(connect.get("free_tier"))
    ready = bool(connect.get("hermes_ready")) and mode in ("paid", "free_nvidia")
    requested = connect.get("requested_provider_id")
    notice = connect.get("user_notice") or ""
    if not notice and free_tier:
        notice = FREE_NVIDIA_NOTICE
    if not notice and mode == "paid" and pid:
        notice = PAID_CONNECT_NOTICE.format(label=provider_label(str(pid)))

    from app.services.nvidia_customer_probe_service import build_probe_public_summary
    probe_summary = build_probe_public_summary(db)
    usage_policy = NVIDIA_USAGE_POLICY_NOTICE if free_tier else None
    return {
        "ready": ready,
        "mode": mode,
        "free_tier": free_tier,
        "alert_title": FREE_NVIDIA_ALERT_TITLE if free_tier else "AI 通道已接通",
        "effective_provider_id": pid,
        "effective_provider_label": provider_label(str(pid)) if pid else None,
        "requested_provider_id": requested,
        "requested_provider_label": provider_label(str(requested)) if requested else None,
        "fallback_from_requested": bool(requested and pid and requested != pid),
        "user_notice": notice,
        "usage_policy_notice": usage_policy,
        "recharge_cta": RECHARGE_CTA_SHORT if free_tier else None,
        "nvidia_probe": probe_summary if free_tier or nvidia_free_available(db) else None,
        "connected_at": connect.get("connected_at"),
        "nvidia_free_available": nvidia_free_available(db),
    }


def list_providers_with_connect_hints(db: Session) -> list[dict[str, Any]]:
    """list_providers_with_connect_hints。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    from app.services.ai_traffic_provider_service import list_providers_for_client
    out: list[dict[str, Any]] = []
    for item in list_providers_for_client():
        pid = item["provider_id"]
        has_key = platform_provider_has_key(db, pid)
        enriched = {
            **item,
            "platform_key_ready": has_key,
            "free_tier_fallback": pid == "nvidia" and nvidia_free_available(db),
        }
        if pid == "nvidia" and nvidia_free_available(db):
            enriched["experience_hint"] = FREE_NVIDIA_PROVIDER_HINT
        elif not has_key:
            enriched["experience_hint"] = (
                "充值后将为您自动接通；若平台暂未配置 Key，将临时使用英伟达免费通道（可用模型以实时为准）。"
            )
        else:
            enriched["experience_hint"] = "充值成功后将自动接通，无需再填 API Key。"
        out.append(enriched)
    return out


def provision_tenant_ai_connect(
    db: Session,
    tenant: Tenant,
    *,
    provider_id: str | None = None,
    trigger: str = "manual",
    user_id: str | None = None,
) -> dict[str, Any]:
    """
    写入租户 ai_connect，并确保 Hermes 默认插件包。
    - 所选平台有 Key → mode=paid
    - 否则若有 NVIDIA → mode=free_nvidia（无缝降级）
    """
    requested = (provider_id or get_tenant_ai_traffic_provider(tenant) or "nvidia").strip().lower()
    if requested not in AI_TRAFFIC_PROVIDERS:
        requested = "nvidia"

    effective = requested
    mode = "unavailable"
    free_tier = False
    user_notice = ""
    if platform_provider_has_key(db, requested):
        mode = "paid"
        free_tier = False
        user_notice = PAID_CONNECT_NOTICE.format(label=provider_label(requested))
    elif nvidia_free_available(db):
        mode = "free_nvidia"
        effective = "nvidia"
        free_tier = True
        if requested != "nvidia":
            user_notice = (
                f"您选择了「{provider_label(requested)}」，平台侧该通道尚未就绪，"
                f"已临时为您接通英伟达免费通道。{FREE_NVIDIA_NOTICE}"
            )
        else:
            user_notice = FREE_NVIDIA_NOTICE
    else:
        user_notice = "平台 AI 通道暂不可用，请联系客服或稍后再试。"

    try:
        set_tenant_ai_traffic_provider(db, tenant, effective)
    except ValueError:
        pass

    cfg = _read_settings(tenant)
    cfg[SETTINGS_CONNECT_KEY] = {
        "mode": mode,
        "free_tier": free_tier,
        "requested_provider_id": requested,
        "effective_provider_id": effective,
        "hermes_ready": mode in ("paid", "free_nvidia"),
        "user_notice": user_notice,
        "connected_at": _utcnow().isoformat(),
        "trigger": trigger,
    }
    _write_settings(tenant, cfg)
    db.add(tenant)
    hermes_plugins = 0
    if mode in ("paid", "free_nvidia"):
        from app.services.hermes.install_service import ensure_default_plugins
        hermes_plugins = ensure_default_plugins(db, str(tenant.id), user_id=user_id)

    db.commit()
    db.refresh(tenant)
    status = build_connect_status(db, tenant)
    return {
        "ok": mode in ("paid", "free_nvidia"),
        "mode": mode,
        "hermes_plugins_seeded": hermes_plugins,
        **status,
    }


def ensure_tenant_ai_connectivity(db: Session, tenant_id: str) -> dict[str, Any]:
    """Hermes / 副驾调用前：无对接记录则自动挂免费 NVIDIA，避免断档。"""
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        return {"ok": False, "reason": "tenant_not_found"}

    connect = get_tenant_ai_connect(tenant)
    if connect.get("hermes_ready") and connect.get("mode") in ("paid", "free_nvidia"):
        return {"ok": True, "skipped": True, **build_connect_status(db, tenant)}

    return provision_tenant_ai_connect(
        db,
        tenant,
        provider_id=get_tenant_ai_traffic_provider(tenant),
        trigger="ensure_connectivity",
    )
