"""AI_Find_Customer 薄适配层 — 暴露优丁 Sidecar 契约 /v1/find-prospects。

将同步找客请求翻译为上游 AI Hunter POST /api/v1/hunts + 轮询。
"""

from __future__ import annotations

import os
import time
from typing import Any

import httpx
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(
    title="AI Find Customer Sidecar Adapter",
    version="1.0.0",
    description="Wraps xiongQvQ/AI_Find_Customer hunt API for YouDing /v1/find-prospects contract",
)

TOKEN = (os.getenv("AI_FIND_CUSTOMER_TOKEN") or "").strip()
UPSTREAM = (os.getenv("AI_HUNTER_UPSTREAM_URL") or "").strip().rstrip("/")
POLL_INTERVAL = float(os.getenv("AI_HUNTER_POLL_SEC") or "2")
POLL_TIMEOUT = float(os.getenv("AI_HUNTER_POLL_TIMEOUT_SEC") or "85")
_TERMINAL = frozenset({"completed", "failed", "cancelled"})


class FindProspectsBody(BaseModel):
    tenant_id: str = ""
    query: str = ""
    region: str = ""
    category: str = ""
    count: int = Field(default=8, ge=3, le=30)


def _auth(authorization: str | None) -> None:
    if not TOKEN:
        return
    if not authorization or authorization != f"Bearer {TOKEN}":
        raise HTTPException(status_code=401, detail="unauthorized")


def _upstream_headers() -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    return headers


def _normalize_lead(row: dict[str, Any]) -> dict[str, Any] | None:
    evidence = (
        str(row.get("evidence_url") or row.get("website") or row.get("url") or "")
        .strip()
    )
    title = str(
        row.get("title")
        or row.get("company_name")
        or row.get("company")
        or row.get("name")
        or ""
    ).strip()
    if not evidence:
        return None
    return {
        "title": title or "Prospect",
        "company": str(row.get("company") or row.get("company_name") or title)[:200],
        "country_code": str(row.get("country_code") or row.get("country") or "")[:8].upper(),
        "email": row.get("email"),
        "phone": row.get("phone"),
        "buyer_type": row.get("buyer_type") or "importer",
        "fit_score": row.get("fit_score") or row.get("score") or 65,
        "notes": row.get("notes") or row.get("snippet") or "",
        "evidence_url": evidence[:500],
        "source": row.get("source") or "ai_hunter",
    }


def _run_hunt(body: FindProspectsBody) -> dict[str, Any]:
    if not UPSTREAM:
        raise HTTPException(
            status_code=503,
            detail="AI_HUNTER_UPSTREAM_URL not configured; deploy AI_Find_Customer backend first",
        )
    hunt_body = {
        "description": body.query or f"{body.region} {body.category} B2B buyer",
        "product_keywords": [w for w in body.category.split() if w][:8],
        "target_customer_profile": body.category or "B2B distributor importer",
        "target_regions": [body.region] if body.region else [],
        "target_lead_count": body.count,
        "max_rounds": 3,
        "min_new_leads_threshold": min(3, body.count),
        "enable_email_craft": False,
    }
    headers = _upstream_headers()
    deadline = time.monotonic() + POLL_TIMEOUT

    with httpx.Client(timeout=30.0) as client:
        create = client.post(f"{UPSTREAM}/api/v1/hunts", json=hunt_body, headers=headers)
    if create.status_code >= 300:
        raise HTTPException(
            status_code=502,
            detail=f"upstream hunt create HTTP {create.status_code}",
        )
    hunt_id = str(create.json().get("hunt_id") or "")
    if not hunt_id:
        raise HTTPException(status_code=502, detail="upstream hunt missing hunt_id")

    status = "pending"
    while time.monotonic() < deadline:
        with httpx.Client(timeout=15.0) as client:
            st = client.get(
                f"{UPSTREAM}/api/v1/hunts/{hunt_id}/status",
                headers=headers,
            )
        if st.status_code < 300:
            status = str(st.json().get("status") or "").lower()
            if status in _TERMINAL:
                break
        time.sleep(POLL_INTERVAL)

    with httpx.Client(timeout=30.0) as client:
        result = client.get(
            f"{UPSTREAM}/api/v1/hunts/{hunt_id}/result",
            headers=headers,
        )
    if result.status_code >= 300:
        raise HTTPException(
            status_code=502,
            detail=f"upstream hunt result HTTP {result.status_code}",
        )
    data = result.json()
    leads = data.get("leads") if isinstance(data, dict) else []
    prospects = []
    for row in leads or []:
        if isinstance(row, dict):
            norm = _normalize_lead(row)
            if norm:
                prospects.append(norm)
    return {
        "prospects": prospects[: body.count],
        "region": body.region,
        "category": body.category,
        "hunt_id": hunt_id,
        "hunt_status": status,
        "human_verify_required": True,
        "probe_mode": data.get("probe_mode") if isinstance(data, dict) else None,
        "mode": data.get("mode") if isinstance(data, dict) else None,
    }


@app.get("/health")
@app.get("/v1/health")
def health() -> dict[str, Any]:
    upstream_ok = None
    detail = None
    if UPSTREAM:
        try:
            with httpx.Client(timeout=5.0) as client:
                resp = client.get(f"{UPSTREAM}/api/v1/health", headers=_upstream_headers())
            upstream_ok = resp.status_code < 300
            if not upstream_ok:
                detail = f"upstream HTTP {resp.status_code}"
        except Exception as exc:
            upstream_ok = False
            detail = str(exc)[:200]
    return {
        "status": "ok",
        "service": "ai-find-customer-sidecar-adapter",
        "upstream_url": UPSTREAM or None,
        "upstream_healthy": upstream_ok,
        "upstream_detail": detail,
        "github_ref": "xiongQvQ/AI_Find_Customer",
    }


@app.post("/v1/find-prospects")
def find_prospects(
    body: FindProspectsBody,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    _auth(authorization)
    return _run_hunt(body)
