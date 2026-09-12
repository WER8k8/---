"""Hermes 对抓取技术候选做安全验证（不安装、不改依赖）。"""

from __future__ import annotations

import logging
import re
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.services.hermes.maintenance_constitution import assert_maintenance_action

logger = logging.getLogger("uj-admin.hermes_tech_validation")

HIGH_IMPACT_PATTERNS = (
    r"breaking",
    r"security",
    r"cve-\d",
    r"deprecated",
    r"major",
    r"v\d+\.0\.0",
    r"schema\.org",
    r"core web vitals",
    r"lcp",
    r"json-ld",
)


def _guess_impact(title: str, body: str = "") -> str:
    """_guess_impact。

    参数说明：
    :param title: 参数 title
    :param body: 参数 body
    :return: 返回处理结果。
    """
    text = f"{title} {body}".lower()
    if any(re.search(p, text, re.I) for p in HIGH_IMPACT_PATTERNS):
        return "high"
    if any(k in text for k in ("release", "update", "new", "fix", "性能", "performance")):
        return "medium"
    return "low"


def _detect_category(url: str, source: str) -> str:
    """_detect_category。

    参数说明：
    :param url: 参数 url
    :param source: 参数 source
    :return: 返回处理结果。
    """
    blob = f"{url} {source}".lower()
    if "schema" in blob or "json-ld" in blob:
        return "structured_data"
    if "web.dev" in blob or "vitals" in blob or "lcp" in blob:
        return "performance"
    if "vue" in blob or "nuxt" in blob or "vite" in blob:
        return "frontend"
    if "fastapi" in blob or "github:fastapi" in blob:
        return "backend"
    return "unknown"


def validate_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    """只读验证：链接可达 + 影响分级；禁止自动升级依赖。"""
    assert_maintenance_action("read_probe")
    url = (candidate.get("url") or "").strip()
    title = (candidate.get("title") or "").strip()
    body = (candidate.get("body_preview") or "")[:500]
    impact = _guess_impact(title, body)
    category = _detect_category(url, candidate.get("source") or "")
    row = {
        **candidate,
        "category": category,
        "impact": impact,
        "validation_status": "pending",
        "validation_note": "",
        "hermes_action": "draft_only",
        "next_step": "license_check_then_isolated_test",
    }
    if not url:
        row["validation_status"] = "skip"
        row["validation_note"] = "无 URL，跳过链接探测"
        return row

    try:
        with httpx.Client(timeout=12, follow_redirects=True, headers={"User-Agent": "UJ-Hermes-Validator/1.0"}) as client:
            resp = client.head(url)
            if resp.status_code >= 400:
                resp = client.get(url)
            ok = resp.status_code < 400
        row["validation_status"] = "pass" if ok else "fail"
        row["validation_note"] = f"HTTP {resp.status_code}" if ok else f"不可达 HTTP {resp.status_code}"
        if ok and impact == "high":
            row["hermes_action"] = "notify_human_review"
    except Exception as exc:
        row["validation_status"] = "fail"
        row["validation_note"] = str(exc)[:160]

    return row


def validate_all(
    candidates: list[dict[str, Any]],
    db: Session | None = None,
    *,
    expert_review: bool = True,
) -> list[dict[str, Any]]:
    """validate_all。

    参数说明：
    :param candidates: 参数 candidates
    :param db: 参数 db
    :param expert_review: 参数 expert_review
    :return: 返回处理结果。
    """
    rows = [validate_candidate(c) for c in candidates]
    if expert_review and db is not None:
        from app.services.hermes.ecc_expert_panel import review_all
        rows = review_all(db, rows)
    return rows
