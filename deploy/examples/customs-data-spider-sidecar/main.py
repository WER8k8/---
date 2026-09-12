"""CustomsDataSpider Sidecar 薄适配 — development stub。"""

from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Customs Data Spider Sidecar", version="1.0.0")

TOKEN = (os.getenv("CUSTOMS_DATA_SPIDER_TOKEN") or "").strip()
ALLOW_DEV_STUB = (os.getenv("CUSTOMS_DATA_SPIDER_ALLOW_DEV_STUB") or "1").strip().lower() in (
    "1",
    "true",
    "yes",
)


class BuyerResearchBody(BaseModel):
    product: str = Field(..., min_length=2, max_length=200)
    hs_code: str | None = Field(None, max_length=32)
    country_code: str | None = Field(None, max_length=8)
    tenant_id: str = ""
    max_results: int = Field(default=8, ge=1, le=20)


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
        "service": "customs-data-spider-sidecar",
        "github_ref": "CustomsDataSpider",
        "mode": "mock" if ALLOW_DEV_STUB else "live",
        "compliance": "restricted",
    }


@app.post("/v1/buyer-research")
def buyer_research(
    body: BuyerResearchBody,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    _auth(authorization)
    if not ALLOW_DEV_STUB:
        raise HTTPException(status_code=503, detail="CustomsDataSpider upstream not configured")

    cc = (body.country_code or "DE").upper()[:2]
    slug = body.product.lower().replace(" ", "-")[:30]
    hs = (body.hs_code or "000000").strip()
    buyers = [
        {
            "company_name": f"Stub Import GmbH ({cc})",
            "country_code": cc,
            "product_hint": body.product,
            "import_volume_hint": "dev_reference_only",
            "evidence_url": f"https://dev.customs-stub.local/brief/{hs}/{cc}/{slug}-buyer-1",
            "source_type": "customs_public_stub",
        },
        {
            "company_name": f"Stub Trading Co ({cc})",
            "country_code": cc,
            "product_hint": body.product,
            "import_volume_hint": "dev_reference_only",
            "evidence_url": f"https://dev.customs-stub.local/brief/{hs}/{cc}/{slug}-buyer-2",
            "source_type": "customs_public_stub",
        },
    ][: body.max_results]

    return {
        "product": body.product,
        "hs_code": body.hs_code,
        "country_code": cc,
        "buyers": buyers,
        "buyer_count": len(buyers),
        "included": None,
        "mode": "mock",
        "probe_mode": "stub",
        "human_verify_required": True,
        "disclaimer": "Dev stub — verify buyers with customs broker before outreach",
    }


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("CUSTOMS_DATA_SPIDER_PORT") or "8096")
    uvicorn.run(app, host="127.0.0.1", port=port)
