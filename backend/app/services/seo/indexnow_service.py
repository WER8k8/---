# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""IndexNow 开放极速收录协议服务。

支持向微软 Bing、Yandex 及各主流搜索引擎联盟实时推送新增/变更 URL，
打破传统蜘蛛轮巡等待周期，实现发布后 24 小时内闪电抓取。
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

INDEXNOW_ENDPOINT = "https://api.indexnow.org/indexnow"
DEFAULT_INDEXNOW_KEY = os.getenv("INDEXNOW_KEY", "youding888999indexnowkey2026")


class IndexNowService:
    """IndexNow 广播服务。"""

    def __init__(self, key: str = DEFAULT_INDEXNOW_KEY):
        self.key = key

    def get_key_filename(self) -> str:
        return f"{self.key}.txt"

    async def submit_urls(self, host: str, urls: List[str], key_location: str = "") -> Dict[str, Any]:
        """向 IndexNow 官方 API 提交 URL 列表。"""
        if not urls:
            return {"status": "skipped", "message": "No URLs provided"}

        clean_host = host.replace("http://", "").replace("https://", "").split("/")[0]

        payload = {
            "host": clean_host,
            "key": self.key,
            "keyLocation": key_location or f"https://{clean_host}/indexnow-key.txt",
            "urlList": urls,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(
                    INDEXNOW_ENDPOINT,
                    json=payload,
                    headers={"Content-Type": "application/json; charset=utf-8"},
                )
                # IndexNow: 200/202 = Success
                is_success = res.status_code in (200, 202)
                return {
                    "status": "success" if is_success else "failed",
                    "http_code": res.status_code,
                    "submitted_count": len(urls),
                    "host": clean_host,
                    "urls": urls,
                    "message": "URLs successfully broadcast to search engines" if is_success else res.text,
                }
        except Exception as exc:
            logger.warning("IndexNow submit failed (offline fallback): %s", exc)
            return {
                "status": "offline_queued",
                "submitted_count": len(urls),
                "host": clean_host,
                "urls": urls,
                "error": str(exc),
                "message": "IndexNow network request queued/degraded",
            }
