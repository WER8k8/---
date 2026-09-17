# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""SEO-11：矩阵发布 URL 追加 UTM 便于 PostHog/流量归因。"""

from __future__ import annotations

from urllib.parse import parse_qs, urlencode, urlparse, urlunparse


def append_publish_utm(
    url: str,
    *,
    platform_code: str | None = None,
    task_id: str | None = None,
    tenant_id: str | None = None,
) -> str:
    """实现 追加发布utm 的功能。
    
    :param url: 参数 url（类型: str）
    :param platform_code: 参数 platform_code（类型: str | None）
    :param task_id: 参数 task_id（类型: str | None）
    :param tenant_id: 参数 tenant_id（类型: str | None）
    :return: 返回 str 结果
    """
    raw = (url or "").strip()
    if not raw or not raw.startswith(("http://", "https://")):
        return raw
    parsed = urlparse(raw)
    qs = parse_qs(parsed.query, keep_blank_values=True)
    if "utm_source" not in qs:
        qs["utm_source"] = [platform_code or "seo_matrix"]
    if "utm_medium" not in qs:
        qs["utm_medium"] = ["publish"]
    if task_id and "utm_campaign" not in qs:
        qs["utm_campaign"] = [str(task_id)[:36]]
    if tenant_id and "utm_content" not in qs:
        qs["utm_content"] = [str(tenant_id)[:36]]
    flat = {k: v[0] if v else "" for k, v in qs.items()}
    return urlunparse(parsed._replace(query=urlencode(flat)))
