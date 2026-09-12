# P5 B2B Sidecars — IMAP Read-Only Inquiry Ingest

Extends P4 (`scripts/start-p5-sidecars-dev.ps1`).

| Service | Port | Env | Compliance |
|---------|------|-----|------------|
| IMAP inquiry (mymailclaw 对标) | 8097 | `IMAP_INQUIRY_URL` | **read-only** — `smtp_disabled: true` |

## Start

```powershell
powershell -File scripts/start-p5-sidecars-dev.ps1
powershell -File scripts/start-dev-admin.ps1 -ForceRestart
```

## Verify

```powershell
cd backend
.\.venv\Scripts\python.exe ..\scripts\verify-imap-inquiry-sidecar.py --smoke
.\.venv\Scripts\python.exe ..\scripts\verify-inquiry-bridge.py
.\.venv\Scripts\python.exe -m pytest tests/unit/test_p5_sidecars.py -q
```

## API

- `POST /api/v1/cross-border/inquiries/imap-poll` — body: `tenant_consent`, `compliance_acknowledged`
- Sidecar status: `integrations/sidecars/status` → `imap_inquiry`
- Bridge status embeds `imap_inquiry` health

## Honesty gates

- Poll only; **no SMTP send**, no「已自动回复」
- Each message needs `message_id` + `from_email` + `body`; dedupe via `[imap-msg:…]` tag
- Dev stub: `mode=mock` / `probe_mode=stub`
