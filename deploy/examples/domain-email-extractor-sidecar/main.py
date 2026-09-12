"""Domain email extractor Sidecar — YouDing /v1/extract-emails contract."""

from __future__ import annotations

import os
import re
from typing import Any

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Domain Email Extractor Sidecar", version="1.0.0")

TOKEN = (os.getenv("DOMAIN_EMAIL_EXTRACTOR_TOKEN") or "").strip()
ALLOW_DEV_STUB = (os.getenv("DOMAIN_EMAIL_EXTRACTOR_ALLOW_DEV_STUB") or "1").strip().lower() in (
    "1",
    "true",
    "yes",
)

_EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


class ExtractBody(BaseModel):
    domain: str = Field(..., min_length=3, max_length=253)
    tenant_id: str = ""
    max_emails: int = Field(default=5, ge=1, le=10)


def _auth(authorization: str | None) -> None:
    if not TOKEN:
        return
    if not authorization or authorization != f"Bearer {TOKEN}":
        raise HTTPException(status_code=401, detail="unauthorized")


def _normalize_domain(domain: str) -> str:
    d = domain.strip().lower()
    if d.startswith("http://") or d.startswith("https://"):
        d = d.split("//", 1)[-1]
    d = d.split("/", 1)[0]
    if d.startswith("www."):
        d = d[4:]
    return d


def _stub_emails(domain: str, limit: int) -> list[dict[str, Any]]:
    base = f"https://{domain}"
    samples = [
        {
            "email": f"procurement.demo@{domain}",
            "source_url": f"{base}/contact",
            "role": "procurement",
        },
        {
            "email": f"import.demo@{domain}",
            "source_url": f"{base}/about-us",
            "role": "import",
        },
    ]
    out = []
    for row in samples[:limit]:
        if _EMAIL_RE.match(row["email"]):
            out.append(row)
    return out


@app.get("/health")
@app.get("/v1/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "domain-email-extractor-sidecar",
        "mode": "mock" if ALLOW_DEV_STUB else "live",
        "note": "development stub — deploy real EmailExtractor worker for production",
    }


@app.post("/v1/extract-emails")
def extract_emails(
    body: ExtractBody,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    _auth(authorization)
    domain = _normalize_domain(body.domain)
    if not domain or "." not in domain:
        raise HTTPException(status_code=400, detail="invalid domain")

    if not ALLOW_DEV_STUB:
        raise HTTPException(
            status_code=503,
            detail="Real EmailExtractor upstream not configured; set ALLOW_DEV_STUB=1 for dev only",
        )

    emails = _stub_emails(domain, body.max_emails)
    if not emails:
        raise HTTPException(status_code=404, detail="no emails with source_url")

    return {
        "domain": domain,
        "emails": emails,
        "count": len(emails),
        "mode": "mock",
        "probe_mode": "stub",
        "human_verify_required": True,
        "disclaimer": "Dev stub emails — verify before outreach",
    }


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("DOMAIN_EMAIL_EXTRACTOR_PORT") or "8093")
    uvicorn.run(app, host="127.0.0.1", port=port)
