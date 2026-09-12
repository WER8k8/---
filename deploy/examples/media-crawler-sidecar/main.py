"""MediaCrawler 薄 Sidecar — 兼容优丁 /v1/run-spider 契约（development stub）。"""

from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="MediaCrawler Sidecar", version="1.0.0")

TOKEN = (os.getenv("MEDIA_CRAWLER_TOKEN") or "").strip()
ALLOW_DEV_STUB = (os.getenv("MEDIA_CRAWLER_ALLOW_DEV_STUB") or "1").strip().lower() in (
    "1",
    "true",
    "yes",
)

_SUPPORTED = frozenset(
    {
        "media_facebook",
        "media_instagram",
        "media_youtube",
        "media_europages",
        "media_thomasnet",
    }
)


class RunSpiderBody(BaseModel):
    spider_id: str
    params: dict[str, Any] = Field(default_factory=dict)
    tenant_id: str = ""
    purpose: str = ""


def _auth(authorization: str | None) -> None:
    if not TOKEN:
        return
    if not authorization or authorization != f"Bearer {TOKEN}":
        raise HTTPException(status_code=401, detail="unauthorized")


def _stub_items(spider_id: str, keyword: str) -> list[dict[str, Any]]:
    platform = spider_id.replace("media_", "")
    slug = keyword.replace(" ", "-").lower()[:40] or "b2b-buyer"
    return [
        {
            "title": f"{keyword} — {platform} public page (dev stub)",
            "company": f"Sample {platform.title()} Merchant",
            "url": f"https://example.com/{platform}/{slug}",
            "evidence_url": f"https://example.com/{platform}/{slug}",
            "country_code": "US",
            "source": platform,
            "snippet": "Development stub — deploy NanmiCoder/MediaCrawler for live crawl",
        }
    ]


@app.get("/health")
@app.get("/v1/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "media-crawler-sidecar",
        "github_ref": "NanmiCoder/MediaCrawler",
        "supported_spiders": sorted(_SUPPORTED),
        "mode": "mock" if ALLOW_DEV_STUB else "live",
    }


@app.post("/v1/run-spider")
def run_spider(
    body: RunSpiderBody,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    _auth(authorization)
    sid = (body.spider_id or "").strip().lower()
    if sid not in _SUPPORTED:
        raise HTTPException(status_code=404, detail=f"unsupported spider_id: {sid}")
    if not ALLOW_DEV_STUB:
        raise HTTPException(status_code=503, detail="MediaCrawler upstream not configured")

    keyword = str(body.params.get("keyword") or body.params.get("query") or "insulation buyer")
    items = _stub_items(sid, keyword)
    return {
        "spider_id": sid,
        "items": items,
        "evidence_url": items[0]["evidence_url"],
        "mode": "mock",
        "probe_mode": "stub",
        "human_review_required": True,
        "purpose": body.purpose,
    }


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("MEDIA_CRAWLER_PORT") or "8094")
    uvicorn.run(app, host="127.0.0.1", port=port)
