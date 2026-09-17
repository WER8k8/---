# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""搜索引擎收录探测 — Baidu site: 查询（失败可降级 HTTP 探活）。"""

from __future__ import annotations

import logging
from typing import Any
from urllib.parse import quote, urlparse

import requests

logger = logging.getLogger("uj-admin.seo_inclusion_probe")

_BAIDU_SEARCH = "https://www.baidu.com/s"
_TIMEOUT = 12
_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)
_NOT_FOUND_MARKERS = (
    "没有找到",
    "未找到相关",
    "0个结果",
    "抱歉，没有找到",
)
_BLOCKED_MARKERS = (
    "请输入验证码",
    "百度安全验证",
    "反爬虫",
)


def _normalize_url(url: str) -> str:
    """实现 normalizeURL 的功能。
    
    :param url: 参数 url（类型: str）
    :return: 返回 str 结果
    """
    u = (url or "").strip()
    if u and not u.startswith(("http://", "https://")):
        u = f"https://{u}"
    return u


def _http_reachable(url: str) -> bool:
    """实现 HTTPreachable 的功能。
    
    :param url: 参数 url（类型: str）
    :return: 返回 bool 结果
    """
    try:
        resp = requests.head(
            url,
            timeout=_TIMEOUT,
            allow_redirects=True,
            headers={"User-Agent": _UA},
        )
        if resp.status_code >= 400:
            resp = requests.get(url, timeout=_TIMEOUT, allow_redirects=True, headers={"User-Agent": _UA})
        return resp.status_code < 400
    except Exception:
        return False


def probe_url_inclusion(url: str, *, engine: str = "baidu") -> dict[str, Any]:
    """
    探测单 URL 是否被收录。
    返回 included / probe_mode / ranking_hint / note
    """
    url = _normalize_url(url)
    if not url:
        return {"included": False, "probe_mode": "skip", "note": "empty_url"}

    parsed = urlparse(url)
    host = parsed.netloc or ""
    path = parsed.path or "/"
    if engine != "baidu":
        reachable = _http_reachable(url)
        return {
            "included": reachable,
            "probe_mode": "http_fallback",
            "search_engine": engine,
            "note": "non_baidu_http_probe",
        }

    query = f"site:{host}{path}" if path and path != "/" else f"site:{host}"
    try:
        resp = requests.get(
            _BAIDU_SEARCH,
            params={"wd": query, "rn": 10},
            timeout=_TIMEOUT,
            headers={
                "User-Agent": _UA,
                "Accept-Language": "zh-CN,zh;q=0.9",
            },
        )
        html = resp.text or ""
    except Exception as exc:
        logger.warning("baidu inclusion probe failed url=%s: %s", url, exc)
        reachable = _http_reachable(url)
        return {
            "included": reachable,
            "probe_mode": "http_fallback",
            "search_engine": "baidu",
            "note": str(exc)[:120],
        }

    if any(m in html for m in _BLOCKED_MARKERS):
        reachable = _http_reachable(url)
        return {
            "included": reachable,
            "probe_mode": "blocked_fallback_http",
            "search_engine": "baidu",
            "note": "baidu_blocked",
        }

    if any(m in html for m in _NOT_FOUND_MARKERS):
        return {
            "included": False,
            "probe_mode": "baidu_site",
            "search_engine": "baidu",
            "ranking_hint": None,
            "note": "no_results",
        }

    # URL 或域名出现在结果页视为收录
    url_tail = quote(url, safe="")
    host_in_page = host in html
    path_in_page = path.strip("/") and path.strip("/") in html
    included = host_in_page and (path == "/" or path_in_page or url in html or url_tail in html)
    rank_hint = 1 if included else None
    if included:
        # 粗估：结果区出现顺序
        idx = html.find(host)
        if idx > 0 and idx < 8000:
            rank_hint = max(1, min(10, idx // 800))

    return {
        "included": included,
        "probe_mode": "baidu_site",
        "search_engine": "baidu",
        "ranking_hint": rank_hint,
        "query": query,
        "note": "ok" if included else "host_not_in_serp",
    }
