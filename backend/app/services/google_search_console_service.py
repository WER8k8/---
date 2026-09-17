# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""谷歌 Search Console 回收闭环 — 生成式引擎（AI Overviews / Discovery）真值回收。

对应缺口 #7：谷歌侧收录与曝光真值。BaiduWebmasterService 已有百度闭环，
本模块补齐谷歌侧：
- GSC API 拉取 Performance（按 query/page，含 AI Overviews 曝光维度）
- Discovery 曝光面板
- 无凭证时走 no_fake_delivery mock 门控（生产禁止假成功），
  与 baidu_webmaster_service 口径一致。

只读回收，不改业务数据；可离线单测（不真连网）。
"""

from __future__ import annotations

import json
import os
import time
import urllib.parse
from typing import Any, Optional

import httpx

from app.core.no_fake_delivery import mock_allowed, stamp_mock

# GSC API 端点（Search Console API v1）
_GSC_PERFORMANCE = "https://searchconsole.googleapis.com/v1/{path}:searchAnalytics/query"
_GSC_API_KEY_ENV = "GSC_API_KEY"
_GSC_SERVICE_ACCOUNT_ENV = "GSC_SERVICE_ACCOUNT_JSON"
_GSC_TOKEN_URL = "https://oauth2.googleapis.com/token"
_GSC_SCOPE = "https://www.googleapis.com/auth/searchconsole.readonly"

# 进程内 access_token 缓存：{client_email: (token, 过期时间戳)}
_TOKEN_CACHE: dict[str, tuple[str, float]] = {}


def _service_account() -> Optional[dict[str, Any]]:
    """读取 GSC 服务账号 JSON（支持内联 JSON 或文件路径）。解析失败返回 None。"""
    raw = os.getenv(_GSC_SERVICE_ACCOUNT_ENV, "").strip()
    if not raw:
        return None
    text = raw
    if not raw.startswith("{"):
        # 约定：值不是 JSON 时按文件路径处理（密钥文件不进仓库，只留在机器上）
        try:
            with open(raw, "r", encoding="utf-8") as fh:
                text = fh.read()
        except OSError:
            return None
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None
    if not (data.get("client_email") and data.get("private_key")):
        return None
    return data


def _access_token(service_account: dict[str, Any]) -> tuple[Optional[str], Optional[str]]:
    """用服务账号签 RS256 assertion 换 access_token。返回 (token, 错误说明)。

    venv 无 google-auth，故按 OAuth2 断言流程手签：这里只做本地签名 + 一次换票请求，
    不打印也不回传任何密钥内容。
    """
    client_email = str(service_account["client_email"])
    now = int(time.time())
    cached = _TOKEN_CACHE.get(client_email)
    if cached and cached[1] > now + 60:
        return cached[0], None

    try:
        import jwt  # PyJWT，venv 已具备
    except ImportError:
        return None, "缺少 PyJWT，无法为服务账号签发 OAuth 断言"

    assertion = jwt.encode(
        {
            "iss": client_email,
            "scope": _GSC_SCOPE,
            "aud": _GSC_TOKEN_URL,
            "iat": now,
            "exp": now + 3600,
        },
        service_account["private_key"],
        algorithm="RS256",
    )
    if isinstance(assertion, bytes):  # PyJWT <2.0 返回 bytes
        assertion = assertion.decode("ascii")

    try:
        resp = httpx.post(
            _GSC_TOKEN_URL,
            data={
                "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                "assertion": assertion,
            },
            timeout=20,
        )
        resp.raise_for_status()
        payload = resp.json()
    except (httpx.HTTPError, ValueError) as exc:
        # 只回错误类型与摘要，绝不回传断言或私钥
        return None, f"服务账号换票失败：{type(exc).__name__}"

    token = str(payload.get("access_token") or "").strip()
    if not token:
        return None, "服务账号换票响应里没有 access_token"
    expires_in = int(payload.get("expires_in") or 3600)
    _TOKEN_CACHE[client_email] = (token, now + expires_in)
    return token, None


class GSCService:
    """谷歌 Search Console：Performance / Discovery 真值回收。"""

    @staticmethod
    def _no_credential_response(*, mock_payload: dict[str, Any]) -> dict[str, Any]:
        if not mock_allowed("GSC_ALLOW_MOCK"):
            return {
                "success": False,
                "message": "GSC 凭证未配置",
                "data": None,
                "error_code": "GSC_NOT_CONFIGURED",
            }
        return {
            "success": True,
            "message": "[dev mock] 需配置 GSC API Key / Service Account 后对接真实 API",
            "data": stamp_mock(dict(mock_payload), reason="gsc_credential_missing"),
        }

    @staticmethod
    def _api_key() -> Optional[str]:
        return os.getenv(_GSC_API_KEY_ENV, "").strip() or None

    @staticmethod
    def configured() -> bool:
        """是否具备真连 GSC 的凭证（API Key 或 Service Account）。"""
        return bool(GSCService._api_key() or os.getenv(_GSC_SERVICE_ACCOUNT_ENV, "").strip())

    @staticmethod
    def _normalize_site(site_url: str) -> str:
        """GSC 的 siteUrl 必须是资源里登记的完整 URL（含 scheme），不能剥掉 https://。"""
        site = str(site_url or "").strip()
        if not site:
            return site
        if "://" not in site:
            site = f"https://{site}"
        return site.rstrip("/")

    @staticmethod
    async def get_performance(
        site_url: str,
        days: int = 28,
        dimensions: Optional[list[str]] = None,
        api_key: Optional[str] = None,
        keyword: Optional[str] = None,
    ) -> dict[str, Any]:
        """回收 Performance 真值（含 AI Overviews / Discovery 曝光维度）。

        无凭证时仅开发环境显式 mock；生产返回 GSC_NOT_CONFIGURED（不假成功）。
        返回 data 里 ai_overviews_impressions / discovery_impressions 为真值，
        供 geo 侧 headless_rank_probe 判断生成式引擎命中率。
        """
        key = api_key or GSCService._api_key()
        sa = _service_account()
        headers: dict[str, str] = {}
        params: dict[str, str] = {}

        if sa:
            token, token_error = _access_token(sa)
            if not token:
                # 有服务账号但换票失败 → 如实失败，不退化成 mock 成功
                return {
                    "success": False,
                    "message": f"GSC 服务账号鉴权失败：{token_error or '未知原因'}",
                    "data": None,
                    "error_code": "GSC_AUTH_FAILED",
                }
            headers["Authorization"] = f"Bearer {token}"
        elif key:
            # 纯 API Key 只能用于部分公开接口，Search Console 数据接口要 OAuth；
            # 这里带着 key 请求，失败由下方 HTTPError 分支如实回报，不假装成功。
            params["key"] = key
        else:
            return GSCService._no_credential_response(
                mock_payload={
                    "site": site_url,
                    "days": days,
                    "rows": [],
                    "total_clicks": 0,
                    "total_impressions": 0,
                    "ai_overviews_impressions": 0,
                    "discovery_impressions": 0,
                }
            )

        dims = dimensions or ["query", "page"]
        site = GSCService._normalize_site(site_url)
        path = urllib.parse.quote(site, safe="")
        payload = {
            "dateRanges": [{"startDate": _days_ago(days), "endDate": _today()}],
            "dimensions": dims,
            "aggregations": ["clicks", "impressions", "position", "ctr"],
            "rowLimit": 1000,
        }
        url = _GSC_PERFORMANCE.format(path=path)
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                resp = await client.post(url, json=payload, params=params, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                # GSC 返回 dataRows；AI Overviews / Discovery 曝光为独立维度，
                # 未提供专用 key 时如实置 0（不猜、不编造真值）
                rows = _rows(data)
                kw_hits = _keyword_hits(rows, keyword)
                return {
                    "success": True,
                    "data": {
                        "site": site,
                        "days": days,
                        "rows": rows,
                        "total_clicks": _sum_rows(data, "clicks"),
                        "total_impressions": _sum_rows(data, "impressions"),
                        "ai_overviews_impressions": _dimension_impressions(data, "ai_overviews_impressions"),
                        "discovery_impressions": _dimension_impressions(data, "discovery_impressions"),
                        "keyword_hits": kw_hits,
                        "keyword_present": bool((keyword or "").strip()),
                    },
                }
            except httpx.HTTPError as exc:
                # 纯 API Key 打数据接口的典型失败，给出可执行指引而不是干巴巴一句失败
                message = f"GSC API 请求失败: {exc}"
                if params and not headers:
                    message += (
                        "；GSC 数据接口需 OAuth（服务账号），"
                        "请在 GCP 启用 Search Console API 并配 GSC_SERVICE_ACCOUNT_JSON"
                    )
                return {"success": False, "message": message, "data": None}


def _days_ago(n: int) -> str:
    from datetime import datetime, timedelta, timezone

    return (datetime.now(timezone.utc) - timedelta(days=n)).strftime("%Y-%m-%d")


def _today() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _rows(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Search Console 响应行在顶层 rows（旧代码读 data.data.rows 恒为空）。"""
    rows = (data or {}).get("rows")
    if isinstance(rows, list):
        return rows
    nested = (data or {}).get("data")
    if isinstance(nested, dict) and isinstance(nested.get("rows"), list):
        return nested["rows"]
    return []


def _sum_rows(data: dict, metric: str) -> int:
    """按指标名累加真值。GSC 真值 shape 是行级字段（row["clicks"]），

    旧实现只读 keys 字典，导致永远累加为 0；这里两种 shape 都兼容，
    定位不到时保守返回 0，不把维度值冒充成指标。
    """
    total = 0
    for row in _rows(data):
        if not isinstance(row, dict):
            continue
        value = row.get(metric)
        if value is None:
            keys = row.get("keys")
            if isinstance(keys, dict):
                value = keys.get(metric)
        try:
            total += int(float(value or 0))
        except (TypeError, ValueError):
            continue
    return total


def _dimension_impressions(data: dict, dim: str) -> int:
    """AI Overviews / Discovery 曝光真值。

    GSC 未开放该专用维度时返回 0（如实标记未回收，不编造）。
    有对应 key 才累加，避免把普通 impression 冒充成生成式引擎曝光。
    """
    return _sum_rows(data, dim)


def _keyword_hits(rows: list, keyword: Optional[str]) -> int:
    """关键词命中真值：仅统计 query 维度且包含目标关键词的行数；keyword 为空返回 0（不编造）。"""
    if not (keyword or "").strip():
        return 0
    target = keyword.strip().lower()
    hits = 0
    for row in rows or []:
        keys = row.get("keys")
        if isinstance(keys, dict):
            q = str(keys.get("query") or "").lower()
        elif isinstance(keys, list):
            # 真值 shape：keys 与请求的 dimensions 顺序对齐，query 在首位
            q = next((str(v).lower() for v in keys if isinstance(v, str)), "")
        else:
            continue
        if q and target in q:
            hits += 1
    return hits


__all__ = ["GSCService"]
