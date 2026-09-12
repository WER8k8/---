# P4 B2B Sidecars — CustomsDataSpider

Extends P3 (`scripts/start-p4-sidecars-dev.ps1`).

| Service | Port | Env | Compliance |
|---------|------|-----|------------|
| CustomsDataSpider | 8096 | `CUSTOMS_DATA_SPIDER_URL` | `restricted` — `tenant_consent` + `compliance_acknowledged` |

## Start

```powershell
powershell -File scripts/start-p4-sidecars-dev.ps1
powershell -File scripts/start-dev-admin.ps1 -ForceRestart
```

## Verify

```powershell
cd backend
.\.venv\Scripts\python.exe ..\scripts\verify-customs-data-spider-sidecar.py --smoke
.\.venv\Scripts\python.exe -m pytest tests/unit/test_p4_sidecars.py -q
```

## API

- `GET /api/v1/foreign-trade/trade-intel/customs-buyer-brief?product=&include_sidecar=true`
- `POST /api/v1/foreign-trade/integrations/customs/buyer-research`
- Sidecar status key: `customs_data_spider`

## Honesty gates

- Buyers **must** include `evidence_url`; dev stub sets `mode=mock`, `included=null`
- Never claim `included:true` without verifiable upstream source
