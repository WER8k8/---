"""并行聚合 B2B / GEO 旁路就绪态（避免 /integrations/sidecars/status 串行超时）。"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable


def _safe_call(fn: Callable[[], dict[str, Any]], *, label: str) -> dict[str, Any]:
    """实现 safecall 的功能。
    
    :param fn: 参数 fn（类型: Callable[[], dict[str, Any]]）
    :param label: 参数 label（类型: str）
    :return: 返回 dict[str, Any] 结果
    """
    try:
        return fn()
    except Exception as exc:
        return {"configured": False, "healthy": False, "detail": str(exc)[:200], "probe": label}


def build_integrations_sidecars_status(*, timeout_sec: float = 2.5) -> dict[str, Any]:
    """实现 构建integrationssidecars状态 的功能。
    
    :param timeout_sec: 参数 timeout_sec（类型: float）
    :return: 返回 dict[str, Any] 结果
    """
    from app.services.analytics.user_action_analytics_sidecar import user_action_analytics_sidecar_status
    from app.services.crawlers.ecommerce_crawlers_sidecar import ecommerce_crawlers_sidecar_status
    from app.services.crawlers.media_crawler_sidecar import media_crawler_sidecar_status
    from app.services.cross_border.libretranslate_sidecar import libretranslate_sidecar_status
    from app.services.foreign_trade.customs_data_spider_sidecar import customs_data_spider_sidecar_status
    from app.services.forum_sidecar_service import forum_sidecar_status
    from app.services.geo.headless_rank_probe_service import headless_probe_sidecar_status
    from app.services.ubrain.ai_find_customer_sidecar import ai_find_customer_sidecar_status
    from app.services.ubrain.deerflow_sidecar import deerflow_sidecar_status
    from app.services.ubrain.domain_email_extractor_sidecar import domain_email_extractor_sidecar_status
    from app.services.ubrain.imap_inquiry_sidecar import imap_inquiry_sidecar_status
    from app.services.ubrain.linkedin_decision_maker_sidecar import linkedin_decision_maker_sidecar_status
    probes: dict[str, Callable[[], dict[str, Any]]] = {
        "ai_find_customer": ai_find_customer_sidecar_status,
        "domain_email_extractor": domain_email_extractor_sidecar_status,
        "media_crawler": media_crawler_sidecar_status,
        "linkedin_decision_maker": linkedin_decision_maker_sidecar_status,
        "customs_data_spider": customs_data_spider_sidecar_status,
        "imap_inquiry": imap_inquiry_sidecar_status,
        "libretranslate": libretranslate_sidecar_status,
        "headless_probe": headless_probe_sidecar_status,
        "ecommerce_crawlers": ecommerce_crawlers_sidecar_status,
        "user_action_analytics": user_action_analytics_sidecar_status,
        "deerflow": deerflow_sidecar_status,
        "forum_answer": forum_sidecar_status,
    }
    out: dict[str, Any] = {}
    with ThreadPoolExecutor(max_workers=min(12, len(probes))) as pool:
        futures = {pool.submit(_safe_call, fn, label=key): key for key, fn in probes.items()}
        try:
            for fut in as_completed(futures, timeout=timeout_sec + 2):
                key = futures[fut]
                try:
                    out[key] = fut.result(timeout=0.1)
                except Exception as exc:
                    out[key] = {"configured": False, "healthy": False, "detail": str(exc)[:200]}
        except TimeoutError:
            pass
    for key in probes:
        out.setdefault(key, {"configured": False, "healthy": None, "detail": "probe_timeout"})
    return out
