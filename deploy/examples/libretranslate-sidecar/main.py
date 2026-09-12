"""LibreTranslate Sidecar — development stub（机翻须标注 machine_translated）。"""

from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="LibreTranslate Sidecar", version="1.0.0")

TOKEN = (os.getenv("LIBRETRANSLATE_TOKEN") or "").strip()
ALLOW_DEV_STUB = (os.getenv("LIBRETRANSLATE_ALLOW_DEV_STUB") or "1").strip().lower() in (
    "1",
    "true",
    "yes",
)


class TranslateBody(BaseModel):
    q: str = Field(..., min_length=1, max_length=8000)
    source: str = "zh"
    target: str = "en"
    format: str = "text"
    tenant_id: str | None = None


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
        "service": "libretranslate-sidecar",
        "github_ref": "LibreTranslate/LibreTranslate",
        "mode": "mock" if ALLOW_DEV_STUB else "live",
        "machine_translated_disclaimer": True,
    }


@app.get("/languages")
def languages() -> list[dict[str, str]]:
    return [
        {"code": "zh", "name": "Chinese"},
        {"code": "en", "name": "English"},
        {"code": "ar", "name": "Arabic"},
    ]


@app.post("/translate")
def translate(body: TranslateBody, authorization: str | None = Header(None)) -> dict[str, Any]:
    _auth(authorization)
    if not ALLOW_DEV_STUB:
        raise HTTPException(status_code=503, detail="LIBRETRANSLATE_UPSTREAM_NOT_CONFIGURED")
    text = body.q.strip()
    stub = f"[machine_translated stub {body.source}->{body.target}] {text}"
    return {
        "translatedText": stub,
        "mode": "mock",
        "probe_mode": "stub",
        "machine_translated": True,
        "evidence_url": "https://libretranslate.local/dev-stub",
    }


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("LIBRETRANSLATE_PORT", "8098"))
    uvicorn.run(app, host="127.0.0.1", port=port)
