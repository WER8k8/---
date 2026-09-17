# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""ITER-03b · 抖音评论真实拉取 — AiToEarn / SAU 导出 / Inbox 文件（禁止造评论）。"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Optional

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.no_fake_delivery import is_production_environment
from app.models.tenant import Tenant
from app.services.aitoearn_publish_adapter import aitoearn_enabled
from app.services.douyin_comment_sync_service import ingest_batch_internal, normalize_batch_item
from app.services.onboarding_progress_service import mark_sales_channel_flag
from app.services.tenant_aitoearn_slot_service import get_tenant_aitoearn_account_ids

logger = logging.getLogger(__name__)

_BACKEND_ROOT = Path(__file__).resolve().parents[2]
_DEV_INBOX_DIR = _BACKEND_ROOT / "fixtures" / "dev" / "douyin_comment_inbox"


def _map_raw_comment(raw: dict[str, Any], tenant_id: str) -> dict[str, Any]:
    """多源字段归一化为 webhook 批处理格式。"""
    comment_id = (
        raw.get("platform_comment_id")
        or raw.get("commentId")
        or raw.get("comment_id")
        or raw.get("cid")
        or raw.get("id")
    )
    post_id = (
        raw.get("platform_post_id")
        or raw.get("awemeId")
        or raw.get("aweme_id")
        or raw.get("postId")
        or raw.get("videoId")
        or raw.get("item_id")
    )
    content = (
        raw.get("content")
        or raw.get("text")
        or raw.get("comment")
        or raw.get("message")
        or ""
    )
    if not comment_id or not post_id or not str(content).strip():
        raise ValueError("incomplete_comment_record")
    return normalize_batch_item(
        {
            "tenant_id": tenant_id,
            "platform_post_id": str(post_id),
            "platform_comment_id": str(comment_id),
            "content": str(content).strip(),
            "author_name": raw.get("author_name") or raw.get("nickname") or raw.get("userName") or "抖音用户",
            "author_platform_id": raw.get("author_platform_id") or raw.get("uid") or raw.get("userId"),
            "phone": raw.get("phone"),
        }
    )


def _aitoearn_comment_path() -> str:
    """_aitoearn_comment_path。
    :return: 返回处理结果。
    """
    return (os.getenv("AITOEARN_COMMENT_LIST_PATH") or "/plugin/comment/list").strip()


async def fetch_comments_from_aitoearn(
    db: Session,
    tenant_id: str,
    *,
    account_ids: Optional[list[str]] = None,
    limit: int = 50,
) -> dict[str, Any]:
    """从 AiToEarn 拉取抖音评论（须配置 AITOEARN_API_KEY + 租户槽位）。"""
    if not aitoearn_enabled():
        return {"source": "aitoearn", "ok": False, "reason": "aitoearn_not_configured", "items": []}

    aids = account_ids or get_tenant_aitoearn_account_ids(
        db.query(Tenant).filter(Tenant.id == tenant_id).first()
    )
    if not aids:
        return {"source": "aitoearn", "ok": False, "reason": "tenant_aitoearn_slot_empty", "items": []}

    base = (settings.AITOEARN_API_BASE or "https://mcp.aitoearn.cn").rstrip("/")
    url = f"{base}{_aitoearn_comment_path()}"
    headers = {"sk-key": settings.AITOEARN_API_KEY or "", "Content-Type": "application/json"}
    collected: list[dict[str, Any]] = []
    errors: list[str] = []
    async with httpx.AsyncClient(timeout=45.0) as client:
        for account_id in aids:
            try:
                resp = await client.get(
                    url,
                    headers=headers,
                    params={"accountId": account_id, "platform": "douyin", "limit": limit},
                )
                if resp.status_code == 404:
                    errors.append(f"endpoint_not_found:{account_id}")
                    continue
                resp.raise_for_status()
                body = resp.json()
                if isinstance(body, dict) and body.get("code"):
                    errors.append(str(body.get("message") or body.get("code")))
                    continue
                rows = body.get("data") if isinstance(body, dict) else body
                if not isinstance(rows, list):
                    errors.append(f"unexpected_payload:{account_id}")
                    continue
                for row in rows:
                    if not isinstance(row, dict):
                        continue
                    try:
                        collected.append(_map_raw_comment(row, tenant_id))
                    except ValueError:
                        continue
            except Exception as exc:
                errors.append(f"{account_id}:{exc}")
                logger.warning("aitoearn comment pull failed account=%s %s", account_id, exc)

    return {
        "source": "aitoearn",
        "ok": len(collected) > 0,
        "reason": None if collected else (errors[0] if errors else "no_comments"),
        "items": collected,
        "errors": errors[:5],
    }


def load_comments_from_inbox(tenant_id: str) -> dict[str, Any]:
    """从运维 Inbox 目录读取已导出评论（SAU/人工导出 JSON/JSONL）。"""
    sau_home = (os.getenv("SAU_HOME") or settings.SAU_HOME or "").strip()
    inbox = (os.getenv("DOUYIN_COMMENT_INBOX_DIR") or "").strip()
    candidates: list[Path] = []
    if inbox:
        inbox_path = Path(inbox)
        if inbox_path.is_file():
            candidates.append(inbox_path)
        elif inbox_path.is_dir():
            candidates.extend(
                [
                    inbox_path / f"{tenant_id}.json",
                    inbox_path / f"{tenant_id}.jsonl",
                    inbox_path / "douyin_comments.json",
                ]
            )
    if sau_home:
        root = Path(sau_home)
        candidates.extend(
            [
                root / "comments" / f"{tenant_id}.json",
                root / "comments" / f"{tenant_id}.jsonl",
                root / "douyin_comments" / f"{tenant_id}.json",
            ]
        )
    if not is_production_environment() and _DEV_INBOX_DIR.is_dir():
        candidates.extend(
            [
                _DEV_INBOX_DIR / f"{tenant_id}.json",
                _DEV_INBOX_DIR / "douyin_comments.json",
            ]
        )

    items: list[dict[str, Any]] = []
    used_files: list[str] = []
    for path in candidates:
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8").strip()
            if not text:
                continue
            rows = json.loads(text) if text.startswith("[") else [json.loads(line) for line in text.splitlines() if line.strip()]
            if not isinstance(rows, list):
                continue
            for row in rows:
                if not isinstance(row, dict):
                    continue
                row_tid = str(row.get("tenant_id") or "*")
                if row_tid not in ("*", tenant_id):
                    continue
                try:
                    items.append(_map_raw_comment(row, tenant_id))
                except ValueError:
                    continue
            used_files.append(str(path))
        except Exception as exc:
            logger.warning("inbox comment file %s: %s", path, exc)

    return {
        "source": "inbox",
        "ok": len(items) > 0,
        "reason": None if items else "inbox_empty_or_missing",
        "items": items,
        "files": used_files,
    }


def build_dev_rehearsal_comments(tenant_id: str) -> list[dict[str, Any]]:
    """开发彩排：无 AiToEarn/Inbox 时生成 1 条可入库测试评论（生产禁用）。"""
    if is_production_environment():
        return []
    if os.getenv("DOUYIN_PULL_DEV_REHEARSAL", "1").strip().lower() in ("0", "false", "no"):
        return []
    import time
    ts = int(time.time())
    return [
        normalize_batch_item(
            {
                "tenant_id": tenant_id,
                "platform_post_id": "dev-rehearsal-post",
                "platform_comment_id": f"dev-rehearsal-{ts}",
                "content": "【开发彩排】岩棉板出口报价多少？",
                "author_name": "开发彩排用户",
                "phone": "13800138000",
            }
        )
    ]


async def pull_and_ingest_for_tenant(
    db: Session,
    tenant_id: str,
    *,
    source: str = "auto",
) -> dict[str, Any]:
    """拉取 + 入库；source=auto|aitoearn|inbox|rehearsal。"""
    pulls: list[dict[str, Any]] = []
    if source in ("auto", "aitoearn"):
        pulls.append(await fetch_comments_from_aitoearn(db, tenant_id))
    if source in ("auto", "inbox"):
        pulls.append(load_comments_from_inbox(tenant_id))
    if source == "rehearsal":
        rehearsal = build_dev_rehearsal_comments(tenant_id)
        pulls.append(
            {
                "source": "dev_rehearsal",
                "ok": bool(rehearsal),
                "reason": None if rehearsal else "rehearsal_disabled",
                "items": rehearsal,
            }
        )

    merged: list[dict[str, Any]] = []
    for p in pulls:
        merged.extend(p.get("items") or [])

    if not merged and source in ("auto", "rehearsal") and not is_production_environment():
        rehearsal = build_dev_rehearsal_comments(tenant_id)
        if rehearsal:
            pulls.append(
                {
                    "source": "dev_rehearsal",
                    "ok": True,
                    "reason": "development_empty_fallback",
                    "items": rehearsal,
                }
            )
            merged.extend(rehearsal)

    if not merged:
        return {
            "tenant_id": tenant_id,
            "ingested": 0,
            "failed": 0,
            "pulls": pulls,
            "reason": "no_comments_from_sources",
            "hint": "生产须配 AiToEarn 或 Inbox；开发可点「投递测试评论」",
        }

    ingest = ingest_batch_internal(db, merged)
    if ingest.get("ingested", 0) > 0:
        try:
            mark_sales_channel_flag(db, tenant_id, "douyin_worker_configured")
            db.commit()
        except Exception:
            db.rollback()

    return {
        "tenant_id": tenant_id,
        **ingest,
        "pulls": pulls,
    }
