# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""并行聚合 B2B / GEO 旁路就绪态（避免 /integrations/sidecars/status 串行超时）。

每项返回带 status_judgement 契约字段：level / label / hint。
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable


def _safe_call(fn: Callable[[], dict[str, Any]], *, label: str) -> dict[str, Any]:
    try:
        return fn()
    except Exception as exc:
        return {"configured": False, "healthy": False, "detail": str(exc)[:200], "probe": label}


def build_integrations_sidecars_status(*, timeout_sec: float = 2.5) -> dict[str, Any]:
    """旁路聚合：每项带 level/label/hint（status_judgement 契约）。"""
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
    from app.services.status_judgement import overall_from_checks, sidecar_check

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
    raw: dict[str, Any] = {}
    pool = ThreadPoolExecutor(max_workers=min(12, len(probes)))
    futures = {pool.submit(_safe_call, fn, label=key): key for key, fn in probes.items()}
    try:
        for fut in as_completed(futures, timeout=timeout_sec):
            key = futures[fut]
            try:
                raw[key] = fut.result(timeout=0.1)
            except Exception as exc:
                raw[key] = {
                    "configured": False,
                    "healthy": False,
                    "detail": str(exc)[:200],
                    "probe": key,
                }
    except TimeoutError:
        pass
    finally:
        pool.shutdown(wait=False)

    for key in probes:
        raw.setdefault(key, {"configured": False, "healthy": None, "detail": "probe_timeout", "probe": key})

    out: dict[str, Any] = {}
    checks = []
    for key, item in raw.items():
        chk = sidecar_check({**(item or {}), "probe": key, "id": key})
        merged = dict(item or {})
        merged.update(chk)
        merged["id"] = key
        out[key] = merged
        checks.append(chk)
    out["_overall"] = overall_from_checks(checks)
    out["_contract"] = "status_judgement: level/label/hint 必填"
    return out
