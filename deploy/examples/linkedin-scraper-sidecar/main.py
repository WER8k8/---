"""LinkedIn 决策人 Sidecar 薄适配 — development stub。"""

from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="LinkedIn Decision Maker Sidecar", version="1.0.0")

TOKEN = (os.getenv("LINKEDIN_DECISION_MAKER_TOKEN") or "").strip()
ALLOW_DEV_STUB = (os.getenv("LINKEDIN_DECISION_MAKER_ALLOW_DEV_STUB") or "1").strip().lower() in (
    "1",
    "true",
    "yes",
)


class DecisionMakerBody(BaseModel):
    company: str = Field(..., min_length=2, max_length=200)
    domain: str = ""
    industry: str = ""
    tenant_id: str = ""
    max_results: int = Field(default=5, ge=1, le=10)


def _auth(authorization: str | None) -> None:
    if not TOKEN:
        return
    if not authorization or authorization != f"Bearer {TOKEN}":
        raise HTTPException(status_code=401, detail="unauthorized")


@app.get("/health")
@app.get("/v1/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "linkedin-decision-maker-sidecar",
        "github_ref": "tufayellus/linkedin-scraper",
        "mode": "mock" if ALLOW_DEV_STUB else "live",
        "compliance": "restricted",
    }


@app.post("/v1/decision-makers")
def decision_makers(
    body: DecisionMakerBody,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    _auth(authorization)
    if not ALLOW_DEV_STUB:
        raise HTTPException(status_code=503, detail="LinkedIn upstream not configured")

    slug = (body.domain or body.company).lower().replace(" ", "-")[:40]
    company = body.company.strip()
    contacts = [
        {
            "name": "Alex Morgan",
            "title": "Purchasing Manager",
            "company": company,
            "linkedin_url": f"https://www.linkedin.com/in/dev-stub-{slug}-buyer",
            "evidence_url": f"https://www.linkedin.com/in/dev-stub-{slug}-buyer",
            "email": None,
        },
        {
            "name": "Jamie Lee",
            "title": "Import Manager",
            "company": company,
            "linkedin_url": f"https://www.linkedin.com/in/dev-stub-{slug}-import",
            "evidence_url": f"https://www.linkedin.com/in/dev-stub-{slug}-import",
            "email": None,
        },
    ][: body.max_results]

    return {
        "contacts": contacts,
        "count": len(contacts),
        "mode": "mock",
        "probe_mode": "stub",
        "human_verify_required": True,
        "disclaimer": "Dev stub — LinkedIn ToS applies; verify before outreach",
    }


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("LINKEDIN_DECISION_MAKER_PORT") or "8095")
    uvicorn.run(app, host="127.0.0.1", port=port)
