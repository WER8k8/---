"""AI_Find_Customer 上游 Mock — 仅 development 接线验收。

返回带 evidence_url 的示例 leads，响应含 mode=mock；禁止在生产启用。
"""

from __future__ import annotations

import os
import uuid
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="AI Hunter Upstream Mock", version="1.0.0")

_HUNTS: dict[str, dict[str, Any]] = {}


class HuntCreate(BaseModel):
    description: str = ""
    product_keywords: list[str] = Field(default_factory=list)
    target_customer_profile: str = ""
    target_regions: list[str] = Field(default_factory=list)
    target_lead_count: int = 8
    max_rounds: int = 3
    min_new_leads_threshold: int = 3
    enable_email_craft: bool = False


def _sample_leads(body: HuntCreate) -> list[dict[str, Any]]:
    region = (body.target_regions[0] if body.target_regions else "中东")[:32]
    category = (body.target_customer_profile or "保温建材")[:64]
    n = max(3, min(int(body.target_lead_count), 8))
    samples = [
        {
            "company_name": f"Gulf {category} Trading LLC",
            "website": "https://example.com/gulf-insulation-distributor",
            "country_code": "AE",
            "email": "procurement.demo@example.com",
            "buyer_type": "distributor",
            "score": 0.78,
            "snippet": f"Mock lead for dev wiring — {region} {category}",
            "source": "google",
        },
        {
            "company_name": f"Riyadh Import & Supply Co.",
            "website": "https://example.com/riyadh-building-materials",
            "country_code": "SA",
            "email": None,
            "buyer_type": "importer",
            "score": 0.71,
            "snippet": "Dev stub — verify evidence_url mapping only",
            "source": "b2b_directory",
        },
        {
            "company_name": "EuroBuild Wholesale GmbH",
            "website": "https://example.com/eurobuild-wholesale",
            "country_code": "DE",
            "email": "buying.demo@example.com",
            "buyer_type": "wholesaler",
            "score": 0.69,
            "snippet": "Replace with real AI_Find_Customer upstream in staging",
            "source": "maps",
        },
    ]
    return samples[:n]


@app.get("/api/v1/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "ai-hunter-upstream-mock",
        "mode": "mock",
        "github_ref": "xiongQvQ/AI_Find_Customer",
        "note": "development wiring only — not real crawl results",
    }


@app.post("/api/v1/hunts")
def create_hunt(body: HuntCreate) -> dict[str, Any]:
    hunt_id = f"mock-{uuid.uuid4().hex[:12]}"
    _HUNTS[hunt_id] = {
        "status": "completed",
        "body": body.model_dump(),
        "leads": _sample_leads(body),
    }
    return {"hunt_id": hunt_id, "status": "completed", "mode": "mock"}


@app.get("/api/v1/hunts/{hunt_id}/status")
def hunt_status(hunt_id: str) -> dict[str, Any]:
    row = _HUNTS.get(hunt_id)
    if not row:
        return {"status": "failed", "mode": "mock", "detail": "unknown hunt_id"}
    return {"status": row["status"], "mode": "mock"}


@app.get("/api/v1/hunts/{hunt_id}/result")
def hunt_result(hunt_id: str) -> dict[str, Any]:
    row = _HUNTS.get(hunt_id)
    if not row:
        return {"leads": [], "mode": "mock", "error": "unknown hunt_id"}
    return {
        "hunt_id": hunt_id,
        "status": "completed",
        "mode": "mock",
        "probe_mode": "stub",
        "leads": row["leads"],
        "human_verify_required": True,
    }


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("AI_HUNTER_MOCK_PORT") or "8080")
    uvicorn.run(app, host="127.0.0.1", port=port)
