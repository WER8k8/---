"""只读 IMAP 询盘 Sidecar — development stub（禁止 SMTP）。"""

from __future__ import annotations

import os
import uuid
from typing import Any

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="IMAP Inquiry Sidecar", version="1.0.0")

TOKEN = (os.getenv("IMAP_INQUIRY_TOKEN") or "").strip()
ALLOW_DEV_STUB = (os.getenv("IMAP_INQUIRY_ALLOW_DEV_STUB") or "1").strip().lower() in (
    "1",
    "true",
    "yes",
)


class PollInboxBody(BaseModel):
    tenant_id: str = ""
    mailbox: str = "INBOX"
    max_messages: int = Field(default=5, ge=1, le=50)


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
        "service": "imap-inquiry-sidecar",
        "github_ref": "mymailclaw",
        "mode": "mock" if ALLOW_DEV_STUB else "live",
        "compliance": "read_only_imap",
        "smtp_disabled": True,
    }


@app.post("/v1/poll-inbox")
def poll_inbox(
    body: PollInboxBody,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    _auth(authorization)
    if not ALLOW_DEV_STUB:
        raise HTTPException(status_code=503, detail="IMAP upstream not configured")

    tid = body.tenant_id or "dev"
    messages = []
    for i in range(min(body.max_messages, 3)):
        mid = f"stub-{uuid.uuid4().hex[:12]}"
        messages.append(
            {
                "message_id": mid,
                "from_email": f"buyer{i + 1}.demo@example.com",
                "from_name": f"Import Manager {i + 1}",
                "subject": f"RFQ: rock wool insulation batch {i + 1}",
                "body": (
                    f"Hello, we are interested in your insulation products. "
                    f"Please send MOQ and FOB price. Ref {mid}."
                ),
                "received_at": "2026-06-20T10:00:00Z",
                "evidence_url": f"https://dev.imap-stub.local/{tid}/INBOX/{mid}",
            }
        )

    return {
        "mailbox": body.mailbox,
        "messages": messages,
        "count": len(messages),
        "mode": "mock",
        "probe_mode": "stub",
        "human_verify_required": True,
        "smtp_disabled": True,
        "disclaimer": "Dev stub — read-only poll; no auto-reply",
    }


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("IMAP_INQUIRY_PORT") or "8097")
    uvicorn.run(app, host="127.0.0.1", port=port)
