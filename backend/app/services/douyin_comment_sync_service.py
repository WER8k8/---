# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""抖音评论采集 Worker — 批量入库（文件/HTTP 批处理，禁止假评论）。"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Optional

import httpx
from sqlalchemy.orm import Session

from app.services import social_interaction_service as social_svc
logger = logging.getLogger(__name__)

REQUIRED_FIELDS = ("tenant_id", "platform_post_id", "platform_comment_id", "content")


def normalize_batch_item(raw: dict[str, Any]) -> dict[str, Any]:
    """normalize_batch_item。

    参数说明：
    :param raw: 参数 raw
    :return: 返回处理结果。
    """
    missing = [k for k in REQUIRED_FIELDS if not str(raw.get(k) or "").strip()]
    if missing:
        raise ValueError(f"missing_fields:{','.join(missing)}")
    return {
        "tenant_id": str(raw["tenant_id"]).strip(),
        "platform_post_id": str(raw["platform_post_id"]).strip(),
        "platform_comment_id": str(raw["platform_comment_id"]).strip(),
        "content": str(raw["content"]).strip(),
        "author_name": str(raw.get("author_name") or "抖音用户").strip()[:120],
        "author_platform_id": (str(raw["author_platform_id"]).strip() if raw.get("author_platform_id") else None),
        "interaction_type": str(raw.get("interaction_type") or "comment"),
        "phone": (str(raw["phone"]).strip() if raw.get("phone") else None),
    }


def load_batch_file(path: str | Path) -> list[dict[str, Any]]:
    """load_batch_file。

    参数说明：
    :param path: 参数 path
    :return: 返回处理结果。
    """
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"batch_file_not_found:{p}")
    text = p.read_text(encoding="utf-8").strip()
    if not text:
        return []
    if text.startswith("["):
        data = json.loads(text)
    else:
        data = [json.loads(line) for line in text.splitlines() if line.strip()]
    if not isinstance(data, list):
        raise ValueError("batch_must_be_array")
    return [normalize_batch_item(item) for item in data if isinstance(item, dict)]


def ingest_batch_internal(db: Session, items: list[dict[str, Any]]) -> dict[str, Any]:
    """进程内直接入库（ops 任务 / 单测）。"""
    created = 0
    failed = 0
    results: list[dict[str, Any]] = []
    for item in items:
        try:
            row = social_svc.ingest_douyin_interaction(db, **item)
            if row.get("status") == "skipped":
                results.append({"comment_id": item["platform_comment_id"], "status": "skipped"})
                continue
            results.append({"comment_id": item["platform_comment_id"], "id": row["id"], "status": row["status"]})
            created += 1
        except Exception as exc:
            failed += 1
            results.append({"comment_id": item.get("platform_comment_id"), "error": str(exc)})
            logger.warning("douyin ingest failed: %s", exc)

    return {
        "mode": "internal",
        "total": len(items),
        "ingested": created,
        "failed": failed,
        "results": results[:20],
    }


def push_batch_via_webhook(
    items: list[dict[str, Any]],
    *,
    api_base: str,
    secret: Optional[str] = None,
) -> dict[str, Any]:
    """独立 Worker 进程：HTTP POST 到 FastAPI Webhook。"""
    base = api_base.rstrip("/")
    url = f"{base}/api/v1/social-interactions/webhook/douyin"
    headers = {"Content-Type": "application/json"}
    sec = (secret or os.getenv("SOCIAL_INTERACTION_WEBHOOK_SECRET") or os.getenv("INQUIRY_WEBHOOK_SECRET") or "").strip()
    if sec:
        headers["X-Social-Webhook-Secret"] = sec

    ok = 0
    failed = 0
    results: list[dict[str, Any]] = []
    with httpx.Client(timeout=30.0) as client:
        for item in items:
            try:
                resp = client.post(url, json=item, headers=headers)
                data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
                if resp.status_code < 400 and (not isinstance(data, dict) or data.get("code", 0) == 0):
                    ok += 1
                    results.append({"comment_id": item["platform_comment_id"], "ok": True})
                else:
                    failed += 1
                    results.append({
                        "comment_id": item["platform_comment_id"],
                        "ok": False,
                        "status": resp.status_code,
                        "body": str(data)[:200],
                    })
            except Exception as exc:
                failed += 1
                results.append({"comment_id": item.get("platform_comment_id"), "error": str(exc)})

    return {
        "mode": "webhook_http",
        "total": len(items),
        "ok": ok,
        "failed": failed,
        "webhook_url": url,
        "results": results[:20],
    }
