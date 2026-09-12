"""NVIDIA 场景模型健康探测（chat / Cosmos infer）。"""

from __future__ import annotations

import logging
import time
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.services.ai_invocation_service import get_scenario_runtime
from app.services.cosmos_infer_service import infer_base_url, infer_endpoint_url
from app.services.nvidia_scenario_service import PRODUCT_SCENARIOS

logger = logging.getLogger(__name__)

VIDEO_SCENARIOS = frozenset(
    {
        "text_to_video",
        "image_to_video",
        "video_transfer",
        "article_to_video_render",
    }
)


def _api_key() -> str:
    """_api_key。
    :return: 返回处理结果。
    """
    return (settings.AI_NVIDIA_API_KEY or "").strip()


def _chat_base_url() -> str:
    """_chat_base_url。
    :return: 返回处理结果。
    """
    return (settings.AI_NVIDIA_BASE_URL or "https://integrate.api.nvidia.com/v1").rstrip("/")


def probe_chat_model(
    model: str,
    *,
    timeout: float | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
) -> dict[str, Any]:
    """探测 chat/completions 模型可用性。"""
    key = (api_key or _api_key()).strip()
    if not key:
        return {
            "healthy": False,
            "latency_ms": 0,
            "model": model,
            "error": "未配置 API Key",
        }

    probe_timeout = timeout
    if probe_timeout is None:
        probe_timeout = float(getattr(settings, "AI_SCENARIO_HEALTH_CHAT_TIMEOUT", 45.0) or 45.0)

    chat_base = (base_url or _chat_base_url()).rstrip("/")
    url = f"{chat_base}/chat/completions"
    started = time.perf_counter()
    try:
        with httpx.Client(timeout=probe_timeout) as client:
            resp = client.post(
                url,
                headers={
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": "ping"}],
                    "max_tokens": 8,
                    "temperature": 0.1,
                },
            )
        latency_ms = int((time.perf_counter() - started) * 1000)
        if resp.status_code >= 400:
            return {
                "healthy": False,
                "latency_ms": latency_ms,
                "model": model,
                "status_code": resp.status_code,
                "error": resp.text[:240],
            }
        return {"healthy": True, "latency_ms": latency_ms, "model": model}
    except Exception as exc:
        latency_ms = int((time.perf_counter() - started) * 1000)
        return {
            "healthy": False,
            "latency_ms": latency_ms,
            "model": model,
            "error": str(exc),
        }


def probe_cosmos_scenario(model: str) -> dict[str, Any]:
    """探测 Cosmos 视频场景（自托管 NIM 或 mock）。"""
    if settings.MEDIA_FACTORY_MOCK_RENDER:
        return {
            "healthy": True,
            "latency_ms": 0,
            "model": model,
            "mode": "mock",
            "note": "MEDIA_FACTORY_MOCK_RENDER=true，跳过真实 infer",
        }

    base = infer_base_url()
    endpoint = infer_endpoint_url()
    if not base or not endpoint:
        return {
            "healthy": False,
            "latency_ms": 0,
            "model": model,
            "mode": "cosmos",
            "error": "未配置 AI_NVIDIA_COSMOS_BASE_URL（自托管 Cosmos NIM /v1/infer）",
        }

    started = time.perf_counter()
    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(
                f"{base.rstrip('/')}/v1/health/ready",
                headers={"Authorization": f"Bearer {_api_key()}"} if _api_key() else {},
            )
        latency_ms = int((time.perf_counter() - started) * 1000)
        if resp.status_code >= 400:
            return {
                "healthy": False,
                "latency_ms": latency_ms,
                "model": model,
                "mode": "cosmos",
                "endpoint": endpoint,
                "status_code": resp.status_code,
                "error": resp.text[:200] or "health/ready 不可用",
            }
        return {
            "healthy": True,
            "latency_ms": latency_ms,
            "model": model,
            "mode": "cosmos",
            "endpoint": endpoint,
        }
    except Exception as exc:
        latency_ms = int((time.perf_counter() - started) * 1000)
        return {
            "healthy": False,
            "latency_ms": latency_ms,
            "model": model,
            "mode": "cosmos",
            "endpoint": endpoint,
            "error": str(exc),
        }


def probe_scenario_health(db: Session | None, scenario_id: str) -> dict[str, Any]:
    """probe_scenario_health。

    参数说明：
    :param db: 参数 db
    :param scenario_id: 参数 scenario_id
    :return: 返回处理结果。
    """
    runtime = get_scenario_runtime(db, scenario_id)
    model = runtime["model_name"]
    label = next(
        (sc["label"] for sc in PRODUCT_SCENARIOS if sc["id"] == scenario_id),
        scenario_id,
    )
    if scenario_id in VIDEO_SCENARIOS or (
        model.startswith("nvidia/cosmos-") and "/v1/infer" not in model
    ):
        probe = probe_cosmos_scenario(model)
    else:
        probe = probe_chat_model(model)

    return {
        "scenario": scenario_id,
        "label": label,
        "model": model,
        **probe,
    }


def probe_all_scenario_health(db: Session | None) -> dict[str, Any]:
    """probe_all_scenario_health。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    rows = [probe_scenario_health(db, sc["id"]) for sc in PRODUCT_SCENARIOS]
    healthy_count = sum(1 for r in rows if r.get("healthy"))
    return {
        "total": len(rows),
        "healthy_count": healthy_count,
        "unhealthy_count": len(rows) - healthy_count,
        "scenarios": rows,
        "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
